import os
from datetime import datetime, timedelta

from app import create_app
from models import db, Company, Listing, ListingRequest

# Bu script, örnek firma, ilan ve talep verileri ekler.
# Tek seferlik çalıştırmanız yeterlidir.


def seed_data():
    app = create_app()
    with app.app_context():
        # Veritabanı dosyasının varlığından emin ol
        os.makedirs(app.instance_path, exist_ok=True)

        # Her ihtimale karşı tabloların varlığını kontrol et
        db.create_all()

        # Zaten veri varsa tekrar eklememek için basit kontrol
        if Company.query.count() > 0:
            print("Seed verileri zaten eklenmiş görünüyor. İşlem iptal edildi.")
            return

        # 1) Örnek firmalar
        companies = [
            Company(
                name="Anadolu Plastik Sanayi A.Ş.",
                sector="Plastik Üretimi",
                city="İstanbul",
                created_at=datetime.utcnow() - timedelta(days=30),
            ),
            Company(
                name="Ege Metal İşleme Ltd.",
                sector="Metal İşleme",
                city="İzmir",
                created_at=datetime.utcnow() - timedelta(days=25),
            ),
            Company(
                name="Yeşil Geri Dönüşüm A.Ş.",
                sector="Geri Dönüşüm",
                city="Kocaeli",
                created_at=datetime.utcnow() - timedelta(days=20),
            ),
            Company(
                name="Marmara Tekstil Fabrikası",
                sector="Tekstil",
                city="Bursa",
                created_at=datetime.utcnow() - timedelta(days=15),
            ),
            Company(
                name="Pak Ambalaj Sanayi",
                sector="Ambalaj",
                city="Ankara",
                created_at=datetime.utcnow() - timedelta(days=10),
            ),
        ]

        db.session.add_all(companies)
        db.session.commit()

        # Kolay erişim için tekrar çekelim
        companies = Company.query.all()

        # 2) Örnek ilanlar
        listings = [
            Listing(
                company_id=companies[0].id,
                title="Renkli Plastik Granül Atığı",
                description="Üretim sürecinden çıkan, farklı renklerde plastik granül atıkları. Temiz ve sınıflandırılmış durumdadır.",
                category="Plastik",
                quantity="3 ton",
                city="İstanbul",
                status="Aktif",
                created_at=datetime.utcnow() - timedelta(days=7),
            ),
            Listing(
                company_id=companies[1].id,
                title="Çelik Sac Kesim Artıkları",
                description="Lazer kesim sonrası oluşan çelik sac artıkları. Geri dönüşüm için uygundur.",
                category="Metal",
                quantity="5 ton",
                city="İzmir",
                status="Aktif",
                created_at=datetime.utcnow() - timedelta(days=6),
            ),
            Listing(
                company_id=companies[2].id,
                title="Karton ve Kağıt Atığı",
                description="Ofis ve üretim hattından toplanan karışık karton ve kağıt atıkları.",
                category="Kağıt",
                quantity="2,5 ton",
                city="Kocaeli",
                status="Aktif",
                created_at=datetime.utcnow() - timedelta(days=5),
            ),
            Listing(
                company_id=companies[3].id,
                title="Kumaş Parça Atıkları",
                description="Farklı renk ve türlerde tekstil kumaş parça atıkları. Dolgu ve yalıtım malzemesi yapımına uygundur.",
                category="Tekstil",
                quantity="1,2 ton",
                city="Bursa",
                status="Aktif",
                created_at=datetime.utcnow() - timedelta(days=4),
            ),
            Listing(
                company_id=companies[0].id,
                title="Şeffaf PET Şişe Atıkları",
                description="İçecek üretiminden çıkan temiz PET şişe atıkları. Sadece şeffaf malzeme.",
                category="Plastik",
                quantity="4 ton",
                city="İstanbul",
                status="Aktif",
                created_at=datetime.utcnow() - timedelta(days=3),
            ),
            Listing(
                company_id=companies[4].id,
                title="Hasarlı Karton Kutular",
                description="Nakliye sırasında hasar gören ancak geri dönüşüme uygun karton kutular.",
                category="Kağıt",
                quantity="1 ton",
                city="Ankara",
                status="Aktif",
                created_at=datetime.utcnow() - timedelta(days=2),
            ),
            Listing(
                company_id=companies[2].id,
                title="Cam Şişe ve Kavanoz Atıkları",
                description="Toplama hattından gelen karışık cam şişe ve kavanoz atıkları.",
                category="Cam",
                quantity="3,5 ton",
                city="Kocaeli",
                status="Aktif",
                created_at=datetime.utcnow() - timedelta(days=2),
            ),
            Listing(
                company_id=companies[1].id,
                title="Elektronik Kart Atıkları",
                description="Arızalı üretimlerden kalan baskılı devre kartları. Ayrıştırma yapılmamıştır.",
                category="Elektronik",
                quantity="500 kg",
                city="İzmir",
                status="Aktif",
                created_at=datetime.utcnow() - timedelta(days=1),
            ),
            Listing(
                company_id=companies[3].id,
                title="Organik Gıda Atıkları",
                description="Üretim tarihi geçen ancak kompost için uygun organik gıda atıkları.",
                category="Organik",
                quantity="1 ton",
                city="Bursa",
                status="Aktif",
                created_at=datetime.utcnow() - timedelta(days=1),
            ),
            Listing(
                company_id=companies[4].id,
                title="Kimyasal Temizlik Artıkları",
                description="Üretim sonrası kalan, belirli standartlara uygun sıvı temizlik kimyasalı artıkları.",
                category="Kimyasal",
                quantity="800 litre",
                city="Ankara",
                status="Aktif",
                created_at=datetime.utcnow(),
            ),
        ]

        db.session.add_all(listings)
        db.session.commit()

        listings = Listing.query.all()

        # 3) Örnek talepler
        requests = [
            ListingRequest(
                listing_id=listings[0].id,
                company_name="Doğa Geri Kazanım Ltd.",
                company_city="İstanbul",
                message="Plastik granülleri düzenli olarak alabiliriz. Aylık minimum 2 ton talebimiz var.",
                created_at=datetime.utcnow() - timedelta(days=3),
            ),
            ListingRequest(
                listing_id=listings[1].id,
                company_name="Anka Metal Geri Dönüşüm",
                company_city="Kocaeli",
                message="Çelik sac artıklarını yerinde görüp teklif vermek isteriz.",
                created_at=datetime.utcnow() - timedelta(days=2, hours=5),
            ),
            ListingRequest(
                listing_id=listings[2].id,
                company_name="Eko Kağıt Sanayi",
                company_city="Ankara",
                message="Düzenli karton ve kağıt atığı tedariki arıyoruz. Uzun vadeli iş birliği için iletişime geçebilir miyiz?",
                created_at=datetime.utcnow() - timedelta(days=2),
            ),
            ListingRequest(
                listing_id=listings[4].id,
                company_name="PET Dönüşüm Merkezi",
                company_city="İstanbul",
                message="Şeffaf PET atıklarınız için kg başı fiyat teklifi sunmak isteriz.",
                created_at=datetime.utcnow() - timedelta(days=1, hours=3),
            ),
            ListingRequest(
                listing_id=listings[7].id,
                company_name="Tekno Geri Dönüşüm",
                company_city="İzmir",
                message="Elektronik kart atıklarını parçalayarak metal geri kazanımı yapıyoruz. Yerinde inceleme talep ediyoruz.",
                created_at=datetime.utcnow() - timedelta(hours=10),
            ),
        ]

        db.session.add_all(requests)
        db.session.commit()

        print("Seed verileri başarıyla eklendi.")


if __name__ == "__main__":
    seed_data()

