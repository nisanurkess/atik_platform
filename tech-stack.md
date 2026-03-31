Teknoloji Yığını
Genel Yapı

Proje, hızlı geliştirme ve minimum manuel kod yazımı hedefiyle “vibe coding” yaklaşımıyla geliştirilmiştir. Backend ve frontend tek uygulama içinde çalışacak şekilde tasarlanmıştır.

Bu süreçte klasik geliştirme yerine yapay zeka destekli üretim ağırlıklı bir yöntem tercih edilmiştir.

Geliştirme Yaklaşımı

Proje geliştirilirken birden fazla yapay zeka aracı aktif olarak kullanılmıştır. Cursor ana geliştirme aracı olarak kullanılmış, bunun yanında ChatGPT, Claude ve Gemini destekleyici araçlar olarak sürece dahil edilmiştir.

Kod yazım sürecinde üç farklı Cursor hesabı kullanılarak paralel ilerlenmiştir(ücretsiz prompt sınırından kaynaklı). Kodun büyük kısmı doğrudan yapay zeka tarafından üretilmiş, geliştirme süreci manuel kod yazmaktan çok yönlendirme ve kontrol üzerine kurulmuştur.

Yönetim Bilişim Sistemleri öğrencisi olarak temel yazılım bilgisi bulunmasına rağmen bu projede bilinçli olarak minimum manuel kod yazımı ve maksimum yapay zeka kullanımı yaklaşımı tercih edilmiştir.

Kullanılacak teknoloji yığını, sistem mimarisi ve araç seçimi büyük ölçüde yapay zeka önerileri doğrultusunda belirlenmiştir.

Backend

Backend tarafında Python ve Flask kullanılmıştır.

Flask framework’ü hızlı geliştirme imkanı sunması, basit bir yapıya sahip olması ve MVP geliştirme için uygun olması nedeniyle tercih edilmiştir.

Backend tarafında routing, form işlemleri ve veritabanı bağlantısı yönetilmektedir.

Frontend

Frontend tarafında HTML, CSS, Bootstrap ve Jinja template yapısı kullanılmıştır.

Sistem sade ve hızlı geliştirilebilir olacak şekilde tasarlanmıştır. Bootstrap modern görünüm, responsive yapı ve hızlı geliştirme imkanı sağladığı için tercih edilmiştir.

Jinja template yapısı sayesinde backend verileri dinamik olarak frontend tarafına aktarılmaktadır.

Veritabanı

Projede SQLite kullanılmıştır.

SQLite, kurulum gerektirmemesi, hafif ve hızlı olması nedeniyle MVP için uygun bir çözüm olarak tercih edilmiştir. Küçük ölçekli projelerde yeterli performans sağlamaktadır.

Sistemde kullanıcılar, firmalar, ilanlar ve teklifler için ayrı tablolar bulunmaktadır.

Yapay Zeka Entegrasyonu

Projede OpenAI API kullanılmıştır.

Yapay zeka, kullanıcı deneyimini iyileştirmek amacıyla kullanılmıştır. Açıklamadan kategori önerisi yapılmakta, metin iyileştirme desteği sağlanmakta ve anahtar kelimeler çıkarılmaktadır.

Bu sayede kullanıcıların daha hızlı ve doğru ilan oluşturması hedeflenmiştir.

Deployment

Projenin ilk aşamalarında Lovable platformu değerlendirilmiştir. Ancak sistemin Flask tabanlı backend mimarisi nedeniyle Lovable yalnızca frontend odaklı olduğu için uygun bulunmamıştır.

Bu nedenle yapay zeka araçlarının da önerisiyle backend desteği sunan Render platformu tercih edilmiştir.

Render platformu, ücretsiz plan sunması, GitHub ile kolay entegrasyon sağlaması ve hızlı deploy imkanı sunması nedeniyle seçilmiştir.

Ücretsiz versiyon kullanıldığı için uygulama belirli bir süre kullanılmadığında uyku moduna geçmektedir. Bu durumda ilk açılışta kısa bir gecikme yaşanabilmektedir.

Versiyon Kontrol

Projede Git ve GitHub kullanılmıştır.

Kodlar GitHub üzerinde tutulmakta ve bu sayede versiyon takibi, yedekleme ve deploy süreçleri kolaylaştırılmaktadır.

Geliştirme Ortamı

Geliştirme sürecinde VS Code kullanılmıştır. Python sanal ortamı (venv) ile bağımlılıklar izole edilmiştir ve proje düzeni korunmuştur.

Sonuç

Bu proje, klasik yazılım geliştirme yaklaşımından farklı olarak yapay zeka destekli geliştirme yaklaşımı ile oluşturulmuştur.

Minimum manuel kod yazımı ile hızlı bir şekilde çalışan bir MVP ortaya çıkarılmıştır. Ortaya çıkan sistem geliştirilebilir bir temel sunmakta ve yapay zeka destekli geliştirme süreçlerine iyi bir örnek oluşturmaktadır.