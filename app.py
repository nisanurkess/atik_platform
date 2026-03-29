import json
import os
from datetime import datetime, timedelta

from dotenv import load_dotenv
from openai import APIError, AuthenticationError, OpenAI, RateLimitError
from flask import (
    Flask,
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import (
    current_user,
    login_required,
    login_user,
    logout_user,
)
from sqlalchemy import text as sql_text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from extensions import login_manager
from models import Firm, Listing, ListingRequest, User, db
from services.ai_service import improve_listing_description
from services.categories import CATEGORIES
from services.listing_analyzer import analyze_listing_text
from services.recommender import recommend_similar_listings
from utils.auth_helpers import normalize_email, normalize_password_input


def dedupe_listing_request_bursts(window_seconds: int = 120) -> None:
    """
    Aynı ilan + aynı kullanıcı + aynı mesaj metni için kısa süre içinde oluşmuş
    ardışık mükerrer kayıtları siler (çift tıklama / çift POST). Aynı kullanıcının
    günler sonra tekrar gönderdiği aynı metinli talepler korunur.
    """
    rows = (
        ListingRequest.query.filter(ListingRequest.user_id.isnot(None))
        .order_by(ListingRequest.listing_id, ListingRequest.user_id, ListingRequest.created_at, ListingRequest.id)
        .all()
    )
    groups: dict[tuple[int, int, str], list] = {}
    for lr in rows:
        msg = " ".join((lr.message or "").split())
        key = (lr.listing_id, lr.user_id, msg)
        groups.setdefault(key, []).append(lr)

    to_delete: list[int] = []
    for key, g in groups.items():
        if len(g) < 2:
            continue
        g.sort(key=lambda r: (r.created_at, r.id))
        kept = g[0]
        for r in g[1:]:
            if (r.created_at - kept.created_at).total_seconds() <= window_seconds:
                to_delete.append(r.id)
            else:
                kept = r

    if not to_delete:
        return
    for rid in to_delete:
        obj = db.session.get(ListingRequest, rid)
        if obj is not None:
            db.session.delete(obj)
    db.session.commit()


def _safe_next_path(next_raw: str | None) -> str | None:
    """Open redirect önlemek için sadece aynı site içi path kabul edilir."""
    if not next_raw:
        return None
    n = next_raw.strip()
    if not n.startswith("/") or n.startswith("//"):
        return None
    return n


def _ensure_sqlite_column(table_name: str, column_name: str, alter_sql: str) -> None:
    """
    SQLite otomatik migration yapmadığı için basit kolon ekleme.
    Sadece kolon yoksa ekler.
    """

    cols = [
        row[1]
        for row in db.session.execute(
            sql_text(f"PRAGMA table_info({table_name})")
        ).fetchall()
    ]
    if column_name in cols:
        return
    db.session.execute(sql_text(alter_sql))
    db.session.commit()


def create_app():
    load_dotenv()

    app = Flask(__name__, instance_relative_config=True)

    # Basit konfigürasyon
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or "çok-gizli-olmayan-bir-anahtar"

    # SQLite: instance/database.db
    os.makedirs(app.instance_path, exist_ok=True)
    db_path = os.path.join(app.instance_path, "database.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = "login"

    @login_manager.user_loader
    def load_user(user_id: str):
        if not user_id:
            return None
        try:
            pk = int(user_id)
        except (TypeError, ValueError):
            return None
        return db.session.get(User, pk)

    # Tablo oluşturma + eski DB için basit şema eklemeleri
    with app.app_context():
        db.create_all()

        try:
            # `companies` tablosuna yeni kolonlar (user_id/description/phone)
            _ensure_sqlite_column(
                "companies",
                "user_id",
                "ALTER TABLE companies ADD COLUMN user_id INTEGER",
            )
            _ensure_sqlite_column(
                "companies",
                "description",
                "ALTER TABLE companies ADD COLUMN description TEXT",
            )
            _ensure_sqlite_column(
                "companies",
                "phone",
                "ALTER TABLE companies ADD COLUMN phone TEXT",
            )
        except Exception:
            # DB'de beklenmeyen durum varsa uygulama çalışmaya devam etsin.
            pass

        try:
            # `listings` tablosuna yeni/eksik kolonlar (tags ve price)
            _ensure_sqlite_column(
                "listings",
                "tags",
                "ALTER TABLE listings ADD COLUMN tags TEXT",
            )
            _ensure_sqlite_column(
                "listings",
                "price",
                "ALTER TABLE listings ADD COLUMN price REAL",
            )
        except Exception:
            pass

        try:
            _ensure_sqlite_column(
                "requests",
                "company_email",
                "ALTER TABLE requests ADD COLUMN company_email VARCHAR(200)",
            )
        except Exception:
            pass

        try:
            _ensure_sqlite_column(
                "requests",
                "user_id",
                "ALTER TABLE requests ADD COLUMN user_id INTEGER REFERENCES users(id)",
            )
        except Exception:
            pass

        # Eski talepler: company_email ile kullanıcı bulunup user_id doldurulur (görünüm tutarlılığı)
        try:
            orphan_reqs = (
                ListingRequest.query.filter(ListingRequest.user_id.is_(None))
                .filter(ListingRequest.company_email.isnot(None))
                .all()
            )
            for lr in orphan_reqs:
                em = normalize_email(lr.company_email or "")
                if not em:
                    continue
                u = User.query.filter_by(email=em).first()
                if u:
                    lr.user_id = u.id
            if orphan_reqs:
                db.session.commit()
        except Exception:
            db.session.rollback()

        try:
            dedupe_listing_request_bursts()
        except Exception:
            db.session.rollback()

    @app.context_processor
    def inject_globals():
        return {"CATEGORIES": CATEGORIES}

    @app.route("/test-ai")
    def test_ai():
        """
        OpenAI bağlantısını test eder. API anahtarı sadece sunucu tarafında kullanılır;
        yanıtta asla anahtar dönülmez.
        """
        api_key = (os.environ.get("OPENAI_API_KEY") or "").strip()
        if not api_key or api_key == "your_api_key_here":
            return (
                jsonify(
                    {
                        "ok": False,
                        "error": "OPENAI_API_KEY eksik veya geçersiz. .env dosyasına gerçek anahtarınızı yazın.",
                    }
                ),
                400,
            )

        prompt = "Merhaba, sistem çalışıyor mu? Kısa cevap ver."
        try:
            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
            )
            reply = (response.choices[0].message.content or "").strip()
            return jsonify({"ok": True, "reply": reply})
        except AuthenticationError:
            return (
                jsonify(
                    {
                        "ok": False,
                        "error": "OpenAI kimlik doğrulama hatası. API anahtarını kontrol edin.",
                    }
                ),
                401,
            )
        except RateLimitError:
            return (
                jsonify(
                    {
                        "ok": False,
                        "error": "OpenAI istek limiti aşıldı. Bir süre sonra tekrar deneyin.",
                    }
                ),
                429,
            )
        except APIError as exc:
            return (
                jsonify(
                    {
                        "ok": False,
                        "error": f"OpenAI API hatası: {str(exc)}",
                    }
                ),
                502,
            )
        except Exception as exc:
            return (
                jsonify(
                    {
                        "ok": False,
                        "error": f"Beklenmeyen hata: {type(exc).__name__}",
                    }
                ),
                500,
            )

    @app.route("/ai/analyze", methods=["POST"])
    def ai_analyze_listing_text():
        payload = request.get_json(silent=True) or {}
        description = (payload.get("description") or "").strip()
        title = (payload.get("title") or "").strip()

        if not description:
            return jsonify(
                {
                    "predicted_category": "Diğer",
                    "confidence": 0,
                    "tags": [],
                    "short_summary": "",
                    "suggested_title": "",
                }
            )

        text_for_ai = (
            f"Başlık: {title}\nAçıklama: {description}" if title else description
        )
        # Yerel yedek: keyword eşleşmesi yalnızca gerçek açıklama üzerinde çalışsın
        result = analyze_listing_text(text_for_ai, local_text=description)
        return jsonify(result)

    @app.route("/ai/improve-description", methods=["POST"])
    @login_required
    def ai_improve_description():
        payload = request.get_json(silent=True) or {}
        description = (payload.get("description") or "").strip()
        if not description:
            return jsonify({"error": "description boş olamaz"}), 400

        result = improve_listing_description(description)
        return jsonify(result)

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template(
            "404.html",
            title="Sayfa Bulunamadı",
            message="İstediğiniz ilan veya sayfa bulunamadı.",
        ), 404

    @app.route("/")
    def index():
        total_listings = Listing.query.count()
        active_listings = Listing.query.filter_by(status="Aktif").count()
        firm_count = Firm.query.count()
        latest_listings = Listing.query.order_by(Listing.created_at.desc()).limit(5).all()

        return render_template(
            "index.html",
            title="Atık Değişim Platformu",
            total_listings=total_listings,
            active_listings=active_listings,
            firm_count=firm_count,
            latest_listings=latest_listings,
        )

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            full_name = (request.form.get("full_name") or "").strip()
            email = normalize_email(request.form.get("email") or "")
            password = normalize_password_input(request.form.get("password") or "")
            password2 = normalize_password_input(request.form.get("password2") or "")

            errors: list[str] = []
            if not full_name:
                errors.append("Ad soyad zorunludur.")
            if not email:
                errors.append("E-posta zorunludur.")
            if not password:
                errors.append("Şifre boş olamaz.")
            if len(password) < 6:
                errors.append("Şifre en az 6 karakter olmalıdır.")
            if password != password2:
                errors.append("Şifre tekrar eşleşmiyor.")

            if email and User.query.filter_by(email=email).first():
                errors.append("Bu e-posta ile kayıtlı bir kullanıcı zaten var.")

            if errors:
                for err in errors:
                    flash(err, "danger")
                return render_template(
                    "auth/register.html",
                    title="Kayıt Ol",
                    form_data=request.form,
                )

            user = User(full_name=full_name, email=email)
            user.set_password(password)
            db.session.add(user)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                flash(
                    "Bu e-posta ile kayıt oluşturulamadı (zaten kullanılıyor olabilir).",
                    "danger",
                )
                return render_template(
                    "auth/register.html",
                    title="Kayıt Ol",
                    form_data=request.form,
                )

            flash("Kayıt başarılı. Giriş yapmak için lütfen giriş sayfasını ziyaret edin.", "success")
            return redirect(url_for("login"))

        return render_template("auth/register.html", title="Kayıt Ol", form_data={})

    @app.route("/login", methods=["GET", "POST"])
    def login():
        next_from_query = _safe_next_path(request.args.get("next"))
        if request.method == "POST":
            email = normalize_email(request.form.get("email") or "")
            password = normalize_password_input(request.form.get("password") or "")
            next_after_login = _safe_next_path(request.form.get("next")) or next_from_query

            if not email or not password:
                flash("E-posta ve şifre zorunludur.", "danger")
                return render_template(
                    "auth/login.html",
                    title="Giriş Yap",
                    form_data=request.form,
                    next_url=next_after_login,
                )

            user = User.query.filter_by(email=email).first()
            if not user:
                flash("E-posta veya şifre hatalı.", "danger")
                return render_template(
                    "auth/login.html",
                    title="Giriş Yap",
                    form_data=request.form,
                    next_url=next_after_login,
                )
            if not user.check_password(password):
                flash("E-posta veya şifre hatalı.", "danger")
                return render_template(
                    "auth/login.html",
                    title="Giriş Yap",
                    form_data=request.form,
                    next_url=next_after_login,
                )

            login_user(user)

            if next_after_login:
                return redirect(next_after_login)

            firm = Firm.query.filter_by(user_id=user.id).first()
            if firm:
                return redirect(url_for("firm_detail"))
            return redirect(url_for("firm_create"))

        return render_template(
            "auth/login.html",
            title="Giriş Yap",
            form_data={},
            next_url=next_from_query,
        )

    @app.route("/logout", methods=["POST", "GET"])
    @login_required
    def logout():
        logout_user()
        flash("Çıkış yapıldı.", "info")
        return redirect(url_for("login"))

    @app.route("/firm/create", methods=["GET", "POST"])
    @login_required
    def firm_create():
        existing = Firm.query.filter_by(user_id=current_user.id).first()
        if existing:
            return redirect(url_for("firm_detail"))

        if request.method == "POST":
            name = (request.form.get("name") or "").strip()
            city = (request.form.get("city") or "").strip()
            sector = (request.form.get("sector") or "").strip()
            description = (request.form.get("description") or "").strip() or None
            phone = (request.form.get("phone") or "").strip() or None

            errors: list[str] = []
            if not name:
                errors.append("Firma adı zorunludur.")
            if not city:
                errors.append("Şehir zorunludur.")
            if not sector:
                errors.append("Sektör zorunludur.")

            if errors:
                for err in errors:
                    flash(err, "danger")
                return render_template("firm/create.html", title="Firma Oluştur", form_data=request.form)

            firm = Firm(
                user_id=current_user.id,
                name=name,
                city=city,
                sector=sector,
                description=description,
                phone=phone,
                created_at=datetime.utcnow(),
            )
            db.session.add(firm)
            db.session.commit()

            flash("Firma bilgileri kaydedildi.", "success")
            return redirect(url_for("firm_detail"))

        return render_template("firm/create.html", title="Firma Oluştur", form_data={})

    @app.route("/firm")
    @login_required
    def firm_detail():
        firm = Firm.query.filter_by(user_id=current_user.id).first()
        if not firm:
            flash("Önce firma bilgilerinizi oluşturmalısınız.", "warning")
            return redirect(url_for("firm_create"))

        return render_template("firm/detail.html", title="Firma Bilgilerim", firm=firm)

    @app.route("/firm/edit", methods=["GET", "POST"])
    @login_required
    def firm_edit():
        firm = Firm.query.filter_by(user_id=current_user.id).first()
        if not firm:
            flash("Önce firma bilgilerinizi oluşturmalısınız.", "warning")
            return redirect(url_for("firm_create"))

        if request.method == "POST":
            name = (request.form.get("name") or "").strip()
            city = (request.form.get("city") or "").strip()
            sector = (request.form.get("sector") or "").strip()
            description = (request.form.get("description") or "").strip() or None
            phone = (request.form.get("phone") or "").strip() or None

            errors: list[str] = []
            if not name:
                errors.append("Firma adı zorunludur.")
            if not city:
                errors.append("Şehir zorunludur.")
            if not sector:
                errors.append("Sektör zorunludur.")

            if errors:
                for err in errors:
                    flash(err, "danger")
                return render_template(
                    "firm/edit.html",
                    title="Firma Düzenle",
                    firm=firm,
                    form_data=request.form,
                )

            firm.name = name
            firm.city = city
            firm.sector = sector
            firm.description = description
            firm.phone = phone
            db.session.commit()

            flash("Firma bilgileri güncellendi.", "success")
            return redirect(url_for("firm_detail"))

        return render_template("firm/edit.html", title="Firma Düzenle", firm=firm, form_data={})

    @app.route("/listing/create", methods=["GET", "POST"])
    @login_required
    def create_listing():
        firm = Firm.query.filter_by(user_id=current_user.id).first()
        if not firm:
            flash("İlan açmadan önce firma bilgilerinizi oluşturmalısınız.", "warning")
            return redirect(url_for("firm_create"))

        if request.method == "POST":
            title = (request.form.get("title") or "").strip()
            description = (request.form.get("description") or "").strip()
            category = (request.form.get("category") or "").strip()
            quantity = (request.form.get("quantity") or "").strip()
            price_raw = (request.form.get("price") or "").strip()

            errors: list[str] = []
            if not title:
                errors.append("İlan başlığı zorunludur.")
            if not description:
                errors.append("Açıklama zorunludur.")
            if not category:
                errors.append("Kategori seçimi zorunludur.")
            if not quantity:
                errors.append("Miktar alanı zorunludur.")

            price_val = None
            if price_raw:
                try:
                    price_val = float(price_raw.replace(",", "."))
                except ValueError:
                    errors.append("Fiyat sayısal olmalıdır (örn: 1250 veya 1250,50).")

            if errors:
                for err in errors:
                    flash(err, "danger")
                return render_template(
                    "listings/create.html",
                    title="İlan Oluştur",
                    firm=firm,
                    form_data=request.form,
                )

            try:
                ai_result = analyze_listing_text(description)
                tags = ai_result.get("tags") or []
                tags_json = json.dumps(tags, ensure_ascii=False)

                new_listing = Listing(
                    firm_id=firm.id,
                    title=title,
                    description=description,
                    category=category,
                    quantity=quantity,
                    city=firm.city,  # MVP: ilan şehri firma şehrinden gelir
                    price=price_val,
                    status="Aktif",
                    created_at=datetime.utcnow(),
                    tags=tags_json,
                )
                db.session.add(new_listing)
                db.session.commit()

                flash("İlan başarıyla oluşturuldu.", "success")
                return redirect(url_for("listing_detail", listing_id=new_listing.id))
            except Exception:
                db.session.rollback()
                flash("İlan kaydedilirken bir hata oluştu. Lütfen tekrar deneyin.", "danger")

        return render_template(
            "listings/create.html",
            title="İlan Oluştur",
            firm=firm,
            form_data={},
        )

    @app.route("/listings")
    def listings():
        selected_category = request.args.get("kategori", "").strip()
        selected_city = request.args.get("sehir", "").strip()

        query = Listing.query
        if selected_category:
            query = query.filter_by(category=selected_category)
        if selected_city:
            query = query.filter(Listing.city.ilike(selected_city))

        all_listings = query.order_by(Listing.created_at.desc()).all()

        distinct_cities = db.session.query(Listing.city).distinct().order_by(Listing.city.asc()).all()
        city_list = [c[0] for c in distinct_cities if c[0]]

        return render_template(
            "listings/list.html",
            title="İlanlar",
            listings=all_listings,
            selected_category=selected_category,
            selected_city=selected_city,
            city_list=city_list,
        )

    @app.route("/listing/<int:listing_id>", methods=["GET", "POST"])
    def listing_detail(listing_id: int):
        listing = Listing.query.get(listing_id)
        if listing is None:
            abort(404)

        if request.method == "POST":
            if not current_user.is_authenticated:
                flash("Talep göndermek için giriş yapmalısınız.", "warning")
                return redirect(url_for("login", next=request.path))

            requester_firm = Firm.query.filter_by(user_id=current_user.id).first()
            if not requester_firm:
                flash("Talep göndermeden önce firma bilgilerinizi oluşturmalısınız.", "warning")
                return redirect(url_for("firm_create"))

            company_city = (request.form.get("company_city") or "").strip()
            message = (request.form.get("message") or "").strip()
            message_norm = " ".join(message.split())

            errors: list[str] = []
            if not company_city:
                errors.append("Firma şehri zorunludur.")
            if not message_norm:
                errors.append("Mesaj alanı zorunludur.")

            if errors:
                for err in errors:
                    flash(err, "danger")
            else:
                try:
                    recent = datetime.utcnow() - timedelta(seconds=90)
                    dup = (
                        ListingRequest.query.filter_by(
                            listing_id=listing.id,
                            user_id=current_user.id,
                            message=message_norm,
                        )
                        .filter(ListingRequest.created_at >= recent)
                        .first()
                    )
                    if dup:
                        flash("Bu talep az önce kaydedildi.", "info")
                        return redirect(url_for("listing_detail", listing_id=listing.id))

                    new_request = ListingRequest(
                        listing_id=listing.id,
                        user_id=current_user.id,
                        company_name=requester_firm.name,
                        company_email=(current_user.email or "").strip() or None,
                        company_city=company_city,
                        message=message_norm,
                        created_at=datetime.utcnow(),
                    )
                    db.session.add(new_request)
                    db.session.commit()
                    flash("Talebiniz başarıyla iletildi.", "success")
                    return redirect(url_for("listing_detail", listing_id=listing.id))
                except Exception:
                    db.session.rollback()
                    flash("Talep kaydedilirken bir hata oluştu. Lütfen tekrar deneyin.", "danger")

        requests_for_listing = (
            ListingRequest.query.filter_by(listing_id=listing.id)
            .options(joinedload(ListingRequest.requester).joinedload(User.firm))
            .order_by(ListingRequest.created_at.desc())
            .all()
        )

        analysis = analyze_listing_text(listing.description or "")
        similar_listings = recommend_similar_listings(
            listing,
            Listing.query.filter(Listing.id != listing.id, Listing.status == "Aktif").all(),
            limit=4,
        )

        analysis_suggestion = {
            "predicted_category": analysis.get("predicted_category", "Diğer"),
            "confidence": analysis.get("confidence", 0),
        }

        requester_firm = None
        if current_user.is_authenticated:
            requester_firm = Firm.query.filter_by(user_id=current_user.id).first()

        return render_template(
            "listings/detail.html",
            title=f"İlan Detayı - {listing.title}",
            listing=listing,
            requests_for_listing=requests_for_listing,
            analysis_suggestion=analysis_suggestion,
            analysis_tags=analysis.get("tags") or [],
            similar_listings=similar_listings,
            requester_firm=requester_firm,
        )

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)

