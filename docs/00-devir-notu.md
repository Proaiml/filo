# Filo — devir notu ve tasarım kararları

Yeni oturumda önce bu dosyayı, sonra `docs/ilerleme.md` dosyasını oku.

## Amaç

Filo, sunucu otomasyonu (OpenText sunucu otomasyonu sınıfı) ve runbook otomasyonu (OpenText akış otomasyonu
sınıfı) adminlik işlerini bir yapay zekâ ajanına yaptıran, modelden bağımsız, arayüzlü bir harness ve onun bench'idir.
Örnek talepler: "adı PA ile başlayan sunucularda şu scripti çalıştır, sonucu XML yap, şu adrese e-posta at",
"yeni kurulan sunucuya standart ürünleri kur ve doğrula". İş 500 sunucuda da 2 sunucuda da aynı yoldan yürür.

İlke: harness ile model orta noktada buluşur. Dili anlamak, plan kurmak, hatayı yorumlamak modelin işidir; hedef
çözümleme, paralel yürütme, şema denetimi, yetki, onay, denetim izi kodun işidir. Küçük bir yerel model harness ile
gelişmiş modele yakın başarı vermelidir. Her yetenek aynı modelin "harness'li" ve "yardımsız" kollarıyla ölçülür.
Metinlerde ve kol adlarında "modelsiz" kelimesi kullanılmaz.

## İki ajan

| Ajan | Karşılığı | Davranış |
|---|---|---|
| **Kalfa** | sunucu otomasyonu sınıfı | Yalnız hazır becerilerle çalışır. Talebi okur, katalogdan beceri seçer, parametreleri doldurur, hedefi çözer, yürütür, raporlar. Beceriyi değiştirmez. |
| **Kaptan** | akış otomasyonu sınıfı | Dinamik. Talepten bir akış (beceri adımları zinciri) kurar, adım adım yürütür. Adım hata verir ya da çıktı beklenen şemaya uymazsa salt-okur becerilerle teşhis koyar, sonra beceriyi ya da akışı çalışma anında değiştirir (yeni sürüm olarak), sınırlı sayıda yeniden dener, olmazsa insana devreder. Başarılı planı sabit akış olarak kaydedebilir. |

Adlar çalışma adıdır (Filo, Kalfa, Kaptan); kullanıcı değiştirebilir. Dinamik ajanın ilk adı "Reis" idi; 17 Kasım
2026'da (ikinci tur) Kaptan oldu: kod `filo/kaptan.py`, komut satırı `--ajan kaptan`, bench kolu `kaptan`. Eski sonuç
dosyalarında kol adı `reis` kalır; `bench rapor` ve arayüz onu `kaptan` diye okur.

## İkinci tur kararları (17 Kasım 2026)

### Go ajanı (`ajan/`, ikili `filo-ajan`)
- Yönetilen sunucuda port açmaz; çekirdeğin ajan kapısına (`filo/ajan_kapisi.py`, 127.0.0.1:8795; laboratuvar
  konteynerleri `host.docker.internal` üzerinden) dışarı doğru bağlanır: kayıt, 10 sn kalp, 25 sn uzun yoklama, sonuç,
  dosya. Yalnız Go standart kitaplığı; `python -m filo ajan derle` resmi `golang:1.23-alpine` imajında `go vet`,
  `go test` ve linux/amd64, linux/arm64, windows/amd64 derlemesi yapar (Go makineye kurulmaz).
- Kimlik: sunucuya bağlı, tek kullanımlık, süreli kayıt belirteci → ajana özel gizli anahtar (ajanda 0600, çekirdekte
  `ayarlar/ajan_gizli.json`, git dışı). İstek ve iş anahtarı ayrı türetilir; her istek imzalı + zaman damgalı + nonce'lu,
  cevaplar isteğin nonce'una bağlı imzalı, iş paketi `{govde, imza}`; ajan imzasız/sahte/süresi dolmuş/başka ajana ait/
  tekrarlanan işi çalıştırmaz. Laboratuvarda düz HTTP (bütünlük ve kimlik var, gizlilik yok); gerçek ağda TLS gerekir.
- Taşıyıcı seçimi (`erisim.tasiyici_sec`): canlı ajan varsa iş ajandan; ajan 8 sn'de işi almazsa SSH'a düşülür; hangi
  yoldan gidildiği sonuçta (`tasiyici`, `tasiyici_notu`) ve denetim izinde yazar. SSH ağırlıkla ilk kurulum ve onarım
  yoludur (`ajan_kur`, `ajan_onar`, `ajan_kaldir`, `ajan_durumu`; `tur: "yonetim"` becerileri).
- Laboratuvarda systemd yok: ajan konteynerin `filo-svc` servis yöneticisine `filo-ajan` servisi olarak tanımlanır;
  ölen ajanı `ajan_onar` başlatır. `lab sifirla` ajanları ve kapıdaki kayıtlarını siler.

### Teslim politikası (yeni sunucu)
- `ayarlar/teslim_politikalari.json`: kurallar (ad kalıbı / grup → profil), profiller (beceri zinciri, ön onaylı adımlar,
  rapor alıcısı, yarıda kalırsa Kaptan ya da insan, Kaptan'ın düzeyi). Envanterde `teslim=bekliyor` işaretli sunucuya
  ajan kaydolunca profil kendiliğinden başlar (`filo/teslim.py`); talep üzerine `teslim_uygula` becerisiyle de başlar.
  Laboratuvar: `python -m filo lab yeni-sunucu PA-WEB-02|PB-APP-02`.

### Kaptan'ın inisiyatif düzeyi
- 0 yalnız öner · 1 teşhis serbest (risk 0-1) · 2 geri alınabilir onarım serbest (risk ≤ 2) · 3 beceri ve
  servis/paket değişikliği serbest (risk ≤ 3) · tam yetki yok: risk 4 her düzeyde insan onayı. Kodla uygulanır
  (`kaptan._calistir`), her karar "bu düzeyde izinli / onay gerekti / reddedildi" diye iş kaydına ve denetim izine yazılır.
  Varsayılan `ayarlar/kaptan.json`; talep başına arayüzden. Bench'te senaryo `kaptan_inisiyatif` verir, yoksa 3.

### Beceriye dönüştürme
- Başarılı Kaptan akışı ya da tek seferlik betik/komut işi tek adımda katalogda v1 beceri olur (`filo/donustur.py`):
  değerler parametreye, sunucu adları hedefe döner; risk ve şema kodla; Kaptan'ın duruma özgü onarımları kalıcı adım
  olmaz. Düz dil tarifinden taslak: model yazar, kod denetler, sınama sunucusunda kuru çalıştırma geçmeden kataloğa
  girmez.

### Arayüz
- Kurumsal konsol: ortak kabuk + iki ayrı ürün sayfası: `/kalfa` (iş konsolu: talep ya da beceriden başla → beceri kartı →
  parametre formu → dondurulmuş hedef → yürütme ızgarası → rapor) ve `/kaptan` (akış tuvali, inisiyatif düzeyi, gerekçe
  izi, beceri sürüm farkı, beceriye dönüştür / sabit akış). Diğer sayfalar ve karşılaştırma: `docs/ilerleme.md` B6.

## Üçüncü tur kararları (17 Kasım 2026)

İlke: sunucu otomasyonu ve akış otomasyonu özellikleri bire bir kopyalanmaz, genel ve kolaylaştırılmış hâli yapılır; operatör düz Türkçe yazar,
yapıyı ajan ve kod kurar. Ayrıntı ve doğrulama: `docs/ilerleme.md` "Üçüncü tur".

- **Zamanlayıcı** (`filo/zamanlayici.py`, `filo/zamanli.py`): konsol sürecinde iş parçacığı, durum
  `results/zamanlama/isler.json`; tek/günlük/haftalık/aylık/cron/"bakım penceresinde"; hedef çözümü (şimdi dondur /
  çalışma anında), kaçırılan koşu (atla / hemen), yasak politikası (bekle / sor / atla); önceden onay tanım sürümüne ve
  özetine bağlı, tanım değişince düşer. Pencereler `ayarlar/pencereler.json`; yasak pencere çekirdekte de uygulanır
  (risk ≥ 2 adım yasaktaki sunucuda başlamaz). Zamanlanmış koşu model çağırmaz (Kalfa: beceri tanımı; Kaptan: akış).
- **Koşu denetimi** (`filo/kontrol.py`, `filo/devam.py`): duraklat/sürdür/iptal/devret bekleme noktalarında (adım sınırı,
  yelpazede her sunucu başlamadan önce); durum iş kaydında (`devam`), konsol yeniden başlarsa kayıttan sürer; tamamlanan
  her üst düzey adım devam noktasıdır. Kaptan insana devredince iş bekler (konsolda), operatör kararı Kaptan'a girdi olur.
- **Yapılı akış** (`filo/akis_motoru.py`, `filo/akis_kurucu.py`): biçim `filo-akis` sürüm 2 (iç içe bloklar); eski düz
  akışlar okunur. Model önce düz liste kurar; kod yapı ipucu bulursa dar sorular sorar, birleştirir, doğrular; ipucu yoksa
  ek soru yok. Kaptan'ın yürütmesi bu motorun üstündedir; inisiyatif ve risk kuralları değişmedi.
- **Çalıştırma kimliği** (`filo/kimlik.py`, `ayarlar/calistirma_kimlikleri.json`): betik `sudo -n -u` ile sarılır;
  taşıyıcıdan bağımsız (SSH ve ajan aynı). Laboratuvarda PC-BATCH-01'de filo yalnız root'a parolasız sudo yapabilir
  (`FILO_SUDO=kok`), her sunucuda `uygulama` servis kullanıcısı var.
- **Bench**: senaryolar sahte saat (`saat`), pencereler, zamanı ilerletme, kayıtlı akış, operatör eylemi (duraklat /
  devirde düzeltip sürdür) ve adımdan devam tanımlayabilir; zamanlama ve iş kaydı ölçütleri referans kolda muaftır
  (referans Filo'yu kullanmaz). Testler laboratuvarın ajan durumunu oturum sonunda geri getirir.

## Dördüncü tur kararları (17 Kasım 2026)

Ayrıntı ve doğrulama: `docs/ilerleme.md` "Dördüncü tur".

- **Ortak çekirdek "istenen durum"**: yama, yazılım politikası, uyum ve anlık görüntü aynı salt-okur toplayıcıyı
  (`filo/durum.py`: paketler, servisler, kullanıcılar, dosya özet/izin, içerik deseni, sysctl, portlar, bekleyen
  güncellemeler + güvenlik sınıfı, yeniden başlatma gereği) ve aynı eylem yürütücüsünü (`filo/duzelt.py`: aileye göre
  komut, risk ve geri alma eylemi koddadır, her uygulama `results/duzeltmeler/kayit.jsonl`'a geri alma eylemleriyle yazılır)
  kullanır. Karşılaştırma ve değerlendirme saf Python'dur.
- **Yönetim becerisinin toplu işleyicisi** (`tur: yonetim`, `toplu: true`): işleyici bütün hedefi birlikte görür (aşamalı
  dağıtım: önce test grubu, başarılıysa kalanlar); sonuç yine sunucu başına tek şemada. Parametreye bağlı risk
  (`risk_kurali`): ör. hemen yeniden başlatma düzey 4.
- **Talepten parametreyi kod çıkarır** (`ajan_ortak.kod_parametreleri`): yeniden başlatma politikası, kapsam, test grubu,
  referans sunucu, "yalnız geri alınabilir", adıyla anılan politika/kural seti. Model bu değerleri değiştiremez; talep bir
  politika adı söylemiyorsa model politika seçemez. "Yeniden başlatma bakım penceresinde" işin zamanlaması değildir.
- **Teslim politikası = yazılım politikasının kullanımı**: profil `politika` + `on_onayli` adım türleri + ön/son adım
  taşır; değiştiren adımlar politikadan üretilir.
- **Laboratuvar internetsiz**: tek paket kaynağı `filo-depo` (kurum içi ayna); örnek paketlerin eski sürümleri imajlarda,
  yenileri depoda (güvenlik sınıfı dağıtımın kendi biçiminde); yeniden başlatma öykünmesi. İmajlar `:2`.
- **Laboratuvar kilidi** (`results/LAB_KILIT`): bench ve laboratuvar sınamaları aynı anda çalışmaz.
- **Bench yalıtımı**: harness'li kolda politika/kural ayarları ve düzeltme/görüntü kayıtları kol başına geçici kopyadadır
  (`durum.yalit`); senaryo `ayarlar` alanıyla kendi politika içeriğini verebilir.

## Araştırmadan gelen zorunlu korumalar

Kaynak: `docs/arastirma/01-sunucu-adminlik.md`, `02-akis-adminlik.md` (sondaki "Harness için çıkarımlar").

1. Hedef çözümlemesi iş başlamadan dondurulur ve gösterilir (sunucu otomasyonu'daki "Now"); çözülen liste denetim izine yazılır.
2. Her işte zaman aşımı zorunlu parametredir; zaman aşımı ayrı durumdur.
3. Sunucu başına sonuç tek şemadadır: `basarili | hatali | zaman_asimi | erisilemedi | iptal`, çıkış kodu, stdout,
   stderr, süre, çıktı kesildiyse `kesildi: true`.
4. Kısmi başarısızlık sessiz geçilmez; yalnız başarısızlar yeniden denenir, deneme sayısı sınırlıdır (varsayılan 2).
5. Beceriler tipli girdi ve çıktı şemasıyla tanımlanır; şemaya uymayan çağrı çalışmaz.
6. Her becerinin risk düzeyi vardır: 0 salt-okur, 1 raporlama/dosya üretme, 2 geri alınabilir değişiklik, 3 servis ve
   paket değişikliği, 4 yıkıcı. Düzey 3 ve üstü insan onayı ister; bench kipinde onayı senaryo tanımı verir.
7. Değiştiren her becerinin geri alma tanımı ve kuru çalıştırması olur.
8. Beceri değişikliği sürüm kaydıyla yapılır: eski sürüm saklanır, fark gösterilir, geri dönülebilir. Kaptan'ın değiştirdiği
   becerinin risk düzeyi kodla yeniden sınıflanır (salt-okur beceriye yazan komut eklenirse düzey yükselir ve onay ister).
9. Kimlik bilgisi modele, komut satırına ve kayıtlara girmez; envanterde adla anılır, çalıştırma anında çözülür.
10. Her karar ve eylem eklemeli denetim izine yazılır (talep, seçilen beceri ve sürümü, hedef listesi, onaylayan, sonuç).
11. Durdurma düğmesi: operatör bütün ajan eylemlerini tek adımda keser.
12. Yürütmeden önce erişim sınaması yapılır; erişilemeyen sunucu hedef kümeden ayrılır ve ayrıca raporlanır.

## Mimari

Python 3.11, çekirdek ve web sunucusu yalnız standart kitaplık (Vardiya'daki gibi). Temel erişim ve model kapısı
Vardiya projesinden (`vardiya/erisim.py`, `vardiya/gateway.py`) kopyalanıp uyarlanır; iki depo
birbirine bağlanmaz, Vardiya deposuna dokunulmaz.

```
filo/
  envanter.py   sunucular (ad, os, adres, port, kullanıcı, gruplar, öznitelikler), hedef seçici (ad kalıbı PA*, grup,
                öznitelik, işletim sistemi), dondurulmuş hedef listesi
  erisim.py     taşıyıcılar: SSH (sistem ssh istemcisi, anahtarla), WinRM (PowerShell Invoke-Command), öykünücü;
                komut ve betik çalıştırma, dosya gönderme, zaman aşımı, denetim izi
  yurutme.py    yelpaze yürütücü: eşzamanlılık sınırı, sunucu başına zaman aşımı, tek şemalı sonuç, başarısızları
                yeniden deneme, çıktı boyut sınırı, durdurma düğmesi
  beceri.py     beceri kataloğu: skills/<ad>/beceri.json + betik dosyaları, şema denetimi, risk düzeyi, sürümleme
  politika.py   onay kapısı, kuru çalıştırma, risk sınıflama
  rapor.py      sonuç dönüştürme (CSV, XML, JSON, HTML) ve SMTP ile e-posta
  gateway.py    model bağlantıları: Ollama, OpenAI uyumlu uç (LM Studio, vLLM, llama.cpp), Anthropic, Gemini, agy
  kalfa.py      beceri seçen ajan
  kaptan.py       dinamik akış ajanı (inisiyatif düzeyi)
  ajan_kapisi.py  Go ajanlarının bağlandığı kapı (kayıt, kalp, uzun yoklama, imzalı iş/sonuç) + yerel API
  ajan_istemci.py ajan taşıyıcısı (ajan → yoksa SSH)
  ajan_yonetimi.py ajan derleme/kurma/onarma/kaldırma; teslim_uygula işleyicisi
  teslim.py       yeni sunucu teslim politikası ve Kaptan devralması
  donustur.py     beceriye dönüştürme (işten ve tariften)
  karsilastirma.py sunucu/akış ile Filo karşılaştırması (07 + ölçülmüş bench)
  durum.py        toplayıcı, anlık görüntü, karşılaştırma; politika/kural kayıtlarının sürümlenmesi (D1-D3)
  duzelt.py       düzeltme eylemleri (paket, servis, kullanıcı, dosya, izin, satır), geri alma eylemleri ve kayıt
  yama.py         yama durumu, politika, uyum, uygulama (aşamalı, ön/son kontrol, yeniden başlatma), geri alma
  yazilim_politikasi.py  yazılım politikası: sapma, önizleme, remediation, geri alma, talepten politika, teslim adımları
  uyum.py         uyum kural setleri, istisnalar, denetim ve düzeltme; anlık görüntü al / karşılaştır
  ui_veri.py      konsolun Yama, Politikalar, Uyum sayfalarının veri uçları
ajan/           Go ajanı (filo-ajan), testleri; ajan/cikti/ derleme çıktısı (git dışı)
  denetim.py    eklemeli denetim izi
  web.py        arayüz sunucusu + JSON API, static/ altında tek sayfa
  bench/        senaryo motoru, hakem, kollar, rapor
skills/         beceriler
lab/            Docker laboratuvarı
bench/          temel/ orta/ ileri/ senaryoları
ayarlar/        envanter ve bağlantı dosyaları (gizli olanlar git dışında)
tests/
```

### Arayüz (Türkçe, tek sayfa, 127.0.0.1)

- **Talep masası**: talep metni, ajan (Kalfa / Kaptan), model bağlantısı; plan önizleme, dondurulmuş hedef listesi, onay, yürütme.
- **Koşular**: canlı sunucu ızgarası (durum renkleri), adım zaman çizgisi, ajanın gerekçe izi, Kaptan'ın beceri değişiklikleri.
- **Envanter**: sunucular, gruplar, erişim sınaması.
- **Beceriler**: katalog, şema, risk düzeyi, sürüm geçmişi ve fark.
- **Onaylar**: bekleyen düzey 3+ eylemler.
- **Bağlantılar**: yerel (Ollama, OpenAI uyumlu uç) ve API (Anthropic, OpenAI, Gemini) model bağlantılarını ekleme,
  düzenleme, sınama; anahtar ortam değişkeni adıyla ya da git dışındaki `ayarlar/gizli.json` içinde tutulur, arayüzde
  hiçbir zaman geri gösterilmez. Her bağlantı türü için nasıl kurulacağını anlatan kısa yardım metni.
- **Bench**: seviyeler, senaryolar, koşu başlatma, harness'li ve yardımsız kol karşılaştırması.
- **Denetim izi**.

### Laboratuvar (kullanıcı kararı, 17 Kasım 2026)

- Docker Compose ile Linux filosu: en az 8 küçük konteyner, sshd açık, karışık dağıtım (Debian, AlmaLinux/Rocky, Alpine),
  adlar `PA-APP-01`, `PA-APP-02`, `PA-DB-01`, `PB-WEB-01` ... biçiminde; anahtar tabanlı giriş; portlar 127.0.0.1'e bağlı.
- Sahte posta sunucusu (Mailpit ya da benzeri): SMTP + hakemin okuyacağı HTTP API.
- Gerçek Windows hedefi: bu makinenin kendi WinRM servisi. WinRM'i açmak ve sınama hesabı oluşturmak sistem ayarıdır,
  kullanıcı yapar; kod yalnız taşıyıcıyı ve `python -m filo winrm-kontrol` sınamasını sağlar. WinRM kapalıyken Windows
  hedefleri öykünücüyle cevaplanır ve sonuçlar "öykünme" etiketiyle ayrı raporlanır.
- Bozukluk enjeksiyonu: senaryo kurulumu konteynere bozukluk koyar (sshd kapalı, disk dolu, sudo requiretty, bozuk paket
  deposu, yanlış anahtar, yavaş cevap).

### Bench (çalışma adı: Filo Admin Bench)

Üç seviye, talep biçiminde görevler, programla denetlenen ölçütler (hakem laboratuvarın gerçek durumuna bakar: dosya,
servis, posta kutusu, denetim izi).

- **Temel**: düz işler (hedef seç, çalıştır, topla, biçimlendir).
- **Orta**: çok adımlı ve koşullu işler (karışık işletim sistemi, kısmi başarısızlık, yeniden deneme, dönüştürüp e-posta,
  kurulum + doğrulama).
- **İleri**: sorunlu ortam ve akıl yürütme (erişilemeyen sunucu, yetki hatası, yarım kurulum, bozuk depo, akışın ortasında
  beklenmeyen çıktı ve akışın yeniden kurulması, geri alma).

Kollar: `yardimsiz` (aynı model, yalnız ham kabuk aracıyla), `kalfa`, `kaptan`. Zararlı sonuç (yanlış sunucuda değişiklik,
sahte başarı raporu) ayrı sayılır. Vaka taslakları `docs/arastirma/03-vaka-taslaklari.md` içinden gelir.

## Makine sınırları

Dizüstü bilgisayar; 16 Kasım 2026'da paralel yük makineyi ısıdan yeniden başlattı. Tek laboratuvar kopyası, tek koşu, tek
model yuvası. Ağır iş ve yerel model koşusu başlamadan ısı bekçisi çalışır (`tools/isi_bekcisi.py`, Vardiya'dan kopya).
Ollama çağrıları düşünme kapalı ve `num_ctx` 16384 ile yapılır. Karta sığan modeller: `qwen3:8b`, `qwen3:14b`,
`gemma4:latest`.

## Öncelik düzeltmesi (kullanıcı, 17 Kasım 2026)

İlk iş gerçek sunucu otomasyonu ve akış otomasyonu ürünlerini indirip kurmak; adminlik görevleri o ürünlerin üzerinde yapılacak (ajan sunucu otomasyonu ve akış otomasyonu'yu
yönetir: sunucu otomasyonu'da sunucu grubu, Run Server Script, ajan kurulumu, yazılım politikası; akış otomasyonu'da akış, içerik paketi, sistem
hesabı vb.). Sonraya kalan şey bizim yayınlayacağımız üründür. İlk oturumda bu ters anlaşıldı: Docker Linux filosu,
Kalfa, Kaptan ve 15 senaryo sunucu/akış olmadan, doğrudan SSH üzerinden kuruldu. Bu katman atılmaz: laboratuvar sunucuları
sunucu otomasyonu'nın yöneteceği hedefler olur, beceriler ve ajanlar sunucu/akış bağdaştırıcılarının üstünde çalışır. Ama bench'in asıl
ölçtüğü şey gerçek üründe adminlik olmalıdır; SSH'la doğrudan yapılan iş bunun yerine geçmez.

**Güncelleme (aynı gün):** kurulum paketlerine ulaşılamadı (SLD portalı yeni hesapta SUID / sipariş numarası istiyor;
bkz. `ilerleme.md`). Kullanıcı kararı: "ürünü kuramasak da sorun değil; bu ürünün tüm özelliklerini biliyoruz, çoğu
balon." Bu yüzden gerçek sunucu/akış kurulumu şart olmaktan çıktı. Filo sunucu otomasyonu ve akış otomasyonu'yu yönetmez, onların yaptığı işi kendi
katmanıyla yapar (doğrudan SSH/WinRM, beceriler, Kalfa, Kaptan). Bench, sunucu/akış adminlerinin gördüğü talepleri ve forumdaki
sorunları Filo'nun kendi laboratuvarında ölçer. Erişim ileride açılırsa gerçek ürün ayrı bir doğrulama kolu olur.
Özellik karşılığı: `docs/11-ozellik-haritasi.md`. Aşağıdaki "sıradaki işler" listesi bu kararla geçersizdir.

Eski sıradaki işler: (1) sunucu otomasyonu ve akış otomasyonu'nun indirme ve kurulum yolu (`docs/arastirma/06-gercek-urun-kurulumu.md`), (2) kurulum,
(3) sunucu otomasyonu ve akış otomasyonu bağdaştırıcıları (pytwist / sunucu otomasyonu API, akış otomasyonu REST), (4) senaryoların gerçek ürün üzerinden yeniden yazılması.
