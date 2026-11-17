# Filo

Sunucu otomasyonu (sunucu otomasyonu sınıfı) ve runbook otomasyonu (akış otomasyonu sınıfı) adminlik işlerini
bir yapay zekâ ajanına yaptıran, modelden bağımsız, konsollu bir harness ve onun bench'i. Filo sunucu/akış'yu yönetmez; o
ürünlerin yaptığı işi kendi katmanıyla yapar: sunucularda çalışan Go ajanı (`filo-ajan`), tipli beceri kataloğu, iki ajan.

Dili anlamak, plan kurmak ve hatayı yorumlamak modelin işidir. Hedef çözümleme, paralel yürütme, şema denetimi, yetki,
onay ve denetim izi kodun işidir.

- **Kalfa** (iş konsolu): yalnız hazır becerilerle çalışır (talep → beceri → parametre → dondurulmuş hedef → plan →
  onay → yürütme → rapor). "Beceriden başla" kipinde model hiç çağrılmaz.
- **Kaptan** (akış tuvali): talepten akış kurar, adım adım yürütür; hata ya da şema uyumsuzluğunda teşhis koyar, onarır,
  beceriyi yeni sürüm olarak değiştirebilir (risk kodla yeniden sınıflanır), sınırlı yeniden dener, olmazsa insana
  devreder. Ne kadar serbest olduğunu operatörün verdiği **inisiyatif düzeyi** (0-3) belirler; yıkıcı işler her
  düzeyde insan onayı ister. Başarılı akış tek adımda **beceriye dönüşür**.
- **filo-ajan** (Go, yalnız standart kitaplık): sunucuda port açmaz, çekirdeğe dışarı doğru bağlanır; imzalı istekler ve
  imzalı iş paketleri. Canlı ajan varsa iş ajandan, yoksa SSH'tan gider.
- **Zamanlama ve pencereler**: tek seferlik / tekrarlı (gün, hafta, ay, isteğe bağlı cron) / "bakım penceresinde" işler;
  yasak (blackout) pencerede değiştiren iş başlamaz (bekle / sor / atla). Talepteki "her gece 02:00'de" gibi ifadeyi ajan
  yapılandırılmış zamanlamaya çevirir, kod doğrular ve sonraki 3 çalışmayı gösterir; önceden onay tanım sürümüne bağlıdır.
- **Koşu denetimi**: çalışan işi duraklat / sürdür / iptal / devret; tamamlanan her adımdan "yalnız başarısızlarla" ya da
  "hepsiyle" yeniden çalıştır; durum kalıcıdır (konsol yeniden başlasa da sürer). Kaptan insana devredince iş bekler,
  operatörün notu ve kararı Kaptan'a girdi olur.
- **Yapılı akış**: dal, sunucu bazında dal, döngü (üst sınır zorunlu), paralel kollar, alt akış, bekleme, insan onayı,
  bildirim; şema kodla doğrulanır. Model akışı tek seferde yazmaz: kod iskelet ve seçenek sunar, model dar kararlar verir.
- **Çalıştırma kimliği**: bağlantı kullanıcısı, root (sudo) ya da adı verilen kullanıcı; sunucu/grup başına izinli
  kimlikler; izinsiz kimlik planda reddedilir, sudo izin vermezse sonuç "yetki yok".
- **Teslim politikaları**: yeni sunucuya ajan kaydolunca profilin beceri zinciri (standart paketler, kullanıcı, servis,
  dosya, doğrulama, teslim raporu) kendiliğinden başlar; yarıda kalırsa Kaptan devralabilir. Profilin değiştiren adımları
  bağlı olduğu yazılım politikasından üretilir.
- **Yama**: bekleyen güncellemeler ve güvenlik sınıfı (apt/dnf/apk farkını beceri çözer), yama politikası (hedef,
  kapsam, gerekçeli ve süreli hariç tutma / istisna), uyum raporu, uygulama (kuru çalıştırma ve fark önizlemesi; önce
  test grubu, başarılıysa kalanlar; ön/son kontrol betiği, son kontrol düşerse eski sürüme iner; yeniden başlatma asla /
  gerekirse / bakım penceresinde), geri alma (önceki sürüme indirme; yapılamıyorsa açıkça söyler).
- **Yazılım politikası**: istenen durum (paketler, servisler, kullanıcılar, dosyalar ve kime atandığı), sürümlü; sapma
  taraması, önizleme, yalnız farkı kapatan ve tekrarında hiçbir şey yapmayan remediation, geri alma. "Web sunucularında
  jq kurulu olsun, telnet olmasın" gibi bir talepten model dar listeleri doldurur, kod denetler ve politikayı kaydeder.
- **Uyum ve anlık görüntü**: kural setleri (dosya, paket, servis, kullanıcı/grup, sysctl, port, komut çıktısı),
  sunucu başına puan ve ihlaller, gerekçeli ve süreli istisnalar, düzeltme (varsayılan yalnız geri alınabilenler);
  yapılandırmanın anlık görüntüsü ve iki sunucunun ya da bir sunucunun iki zamanının karşılaştırması (altın sunucu).

Ayrıntılar: `docs/00-devir-notu.md` (tasarım), `docs/ilerleme.md` (ne yapıldı, nasıl doğrulandı, ne eksik).

## Gereksinimler

- Python 3.11 (çekirdek ve web sunucusu yalnız standart kitaplık; testler için `pytest`)
- Sistemdeki OpenSSH istemcisi (`ssh`, `scp`, `ssh-keygen`)
- Docker (laboratuvar: 8 küçük Linux konteyneri + 2 isteğe bağlı "yeni" sunucu + Mailpit; Go ajanı da resmi `golang`
  imajında derlenir, Go'yu makineye kurmak gerekmez)
- Bir model bağlantısı: yerel Ollama (`qwen3:8b`), OpenAI uyumlu yerel sunucu (LM Studio, llama.cpp, vLLM) ya da
  Anthropic / OpenAI / Gemini API'si

## Kurulum

```
python -m filo lab kur          # anahtarları üretir (lab/anahtar/, git dışında), imajları kurar, konteynerleri başlatır
python -m filo lab depo-derle   # yalnız yerel paket deposunu yeniden üretmek için (bir kez internet ister; çıktı lab/depo/srv)
python -m filo lab durum --erisim
python -m filo ajan derle        # Go ajanı: go vet + go test + linux/amd64, linux/arm64, windows/amd64 (ajan/cikti/)
python -m filo winrm-kontrol     # Windows hedefi için; Filo sistem ayarı değiştirmez, eksikse komutları söyler
```

## Çalıştırma

```
python -m filo web --port 8790                 # konsol http://127.0.0.1:8790 + ajan kapısı 127.0.0.1:8795
python -m filo ajan kur --hedef "os:linux" --onayla      # ajanları SSH ile kur (risk 3: onay)
python -m filo ajan durum | onar --hedef X | kaldir --hedef X | belirtec --hedef X
python -m filo calistir --hedef "PA*" --komut "hostname; uname -r"   # salt-okur komut (YOL sütunu: ajan/ssh)
python -m filo is --hedef "PA*" --beceri betik_calistir --param betik=uygulama_surumu --bicim xml --eposta ops@lab.yerel
python -m filo is --hedef "PA-APP-01" --beceri komut_calistir --param "komut=id -un" --kimlik root   # çalıştırma kimliği
python -m filo talep "PB grubundaki sunucuların disk doluluğunu göster" --ajan kalfa
python -m filo talep "PA-APP-01'de uygulama servisi durmuş, düzelt" --ajan kaptan
python -m filo lab yeni-sunucu PA-WEB-02       # yeni sunucu aç; ajan kurulunca teslim profili kendiliğinden başlar
python -m filo teslim liste | denetle | baslat <sunucu>
python -m filo beceri liste | gecmis <ad> | fark <ad> 1 2 | geri-al <ad> 1
python -m filo onay liste | ver <kimlik> | reddet <kimlik>
python -m filo denetim --dogrula
python -m filo durdur            # durdurma düğmesi: bütün uzak işlemleri ve ajan işlerini keser (kaldırmak için --kaldir)
```

Konsol sayfaları: `/` genel bakış, `/kalfa`, `/kaptan`, `/onaylar`, `/zamanlama`, `/pencereler`, `/envanter`, `/ajanlar`,
`/teslim`, `/yama`, `/politikalar`, `/uyum`, `/beceriler`, `/bench`, `/karsilastirma`, `/baglantilar`, `/denetim`.
Ekran görüntüleri: `docs/ekran/`. Mailpit: http://127.0.0.1:18025.

Laboratuvarın tek paket kaynağı laboratuvar ağındaki `filo-depo` konteyneridir (kurum içi ayna gibi; internet gerekmez):
örnek paketlerin eski sürümleri imajlarda kurulu, yeni sürümleri depoda olduğu için "bekleyen yama" tekrarlanabilir.
Konteynerde gerçek yeniden başlatma yoktur; `systemctl reboot` / `reboot` bir öykünmedir (açılış kimliği yenilenir,
servisler yeniden başlar).

Model bağlantıları `ayarlar/baglantilar.json` içindedir; konsolun Model bağlantıları sayfasından da eklenir. API anahtarı
ya bir ortam değişkeninin adıyla (`anahtar_ortam`) ya da git dışındaki `ayarlar/gizli.json` dosyasında durur; geri
gösterilmez. Ajan gizli anahtarları `ayarlar/ajan_gizli.json` (git dışı).

## Bench

```
python -m filo bench liste
python -m filo bench dogrula                 # her senaryo referans çözümle geçmeli, boş çözümle kalmalı
python -u tools/isi_bekcisi.py 60            # model kollarından önce arka planda (makine ısı sınırı)
python -m filo bench kos --kol yardimsiz kalfa kaptan --baglanti yerel-qwen3-8b --kosu <ad>
python -m filo bench rapor
```

59 senaryo `bench/temel|orta|ileri/*.json` (üçüncü turda 15 yeni: zamanlama Z01-Z04, çalıştırma kimliği K01-K02, koşu
denetimi D01-D03, akış yapıları A01-A06; dördüncü turda 14 yeni: yama Y01-Y08, yazılım politikası P01-P04, uyum U01-U03,
altın sunucu G01). Kaynakları `docs/arastirma/05-forum-vakalari.md` (OpenText forumu),
`03-vaka-taslaklari.md`, `07-talep-karsilastirmasi.md`, `08`, `09`, `09b`, `09c`. Zaman isteyen senaryolarda saat sahtedir.

## Testler

```
python -m pytest            # laboratuvar isteyen testler `lab` işaretlidir, laboratuvar yoksa atlanır
```

Laboratuvar tek kullanıcılıdır: bench koşusu ve laboratuvar sınamaları `results/LAB_KILIT` kilidini alır; biri sürerken
öteki başlamaz (pytest laboratuvar sınamalarını gerekçesiyle atlar).

Go testleri `python -m filo ajan derle` içinde konteynerde koşar.
