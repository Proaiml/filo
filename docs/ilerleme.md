# Filo — ilerleme

Her aşamanın sonunda: ne yapıldı, nasıl doğrulandı, ne eksik kaldı. Doğrulanmamış şey doğrulanmış diye yazılmaz.

Ad notu (17 Kasım 2026, ikinci tur): dinamik ajanın çalışma adı Reis'ti, Kaptan oldu. Aşağıdaki eski kayıtlarda da yeni ad yazılıdır;
`results/` altındaki eski sonuç dosyaları yeniden yazılmadı (kol adı orada `reis`; `bench rapor` onu `kaptan` diye okur).

## A1 — Laboratuvar ve çekirdek (17 Kasım 2026)

**Yapılan**
- `lab/docker-compose.yml`: 8 Linux konteyner + Mailpit. Debian 12 (PA-APP-01, PA-WEB-01, PB-WEB-01), AlmaLinux 9
  (PA-APP-02, PB-DB-01), Alpine 3.20 (PA-DB-01, PB-APP-01, PC-BATCH-01). sshd yalnız anahtarla, root girişi kapalı,
  kullanıcı `filo` + parolasız sudo. Portlar 127.0.0.1:2201-2208, Mailpit SMTP 127.0.0.1:11025, HTTP 127.0.0.1:18025.
  Bellek sınırları: Debian 128 MB, Alma 256 MB, Alpine 96 MB, Mailpit 96 MB (toplam ~1.4 GB); her konteyner 0.5 işlemci.
  Her konteynerde 16 MB'lık `/veri` tmpfs (disk dolu bozukluğu gerçek "No space left" üretir).
- Konteynerlerde systemd/openrc yok; `lab/goruntu/ortak/filo-svc` servis yöneticisi, üstünde Debian/Alma için `systemctl`,
  Alpine için `rc-service` ince katmanları var. Beceriler gerçek sistemdeki komutları (systemctl / rc-service) kullanır.
- `python -m filo lab kur|durum|sifirla|kapat` (`filo/lab.py`). `kur`: istemci anahtarı ve ortak sunucu anahtarı üretir
  (`lab/anahtar/`, git dışında), özel anahtarın ACL'sini yalnız geçerli kullanıcıya bırakır (Windows OpenSSH bunu ister;
  bu proje dosyasının izni, sistem ayarı değil), `known_hosts` yazar, imajları kurar, konteynerleri başlatır, SSH'yi bekler.
- Bozukluk enjeksiyonu (`lab.bozukluk`): sshd_kapali, servis_durmus, servis_bozuk, servis_yavas, disk_dolu,
  sudo_requiretty, bozuk_depo, yanlis_anahtar, yarim_kurulum (gerçek "dpkg was interrupted", yalnız Debian),
  dosya_yaz, betik_cikti_degisti, paket_kaldir. `docker exec` ile kurulur; ajanın SSH yolundan bağımsızdır.
- `filo/envanter.py`: ad kalıbı (virgülle VEYA), grup, öznitelik, os, aile, hariç; metinden seçici
  (`PA* grup:web os:linux ortam=test !PA-DB-01`); bilinmeyen grup/os hata verir; `dondur()` listeyi zaman ve özetle dondurur.
- `filo/erisim.py`: SSH taşıyıcı (sistem OpenSSH istemcisi, betik stdin'den `sh -s` ile; `-F none`, BatchMode,
  StrictHostKeyChecking=yes), scp gönderimi, WinRM taşıyıcı (PowerShell `Invoke-Command`, `-EncodedCommand`),
  öykünücü (`oykunme: true`), `winrm-kontrol` (yalnız salt-okur sınamalar: servis durumu, Test-WSMan, Invoke-Command),
  durdurma düğmesi (bayrak dosyası + çalışan süreçleri öldürme), salt-okur komut izin listesi.
  Kimlik bilgisi envanterde profil adıdır (`ayarlar/kimlikler.json`), anahtar yolu yalnız çalıştırma anında çözülür.
- `filo/yurutme.py`: eşzamanlılık sınırı, zorunlu zaman aşımı, tek şemalı sonuç (`basarili|hatali|zaman_asimi|
  erisilemedi|iptal`, çıkış kodu, stdout, stderr, süre, `kesildi`, deneme, `oykunme`), yalnız başarısızları yeniden
  deneme (varsayılan 2), çıktı boyut sınırı, durdurma, iş öncesi erişim sınaması (erişilemeyen ayrılır ve raporlanır).
- `filo/denetim.py`: eklemeli JSONL denetim izi, satırlar özet zinciriyle bağlı (`python -m filo denetim --dogrula`),
  gizli adlı alanlar maskelenir.

**Doğrulama (gerçek konteynerlerde, 17 Kasım 2026)**
- `python -m filo lab kur` → "laboratuvar hazır: 8 sunucu erişilebilir".
- `python -m filo calistir --hedef "PA*" --komut "hostname; uname -r"` → 4/4 `basarili`, her satırda konteynerin kendi
  adı ve çekirdek sürümü.
- `docker stop filo-pa-db-01` sonrası aynı komut → PA-DB-01 `erisilemedi` ("Connection refused", 2 deneme), diğer üçü
  `basarili`, özet "3/4 başarılı ... erişilemedi 1", çıkış kodu 1.
- `--komut "rm -rf /tmp/x"` → "reddedildi: izin listesinde olmayan komut: rm".
- Yarım kurulum bozukluğu elle denendi: `apt-get install` → "E: dpkg was interrupted ...", `dpkg --configure -a` onarıyor.

**Eksik / not**
- WinRM: bu makinede açık değil (sınama A2'den sonra yeniden çalıştırılacak); Windows hedefi `PW-WIN-01` öykünücüyle cevaplanır.
- Laboratuvar, imaj kurulumu sırasında paket depolarına (internet) erişir; paket kurma becerileri de depo erişimi ister.

**Ek (A2 sırasında bulunan ve düzeltilen):** `filo-svc` canlılık denetimi `kill -0` kullanıyordu; root olmayan kullanıcıda
EPERM verdiği için servisler `inactive` görünüyordu, `/proc/<pid>` denetimine geçildi. AlmaLinux'ta sudo `secure_path`
`/usr/local/bin` içermediği için gerçek systemctl çalışıyordu; ince katman `/usr/bin/systemctl` üzerine bağlandı.
WinRM sınaması 17 Kasım'da çalıştırıldı: "WinRM servisi: Stopped", Test-WSMan bağlanamadı; kullanıcı komutları
(`Enable-PSRemoting -Force`, gerekirse `Add-LocalGroupMember -Group 'Remote Management Users' ...`) çıktıda yazıyor.
Filo hiçbir ayarı değiştirmedi.

## A2 — Beceriler, politika, rapor (17 Kasım 2026)

**Yapılan**
- `filo/beceri.py`: katalog (`skills/<ad>/beceri.json`), tipli girdi şeması (metin, tamsayi, mantik, secim, liste,
  eposta, yol + izinli önekler, komut = salt-okur izin listesi), çıktı şeması (anahtar_deger, satirlar, json, ham,
  belge, betik) ve son koşullar (`beklenen`, `yasak`: komut sıfırla bitse de istenen durum yoksa adım başarısız),
  risk düzeyi 0-4, kodla risk sınıflaması (`risk_sinifla`; etkin düzey = max(beyan, hesaplanan)), betik
  kütüphanesindeki betiğin de sınıflanması, sürümleme (eski sürüm `gecmis/v<N>/` altında, `fark`, `geri_don` eski
  içeriği yeni sürüm olarak yazar), düzeyi 2+'ya çıkan değişiklik kuru çalıştırma ve geri alma tanımı yoksa reddedilir.
- 18 beceri: erisim_sinamasi, sistem_envanteri, disk_durumu, servis_durumu, servis_yeniden_baslat, servis_baslat,
  paket_kur, paket_dogrula, paket_onar, dosya_dagit, kullanici_ac, yama_durumu, komut_calistir, betik_calistir,
  sonucu_donustur, eposta_gonder, standart_sunucu_teslimi (zincir), gecici_dosya_temizle (düzey 4). Debian/RHEL/Alpine
  farkını beceri çözer (apt-get/dnf/apk, systemctl/rc-service, useradd/adduser). Windows komutları beş salt-okur
  becerde var; öykünücü `#filo:<işaret>` satırıyla cevap seçer.
- Betik kütüphanesi `skills/_betikler/` (5 betik, her biri kendi çıktı şemasıyla), dosya kütüphanesi `skills/_dosyalar/`.
- `filo/politika.py`: düzey 2+ önce kuru çalıştırma, düzey 3+ onay; onay kayıtları `results/onaylar.json`; onay plana
  bağlıdır (beceri, sürüm, hedef listesi değişirse geçersiz); kipler etkilesimli / komut_satiri (`--onayla`) / bench.
- `filo/motor.py`: plan (şema, dondurulmuş hedef, etkin risk) → kuru → onay → yürütme → şema denetimi; plan sonrası
  beceri sürümü değişirse yürütme reddedilir; zincirde bir adımda düşen sunucu sonraki adımlara girmez ve raporlanır;
  geri alma.
- `filo/rapor.py`: CSV/XML/JSON/HTML (kısmi başarısızlık satır olarak kalır), dürüst özet metni, SMTP gönderimi
  (`ayarlar/posta.json`, izinli alıcı alan adları).
- Komut satırı: `beceri liste|goster|gecmis|fark|geri-al|sinifla [--betik]`, `is --beceri ... --hedef ... [--param]
  [--kuru] [--onayla] [--bicim xml] [--eposta]`, `onay liste|ver|reddet`.

**Doğrulama**
- `python -m filo is --hedef "PA*" --beceri betik_calistir --param betik=uygulama_surumu --bicim xml --eposta
  ops@lab.yerel --konu "PA surum raporu"` → 4/4 başarılı, XML belgesi, Mailpit API'sinde konu "PA surum raporu",
  ek `filo-betik_calistir-...xml` (application/xml). Aynı yol `tests/test_lab.py::test_betik_xml_posta_mailpit` içinde
  eki Mailpit'ten okuyup 4 `<sunucu>` öğesini doğruluyor.
- Laboratuvarda elle: sistem_envanteri / disk_durumu / servis_durumu / yama_durumu / erisim_sinamasi Debian, Alma,
  Alpine ve öykünmeli Windows'ta; servis_baslat onaysız → `onay_bekliyor` (hiçbir şey çalışmadı), `--onayla` ile
  çalıştı; paket_kur kuru çalıştırma (apt -s, dnf --assumeno, apk --simulate) ve gerçek kurulum (jq, tree) üç ailede;
  dosya_dagit özet doğrulamasıyla; kullanici_ac üç ailede; standart_sunucu_teslimi PB* üzerinde 3/3, HTML + posta.
- `python -m pytest`: 61 test geçti (4'ü gerçek laboratuvarda).

**Eksik / not**
- Geri alma komut satırından ayrı bir komutla çağrılmıyor (motor `geri_al` var, Kaptan ve testler kullanıyor).
- Windows komutları öykünücüde denendi; gerçek WinRM'de çalıştırılmadı (WinRM kapalı).

## A3 — Model kapısı ve iki ajan (17 Kasım 2026)

**Yapılan**
- `filo/gateway.py`: bağlantı profilleri (`ayarlar/baglantilar.json`; türler ollama, openai-uyumlu, anthropic, openai,
  gemini, agy). Anahtar ya `anahtar_ortam` (ortam değişkeni ADI) ya git dışındaki `ayarlar/gizli.json`; `ozet()` yalnız
  `anahtar_var` ve kaynağını söyler. Anthropic yerel Messages API (`/v1/messages`, `x-api-key`, `anthropic-version`),
  model kimliği kullanıcıdan. Bağlantı sınaması (`sina`), model listeleme (`/api/tags`, `/v1/models`, `/models`,
  `agy models`). Ollama: `think: false`, `num_ctx` 16384, aynı anda tek model (başka yüklü model `keep_alive: 0` ile
  boşaltılır), çağrı öncesi ısı bekçisinin `results/durum/BEKLE`/`DUR` bayraklarına bakılır. `sor_json`: dar soru +
  kod doğrulaması + hata metniyle onarım döngüsü (varsayılan 2 onarım). `FakeModel`.
- `filo/ajan_ortak.py`: kod daraltmaları — aday beceriler (4 harflik kök örtüşmesi; Türkçe ünsüz yumuşaması 5 harfte
  kökü bozuyordu), hedef seçicide talepte dayanağı olmayan grup/os/aile/öznitelik koşulunu kod çıkarır ve gerekçe izine
  yazar, ad kalıbı talepte geçmek zorunda, boş sonuçta hangi koşulun elediğini söyler; parametrelerde talepte geçmeyen
  servis/paket/kullanıcı/yol/e-posta reddedilir; biçim ve alıcı seçenekleri talepten çıkarılır, tek seçenekte model
  çağrılmaz; başarısızlık varsa modelin kısa yorumu ayrı etiketle rapora girer.
- `filo/kalfa.py`: beceri seçimi → hedef → parametre → biçim/alıcı → plan (dondurulmuş) → onay → yürütme → dönüştür →
  e-posta → rapor. Beceri değiştirmez; uygun beceri yoksa `beceri_yok` der ve hiçbir şey çalıştırmaz.
- `filo/kaptan.py`: akış kurma (en çok 6 adım, yerel adımların sırası kodla denetlenir) → hedef → adım parametreleri →
  adım adım yürütme. Hata/şema uyumsuzluğunda en çok 2 salt-okur teşhis, sonra karar (yeniden_dene / onarim:<beceri> /
  beceriyi_degistir / devret; seçenekleri kod daraltır: erişilemeyen sunucuda yalnız yeniden dene/devret, çıkış kodu 0 ama
  şema uyumsuzsa yalnız değiştir/devret). Değişiklik yeni sürüm olarak kaydedilir, risk kodla yeniden sınıflanır
  (yükselirse onay). Değişiklik adımı düzeltmezse ya da eskisiyle başarılı olan bir sunucuda bozarsa (gerileme
  sınaması, yalnız düzey 0-1 becerilerde) değişiklik geri alınır (eski içerik yeni sürüm olarak). Adım başına en çok 2
  deneme, sonra insana devir; başarısız sunucu sonraki adımlara girmez. Tam başarılı akış `akislar/` altına sabit akış
  olarak kaydedilir; `python -m filo akis calistir <ad>` modele sormadan yürütür.
- `filo/isler.py`: iş kaydı (plan, olaylar, gerekçe izi, değişiklikler, canlı ızgara, rapor), `results/isler/`.
- Komut satırı: `talep "<metin>" --ajan kalfa|kaptan [--baglanti] [--onayla] [--plan]`, `baglanti liste|sina|modeller`,
  `akis liste|calistir`. `tools/isi_bekcisi.py` Vardiya'dan kopyalanıp `results/durum` yoluna uyarlandı.

**Doğrulama**
- FakeModel testleri (`tests/test_ajanlar.py`, 14 test): onarım döngüsü, anahtarın geri dönmemesi, Kalfa uçtan uca
  (betik → XML → e-posta), uygun beceri yok, uydurma parametre reddi, onaysız değişiklik yapılmaması, kısmi başarısızlığın
  raporlanması; Kaptan onarım becerisiyle devam (dpkg kesik → paket_onar → paket_kur), şema uyumsuzluğunda betiğin yeni
  sürümü, deneme sınırı ve devir, riski yükselten değişikliğin onaysız çalışmaması, düzeltmeyen değişikliğin geri
  alınması, gerileme sınaması, sabit akışın yeniden yürütülmesi.
- Yerel model duman sınaması (ısı bekçisi açık, `hal=calis`, GPU 47-53 °C; Ollama `qwen3:8b`, düşünme kapalı, num_ctx
  16384). Gerçek laboratuvarda:
  1. Kalfa "Adı PA ile başlayan sunucularda uygulama_surumu betiğini çalıştır, sonucu XML yap, ops@lab.yerel adresine
     e-posta at": ilk denemede model `hicbiri` dedi (aday satırında betik adları yoktu, kök eşleşmesi bozuktu) → düzeltildi;
     ikinci denemede model hedefe talepte olmayan `rol=uygulama` ekledi ve 4 PA sunucusundan 2'si düştü → kod denetimi
     eklendi; üçüncü koşuda onarım döngüsü koşulu reddetti, 4/4 başarılı, XML eki Mailpit'e gitti (4 model çağrısı).
     Model yine de istenmemiş `argumanlar: ["PA"]` yazdı (zararsız, betik argüman kullanmıyor; giderilmedi).
  2. Kalfa "PB grubundaki sunucuların disk doluluğunu göster", PB-DB-01 konteyneri durdurulmuşken: `kismi`, 2/3,
     PB-DB-01 `erisilemedi` (Connection refused) raporda, model yorumu ayrı etiketli.
  3. Kaptan, PA-APP-02'de sürüm dosyasının biçimi değiştirilmişken "... uygulama_surumu betiğini çalıştır, CSV yap,
     ops@lab.yerel adresine gönder": dört koşu yapıldı (her biri bir harness zayıflığını gösterdi ve düzeltildi: e-posta
     adresindeki "yerel" sözcüğü öznitelik dayanağı sayılıyordu; şema sorununda model servis yeniden başlatmayı seçti →
     seçenekler daraltıldı). Son koşuda Kaptan doğru eylem sınıfını seçti (betiği değiştir), iki yeni sürüm yazdı (risk 0→0,
     fark kayıtlı) ama qwen3:8b'nin betikleri `surum=` önekini üretmedi; 2 denemeden sonra PA-APP-02 insana devredildi,
     sonuç `kismi`, PA-APP-01 başarılı, CSV posta gönderildi; sahte başarı yok. Bu koşudan sonra "düzeltmeyen değişikliği
     geri al" ve gerileme sınaması eklendi (FakeModel ile sınandı, gerçek modelle yeniden koşulmadı).
  Not: istenen 2-3 talep sınırı, zayıflıkları düzeltirken aşıldı (toplam 7 talep koşusu, hepsi kısa; tam bench koşusu
  yapılmadı). Kaptan koşuları geçici bir katalog kopyasında yapıldı; depodaki beceriler v1'de kaldı.

**Eksik / not**
- Anthropic, OpenAI, Gemini, agy ve OpenAI uyumlu bağlantılar gerçek bir uca karşı sınanmadı (anahtar yok, LM Studio
  çalışmıyor); kod yolu yalnız okunarak ve FakeModel ile denendi. Ollama bağlantısı gerçek sunucuyla sınandı.

## A4 — Arayüz (17 Kasım 2026)

**Yapılan**
- `filo/web.py` (yalnız standart kitaplık): `python -m filo web --port 8790`, yalnız 127.0.0.1'e bağlanır ve başka
  adresten gelen isteği 403 ile reddeder; değiştiren her POST `X-Filo: 1` başlığı ister (başka bir sitenin sayfası
  tarayıcı üzerinden istek atamaz). Talep planlama ve yürütme arka plan iş parçacığında; aynı anda tek iş yürür. Onay
  gerektiren adımda iş onay kaydını bekler (en çok 30 dk); onay Talep masasından ya da Onaylar sekmesinden verilir.
- `filo/static/index.html` (bağımlılıksız, dış yazı tipi yok): Talep masası (plan önizleme, dondurulmuş hedef listesi,
  risk ve onay gereği, Planı yürüt / Vazgeç, onay düğmeleri), Koşular (canlı sunucu ızgarası, adım zaman çizgisi,
  ajanın gerekçe izi ve onarım denemeleri, kodun çıkardığı koşullar, Kaptan'ın değişiklikleri ve renkli fark, adım
  tabloları, kuru çalıştırma ve belge önizlemesi), Envanter (seçici, erişim sınaması, WinRM sınaması ve kullanıcı
  komutları), Beceriler (girdi/çıktı şeması, risk ve gerekçesi, komutlar, kuru, geri alma, sürüm geçmişi, iki sürüm
  arası fark, sürüme dönüş), Onaylar, Bağlantılar (ekle/düzenle/sil/varsayılan, sına, kısa soruyla sına, modelleri
  listele; her tür için yardım metni; anahtar alanı parola tipinde, geri gösterilmez), Bench, Denetim izi (zincir
  durumu, süzgeç). Durdurma düğmesi üst çubukta her sayfada; basılıyken uyarı bandı çıkar. Açık/koyu tema.
- Denetim izinde bulunan hata düzeltildi: yük alanı `ozet` zincirin kendi `ozet` alanını eziyordu ve zincir A1'den beri
  bozuk görünüyordu; zincir alanları `_onceki`/`_ozet` oldu, eski dosya `results/denetim-A1-A3-alan-cakismali.jsonl`
  adıyla saklandı, yeni dosya temiz başladı; regresyon testi eklendi.

**Doğrulama**
- Sunucu başlatıldı; her GET ucu ve POST ucu bir Python betiğiyle çağrıldı: başlıksız POST 403, durdurma basılıyken talep
  400, bilinmeyen grup 400, bağlantı kaydında anahtar ne cevapta ne `baglantilar.json`'da, Ollama sınama ve model listesi
  çalıştı, sahte anahtarlı Anthropic sınaması "HTTP 401 invalid x-api-key" döndü (yani istek gerçekten
  `/v1/messages` yolunun sahibine gitti; gerçek anahtarla sınanmadı), WinRM sınaması arayüzden çalıştı.
- `tests/test_web.py`: gerçek HTTP sunucusu + gerçek `Ofis`, FakeModel ile talep → plan (dondurulmuş hedef PB-WEB-01,
  onay gerekli) → yürüt → kuru çalıştırma → `onay_bekliyor` → `/api/onay` ile onay → yürütme → `bitti`; biri sahte
  taşıyıcıyla, biri gerçek laboratuvarda (jq PB-WEB-01'e kuruldu, `dpkg-query` ile doğrulandı). Denetim izinde talep,
  plan, kuru_calistirma, onay_istendi, onay_verildi, adim satırları ve zincir sağlam.
- Tarayıcı bölmesinde sayfa açıldı: konsol hatası yok, sekmelerin hepsi içerik gösteriyor, koyu tema çalışıyor, uzun JSON
  taşması düzeltildi (hiçbir sekmede yatay kaydırma yok, 1024 px).

**Eksik / not**
- Arayüzden gerçek yerel modelle talep yürütülmedi (duman sınaması sınırı nedeniyle); arayüz yolu FakeModel ile uçtan uca
  sınandı, gerçek model yolu komut satırında sınandı.
- Dar ekranda (telefon) düzen denenmedi.

## A5 — Bench iskeleti (17 Kasım 2026)

**Yapılan**
- `filo/bench/senaryo.py`: senaryo biçimi (kimlik, seviye, başlık, kaynak + kaynak_turu, talep, kurulum = bozukluk
  enjeksiyonu, onay politikası, `degisebilir` sunucular, hakem ölçütleri, `yasak` ölçütler, referans çözüm, adım
  bütçesi) ve biçim denetimi.
- `filo/bench/hakem.py`: laboratuvarın gerçek durumuna bakar (docker exec ile paket, servis, dosya, kullanıcı, komut,
  servis pid'i; Mailpit API'siyle posta gövdesi ve ekleri). Zararlılar ayrı sayılır: `yanlis_sunucu` (`degisebilir`
  dışındaki sunucunun parmak izi — paketler, kullanıcılar, servis durumları ve pid'leri, uygulama dosyaları, sudoers,
  authorized_keys, depo ayarı — değişti), `sahte_basari` (kol "basarili" dedi ama ölçüt tutmadı), `onaysiz_degisiklik`
  (`yasak` ölçütü tuttu). `beyan` ölçütünde `muaf`: iş gerçekten yapıldıysa beyan serbest.
- `filo/bench/kollar.py`: `bos`, `referans` (docker exec + SMTP, harness'i kullanmaz), `yardimsiz` (aynı model, ham kabuk
  + ham e-posta, aynı adım bütçesi; beceri/şema/onay/dondurma yok), `kalfa`, `kaptan` (her senaryoda katalog temiz bir
  kopyadan başlar; onayı senaryo verir; denetim izi koşu dizinine).
- `filo/bench/kos.py`: `python -m filo bench liste|dogrula|kos|rapor`. Her koşudan önce laboratuvar sıfırlanır (~2.5 sn),
  bozukluklar konur, parmak izleri alınır. Model kolları ısı bekçisi son 3 dakikada yazmadıysa başlamaz; her senaryo
  öncesi `BEKLE` bayrağı beklenir; `results/bench/KILIT` ile tek koşu.
- 15 tohum senaryo (`bench/temel` 4, `bench/orta` 6, `bench/ileri` 5). Önce `docs/arastirma/05-forum-vakalari.md`
  içindeki, `lab_uyarlamasi` "yalnız gerçek üründe" olmayan vakalar kullanıldı (7 senaryo, `kaynak_turu: forum`,
  `kaynak` = konu adresi: F-SV-002, F-SV-012, F-SV-020, F-SV-009, F-AK-002, F-AK-006, F-AK-008); kalanlar
  `docs/arastirma/03-vaka-taslaklari.md` taslaklarından (kaynağı olanlar `taslak`, "kaynak: yok" olanlar `turetilmis`).
- Bu aşamada harness'e eklenenler: e-posta eksiz giderse sunucu başına sonuçlar gövdeye girer; Kalfa onay reddinde ve
  Kaptan yarıda kalan akışta istenen e-posta raporunu yine gönderir (ne yapılacaktı, neden yapılmadı); laboratuvar
  sıfırlamasının erişim beklemesi ana denetim izine değil `results/lab-denetim.jsonl` dosyasına yazar.
- Arayüzün Bench sekmesi senaryoları, doğrulama durumunu ve koşu sonuçlarını (kol × seviye, geçen, zararlı, sahte başarı,
  ortalama model çağrısı) gösterir; koşu seçili senaryolarla ve onayla başlar.

**Doğrulama**
- `python -m filo bench dogrula` (gerçek laboratuvar): 15/15 senaryoda referans çözüm GEÇTİ (zararlı yok), boş çözüm
  KALDI ("15/15 senaryo doğrulandı").
- `tests/test_bench.py`: biçim (≥12 senaryo, her seviyede ≥4, forum kaynakları konu adresi), hakem posta/ek/sayı ölçütü,
  beyan muafiyeti, yanlış sunucu ve sahte başarı tespiti, yardımsız kolun ham araçları ve bütçe bitince başarı iddia
  etmemesi, rapor tablosu; laboratuvarda: senaryolu FakeModel ile Kalfa kolu T03'te GEÇTİ (zararsız), iş yapmadan
  "başarılı" diyen yardımsız kol T01'de `sahte_basari` olarak işaretlendi.
- Tam model koşusu başlatılmadı (görev gereği).

**Eksik / not**
- Kolların gerçek modelle karşılaştırması yapılmadı; sonuç tablosu boş.
- I03'te hakem, Kalfa'nın şema hatası metninde ham satırın (1.4.2) geçmesi yüzünden yalnız posta sayısına güvenemez;
  bu yüzden I03 başarı için `beyan: basarili` de ister. Ham çıktıyı gizleyip sahte biçimde başarı diyen bir kol bu
  ölçütü aldatabilir; daha sıkı bir ölçüt (CSV'de alan düzeyinde sürüm) sonraya kaldı.
- `yardimsiz` kolu ham e-posta aracına da sahip (yalnız kabukla e-posta göndermenin laboratuvarda yolu yok); bu, kol
  tanımındaki "yalnız ham kabuk" ifadesinden bilinçli bir sapmadır.
- O03 (standart teslim) yardımsız kol için kurumsal bilgi gerektirir (standart paketler jq, tree ve motd); harness bu
  bilgiyi beceri kataloğunda taşır. Karşılaştırmada bu fark bilerek bırakıldı.

## Genel durum (17 Kasım 2026 sonu)

- `python -m pytest`: 85 test geçti (laboratuvar açıkken; laboratuvar isteyenler `lab` işaretli, kapalıyken atlanır).
- Laboratuvar açık bırakıldı (`python -m filo lab kapat` ile kapanır). Ollama sunucusu, ısı bekçisi ve arayüz sunucusu
  oturum sonunda durduruldu.
- Devir notundan sapmalar: (1) yardımsız kola ham e-posta aracı verildi (yukarıda); (2) Windows hedefi `PW-WIN-01`
  adıyla PA* dışında tutuldu, böylece PA* doğrulaması yalnız gerçek Linux sunucularla yapıldı; (3) konteynerlerde systemd
  yerine `filo-svc` + systemctl/rc-service ince katmanı.

## İlk model koşusu ve öncelik düzeltmesi (17 Kasım 2026, ana oturum)

**İlk tam koşu** (`results/bench/ilk-qwen3-8b`, qwen3:8b, düşünme kapalı, 15 senaryo x 3 kol, ısı bekçisi açık, en yüksek ekran
kartı sıcaklığı 67 °C):

| Kol | Geçen | Zararlı | Sahte başarı | Ortalama çağrı |
|---|---|---|---|---|
| kalfa | 9/15 (temel 2/4, orta 5/6, ileri 2/5) | 1 | 1 | ~2,8 |
| kaptan (sonuç dosyasında `reis`) | 9/15 (temel 2/4, orta 3/6, ileri 4/5) | 1 | 1 | ~7,7 |
| yardimsiz | 4/15 (temel 1/4, orta 2/6, ileri 1/5) | 3 | 2 | ~12 |

İncelenmedi: temel seviyede iki harness'li kolun da 2/4'te kalması (orta ve ileriden düşük), kalfa ve kaptan'daki birer
zararlı/sahte başarı sonucu. Tek koşu; tekrar ve güven aralığı yok.

**Öncelik düzeltmesi:** bu koşu sunucu/akış olmadan, doğrudan SSH üzerinden çalışan katmanı ölçer. Kullanıcının asıl istediği
gerçek sunucu otomasyonu ve akış otomasyonu üzerinde adminliktir (bkz. `00-devir-notu.md`, "Öncelik düzeltmesi"). Kurulum yolu:
`docs/arastirma/06-gercek-urun-kurulumu.md` (akış otomasyonu 26.4, sunucu otomasyonu 25.4; indirme SLD portalından kullanıcının OpenText hesabıyla).

## Gerçek ürün indirme denemesi (17 Kasım 2026, ana oturum)

- İndirme portalı: Software Licenses and Downloads, `https://sld.microfocus.com/mysoftware/index`. Girişi OpenText Connect
  hesabından ayrıdır (`extlogin.opentext.com`, hesap `microfocus.com/selfreg` üzerinden açılır). Kullanıcı hesabı açtı ve
  Chrome'da giriş yaptı; lisans koşulları penceresi geçildi.
- Sonuç: yeni hesapta ürün yetkisi yok. Portal "It appears you currently do not have permission to manage these software
  entitlements" diyor ve yalnız "Request Access" sunuyor; erişim talebi SUID, Order Number ya da Software Serial Number
  ister. İndirme bölümü görünmüyor; akış otomasyonu 26.4 ve sunucu otomasyonu 25.4 paketleri indirilemedi.
- Herkese açık deneme indirme sayfası bulunamadı (eski Micro Focus "free trial" adresi ürün listesine yönleniyor; ürün
  sayfasında yalnız "Request a demo" var).
- Açık yollar: (1) ürünü kullanan bir kurumun SUID / sipariş numarası ile "Request Access", (2) OpenText'ten değerlendirme
  talebi, (3) beklerken akış otomasyonu'nun açık kaynak çekirdeği CloudSlang ile akış tarafını denemek (gerçek ürün değildir).

# İkinci tur (17 Kasım 2026)

Kullanıcı kararları: gerçek sunucu/akış kurulmayacak; Filo o ürünleri yönetmez, işlerini kendi katmanıyla yapar. Dinamik ajanın
yeni adı Kaptan. Sunucularda Go ile yazılmış bir ajan çalışacak. Kalfa ile Kaptan iki ayrı ürün sayfası olacak.

## B1 — Ad değişikliği: Reis → Kaptan

**Yapılan**
- `filo/reis.py` → `filo/kaptan.py`, sınıf `Kaptan`, ajan adı `kaptan`; komut satırı `--ajan kaptan`, bench kolu `kaptan`;
  web, testler, README ve devir notu güncellendi. Eski sonuç dosyaları yeniden yazılmadı: `bench rapor`
  (`ESKI_KOL_ADLARI`) ve arayüz eski `reis` kolunu ve eski iş kayıtlarını `kaptan` diye okur.
- Bu sırada bulunan iki ortam sorunu (adla ilgisi yok, ama testleri düşürüyordu):
  1. `lab/anahtar/filo_lab` dosyasının ACL'si kalıtılan izinlere dönmüştü (Windows OpenSSH "bad permissions" deyip
     anahtarı yok sayıyor, bütün sunucular "Permission denied"). Eski kod izni yalnız anahtar üretilirken ve `whoami`
     çıktısıyla veriyordu; `whoami` çıktısının kod sayfası kullanıcı adındaki "İ" harfini bozduğu için icacls aslında hiç başarılı
     olmamış olabilir. `lab.anahtar_izni()` artık kullanıcı adını ortamdan kurar, hata verirse durur ve `kur` ile
     `sifirla` her seferinde uygular (proje dosyasının izni; sistem ayarı değil).
  2. Durdurulmuş konteynere SSH artık "Connection refused" yazmıyor: Docker Desktop'un port vekili bağlantıyı kabul edip
     iletisiz kapatıyor, ssh 255 ile sessiz çıkıyor ve sonuç `erisilemedi` yerine `hatali` oluyordu. SSH taşıyıcısı
     çıktısız 255'i `erisilemedi` sayar.

**Doğrulama**
- `python -m pytest -q`: 85 test geçti (ACL ve 255 düzeltmesinden sonra `tests/test_lab.py` 4/4).
- `python -m filo calistir --hedef "PA*" --komut hostname` → 4/4 başarılı.

## B2 — Go ajanı (`ajan/`, ikili `filo-ajan`)

**Yapılan**
- `ajan/` (yalnız Go standart kitaplığı, `go 1.23`): `main.go` (ayar, kayıt, kalp, uzun yoklama, iş dağıtımı, dosya alma),
  `imza.go` (anahtar türetme, istek/yanıt/iş imzası, iş doğrulama, yeniden oynatma koruması), `yurut.go` (betik
  standart girdiden `sh -s`, zaman aşımı, çıktı sınırı + `kesildi`, iptal; sonuç şeması `yurutme.py` ile aynı),
  `surec_unix.go` (süreç grubu, root ise iş istenen kullanıcının uid/gid/ek gruplarıyla), `surec_windows.go`,
  `sistem.go` (işletim sistemi, dağıtım, aile, çekirdek, mimari, paket ve hizmet yöneticisi, ajan sürümü).
- Kimlik ve imza: kurulumda verilen tek kullanımlık, sunucuya bağlı, 15 dk geçerli kayıt belirteci → ajana özel 256 bit
  gizli anahtar. İki yön ayrı türetilmiş anahtar kullanır (istek: HMAC(gizli,"filo-istek-v1"), iş: HMAC(gizli,"filo-is-v1")).
  Her istek imzalı + zaman damgalı (±60 sn) + nonce'lu (tekrar reddedilir); çekirdeğin cevabı isteğin nonce'una bağlı
  imzayla döner (imzasız cevap yok sayılır); iş paketi `{govde, imza}` — ajan imzayı, ajan kimliğini, geçerlilik
  süresini, türü ve iş kimliğinin tekrarını doğrulamadan çalıştırmaz. Ajanda gizli anahtar `kimlik.json` (0600), belirteç
  kayıttan sonra ayar dosyasından silinir; günlüğe yazılmaz. Çekirdekte gizliler `ayarlar/ajan_gizli.json` (git dışı),
  belirteçlerin yalnız özeti `results/ajanlar/belirtecler.json`.
- Çekirdek: `filo/ajan_kapisi.py` (standart kitaplık, ayrı port 8795, yalnız 127.0.0.1'e bağlı). Konteynerler Docker
  Desktop'un `host.docker.internal` vekiliyle ulaşır (denendi: 127.0.0.1'e bağlı dinleyiciye konteynerden erişiliyor;
  güvenlik duvarı ayarı gerekmedi). Ajan protokolü `/ajan/v1/{kayit,kalp,yokla,sonuc,dosya}`, yerel istemciler için
  `/yerel/v1/...` (`results/ajanlar/yerel.anahtar` ile). Durdurma düğmesi basılıyken kapı iş vermez ve çalışan işleri
  iptal ettirir. Canlılık: son imzalı istek 35 sn'den yeni (kalp 10 sn). Ölen ajanın açık yoklaması iş almasın diye
  bekleyen yoklamada bağlantının kapanıp kapanmadığına bakılır; cevabı yazılamayan işler kuyruğa döner.
- `python -m filo ajan kapi` (ayrı süreç) ya da `python -m filo web` (aynı süreçte, port boşsa). Laboratuvarda düz HTTP:
  imza bütünlüğü ve kimliği korur, gizliliği değil (gerçek ağda önüne TLS gerekir; belgede yazılı).
- `filo/ajan_istemci.py`: `AjanTasiyici` ve `YedekliTasiyici`; `erisim.tasiyici_sec` SSH sunucusunda canlı ajan varsa
  yedekli taşıyıcıyı verir: iş ajandan gider, ajan 8 sn içinde almazsa SSH'a düşülür (`tasiyici: "ssh"` +
  `tasiyici_notu`), o sunucu 40 sn şüpheli sayılır. `yurutme.py` sonucun `tasiyici` alanını gerçekten kullanılan yola göre
  yazar; denetim izindeki `yurutme` satırı sunucu başına `tasiyici` (ve varsa notu) taşır. Komut satırı tablosunda YOL
  sütunu.
- Beceriler (`tur: "yonetim"`, işleyiciler `filo/ajan_yonetimi.py`): `ajan_kur` (SSH keşif → kapıdan belirteç → scp ile
  ikili → stdin'den ayar betiği → hizmet → kalp bekleme; kuru çalıştırma, geri alma `ajan_kaldir`), `ajan_durumu` (kapıdan,
  sunucuya bağlanmaz), `ajan_onar` (süreç yoksa yeniden başlatır, kimlik yoksa yeni belirteçle yeniden kaydeder, ikili
  yoksa yeniden kurar; "canlı" kaydı eskiyse taze kalp bekler), `ajan_kaldir`. Motor `yonetim` türünü ve başka bir
  beceriye işaret eden geri almayı (`{"beceri": "ajan_kaldir"}`) destekler. Kalfa ve Kaptan bu becerileri görür.
- Yaşatma: laboratuvar konteynerlerinde systemd yok; ajan konteynerin servis yöneticisi `filo-svc`'ye `filo-ajan`
  servisi olarak tanımlanır (root çalışır, işleri `filo` kullanıcısıyla yürütür). `filo-svc` ölen servisi kendiliğinden
  başlatmaz: bunu `ajan_onar` yapar. Gerçek systemd'li sunucuda `Restart=always` birimi yazılır (kod yolu var, systemd'li
  bir hedefte DENENMEDİ). `lab sifirla` konteynerleri yeniden yarattığı için ajanlar gider; sıfırlama kapıdaki kayıtları
  da düşürür.
- Derleme: `python -m filo ajan derle` → `docker run golang:1.23-alpine` (CGO kapalı): `go vet`, `go test`, linux/amd64,
  linux/arm64, windows/amd64 → `ajan/cikti/` + `SHA256SUMS` (git dışı). Derleme önbelleği adlı Docker birimlerinde.

**Doğrulama**
- `python -m filo ajan derle` → go1.23.12, `ok filo/ajan`, üç ikili (5.6 / 5.4 / 5.8 MB). Go testleri (konteynerde root
  olarak, 11 test): çapraz dil imza örneği, imzasız / başka anahtarlı / gövdesi değiştirilmiş / başka ajana ait / süresi
  dolmuş / tekrarlanan işin reddi, sonuç şeması, zaman aşımının süreç grubunu öldürmesi, çıktı sınırı ve `kesildi`, iptal,
  başka kullanıcı adına çalıştırma (`nobody`), dosya almada özet doğrulaması ve kip, imzasız çekirdek cevabının yok
  sayılması, kimlik dosyasının 0600 yazılıp belirtecin silinmesi, sistem bilgisi.
- `tests/test_ajan_kapisi.py` (8, sahte Python ajanıyla): aynı imza örneği, belirtecin tek kullanımlık ve sunucuya bağlı
  olması (diskte yalnız özet), imzasız / yanlış anahtarlı / eski zaman damgalı / tekrarlanan nonce'lu isteğin 401 alması,
  işin ajandan gidip aynı şemada dönmesi, ajan almazsa SSH yedeğine düşülmesi, taşıyıcı seçimi ve denetim izinde yol,
  durdurma düğmesinin ajandaki işi iptal etmesi, kaldırılan ajanın 410 alması.
- `tests/test_ajan_lab.py` (4, gerçek Go ajanı PB-APP-01 konteynerinde, sınamaya özel kapı): kimlik ve ayar dosyası 0600,
  belirteç silinmiş, gizli anahtar ne ajan günlüğünde ne denetim izinde; çalıştırma (`filo` kullanıcısı, stderr, çıkış 4),
  zaman aşımı, 200 KB çıktının 1000 baytta kesilip `kesildi` olması, sistem bilgisi (alpine/apk); dosya alma (0640, sahibi
  filo); **sahte imzalı iş ve imzadan sonra gövdesi değiştirilmiş iş kapı kuyruğuna konuldu → gerçek ajan ikisini de
  `reddedildi` diye geri çevirdi, dosya oluşmadı**.
- Laboratuvarda elle (ayrı süreçte `python -m filo ajan kapi`):
  - `python -m filo ajan kur --hedef "os:linux" --onayla` → 8/8 başarılı (Debian, AlmaLinux, Alpine; her biri ~1-2 sn);
    `ajan durum` → 8 sunucu `canli`, sürüm 0.2.0, dağıtım adları ajandan.
  - `python -m filo calistir --hedef "PA*" --komut "hostname; id -un"` → 4/4 başarılı, YOL `ajan`, kullanıcı `filo`;
    `is --beceri betik_calistir --param betik=uygulama_surumu --bicim xml` → 4/4 ajan üzerinden, XML üretildi.
  - PA-DB-01'deki ajan `pkill` ile öldürüldü: hemen ardından iş PA-DB-01'de 8.2 sn sonra `ssh` ile tamamlandı ("ajan işi
    zamanında almadı; SSH'a düşüldü"), PA-APP-01 ajandan; 36 sn sonra `ajan durum` → PA-DB-01 `ajan yok`, iş doğrudan
    SSH'tan (0.14 sn). `python -m filo ajan onar --hedef "PA-DB-01,PA-APP-01" --onayla` → PA-APP-01 "eylem yok (zaten
    çalışıyor)", PA-DB-01 yeniden başlatıldı; sonraki iş yine `ajan` yolundan.
- `python -m pytest -q`: 97 test geçti.

**Eksik / not**
- Windows ikilisi derleniyor ama gerçek bir Windows sunucuda DENENMEDİ (başka kullanıcı adına çalıştırma Windows'ta yok).
  linux/arm64 ikilisi derleniyor, arm64 bir makinede denenmedi.
- systemd birimi yazan kod yolu systemd'li bir hedefte denenmedi (laboratuvarda systemd yok).
- Kapı ile ajan arası düz HTTP (laboratuvar); TLS yok. Gizli anahtarın döndürülmesi (rotation) yok; yeniden kurulum yeni
  anahtar üretir.
- Ajanın kendini güncellemesi yok (dosya alma yeteneği bunun için temel; kurulum yeniden `ajan_kur` ile yapılır).

## B3 — Yeni sunucu teslimi

**Yapılan**
- `ayarlar/teslim_politikalari.json`: kurallar (`*-WEB-*` → `web`, `grup:app` → `uygulama`) ve profiller (beceri
  zinciri; risk 3+ adım `on_onayli` değilse insan onayı bekler; `rapor.alici`; `yarida_kalirsa: kaptan|insan`,
  `kaptan_inisiyatif`). `web` profili: erişim, envanter, jq+tree (ön onaylı), paket doğrulama, `webops` kullanıcısı
  (ön onaylı DEĞİL → onay), motd, `webd` başlat (ön onaylı), `webd` durumu, HTML teslim raporu e-postası.
- `filo/teslim.py`: `Teslim` (zincir motor üzerinden; ön onay denetim izine `onaylayan: teslim_politikasi:<profil>`
  diye yazılır; onay bekleme; yarıda kalırsa Kaptan devralır: kalan adımlar ve hata talep olur, kalan adımlar aday
  olarak zorunlu verilir, düzey profilden), kapı kayıt dinleyicisi. Yalnız envanterde `teslim=bekliyor` işaretli
  sunucu teslim edilir: çalışan bir sunucuya sonradan ajan kurmak onu "yeniden teslim" etmez (ilk taslakta PA-WEB-01 de
  profile düşüyordu; işaret bu yüzden eklendi). Başarılı teslim işareti `tamam` yapar ve `results/teslimler.json`'a yazar.
- Laboratuvar: `docker-compose.yml`'de `profiles: ["yeni"]` ile iki yeni sunucu (PA-WEB-02 Debian :2209, PB-APP-02
  Alpine :2210). `python -m filo lab yeni-sunucu <ad> [--kaldir]` sıfırdan açar, `webd`'yi durdurur (yeni sunucuda
  servis henüz etkin değil), `ayarlar/envanter.ek.json`'a (git dışı) `teslim=bekliyor` ile ekler, known_hosts'u yazar.
  Tam `lab sifirla` yeni sunucuları kapatır ve envanterden çıkarır.
- `teslim_uygula` becerisi (`tur: yonetim`): teslimi talep üzerine başlatır (Kalfa/Kaptan seçebilir).
- `depo_onar` becerisi (risk 3, Debian ve Alpine; eskisini `/var/backups/filo-depo`'ya alır, kuru ve geri alması var).
- Komut satırı: `python -m filo teslim liste|denetle|baslat <sunucu>`.

**Doğrulama**
- Gerçek laboratuvarda (kapı ayrı süreçte, ajanlar canlı): `lab yeni-sunucu PA-WEB-02` → `ajan kur --hedef PA-WEB-02
  --onayla` → kapı kaydı gördü, `web` teslimi kendiliğinden başladı, `kullanici_ac` adımında onay istedi
  (`onay liste` → `fda835b9 bekliyor kullanici_ac`), `onay ver` sonrası 9 adımın hepsi `basarili`, teslim `bitti`. Hakem
  gözüyle (docker exec): `jq 1.6`, `tree 2.1.0`, `webops` uid 1001, `/etc/motd` Filo metni, `webd active`; Mailpit'te
  "Filo teslim raporu: PA-WEB-02 (bitti)" + HTML eki. Denetim izinde paket_kur ve servis_baslat
  `onaylayan: teslim_politikasi:web, on_onay: true`, kullanici_ac `onaylayan: komut_satiri:<kullanıcı>`; bütün yürütme
  satırları `tasiyici: ajan`.
- `tests/test_teslim.py` (5): politika geçerli ve kurallar; insan her onayı reddederken yalnız ön onaylı adımların
  çalışması ve zincirin `kullanici_ac`'ta durup insana devredilmesi + rapor postası; onayla tamamlanma; **bozuk depoda
  zincir paket_kur'da durur, Kaptan düzey 3 ile devralır, `depo_onar` (izinli) → paket_kur → kalan adımlar, teslim
  `bitti`**; işaretsiz sunucuya ajan kurmanın teslim başlatmaması.
- Bench: O07 (teslim) ve I06 (bozuk depoda teslim) senaryoları (B7).

**Eksik / not**
- Bozuk depoda Kaptan devralması gerçek laboratuvarda gerçek modelle bench I06 içinde koşuldu (B7 sonucuna bakın); ayrıca
  elle denenmedi.
- `depo_onar` RHEL ailesi için tanımlı değil (özgün depo dosyaları elde yok); RHEL'de "komut tanımlı değil" der.

## B4 — Kaptan'ın inisiyatif düzeyi

**Yapılan**
- `filo/kaptan.py`: `DUZEYLER` 0-3 (0 yalnız öner, 1 teşhis serbest (risk 0-1), 2 geri alınabilir onarım serbest
  (risk ≤ 2), 3 beceri ve servis/paket değişikliği serbest (risk ≤ 3)); düzey 4 yok, risk 4 her düzeyde insan onayı.
  Varsayılan `ayarlar/kaptan.json` (2), talep başına arayüzden/API'den. Kaptan'ın bütün yürütmeleri (ana adım, teşhis,
  onarım, gerileme sınaması, rapor e-postası) tek kapıdan geçer (`_calistir`): `izinli` → motorun onay kapısı atlanır,
  denetim izine `onaylayan: inisiyatif:<n>`; `onay_gerekli` → plan onay ister (arayüzde insan, bench'te senaryo);
  düzey 0 → hiçbir şey çalışmaz, rapor plan + gerekçe + her adımın kaç düzeyde onaysız geçeceği, durum `oneri`.
  Beceri değiştirme düzey 3 ister: altında seçenek modele sunulmaz ve `_degistir` kodla ikinci kez reddeder. Her karar
  iş kaydının `inisiyatif.kararlar` listesine (beceri, risk, düzey, karar, açıklama, amaç, sonuç) yazılır.
- Bench: senaryo `kaptan_inisiyatif` verebilir; vermezse 3 (ilk turdaki davranışa eşdeğer: risk 3'ü senaryo zaten
  onaylıyordu, risk 4 yine senaryonun onayına kalır).

**Doğrulama**
- `tests/test_inisiyatif.py` (7): aynı arıza (yanlış yapılandırma + duran servis; akış servis_durumu → dosya_dagit →
  servis_yeniden_baslat), insan her onayı reddediyor: düzey 0 → tek komut gitmedi, `oneri`; düzey 1 → teşhis çalıştı,
  dosya_dagit onay gerekti → reddedildi, hiçbir şey değişmedi; düzey 2 → dosya dağıtıldı, servis onay gerekti →
  reddedildi; düzey 3 → hepsi izinli, `bitti`; düzey 3'te risk 4 (geçici dosya silme) onay gerekti → reddedildi;
  düzey 2'de model "beceriyi_degistir" dese de değişiklik istenmedi, katalog v1'de kaldı; düzey 4 kurulamıyor.
- qwen3:8b ile arayüzden (aşağıda B6): düzey 3, PA-APP-01'de dpkg kesik, "PA-APP-01 ve PA-WEB-01 sunucularına jq paketini
  kur, sonucu ops@lab.yerel adresine gönder" → kararlar: paket_kur r3 izinli (kısmi), paket_dogrula ve komut_calistir
  teşhis r0 izinli, paket_onar r3 onarım izinli, paket_kur r3 izinli (başarılı), eposta r1 izinli; `bitti`, 12 model
  çağrısı.

## B5 — Beceriye dönüştürme

**Yapılan**
- `filo/donustur.py`: (a) `isten_beceri`: bitmiş (`bitti`) Kaptan akışı → `zincir` beceri (adımların parametreleri üst
  düzey girdiye taşınır, varsayılan eski değer; adımda `{ad}` yer tutucusu olur — motor zincirde bunu girdiden doldurur;
  sunucu adları beceriye gömülmez; Kaptan'ın duruma özgü onarımları kalıcı adım olmaz, açıklamaya yazılır); tek seferlik
  `betik_calistir`/`komut_calistir` işi → kendi komutunu taşıyan `uzak` beceri (mutlak yollar `yol` parametresi olur).
  Risk `etkin_risk`/`risk_sinifla` ile kodla, tanım `tanim_dogrula` + yer tutucu/girdi tutarlılığıyla denetlenir,
  `surum: 1`, `kaynak` (iş kimliği, talep), etiketler talepten ve paket/servis adlarından. (b) `tariften_beceri`:
  model taslak yazar → kod denetimi (ad, tipler, çıktı biçimi, komut anahtarları, tanımsız/kullanılmayan yer tutucu,
  risk 2+ ise kuru ve geri alma) hatayla geri sorar → sınama sunucusunda kuru çalıştırma (risk 0-1: komut + çıktı
  şeması; 2+: kuru komutu) → geçerse katalog v1, geçmezse `results/taslaklar/` altında hatasıyla.
- Kalfa, seçtiği zincir kendi dönüştürme/e-posta adımını içeriyorsa ikincisini eklemez.
- Arayüz: Kaptan'da başarılı akışta "Beceriye dönüştür" ve "Sabit akış olarak kaydet"; Kalfa'da bitmiş işte "Bu işi
  beceriye dönüştür"; Beceriler sayfasında "Tariften yeni beceri".

**Doğrulama**
- `tests/test_donustur.py` (5, FakeModel): Kaptan akışı → zincir v1 (girdi betik/bicim/alici, risk 1, sunucu adı yok) →
  benzer talepte aday listesinde → Kalfa 3 model çağrısıyla (beceri, hedef, parametre) `bitti`, tek posta; duruma özgü
  onarım kalıcı adım olmuyor; tek seferlik betik işi `{yol}` parametreli uzak beceri; tarif: tanımsız yer tutucu ve
  yazan komut (risk 0 beyanı kodla 2'ye çıktı, kuru/geri alma yok) reddedilip onarıldı, kuru çalıştırma geçti, katalogda;
  kuru çalıştırması şemaya uymayan taslak kataloğa girmedi.
- **qwen3:8b ile bir kez (arayüz, gerçek laboratuvar, ajanlar canlı):** yukarıdaki Kaptan akışı (12 çağrı, `bitti`) →
  "Beceriye dönüştür" → `jq_kur_ve_bildir` v1 (zincir, risk 3, girdi paketler/alici/konu). İlk denemede dönüştürme
  Kaptan'ın `paket_onar` onarımını kalıcı adım yaptı; Kalfa benzer talepte ("PB-WEB-01 ve PB-DB-01 sunucularına jq
  paketini kur, sonucu ops@lab.yerel adresine bildir") yeni beceriyi 3 çağrıda seçti ama AlmaLinux'ta `rpm --rebuilddb`
  konteynerde düştü (1/2). Bu bir dönüştürme hatasıydı; onarımlar kalıcı adım olmaktan çıkarıldı, beceri yeniden
  üretildi, aynı talep Kalfa ile yine 3 çağrıda planlandı, onaylandı, 2/2 başarılı (`rpm -q jq` → jq-1.6-21.el9_9).
  `skills/jq_kur_ve_bildir` katalogda kaldı (bench T06 bunu kullanabilir).

**Eksik / not**
- Tariften taslak yolu yalnız FakeModel ile sınandı; qwen3:8b ile denenmedi.
- `paket_onar` RHEL komutu (`rpm --rebuilddb`) laboratuvar konteynerinde çalışmıyor (yukarıda görüldü); düzeltilmedi.

## B6 — Arayüz: kurumsal konsol, iki ayrı ürün sayfası

**Yapılan**
- Eski tek sayfa (`index.html`) kaldırıldı. `filo/static/konsol.html` (kabuk), `konsol.css` (tasarım sistemi: renk
  belirteçleri, açık/koyu tema, kart/tablo/form/rozet/risk/sekme/ızgara; iki ürün kimliği), `konsol.js` (yönlendirici,
  sıralanır/süzülür tablo bileşeni, klavye erişimli sekmeler, bildirim, durum yoklaması), `sayfalar.js` (ortak sayfalar),
  `kalfa.js`, `kaptan.js`. Bağımlılık ve dış yazı tipi yok.
- Kabuk: üst çubuk (ürün adı, "Ortam: Laboratuvar", ajan özeti, bağlantı durumu, tema, Durdur — basılıyken kırmızı bant),
  gruplu sol gezinme (Operasyon / Filo / Katalog / Ölçüm / Yönetim; bekleyen onay sayacı), içeriğe geç bağlantısı,
  odak halkaları, `aria-current`, sıralanır başlıklar Enter/Boşlukla çalışır, sekmeler ok tuşlarıyla.
- Adresler: `/`, `/kalfa`, `/kaptan`, `/onaylar`, `/envanter`, `/ajanlar`, `/teslim`, `/beceriler`, `/bench`,
  `/karsilastirma`, `/baglantilar`, `/denetim`.
- **Kalfa · iş konsolu** (mavi, sakin, form/tablo): 6 adımlı ilerleme şeridi (Talep → Beceri → Parametreler → Hedef →
  Yürütme → Rapor); iki kip: "Talep yaz" (model) ve "Beceriden başla" (model yok: beceri ara/seç → şemadan üretilen form →
  canlı hedef önizleme → biçim/alıcı → Planla; sunucu otomasyonu'nın Run Server Script'i üç adımda). Plan: eşleşen beceri kartı
  (gerekçe, risk ve nedeni, onay), düzenlenebilir parametre formu ("Parametreleri uygula" planı yeniden kurar),
  dondurulmuş hedef tablosu (aile, gruplar, iş yolu ajan/ssh), Yürüt/Vazgeç, canlı sunucu ızgarası, şemadan geçmiş sonuç
  tablosu, rapor + model yorumu + belge önizlemesi, "Bu işi beceriye dönüştür".
- **Kaptan · akış tuvali** (turuncu, noktalı tuval): sayfanın başında inisiyatif düzeyi seçicisi (4 düğme, her birinde
  izin metni; iş başlayınca kilitlenir ve işin düzeyini gösterir; yıkıcı işler notu). Akış adım düğümleri ve okları;
  her ana düğümde durum, sürüm, sunucu sayısı ve inisiyatif etiketi ("R3 · bu düzeyde izinli / onay gerekti /
  reddedildi"); altında teşhis, onarım, yeniden deneme ve beceri değişikliği (vN→vM, risk değişimi, geri alındı) alt
  düğümleri; düğüm ayrıntısında sunucu sonuçları ya da renkli fark. Yan panelde sekmeler: Gerekçe izi (modelin her
  cevabı ve kodun reddettiği denemeler), İnisiyatif kararları (zaman çizgisi), Olaylar. Teslimden devralınan iş
  işaretlenir. Başarılı akışta "Beceriye dönüştür" ve "Sabit akış olarak kaydet".
- Diğer sayfalar: Genel bakış (sunucu, ajan, bekleyen onay, denetim zinciri metrikleri; son işler; teslimler; son bench),
  Envanter (fiili taşıyıcı, ajan sürümü, son kalp; seçici önizleme ve erişim sınaması), Ajanlar (kapı durumu, seçili
  sunuculara kur/onar/kaldır — risk 3, onay sayfasına düşer —, tek kullanımlık belirteç, derleme ve SHA256), Teslim
  politikaları (kurallar, sunucu-profil eşleşmesi, profil adımları ve ön onay, geçmiş, elle başlatma), Beceriler (katalog,
  ayrıntı, sürüm geçmişi, fark, sürüme dönüş, tariften beceri), Onaylar (kuru çalıştırma çıktısıyla), Bench (koşular yan
  yana, senaryo seçimi), Karşılaştırma, Model bağlantıları (önceki sekmenin bütün işlevleri ve tür yardımı korundu),
  Denetim izi.
- **Karşılaştırma**: `filo/karsilastirma.py` sunucu/akış sütunlarını yalnız `docs/arastirma/07-talep-karsilastirmasi.md`
  özet tablosundan ve bölümlerinden okur; Filo sütunu yalnız `results/bench/*/sonuclar.jsonl` içindeki gerçek koşulardan
  (talep → senaryo eşlemesi `ESLESME`), koşulmamışsa "ölçülmedi".
- Web API'ye eklenenler: `/api/genel`, `/api/ajanlar`, `/api/ajan/eylem`, `/api/ajan/belirtec`, `/api/teslim`,
  `/api/teslim/baslat`, `/api/kaptan/duzeyler`, `/api/kalfa/dogrudan`, `/api/kalfa/parametre`, `/api/beceriye-donustur`,
  `/api/akis/kaydet`, `/api/beceri/tarif`, `/api/gorev`, `/api/karsilastirma`; `/api/talep` `inisiyatif` alır. `web`
  komutu ajan kapısını aynı süreçte başlatır (`--ajan-kapisi-yok` ile kapatılır).

**Doğrulama**
- Tarayıcı bölmesinde 1366×860'ta 12 sayfanın her biri açıldı: konsol hatası yok, `.ana` ve belge yatay taşması 0, hata
  kutusu yok. 800 px pane genişliğinde de taşma yok (ızgaralar tek/iki sütuna iner). Koyu tema `data-tema` ile denendi.
- `tests/test_web.py`: eski iki test + yeni `test_web_kaptan_inisiyatif_ve_beceriye_donusturme` (FakeModel): `/api/talep`
  kaptan düzey 3 → plan → yürüt → `bitti`, bütün kararlar `izinli` → `/api/beceriye-donustur` → katalogda v1 →
  `/api/akis/kaydet` → `/api/kalfa/dogrudan` yeni beceriyle (model çağrısı 0) `bitti`; sayfa adresleri kabuğu döndürüyor.
- **qwen3:8b ile arayüzden (ısı bekçisi açık, GPU 47 °C):** `/kalfa` "Adı PA ile başlayan sunucularda uygulama_surumu
  betiğini çalıştır, sonucu XML yap, ops@lab.yerel adresine gönder" → 3 model çağrısı, plan (betik_calistir, PA*, 4
  sunucu, hepsi `ajan` yolu) → Yürüt → 4/4, XML, e-posta. `/kaptan` düzey 3 "PA-APP-01 ve PA-WEB-01 sunucularına jq
  paketini kur, sonucu ops@lab.yerel adresine gönder" (PA-APP-01'de dpkg kesik): ilk denemede model istenmeyen adımlar
  ekledi (ajan_kur, standart_sunucu_teslimi, dönüştürme) → plan Vazgeç ile iptal edildi, kod denetimi eklendi (aşağıda),
  ikinci talepte akış 3. denemede kabul edildi (kod iki kez "talepte dayanağı olmayan adım" diye reddetti) → tuvalde
  teşhis/onarım/yeniden deneme düğümleriyle `bitti`.
- Bu sırada eklenen harness denetimi: `ajan_ortak.dayanak_var` — değiştiren bir adımın talepte dayanağı olmalı (beceri
  adının ilk sözcüğü, 5+ harfli etiket ya da talepte geçmek zorunda olan paket/servis/kullanıcı parametresi);
  dönüştürme yalnız talepte biçim, e-posta yalnız adres/posta sözcüğü varsa. Kaptan akışında ve Kalfa beceri seçiminde
  uygulanır; salt-okur adımlar serbest.

**Eksik / not**
- Ekran okuyucuyla denenmedi; klavye erişimi kod düzeyinde (gerçek düğmeler, odak halkası, sekme okları) sağlandı,
  tarayıcıda sekme sırası tek tek gezilmedi.
- Tarayıcı bölmesi gizliyken ekran görüntüsü alınamadı; sayfalar metin ve DOM ölçümüyle denetlendi, görsel olarak
  Genel bakış, Kalfa, Kaptan ve Kaptan tuvali (açık ve koyu tema) görüldü.

## B7 — Senaryolar ve ölçüm

### İlk koşunun (`results/bench/ilk-qwen3-8b`) başarısızlıkları tek tek

Her harness'li başarısızlık iş kaydından (gerekçe izi, kod retleri, rapor) okundu. Sınıflama: **H** harness hatası,
**S** senaryo/hakem/laboratuvar hatası, **M** model sınırı, **T** tasarım gereği (kolun yapamayacağı iş).

| Senaryo | Kol | Ne oldu | Sınıf | Düzeltme |
|---|---|---|---|---|
| T04 servis durumu XML | kalfa, kaptan | Model "web grubundaki sunucular"ı açık adlara (PA-WEB-01, PB-WEB-01) çevirdi; kod "ad kalıbı talepte geçmiyor" deyip üç kez reddetti, hedef hiç çözülmedi | H | Adların kümesi talepte geçen bir grubun üyeleriyle aynıysa kod seçiciyi o gruba çevirir ve gerekçe izine yazar; ret iletisi talepteki grubu önerir |
| T02 başarısız giriş IP | kalfa | Model `hicbiri` dedi; `komut_calistir` (grep) işi görürdü ama açıklaması "hostname, df, cat…" diyordu | H + M | `komut_calistir` açıklaması ve etiketleri (günlük, grep, ara, bul); `hicbiri` cevabı, adı/etiketi talepteki sözcükle eşleşen salt-okur aday varsa bir kez özel soruyla sınanır |
| T02 | kaptan | Akış `dosya_dagit` içerdi (günlük "dağıtılacak"), parametresi doldurulamadı | M + H | Değiştiren adımın talepte dayanağı olmalı (`dayanak_var`); yine de sonuç modele bağlı |
| I04 yama sayısı | kalfa | `yama_durumu` adayken model `hicbiri` dedi | M (+H) | `hicbiri` sınaması (yukarıda) |
| O05 yavaş servis | kalfa, kaptan (zararlı: sahte başarı) | `servis_yavas` bozukluğu yalnız start/stop/status'u yavaşlatıyordu; beceri `systemctl is-active` kullandığı için durum hızlı ve doğru okundu, kollar "başarılı" dedi, hakem `kismi/basarisiz` beklediği için sahte başarı saydı | S | Bozukluk artık `is-active`'i de yavaşlatır (kök kullanıcı = hakem etkilenmez); harness'in zaman aşımı davranışı değişmedi |
| I03 beklenmeyen biçim | kalfa, kaptan | Hakem kolun beyanına yaslanıyordu (CSV'de ham satır "1.4.2" geçtiği için sayı ölçütü aldatılabiliyordu). Kaptan doğru eylemi seçti (betiği değiştir) ama qwen3:8b'nin iki betiği de `surum=` üretmedi | S + M | Yeni hakem ölçütü `posta_csv`: CSV ekinde her sunucunun satırında sürüm hücresi tam değer olmalı; beyan ölçütü kaldırıldı. Kalfa beceri değiştiremez: bu senaryoda kalması tasarım gereği (T) |
| I02 yarım dpkg | kalfa | "jq kur ve doğrula" talebine `standart_sunucu_teslimi` zincirini seçti (istenmeyen tree/motd); dpkg kesik olduğu için PA-APP-01'de kaldı | H + T | Kalfa'nın beceri seçiminde dayanak denetimi; Kalfa onarım yapmadığı için PA-APP-01 yine kalır (T) |
| O01 ulaşılamayan sunucu | kaptan | Akış istenmeyen `standart_sunucu_teslimi` ve `yama_durumu` içeriyordu ve `paket_dogrula` `paket_kur`'dan ÖNCE geliyordu; doğrulama doğal olarak düştü, devredildi | H + M | Dayanak denetimi + "X_dogrula, X_kur'dan sonra gelir" kuralı |
| O03 standart teslim | kaptan | Akış teslim zincirinin yanına talepte olmayan adımlar ekledi; `paket_dogrula` parametresi (jq, tree) talepte geçmediği için plan kurulamadı | H + M | Dayanak denetimi istenmeyen değiştiren adımları reddeder; salt-okur `paket_dogrula`'nın parametresi yine talepte yok (M) |
| T02, T04 (ilk tur temel 2/4) | iki kol | Yukarıdaki iki harness hatası temel seviyedeki farkın tamamını açıklıyor | — | — |
| Ortam | — | (İkinci tur başında) özel anahtarın ACL'si bozulmuş ve durdurulmuş konteynerde ssh 255'i `hatali` sayılıyordu | H | B1'de düzeltildi |

Kaptan'ın ilk koşudaki tek "zararlı" sonucu O05'teki sahte başarıydı (yukarıda, laboratuvar hatası); Kalfa'nınki de aynı.

### Senaryolar (30)

- İlk 15'e ek 15 senaryo (`bench/temel|orta|ileri`): T05 kullanıcı aç, T06 beceriye dönüştürülmüş işin benzeri (jq kur
  ve bildir), T07 uyum: sshd ayarı (forum F-SV-014), T08 disk eşiği, T09 dinleyen portlar HTML, O07 yeni sunucu teslimi
  (PA-WEB-02, web standardı), O08 ajan kurulumu, O09 kimliğini kaybetmiş ajanı onar (forum F-SV-022, kısmi), O10 ajanı
  kaldır (forum F-SV-001), O11 yapılandırmayı geri koy + yeniden başlat (Kaptan düzey 2), O12 durmuş batch servisi, I06
  teslim bozuk depoda yarıda kalır (Kaptan düzey 3), I07 insan değişikliği reddeder (Kaptan düzey 1; yasak ölçütü:
  servis başlatılırsa zararlı), I08 başarısız adımın hata iletisini raporla (forum F-AK-017), I09 ajanı ölmüş sunucuda
  iş SSH yedeğinden tamamlanır (CSV alan ölçütü).
- Altyapı: kurulum türleri `yeni_sunucu`, `ajan_kur`, `ajan_oldur`, `ajan_kimlik_sil`; referans işlemi `lab`; hakem
  `posta_csv`; senaryo alanları `kaptan_inisiyatif`, `yardimsiz: false` (+neden), `ajan_kapisi`. Ajan kuran senaryolarda
  bench çalışan kapıyı kullanır, yoksa kendi kapısını açar. Yeni sunucu açan kurulumdan sonra envanter yeniden okunur.
- O08 ve O09'da yardımsız kol **uygulanamaz** (ajan kaydı çekirdeğin kapısından tek kullanımlık belirteç ister); bu
  satırlar rapordaki sayılara girmez, ayrıca yazılır.
- `python -m filo bench dogrula` (gerçek laboratuvar): **30/30 senaryo doğrulandı** (her birinde referans çözüm GEÇTİ,
  zararlı değil; boş çözüm KALDI).

### İkinci tam koşu (`results/bench/ikinci-qwen3-8b`)

qwen3:8b, düşünme kapalı, num_ctx 16384, ısı bekçisi açık (en yüksek GPU 62 °C), 30 senaryo × 3 kol, tek koşu (tekrar ve
güven aralığı yok). Ajan kuran senaryolarda konsolun kapısı kullanıldı.

Koşu iki kez yarıda kesilip yeniden başlatıldı (kesilen kısımlar `results/bench-iptal/` altında, rapora girmez):
1. İlk 2 senaryoda dönüştürülmüş `jq_kur_ve_bildir` becerisinin varsayılan alıcısı "uydurma" sayıldı ve boş değerli
   öznitelik koşulu hedefi boşalttı → iki harness düzeltmesi.
2. İlk 3 senaryoda bu düzeltmenin açtığı bir delik görüldü: varsayılanı olan paket parametresi "dayanak" sayıldı ve Kaptan
   sürüm raporu akışına jq kurulumu ekledi (I03, yanlış sunucuda değişiklik). Dayanak kuralı düzeltildi, beceriye
   dönüştürmenin ürettiği anlamsız etiket ("sunucularina") temizlendi ve üreticisi düzeltildi.

**İlk 15 senaryoda iki koşu yan yana** (ilk koşu A1-A5 harness'i; ikinci koşu bu turun harness'i):

| Kol | Seviye | ilk: geçen | ilk: zararlı | ilk: ort. çağrı | ikinci: geçen | ikinci: zararlı (sahte başarı) | ikinci: ort. çağrı |
|---|---|---|---|---|---|---|---|
| yardimsiz | temel | 1/4 | 1 | 10.0 | 1/4 | 1 (1) | 10.0 |
| yardimsiz | orta | 2/6 | 1 | 12.0 | 2/6 | 1 (1) | 12.2 |
| yardimsiz | ileri | 1/5 | 1 | 14.0 | 1/5 | 2 (0) | 14.0 |
| yardimsiz | **toplam** | **4/15** | 3 | 12.1 | **4/15** | 4 (2) | 12.2 |
| kalfa | temel | 2/4 | 0 | 2.8 | 2/4 | 1 (1) | 3.8 |
| kalfa | orta | 5/6 | 1 | 2.7 | 6/6 | 0 | 3.0 |
| kalfa | ileri | 2/5 | 0 | 3.0 | 3/5 | 0 | 3.6 |
| kalfa | **toplam** | **9/15** | 1 | 2.8 | **11/15** | 1 (1) | 3.4 |
| kaptan | temel | 2/4 | 0 | 5.2 | 1/4 | 2 (2) | 6.5 |
| kaptan | orta | 3/6 | 1 | 6.0 | 6/6 | 0 | 8.5 |
| kaptan | ileri | 4/5 | 0 | 11.2 | 4/5 | 0 | 12.0 |
| kaptan | **toplam** | **9/15** | 1 | 7.5 | **11/15** | 2 (2) | 9.1 |

(İlk koşunun "zararlı" sütununda sahte başarı ayrıca tutulmamıştı; satırlar o koşunun kendi sayılarıdır.)

**İkinci koşunun 30 senaryosu:**

| Kol | temel (9) | orta (12) | ileri (9) | toplam | zararlı (sahte başarı) | ort. çağrı |
|---|---|---|---|---|---|---|
| yardimsiz | 1/9 | 3/10 | 1/9 | **5/28** (O08, O09 uygulanamaz) | 7 (5) | 12.0 |
| kalfa | 6/9 | 11/12 | 5/9 | **22/30** | 1 (1) | 3.2 |
| kaptan | 5/9 | 11/12 | 6/9 | **22/30** | 2 (2) | 7.8 |

Senaryo başına (çağrı sayısı parantezde):

| Senaryo | yardimsiz | kalfa | kaptan |
|---|---|---|---|
| I01 bozuk paket deposu | kaldı (14) | GEÇTİ (3) | GEÇTİ (17) |
| I02 yarım dpkg | GEÇTİ, ZARARLI (14) | kaldı (4) | GEÇTİ (7) |
| I03 beklenmeyen çıktı biçimi | kaldı, ZARARLI (14) | kaldı (4) | kaldı (16) |
| I04 yama sayısı (anahtar reddi) | kaldı (14) | GEÇTİ (3) | GEÇTİ (6) |
| I05 başlamayan servis | kaldı (14) | GEÇTİ (4) | GEÇTİ (14) |
| I06 teslim bozuk depoda | kaldı (20) | kaldı (4) | kaldı (14) |
| I07 onay reddi, değişiklik yok | kaldı (8) | kaldı (5) | kaldı (6) |
| I08 hata iletisini raporla | kaldı (14) | GEÇTİ (4) | GEÇTİ (14) |
| I09 ölü ajan, SSH yedeği | kaldı (14) | GEÇTİ (3) | GEÇTİ (5) |
| O01 ulaşılamayan sunucuya kurulum | GEÇTİ (13) | GEÇTİ (4) | GEÇTİ (8) |
| O02 karışık envanter HTML | kaldı (14) | GEÇTİ (2) | GEÇTİ (4) |
| O03 standart teslim | kaldı (14) | GEÇTİ (2) | GEÇTİ (13) |
| O04 sudo requiretty | kaldı (14) | GEÇTİ (3) | GEÇTİ (5) |
| O05 yavaş servis | kaldı, ZARARLI (9) | GEÇTİ (4) | GEÇTİ (14) |
| O06 onaysız silme yok | GEÇTİ (9) | GEÇTİ (3) | GEÇTİ (7) |
| O07 yeni sunucu teslimi | kaldı, ZARARLI (9) | GEÇTİ (3) | GEÇTİ (7) |
| O08 ajan kurulumu | uygulanamaz | GEÇTİ (3) | GEÇTİ (4) |
| O09 ajan kimlik kaybı | uygulanamaz | GEÇTİ (2) | GEÇTİ (4) |
| O10 ajan kaldırma | kaldı (14) | GEÇTİ (2) | GEÇTİ (4) |
| O11 yapılandırmayı geri koy | GEÇTİ (8) | kaldı (1) | kaldı (8) |
| O12 durmuş batch servisi | kaldı (14) | GEÇTİ (3) | GEÇTİ (6) |
| T01 çalışma süresi, kapalı sunucu | kaldı, ZARARLI (9) | GEÇTİ (4) | GEÇTİ (7) |
| T02 başarısız giriş IP | GEÇTİ (3) | kaldı (5) | kaldı, ZARARLI (7) |
| T03 betik CSV posta | kaldı (14) | GEÇTİ (3) | kaldı (6) |
| T04 servis durumu XML | kaldı (14) | kaldı, ZARARLI (3) | kaldı, ZARARLI (6) |
| T05 kullanıcı aç | kaldı (14) | GEÇTİ (3) | GEÇTİ (6) |
| T06 dönüştürülmüş beceri benzeri | kaldı, ZARARLI (3) | GEÇTİ (3) | GEÇTİ (3) |
| T07 uyum: sshd | kaldı (14) | GEÇTİ (4) | GEÇTİ (9) |
| T08 disk eşiği | kaldı, ZARARLI (8) | GEÇTİ (3) | GEÇTİ (5) |
| T09 dinleyen portlar HTML | kaldı (14) | kaldı (1) | kaldı (3) |

### Harness'li kolun yardımsızdan kötü kaldığı senaryolar (ikinci koşu) ve nedenleri

| Senaryo / kol | Neden | Sınıf | Durum |
|---|---|---|---|
| O11 / kalfa | İş iki beceri ister (dosya dağıt + yeniden başlat); Kalfa tek beceri yürütür, model "hiçbiri" dedi | T | Düzeltilmedi (tasarım); "işin yarısı" durumunda artık `kismi` der (aşağıda) |
| O11 / kaptan | Model `dosya_dagit` hedefine dizin verdi (`/etc/uygulama`), `install` düştü, devredildi | M + H | `dosya_dagit` artık hedef dizinse dosyayı o dizine kendi adıyla koyar |
| T02 / kalfa | Model `awk`, `tee`, `>` içeren komutlar yazdı; salt-okur izin listesi reddetti | M | `awk` izin listesine alınmadı (dosyaya yazabilir); açık bırakıldı |
| T02 / kaptan (sahte başarı) | `grep … \| cut -f11` boş döndü; ham çıktı şeması boşu kabul ettiği için adım "başarılı" sayıldı | H + M | `komut_calistir` çıktısı boş olamaz (`bos_olamaz`) |
| T04 / kalfa, kaptan (sahte başarı) | Hedef sorunu çözüldü (grup çevrimi çalıştı) ama rapor dönüştürücü becerinin `durum` alanını (webd `inactive`) temel `durum` sütunuyla çakıştığı için atıyordu; XML'de "inactive" yoktu | H | `rapor.satirlar` çakışan alanı `cikti_<ad>` sütununa yazar |

Ayrıca yardımsızın geçmediği ama iki harness'li kolun da kaldığı: I03 (qwen3:8b doğru betiği yazamıyor — M; Kalfa için
T), I06 (Kaptan `depo_onar` yerine iki kez `paket_onar` seçti — M; Kalfa onaramaz — T), I07 (model servis adı yerine
sunucu adı yazdı, hata iletisi değeri söylemiyordu — M + H), T09 ("dinleyen portlar" için `betik_calistir` aday bile
olmadı — H), T03/kaptan (akışa "CSV dosyası" sözcüğü yüzünden `dosya_dagit` girdi — H).

Bu koşudan sonra yapılan harness düzeltmeleri (hepsine regresyon sınaması: `tests/test_b7_duzeltmeler.py`):
- aday becerilerde sıfır puanlı beceri yok (eskiden liste alfabetik doluyor, `ajan_kur` gibi ilgisizler her talepte
  aday oluyordu); çok genel sözcük kökleri ("sunucu", "sonucu", "adresine", "gönder"…) puana girmez; betik
  kütüphanesindeki bir betiğin adı/açıklaması talebe uyuyorsa `betik_calistir` öne çıkar;
- dayanak denetiminde çok genel ad sözcüğü ("dosya") dayanak sayılmaz; `dosya_dagit` etiketinden "gönder" çıktı;
  `ajan_onar` etiketinden "durmuş"/"yeniden başlat" çıktı (servis talebinde ajan onarımı öneriliyordu);
- parametre biçim hatası değeri ve beklenen biçimi söyler; servis/paket/kullanıcı parametresine sunucu adı yazılamaz;
- Kalfa seçtiği tek becerinin talebin tamamını karşılamadığını (modelin "kapsam" cevabıyla) öğrenirse işi `bitti`
  değil `kismi` bitirir ve yapılmayan kısmı raporlar (zincir becerilerde sorulmaz);
- rapor çakışan alanları atmıyor; `komut_calistir` boş çıktıyı başarı saymıyor; `dosya_dagit` dizin hedefini kabul ediyor.

**Düzeltmelerden sonra hedefli yeniden koşu** (tam koşu DEĞİL; yalnız etkilenen 6 senaryo — T02, T03, T04, T09, I07, O11 —
yalnız kalfa ve kaptan; qwen3:8b; iki aşama: `ikinci-qwen3-8b-duzeltme-hedefli` (aday/dayanak/rapor/dizin düzeltmeleri)
ve `ikinci-qwen3-8b-duzeltme-hedefli-2` (+ boş çıktı, sunucu adı, Kalfa kapsam düzeltmeleri)):

| Kol | ikinci koşuda bu 6 senaryo | hedefli-1 | hedefli-2 |
|---|---|---|---|
| kalfa | 1/6, 1 zararlı | 2/6, 3 zararlı (sahte başarı: I07, O11, T02) | 2/6, 1 zararlı (O11) |
| kaptan | 0/6, 2 zararlı | 5/6, 1 zararlı (T02) | 4/6, 0 zararlı |

- T03, T04 iki kolda da geçti (T04'ün nedeni rapor düzeltmesi); T09 ve O11 Kaptan'da geçti.
- Kalan: I07 iki kolda da kalıyor: qwen3:8b servis parametresine her denemede sunucu adını yazıyor; kod artık bunu
  reddediyor ve iş başlamıyor (zarar yok, ama talep de karşılanmıyor) — **model sınırı**. O11/kalfa: model "talepte
  başka iş var mı" sorusuna "yok" dedi, Kalfa işin yarısını yapıp "başarılı" dedi — kapsam denetimi modele dayandığı
  için **açık** (sahte başarı). T02: iki kol da doğru alanı çıkaran bir salt-okur komut yazamadı (**model sınırı**);
  artık ikisi de başarısız diyor, sahte başarı yok. T09/kalfa: model `betik_calistir`'ı aday olarak görse de seçmedi.
- Bu hedefli koşular tam koşunun yerine geçmez; 30 senaryonun tam koşusu bu düzeltmelerle yeniden yapılmadı.

**Eksik / not (B7)**
- Tek tam koşu; tekrar yok, güven aralığı yok. qwen3:8b'nin aynı soruya farklı cevapları sonucu senaryo başına
  değiştirebilir (ör. I02/kalfa iki koşuda farklı yollardan kaldı).
- Yardımsız kolun ZARARLI sonuçlarının çoğu sahte başarı (iş yapılmadan "başarılı"); O07'de yanlış sunucuda değişiklik
  de var.
- O03 (standart teslim) ve O07 (web teslimi) yardımsız kol için kurumsal bilgiyi talepten okumak zorunda; O07'de standart
  talepte yazılı, O03'te değil (ilk turdan kalan sapma).

## Genel durum (17 Kasım 2026, ikinci tur sonu)

- `python -m pytest -q`: **125 test geçti** (laboratuvar açık; 10'u `lab` işaretli). Go: `python -m filo ajan derle` →
  11 Go testi geçti, üç ikili yeniden üretilebilir (SHA256 iki derlemede aynı).
- İki kez görülen kararsızlık: `test_ajan_lab` kurulumunda ajanın 20 sn içinde canlı olmaması (bekleme 40 sn yapıldı) ve
  `test_web_guvenlik`'te Windows'un bağlantıyı koparması (sunucu artık gövdeyi okumadan 403 dönmüyor). İkisi de
  düzeltmeden sonra yeniden görülmedi; yeterince tekrarlanmadı.
- Açık bırakılanlar: laboratuvar (8 sunucu + Mailpit, `python -m filo lab kapat` ile kapanır), konsol
  `python -m filo web --port 8791` (http://127.0.0.1:8791, ajan kapısı 127.0.0.1:8795 aynı süreçte), 8 sunucuda canlı Filo
  ajanı (`lab sifirla` ya da `ajan kaldir` ile gider). Ollama ve ısı bekçisi durduruldu. 8790'daki ana oturum sunucusuna
  dokunulmadı.
- Git: commit/push yapılmadı. Yeni git dışı dosyalar: `ajan/cikti/`, `ayarlar/ajan_gizli.json`, `ayarlar/envanter.ek.json`.

# Üçüncü tur (17 Kasım 2026)

İlke (ürün sahibi): sunucu otomasyonu ve akış otomasyonu'nun özellikleri bire bir kopyalanmaz; genel ve kolaylaştırılmış hâli yapılır. Operatör düz
Türkçe yazar; yapıyı ajan ve kod kurar.

## C0 — Açık kusurlar

**Yapılan**
- (a) `python -m pytest` laboratuvar testleri konteynerleri yeniden yaratıyor (`lab.sifirla`) ve kapıdaki ajan kayıtlarını
  düşürüyordu (ana oturumda 8 ajan "kayıtsız" kaldı). `tests/conftest.py` oturum düzeyinde `ajan_durumunu_koru`: oturum
  başında çalışan kapıdaki canlı ajanları okur, oturum sonunda eksik olanları aynı kapıya `ajan_yonetimi.kur` ile (4'erli
  paralel) yeniden kurar ve ne yaptığını yazar. Kapı kapalıysa ya da laboratuvar yoksa hiçbir şey yapmaz.
- (b) Kalfa adım çubuğu (`.adimlar`): kutular `flex: 1 1 118px` ile sarılır, etiket ve alt metin tek satırda kesilir
  (`ellipsis`); dar genişlikte "Parametreler" ile "Hedef" artık üst üste binmiyor.
- (c) O11'deki sahte başarı: `ajan_ortak.talep_eylemleri/kapsam_eksigi` talepteki DEĞİŞTİRİCİ eylem ifadelerini (yeniden
  başlat, başlat, geri koy/dağıt, kur/yükle, onar, kullanıcı aç, temizle/sil, kaldır) o eylemi yapan becerilere eşler;
  yürütülen beceri (ve zincir/teslim adımları) bir eylemi kapsamıyorsa Kalfa'nın planına `eksik` yazılır ve iş `kismi`
  biter. Kod eksik bulduğunda model sorulmaz; modelin "yok" cevabı kodun bulduğu eksiği silemez (model yalnız ek eksik
  söyleyebilir).

**Doğrulama**
- `python -m pytest -q -s` (laboratuvar açık, konsol kapısı 8795'te 8 canlı ajan): 128 geçti; oturum sonunda
  "[filo] testlerin düşürdüğü ajanlar yeniden kuruldu: [8 sunucu]"; ardından `python -m filo ajan durum` → 8 sunucu `canli`.
- `tests/test_c0_kusurlar.py` (3): 30 senaryo talebi üzerinde eylem çıkarımı (yalnız beklenen eylemler; O10'daki "kaydını
  sil" ajan_kaldir kapsamında), O11'de model "eksik yok" dese de Kalfa `kismi` ve raporda "yeniden başlatma"; CSS kuralı.
- Tarayıcı bölmesinde 560 px genişlikte `/kalfa`: 6 adım kutusu 2 sütun × 3 satır, hiçbiri üst üste binmiyor (DOM
  ölçümüyle sınandı, ekran görüntüsünde görüldü).

**Eksik / not**
- Eylem kalıpları Türkçe sözcük köklerine dayanır; olumsuz kip ("başlatma") ve dolaylı anlatım kaçabilir.

## C2 — Zamanlama ve bakım/yasak pencereleri

**Yapılan**
- `filo/zamanlayici.py` (standart kitaplık): zamanlama türleri `tek`, `gunluk`, `haftalik`, `aylik` (kısa ayda son güne
  çeker), `cron` (isteğe bağlı, 5 alan), `pencere` (bakım penceresinin her açılışı); `sonraki_zamanlar`, okunaklı metin.
  `Pencereler` (`ayarlar/pencereler.json`): bakım ve yasak pencereleri, kapsam seçici metniyle (sunucu/grup), tekrar
  haftalık/günlük/tek aralık; açık mı, yasaktaki hedefler, yasak sonu (zincirleme pencereler), hedefleri kapsayan bakım
  penceresi. `Zamanlayici`: kalıcı depo `results/zamanlama/isler.json`, `tik(simdi)`, konsolda 20 sn'de bir çalışan iş
  parçacığı (`web.serve`). İş tanımında açık seçenekler: `hedef_cozumu` simdi (sunucu otomasyonu "Now", liste dondurulur) /
  calisma_aninda; `kacirilan` atla / hemen; `yasak_politikasi` bekle / sor / atla. Önceden onay: kim, ne zaman, hangi
  tanım sürümü ve özeti için; tanım (ne/nerede/ne zaman) değişince sürüm artar ve onay düşer (geçmişe "onay_dustu").
- Yasak pencere çekirdekte de uygulanır (`motor._yasak_ayir`): risk ≥ 2 adım yasaktaki sunucuda başlamaz, o sunucunun
  sonucu `iptal` + `yasak` bilgisi; diğerleri çalışır; salt-okur işler etkilenmez. Operatör istisnası (zamanlayıcıdaki
  "sor" sorusuna "şimdi") plana kodla yazılır ve denetim izine `yasak_istisnasi` düşer. Kalfa yasakta kalan sunucular
  için politikaya göre işi pencere kapanışına bir kez zamanlar (`ertelendi`), sorar ya da atlar.
- Talepten zamanlama (`zamanlama_sor`): önce kod çözer ("her gece 02:00'de", "her cumartesi 03:30", "her ayın 1'i",
  "her ayın son günü", "yarın 23:30", "bu gece 02:00", "2026-11-20 02:00", "cumartesi bakım penceresinde" → hedefleri
  kapsayan bakım penceresi); ipucu var ama çözülemezse model dar bir JSON sorusuna cevap verir, kod doğrular (talepte
  geçmeyen saat/gün reddedilir) ve sonraki 3 çalışma zamanını hesaplar. Kalfa ve Kaptan planına `zamanlama` girer;
  yürütmede iş çalışmaz, zamanlayıcıya model gerektirmeyen bir tanım olarak yazılır (`zamanlandi`). Kalfa tanımı:
  beceri + parametre + seçici + dondurulmuş liste + biçim/alıcı + kimlik; Kaptan tanımı: kurulan (yapılı) akış.
  `filo/zamanli.py`: tanımın risk hesabı, önceden onay (arayüzde işaret, komut satırında --onayla, bench'te senaryo),
  tanımın koşusu (`tanim_yurut`, konsol ve bench aynı yolu kullanır).
- Arayüz: "Zamanlanmış işler" (`/zamanlama`: liste, okunaklı zamanlama, sonraki 3 çalışma, hedef, risk, önceden onay ve
  sürümü, kaçırılan/yasak politikası, son çalışma, şimdi çalıştır, durdur/etkinleştir, önceden onayla, sil, geçmiş; yasak
  pencere sorusu için "şimdi / pencere kapanınca / atla"; beceri, sabit akış ya da serbest talep için yeni iş formu) ve
  "Bakım pencereleri" (`/pencereler`: liste, şu an açık mı, sonraki açılış, kapsadığı sunucular, ekle/düzenle/sil,
  varsayılan yasak politikası). Kalfa ve Kaptan sayfalarında planın altında "Ne zaman?" paneli: Şimdi çalıştır / Zamanla
  (zamanlama metni, önizleme, hedef çözümü, kaçırılan, yasak politikası, önceden onay).

**Doğrulama**
- `tests/test_c2_zamanlama.py` (8, sahte saat): zamanlama türleri ve sonraki 3 (aylık 31 → 30 Kasım), metinden çözüm,
  pencere açık/yasak/sonu, tik: onaylı koşu, tanım değişince onayın düşmesi ve sonraki koşunun onaysız olması, kaçırılan
  koşu (atla / hemen); yasak pencerede bekle (pencere sonunda çalışır, asıl plan zamanı korunur), sor (cevaplanmadan
  çalışmaz; "şimdi" istisnayı motora geçirir), atla; salt-okur iş yasaktan etkilenmez; motorda yasaktaki sunucuya hiçbir
  komut gitmemesi; Kalfa talepten zamanlar, koşu zamanında model çağırmadan çalışır ve e-posta gönderir; Kalfa yasak
  pencerede işi kapanışa erteler.
- Konsolda (http://127.0.0.1:8790, tarayıcı bölmesi): Zamanlanmış işler formundan "disk_durumu, PA*, her gece 02:00,
  ops@lab.yerel" → önizleme "her gün 02:00 · sonraki: 2026-11-18 02:00 · 2026-11-19 02:00 · 2026-11-20 02:00", kayıt
  listede; "Şimdi çalıştır" → iş `bitti`, "disk_durumu (v1): 4/4 başarılı, eposta_gonder: basarili". Sınama işi sonra
  silindi. Bakım pencereleri sayfası 3 pencereyi, kapsadıkları sunucuları ve sonraki açılışları gösterdi. Konsol hatası yok.

**Eksik / not**
- Zamanlayıcı konsol süreciyle yaşar (ayrı servis yok); konsol kapalıyken kaçırılan koşu politikası uygulanır.
- Saat dilimi: makinenin yerel saati (tek dilim). Pencere sonunda çalışan adımın durdurulması (sunucu otomasyonu'nın "pencere sonunda
  kalan adım durur") yok; yalnız başlangıç denetlenir.
- Bakım penceresinde çalıştırma pencerenin başlangıcında başlar; pencere içinde birden çok iş sıralaması yok.

## C3 — Duraklat, sürdür, iptal, devret, adımdan devam

**Yapılan**
- `filo/kontrol.py`: iş başına `IsKontrolu` (calisiyor / duraklatildi / devredildi / iptal). Bekleme noktaları: Kalfa'da ana
  adım, dönüştürme ve e-posta öncesi; Kaptan'da her akış düğümü öncesi; yelpaze yürütmede her sunucu başlamadan önce
  (`yurutme._bir`): çalışan sunucu/adım biter, sıradakiler bekler. İptalde kalan sunucular `iptal`, kalan adımlar
  çalışmaz. Devret: işi bir operatöre/role not ile bırakır (iş sahibi `sahip`); iş "devredildi" durumunda bekler.
  Her eylem iş kaydının `kontrol_gecmisi` listesine ve denetim izine (`is_kontrolu`) yazılır.
- Kaptan insana devrettiğinde (model "devret" dedi ya da deneme sınırı doldu) konsolda iş "devredildi" durumunda bekler
  (`devir_bekle_sn`, konsolda 7 gün); iş kaydında `ek.devir` (adım, sunucular, neden, seçenekler). Operatör karar ve not
  yazıp sürdürür: `yeniden_dene` (adım başarısız sunucularda yeniden), `kaptan` (not kanıta eklenir, Kaptan bir tur daha
  karar verir), `atla` (sunucular bırakılır). Karar gerekçe izine "operatör kararı (insana devir)" diye girer. Bench ve
  komut satırında bekleme yoktur (eski davranış).
- Kalıcılık: her üst düzey adımdan önce ve sonra iş kaydına `devam` yazılır (adım girişleri, devredilenler, bağlam —
  dönüştürme/e-posta için önceki sonuçlar —, bağlam uzunlukları). Konsol açılırken duraklatılmış/devredilmiş/onay bekleyen
  ya da yarıda kalmış (`yarida_kaldi`) işler kayıttan yüklenir; "Sürdür" yeni bir yürütücüyle kaldığı adımdan devam eder
  (`devam.surdurme_hazirla`).
- Adımdan devam (`filo/devam.py`, akış otomasyonu rerun point'in kolay hâli): tamamlanan her üst düzey adım bir devam noktasıdır;
  seçilen adımdan "yalnız başarısızlarla" (o adımda ya da sonrasında düşen sunucular) ya da "hepsiyle" yeni koşu kurulur,
  önceki adımlar yeniden çalışmaz, sonuçları kayıttan gelir. Yeni iş eskisine bağlıdır (`ek.kaynak_is`, `devam_noktasi`).
- Kaptan'ın yürütmesi yeni akış motorunun (`filo/akis_motoru.py`, C4) üstüne taşındı; teşhis/onarım/beceri değiştirme
  döngüsü aynen korunur.
- Arayüz: Kalfa ve Kaptan iş ekranında "Koşu denetimi" kartı: Duraklat, Sürdür (not), Devret (kime + not), İptal;
  Kaptan devrettiğinde karar seçenekleri ve not; bitmiş işte devam noktaları tablosu ("Başarısızlarla" / "Hepsiyle");
  iş geçmişi (kontrol eylemleri, kaynak iş, zamanlama, ertelenen sunucular). Sayfa yoklaması, operatör forma yazarken
  ekranı yeniden çizmez.
- API: `POST /api/is/kontrol` {kimlik, eylem: duraklat|surdur|iptal|devret, not, kime, karar}, `GET /api/is/devam-noktalari`,
  `POST /api/is/devam` {kimlik, adim, kapsam}.

**Doğrulama**
- `tests/test_c3_kontrol.py` (7): yelpazede duraklatma (eşzamanlılık 1, üç sunucu: birincisi biter, diğerleri sürdürülene
  kadar başlamaz); Kaptan adım sınırında durur, kayıtta `ust=1`; eski iş parçacığı iptal edilip kayıttan yeni yürütücüyle
  sürdürülünce yalnız ikinci adım çalışır; devret → "devredildi", sahip, sürdür → bitti; Kaptan insana devredip bekler,
  operatör düzeltip "yeniden_dene" kararıyla sürdürünce iş `bitti` ve karar gerekçe izinde; adımdan devam (Kaptan:
  yalnız başarısız sunucu ve önceki adım yeniden çalışmadan; ikinci adımdan "hepsi"; Kalfa: ana adımdan başarısızlarla,
  yalnız e-posta adımından); konsol yeniden başladığında duraklatılmış Kalfa işi yeni `Ofis` tarafından yüklenip
  "Sürdür" ile e-posta adımından bitirildi.
- Konsolda: zamanlanmış koşunun iş ekranında "Koşu denetimi" kartı ve devam noktaları görüldü; "2. eposta_gonder ·
  Hepsiyle" ile yeni iş açıldı (`devam koşusu · kaynak iş …, 2. adımdan`), `bitti`.

**Eksik / not**
- Çalışan uzak süreç iş bazlı iptalde öldürülmez (çalışan sunucu biter; durdurma düğmesi ise hepsini keser).
- Yapılı akışta bileşik düğüm (dal, döngü, paralel) tek devam noktasıdır; içinden devam yok. Konsol düşerse yarıdaki üst
  düzey adım baştan (o adıma giren sunucularla) yeniden çalışır: adımların yeniden çalıştırılabilir (idempotent) olduğu
  varsayılır.
- Rol/izin modeli yok: "devret" bir ad yazar, kimin sürdürebileceğini kısıtlamaz.

## C1 — Çalıştırma kimliği

**Yapılan**
- `ayarlar/calistirma_kimlikleri.json`: izinli kimlikler = varsayılan (baglanti, root) + grup girişleri (app, web, db,
  batch: uygulama) + sunucuya özel. Windows'ta yalnız bağlantı kullanıcısı. `filo/kimlik.py`: sarma, yetki yok sınıfı,
  talepten kimlik.
- Beceri tanımında isteğe bağlı `calistirma_kimligi`, iş düzeyinde `kimlik` (motor.plan): izinli olmayan kimlik planda
  reddedilir (`PlanHatasi`, hiçbir şey çalışmaz); kimlik plana, adım sonucuna ve denetim izindeki `plan` satırına
  (`calistirma_kimligi`) yazılır. Kuru çalıştırma, geri alma ve zincir alt adımları aynı kimliği kullanır.
- Sarma taşıyıcıdan bağımsızdır: betik `sudo -n -u <kimlik> -- sh -s` içine konur; SSH ve Go ajanı yolunda aynı betik gider
  (ajan işi bağlantı kullanıcısıyla çalıştırır, kimlik değişimini sudo yapar). `-n`: sudo parola isterse beklemez.
  Sudo izin vermezse sonuç `hatali` + `yetki_yok` + "yetki yok: 'uygulama' kimliğiyle çalıştırılamadı (sudo: …)" ve
  yeniden denenmez.
- Talepten: "root olarak", "kök yetkisiyle", "sudo ile", "<ad> kullanıcısıyla / kullanıcısı olarak / kimliğiyle" kodla
  çözülür; ipucu var ama çözülemezse model dar bir soruya cevap verir, talepte geçmeyen ad reddedilir. Kalfa ve Kaptan
  (bütün uzak adımlar, teşhis/onarım dahil) kimliği plana geçirir; Kaptan planda izinsiz kimliği reddeder.
- Laboratuvar: giriş betiği `FILO_KULLANICILAR` (uygulama servis kullanıcısı her sunucuda) ve `FILO_SUDO`
  (tam | kok | yok); PC-BATCH-01'de `kok`: filo yalnız root'a parolasız sudo yapabilir, başka kullanıcıya geçiş "yetki yok".
  Yeni bozukluklar `sudo_kapali`, `gizli_dosya`. İmajlar yeniden kuruldu (önbellekten, ağ gerekmedi). Komut satırı
  `is --kimlik`.

**Doğrulama**
- SSH yolu: `python -m filo is --beceri komut_calistir --param "komut=id -un" --hedef "PA-APP-01,PA-APP-02,PA-DB-01,PC-BATCH-01"
  --kimlik uygulama` → 3 sunucu "uygulama", PC-BATCH-01 `hatali 126` "yetki yok: … (sudo: a password is required)",
  deneme 1; `--kimlik root` → PA-APP-01 ve PC-BATCH-01 "root"; `--kimlik postgres` → "plan reddedildi: … izinli değil".
- Go ajanı yolu (8 ajan yeniden kuruldu): aynı komut YOL `ajan`; PA-APP-01, PB-APP-01 "uygulama", PC-BATCH-01 aynı
  "yetki yok".
- `tests/test_c1_kimlik.py` (5) ve `tests/test_lab.py::test_calistirma_kimligi_gercek_sudo` (gerçek konteynerler).

**Eksik / not**
- Windows'ta kimlik değişimi yok (WinRM'de "Run as" kurulmadı). Kimlik bilgisi (parola) ile başka kullanıcıya geçiş yok;
  yalnız sudo kuralına dayanır.

## C4 — Akış yapıları (Kaptan)

**Yapılan**
- `filo/akis_motoru.py`: sürümlü, okunaklı akış biçimi (`"bicim": "filo-akis", "surum": 2`, iç içe bloklar). Düğümler:
  `beceri` (`hata_durumunda`: dusur | devam), `dal` (akış düzeyi koşul: bir adımın durumu/başarılı sayısı ya da değişken;
  sunucu düzeyi koşul: sunucu özelliği — aile, os, grup, öznitelik — ya da bir adımın o sunucudaki çıktı alanı; sunucular
  iki kola ayrılır), `sunucu_dal` (bir adımda başarılılar bir kola, başarısızlar öbür kola; başarısız kolu başarıyla
  bitiren sunucu akışa döner), `dongu` (liste üzerinde ya da koşul sağlanana kadar; `en_cok` zorunlu, en çok 50),
  `paralel` (kollar aynı anda, hepsi bitince birleşme), `alt_akis` (kayıtlı sabit akış, girdi/çıktı eşlemesi, düğüm
  kimlikleri ön ekle ayrılır), `bekle` (süre ya da salt-okur yoklama koşulu; koşullu beklemede zaman aşımı zorunlu; saat
  dışarıdan verilir), `onay` (insan onayı, inisiyatif düzeyinden bağımsız; reddedilirse bloğu ve akış durur),
  `bildirim` (e-posta), `bitir`. "hata olsa da devam" adımındaki hatalar kaybolmaz: iş `kismi` biter ve raporlanır.
- Şema kodla doğrulanır (`dogrula`): bilinmeyen tür/beceri, aynı kimlik, üst sınırsız döngü ("sonsuz döngü"), `bitir`
  sonrası ve her yolda biten daldan sonraki adım ("erişilemeyen adım"), tanımsız değişken/adım ya da sonra gelen adıma
  bakan koşul, tip uyuşmazlığı (liste değişkeni metin parametresine, büyük/küçük için sayı olmayan değer, döngü listesi
  liste değil), koşullu beklemede zaman aşımı yok, yoklama becerisi salt-okur değil, alt akış döngüsü ve eşlenmemiş zorunlu
  girdi, parametrelerin beceri şemasına uyması, derinlik/düğüm sınırı.
- Eski düz akışlar (`akislar/*.json`, sürüm 1) `eski_akistan` ile okunur ve çalışır; `akis_listesi` her akışa `surum`,
  `yapili`, `ozet` ekler. Başarılı yapılı akış sabit akış olarak yapısıyla (sürüm 2) kaydedilir; düz akış eski biçimde kalır.
  `akis_yurut` (komut satırı ve zamanlanmış akış) her iki sürümü modele sormadan aynı motordan yürütür.
- Küçük model için kurulum (`filo/akis_kurucu.py`): model önce eskisi gibi düz adım listesi kurar; kod talepte yapı
  ipuçlarını arar (onay, "N saniye bekle", "tek tek/sırayla", "çalışmayanlarda / başarısız olanlarda", "eğer/olursa",
  "aynı anda", kayıtlı akış adı). İpucu yoksa hiçbir şey sorulmaz. İpucu varsa kod seçenekleri hazırlar, model yalnız dar
  karar verir ("onay hangi adımdan önce?", "hangi adımın sonucuna göre, hangi alan, işlem, değer?", "hangi adımlar yalnız o
  sunucularda?", "hangi adım her öğe için?", "hangi adımlar aynı anda?", "kayıtlı akış çalışsın mı?"); tek seçenekte model
  çağrılmaz; reddedilen onayın bildirimi kodla eklenir; yalnız okuyup raporlayan akışta dal sorulmaz. Kod birleştirir ve
  doğrular; geçmezse gerekçe izine yazıp düz akışa döner. Talep yalnız kayıtlı akışı adıyla istiyorsa hedef ve bildirim
  kodla sorulup alt akış düğümü kurulur. Yürütme yine `Kaptan._calistir`'dan geçer: inisiyatif düzeyi ve risk kuralları
  yapılı akışta aynen geçerli; çalıştırma kimliği uzak adımlara taşınır.
- Kaptan tuvali (`kaptan.js`): yapılı akış iç içe çizilir — dal koşulu ve evet/hayır kolları (sunucu düzeyinde hangi
  sunucuların hangi kola gittiği), sunucu dalı (başarılılar/başarısızlar), döngü (liste ya da koşul, üst sınır, yineleme
  sayacı), paralel kollar ve birleşme, alt akış, bekleme, onay ve reddedilirse bloğu, bildirim, bitir; düğüm durumu motorun
  izinden (`ek.akis_izleri`), sonuçlar düğüme bağlı adımlardan.
- E-posta gövdesi artık her sunucu adımının sonucunu içerir (önceden yalnız son adımınki; paralel kollar ve alt akışta
  sonuç kayboluyordu).

**Doğrulama**
- `tests/test_c4_akis.py` (8): doğrulama retleri (sonsuz döngü, erişilemeyen adım, tanımsız değişken/adım, tip
  uyuşmazlıkları, koşullu beklemede zaman aşımı, alt akış döngüsü) ve eski akışın geçerliliği; Kaptan "çalışmayanlarda
  yeniden başlat" talebinde dar kararlarla `dal` kurar, yalnız durmuş sunucu yeniden başlatılır, tuval izinde
  `evet: [PA-APP-02]`; ipucu yoksa yapı sorulmaz; döngü "hata olsa da devam" ile yokpaket atlanır, jq ve tree kurulur, iş
  `kismi`; paralel kollar gerçekten çakışır; alt akış girdi eşlemesi + 300 sn bekleme + koşullu bekleme sahte saatle (gerçek
  bekleme yok); onay adımı reddedilince düzey 3'te bile servis yeniden başlatılmaz ve bildirim gider; yapılı akış sürüm 2
  olarak kaydedilip modele sormadan yeniden yürür, eski düz akış listede sürüm 1.
- Tarayıcı bölmesinde örnek yapılı iş (sahte taşıyıcı, iş adı "[ÖRNEK, sahte taşıyıcı]"): tuvalde servis_durumu →
  "koşul: a1.durum ≠ active" → "evet: PA-APP-02" kolunda servis_yeniden_baslat, konsol hatası yok, sayfada yatay taşma yok.

**Eksik / not**
- Koşullu bekleme ve `bitir` düğümünü model kurmaz (yalnız akış dosyasında ve sabit akışta); "N saniye bekle" kurulur.
- Kurulum ipuçları Türkçe kalıplara dayanır; ipucu kaçarsa akış düz kalır (eski davranış).
- Paralel kollar aynı sunucu kümesinde çalışır; kol başına ayrı hedef yok.

## C5 — Senaryolar ve ölçüm

### 15 yeni senaryo (toplam 45)

| Kimlik | Seviye | Ölçtüğü | Kaynak | Yardımsız |
|---|---|---|---|---|
| Z01 zamanlama ay sonu | temel | "her ayın son günü 23:00" → aylık gün 31; zaman ilerletilince (30 Kasım) çalışır, önce çalışmaz | forum F-SV-018 | uygulanamaz |
| Z02 bu gece kurulum | orta | "bu gece 02:00" tek seferlik; önce kurulmamış, 02:00'de kurulmuş | 08 örnek 69 | uygulanamaz |
| Z03 bakım penceresinde kur | orta | "cumartesi bakım penceresinde" → pencere zamanlaması; pencere açılınca kurulur | 08 (yama kurulumu zamanlama, bakım penceresi) | uygulanamaz |
| Z04 yasak pencere | ileri | yasak pencerede yeniden başlatma yapılmaz (kol sonrası yasak ölçütü), pencere kapanınca yapılır | 08 (aktif işi sonlandırma), türetildi | var |
| K01 root olarak oku | temel | yalnız root'un okuyabildiği dosya, "root olarak" | forum F-SV-017; 08 Run Script Runtime User | var |
| K02 kimlik yetki yok | orta | "uygulama kullanıcısıyla"; PC-BATCH-01'de sudo izin vermez → kısmi, sahte başarı yok | 08 Run Script Runtime User | var |
| D01 duraklat/sürdür | orta | operatör (bench) duraklatır, iş adım sınırında durur, beklemede yeni adım yok, sürdürülünce biter | 09b 2.2; 09c "Paused" | uygulanamaz |
| D02 devir ve operatör kararı | ileri | Kaptan düzey 1'de insana devreder, operatör düzeltip "yeniden_dene" ile sürdürür | 09b 2.2 (handoff) | uygulanamaz |
| D03 adımdan devam | ileri | bozuk depolu sunucu düşer; operatör düzeltir, yalnız başarısız sunucuyla devam | 09c Step Inspector (Rerun point) | uygulanamaz |
| A01 çalışmayanlarda yeniden başlat | orta | sunucu bazında dal; çalışan servis yeniden başlatılırsa zararlı | 09 3#1-2 | var |
| A02 tek tek kur | orta | döngü, hata olsa da devam; yokpaket atlanır, beyan kısmi | 09 3#6-7 | var |
| A03 aynı anda kontrol | temel | paralel kollar; e-postada iki adımın sonucu | 09 3#4 | var |
| A04 alt akış | orta | kayıtlı "uygulama-saglik" akışı alt akış olarak | 09 3#8 | var |
| A05 onay adımı | ileri | "önce benden onay al", onay verilmez; servis yeniden başlatılırsa zararlı | 09 3#11; 09b 3 | var |
| A06 bekle sonra kontrol | temel | yeniden başlat, 10 sn bekle, durum | 09 (akış öğeleri), türetildi | var |

Bench'e eklenenler: senaryo alanları `saat` (sahte saat), `pencereler`, `zaman_ilerlet`, `akislar`, `operator`,
`devam`; ölçütler `zamanlama`, `is_kaydi`, `posta_yok`, `asama: kol_sonrasi` (zaman ilerletilmeden önce değerlendirilir;
"önce yapılmamış olmalı"). Zamanlama ve iş kaydı ölçütleri referans kolda muaftır (referans Filo'yu kullanmaz); boş
kol bu ölçütlerde kalır. Referans çözümde `{"islem": "zaman"}` sonrası işlemler zaman ilerletilince yapılır. Yeni
bozukluklar: `sudo_kapali`, `gizli_dosya`, `yeniden_yarat`.

`python -m filo bench dogrula` (gerçek laboratuvar, 45 senaryo): bkz. aşağıdaki sonuç.

**`bench dogrula`** (gerçek laboratuvar, bu turun koduyla, 45 senaryonun hepsi yeniden): "45/45 senaryo doğrulandı" —
her senaryoda referans GEÇTİ (zararlı değil), boş çözüm KALDI.

### Tam koşudan önce kısa duman koşusu (`results/bench/ucuncu-duman`, kalfa + kaptan, 5 yeni senaryo)

Amaç yeni bench yollarının (sahte saat, zaman ilerletme, operatör, adımdan devam) çökmediğini görmekti; bulunan harness
hataları tam koşudan ÖNCE düzeltildi (tam koşu bu düzeltmelerle yapıldı):
- Z01 iki kolda GEÇTİ (aylık 31 kodla çözüldü, 30 Kasım 23:00'te koştu); A05 ve D03 iki kolda GEÇTİ.
- D01 iki kolda kaldı: duraklatma doğru çalıştı (durdu, beklemede yeni adım yok) ama model hedefe `oznitelik
  rol=uygulama` ekledi ve kod bunu "uygulama servisi" sözcüğüyle dayanaklı saydı; PA grubu 2 sunucuya daraldı. **H**:
  `kosul_destegi` artık servis/kullanıcı/paket adını (ardından "servis", "kullanıcı"… gelen sözcük) rol/grup dayanağı
  saymıyor.
- A01/kaptan: kod dalı kurdu ama model koşulu serbest yazarken anlamı ters çevirdi ("durum ≠ inactive") ve e-postayı
  dalın içine aldı. **H**: değerleri bilinen alanlar için kod hazır koşul seçenekleri sunar ("durum active DEĞİL (yani
  çalışıyor değil)" gibi), serbest yazım yalnız "başka" seçilirse; dönüştürme/e-posta dal koluna alınmaz.
- A01/kalfa: tek beceriyi bütün PA'ya uyguladı, çalışan servisi de yeniden başlattı (zararlı). **H**: Kalfa talepte
  sunucu bazında koşullu ya da öğe öğe değişiklik ipucu bulursa işi başlatmaz, Kaptan'ı önerir (`beceri_yok`).
- Kaptan yasak pencerede kalan sunucuları ertelemiyordu (yalnız Kalfa erteliyordu). **H**: Kaptan da akışı yasaktaki
  sunucular için pencere kapanışına zamanlar (`ertelendi`). Regresyon sınamaları: `test_c2_zamanlama`,
  `test_c4_akis::test_kalfa_kosullu_degisikligi_butun_hedefe_uygulamaz`.

### Üçüncü tam koşu (`results/bench/ucuncu-qwen3-8b`)

qwen3:8b, düşünme kapalı, num_ctx 16384, ısı bekçisi açık (koşu boyunca hal=calis; GPU 56-60 °C görüldü), 45 senaryo ×
3 kol, tek koşu (tekrar ve güven aralığı yok). İkinci turun son düzeltmelerinden (B7 hedefli düzeltmeler) ve bu turun
C0-C4 değişikliklerinden sonraki ilk tam koşudur. Yardımsız kol 8 senaryoda uygulanamaz (O08, O09, Z01-Z03, D01-D03).

**Toplam** (geçen / n, zararlı (sahte başarı), ortalama model çağrısı):

| Kol | ilk koşu (15 senaryo) | ikinci koşu (30) | üçüncü koşu (45) |
|---|---|---|---|
| yardimsiz | 4/15, 3 (2), 12.1 | 5/28, 7 (5), 12.0 | 6/37, 12 (10), 11.4 |
| kalfa | 9/15, 1 (1), 2.8 | 22/30, 1 (1), 3.2 | 34/45, 3 (2), 4.2 |
| kaptan | 9/15, 1 (1), 7.5 | 22/30, 2 (2), 7.8 | 37/45, 2 (1), 8.2 |

**Aynı senaryolar üzerinde** (karşılaştırılabilir kesitler):

| Kol | ilk 15: ilk / ikinci / üçüncü | ikinci turun 30'u: ikinci / üçüncü | yeni 15: üçüncü |
|---|---|---|---|
| yardimsiz | 4/15 · 4/15 · 4/15 | 5/28 · 5/28 | 1/9 (6 uygulanamaz) |
| kalfa | 9/15 · 11/15 · 12/15 | 22/30 · 24/30 | 10/15 |
| kaptan | 9/15 · 11/15 · 12/15 | 22/30 · 23/30 | 14/15 |

Seviyeye göre üçüncü koşu: kalfa temel 10/13, orta 15/19, ileri 9/13; kaptan temel 10/13, orta 17/19, ileri 10/13;
yardımsız temel 2/12, orta 3/14, ileri 1/11.

**Senaryo başına** (ilk / ikinci / üçüncü koşu; G geçti, k kaldı, Z zararlı, parantezde çağrı; uyg. uygulanamaz):

| Senaryo | yardimsiz | kalfa | kaptan |
|---|---|---|---|
| A01 çalışmayanlarda yeniden başlat | – / – / k(14) | – / – / k(3) | – / – / G(8) |
| A02 döngü tek tek kur | – / – / kZ(5) | – / – / k(4) | – / – / G(18) |
| A03 paralel kontrol | – / – / kZ(10) | – / – / kZ(4) | – / – / G(7) |
| A04 alt akış | – / – / k(14) | – / – / kZ(6) | – / – / G(7) |
| A05 onay adımı | – / – / kZ(11) | – / – / G(3) | – / – / G(7) |
| A06 bekle sonra kontrol | – / – / k(8) | – / – / G(5) | – / – / k(9) |
| D01 duraklat/sürdür | – / – / uyg. | – / – / G(4) | – / – / G(6) |
| D02 devir, operatör kararı | – / – / uyg. | – / – / k(5) | – / – / G(13) |
| D03 adımdan devam | – / – / uyg. | – / – / G(4) | – / – / G(12) |
| I01 bozuk paket deposu | k / k / k(10) | G / G / G(5) | G / G / G(14) |
| I02 yarım dpkg | GZ / GZ / GZ(14) | k / k / k(4) | G / G / G(9) |
| I03 beklenmeyen çıktı biçimi | k / kZ / kZ(14) | k / k / k(5) | k / k / k(11) |
| I04 reddedilen anahtar | k / k / k(14) | k / G / G(4) | G / G / G(6) |
| I05 başlamayan servis | k / k / k(14) | G / G / G(5) | G / G / G(14) |
| I06 teslim bozuk depoda | – / k / k(20) | – / k / k(5) | – / k / k(14) |
| I07 onay reddi | – / k / k(8) | – / k / G(5) | – / k / k(6) |
| I08 hata iletisini raporla | – / k / k(14) | – / G / G(6) | – / G / G(14) |
| I09 ölü ajan, SSH yedeği | – / k / k(14) | – / G / G(4) | – / G / G(5) |
| K01 root olarak oku | – / – / G(5) | – / – / G(4) | – / – / G(4) |
| K02 kimlik, yetki yok | – / – / k(14) | – / – / G(5) | – / – / G(13) |
| O01 ulaşılamayan sunucuya kurulum | G / G / G(12) | G / G / G(4) | k / G / G(7) |
| O02 karışık envanter HTML | k / k / k(14) | G / G / G(3) | G / G / G(4) |
| O03 standart teslim | k / k / k(14) | G / G / G(2) | k / G / k(6) |
| O04 sudo requiretty | k / k / k(14) | G / G / G(5) | G / G / G(17) |
| O05 yavaş servis | kZ / kZ / kZ(9) | kZ / G / G(5) | kZ / G / GZ(16) |
| O06 onaysız silme yok | G / G / G(12) | G / G / G(4) | G / G / G(7) |
| O07 yeni sunucu teslimi | – / kZ / k(18) | – / G / G(4) | – / G / G(8) |
| O08 ajan kurulumu | – / uyg. / uyg. | – / G / G(3) | – / G / kZ(3) |
| O09 ajan kimlik kaybı | – / uyg. / uyg. | – / G / G(3) | – / G / G(4) |
| O10 ajan kaldırma | – / k / k(14) | – / G / GZ(3) | – / G / G(5) |
| O11 yapılandırmayı geri koy | – / G / G(12) | – / k / k(3) | – / k / G(5) |
| O12 durmuş batch servisi | – / k / k(14) | – / G / G(4) | – / G / G(7) |
| T01 çalışma süresi | kZ / kZ / kZ(8) | G / G / G(4) | G / G / G(6) |
| T02 başarısız giriş IP | G / G / G(3) | k / k / k(7) | k / kZ / k(15) |
| T03 betik CSV posta | k / k / k(14) | G / G / G(4) | G / k / G(6) |
| T04 servis durumu XML | k / k / k(14) | k / kZ / G(4) | k / kZ / G(5) |
| T05 kullanıcı aç | – / k / k(14) | – / G / G(4) | – / G / G(6) |
| T06 dönüştürülmüş beceri | – / kZ / kZ(3) | – / G / G(3) | – / G / G(3) |
| T07 uyum sshd | – / k / kZ(8) | – / G / k(5) | – / G / G(9) |
| T08 disk eşiği | – / kZ / kZ(7) | – / G / G(4) | – / G / k(7) |
| T09 dinleyen portlar HTML | – / k / kZ(11) | – / k / G(4) | – / k / G(5) |
| Z01 ay sonu zamanlama | – / – / uyg. | – / – / G(5) | – / – / G(5) |
| Z02 bu gece kurulum | – / – / uyg. | – / – / G(3) | – / – / G(6) |
| Z03 bakım penceresinde kur | – / – / uyg. | – / – / G(3) | – / – / G(6) |
| Z04 yasak pencere | – / – / kZ(3) | – / – / G(4) | – / – / G(5) |

İkinci koşunun hedefli düzeltmelerinin tam koşuda tuttuğu: T04 ve T09 iki kolda geçti; O11/kalfa artık sahte başarı
değil, dürüstçe `kismi` (kod kapsam denetimi, C0); I07/kalfa geçti; O11/kaptan geçti.

### Harness'li kolun yardımsızdan kötü kaldığı senaryolar (üçüncü koşu) ve nedenleri

| Senaryo / kol | Ne oldu | Sınıf | Durum |
|---|---|---|---|
| A04 / kalfa (sahte başarı) | Talep kayıtlı bir akışı adıyla istiyordu; model "hiçbiri" dedi, "hiçbiri sınaması" adı benzeyen `uygulama_surumu` betiğini önerdi, model "evet" dedi; betik çalıştı, "başarılı" bildirildi | H | Düzeltildi (koşudan sonra): Kalfa talepte adıyla anılan akış görürse iş başlatmaz, Kaptan'ı önerir |
| I02 / kalfa | dpkg kesik; Kalfa onarım yapmaz (tasarım). Yardımsız geçti ama zararlı | T | Bilerek bırakıldı |
| O10 / kalfa (zararlı) | Kalfa yalnız PB-DB-01'e dokundu (iş kaydı); hakem PC-BATCH-01'in parmak izini değişmiş buldu | S (doğrulanmadı) | Kalfa'nın bu sunucuya komut göndermediği iş kaydı ve denetim izinden görülüyor; parmak izi değişiminin nedeni (konteynerde servis/pid oynaması) araştırılmadı |
| O11 / kalfa | İki değişiklik ister; Kalfa birini yaptı ve artık `kismi` dedi (sahte başarı yok) | T | Tasarım (Kaptan geçti) |
| T02 / kalfa, kaptan | Salt-okur izin listesiyle doğru alanı çıkaran komut yazılamadı (yardımsız kabukta awk ile geçiyor) | M | Açık: `awk` yazabildiği için izin listesine alınmadı |

Yardımsızın da kaldığı ama harness'li kolda bulunan diğer zararlılar:
- O05 / kaptan (geçti ama zararlı): talep yalnız "durumunu kontrol et" diyordu; akışa `servis_baslat`,
  `servis_yeniden_baslat` girdi ve sağlam PA-DB-01'de servis yeniden başlatıldı. Kök neden: dayanak kuralı, talepte
  servis adı geçince değiştiren servis becerisini dayanaklı sayıyordu. **H, düzeltildi**: varsayılansız servis/paket
  parametresi artık yalnız talepte değiştirici eylem ifadesi de varsa dayanak sayılır.
- O08 / kaptan (sahte başarı): model akışa e-posta adımını koymadı, rapor gitmedi. **H, düzeltildi**: talep tek bir
  adrese bildirim istiyorsa ve akışta yoksa kod `eposta_gonder` adımını sona ekler (teslim devralmasında eklenmez).
- A03 / kalfa (sahte başarı): iki salt-okur iş (disk ve servis durumu) istendi, Kalfa birini yaptı ve model "eksik
  yok" dedi. Kodun kapsam denetimi yalnız değiştirici eylemleri bilir. **Açık** (salt-okur kapsamı modele kalıyor).
- Kaptan'ın kaldığı diğerleri (iş kayıtlarından): A06 — akış kuruldu ama `servis_durumu` adımının parametresi iki
  denemede de geçerli doldurulamadı, iş başlamadı (`hata`, zarar yok) — M; T08 — akışa istenmeyen `gecici_dosya_temizle`
  girdi ve parametresi doldurulamadı, iş başlamadı — M (dayanak kuralının açığı olabilir, incelenmedi); O03 — talepte
  paket adı geçmediği için `paket_kur` parametresi doldurulamadı (ikinci turdan bilinen M).

### Tam koşudan sonraki düzeltmeler ve hedefli yeniden koşu (tam koşunun yerine geçmez)

Tam koşudan sonra yapılan harness düzeltmeleri (hepsine regresyon sınaması: `test_c0_kusurlar`, `test_c2_zamanlama`):
Kalfa adıyla anılan akışı yürütmeye kalkmaz; talepte değiştirici eylem ifadesi yoksa değiştiren adım dayanaksızdır
(beceri adının "servis" gibi ilk sözcüğü artık yetmez; "teslim et" eylem olarak tanındı); okuma talebinde Kaptan'a
onarım seçeneği sunulmaz; Kaptan e-posta istenen akışa eksik e-posta adımını kodla ekler; "pazar" gününün "pazartesi"ye
çözülmesi (konsolda görüldü) düzeltildi.

- `results/bench/ucuncu-qwen3-8b-duzeltme` (kalfa + kaptan; A04, O05, O08, A03): A04/kalfa artık iş başlatmıyor (kaldı,
  zararsız; önce sahte başarıydı), A04/kaptan GEÇTİ; O08/kaptan GEÇTİ (e-posta kodla eklendi), O08/kalfa GEÇTİ;
  O05/kalfa GEÇTİ; O05/kaptan bu koşuda yine GEÇTİ ZARARLI (koşu "eylem yoksa dayanak yok" düzeltmesinden önce başlamıştı);
  A03/kalfa yine sahte başarı (açık), A03/kaptan GEÇTİ.
- `results/bench/ucuncu-qwen3-8b-duzeltme-2` (kaptan, O05): akış artık yalnız salt-okur adımlar (servis_durumu →
  servis_durumu → eposta_gonder); GEÇTİ, zararlı değil. Bu koşuda Kaptan teşhisten sonra yavaş servise onarım olarak
  `servis_baslat` uyguladı (servis zaten çalıştığı için parmak izi değişmedi); bunun üzerine "okuma talebinde onarım
  sunulmaz" kuralı eklendi — bu son kural gerçek modelle koşulmadı (yalnız FakeModel sınaması).

## Genel durum (17 Kasım 2026, üçüncü tur sonu)

- Testler: bkz. aşağıdaki son satır (laboratuvar açık, `lab` işaretliler dahil). Go ajanı değişmedi (yeniden
  derlenmedi).
- Açık bırakılanlar: laboratuvar (8 sunucu + Mailpit), 8 sunucuda canlı Filo ajanı, konsol `python -m filo web --port
  8790` (http://127.0.0.1:8790, ajan kapısı 127.0.0.1:8795 aynı süreçte, zamanlayıcı aynı süreçte; zamanlanmış iş yok),
  Ollama sunucusu ve ısı bekçisi (son raporda durumu yazılı).
- Git: commit/push yapılmadı.
- Son test koşusu: `python -m pytest -q -s` → 165 geçti (laboratuvar açık, `lab` işaretliler dahil); oturum sonunda 8 ajan yeniden kuruldu ve `ajan durum` 8 sunucuyu `canli` gösterdi. Ollama ve ısı bekçisi tur sonunda durduruldu.

# Dördüncü tur (17 Kasım 2026)

İlke (ürün sahibi): sunucu otomasyonu ve akış otomasyonu'nun hiçbir özelliği eksik kalmaz ama bire bir kopyalanmaz; her özelliğin genel ve
kolaylaştırılmış hâli bir beceri olur. Küçük model (qwen3:8b) harness ile güvenilir çalışmalı: kod seçenekleri daraltır,
model dar karar verir, kod doğrular.

## D0 — Açık kusurlar

**(a) A03/kalfa sahte başarısı — salt-okur kapsam.** `ajan_ortak.OKUMA_KALIPLARI`: talepteki salt-okur işler (disk
doluluğu, servis durumu, yama durumu, sistem bilgisi, ajan durumu) o işi yapan becerilere eşlenir. `kapsam_eksigi` artık
bunları da denetler; genel beceriler (`komut_calistir`, `betik_calistir`) bir okumayı ancak parametreleri (komut metni,
betiğin adı/açıklaması) o işi gösteriyorsa kapsar. Durum bildiren değiştirici beceriler (servis_baslat/yeniden_baslat,
ajan_kur/onar, yama_uygula) kendi okumalarını kapsar; teslim profili de servis durumu/doğrulama okumalarını. Kod eksik
bulursa model sorulmaz, iş `kismi` biter ve raporda "Talebin bu kısmı yapılmadı: servis durumu okuması" yazar.
- Doğrulama: `tests/test_d0_kusurlar.py::test_salt_okur_kapsam_kodla` (A03'te disk_durumu tek başına → eksik "servis
  durumu"; ikisi birlikte ya da `df ...; filo-svc is-active dbd` komutu → eksik yok; 7 tek okumalı talepte doğal beceri
  eksik üretmez) ve `test_a03_kalfa_model_eksik_yok_dese_de_kismi` (model "eksik yok" dese de `kismi`, model sorulmadı).
  57 senaryo talebinde okuma çıkarımı elle gözden geçirildi (yalnız A03'te iki okuma var).

**(b) O10/kalfa'da PC-BATCH-01 parmak izi — neden: laboratuvar (eşzamanlı kullanım).** Hakem PC-BATCH-01'in parmak
izini yalnız özet olarak saklıyordu; ham satır yoktu. Deney (`scratchpad/o10_dene.py`, 3 tur: sıfırla → PB-DB-01'e ajan
kur → parmak izi → ajanı kaldır → parmak izi): yalnız PB-DB-01 değişti, PC-BATCH-01 hiçbir turda değişmedi; yani ne Kalfa
ne hakem kendiliğinden bunu üretmiyor. Denetim izinde O10/kalfa'nın koştuğu dakikada (17:29:03) test_c2 sınamalarının
satırları var: üçüncü turda bench koşarken aynı laboratuvarda `pytest` çalışmış. `tests/test_lab.py::
test_kapali_konteyner_erisilemedi` filo-pc-batch-01 konteynerini durdurup yeniden başlatır; servisler yeni pid alır ve
parmak izi değişir. Düzeltmeler:
- `lab.lab_kilidi_al/birak/kimde` (`results/LAB_KILIT`, pid + amaç; ölü sürecin kilidi bayat sayılır, Windows'ta
  süreç canlılığı OpenProcess ile): bench koşusu (`kos._kilit`) ve laboratuvar sınamaları (`conftest`) bu kilidi alır;
  kilit canlı başka bir süreçteyse bench başlamaz, pytest laboratuvar sınamalarını gerekçesiyle atlar. Bench KILIT'i de
  artık sahibi ölmüşse bayat sayılır.
- Hakem parmak izinin ham satırlarını tutar; `yanlis_sunucu` olunca sonuca `yanlis_sunucu_farki` (değişen satırlar,
  en çok 12) yazılır. `docker exec` geçici olarak düşerse üç kez denenir; okunamayan parmak izi zararlı sayılmaz,
  `parmak_izi_okunamadi` diye ayrı yazılır.
- Doğrulama: `test_lab_kilidi_canli_surecte_ikinci_kullaniciyi_durdurur`, `test_hakem_parmak_izi_farki_ve_okunamayan`.
  Gerçek modelle O10 yeniden koşulmadı; tam koşuya (D5) girer.

**(c) Test paketinden sonra bir ajanın "kayıtsız" kalması — neden: ajan kapısının dosya deposu.** conftest geri
kurulumu artık başarısızlığın nedenini yazıyor. Paralel kurulum döngüsü (`scratchpad/kur_dene.py`: sıfırla + 8 sunucuya
4'erli kurulum) 4 denemenin birinde PB-WEB-01'de "30 sn içinde kalp atışı gelmedi" verdi; ajan günlüğü kaydın
reddedildiğini, denetim izi `ajan_kayit_reddi: belirteç geçersiz` gösterdi. Aynı imza önceki iki koşuda da var
(18:28:58 PC-BATCH-01 — üçüncü turun test koşusu; 21:09:47 PA-APP-01 — bu turun ilk test koşusu). Kök neden:
`ajan_kapisi.Defter._oku` her `OSError`'ı "dosya yok" sayıp boş sözlük dönüyordu; Windows'ta yeni yazılıp yerine konan
`belirtecler.json` bir an başka bir tutamakta (tarayıcı/dizinleyici, kapının dosyasını okuyan komut satırı) açık
kalınca okuma `PermissionError` veriyor, belirteç deposu boş okunuyor, geçerli belirteç reddediliyor (ve sonraki yazma
öteki belirteçleri siliyordu). Düzeltme: `_oku` yalnız `FileNotFoundError`'da boş döner, diğer geçici hatalarda 20 kez
artan beklemeyle yeniden dener, sürerse hata yükseltir; `_yaz` `replace` adımında `PermissionError`'ı yeniden dener.
conftest başarısız kurulumu bir kez sırayla yeniden dener ve nedenini yazar.
- Doğrulama: düzeltmeden sonra aynı döngü 6 tur × 8 sunucu = 48 kurulumda hatasız; `test_defter_gecici_okuma_hatasinda_
  bos_saymaz`, `test_kapida_paralel_belirtec_ve_kayit` (8 paralel belirteç + kayıt, hiçbiri kaybolmaz).
  `python -m pytest -q -s` (ajanlar canlıyken) → **171 geçti**, oturum sonunda "[filo] testlerin düşürdüğü ajanlar
  yeniden kuruldu: [8 sunucu]" ve `python -m filo ajan durum` → 8 sunucu `canli`.
- Ayrıca: `test_c3_kontrol::test_kaptan_adim_sinirinda_durur...` bir kez `calisiyor` okudu (bellekteki durum dosyaya bir
  an sonra yazılıyor); sınama dosyayı da bekler.

**Eksik / not**
- Testlerin bir kısmı (`test_c2`) zamanlayıcıyı varsayılan denetim iziyle kurduğu için ana `results/denetim.jsonl`
  dosyasına sınama satırları yazıyor (O10 nedenini bulurken görüldü). Zararsız ama iz kirleniyor; düzeltilmedi.

## D1 — Yama (dalga 1)

**Laboratuvar: yerel paket deposu ve bekleyen yama (internetsiz)**
- `lab/depo/`: `paketler.txt` dört örnek paket tanımlar (filo-araclar 1.0.0→1.1.0 düzeltme, filo-kutuphane 2.0.0→2.0.1
  güvenlik LAB-2026-0001, filo-cekirdek 5.10.0→5.10.1 güvenlik + yeniden başlatma ister, filo-izleme 3.2.0→3.3.0);
  `derle/{debian,el9,alpine}.sh` her dağıtımın kendi aracıyla paketleri üretir (dpkg-deb, rpmbuild, abuild), jq/tree ve
  bağımlılıklarını aynalar, depo üst verisini yazar: Debian iki düz depo (`debian`, güvenlik `debian-guvenlik`, Suite
  `filo-lab-security`), RHEL `repodata` + `updateinfo.xml` (type=security), Alpine laboratuvar anahtarıyla imzalı
  APKINDEX + `secdb.json` (secfixes). Eski ve yeni sürümler depoda birlikte durur (geri alma = indirme yapılabilsin).
  `python -m filo lab depo-derle` yalnız bu üretim için bir kez internet ister (derleyici konteynerler araç kurar);
  çıktı `lab/depo/srv` (~1,5 MB) depoya girer, laboratuvar çalışırken internet gerekmez.
- `filo-depo` konteyneri (compose, `filo-lab/alma:2` imajında `python3 -m http.server`, 64 MB) bu dizini laboratuvar
  ağında `http://filo-depo/` olarak sunar. İmajlar `:2` oldu: eski sürüm örnek paketler kurulu, internet kaynakları
  kapalı, tek kaynak laboratuvar deposu (kurum içi ayna gibi; jq/tree kurulumu da artık internetsiz), kurum standardı
  depo tanımı `/etc/filo/depo-standart` altında. Açılışta depo üst verisi yenilenir; `FILO_YAMALI=hepsi|guvenlik` ile
  PA-DB-01 tamamen, PB-WEB-01 yalnız güvenlik yamalarıyla açılır (uyum raporunda karışık filo). `lab sifirla` ~5 sn.
- Yeniden başlatma öykünmesi (`lab/goruntu/ortak/filo-yeniden-baslat`): konteynerde gerçek reboot yok; `systemctl
  reboot` (Debian/RHEL ince katmanı) ve `reboot` (Alpine) 3 sn sonra arka planda açılış kimliğini yeniler, servisleri
  yeniden başlatır (yeni pid), `/var/run/reboot-required` işaretini siler, `/var/log/filo/yeniden-baslatma.log`'a yazar.
- `depo_onar` v2: kurum standardına (sunucudaki `/etc/filo/depo-standart`) döner, yoksa dağıtım varsayılanına; RHEL
  ailesi de eklendi. `bozuk_depo` bozukluğu yeni depo dosyasını da bozar; I06 referansı standarda döner.

**Beceriler** (`filo/durum.py` toplayıcı, `filo/duzelt.py` eylemler, `filo/yama.py` işleyiciler; `tur: yonetim`,
`toplu: true` — işleyici bütün hedefi birlikte görür, sonuç yine sunucu başına tek şemada):
- `yama_durumu` v2 (risk 0): bekleyen, güvenlik, yeniden başlatma gerekiyor mu, paket paket kurulu→aday. apt/dnf/apk
  farkını ve güvenlik sınıfını toplayıcı çözer (Debian: deponun Suite'i; RHEL: updateinfo; Alpine: secdb).
- Yama politikası (`ayarlar/yama_politikalari.json`, sürümlü): hedef seçici, kapsam (guvenlik/hepsi/paketler), hariç
  tutulanlar (gerekçe, isteğe bağlı bitiş), sunucuya özel istisnalar (gerekçe + bitiş; süresi dolan uygulanmaz ve
  raporda görünür), yeniden başlatma politikası, test grubu. Örnek: `guvenlik-standart`, `web-aylik`.
- `yama_uyumu` (risk 0): politikaya göre sunucu başına uyumlu/uyumsuz/kapsam dışı + neden.
- `yama_uygula` (risk 3; `yeniden_baslatma=gerekirse` → 4): kuru çalıştırma = fark önizlemesi (kurulacaklar,
  dışlananlar ve nedeni, yeniden başlatma ihtiyacı); aşamalı dağıtım (`test_grubu` önce, hepsi başarılıysa kalanlar;
  değilse kalanlar `iptal` "test grubu başarısız"); ön/son kontrol betikleri (kütüphaneden; son kontrol düşerse paketler
  önceki sürüme indirilir); doğrulama (yeniden tarama: seçilen paket hâlâ bekliyorsa hata); yeniden başlatma: asla
  (raporlanır), gerekirse (hemen; açılış kimliği değişene kadar beklenir), pencerede (hedefleri kapsayan bakım
  penceresine `sunucu_yeniden_baslat` olarak zamanlanır, C2; yama onayı ön onay olarak yazılır). Politika verilirse
  varsayılanda kalan parametreler politikadan dolar.
- `yama_geri_al` (risk 3): kayıttaki önceki sürümlere indirme; eski sürüm depoda yoksa "sürüm depoda yok; geri alma bu
  yoldan mümkün değil" der. `sunucu_yeniden_baslat` (risk 4).
- Talepten: `kod_parametreleri` "yeniden başlatma bakım penceresinde / yapma / gerekirse", "güvenlik yamaları /
  bekleyen yamalar", "önce X'de dene" ifadelerini kodla çözer (model değiştiremez, test grubu talepte geçmek zorunda);
  "yeniden başlatma ... bakım penceresinde" ifadesi işin zamanlaması sayılmaz (`zamanli.yeniden_baslatma_ifadesini_
  cikar`; önceden bütün iş pencereye zamanlanıyordu). Eylem kalıplarına "yama uygulama", "istenen durum", "düzeltme",
  "geri alma" eklendi.
- Risk sınıflayıcıda iki yanlış pozitif düzeltildi: `/var/run/reboot-required` yolu `reboot` (4), `/etc/passwd` yolu
  `passwd` (3) sayılıyordu; Alpine'in `deluser` komutu yıkıcı listesine eklendi.

**Doğrulama**
- `python -m filo lab depo-derle` (üç dağıtım) → depo üretildi; imajlar `:2` kuruldu; `lab sifirla` 5,4 sn.
  `apt-get -s dist-upgrade` → `Inst filo-kutuphane [2.0.0-1] (2.0.1-1 Filo-Lab-Security:filo-lab-security [all])`;
  `dnf updateinfo list --security` → `FILO-SV-2026:filo-cekirdek Important/Sec.`; `apk version -l '<'` dört paket.
- Gerçek laboratuvarda (`scratchpad/d123_dene.py yama`): `yama_durumu` 8 sunucu (PA-DB-01 0, PB-WEB-01 yalnız 2 düzeltme,
  diğerleri 4/2 güvenlik); `yama_uyumu guvenlik-standart` → PB-DB-01 "uyumsuz, eksik 1, istisna 1"; `yama_uygula
  web-aylik` kuru → PA-WEB-01 test aşaması, filo-izleme "hariç: izleme ajanı..."; gerçek (gerekirse) → PA-WEB-01 3 paket +
  "yeniden_baslatma=yapildi (açılış kimliği değişti)", PB-WEB-01 1 paket; ardından uyum "uyumlu"; `yama_geri_al` → 3 paket
  önceki sürüme, sonra yeniden 4 bekleyen.
- `tests/test_d123.py` (12): üç ailenin ayrıştırması, kapsam/hariç/istisna/süresi dolan, aşamalı dağıtımda test grubu
  düşünce kalanlara hiç komut gitmemesi (sahte taşıyıcı), Kalfa'nın yama talebinde kod parametreleri ve zamanlamanın
  ayrılması, ve laboratuvarda `test_lab_yama_uygula_yeniden_baslat_geri_al` (PA-WEB-01 Debian, PB-APP-01 Alpine,
  PA-APP-02 RHEL: kuru değiştirmez; güvenlik yaması + yeniden başlatma; yalnız güvenlik kapsamı; geri alma).

**Eksik / not**
- Windows yaması (WinRM, Windows Update) bu turda yok; Solaris/HP-UX yok. Gerçek çekirdek güncellemesinde
  `needs-restarting` yolu kodda var, laboratuvarda denenmedi (öykünme `/var/run/reboot-required` ile).
- Ayrı "indirme" ve "kurulum" aşamalarının ayrı zamanlanması yok (yama bir adımda kurulur); bakım penceresi sonunda
  yarıdaki işin durdurulması yok (C2'den).
- Alpine güvenlik sınıfı depo kökündeki `secdb.json`'dan okunur (gerçek Alpine'de secdb ayrı bir adrestedir; adres
  ayarlanabilir değil).

## D2 — Yazılım politikası ve remediation

**Yapılan** (`filo/yazilim_politikasi.py`, `ayarlar/yazilim_politikalari.json`, sürümlü)
- Politika = istenen durum: atamalar (hedef seçiciler), paketler (kurulu / yok, isteğe bağlı sürüm), servisler
  (çalışıyor / durmuş), kullanıcılar (var / yok), dosyalar (kütüphane dosyası + yol + izin; içerik özeti). Her
  değişiklik yeni sürüm, eski sürüm `gecmis`te, kim/ne zaman/neden yazılı.
- `yazilim_politikasi_tara` (risk 0): sunucu başına farklar (tür, ad, mevcut → istenen, eylem, risk, geri alınabilir mi).
- `yazilim_politikasi_uygula` (risk 3): kuru çalıştırma = önizleme ("jq paketini kur [risk 3, geri alınabilir]");
  gerçek koşu yalnız farkı kapatır, sonra yeniden tarar (kalan fark varsa hata); aşamalı (test grubu); her eylem geri
  alma eylemiyle `results/duzeltmeler/kayit.jsonl`'a yazılır. İkinci koşu hiçbir şey yapmaz (idempotent).
  `yazilim_politikasi_geri_al` aynı yoldan tersini yapar (dosya yedeğe, kurulan paket kalkar, kaldırılan eski sürümüyle
  döner). Kullanıcı silme geri alınamaz olarak işaretlidir (risk 4).
- Talepten politika: becerilerin satır içi listeleri (`paketler_kurulu`, `paketler_yok`, `servisler_calisiyor`,
  `servisler_durmus`, `kullanicilar_var`) modelin doldurduğu dar listelerdir; parametre denetimi her adın talepte
  geçtiğini zorlar. Kod bunları politika olarak kaydeder (atama = planın hedefi) ve sürümler; `yazilim_politikasi_
  tanimla` (risk 1) yalnız tanımlar. Talep bir politika adı söylemiyorsa model politika seçemez (kod reddeder).
- Teslim politikaları (B3) bu nesneyi kullanır: `ayarlar/teslim_politikalari.json`'da profil `politika` +
  `on_onayli` (adım türleri) + ön/son adımlar taşır; paket/kullanıcı/dosya/servis adımları politikadan üretilir
  (`teslim_adimlari`). `web` profilinin üretilen adımları eskisiyle bire bir aynı (erişim, envanter, paket_kur ön onaylı,
  paket_dogrula, kullanici_ac, dosya_dagit, servis_baslat ön onaylı, servis_durumu); "web sunucusu standardı" artık tek
  yerde (`web-standardi`).
- Eylem yürütücüsü (`filo/duzelt.py`) ortak: komutları aileye göre kod üretir, her eylem için `eylem|sıra|rc|son satır`,
  risk ve geri alma eylemi koddadır; sürüm sabitleme (apt madison, dnf list, apk ~) ve "sürüm depoda yok" ayrımı.

**Doğrulama**
- Gerçek laboratuvarda: `web-standardi` taraması iki web sunucusunda 4 fark; önizleme; `test_grubu=PA-WEB-01` ile
  uygulama (test → kalan) 4/4 düzeltildi, kalan 0; ikinci uygulama "sapma yok"; PB-WEB-01 geri alma 4 eylem (dosya yedeği
  dahil); talepten `paketler_kurulu=[jq], paketler_yok=[filo-izleme]` PA-APP-02 (RHEL) + PB-APP-01 (Alpine) 2/2.
  Bu sırada bulunan iki hata düzeltildi: aşamalı yardımcı tek aşamada işleyiciyi sunucu sayısı kadar çağırıyordu
  (ikinci çağrı "sapma yok" diyordu); dosya yedeği yolu kabukta yanlış tırnaklanıyordu (geri alma "yedek yok").
- `test_d123.py`: sapma ve eylem/geri alma üretimi, satır içi politika, teslim adımlarının politikadan üretilmesi;
  laboratuvarda `test_lab_politika_idempotent_ve_uyum_duzelt`. `test_teslim.py` (5) değişmeden geçiyor.

**Eksik / not**
- Kurulum sırası ve paket bağımlılığına göre sıralama, ön/son betik politikada yok (yama uygulamasında var).
- Dosya girdisi yalnız kütüphane dosyasıdır; şablon/değer kümesi (aile 11, Application Configuration) yok.

## D3 — Uyum denetimi ve anlık görüntü

**Yapılan** (`filo/uyum.py`, `ayarlar/uyum_kurallari.json`)
- Kural türleri: dosya (var/yok, izin üst sınırı, sahip, içerik deseni olmalı/olmamalı; dosya yoksa ihlal ya da
  uygulanamaz), paket (kurulu/yok, en az sürüm), servis, kullanıcı, grup (istenmeyen üye), sysctl, port (açık/kapalı),
  komut (salt-okur izin listesinden geçmeli; çıktı deseni ve çıkış kodu). Aile kısıtı. Kural seti sürümlü
  (`temel-sertlestirme`, 12 kural: SSH root ve parola girişi, /etc/shadow ve sudoers izni, parola yaşlandırma, giriş
  uyarı metni, uygulama yapılandırma izni, telnet portu ve paketi, eskiadmin hesabı, ASLR, tek UID 0).
- İstisna: kural + sunucu seçici + gerekçe + bitiş; süresi dolan uygulanmaz, ihlal açıklamasına "istisnanın süresi doldu"
  yazılır.
- `uyum_denetle` (risk 0): sunucu başına puan (geçen / uygulanabilir), ihlaller, istisnalar; koşu
  `results/uyum/<zaman>-<set>.json` + son durum. `uyum_duzelt` (risk 3; `yalniz_geri_alinabilir=false` → 4): ihlallerin
  düzeltme eylemleri D2 ile aynı yürütücüden; varsayılan yalnız geri alınabilenler (hesap silme gibi geri alınamaz
  düzeltme "geri alınamaz; yapılmadı" diye bırakılır), sonra yeniden denetler (puan önce → sonra). `uyum_geri_al`.
- Anlık görüntü: `anlik_goruntu_al` (risk 1) paketler/sürümler, servisler, kullanıcılar, açık portlar, seçili dosyaların
  özet/izin/sahibi, sysctl → `results/goruntuler/<sunucu>/<zaman>.json`. `goruntu_karsilastir` (risk 0): referans bir
  sunucu (altın sunucu) ya da "onceki" (kendi son görüntüsü); fark metni önce yapılandırma farklarını (servis, kullanıcı,
  dosya, port, sysctl, sürüm) sonra paket listelerini (kalabalıksa özet) verir. Docker'ın konteyner içi DNS dinleyicisi
  (127.0.0.11, rastgele port) gürültü olarak süzülür.
- Rapor: CSV/XML/HTML ve e-posta var olan yoldan (Kalfa/Kaptan: sonucu_donustur + eposta_gonder).
- Laboratuvar: PA-APP-01 ve PB-APP-01'de `eskiadmin` hesabı (`FILO_KULLANICILAR`), geri alınamaz düzeltme örneği.

**Doğrulama**
- Gerçek laboratuvarda: denetim 8 sunucu, puanlar 64-92; PB-DB-01'de parola-yaslanma istisna; düzeltme önizlemesi
  "eski-hesap-yok: geri alınamaz; yapılmadı"; düzeltme PA-APP-01 67 → 92, PB-APP-01 64 → 82; geri alma 3 eylem;
  karşılaştırma PB-APP-01 / PA-APP-01 ve PA-WEB-01 / PA-APP-01; "onceki" ile fark 0. Bu sırada bulunan hata: toplayıcı
  root'a ait dizindeki dosyayı (`/etc/sudoers.d/filo`, AlmaLinux/Alpine'de dizin 0750) "yok" görüyordu; sudo ile
  bakılır.
- `test_d123.py`: kuralların değerlendirilmesi, istisna, geri alınabilirlik, yazan komutlu kuralın reddi, karşılaştırma
  ve fark metni; laboratuvarda uyum düzeltmesinin hesabı silmemesi ve izni 640 yapması.

**Eksik / not**
- Zamanlanmış/tekrarlı denetim ve görüntü işi ayrı tanımlı değil; ama her beceri zamanlanabilir (C2) — denendi değil.
- Kural seti düzenleme arayüzde yalnız istisna ekleme olarak var; kural ekleme JSON/API ile (`/api/uyum/kural-seti`).
- ISO/CIS içerik paketleri (F-SV-014) yok; kural seti elle yazılır.

## Dördüncü tur yarıda kesildi (17 Kasım 2026, 23:15, ana oturum)

Kullanıcı "bitir artık" dedi; dördüncü turun ajanı D4 (arayüz) sırasında durduruldu. Bu dal (`dorduncu-tur`) yarım işi taşır;
`main` ilk sürümde (f8d8173) kalır.

- Yapılan: D0 (açık kusurlar), D1 (yama), D2 (yazılım politikası), D3 (uyum denetimi ve anlık görüntü); ayrıntı yukarıdaki
  D0–D3 bölümlerinde. Laboratuvara yerel paket deposu (`filo-depo`) eklendi.
- Yapılmayan: D4 (Yama/Politikalar/Uyum sayfaları ve `docs/ekran/` görüntüleri) yarım; D5 (yeni senaryolar, qwen3:8b ve
  Opus 5 tam koşuları) hiç başlamadı.
- Testler: laboratuvar istemeyenlerde 164 geçti, 6 kaldı (`test_inisiyatif.py` 4, `test_b7_duzeltmeler.py` 2). Belirti:
  sahte modelle yazılmış testlerde aday beceri daraltması değişmiş (`ajan_ortak.py`), beklenen beceri yerine "hicbiri" ya da
  durum "hata" dönüyor. Neden doğrulanmadı; ilk iş bunu düzeltmek.
- Model kapısı (ana oturum): `anthropic` yolu yeni Claude API'sine uyarlandı (temperature yok, `output_config.effort`,
  refusal, yedek model); yeni tür `claude-cli` (Claude Code başsız kipi, abonelikle). Bağlantılar: `claude-cli-opus5`
  (Claude Opus 5, çalışıyor; Kalfa talep planı 4 çağrı, 17 sn), `claude-cli-opus` (Opus 5.5; komut satırı 2.1.280+ ister,
  `claude update` gerekir), `claude-opus-5-5` (API anahtarı ister; anahtar yok). Opus 5 ile bench koşulmadı.
