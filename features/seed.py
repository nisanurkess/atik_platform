import json
from datetime import datetime, timedelta

from app import create_app, dedupe_listing_request_bursts
from models import Firm, Listing, ListingRequest, User, db
from utils.auth_helpers import normalize_email

# Bu script idempotent demo veri yukler.
# Her calistirmada hedef kayitlarin varligini garanti eder, duplicate olusturmaz.


def seed_data():
    app = create_app()
    with app.app_context():
        db.create_all()

        demo_password = "demo12345"
        demo_users = [
            {
                "email": "anadolu@demo.com",
                "full_name": "Anadolu Plastik Demo",
                "firm": {
                    "name": "Anadolu Plastik Sanayi AS",
                    "sector": "Plastik Uretimi",
                    "city": "Istanbul",
                    "description": "Temiz ve siniflandirilmis plastik atik tedariki.",
                    "phone": "0212 000 00 00",
                },
            },
            {
                "email": "ege@demo.com",
                "full_name": "Ege Metal Demo",
                "firm": {
                    "name": "Ege Metal Isleme Ltd",
                    "sector": "Metal Isleme",
                    "city": "Izmir",
                    "description": "Lazer kesim sonrasi metal hurdalarin degerlendirilmesi.",
                    "phone": "0232 000 00 00",
                },
            },
            {
                "email": "yesil@demo.com",
                "full_name": "Yesil Donusum Demo",
                "firm": {
                    "name": "Yesil Geri Donusum AS",
                    "sector": "Geri Donusum",
                    "city": "Kocaeli",
                    "description": "Geri donusum operasyonlari ve malzeme hazirligi.",
                    "phone": "0262 000 00 00",
                },
            },
            {
                "email": "marmara@demo.com",
                "full_name": "Marmara Tekstil Demo",
                "firm": {
                    "name": "Marmara Tekstil Fabrikasi",
                    "sector": "Tekstil",
                    "city": "Bursa",
                    "description": "Tekstil parca atiklarinin degerlendirilmesi.",
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
                    "description": "Ambalaj atiklarinin geri donusume kazandirilmasi.",
                    "phone": "0312 000 00 00",
                },
            },
            {
                "email": "dogageri@demo.com",
                "full_name": "Doga Geri Kazanim Temsilcisi",
                "firm": {
                    "name": "Doga Geri Kazanim Ltd",
                    "sector": "Geri Donusum",
                    "city": "Istanbul",
                    "description": "Plastik ve granul atiklarinin duzenli tedariki.",
                    "phone": "0212 100 20 30",
                },
            },
            {
                "email": "ankametal@demo.com",
                "full_name": "Anka Metal Temsilcisi",
                "firm": {
                    "name": "Anka Metal Geri Donusum",
                    "sector": "Metal Geri Donusum",
                    "city": "Kocaeli",
                    "description": "Celik ve sac artiklarinin yerinde degerlendirilmesi.",
                    "phone": "0262 200 30 40",
                },
            },
            {
                "email": "ekokagit@demo.com",
                "full_name": "Eko Kagit Temsilcisi",
                "firm": {
                    "name": "Eko Kagit Sanayi",
                    "sector": "Kagit",
                    "city": "Ankara",
                    "description": "Karton ve kagit atigi tedariki.",
                    "phone": "0312 300 40 50",
                },
            },
            {
                "email": "tekno@demo.com",
                "full_name": "Tekno Geri Donusum Temsilcisi",
                "firm": {
                    "name": "Tekno Geri Donusum",
                    "sector": "Elektronik Atik",
                    "city": "Izmir",
                    "description": "Elektronik kart ve metal geri kazanimi.",
                    "phone": "0232 400 50 60",
                },
            },
            {
                "email": "pet@demo.com",
                "full_name": "PET Donusum Demo",
                "firm": {
                    "name": "PET Donusum Merkezi",
                    "sector": "Geri Donusum",
                    "city": "Istanbul",
                    "description": "PET plastik atiklarinin toplanmasi ve degerlendirilmesi.",
                    "phone": "0212 000 00 01",
                },
            },
            {
                "email": "adeniz@demo.com",
                "full_name": "Akdeniz Kimya Demo",
                "firm": {
                    "name": "Akdeniz Kimya",
                    "sector": "Kimya",
                    "city": "Adana",
                    "description": "Ambalaj ve plastik bazli atik ayristirma.",
                    "phone": "0322 111 22 33",
                },
            },
            {
                "email": "karadeniz@demo.com",
                "full_name": "Karadeniz Ahsap Demo",
                "firm": {
                    "name": "Karadeniz Ahsap",
                    "sector": "Mobilya",
                    "city": "Samsun",
                    "description": "Ahsap ve talaş atiklarinin geri kazanimina odakli.",
                    "phone": "0362 222 33 44",
                },
            },
            {
                "email": "icadolu@demo.com",
                "full_name": "Ic Anadolu Cam Demo",
                "firm": {
                    "name": "Ic Anadolu Cam",
                    "sector": "Cam",
                    "city": "Eskisehir",
                    "description": "Cam kirigi ve uretim firelerinin geri donusumu.",
                    "phone": "0222 333 44 55",
                },
            },
            {
                "email": "egepetrokimya@demo.com",
                "full_name": "Ege Petrokimya Demo",
                "firm": {
                    "name": "Ege Petrokimya",
                    "sector": "Petrokimya",
                    "city": "Aliaga",
                    "description": "Endustriyel atik ayrimi ve lojistigi.",
                    "phone": "0232 444 55 66",
                },
            },
            {
                "email": "trakyalojistik@demo.com",
                "full_name": "Trakya Lojistik Demo",
                "firm": {
                    "name": "Trakya Lojistik",
                    "sector": "Lojistik",
                    "city": "Tekirdag",
                    "description": "Atik toplama ve sevkiyat operasyonlari.",
                    "phone": "0282 555 66 77",
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
            else:
                # Demo hesaplari guncel profile sahip olsun.
                existing_user.full_name = u["full_name"]
            user_by_email[em] = existing_user
        db.session.commit()

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
            else:
                firm.name = u["firm"]["name"]
                firm.sector = u["firm"]["sector"]
                firm.city = u["firm"]["city"]
                firm.description = u["firm"].get("description") or None
                firm.phone = u["firm"].get("phone") or None
            firm_by_email[normalize_email(u["email"])] = firm
        db.session.commit()

        # 13 demo ilan
        demo_listings = [
            {
                "firm_email": "anadolu@demo.com",
                "title": "Renkli Plastik Granul Atigi",
                "description": "Uretim surecinden cikan farkli renklerde plastik granul atiklari.",
                "category": "Plastik",
                "quantity": "3 ton",
                "price": None,
                "created_at": datetime(2026, 3, 10, 9, 0),
            },
            {
                "firm_email": "ege@demo.com",
                "title": "Celik Sac Kesim Artiklari",
                "description": "Lazer kesim sonrasi olusan celik sac artiklari.",
                "category": "Metal",
                "quantity": "5 ton",
                "price": None,
                "created_at": datetime(2026, 3, 11, 10, 0),
            },
            {
                "firm_email": "ege@demo.com",
                "title": "Elektronik Kart Atiklari",
                "description": "Uretim hattindan cikan bozuk elektronik kart ve PCB atiklari.",
                "category": "Metal",
                "quantity": "800 kg",
                "price": None,
                "created_at": datetime(2026, 3, 12, 11, 0),
            },
            {
                "firm_email": "yesil@demo.com",
                "title": "Karton ve Kagit Atigi",
                "description": "Ofis ve uretim hattindan toplanan karisik karton ve kagit atiklari.",
                "category": "Kagit",
                "quantity": "2,5 ton",
                "price": None,
                "created_at": datetime(2026, 3, 13, 12, 0),
            },
            {
                "firm_email": "marmara@demo.com",
                "title": "Kumas Parca Atiklari",
                "description": "Farkli renk ve turlerde tekstil kumas parca atiklari.",
                "category": "Tekstil",
                "quantity": "1,2 ton",
                "price": None,
                "created_at": datetime(2026, 3, 14, 13, 0),
            },
            {
                "firm_email": "anadolu@demo.com",
                "title": "Seffaf PET Sise Atiklari",
                "description": "Icecek uretiminden cikan temiz PET sise atiklari.",
                "category": "Plastik",
                "quantity": "4 ton",
                "price": None,
                "created_at": datetime(2026, 3, 15, 14, 0),
            },
            {
                "firm_email": "pakambalaj@demo.com",
                "title": "Hasarli Karton Kutular",
                "description": "Nakliye sirasinda hasar goren geri donusume uygun karton kutular.",
                "category": "Kagit",
                "quantity": "1 ton",
                "price": None,
                "created_at": datetime(2026, 3, 16, 15, 0),
            },
            {
                "firm_email": "adeniz@demo.com",
                "title": "Polietilen Ambalaj Firesi",
                "description": "Temizlenmis ve ayrilmis PE ambalaj fireleri.",
                "category": "Plastik",
                "quantity": "2 ton",
                "price": None,
                "created_at": datetime(2026, 3, 17, 10, 15),
            },
            {
                "firm_email": "karadeniz@demo.com",
                "title": "Ahsap Talaş Atigi",
                "description": "Mobilya uretiminden kalan kuru ahsap talaslari.",
                "category": "Diger",
                "quantity": "900 kg",
                "price": None,
                "created_at": datetime(2026, 3, 18, 11, 20),
            },
            {
                "firm_email": "icadolu@demo.com",
                "title": "Cam Kirigi Atigi",
                "description": "Renksiz cam kirigi atiklari, geri donusume uygun.",
                "category": "Diger",
                "quantity": "1.4 ton",
                "price": None,
                "created_at": datetime(2026, 3, 19, 12, 25),
            },
            {
                "firm_email": "egepetrokimya@demo.com",
                "title": "Endustriyel Plastik Hurda",
                "description": "Petrokimya hatlarindan cikan siniflandirilmis plastik hurdalar.",
                "category": "Plastik",
                "quantity": "6 ton",
                "price": None,
                "created_at": datetime(2026, 3, 20, 13, 30),
            },
            {
                "firm_email": "trakyalojistik@demo.com",
                "title": "Karisik Ambalaj Atigi",
                "description": "Toplama merkezinden gelen ayrilmamis ambalaj atiklari.",
                "category": "Ambalaj",
                "quantity": "2.2 ton",
                "price": None,
                "created_at": datetime(2026, 3, 21, 14, 35),
            },
            {
                "firm_email": "yesil@demo.com",
                "title": "Aluminyum Kutu Presi",
                "description": "Preslenmis aluminyum kutu atiklari.",
                "category": "Metal",
                "quantity": "1.1 ton",
                "price": None,
                "created_at": datetime(2026, 3, 22, 15, 40),
            },
        ]

        for dl in demo_listings:
            firm = firm_by_email[normalize_email(dl["firm_email"])]
            exists = Listing.query.filter_by(firm_id=firm.id, title=dl["title"]).first()
            base_tags = [dl["category"], "demo"]
            tags_json = json.dumps(base_tags, ensure_ascii=False)

            if not exists:
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
                    tags=tags_json,
                )
                db.session.add(listing)
            else:
                exists.description = dl["description"]
                exists.category = dl["category"]
                exists.quantity = dl["quantity"]
                exists.city = firm.city
                exists.price = dl.get("price") or None
                exists.status = "Aktif"
                if not exists.tags:
                    exists.tags = tags_json

        db.session.commit()

        # Demo talepler: toplam 14 kayit
        def _find_listing(seller_email: str, title: str):
            fe = normalize_email(seller_email)
            firm = firm_by_email.get(fe)
            if not firm:
                return None
            return Listing.query.filter_by(firm_id=firm.id, title=title).first()

        demo_request_specs: list[tuple[str, str, str, str, str, datetime]] = [
            (
                "anadolu@demo.com",
                "Renkli Plastik Granul Atigi",
                "dogageri@demo.com",
                "Istanbul",
                "Plastik granulleri duzenli olarak alabiliriz.",
                datetime(2026, 3, 16, 11, 22),
            ),
            (
                "ege@demo.com",
                "Celik Sac Kesim Artiklari",
                "ankametal@demo.com",
                "Kocaeli",
                "Celik sac artiklarini yerinde gorup teklif vermek isteriz.",
                datetime(2026, 3, 17, 6, 22),
            ),
            (
                "pakambalaj@demo.com",
                "Hasarli Karton Kutular",
                "ekokagit@demo.com",
                "Ankara",
                "Duzenli karton ve kagit atigi tedariki ariyoruz.",
                datetime(2026, 3, 17, 11, 22),
            ),
            (
                "anadolu@demo.com",
                "Seffaf PET Sise Atiklari",
                "pet@demo.com",
                "Istanbul",
                "Seffaf PET atiklariniz icin kg bazli teklif verebiliriz.",
                datetime(2026, 3, 18, 8, 22),
            ),
            (
                "ege@demo.com",
                "Elektronik Kart Atiklari",
                "tekno@demo.com",
                "Izmir",
                "Elektronik kart atiklari icin yerinde inceleme talep ediyoruz.",
                datetime(2026, 3, 19, 1, 22),
            ),
            (
                "anadolu@demo.com",
                "Seffaf PET Sise Atiklari",
                "pet@demo.com",
                "Istanbul",
                "Seffaf PET atiklari icin ikinci parti teklifimiz hazir.",
                datetime(2026, 3, 25, 10, 8),
            ),
            (
                "yesil@demo.com",
                "Karton ve Kagit Atigi",
                "ekokagit@demo.com",
                "Ankara",
                "Aylik alim plani icin miktar teyidi rica ederiz.",
                datetime(2026, 3, 20, 9, 11),
            ),
            (
                "marmara@demo.com",
                "Kumas Parca Atiklari",
                "dogageri@demo.com",
                "Istanbul",
                "Tekstil parca atiklari icin duzenli alim yapabiliriz.",
                datetime(2026, 3, 20, 10, 22),
            ),
            (
                "adeniz@demo.com",
                "Polietilen Ambalaj Firesi",
                "anadolu@demo.com",
                "Istanbul",
                "PE fireleri icin lojistik plan cikarabiliriz.",
                datetime(2026, 3, 21, 11, 33),
            ),
            (
                "karadeniz@demo.com",
                "Ahsap Talaş Atigi",
                "trakyalojistik@demo.com",
                "Tekirdag",
                "Ahsap atigi tasima ve depolama teklifi iletebiliriz.",
                datetime(2026, 3, 21, 12, 44),
            ),
            (
                "icadolu@demo.com",
                "Cam Kirigi Atigi",
                "yesil@demo.com",
                "Kocaeli",
                "Cam kirigi aliminda duzenli kontrat dusunuyoruz.",
                datetime(2026, 3, 22, 13, 55),
            ),
            (
                "egepetrokimya@demo.com",
                "Endustriyel Plastik Hurda",
                "dogageri@demo.com",
                "Istanbul",
                "6 tonluk parti icin fiyat teklifi bekliyoruz.",
                datetime(2026, 3, 22, 14, 6),
            ),
            (
                "trakyalojistik@demo.com",
                "Karisik Ambalaj Atigi",
                "pakambalaj@demo.com",
                "Ankara",
                "Ayrim sonrasi alim icin test sevkiyati yapalim.",
                datetime(2026, 3, 23, 15, 7),
            ),
            (
                "yesil@demo.com",
                "Aluminyum Kutu Presi",
                "ankametal@demo.com",
                "Kocaeli",
                "Aluminyum pres atiklari icin haftalik alim mumkun.",
                datetime(2026, 3, 24, 16, 18),
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
                exists.company_email = normalize_email(buyer_em)
                exists.user_id = bu.id
                exists.company_name = bf.name
                exists.company_city = city
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

        # Eski satirlar: company_email ile user_id esitle
        for lr in ListingRequest.query.filter(ListingRequest.user_id.is_(None)).all():
            if lr.company_email:
                u = User.query.filter_by(email=normalize_email(lr.company_email)).first()
                if u:
                    lr.user_id = u.id
        db.session.commit()

        dedupe_listing_request_bursts()

        print(
            "Seed tamamlandi. "
            f"Firma: {Firm.query.count()}, "
            f"Ilan: {Listing.query.count()}, "
            f"Talep: {ListingRequest.query.count()}"
        )


if __name__ == "__main__":
    seed_data()

