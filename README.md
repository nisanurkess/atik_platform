# Atık Değişim Platformu (MVP)

Basit bir Flask + SQLite web uygulaması. Fabrikaların atık ilanı açmasını ve diğer firmaların bu ilanlara talep/mesaj göndermesini sağlar.

## Kurulum

1. Python 3.10+ yüklü olduğundan emin olun.
2. Bu klasörde bir sanal ortam (opsiyonel ama önerilir) oluşturun:
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   ```
3. Gerekli paketleri yükleyin:
   ```bash
   pip install -r requirements.txt
   ```

## Çalıştırma

1. `atik_platform` klasöründe olduğunuzdan emin olun.
2. Uygulamayı başlatın:
   ```bash
   python app.py
   ```
3. Tarayıcıda şu adrese gidin: `http://127.0.0.1:5000`

İlk çalıştırmada `instance/database.db` dosyası otomatik oluşturulur ve tablolar yaratılır.

## Seed (Örnek Veri) Yükleme

1. Uygulama kapalıyken aşağıdaki komutu çalıştırın:
   ```bash
   python seed.py
   ```
2. Konsolda "Seed verileri başarıyla eklendi." mesajını görmelisiniz.
3. Sonrasında tekrar:
   ```bash
   python app.py
   ```
   komutuyla uygulamayı başlatın.

## Özellikler (MVP)

- Ana sayfa: özet sayılar, son 5 ilan
- İlan oluşturma
- İlan listeleme ve filtreleme (kategori / şehir)
- İlan detay sayfası
- İlan için talep/mesaj gönderme
- Basit Bootstrap tabanlı arayüz

