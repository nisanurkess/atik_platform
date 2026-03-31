from __future__ import annotations

from datetime import datetime
import json

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Tek kullanıcı = tek firma (MVP kuralı)
    firm = db.relationship("Firm", backref="user", uselist=False, lazy=True)
    listing_requests = db.relationship(
        "ListingRequest",
        back_populates="requester",
        lazy=True,
    )

    def set_password(self, password: str) -> None:
        # scrypt: Werkzeug 3 varsayılanı; pbkdf2 ile üretilmiş eski kayıtlar da check_password_hash ile doğrulanır
        self.password_hash = generate_password_hash(password, method="scrypt")

    def check_password(self, password: str) -> bool:
        h = self.password_hash or ""
        if not h:
            return False
        try:
            return check_password_hash(h, password)
        except (ValueError, TypeError):
            return False

    def __repr__(self) -> str:
        return f"<User {self.email}>"


class Firm(db.Model):
    """
    Mevcut projedeki `companies` tablosunu bozmadan yeni MVP mantığına uyarlıyoruz.
    - companies -> firms/Firm (ORM adı)
    - eski kolonlar korunur (name/sector/city)
    - yeni kolonlar (user_id/description/phone) eğer yoksa runtime eklenir
    """

    __tablename__ = "companies"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, unique=True)

    name = db.Column(db.String(200), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    sector = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    phone = db.Column(db.String(50), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    listings = db.relationship("Listing", backref="firm", lazy=True)

    def __repr__(self) -> str:
        return f"<Firm {self.name}>"


class Listing(db.Model):
    __tablename__ = "listings"

    id = db.Column(db.Integer, primary_key=True)

    # DB'de eski şemada kolon adı `company_id` idi. SQLite verisini bozmamak için
    # ORM tarafında bunu `firm_id` olarak expose ediyoruz.
    firm_id = db.Column(
        "company_id",
        db.Integer,
        db.ForeignKey("companies.id"),
        nullable=False,
    )

    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.String(100), nullable=False)

    # MVP'de ilan şehri firmadan otomatik doldurulacak; ama şemayı bozmayıp alanı koruyoruz.
    city = db.Column(db.String(100), nullable=False)

    price = db.Column(db.Float, nullable=True)

    status = db.Column(db.String(50), default="Aktif", nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    tags = db.Column(db.Text, nullable=True)

    requests = db.relationship("ListingRequest", backref="listing", lazy=True)

    def __repr__(self) -> str:
        return f"<Listing {self.title}>"

    # Geriye dönük uyumluluk: eski şablonlar `listing.company` bekliyor olabilirdi.
    @property
    def company(self) -> Firm | None:
        return getattr(self, "firm", None)

    @property
    def tags_list(self) -> list[str]:
        """
        DB'de `tags` alanı farklı formatlarda kalmış olabileceği için (erken sürümler)
        hem JSON hem de CSV benzeri basit formatleri destekler.
        """

        if not getattr(self, "tags", None):
            return []

        raw = self.tags.strip()
        if not raw:
            return []

        # Muhtemel format 1: JSON array
        if raw.startswith("["):
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    return [str(x) for x in parsed if str(x).strip()]
            except Exception:
                pass

        # Muhtemel format 2: virgülle ayrılmış
        if "," in raw:
            parts = [p.strip() for p in raw.split(",")]
            return [p for p in parts if p]

        # Muhtemel format 3: '|' ayrılmış
        if "|" in raw:
            parts = [p.strip() for p in raw.split("|")]
            return [p for p in parts if p]

        return [raw]


class ListingRequest(db.Model):
    __tablename__ = "requests"

    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, db.ForeignKey("listings.id"), nullable=False)
    # Talep sahibi hesap; e-posta ve firma adı gösterimi bu ilişki üzerinden doğrulanır.
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    company_name = db.Column(db.String(200), nullable=False)
    company_email = db.Column(db.String(200), nullable=True)
    company_city = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    requester = db.relationship(
        "User",
        back_populates="listing_requests",
        foreign_keys=[user_id],
    )

    @property
    def display_company_name(self) -> str:
        """Talebi oluşturan hesabın firması; user_id yoksa eski company_name."""
        u = self.requester
        if u is not None:
            f = getattr(u, "firm", None)
            if f is not None and getattr(f, "name", None):
                return str(f.name).strip()
        return (self.company_name or "").strip() or "—"

    @property
    def display_email(self) -> str:
        """Talebi oluşturan hesabın e-postası; oturumdaki kullanıcıya göre değişmez."""
        u = self.requester
        if u is not None and getattr(u, "email", None):
            return str(u.email).strip()
        return (self.company_email or "").strip()

    def __repr__(self) -> str:
        return f"<Request {self.company_name} - Listing {self.listing_id}>"

