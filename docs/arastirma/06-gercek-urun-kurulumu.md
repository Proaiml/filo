# OpenText sunucu otomasyonu (sunucu otomasyonu) 25.4 ve akış otomasyonu (akış otomasyonu) 26.4: Gerçek Kurulum Bilgileri

Tarih: 2026-11-17. Yöntem: OpenText belge portalı (docs.microfocus.com) tarayıcı üzerinden açılıp okundu. Giriş gerektiren indirme portalı (SLD) açılmadı, hiçbir indirme yapılmadı, hesap açılmadı, form gönderilmedi.

Etiketler: **[okundu]** sayfayı açıp okudum; **[ana oturum okudu]** bu araştırmanın başında ana oturum okudu, burada yeniden açmadım; **[doğrulanamadı]** kaynak bulunamadı ya da bilgi belgede yok.

Eski taslakta yazılan sürüm bilgileri (sunucu otomasyonu 10.60, akış otomasyonu 10.x, Oracle zorunluluğu, akış otomasyonu Community imajı) bu yeni okumayla geçersiz kabul edildi.

## Sonuç ve önerilen yol

**akış otomasyonu 26.4 için öneri:** Windows 11 Home üzerine akış otomasyonu Central doğrudan kurulmamalı. Destek matrisinde Central için yalnızca Windows Server 2016/2019/2022/2025 ve SUSE 15, RHEL 8/9/10, Rocky 9.3/10 listeli; Windows 10/11 yalnız akış otomasyonu Studio, Recorder ve Robot için destekli. Öneri: VirtualBox veya VMware içinde Rocky Linux 9.x (ya da RHEL 9.x) bir VM; VM içinde PostgreSQL 16 veya 17 (desteklenen 15-18 arasından). akış otomasyonu Central bu VM'e sessiz kurulumla kurulur. akış otomasyonu Studio Windows 11'de çalıştırılır.

**sunucu otomasyonu 25.4 için öneri:** Tek sunucu (single-host) core, RHEL veya SUSE Linux VM'inde; Model Repository için Oracle VEYA PostgreSQL (eski taslağın "Oracle zorunlu" iddiası düzeltildi). Önerilen veritabanı donanımı 32 GB RAM ve 12 CPU; bu dizüstünde (29,7 GB RAM, Windows açıkken) bu öneri karşılanmaz. Core için resmi RAM minimumu bulunamadı. sunucu otomasyonu bu dizüstünde en fazla deneme amaçlı ve destek dışı kalır; önce OpenText'ten deneme talebi gerekir.

**İki ürün aynı anda çalışmaz:** akış otomasyonu VM'i (4-6 GB) ile sunucu otomasyonu VM'i (önerilen 32 GB+) birlikte bu dizüstünde yapılamaz.

**Kullanıcının kendi yapacakları (indirme ve kabul, bizim yapamayacağımız adımlar):**
1. OpenText hesabıyla Software Licenses and Downloads portalına (https://sld.microfocus.com/mysoftware/index) giriş. Parolayı ve doğrulama kodunu kendiniz girin.
2. akış otomasyonu için indirilecek dosya: `OO_Product_SW_and_Doc_<sürüm>_oo-<sürüm>.zip` (sürüm numarası portaldaki güncel sürüme göre). Boyutu doğrulanamadı.
3. sunucu otomasyonu 25.4 için indirilecek medya: "sunucu otomasyonu Product Software" ve "Agent and Utilities" (SLD'deki tam dosya adları doğrulanamadı). Oracle kurulum medyası sunucu otomasyonu medyasında yok.
4. Lisans ve kullanım koşullarını kabul (akış otomasyonu deneme lisansı 61 gün; sunucu otomasyonu AutoPass InstantOn 60 gün [ana oturum okudu]).
5. RHEL veya SUSE kullanılacaksa abonelik ve lisans koşullarını kendiniz kontrol edin. Rocky Linux için böyle bir abonelik gerekmez (bu konuda belge okunmadı, [doğrulanamadı]).
6. Kurulum sırasında akış otomasyonu ve sunucu otomasyonu yönetici parolalarını kendiniz girin.

**Bizim yapacağımız adımlar (kullanıcı indirmeleri ve kabulleri tamamlandıktan sonra):**
1. VirtualBox/VMware için VM oluşturma planı (işletim sistemi, RAM, disk) ve PostgreSQL kurulum adımlarını belgelemek.
2. akış otomasyonu Central için `silent.properties` taslağı hazırlamak (ürün ZIP'indeki `config/sample-silent.properties` dosyasından).
3. Kurulum sonrası akış otomasyonu REST API ile bir test akışı başlatmak (yalnız kullanıcı onayıyla ve yerel test ortamında).
4. sunucu otomasyonu core kurulum ön kontrol listesini (disk, NFS, ağ, zaman ayarı) bir kontrol dosyasına çevirmek.

## akış otomasyonu 26.4

### Gereksinimler

| Konu | Belgedeki değer | Kaynak |
|---|---|---|
| İşletim sistemi (akış otomasyonu Central, RAS, Workflow Designer, Self-Service X) | Windows Server 2016, 2019, 2022, 2025; SUSE Enterprise Linux 15.x; RHEL 8.3, 8.4, 8.6, 8.10, 9.0, 9.4, 9.8, 10.0; Rocky Linux 9.3, 10.0 | [okundu] supportmatrix |
| İşletim sistemi (akış otomasyonu Studio) | Windows Server 2016-2025, Windows 10 ve 11 (x86_x64; 32 bit desteklenmiyor) | [okundu] supportmatrix |
| İşletim sistemi (Recorder, Robot) | Windows Server 2016-2025, Windows 10 ve 11 | [okundu] supportmatrix |
| Central CPU | Minimum 1 çekirdek, önerilen 4 çekirdek | [okundu] supportmatrix |
| Central RAM | Minimum 2 GB, önerilen 4 GB | [okundu] supportmatrix |
| Central disk | 4 GB | [okundu] supportmatrix |
| Workflow Designer / Self-Service X RAM | Minimum 2 GB, önerilen 6 GB; disk 2 GB | [okundu] supportmatrix |
| RAS | 1 GB RAM, 2 GB disk | [okundu] supportmatrix |
| Studio | 2 GB RAM, 4 GB disk, 1 çekirdek, ekran 1280x1024 | [okundu] supportmatrix |
| Veritabanı sunucusu CPU/RAM | En az 2 çekirdek; RAM satıcı önerisine göre, en az 4 GB | [okundu] supportmatrix |
| Veritabanı disk (merkezi, Central) | 50 GB (çok kullanımda 100 GB+); ayrı sunucuda 80 GB (yoğun kullanımda 140 GB+) | [okundu] supportmatrix |
| Veritabanları (Central) | Oracle 19c; PostgreSQL 15.x, 16.x, 17.x, 18.x; Microsoft SQL Server 2016, 2017, 2019, 2022 (Standard ve Enterprise) | [okundu] supportmatrix |
| Tarayıcı | Chrome 96+, Firefox 91.5.1 ESR ve 95+, Edge Chromium 89+ | [okundu] supportmatrix |
| Yazılım çerçevesi | .NET Framework 4.5+ (RAS ve .NET operasyonları için) | [okundu] supportmatrix |
| Sıkıştırma | bzip2 (Red Hat sistemlerde Central kurulumu için gerekli) | [okundu] supportmatrix |
| Lisans sunucusu | AutoPass License Server 11.8.1 - 24.1 | [okundu] supportmatrix |
| RabbitMQ | 3.13.x ve 4.2.x (RPA Robot ve Recorder için) | [okundu] supportmatrix ve installcentral |
| Portlar | Central HTTPS 8443; Python Executor 8001 (localhost); RAS 8002; Workflow Designer 8445; Self-Service X 8446; Recorder 5443 | [okundu] supportmatrix |
| Java | Destek matrisinde Java sürümü geçmiyor | [doğrulanamadı] |
| Embedded (gömülü) veritabanı | Destek matrisinde gömülü veritabanı yok; yalnız yukarıdaki sunucu veritabanları listeli | [okundu] supportmatrix |

Not: Destek matrisinde Central için bir sanal makine türü (Hyper-V, VirtualBox vb.) ayrıca belirtilmiyor. Bulut ve sanal makine için ayrı sayfa var (Virtual systems and cloud deployments); bu sayfa okunmadı [doğrulanamadı].

### Kurulum yöntemleri

- **Grafik sihirbazı (installer):** Windows için `installer-oo-win64-<sürüm>.exe` çift tıklanır. Linux için `bash installer-oo-linux64-<sürüm>.bin` komutu; kurucu bir X11 grafik ortamı ister. Varsayılan dizinler: Windows `C:\Program Files\Micro Focus\akış otomasyonu`, Linux `/opt/microfocus/oo`. Kurulum yolunda yalnızca İngilizce harf, rakam, boşluk, tire ve alt çizgi olmalıdır [okundu] installcentral. Linux dizin adlarında özel karakter olamaz [okundu] cleaninstallation.
- **Sessiz kurulum (silent):** Windows için komut: `installer-win64.exe -gm2 -s c:\\temp\my-silent.properties` (-gm2 ilerleme çubuğunu kapatır; -n Central'ı kurulum sonunda başlatmaz). Linux'ta -gm2 desteklenmez. Yanıt dosyası ürün ZIP'indeki `config` klasöründeki `sample-silent.properties` dosyasından kopyalanır; kullanılacak satırların başındaki `#` silinir. Ters eğik çizgi (\) kullanılan değerlerde çift yazılmalıdır (`\\`). Dosya yolunda boşluk olmamalıdır. Sihirbaz ve sessiz kurulumun varsayılanları farklıdır (sertifika: sihirbazda CA, sessizde self-signed; HTTP: sihirbazda kapalı, sessizde açık) [okundu] silentinstall.
- **Küme (cluster):** İkinci bir Central aynı veritabanı şemasına bağlanarak kümeye eklenir. Canlı ölçekleme için kesinti gerekmez [okundu] deploymentarchitecture.
- **Kurulum sihirbazı adımları (Central):** Lisans kabulü, konum, seçenek (Central), Central kümesi (atla), IdM (akış otomasyonu built-in ya da IdM), Central sunucu bağlantısı (port 8443, TLS sertifikası), veritabanı bağlantısı (Oracle, SQL Server, PostgreSQL veya "Other database"), bağlantı testi [okundu] installcentral.
- **Kimlik doğrulama:** Yerleşik akış otomasyonu kimlik doğrulaması (built-in) veya IdM. Parola kuralları: 8-20 karakter, büyük ve küçük harf, rakam, özel karakter. IdM "Create" modunda ayrı bir IdM veritabanı gerekir; IdM HA henüz tam değil [okundu] installcentral.
- **RPA bileşenleri:** RabbitMQ ve Erlang yalnız RPA Robot ve Recorder için gerekir [okundu] installcentral. Ancak "Install akış otomasyonu components" sayfasında akış otomasyonu Central'ın önkoşulları arasında "Erlang ve RabbitMQ" yazıyor; bu iki sayfa çelişiyor. Kurulumdan önce RabbitMQ'nun gerekip gerekmediği doğrulanmalı [okundu, çelişki] cleaninstallation ve installcentral.

### Kurulum adımları özeti

1. Ön hazırlık: donanım ve işletim sistemi kontrolü, Administrator/root yetkisi, UAC (Windows) için yönetici olarak çalıştırma [okundu] cleaninstallation.
2. Veritabanı hazırla: "Set up database environment for akış otomasyonu Central" altında Oracle, SQL Server ve PostgreSQL için ayrı alt sayfalar var. Kullanıcı yetkisi DDL ve DML [okundu] setupdatabaseoo. (PostgreSQL alt sayfasının içeriği okunmadı [doğrulanamadı].)
3. Medyayı çıkar ve kurucuyu çalıştır (Windows exe veya Linux bin). Kurucu bir ZIP'i açar ve sihirbazı başlatır [okundu] installcentral.
4. Sihirbazdan Central'ı seç, IdM ve TLS ayarlarını yap, veritabanını bağla (bağlantı testi zorunlu), kurulumu bitir.
5. Kurulum sonrası: Central'ı lisansla (varsayılan 61 günlük deneme; 2 eşzamanlı akış) [okundu] licenses.
6. Sağlık kontrolü: `https://<IP>:<PORT>/oo/hello.html` (port varsayılan 8443) [okundu] deploymentarchitecture.

Önemli: Sessiz kurulumun Central'a özgü parametre listesi (alt bölüm "Silent installation of akış otomasyonu Central") okunmadı; ayrı bir sayfa olabilir [doğrulanamadı]. Yanıt dosyasının alan adları için ZIP içindeki `sample-silent.properties` dosyası esas alınmalı.

### API yüzeyi

- **Kök yol:** Tüm REST çağrıları `/oo/rest/v2/` önekiyle yapılır (örnek: `POST /oo/rest/v2/executions`). Tam adres: `https://<central-host>:8443/oo/rest/v2/...` [okundu] apiintro, restapis.
- **Biçim:** JSON; Content-Type ve Accept genelde application/json [okundu] apiintro.
- **Kimlik doğrulama:** Basic (ön tanımlı) — her istekte `Authorization: Basic base64(kullanıcı:parola)`. Yanlış kimlik 401, yetkisiz işlem 403 döner [okundu] basicauthentication. CSRF koruma sayfası ana sayfaya yönlendirdi; doğrulanamadı [doğrulanamadı] (csrfprotection).
- **Akış başlatma:** `POST /executions`. Gövde: `flowUuid` (zorunlu), `runName` (isteğe bağlı; önerilen format `<UygulamaAdı>:<Kullanıcı>:<Hedef>:<Eylem>`), `logLevel` (STANDARD ya da EXTENDED), `inputs`, `inputPromptUseBlank`, `sensitiveInputs`. Yanıt 201 ve `executionId`; Location başlığı `/executions/<id>/steps` [okundu] executeflowuuid.
- **Koşu durumu:** `GET /executions` (sayfalama `pageNum`, `pageSize` (varsayılan 200), filtreler: `flowPath`, `status`, `owner`, `runName`, `executionId`, `flowUuid`, `startedAfter`, `startedBefore`). Durum değerleri: RUNNING, COMPLETED, COMPLETED_ERROR, PAUSED, CANCELED vb. [okundu] restapis.
- **Diğer koşu uç noktaları (adları okunan sayfada):** Get execution summary, Get execution log, Get execution steps (sayfalı, CSV, metin), Change the status of an execution, Flow execution status, Flow input, Rerun from step, Purge execution data [okundu] (TOC listesi, restapis).
- **Akış kitaplığı, zamanlayıcı, deployment, kuyruk, içerik paketleri:** Content packs için `GET /content-packs` (`active=true|false` parametresi) okundu [okundu] contentpacks. Flow library, Scheduler, Deployment ve Workers sayfaları TOC'da var; içerikleri okunmadı [doğrulanamadı].
- **akış otomasyonu komut satırı (akış komut aracı) ve komut satırı araçları:** Belgede bulunamadı [doğrulanamadı].
- **Ek API grupları (TOC):** Dashboard, Audit events, LDAP, Users, Roles, System log level, Get akış otomasyonu version, RPA Robot APIs, Self-Service X APIs [okundu, yalnız TOC].

### İçerik paketleri

- Content pack bir akış, operasyon, yapılandırma öğesi ve bağımlılık binary'lerinden oluşur. akış otomasyonu Workflow Designer'da hazırlanabilir ya da ITOM Marketplace'ten indirilebilir [okundu] contentpacks.
- Entegrasyon için akış otomasyonu-sunucu otomasyonu içerik paketi: `oo10-sa-cp-<VERSION>.jar` (ITOM Marketplace, "akış otomasyonu Content for sunucu otomasyonu"); akış otomasyonu Studio ve akış otomasyonu Central'a aktarılır [ana oturum okudu; oosaintegration].
- Marketplace içerikleri için satıcı şartlarının kabulü gerekir [doğrulanamadı; ayrıntısı okunmadı].

## sunucu otomasyonu 25.4

### Gereksinimler

| Konu | Belgedeki değer | Kaynak |
|---|---|---|
| Core işletim sistemi | Tüm core sunucuları aynı işletim sistemini çalıştırmalı; kurulum sayfasında RHEL veya SUSE Enterprise Linux; tam sürüm listesi "sunucu otomasyonu Support and Compatibility Matrix" adlı harici belgede | [okundu] preinstallationsystemchecks, remotecustomersuppliedoracledatabase, checkhostagentssatellitessupported |
| Desteklenen Agent (yönetilen sunucu) platformları | Harici uyumluluk matrisinde; sayfa içinde liste yok | [okundu, harici matrise bağlı] |
| Core disk (tek core, kök dizin) | En az 150 GB boş (ayrı bölüm kullanılmıyorsa); /etc/opt/opsware 50 MB; /media 15 GB; /opt/opsware 25 GB; /var/log/opsware 80 GB; /var/opt/opsware 30+ GB; word host 80 GB; yazılım deposu (word*) için 80 GB + yazılıma göre değişken (10-250 GB arası bilinen boyutlar) | [okundu] freediskspacerequirements |
| Core RAM ve CPU (resmi minimum) | Bulunamadı | [doğrulanamadı] |
| Veritabanı sunucusu RAM ve CPU | Önerilen 32 GB+ RAM ve 12 CPU; sanal makinede RAM tam ayrılmalı; swap: RAM 4-16 GB ise swap = RAM, 16 GB üzerinde swap 16 GB | [okundu] oraclerequirements (= "Verify database requirements") |
| Veritabanı disk | Yönetilen sunucu başına 3,1 GB / 1000 sunucu (Oracle); PostgreSQL için SADATA 9216 MB / 1000 sunucu, minimum 5120 MB | [okundu] oraclerequirements |
| Slice bileşeni | Bileşen başına 24 GB RAM ve 8 CPU; Secure Boot kapalı olmalı (OGFS kernel modülü) | [okundu] slicerequirement |
| Veritabanları (Model Repository) | Oracle (sürüm ve OS listesi harici matriste, "Supported Oracle versions and operating systems") ve PostgreSQL (sürüm listesi harici matriste) | [okundu] supportedoracleversionsos, postgresqlmodelrepositorysetup |
| NFS | Kurulumda NFS servis kontrolü gerekir | [okundu] (alt sayfa adı: nfs kontrolü, içeriği okunmadı [doğrulanamadı]) |
| Zaman ve yerel ayar | Core sunucularında saat ve yerel ayar gereksinimi | [doğrulanamadı; alt sayfa okunmadı] |
| Lisans | AutoPass; InstantOn 60 gün deneme; lisans süresi bitince çalışmaya devam eder; kapasite sunucu otomasyonu Agent ile yönetilen sunucu sayısıyla ölçülür | [ana oturum okudu] saautopassintegration |
| Windows core | Kurulum sayfasında Windows core yok; Windows yalnız Windows Update, yama dosyaları ve Windows yönetimi için [okundu] | [okundu] preinstallationsystemchecks |

### Kurulum adımları özeti

Plan (sistem gereksinimleri ve planlama) > Prepare (veritabanı ve ön kontroller) > Deploy (core kurulumu) > Post-installation tasks.

1. Medyaları yerel diske kopyala veya NFS paylaşımına koy (önerilen). Kurulum kullanıcısı sudo yetkili olmalı [okundu] preinstallationsystemchecks, remotecustomersuppliedoracledatabase.
2. Veritabanını kur ve kurulumdan önce çalışır olduğunu doğrula. sunucu otomasyonu medyasında Oracle kurulumu yok. Oracle Client veya PostgreSQL Client, Model Repository'nin çalışacağı sunucuya elle kurulmalı [okundu] remotecustomersuppliedoracledatabase, oraclemodelrepositorysetup.
3. Core kurulum komutu: `/<distro>/opsware_installer/hpsa_install.sh` (`<distro>`, Product Software medyasının tam yolu) [okundu] remotecustomersuppliedoracledatabase.
4. Kurulum menüsü (belgedeki örnek akış):
   - Host seç ("c" devam).
   - Kurulum tipi: 1. Typical Primary Core (ilk core için).
   - Veritabanı: 1. mevcut Oracle veya 2. mevcut PostgreSQL.
   - TLS sürümü: TLSv1, TLSv1.1, TLSv1.2 (örnekte TLSv1.2 seçilmiş; mesh'teki tüm core'lar aynı seviyede olmalı).
   - Sertifika modu: self-signed veya 3rd party (3rd party'de /etc/hosts'a tüm core hostname'leri eklenmeli).
   - Görüşme (interview) tipi: Simple, Advanced, Expert. Simple'da girilen değerler: `truth.oaPwd` (admin parolası), `fips.mode`, `crypto.hash_algorithm` (SHA224/256/384/512), `crypto.key_length` (2048 veya 4096), `crypto.legacyCertificateValidity` (3rd party modunda).
5. Bileşenlerin kurulumu tamamlanır; log dosyaları kurulum sırasında otomatik tutulur [okundu] remotecustomersuppliedoracledatabase.
6. Diğer kurulum sayfaları: "Install sunucu otomasyonu Core with a remote database and additional slice component bundles", "Install sunucu otomasyonu first (primary) core with a secondary Core (multimaster mesh)", "Install additional slice component bundles", Satellite kurulumu [okundu] (başlıklar), içerikleri okunmadı.

Not: Belge, bu kurulumun "tek sunucu" (her bileşen aynı host) olduğunu ve veritabanının uzak (remote) olabileceğini açıkça gösteriyor [okundu] remotecustomersuppliedoracledatabase. Yani tek sunucu core + ayrı veritabanı kurulumu belgede var; tek VM'de her şey de sanal olarak mümkün görünüyor ama bunun kaynak yeterliliği resmi olarak doğrulanamadı.

### API yüzeyi

- **REST API (önerilen, yeni entegrasyonlar için):** `https://<sa-core>/rest/v1/...` [okundu] restapi.
  - Kimlik doğrulama: `POST https://<sa-core>/rest/v1/authentications/actions/authenticate?duration=3600` ile JSON `{"username": "...", "password": "..."}` gövdesi; dönen token `Authorization` başlığında kullanılır [okundu] restapi.
  - Örnek kök dizin çağrısı: `POST /rest/v1/folders/actions/get-root` [okundu] restapi.
  - API belgesi (OpenAPI): `docs.microfocus.com/api/Server_Automation` ve Twister arayüzü `https://<SA_core_host>/twister` (Command Center bileşeninin çalıştığı core) [okundu] restapi.
- **Pytwist (Python istemcisi):** Managed server ve core sunucularında çalışır; Python 3.8 (Agent ile gelir; Python 2.7 örnekleri de çalışır). Core dışı bir sunucudan kullanılmamalı; onun yerine Web Services veya Java RMI kullanılır. Erişim: core sunucusunun 1032 portu [okundu] pytwist.
  - Örnek kod: `from pytwist import *`, `ts = twistserver.TwistServer()`, servis referansı `ts.server.ServerService` [okundu] pytwist.
- **Web Services (SOAP):** REST sayfası SOAP Web Services'in kullanımdan kaldırıldığını ve REST'e geçiş yolu olduğunu söylüyor [okundu] restapi. Ayrıntılı SOAP sayfası okunmadı [doğrulanamadı].
- **Java RMI:** sunucu otomasyonu Platform başlığı altında listelenmiş; içerik okunmadı [doğrulanamadı].
- **sunucu otomasyonu CLI yöntemleri, Global Shell / OGFS:** Başlık TOC'da var (sunucu otomasyonu CLI methods); içerik okunmadı [doğrulanamadı]. Eski 10.60 bilgisinde CLI'ın OGFS üzerinden Global Shell oturumunda çalıştığı yazılıydı; 25.4 için doğrulanamadı.
- **Windows PowerShell entegrasyonu:** REST ve SOAP üzerinden iki ayrı sayfa var (TOC); içerik okunmadı [doğrulanamadı].
- **Agent Tools, Pluggable checks, Advanced pluggable checks, Search filter syntax, Application Configuration:** TOC'da var; içerik okunmadı [doğrulanamadı].
- **Platform giriş sayfası:** sunucu otomasyonu Platform, "Automation Platform Extensions (APX)", "Web Services clients", "Java RMI clients" bölümleri [okundu, yalnız TOC].

### akış otomasyonu ile sunucu otomasyonu entegrasyonu

- Gereksinimler: akış otomasyonu-sunucu otomasyonu içerik jar'ı (ITOM Marketplace) akış otomasyonu'ya kurulur; sunucu otomasyonu bağlantı parametreleri: `coreHost`, `corePort` (varsayılan 443), `coreProtocol` (varsayılan https), `coreUsername`, `corePassword`, `coreVersion` (sunucu otomasyonu 25.4 için değer: sayfada eşleme tablosunda 24.1 = sas241, 2022.11 = sas109, 2020.11 = sas108; 25.4 satırı yok [doğrulanamadı]) [okundu] oosaintegration.
- sunucu otomasyonu sertifikası akış otomasyonu Studio, akış otomasyonu Central ve akış otomasyonu RAS'ın truststore'una keytool ile içe aktarılır (ADM işlemleri için gerekli) [okundu] oosaintegration.
- Entegrasyon kullanım senaryoları: sağlama, yama, yazılım güncelleme ve denetim [okundu] oosaintegration.

## Doğrulanamayanlar

1. **sunucu otomasyonu 25.4 Core ve Agent için resmi RAM ve CPU minimumu.** Yalnız veritabanı için öneri (32 GB, 12 CPU) ve slice için 24 GB/8 CPU var. Bu dizüstünde sunucu otomasyonu'nın gerçekten çalışıp çalışmayacağı belirsiz.
2. **sunucu otomasyonu ve akış otomasyonu için desteklenen tam sürüm listeleri.** sunucu otomasyonu'nın Oracle/PostgreSQL ve Agent platform listeleri ile RHEL/SUSE sürümleri, "sunucu otomasyonu Support and Compatibility Matrix" adlı harici belgede; bu belge açılmadı. akış otomasyonu'nun Java gereksinimi de destek matrisinde yok.
3. **İndirme dosya adları ve boyutları (SLD).** akış otomasyonu ZIP adı belgede var; sunucu otomasyonu medyası adları ("sunucu otomasyonu Product Software", "Agent and Utilities") yalnız belgeden çıkarıldı; SLD'deki gerçek dosya adları, boyutları ve sürüm numarası kullanıcı tarafından portalda kontrol edilmeli.
4. **akış otomasyonu RabbitMQ gereksinimi.** Kurulum belgeleri birbiriyle çelişiyor: installcentral RabbitMQ'yu yalnız RPA için diyor, cleaninstallation akış otomasyonu Central'ın önkoşulları arasında gösteriyor.
5. **akış otomasyonu Central sessiz kurulum parametreleri (alt bölüm).** Ana silent sayfası okundu ama Central'a özgü anahtar listesi okunmadı; ZIP içindeki sample dosyası kullanılmalı.
6. **sunucu otomasyonu 25.4 ve akış otomasyonu 26.4 için bir sanal makinede yönetici yetkisi ve Windows Home sınırlamaları.** Windows 11 Home'da Hyper-V yok; VirtualBox veya VMware gerekir; bu, kurulum ön koşulu olarak belgede yazmıyor.
7. **sunucu otomasyonu "tek sunucu" core kurulumu için resmi donanım.** Belgede yalnız disk gereksinimleri var; RAM ve CPU eksik.
8. **akış otomasyonu CSRF koruma sayfası ve akış komut aracı komut satırı.** Sayfalar bulunamadı ya da okunamadı.
9. **akış otomasyonu kurulum sonrası ilk giriş adresi.** Yalnız sağlık denetim adresi okundu (`/oo/hello.html`); ana giriş sayfasının adı ve yönlendirmesi okunmadı; genel olarak `https://<host>:8443/oo` varsayımı belgede doğrulanmadı.
10. **sunucu otomasyonu Agent (yönetilen sunucu) konteyner desteği.** Belgede bu konuda bilgi bulunamadı [doğrulanamadı]; tam VM varsayımıyla ilerlenmeli.
11. **Veri ve olay sınırları (deneme ürünün kapsamı).** akış otomasyonu deneme 61 gün ve 2 eşzamanlı akış; sunucu otomasyonu InstantOn 60 gün. Kullanım kısıtları (örneğin ticari kullanım, kıyaslama) okunmadı.
