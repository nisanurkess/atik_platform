import os
import json
from datetime import datetime, timedelta

from app import create_app
from models import Firm, Listing, ListingRequest, User, db
from services.listing_analyzer import analyze_listing_text
from utils.auth_helpers import normalize_email

# Bu script, örnek firma, ilan ve talep verileri ekler.
# Tek seferlik değildir; tekrar çalıştırıldığında duplicate üretmemesi için
# var olan kayıtlar kontrol edilir.


def seed_data():
    app = create_app()
    with app.app_context():
        # Veritabanı dosyasının varlığından emin ol
        os.makedirs(app.instance_path, exist_ok=True)

        # Her ihtimale karşı tabloların varlığını kontrol et
        db.create_all()

        demo_password = "demo12345"

        demo_users = [
            {
                "email": "anadolu@demo.com",
                "full_name": "Anadolu Plastik Demo",
                "firm": {
                    "name": "Anadolu Plastik Sanayi A.Ş.",
                    "sector": "Plastik Üretimi",
                    "city": "İstanbul",
                    "description": "Temiz ve sınıflandırılmış plastik atık tedariki.",
                    "phone": "0212 000 00 00",
                },
            },
            {
                "email": "ege@demo.com",
                "full_name": "Ege Metal Demo",
                "firm": {
                    "name": "Ege Metal İşleme Ltd.",
                    "sector": "Metal İşleme",
                    "city": "İzmir",
                    "description": "Lazer kesim sonrası metal hurdaların değerlendirilmesi.",
                    "phone": "0232 000 00 00",
                },
            },
            {
                "email": "yesil@demo.com",
                "full_name": "Yeşil Dönüşüm Demo",
                "firm": {
                    "name": "Yeşil Geri Dönüşüm A.Ş.",
                    "sector": "Geri Dönüşüm",
                    "city": "Kocaeli",
                    "description": "Geri dönüşüm operasyonları ve malzeme hazırlığı.",
                    "phone": "0262 000 00 00",
                },
            },
            {
                "email": "marmara@demo.com",
                "full_name": "Marmara Tekstil Demo",
                "firm": {
                    "name": "Marmara Tekstil Fabrikası",
                    "sector": "Tekstil",
                    "city": "Bursa",
                    "description": "Tekstil parça atıklarının değerlendirilmesi.",
                    "phone": "0224 000 00 00",
                },
            },
            {
                "email": "pakambalaj@demo.com",
                "full_name": "Pak Ambalaj Demo",
                "firm": {
                    "name": "Pak Ambalaj Sanayi",
                    "sector": "Ambalaj",
                    "city": "Ankara",
                    "description": "Ambalaj atıklarının geri dönüşüme kazandırılması.",
                    "phone": "0312 000 00 00",
                },
            },
        ]

        user_by_email = {}
        for u in demo_users:
            em = normalize_email(u["email"])
            existing_user = User.query.filter_by(email=em).first()
            if not existing_user:
                existing_user = User(
                    full_name=u["full_name"],
                    email=em,
                )
                existing_user.set_password(demo_password)
                db.session.add(existing_user)
                db.session.commit()
            user_by_email[em] = existing_user

        # Firmaları tek kullanıcı tek firma kuralına göre ekle/güncelle
        firm_by_email = {}
        for u in demo_users:
            user = user_by_email[normalize_email(u["email"])]
            firm = Firm.query.filter_by(user_id=user.id).first()
            if not firm:
                firm = Firm(
                    user_id=user.id,
                    name=u["firm"]["name"],
                    sector=u["firm"]["sector"],
                    city=u["firm"]["city"],
                    description=u["firm"].get("description") or None,
                    phone=u["firm"].get("phone") or None,
                    created_at=datetime.utcnow() - timedelta(days=30),
                )
                db.session.add(firm)
                db.session.commit()
            firm_by_email[normalize_email(u["email"])] = firm

        # Demo ilanlar (firmalara bağlı olacak)
        demo_listings = [
            {
                "firm_email": "anadolu@demo.com",
                "title": "Renkli Plastik Granül Atığı",
                "description": "Üretim sürecinden çıkan, farklı renklerde plastik granül atıkları. Temiz ve sınıflandırılmış durumdadır.",
                "category": "Plastik",
                "quantity": "3 ton",
                "price": None,
                "created_at": datetime.utcnow() - timedelta(days=7),
            },
            {
                "firm_email": "ege@demo.com",
                "title": "Çelik Sac Kesim Artıkları",
                "description": "Lazer kesim sonrası oluşan çelik sac artıkları. Geri dönüşüm için uygundur.",
                "category": "Metal",
                "quantity": "5 ton",
                "price": None,
                "created_at": datetime.utcnow() - timedelta(days=6),
            },
            {
                "firm_email": "yesil@demo.com",
                "title": "Karton ve Kağıt Atığı",
                "description": "Ofis ve üretim hattından toplanan karışık karton ve kağıt atıkları.",
                "category": "Kağıt",
                "quantity": "2,5 ton",
                "price": None,
                "created_at": datetime.utcnow() - timedelta(days=5),
            },
            {
                "firm_email": "marmara@demo.com",
                "title": "Kumaş Parça Atıkları",
                "description": "Farklı renk ve türlerde tekstil kumaş parça atıkları. Dolgu ve yalıtım malzemesi yapımına uygundur.",
                "category": "Tekstil",
                "quantity": "1,2 ton",
                "price": None,
                "created_at": datetime.utcnow() - timedelta(days=4),
            },
            {
                "firm_email": "anadolu@demo.com",
                "title": "Şeffaf PET Şişe Atıkları",
                "description": "İçecek üretiminden çıkan temiz PET şişe atıkları. Sadece şeffaf malzeme.",
                "category": "Plastik",
                "quantity": "4 ton",
                "price": None,
                "created_at": datetime.utcnow() - timedelta(days=3),
            },
            {
                "firm_email": "pakambalaj@demo.com",
                "title": "Hasarlı Karton Kutular",
                "description": "Nakliye sırasında hasar gören ancak geri dönüşüme uygun karton kutular.",
                "category": "Kağıt",
                "quantity": "1 ton",
                "price": None,
                "created_at": datetime.utcnow() - timedelta(days=2),
            },
        ]

        for dl in demo_listings:
            firm = firm_by_email[dl["firm_email"]]
            exists = Listing.query.filter_by(firm_id=firm.id, title=dl["title"]).first()
            if exists:
                continue

            ai_result = analyze_listing_text(dl["description"] or "")
            tags = ai_result.get("tags") or []

            listing = Listing(
                firm_id=firm.id,
                title=dl["title"],
                description=dl["description"],
                category=dl["category"],
                quantity=dl["quantity"],
                city=firm.city,
                price=dl.get("price") or None,
                status="Aktif",
                created_at=dl["created_at"],
                tags=json.dumps(tags, ensure_ascii=False),
            )
            db.session.add(listing)

        db.session.commit()

        # Listeleme için yardımcı: tags boş kalanları güncelle
        updated_tags = 0
        for l in Listing.query.all():
            if not l.tags_list:
                ai_result = analyze_listing_text(l.description or "")
                tags = ai_result.get("tags") or []
                l.tags = json.dumps(tags, ensure_ascii=False)
                updated_tags += 1
        db.session.commit()

        # Demo talepler (isteğe bağlı; tekrar çalıştırıldığında duplicate olmasın)
        pet_listing = Listing.query.filter_by(
            title="Şeffaf PET Şişe Atıkları",
            firm_id=firm_by_email["anadolu@demo.com"].id,
        ).first()
        if pet_listing:
            demo_requests = [
                {
                    "listing_id": pet_listing.id,
                    "company_name": "PET Dönüşüm Merkezi",
                    "company_city": "İstanbul",
                    "message": "Şeffaf PET atıklarınız için kg başı fiyat teklifi sunmak isteriz.",
                    "created_at": datetime.utcnow() - timedelta(days=1, hours=3),
                },
            ]

            for dr in demo_requests:
                exists = ListingRequest.query.filter_by(
                    listing_id=dr["listing_id"],
                    company_name=dr["company_name"],
                    message=dr["message"],
                ).first()
                if exists:
                    continue

                req = ListingRequest(
                    listing_id=dr["listing_id"],
                    company_name=dr["company_name"],
                    company_city=dr["company_city"],
                    message=dr["message"],
                    created_at=dr["created_at"],
                )
                db.session.add(req)

            db.session.commit()

        print(f"Seed tamamlandı. Etiket güncellemeleri: {updated_tags}")


if __name__ == "__main__":
    seed_data()

