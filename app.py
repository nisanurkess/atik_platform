import os
import json
from datetime import datetime

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    abort,
    jsonify,
)

from models import db, Company, Listing, ListingRequest
from services.listing_analyzer import analyze_listing_text
from services.recommender import recommend_similar_listings

from sqlalchemy import text as sql_text

# Sabit kategori listesi
CATEGORIES = [
    "Plastik",
    "Metal",
    "Kağıt",
    "Cam",
    "Organik",
    "Tekstil",
    "Elektronik",
    "Kimyasal",
    "Diğer",
]


def create_app():
    app = Flask(__name__, instance_relative_config=True)

    # Basit ve anlaşılır konfigürasyon
    app.config["SECRET_KEY"] = "çok-gizli-olmayan-bir-anahtar"
    # instance/database.db konumunda SQLite dosyası
    os.makedirs(app.instance_path, exist_ok=True)
    db_path = os.path.join(app.instance_path, "database.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    # Tablo oluşturma
    with app.app_context():
        db.create_all()
        # Yeni alan eklediğimiz durumlarda (ör: `tags`), Flask-SQLAlchemy mevcut tabloyu
        # otomatik ALTER etmez. SQLite üzerinde basit kolon kontrolü yapıyoruz.
        try:
            cols = [
                row[1]
                for row in db.session.execute(
                    sql_text("PRAGMA table_info(listings)")
                ).fetchall()
            ]
            if "tags" not in cols:
                db.session.execute(
                    sql_text("ALTER TABLE listings ADD COLUMN tags TEXT")
                )
                db.session.commit()
        except Exception:
            # Uygulama çalışsın diye şema kontrol hatasını yutuyoruz.
            # DB tarafında sorun olursa isteklerde hata göreceksiniz.
            pass

    # Kategorileri tüm şablonlara otomatik gönder
    @app.context_processor
    def inject_globals():
        return {"CATEGORIES": CATEGORIES}

    @app.route("/ai/analyze", methods=["POST"])
    def ai_analyze_listing_text():
        payload = request.get_json(silent=True) or {}
        description = (payload.get("description") or "").strip()

        if not description:
            return jsonify(
                {"predicted_category": "Diğer", "confidence": 0, "tags": []}
            )

        result = analyze_listing_text(description)
        return jsonify(result)

    # 404 için kullanıcı dostu bir sayfa
    @app.errorhandler(404)
    def page_not_found(e):
        return (
            render_template(
                "404.html",
                title="Sayfa Bulunamadı",
                message="İstediğiniz ilan veya sayfa bulunamadı.",
            ),
            404,
        )

    # Ana sayfa
    @app.route("/")
    def index():
        total_listings = Listing.query.count()
        active_listings = Listing.query.filter_by(status="Aktif").count()
        company_count = Company.query.count()
        latest_listings = (
            Listing.query.order_by(Listing.created_at.desc()).limit(5).all()
        )

        return render_template(
            "index.html",
            title="Atık Değişim Platformu",
            total_listings=total_listings,
            active_listings=active_listings,
            company_count=company_count,
            latest_listings=latest_listings,
        )

    # İlan oluşturma
    @app.route("/listing/create", methods=["GET", "POST"])
    def create_listing():
        companies = Company.query.order_by(Company.name.asc()).all()

        if not companies:
            flash(
                "Önce en az bir firma kaydı oluşturmalısınız. (seed.py ile örnek verileri yükleyebilirsiniz.)",
                "warning",
            )

        if request.method == "POST":
            company_id = request.form.get("company_id")
            title = request.form.get("title", "").strip()
            description = request.form.get("description", "").strip()
            category = request.form.get("category", "").strip()
            quantity = request.form.get("quantity", "").strip()
            city = request.form.get("city", "").strip()

            errors = []

            if not company_id:
                errors.append("Firma seçimi zorunludur.")
            if not title:
                errors.append("İlan başlığı zorunludur.")
            if not description:
                errors.append("Açıklama zorunludur.")
            if not category:
                errors.append("Kategori seçimi zorunludur.")
            if not quantity:
                errors.append("Miktar alanı zorunludur.")
            if not city:
                errors.append("Şehir alanı zorunludur.")

            # Firma gerçekten var mı kontrolü
            company = None
            if company_id:
                try:
                    company = Company.query.get(int(company_id))
                except ValueError:
                    company = None
                if company is None:
                    errors.append("Seçilen firma bulunamadı.")

            if errors:
                for err in errors:
                    flash(err, "danger")
                return render_template(
                    "create_listing.html",
                    title="İlan Oluştur",
                    companies=companies,
                    form_data=request.form,
                )

            try:
                ai_result = analyze_listing_text(description)
                tags = ai_result.get("tags") or []
                tags_json = json.dumps(tags, ensure_ascii=False)

                new_listing = Listing(
                    company_id=company.id,
                    title=title,
                    description=description,
                    category=category,
                    quantity=quantity,
                    city=city,
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
                flash(
                    "İlan kaydedilirken bir hata oluştu. Lütfen tekrar deneyin.",
                    "danger",
                )

        return render_template(
            "create_listing.html",
            title="İlan Oluştur",
            companies=companies,
            form_data={},
        )

    # İlan listeleme ve filtreleme
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

        # Şehir filtre dropdown'ı için mevcut şehirleri listele
        distinct_cities = (
            db.session.query(Listing.city)
            .distinct()
            .order_by(Listing.city.asc())
            .all()
        )
        city_list = [c[0] for c in distinct_cities if c[0]]

        return render_template(
            "listings.html",
            title="İlanlar",
            listings=all_listings,
            selected_category=selected_category,
            selected_city=selected_city,
            city_list=city_list,
        )

    # İlan detay ve talep gönderme
    @app.route("/listing/<int:listing_id>", methods=["GET", "POST"])
    def listing_detail(listing_id):
        listing = Listing.query.get(listing_id)
        if listing is None:
            abort(404)

        if request.method == "POST":
            company_name = request.form.get("company_name", "").strip()
            company_city = request.form.get("company_city", "").strip()
            message = request.form.get("message", "").strip()

            errors = []
            if not company_name:
                errors.append("Firma adı zorunludur.")
            if not company_city:
                errors.append("Firma şehri zorunludur.")
            if not message:
                errors.append("Mesaj alanı zorunludur.")

            if errors:
                for err in errors:
                    flash(err, "danger")
            else:
                try:
                    new_request = ListingRequest(
                        listing_id=listing.id,
                        company_name=company_name,
                        company_city=company_city,
                        message=message,
                        created_at=datetime.utcnow(),
                    )
                    db.session.add(new_request)
                    db.session.commit()
                    flash("Talebiniz başarıyla iletildi.", "success")
                    return redirect(
                        url_for("listing_detail", listing_id=listing.id)
                    )
                except Exception:
                    db.session.rollback()
                    flash(
                        "Talep kaydedilirken bir hata oluştu. Lütfen tekrar deneyin.",
                        "danger",
                    )

        requests_for_listing = (
            ListingRequest.query.filter_by(listing_id=listing.id)
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

        return render_template(
            "listing_detail.html",
            title=f"İlan Detayı - {listing.title}",
            listing=listing,
            requests_for_listing=requests_for_listing,
            analysis_suggestion=analysis_suggestion,
            analysis_tags=analysis.get("tags") or [],
            similar_listings=similar_listings,
        )

    return app


app = create_app()

if __name__ == "__main__":
    # Windows ortamında doğrudan çalıştırılabilir
    app.run(debug=True)

