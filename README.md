# Atik Degisim Platformu (MVP)

Bu repo yeniden duzenlenmistir. Kaynak kodlar `features/` altina tasinmistir.
Proje Flask + SQLite ile calisir ve firmalarin atik ilani acmasini, diger firmalarin taleplerini yonetmesini saglar.

## Klasor Duzeni

- `features/`: Tum uygulama kaynak kodlari
- `assets/`: Ekran goruntuleri, gorseller, dokuman varliklari
- `agents/`: AI/otomasyon notlari veya agent dokumanlari
- `README.md`, `idea.md`, `user-flow.md`, `tech-stack.md`: Koku dokumanlari

## Kurulum

1. Python 3.10+ yüklü oldugundan emin olun.
2. (Opsiyonel) Sanal ortam olusturun:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```
3. Bagimliliklari yukleyin:
   ```bash
   pip install -r features/requirements.txt
   ```

## Calistirma

1. Proje kok klasorunde olun (`atik_platform`).
2. Uygulamayi baslatin:
   ```bash
   python features/app.py
   ```
3. Tarayicida acin: `http://127.0.0.1:5000`

Veritabani dosyasi `features/instance/database.db` altinda kullanilir.

## Seed (Ornek Veri) Yukleme

Uygulama kapaliyken:

```bash
python features/seed.py
```

Sonra tekrar:

```bash
python features/app.py
```

## Not

Eger ekran goruntusu veya tasarim gorselleri ekleyeceksen, bunlari `assets/` altinda toplaman onerilir.

