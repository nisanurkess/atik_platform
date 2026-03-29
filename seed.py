import os
import json
from datetime import datetime, timedelta

from app import create_app, dedupe_listing_request_bursts
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
            {
                "email": "dogageri@demo.com",
                "full_name": "Doğa Geri Kazanım Temsilcisi",
                "firm": {
                    "name": "Doğa Geri Kazanım Ltd.",
                    "sector": "Geri Dönüşüm",
                    "city": "İstanbul",
                    "description": "Plastik ve granül atıklarının düzenli tedariki.",
                    "phone": "0212 100 20 30",
                },
            },
            {
                "email": "ankametal@demo.com",
                "full_name": "Anka Metal Temsilcisi",
                "firm": {
                    "name": "Anka Metal Geri Dönüşüm",
                    "sector": "Metal Geri Dönüşüm",
                    "city": "Kocaeli",
                    "description": "Çelik ve sac artıklarının yerinde değerlendirilmesi.",
                    "phone": "0262 200 30 40",
                },
            },
            {
                "email": "ekokagit@demo.com",
                "full_name": "Eko Kağıt Temsilcisi",
                "firm": {
                    "name": "Eko Kağıt Sanayi",
                    "sector": "Kağıt",
                    "city": "Ankara",
                    "description": "Karton ve kağıt atığı tedariki.",
                    "phone": "0312 300 40 50",
                },
            },
            {
                "email": "tekno@demo.com",
                "full_name": "Tekno Geri Dönüşüm Temsilcisi",
                "firm": {
                    "name": "Tekno Geri Dönüşüm",
                    "sector": "Elektronik Atık",
                    "city": "İzmir",
                    "description": "Elektronik kart ve metal geri kazanımı.",
                    "phone": "0232 400 50 60",
                },
            },
            {
                "email": "pet@demo.com",
                "full_name": "PET Dönüşüm Demo",
                "firm": {
                    "name": "PET Dönüşüm Merkezi",
                    "sector": "Geri Dönüşüm",
                    "city": "İstanbul",
                    "description": "PET plastik atıklarının toplanması ve değerlendirilmesi.",
                    "phone": "0212 000 00 01",
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
                "firm_email": "ege@demo.com",
                "title": "Elektronik Kart Atıkları",
                "description": "Üretim hattından çıkan bozuk ve kullanılmayan elektronik kart ve PCB atıkları.",
                "category": "Metal",
                "quantity": "800 kg",
                "price": None,
                "created_at": datetime.utcnow() - timedelta(days=7),
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

        # Demo talepler (user_id + firma; tekrar çalıştırıldığında aynı kayıt iki kez eklenmez)
        def _find_listing(seller_email: str, title: str):
            fe = normalize_email(seller_email)
            firm = firm_by_email.get(fe)
            if not firm:
                return None
            return Listing.query.filter_by(firm_id=firm.id, title=title).first()

        demo_request_specs: list[tuple[str, str, str, str, str, datetime]] = [
            (
                "anadolu@demo.com",
                "Renkli Plastik Granül Atığı",
                "dogageri@demo.com",
                "İstanbul",
                "Plastik granülleri düzenli olarak alabiliriz. Aylık minimum 2 ton talebimiz var.",
                datetime(2026, 3, 16, 11, 22),
            ),
            (
                "ege@demo.com",
                "Çelik Sac Kesim Artıkları",
                "ankametal@demo.com",
                "Kocaeli",
                "Çelik sac artıklarını yerinde görüp teklif vermek isteriz.",
                datetime(2026, 3, 17, 6, 22),
            ),
            (
                "pakambalaj@demo.com",
                "Hasarlı Karton Kutular",
                "ekokagit@demo.com",
                "Ankara",
                "Düzenli karton ve kağıt atığı tedariki arıyoruz. Uzun vadeli iş birliği için iletişime geçebilir miyiz?",
                datetime(2026, 3, 17, 11, 22),
            ),
            (
                "anadolu@demo.com",
                "Şeffaf PET Şişe Atıkları",
                "pet@demo.com",
                "İstanbul",
                "Şeffaf PET atıklarınız için kg başı fiyat teklifi sunmak isteriz",
                datetime(2026, 3, 18, 8, 22),
            ),
            (
                "ege@demo.com",
                "Elektronik Kart Atıkları",
                "tekno@demo.com",
                "İzmir",
                "Elektronik kart atıklarını parçalayarak metal geri kazanımı yapıyoruz. Yerinde inceleme talep ediyoruz.",
                datetime(2026, 3, 19, 1, 22),
            ),
            (
                "anadolu@demo.com",
                "Şeffaf PET Şişe Atıkları",
                "pet@demo.com",
                "İstanbul",
                "Şeffaf PET atıklarınız için kg başı fiyat teklifi sunmak isteriz.",
                datetime(2026, 3, 25, 10, 8),
            ),
        ]

        for seller_em, title, buyer_em, city, msg, created in demo_request_specs:
            listing = _find_listing(seller_em, title)
            bu = user_by_email.get(normalize_email(buyer_em))
            bf = firm_by_email.get(normalize_email(buyer_em))
            if not listing or not bu or not bf:
                continue
            msg_norm = " ".join(msg.split())
            exists = ListingRequest.query.filter_by(
                listing_id=listing.id,
                user_id=bu.id,
                message=msg_norm,
            ).first()
            if exists:
                if exists.company_email != normalize_email(buyer_em) or exists.user_id != bu.id:
                    exists.company_email = normalize_email(buyer_em)
                    exists.user_id = bu.id
                    exists.company_name = bf.name
                continue

            db.session.add(
                ListingRequest(
                    listing_id=listing.id,
                    user_id=bu.id,
                    company_name=bf.name,
                    company_email=normalize_email(buyer_em),
                    company_city=city,
                    message=msg_norm,
                    created_at=created,
                )
            )
        db.session.commit()

        # Eski satırlar: company_email ile user_id eşitle (PET vb.)
        for lr in ListingRequest.query.filter(ListingRequest.user_id.is_(None)).all():
            if lr.company_email:
                u = User.query.filter_by(email=normalize_email(lr.company_email)).first()
                if u:
                    lr.user_id = u.id
        db.session.commit()

        dedupe_listing_request_bursts()

        print(f"Seed tamamlandı. Etiket güncellemeleri: {updated_tags}")


if __name__ == "__main__":
    seed_data()

