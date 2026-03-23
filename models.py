from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Company(db.Model):
    __tablename__ = "companies"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    sector = db.Column(db.String(200), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    listings = db.relationship("Listing", backref="company", lazy=True)

    def __repr__(self):
        return f"<Company {self.name}>"


class Listing(db.Model):
    __tablename__ = "listings"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(
        db.Integer, db.ForeignKey("companies.id"), nullable=False
    )
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), default="Aktif", nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    requests = db.relationship("ListingRequest", backref="listing", lazy=True)

    def __repr__(self):
        return f"<Listing {self.title}>"


class ListingRequest(db.Model):
    __tablename__ = "requests"

    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(
        db.Integer, db.ForeignKey("listings.id"), nullable=False
    )
    company_name = db.Column(db.String(200), nullable=False)
    company_city = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Request {self.company_name} - Listing {self.listing_id}>"

