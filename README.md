Atık Değişim Platformu (Endüstriyel Simbiyoz Pazaryeri)
Proje Tanımı

Bu proje, firmaların üretim süreçlerinde ortaya çıkan atık ve yan ürünleri diğer işletmelerle eşleştirerek ekonomik değere dönüştürmesini sağlayan dijital bir platformdur.

Birçok işletme, atıklarını değerlendiremeden bertaraf etmekte ve bu süreç hem maliyet hem de çevresel yük oluşturmaktadır. Bu platform, atıkları potansiyel bir hammadde olarak ele alarak döngüsel ekonomi yaklaşımını desteklemeyi amaçlar.

Bu proje AI destekli vibe coding yaklaşımıyla geliştirilmiştir.

Problem

Firmalar atıklarını değerlendirecek doğru alıcıyı bulmakta zorlanmaktadır. Atıklar çoğu zaman bir maliyet kalemi olarak görülmekte ve işletmeler arası paylaşımı sağlayacak merkezi bir sistem bulunmamaktadır. Bu nedenle potansiyel ekonomik değer kaybolmaktadır.

Çözüm

Bu platform ile firmalar atıklarını ilan olarak paylaşabilir. Diğer firmalar bu ilanları inceleyebilir ve uygun gördükleri ilanlara teklif gönderebilir. Böylece atıklar ekonomik değere dönüştürülür ve işletmeler arasında yeni bir iş birliği ortamı oluşur.

Temel Özellikler

Kullanıcı kayıt ve giriş sistemi bulunmaktadır. Sistem firma bazlı çalışır. Kullanıcılar atık ilanı oluşturabilir, ilanları listeleyebilir ve detaylarını görüntüleyebilir. Kategori ve şehir bazlı filtreleme yapılabilir. İlanlara teklif gönderme sistemi vardır. Ayrıca temel düzeyde bir dashboard ekranı sunulmaktadır.

AI Özelliği

Platformda basit bir yapay zeka desteği bulunmaktadır. Kullanıcının girdiği açıklamaya göre kategori önerisi yapılır. Metinden anahtar kelimeler çıkarılır ve kullanıcıya daha anlaşılır bir ilan oluşturması için açıklama iyileştirme önerileri sunulur.

Kullanılan Teknolojiler

Backend tarafında Python ve Flask kullanılmıştır.
Frontend tarafında HTML, CSS, Bootstrap ve Jinja template yapısı tercih edilmiştir.
Veritabanı olarak SQLite kullanılmıştır.

Ek olarak OpenAI API ile basit AI analizleri yapılmaktadır. Versiyon kontrol için GitHub, canlıya almak için Render kullanılmıştır.

Kurulum

Projeyi çalıştırmak için:

git clone https://github.com/nisanurkess/atik_platform
cd atik_platform
python -m venv venv
venv\Scripts\activate
pip install -r features/requirements.txt
Uygulamayı Çalıştırma
python features/seed.py
python features/app.py

Tarayıcıdan şu adresi aç:

http://127.0.0.1:5000/

Proje Akışı

Kullanıcı sisteme kayıt olur ve giriş yapar.
Firma adına ilan oluşturur.
Diğer firmaların ilanlarını inceler.
İlgilendiği ilanların detayına girer.
Uygun gördüğü ilanlara teklif gönderir.

Yayın Linki

https://atik-platform-1.onrender.com/
Uygulama Render’ın ücretsiz versiyonu üzerinde çalıştığı için belirli bir süre kullanılmadığında uyku moduna geçebilir. Bu nedenle ilk açılışta kısa bir gecikme yaşanabilir.


Demo Video

https://www.loom.com/share/92f568af46d74c8b8f4106f1ca3e3270

Projenin Katkısı

Bu proje atıkların ekonomiye kazandırılmasını hedefler. Firmalar arasında iş birliği oluşturur ve döngüsel ekonomiye katkı sağlar. Aynı zamanda atık yönetim maliyetlerinin azaltılmasına yardımcı olur.

Not

Bu proje hızlı prototipleme yaklaşımıyla geliştirilmiştir. Amaç, temel işlevleri çalışan bir sistem ortaya koymak ve fikri somutlaştırmaktır.

Bu proje demo amaçlı SQLite veritabanı kullanmaktadır. Ücretsiz ve hızlı geliştirme için tercih edilmiştir. Ancak Render ortamında kalıcı disk kullanılmadığı için bazı durumlarda veriler yeniden oluşturulabilir.

Daha stabil ve kalıcı veri yönetimi için PostgreSQL gibi harici veritabanları tercih edilebilir. Bu proje kapsamında ücretsiz çözümler önceliklendirildiği için SQLite kullanılmıştır.