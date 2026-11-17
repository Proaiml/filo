# OpenText akış otomasyonu 26.4: içerik ve sorunlar envanteri

Kaynak: https://docs.microfocus.com/doc/397/26.4/home (İçindekiler: tocflat.json ve toctree.json; sayfa gövdeleri /397/26.4/<slug>/default-<revizyon>.json).
Okuma tarihi: 2026-11-17. Sayfalar İngilizce, açıklamalar Türkçe özetlenmiştir.

## Okuma durumu

- Okunan sayfa gövdesi: 184
  - Integrate: 1 (sayfa yalnızca "Integration Central" bağlantısı veriyor)
  - Studio/Designer kalan alt konular: 48
  - Sürüm notları (Release notes): 5
  - Sorun giderme (Troubleshoot): 130
- Ek okunan kaynak: Integration Central ürün matrisi (https://docs.microfocus.com/integration/Operations_Orchestration/all). Bu bir istemci tarafı uygulama; yalnızca 41 ürün adı döndürüyor, ürün başına bağlantı yok.
- Okunmayanlar:
  - Studio/Designer'da bu envanterin kapsamı dışında kalan kullanım sayfaları: studioauthoring, navigatingoostudio, setupdesignerproject, useexternalcloudslangfiles, objectidentificationdesigner, generatecontentrestapi, ooshcontentmanagement, ooshsystemconfiguration, flowauthoringcs, bestpracticescontent, deprecation, configurecpimportsize, useoodesigner, systeminformationsettings, systemnotifications, signingoocontent, verifyingintegrity, minimizerisk, testtroubleshootcp, setupconfigitems (yalnızca başlığı okundu), deploymanagecp (yalnızca başlık özeti okundu).
  - Integrate bölümünün Base content, SSH, PowerShell/WinRM, e-posta, dosya/FTP/SFTP, veritabanı, HTTP/REST, JSON/XML, tarih/metin, Active Directory, sunucu otomasyonu, SMAX gibi paket sayfaları: bu doküman setinde yok (bkz. Bölüm A).
  - Fixed issues sayfasının çıkarılan metni tek kayıt döndürdü (OCTCR19XW2938032). Sayfanın devamı doğrulanmadı.
- Sorun giderme ve sürüm notu sayfalarında "Cause/Solution" bölümlerinin tamamı değil, her sayfanın ilk ~2500 karakteri okundu. Ayrıntılı adımlar için ilgili sayfaya bakılmalı.

---

## Bölüm A: Integrate

Integrate sayfasının metni: "akış otomasyonu, birden fazla ürünle entegre olur. akış otomasyonu entegrasyon matrisi için Integration Central'a bakın." Yani doküman setinde paket bazlı operasyon listesi yok. Aşağıdaki tablo Integration Central'daki ürün adlarını gösterir.

Kullanıcının listesindeki paketlerden kontrol sonucu:
- Bulunan (matriste ürün adı olarak): vSphere/vCenter, Hyper-V, SCVMM, KVM, Nutanix Prism, AWS, Azure, Google Cloud, OCI, ServiceNow, Service Manager, Service Management, Zabbix, AI Operations Management (Containerized), Network Automation, NNM, Infoblox, F5 BigIP, SAP LaMa, SAP S/4 HANA, PostgreSQL, Oracle Database Server, Oracle Cloud Databases, Universal Discovery and CMDB, Data Center Automation, Veritas NetBackup, Docker, Kubernetes, Terraform, CyberArk, Microsoft 365, Efficient IP DDI, OpenNetAdmin, Operations Manager, Network Operations Management, Citrix XenServer, Alibaba Cloud, Foreman, ABBYY Cloud OCR, Cloud Management.
- Bulunamayan (bu doküman setinde ad olarak yok): Base content, SSH, PowerShell/WinRM, e-posta, dosya/FTP/SFTP, veritabanı (genel), HTTP/REST (genel), JSON/XML, tarih/metin yardımcıları, Active Directory, sunucu otomasyonu, SMAX.
- Ön koşul ve operasyon ayrıntısı: bu doküman setinde yok. Her paket için operasyon ailesi, ön koşul ve kullanım bilgisi Integration Central ürün sayfalarında olabilir; bu sayfalar istemci tarafı yüklendiği için bu oturumda açılamadı.

| ozellik | ne_yapar | admin_isi | kaynak | agirlik (tahmin) |
|---|---|---|---|---|
| Integrate (ana sayfa) | akış otomasyonu'nun entegre olduğu ürünlerin genel tanımı; ayrıntı Integration Central'da | Entegrasyon matrisini kontrol et | https://docs.microfocus.com/doc/397/26.4/integrate | sık |
| Integration Central matrisi | 41 ürün adı listeler (aşağıdaki satırlar) | Hedef ürün sürümünü ve paketini matristen doğrula | https://docs.microfocus.com/integration/Operations_Orchestration/all | sık |
| VMware vCenter / vmWare vSphere | Sanal makine (VM) yaşam döngüsü için entegrasyon (ürün adı) | Ayrıntılı operasyon listesi bu dokümanda yok | https://docs.microfocus.com/integration/Operations_Orchestration/all | sık |
| Microsoft Hyper-V | Sanal makine entegrasyonu (ürün adı) | Matristen doğrula | (aynı) | sık |
| Microsoft SCVMM | Sanal makine yönetimi (ürün adı) | Matristen doğrula | (aynı) | seyrek |
| KVM | Sanal makine entegrasyonu (ürün adı) | Matristen doğrula | (aynı) | seyrek |
| Nutanix Prism | Hiper-yakınsık altyapı (ürün adı) | Matristen doğrula | (aynı) | seyrek |
| Citrix XenServer | Sanal makine entegrasyonu (ürün adı) | Matristen doğrula | (aynı) | niş |
| Amazon AWS | Bulut kaynak yönetimi (ürün adı) | Matristen doğrula | (aynı) | sık |
| Microsoft Azure | Bulut kaynak yönetimi (ürün adı) | Matristen doğrula | (aynı) | sık |
| Google Cloud | Bulut kaynak yönetimi (ürün adı) | Matristen doğrula | (aynı) | seyrek |
| Oracle Cloud Infrastructure | Bulut kaynak yönetimi (ürün adı) | Matristen doğrula | (aynı) | seyrek |
| Oracle Cloud Databases | Bulut veritabanı (ürün adı) | Matristen doğrula | (aynı) | niş |
| Alibaba Cloud | Bulut kaynak yönetimi (ürün adı) | Matristen doğrula | (aynı) | niş |
| Cloud Management | Bulut yönetimi (ürün adı) | Matristen doğrula | (aynı) | seyrek |
| ServiceNow | ITSM (bilet) entegrasyonu (ürün adı) | Matristen doğrula | (aynı) | sık |
| Service Manager | ITSM (bilet) entegrasyonu (ürün adı) | Matristen doğrula | (aynı) | sık |
| Service Management (SMAX) | ITSM entegrasyonu (ürün adı; matriste "Service Management") | Matristen doğrula | (aynı) | sık |
| Network Automation | Ağ cihazı otomasyonu (ürün adı) | Matristen doğrula | (aynı) | sık |
| Network Node Manager (NNM) | Ağ izleme/keşif (ürün adı) | Matristen doğrula | (aynı) | sık |
| Network Operations Management | Ağ olay yönetimi (ürün adı) | Matristen doğrula | (aynı) | seyrek |
| Infoblox | DNS/IP yönetimi (ürün adı) | Matristen doğrula | (aynı) | sık |
| Efficient IP DDI | DNS/DHCP/IP yönetimi (ürün adı) | Matristen doğrula | (aynı) | seyrek |
| OpenNetAdmin | IP/DNS envanteri (ürün adı) | Matristen doğrula | (aynı) | niş |
| F5 BigIP | Yük dengeleyici (ürün adı) | Matristen doğrula | (aynı) | sık |
| Zabbix | İzleme (ürün adı) | Matristen doğrula | (aynı) | sık |
| Operations Manager | Olay/izleme (ürün adı) | Matristen doğrula | (aynı) | seyrek |
| AI Operations Management - Containerized | AIOps izleme (ürün adı) | Matristen doğrula | (aynı) | seyrek |
| Universal Discovery and CMDB | CMDB/keşif (ürün adı) | Matristen doğrula | (aynı) | sık |
| Data Center Automation | Veri merkezi otomasyonu (ürün adı) | Matristen doğrula | (aynı) | seyrek |
| SAP Landscape Management | SAP sistem yönetimi (ürün adı) | Matristen doğrula | (aynı) | niş |
| SAP S/4 HANA | SAP ERP (ürün adı) | Matristen doğrula | (aynı) | niş |
| PostgreSQL | Veritabanı (ürün adı; akış otomasyonu'nun kendi DB'si için de kullanılır) | Sürüm desteği 26.4'te PostgreSQL 14 düşürüldü, 18 eklendi | https://docs.microfocus.com/doc/397/26.4/releasenotes | sık |
| Oracle Database Server | Veritabanı (ürün adı) | Matristen doğrula | (aynı) | seyrek |
| Veritas NetBackup | Yedekleme (ürün adı) | Matristen doğrula | (aynı) | niş |
| Docker | Konteyner (ürün adı) | Matristen doğrula | (aynı) | seyrek |
| Kubernetes | Konteyner orkestrasyonu (ürün adı) | Matristen doğrula | (aynı) | seyrek |
| HashiCorp Terraform | IaC (ürün adı) | Matristen doğrula | (aynı) | seyrek |
| CyberArk | Parola/erişim kasası (ürün adı) | Matristen doğrula | (aynı) | seyrek |
| Microsoft 365 | Bulut ofis (ürün adı) | Matristen doğrula | (aynı) | seyrek |
| Foreman | Sunucu yaşam döngüsü (ürün adı) | Matristen doğrula | (aynı) | niş |
| ABBYY Cloud OCR | OCR servisi (ürün adı) | Matristen doğrula | (aynı) | niş |

---

## Bölüm B: Studio/Designer kalan alt konular

Okunan 48 sayfa beş gruba ayrıldı. Kaynak adresleri https://docs.microfocus.com/doc/397/26.4/<slug> biçimindedir.

### B1. Sistem hesapları ve sistem özellikleri (akışta kullanım)

| ozellik | ne_yapar | admin_isi | kaynak | agirlik (tahmin) |
|---|---|---|---|---|
| System accounts (sistem hesapları) | Kullanıcı adı ve parolayı Configuration\System Accounts altında saklar; akış girdisi olarak kullanılır, kullanıcı adı son kullanıcıya görünmez. Hesap sadece Studio'da tanımlanır; çalışma zamanı için ayrıca API ile kurulmalı. | Hesap oluştur, kopyala, düzenle, sil; content pack silinince hesap da gider | configuresystemaccount | sık |
| System properties (sistem özellikleri) | Değeri değişmeyen global değişkenler; her akışta kullanılabilir. Akış değişkeni aynı ada sahipse akış değişkeni önceliklidir. | Global kapsam nedeniyle değiştirirken dikkatli ol; çalışan akışları bozabilir | configuresystemproperty | sık |
| Author system properties | Sistem özelliklerini dosya yapısında (Configuration\System Properties) tanımlama; isim kuralları (128 karakter, a-z, 0-9, _, -) | Dosya/klasör isimlerini kurala uygun seç | authorsystemproperties | sık |
| System filters (sistem filtreleri) | Operasyon çıktısını ya da adım sonucunu süzmek için yeniden kullanılabilir filtre; Quick Command ile test edilir | Filtreyi kaydet ve Input Editor'da Validation Format olarak kullan | configuresystemfilter | orta |
| System evaluators (sistem değerlendiricileri) | Girdi doğrulama formatı (e-posta, sayı aralığı, regex, scriptlet); sistem hesapları dışındaki veri kaynaklarında kullanılır | Silmeden önce "What Uses This" ile bağımlılık kontrol et | configureevaluator | orta |
| Out-of-the-box underlying variables | CloudSlang akışlarında çalışma kimliği, kullanıcı kimliği ve worker grubu değişkenlerini döndüren fonksiyonlar (get_run_id(), get_user_id(), get_worker_group()) | Akış tasarımında kullan; çalışma zamanında Central'dan okunur | useunderlyingvariables | seyrek |

### B2. AFL (Advanced Flow Language) içeriği

| ozellik | ne_yapar | admin_isi | kaynak | agirlik (tahmin) |
|---|---|---|---|---|
| AFL içerik geliştirme | AFL içerik üretimi için Java 1.8, Maven 3.2.1; .NET aksiyonları için .NET 4.0; plugin (JAR, Maven) tabanlı, sınıf yolu izoleli | Geliştirici ortamı ve Maven kurulumu gerekir | aflcontentdevelopment | seyrek |
| Author AFL in Workflow Designer | Designer'da AFL projelerini Dependencies panelinde görüntüler; GRAPH ve PROPERTIES sekmeleri | Studio'da yazılmış AFL akışlarını Designer'da incele | authoraflprojectswfd | sık |
| View AFL flows in Workflow Designer | AFL akışlarını salt okunur gösterir; debugging AFL için desteklenmez | Yalnız görüntüleme | viewaflflowswfd | orta |
| Edit AFL flows in Workflow Designer | Beta özellik; kopyala/yapıştır, geçiş ekleme/silme, akış özellikleri düzenleme. AFL için debug yok. | Beta uyarısı var; üretimde dikkat | editaflflowswfd | seyrek |
| Step details in AFL flows (Step Inspector) | Adım girdi, sonuç, görüntü (prompt), açıklama, gelişmiş (Step Persistence, Rerun point, Throttle) ayarları | Adım yürütme davranışını ayarla | stepinspectorwkfdesigner | orta |
| AFL multi-instance steps | Bir liste üzerinde paralel "lane" çalıştırır (örn. 100 sunucuda aynı flow); hata veren lane durur, diğerleri sürer; throttle ile eşzamanlılık sınırlanır | Hedef listesini ve throttle değerini ayarla | aflmiedit | sık |

### B3. Kaynak denetimi (SCM)

| ozellik | ne_yapar | admin_isi | kaynak | agirlik (tahmin) |
|---|---|---|---|---|
| SCM genel kurulum | Merkezi depo üzerinden proje yönetimi; Studio'da SVN veya Git seçilir (aynı anda biri); bir workspace'e bir depo bağlanır | Depo türünü seç; belirsizse sistem yöneticisine danış | scmsetup | sık |
| Work with SCM in Studio | SCM > Connection menüsünden tür ve depo URL'si; Git'te Clone/Detach | Bağlantı ayarını yap | workingsourcecontrol | sık |
| Subversion işlemleri | Checkout, Commit, Add, Delete, Update; yerel çalışma kopyası | Commit öncesi update; kilit yönetimi | workingsvn | orta |
| Git işlemleri | Clone, Add, Commit, Pull, Push, Fetch; yerel repo üzerinde çalışır | Pull'u günde bir kez yap | workinggit | orta |
| Filesystem protocol in SCM (Designer) | 2022.11'de kaldırıldı (Designer'da dosya sistemi protokolü desteklenmez) | Eski kurulumlarda SCM URL'sini güncelle | https://docs.microfocus.com/doc/397/26.4/deprecations | niş |

### B4. İçerik paketi içe aktarma ve yönetimi

| ozellik | ne_yapar | admin_isi | kaynak | agirlik (tahmin) |
|---|---|---|---|---|
| Content packs (genel) | Akış, operasyon, configuration item ve kaynak paketi; ITOM Marketplace'ten indirilir veya Designer/Studio ile üretilir | Paket kaynağını doğrula | contentpacks | sık |
| Import content packs to a project in Studio | Kurulumda seçilebilir; ilk açılışta yüklenir. Önce Base Content Pack, sonra gerekli paketler içe aktarılır | Base paketi önce içe aktar | importingcontentpacks | çekirdek |
| Manage content packs and dependencies | İçe aktarılan operasyonlar salt okunur; değiştirmek için projeye kopyalanır (kopya ayrılır) | Kopya ayrımını not et | managingcontentpacks | sık |
| Export a content pack in Studio | Proje, içerik paketi olarak dışa aktarılır; geçersiz akış ya da çift UUID olan öğeler dahil edilmez | Dışa aktarma öncesi Problems paneli temiz olmalı | creatingcontentpack | sık |
| Import content packs to Dependencies (Designer) | Designer'da CloudSlang ve AFL paketleri içe aktarılır; önce base paket | Base paketi önce ekle | designerdependenciespane | sık |
| Create and deploy a content pack (Designer) | Projeyi kaydet, doğrula, içerik paketi olarak dışa aktar, dağıt | Dağıtım öncesi akışları doğrula | designercreatedeploycp | sık |
| Content pack versioning | X.Y.Z[-SNAPSHOT]; major (kırıcı değişiklik), minor (yeni akış/operasyon), micro (hata düzeltme) | Sürüm numarasını kurala göre artır | contentpackversioning | sık |
| Deploy content packs with progress (API) | Deployment oluştur, dosya yükle, çalıştır; RUNNING/FINISHED durumu API ile izlenir | Otomasyonda API çağrı sırası önemli | deploycontentpacks | seyrek |
| Delete a content pack from a deployment process (API) | DELETE /deployments/{id}/files/{fileId}; 403 ise "Manage Content Packs" izni yok | Yetki kontrolü | deletedeploymentcp | seyrek |
| Add content pack files for deleting (API) | POST /deployments/{id}/cpsForDelete ile silinecek paketleri işaretler | Silme sırasını planla | addingcontentpackfiles | seyrek |
| Promote content packs | Op Admin paketleri ortamlar arasında taşır (Dev, Test, Prod) | Taşıma sırası: önce base paket, sonra diğerleri | promotecp | sık |
| Deploy and manage content packs (Central) | Central'ın Content Packs sekmesinden dağıtım; base paket ve Studio'nun kullandığı paketler önce | Dağıtım en az iki kez yapılır | deploymanagecp | sık |
| Set up configuration items for a content pack | Dağıtımdan sonra sistem hesapları ve diğer öğeler ortama göre ayarlanır (örn. Oracle hesapları) | Ortam değerlerini gir | setupconfigitems | sık |
| Configure content pack import size | Studio'da içe aktarılabilecek paket boyutu limiti | Büyük paketlerde heap/limit ayarı | configurecpimportsize | seyrek |

### B5. Operasyon türleri ve Studio araçları

| ozellik | ne_yapar | admin_isi | kaynak | agirlik (tahmin) |
|---|---|---|---|---|
| Operations in Studio (tasarım önerileri) | Operasyon tasarımı: mevcut hazır operasyonları yeniden kullan, aynı komutu çalıştıran çift operasyon yazma, standart çıktı, anlamlı hata mesajları | Yeni operasyon yerine mevcut operasyonu kullan | operations | sık |
| Validate content (Problems, Debugger) | Problems paneli ve Debugger ile hataları bulma | Yayından önce doğrula | debuggingflows | sık |
| Debug flows from Studio in a remote Central | Central'daki akış çalışmalarını Studio'dan uzaktan debug; Central URL tanımı | Uzak debug için Central bağlantısı | debuggingcentralstudio | orta |
| Third party content pack wizard | Eksik üçüncü taraf jar'ları içeren content pack üretir (third-party-cp-wizard.bat) | Wizard ile jar paketini üret | thirdpartywizardintro | niş |
| Third party wizard steps | Kütüphane seçimi XML dosyası ile yapılır | XML tanımını hazırla | thirdpartywizardsteps | niş |
| Third party wizard command line | java -jar ... --help ile komut satırı kullanımı | Otomasyon için komut satırı | thirdpartywizardcommandline | niş |
| Third party wizard troubleshooting | Sorun giderme sayfası (içerik sayfası okunmadı) | Sorun durumunda bak | thirdpartywizardtroubleshooting | niş |
| REST wizard (generated flows) | REST çağrılarından akış üretir; akış Studio'da proje olarak içe aktarılır; System Properties içindeki Service_Url güncellenmeli | Service_Url değerini hedef adrese göre düzelt | restwizardimportflows | sık |
| Shell wizard (generated flows) | Kabuk komutlarından akış üretir; Shell operasyonu girdileri ile aynı | Üretilen projeyi içe aktar | shellwizardimport | orta |
| akış yönetim aracı komut satırı | Studio'nun komutlarını CLI'dan çalıştırır (otomasyon için) | Otomasyon için CI betiği | oosha | seyrek |
| akış yönetim aracı createCP | Studio ya da CloudSlang projesinden içerik paketi üretir; yapısal ve tutarlılık kontrolleri | Üretim betiğinde kullan | ooshapackaging | seyrek |
| akış yönetim aracı scan | Proje ya da içerik paketini en iyi uygulamalara göre tarar | Yayın öncesi tarama | ooshascancp | seyrek |
| Localize akış otomasyonu Studio | Fransızca, Almanca, Japonca, İspanyolca, Çince; açıklama ve prompt metinleri yerelleşir | Dil kodunu ayarla | workingdifferentlanguages | seyrek |
| Get started with akış otomasyonu Studio | Proje oluştur, SCM kur, içerik paketi içe aktar, akış yaz, doğrula, dışa aktar | Başlangıç sırası | studiomajorsteps | sık |
| Visual overview of akış otomasyonu Studio | Projects paneli, Dependencies paneli, Authoring alanı ve diğer ekran öğeleri | Arayüz referansı | studioscreenelements | sık |
| Configure Studio properties | studio.properties (çalışma alanı başına) ve Options iletişim kutusu | Heap (-Xmx) ve dil ayarları | studioproperties | orta |
| Flow authoring using akış otomasyonu Studio | Modüler akış tasarımı, tek amaçlı akışlar, anlamlı isimler | Alt akış kullan | flowauthoring | sık |
| Work with CloudSlang content flows | CloudSlang 1.0 ve 2.0 içerikleri dağıtılıp çalıştırılabilir; motor hafif Java JAR | Eski CloudSlang içeriği için sürüm kontrolü | cloudslangcontentflows | seyrek |

---

## Bölüm C: Sorun giderme (Troubleshoot) ve sürüm notları

### C0. Sürüm notları (Release notes)

| ozellik | ne_yapar | admin_isi | kaynak | agirlik (tahmin) |
|---|---|---|---|---|
| 26.4 yenilikleri | Tomcat 11.0.26, Java 17.0.20.1, Spring Boot 4.0.8, Spring Framework 7.0.9, Python 3.14.7, PG JDBC 4.7.12; PostgreSQL 18 desteği eklendi; RHEL 9.8 desteği eklendi; PostgreSQL 14 desteği bırakıldı | Yükseltme öncesi destek matrisini kontrol et | https://docs.microfocus.com/doc/397/26.4/releasenotes | çekirdek |
| Enhancements (26.4) | Multi-Instance Recovery iyileştirmesi: çift branch birleştirmesini önler, recovery mesajlarını tamamlar, bellek kullanımını azaltır | Çok lane'li akışlarda bellek düşüşünü gözle | https://docs.microfocus.com/doc/397/26.4/enhancements | sık |
| Fixed issues (26.4) | Çıkarılan metinde tek kayıt: güvenlik, Sign In banner'ı (OCTCR19XW2938032). Sayfanın tamamı doğrulanmadı | Tam listeyi sayfadan kontrol et | https://docs.microfocus.com/doc/397/26.4/fixeddefects | çekirdek |
| Deprecation and obsolescence | Kullanımdan kalkan: RPA Robot ve Recorder (26.2.1). Kaldırılanlar: PostgreSQL 14 (26.4), SLES 12 (25.4), PostgreSQL 13 (25.4), Windows 2012 ve 2012 R2 (25.2), RHEL 7.9 (24.4), CentOS 7.9 (24.1.1), PostgreSQL 11 (24.1), Oracle 18c (2023.05), SQL Server 2014 (2022.11), Designer SCM Filesystem protokolü (2022.11), Ubuntu 14.04 (2022.05), PostgreSQL 9/10 ve Oracle 12c (2022.05), MySQL (obsolete, 2022.05), akış otomasyonu 9.x'ten yükseltme (2021.02) | Kaldırılan platformları ortamdan çıkar | https://docs.microfocus.com/doc/397/26.4/deprecations | çekirdek |
| Release log | Sürüm bazlı kümülatif yenilik listesi; 26.2.1: Tomcat 11.0.22, Java 17.0.19, Spring Boot 4.0.6; 26.2: PHS (Private Help Server) mimarisi, Tomcat 10.1.54; 25.4.1: Studio'dan ITOM Marketplace araması kaldırıldı | Sürüm farklarını izle | https://docs.microfocus.com/doc/397/26.4/releaselog | sık |

### C1. Genel sorun giderme

| ozellik | ne_yapar | admin_isi | kaynak | agirlik (tahmin) |
|---|---|---|---|---|
| General troubleshooting (üst başlık) | Tüm bileşenler (Central, RAS, Designer) için genel adımlar | Sorun öncesi genel kontroller | gentroubleshoot | sık |
| Yarım kalmış yükseltme/geri alma | Yıkıcı adımlar dosyaları silip geri yüklediği için yeniden deneme hata verir | Dosya yapısını onar, yedekten başlat | failedupgrade | sık |
| Başlatma takılması: entropi havuzu (Linux) | Entropi değeri 1000'in altındaysa süreçler bloke olur | Entropi değerini kontrol et ve artır | insufficiententropypool | sık |
| Metaspace OutOfMemory (Central/RAS) | Wrapper log'da Metaspace hatası; boyut küçük | central-wrapper.conf (ya da ras-wrapper.conf) Metaspace değerini artır | oomerror | sık |
| 2020.02 Python ifadeleri | Eski Python ifadeleri yeni sürümde beklenmeyen davranır (akış otomasyonu 2021.02.P1 dahil) | İfadeleri gözden geçir | pythonexpressionsnotworking | seyrek |
| İkinci kurulum başlamıyor (RPA) | Robot ya da Recorder kurulu makinede UFT çalışırken ikinci kurulum açılmaz | UFT'yi kapat; kayıt defterindeki adımı uygula | secondrpainstallerfails | niş |
| Installer temp klasörü (Linux) | Güvenlik politikası /tmp çalıştırmayı engeller | Installer geçici klasörünü değiştir | installertempfolderlocationlinux | sık |
| Installer temp klasörü (Windows) | AppData\Local\Temp çalıştırma kısıtı | Installer geçici klasörünü değiştir | installertempfolderlocationwindows | sık |
| Python 3.12 sözdizimi | Kaçışsız özel karakterler akışı "running"de bırakır | Python ifadelerini düzelt | pythonsyntaxerror | orta |
| Localization (üst başlık) | Yerelleştirme sorunları alt başlığı | Alt konulara bak | troubleshootinglocalization | niş |
| Gibberish karakterler (MS SQL) | Veritabanı collation yanlış; UI bozuk | Collation'ı dile uygun ayarla | gibberishcharactersinui | niş |
| Japonca karakterler | Studio Filter Editor ve Quick Command Japonca karakteri işleyemez | Studio.l4j.ini'ye unicode parametresi ekle | japanesecharactersissues | niş |

### C2. Yükseltme (Upgrade) sorunları

| ozellik | ne_yapar | admin_isi | kaynak | agirlik (tahmin) |
|---|---|---|---|---|
| Upgrade (üst başlık) | Yükseltme sorunları alt konuları | Alt konulara bak | troubleshootupgrades | sık |
| Bozuk yedek (yükseltme sonrası) | 10.x yama geri alma sırasında klasör yeniden adlandırma/silme; Central, Studio, RAS başlamaz | Yedeği kontrol et; geri alma adımlarını izle | backupcorruption | seyrek |
| Explorer ikonları güncellenmiyor | Eski sürümden (2018.05 öncesi) yükseltmede OS ikon önbelleği | Önbelleği temizle | iconerror | niş |
| Tarayıcı favicon güncellenmiyor | Tarayıcı önbelleği | Önbelleği temizle | browserfavicon | niş |
| IdM admin konsolu erişilemiyor (10.80 yükseltmesi) | IdM 1.16'dan 1.17'ye şifreleme yöntemi değişti | Parolayı çözüp yeniden yapılandır | postupgradeidmissue | seyrek |
| OO_ACQUIRED_LICENSES tablosu var | HF_1206713 uygulanmış 2020.11'den 2021.02'ye yükseltmede hata | Belirtilen SQL/adımı uygula | posthotfixupgradefails | niş |
| IdM CREATE modunda yükseltme | 2018.09 ve altı Central; IdM'de aynı sürümde çift seed dosyası | Belirtilen Central adımını uygula | centralupgradefailidmcreate | seyrek |
| Geri alma sonrası yükseltme DB hatası | Geri alma script'i veritabanı yapısını silmedi | DB yapısını elle temizle | upgradeafterrollbackissue | seyrek |
| Java 8 + SAML yükseltmesi | Java 17 ile SAML kütüphaneleri değişir; metadata farklı üretilir | Yükseltmeden önce SAML'i devre dışı bırak | java8samlupgrade | seyrek |
| MaxPermSize hatası (2023.05 öncesi) | Eski JVM parametreleri Java 17'de tanınmaz | JVM parametrelerini güncelle | jvmparamsupgradeissue | sık |
| Central yapılandırma adımı hatası | central-wrapper.conf yanlış; IndexOutOfBounds | Wrapper dosyasını düzelt | cconfigchange | seyrek |

### C3. akış otomasyonu Central sorunları (39 alt konu)

| ozellik | ne_yapar | admin_isi | kaynak | agirlik (tahmin) |
|---|---|---|---|---|
| Troubleshoot akış otomasyonu Central (üst) | Central sorunları listesi | Alt konulara bak | troubleshootingcentral | sık |
| RPA Central Java 17 yükseltme hatası | Aynı sunucuda Robot/Recorder kalıntısı; EXCEPTION_UNCAUGHT_CXX_EXCEPTION | Kalıntı bileşenleri kaldır | uprdrpajava17 | niş |
| CSV özel karakter | Excel kodlamasıyla Run Log dışa aktarımı bozuk | Dışa aktarımda kodlama seç | specialcharacters | seyrek |
| SSL handshake hatası (HTTP istekleri) | Java'da SNI varsayılan açık; bazı sunucular yanlış yanıt verir | Sunucu SNI ayarını düzelt ya da Java yapılandırmasını gözden geçir | sslhandshakeerror | sık |
| Content pack plugin silinmemiş | Silinen paketteki plugin Central cache'te kalır; aynı sürüm üzerine yazmaz | Cache'i temizle; sürüm artır | pluginsnotdeleted | seyrek |
| Akış yavaşlaması zamanla | Kaynak, donanım ve DB bağlantıları | Kaynak ve DB bağlantılarını incele | slowexecution | sık |
| Firefox düşük çözünürlük | Windows'ta yazı boyutu %125 olduğunda | Yazı ölçeğini düzelt | lowresolutionff | niş |
| Content pack dağıtımı uzun sürüyor | Central için bellek yetersiz (OOM) | Central bellek değerini artır | contentdeploymentslow | sık |
| Central'dan kilitlenme (lockout) | SAML'de silinmiş admin kullanıcı ya da yanlış URL | Admin kullanıcıyı ve URL'yi doğrula | oolockout | sık |
| RC4 cipher güvenlik riski | JRE düzeyinde RC4 açık; zayıf | RC4'ü devre dışı bırak | remhostrc4 | sık |
| Group alias ve worker grubu eşlenmiyor | Akış çalışırken alias'a grup eşlemesi yapılmaya çalışılırsa | Çalışma bitince eşle; isimler aynıysa sorun yok | mapworkgroup | seyrek |
| Content deployment bitmiyor | Antivirüs tarayıcı okumalarını engelliyor | Antivirüs CPU tüketimini kontrol et, istisna ekle | contentdeploy | sık |
| Zamanlanmış çalıştırmalar tutarsız | Scheduler, Central, RAS ve istemci farklı saat dilimlerinde | Saat dilimini eşitle | inconsistentstart | sık |
| akış otomasyonu yardım bağlantıları çalışmıyor | Load balancer yapılandırması | Load balancer'ı düzelt | helplinkissue | seyrek |
| Bazı düğmeler görünmüyor | Ekran çözünürlüğü düşük | 1280x1024 ya da 1920x1080 yap | lowresolution | niş |
| Worker kaydedilemiyor | Load balancer'da sıkıştırma (compression) worker bağlantısını etkiler | Load balancer'daki sıkıştırmayı kaldır | workerregistration | sık |
| Adımlar karışık görünüyor (Tree/Table) | Oracle DB ve dil ayarı kombinasyonu | DB ve dil ayarını düzelt | scrambledview | seyrek |
| Dağıtım sırasında istisna mesajı | Birden fazla neden; sunucu logu gerekli | Sunucu logunu incele | deployexception | sık |
| Service unavailable mesajı | Sunucu kapalı, meşgul ya da ağ sorunu | Sunucu ve ağ durumunu kontrol et | serviceunavailable | sık |
| Dağıtımda çift UUID hatası | Aynı UUID başka bir akışta/operasyonda var | UUID'yi benzersiz yap | deployerror | sık |
| Dağıtımda dosya adı bozuluyor | Dosya adı bozuk durumda | Yeniden dağıt | filecorrupted | seyrek |
| İzin yok hatası | Kullanıcının ilgili izni yok | Rol ve izinleri kontrol et | nopermission | sık |
| Existing IDM ile kurulumda NPE | RAS'ı Central API'ye kaydetmek için kimlik bilgisi eksik | Kimlik bilgilerini sağla | npeooexistingidm | seyrek |
| Adım sırası karışık (çalıştırılmış) | Oracle DB ve dil ayarı; Run Report da karışık | DB ve dil ayarını düzelt | scrambledviewsteps | seyrek |
| Windows 2016'da dağıtım donuyor | İlk dağıtım yüklemeden sonra asılı kalıyor | Sayfayı yenileyip tekrar dene | win2016cpdeployissue | seyrek |
| Genel sunucu hatası | Sunucudan beklenmeyen hata durumu | Sunucu logunu incele | unexperror | sık |
| Liquibase: changelog lock bekleniyor | Birkaç denemeden sonra sunucu başlamıyor; changelog kilidi bozuk | Changelog lock kaydını düzelt | errormsg | sık |
| Internal server error | Beklenmeyen sunucu hatası | Sunucu logunu incele | serverror | sık |
| Akış tetiklenemiyor | Varsayılan gruptaki worker atanmamış | Worker grubunu kontrol et | flowlaunch | sık |
| akış otomasyonu Central'a erişilemiyor | IdM admin parola sıfırlaması senkron değil | IdM parolasını senkronize et | resetpwaccessissue | sık |
| Central/RAS OOM ile çöküyor | Heap küçük | Heap boyutunu artır | oofails | sık |
| RabbitMQ servisi kaldırılmıyor | Kaldırıcı RabbitMQ servisini silmiyor (Windows 2019) | Servisi elle kaldır | unabletoremoverabbitmq | seyrek |
| Erlang uyumsuz | Erlang elle ya da kaldırıcıyla silindi; yeniden kurulum hata veriyor | Uyumlu Erlang'ı kur | erlangnotcompatible | seyrek |
| SAML ile yönetim portalına giriş yok | SAML ayarı yanlış | IdM girişine geri dön (sorgularla) | incorrectsamlsetup | seyrek |
| Multi-instance akış RUNNING'de takılı | Tüm lane'ler başarılı; suspendedExecutionCleanerJob ilerlemeyi engelliyor | Cleaner job'ı kontrol et | miflowsstuck | sık |
| Akışlar "Pause - No Workers in Group" | Worker'lar Central'ın gönderdiği tüm akış/adımları işleyemiyor | Worker kapasitesini artır, grubu kontrol et | workerrecovery | sık |
| Flow library donuyor (Central IDM) | Özel kullanıcı promoter'ı yalnız kısıtlı yetkiye sahip | Yetkileri gözden geçir, sayfayı yenile | centralidmmodeissue | seyrek |
| Websocket ve long polling geçişi | Performans veya politika nedeniyle yöntem değiştirilir | Drilldown yöntemini long polling yap | websocketlongpolling | seyrek |
| RPA Central 25.2 yükseltmesi | DeleteClassicQueuesForQuorum252 veri görevi hata verir (eksik özellik) | Belirtilen ayarı ekle | rpacentralerror | niş |
| Cluster yükseltme şifreleme | 25.4 öncesi yükseltme --norestart olmadan şifreleme hataları | Yükseltme komutunu doğru seçenekle çalıştır | clusterencryptionissues | seyrek |

### C4. RPA Robot sorunları

| ozellik | ne_yapar | admin_isi | kaynak | agirlik (tahmin) |
|---|---|---|---|---|
| Troubleshoot akış otomasyonu RPA Robot (üst) | Robot sorunları listesi | Alt konulara bak | robottroubleshooting | sık |
| Paused - No Robots in Group | Akış adımı için grupta uygun robot yok | Robot grubuna robot ekle | norobots | sık |
| Robot aynı akışı kendiliğinden yeniden çalıştırıyor | Central akışı bitirdikten sonra tetiklenmeden tekrar çalıştırma | Tetikleyici ve yeniden çalıştırma ayarlarını gözden geçir | incorrectsecondexecutionactivity | seyrek |
| RPA aktivitesi çalışmaya devam etmiyor | Sık çalıştırmada UFT çökmesi | UFT'yi yeniden başlat, sürüm kontrolü | uftcrashfailsactivityrun | sık |
| Robot RDP oturumunda çalışmıyor | RDP oturumu aktif değil | Oturumu aktif tut | robotrdp | sık |
| Pending Robot | Uygun robot yok ya da robotlar meşgul | Robot kapasitesini kontrol et | pendingrobot | sık |
| Insights verisi yüklenmiyor | Yükseltme sonrası ROI verisi görünmüyor | Insights loglarını kontrol et | insightsdataupgradeissue | seyrek |

### C5. Studio sorunları

| ozellik | ne_yapar | admin_isi | kaynak | agirlik (tahmin) |
|---|---|---|---|---|
| Troubleshoot akış otomasyonu Studio (üst) | Studio sorunları listesi | Alt konulara bak | troubleshootingstudio | sık |
| Yüksek DPI'da küçük yazı/ikon | Otomatik ölçekleme sorunu | Kısayol özelliklerinde DPI ayarını düzelt | oostudiohighdpi | seyrek |
| Yükseltme sonrası uzak debugger sertifika parolası | Parolalar düz metin olarak görünüyor | Sertifika parolasını koru | remotecertissue | seyrek |
| Çok proje içe aktarırken GC overhead | Heap küçük | Studio.l4j.ini heap değerini artır | multiprojectimporterror | seyrek |
| Büyük XML dosyalarında düzenleme hatası | Heap küçük | Studio.l4j.ini -Xmx değerini artır | editxmloperationfailure | seyrek |
| Debugger akışları Central Run'da görünmüyor | Kimlik doğrulamalı Central; prompt'suz akışlar | Central Run yapılandırmasını kontrol et | debuggerflowsnotvisible | seyrek |
| Çok fazla paket içe aktarınca yavaşlık | Heap düşük; paketler silindikten sonra | Heap'i artır | importcpoomerror | seyrek |
| Tutarsız content pack | 10.02 ve öncesi SDK ile üretim | Güncel sürüm ile yeniden üret | inconsistentcp | niş |
| Kütüphede yeni üst klasör seçilemiyor | Klasör yapısı izin vermiyor | Klasörü farklı yolla taşı | parentfoldererror | niş |
| SCM klasörü commit edilemiyor (kilit) | Klasör çok taşınıp geri getirildi | Doğrulama adımlarını tekrar et | commitfoldererror | seyrek |
| Multi-author proje tutarsız | Kilitleme sırasında "Update Item and Perform Lock Action" seçimi | Projeyi yenile | projectinconsistentstate | seyrek |
| Çift UUID doğrulaması takılı | SVN/Git ile çalışırken | Projeyi yenile | validationfailureduplicateuuid | seyrek |
| SCM Messages paneli hataları | Studio/SlikSVN klasörü yeniden adlandırıldı ya da silindi; SCM URL yok | URL'yi yapılandır, klasörü geri koy | scmerror | sık |
| Boş Git deposuna bağlanılamıyor | Clone başarılı ama diğer işlemler çalışmıyor, bildirim yok | Depo içeriğini hazırla | emptygitrepoissue | seyrek |
| Git merge hatası (paralel lane) | Paralel lane içeren akış çakışınca | Manuel birleştir | gitmergeoperationissue | seyrek |
| Git: "system cannot find the file" | Studio\Git\bin\git yolu bulunamıyor | Git yolunu doğrula | gitoperationerror | sık |
| SVN güncellemesi başkalarının değişikliğini silmiş | Aynı akış iki kullanıcıda düzenlendi | Güncellemeden önce koordinasyon yap | svnprojectupdateissues | seyrek |
| Studio açılmıyor (Windows 7/2008) | Eksik DLL'ler | DLL'leri kur | missingdlls | niş |
| Ağ paylaşımındaki SVN yavaş | file:/// ile paylaşılan SVN işlemleri yavaş | Sunucu tabanlı SVN'e geç | scmoperationissue | seyrek |
| SCM'den ayrılamıyor (detach) | Kilitli öğeler ve erişilemeyen SCM | .svn klasörünü sil | scmdetachissue | seyrek |
| Studio ikonu eski logoyu gösteriyor | Eski sürümden yükseltme | Yeniden kur ya da önbellek temizle | studiowithnobrandlogo | niş |
| Commit sonrası öğe kilitli görünüyor | Editör durumu güncellenmiyor | Öğeyi yeniden aç | scmlockeditem | seyrek |
| Git update sonrası projeler yenilenmiyor | Yeni Git güvenli dizin kavramı | Dizini güvenli olarak işaretle | scmupdaterefreshissue | seyrek |
| Java 17'den geri alma sonrası proje açılmıyor | Kütüphane iç ID'leri değişti | Proje dosyalarını yeniden içe aktar | studioimportjava17issue | niş |

### C6. akış otomasyonu Workflow Designer sorunları

| ozellik | ne_yapar | admin_isi | kaynak | agirlik (tahmin) |
|---|---|---|---|---|
| Troubleshoot akış otomasyonu Workflow Designer (üst) | Designer sorunları listesi | Alt konulara bak | workflowdesignertroubleshooting | sık |
| .NET operasyonları Linux'ta | Designer Linux'ta .NET özelliklerini tam göstermiyor | Yapılandırmayı gözden geçir | dotnetissuedesignerlinux | seyrek |
| Oracle Linux'ta Designer erişim hatası | IdM Create modunda IP ile çözümleme hostname yerine | Hostname çözümlemesini düzelt | designererrorolaccess | seyrek |
| Run düğmesi devre dışı | Uzak debug sonrası debugger küçültülürse | Debugger penceresini geri getir | runbuttondisabled | seyrek |
| SAP kullanıcı oluştururken parola yıldızlı | Kaydedilmiş aktivite yeniden kullanılıyor | Parola adımını düzelt | passwordissue | seyrek |
| Windows uygulaması kaydı çift örnek açıyor | Çocuk süreç akış otomasyonu tarafından izlenemiyor | Record and Run ayarını gözden geçir | doubleinstancerunning | seyrek |
| Proje ağacı boş (sunucu yeniden başlatıldı) | DB ile Designer aynı sunucuda | Ayrı sunucu ya da servis sırası | designerprojecttreemissing | seyrek |
| Paralel döngüde breakpoint çalışmıyor | Kaldırılan breakpoint hâlâ aktif | Breakpoint'i yeniden ayarla | bponloopnotworking | niş |
| LDAP kullanıcısı IdM konsoluna giremiyor | Grup ayarında Association eksik | Grup ilişkisini ekle | idmldapuserissue | seyrek |
| IdM özelliği değiştirilemiyor | Bazı kurulumlarda rastgele hata | IdM ayarını yeniden dene | modifyidmproperror | seyrek |
| Firefox'ta akış grafiği zoom'u | Tree View'da okunmaz metin | Tarayıcı değiştir | lowresolutionffdesigner | niş |
| Paralel adım seçimi kenarda çalışmıyor | Canvas kenarındaki adımlar | Canvas'ı kaydır | dragselectparallelsteps | niş |
| Prompt girdileri dizi olarak görünüyor | Python ifadeleri liste gibi değerlendiriliyor | Girdi ifadesini düzelt | promptuserinputsissue | seyrek |
| Uzun açıklama akışı geçersiz kılıyor (>1600 karakter) | AFL açıklaması yapıştırılıp hemen kaydedilince | Açıklamayı kısalt | longdescriptionssaveissue | seyrek |
| Debugger plugin indiremiyor | Plugin indirme hatası | Ağ/proxy ayarını kontrol et | plugindownloadfailure | seyrek |
| Azure'da barındırılan Git bağlantısı | Azure Git bağlantısı | Erişim/kimlik bilgilerini kontrol et | gitrepazureissue | seyrek |

### C7. RPA Recorder sorunları

| ozellik | ne_yapar | admin_isi | kaynak | agirlik (tahmin) |
|---|---|---|---|---|
| Troubleshoot akış otomasyonu RPA Recorder (üst) | Recorder sorunları listesi | Alt konulara bak | troubleshootingoorecorder | seyrek |
| Yeni kullanıcı kayıt başlatamıyor | Designer kullanıcısı için kayıt yetkisi/kurulum | Kullanıcı kayıt ayarlarını kontrol et | diffusercantrec | seyrek |
| Ekran olaylarını yakalamıyor | Recorder ekran olaylarını yakalayamıyor | Recorder'ı yeniden başlat | recordernotworking | seyrek |
| Beklenmeyen hata | Recorder beklenmeyen hatayla düşüyor | Logları incele | recorderunexpectedfailure | seyrek |
| Recorder yerelleştirilmemiş | Yerelleştirme yok | Dil seçeneğini kontrol et | recordernotlocalized | niş |
| UFT yapılandırılamıyor | UFT kurulumu/yapılandırması | UFT'yi yeniden kur | uftconfigfailure | seyrek |

### C8. Self-Service X sorunları

| ozellik | ne_yapar | admin_isi | kaynak | agirlik (tahmin) |
|---|---|---|---|---|
| Troubleshoot akış otomasyonu Self-Service X (üst) | SSX sorunları listesi | Alt konulara bak | troubleshootingssx | seyrek |
| Aktivite bilinmeyen durumda | Aktivite durumu "unknown" | Durumu yenile | activityunknownstate | seyrek |
| Aktiviteler 15 saniyede bir yenileniyor | Tasarım gereği yenileme aralığı | Beklenen davranış | activityrefresh | seyrek |
| SSX'e erişilemiyor | Erişim sorunu | Ağ ve URL'yi kontrol et | ssxnotaccessible | seyrek |
| Parola değişikliğinden sonra SSX girişi yok | Parola değişikliği senkronize değil | Oturumu kapat, yeniden gir | pwdchange | seyrek |

### C9. RAS sorunları

| ozellik | ne_yapar | admin_isi | kaynak | agirlik (tahmin) |
|---|---|---|---|---|
| Troubleshoot akış otomasyonu RAS (üst) | RAS sorunları listesi | Alt konulara bak | rastroubleshooting | seyrek |
| Windows'ta log dosyası oluşmuyor | Log dizinine yazma izni | İzinleri düzelt | nologsgenerated | seyrek |
| RAS otomatik yükseltmesi izin hatası | İzin değişikliği yükseltmeyi bozuyor | İzinleri eski haline getir | rasupgradeerror | seyrek |
| TLSv1.2 ile RAS kurulumu | Kurulum TLS hatası veriyor | TLS ayarını düzelt | rasinstallertlserror | niş |

### C10. Studio sihirbazları (wizards) sorunları

| ozellik | ne_yapar | admin_isi | kaynak | agirlik (tahmin) |
|---|---|---|---|---|
| Troubleshoot Studio wizards (üst) | Sihirbaz sorunları | Alt konulara bak | troubleshootstudiowizards | seyrek |
| getCategories SOAP isteği başarısız | SOAP isteği çalışmıyor | Servis URL ve kimlik bilgisini kontrol et | soaprequestfailure | seyrek |
| PowerShell sihirbazı başlamıyor | Sihirbaz başlamıyor | Studio ve PowerShell ortamını kontrol et | pshellwizardstartissue | seyrek |
| Bazı Middleware/SAP içerikleri kırmızı | Eksik içerik | İçerik paketini yeniden içe aktar | middlewaresapcpissue | niş |

---

## Genelleştirilmiş beceri aileleri

Not: Bu aileler doküman setindeki ürün adları ve örnek akışlardan (Ping, Shell wizard, REST wizard, Windows Diagnostic flow, SAP kullanıcı oluşturma, Central/Studio sorunları) türetilmiştir. Paket içindeki gerçek operasyon listesi bu dokümanlarda yok; aileler tahmindir.

1. Uzak komut çalıştırma: Shell wizard ile kabuk komutlarından akış üretme; Ping ve Windows tanılama akışı gibi örnekler; RPA Robot'un RDP oturumunda çalışması.
   - "Üç sunucuda disk kullanımını çalıştır ve sonuçları raporla."
   - "Linux makinede servis durumunu kontrol eden akış oluştur."
   - "Windows tanılama akışını yüz sunucuda paralel çalıştır."
2. HTTP/REST çağrısı: REST wizard ile akış üretme; SSL handshake hatasında HTTP isteği; Service_Url sistem özelliği.
   - "REST API'den token al ve sonraki adıma geçir."
   - "Servis URL'sini ortam değişkenine göre ayarla."
   - "HTTP isteğindeki SSL hatasını çöz."
3. Sanal makine yaşam döngüsü: vSphere, vCenter, Hyper-V, SCVMM, KVM, Nutanix, AWS, Azure, GCP, OCI (yalnız ürün adı olarak).
   - "Üç VM'i yeniden başlat ve durumunu raporla."
   - "Yeni VM oluşturup ağ ayarını yap."
   - "Bulut örneğini durdur ve sil (onay ile)."
4. Bilet açma/güncelleme (ITSM): ServiceNow, Service Manager, Service Management (SMAX) (yalnız ürün adı).
   - "Olay için ServiceNow'da bilet aç ve numarayı döndür."
   - "Service Manager'daki bileti kapat ve not düş."
   - "Değişiklik kaydını onay için güncelle."
5. DNS/IP yönetimi: Infoblox, Efficient IP DDI, OpenNetAdmin (yalnız ürün adı).
   - "Bu IP için DNS kaydını oluştur."
   - "Ağ bloğunda boş IP bul ve rezerve et."
6. Yük dengeleyici ve ağ cihazı: F5 BigIP, Network Automation, NNM (yalnız ürün adı); Central'da load balancer sıkıştırma ayarı sorunu.
   - "F5 havuzuna sunucu ekle ya da çıkar."
   - "Ağ cihazının yapılandırmasını yedekle."
7. Veritabanı sorgusu ve bakım: PostgreSQL, Oracle DB, Oracle Cloud Databases; akış otomasyonu'nun DB bakımı (veritabanı temizliği, parola değişimi, IP değişimi).
   - "Veritabanı boyutunu kontrol et ve eski kayıtları temizle."
   - "Veritabanı parolasını değiştir."
8. İzleme ve olay: Zabbix, Operations Manager, AI Operations Management, Universal Discovery and CMDB.
   - "Zabbix'ten alarm listesini al."
   - "CMDB'de bu sunucunun kaydını güncelle."
9. Yedekleme: Veritas NetBackup (yalnız ürün adı).
   - "Bu sunucunun yedeğini başlat ve durumunu döndür."
10. SAP yönetimi: SAP LaMa, SAP S/4 HANA (yalnız ürün adı); SAP kullanıcı oluşturma (Designer sorun giderme).
    - "SAP kullanıcısı oluştur ve parolayı sistem hesabından ata."
11. Kimlik ve sır yönetimi: CyberArk (yalnız ürün adı); sistem hesapları (Studio'da kimlik bilgisi saklama).
    - "Hesap kasasından parola al ve akışta kullan."
    - "Sistem hesabını ortama göre güncelle."
12. Konteyner ve IaC: Docker, Kubernetes, HashiCorp Terraform, Foreman (yalnız ürün adı).
    - "Bir konteyneri yeniden başlat."
    - "Terraform planını uygula."
13. Dosya ve XML: Studio'da XML operasyonları (büyük dosyada heap hatası). Dosya/FTP/SFTP, e-posta, JSON/XML paketleri bu dokümanda yok.
    - "Büyük XML dosyasını düzenle (heap'i artırarak)."
14. Akış/çalışma yönetimi: multi-instance lane, Central worker grubu, akış tetikleme, zamanlama.
    - "Bu akışı şu worker grubunda çalıştır."
    - "Takılı kalmış çalışmayı iptal et."

---

## Sorun giderme ve bilinen sorunlardan çıkan vaka adayları

1. Talep: "akış otomasyonu Central'da bir akış 'Paused - No Robots in Group' durumunda bekliyor, çözümü bul."
   - Belirti: Adım, robot grubunda uygun robot olmadığı için beklemede.
   - Kaynak: https://docs.microfocus.com/doc/397/26.4/norobots
2. Talep: "Yükseltme sonrası içerik paketi dağıtımı 'duplicated UUID' hatası veriyor."
   - Belirti: Aynı UUID başka bir akış ya da operasyonda zaten var.
   - Kaynak: https://docs.microfocus.com/doc/397/26.4/deployerror
3. Talep: "Multi-instance akış tüm lane'ler başarılı olduğu halde RUNNING'de kalıyor."
   - Belirti: Run log'da tüm lane'ler tamam, akış ilerlemiyor.
   - Kaynak: https://docs.microfocus.com/doc/397/26.4/miflowsstuck
4. Talep: "Zamanlanmış çalıştırmaların başlangıç saatleri tutarsız."
   - Belirti: Scheduler, Central, RAS ve istemci farklı saat dilimlerinde.
   - Kaynak: https://docs.microfocus.com/doc/397/26.4/inconsistentstart
5. Talep: "SAML ile Central yönetim portalına giriş yapılamıyor."
   - Belirti: SAML ayarı hatalı ya da admin kullanıcı silinmiş.
   - Kaynak: https://docs.microfocus.com/doc/397/26.4/incorrectsamlsetup ve https://docs.microfocus.com/doc/397/26.4/oolockout
6. Talep: "HTTP isteği yapan akışlar SSL handshake hatası veriyor."
   - Belirti: Yükseltme sonrası Java SNI varsayılanı nedeniyle bazı sunucularda el sıkışma hatası.
   - Kaynak: https://docs.microfocus.com/doc/397/26.4/sslhandshakeerror
7. Talep: "Yükseltme sırasında 'liquibase: Waiting for changelog lock' hatası alıyorum."
   - Belirti: Birkaç denemeden sonra sunucu başlamıyor.
   - Kaynak: https://docs.microfocus.com/doc/397/26.4/errormsg
8. Talep: "Linux'ta akış otomasyonu kurulumu başlatma sırasında takılıyor."
   - Belirti: Entropi havuzu yetersiz (değer <1000).
   - Kaynak: https://docs.microfocus.com/doc/397/26.4/insufficiententropypool
9. Talep: "Installer, güvenlik politikası yüzünden geçici klasörde çalışmıyor."
   - Belirti: /tmp ya da AppData\Local\Temp çalıştırmayı engelliyor.
   - Kaynak: https://docs.microfocus.com/doc/397/26.4/installertempfolderlocationlinux ve https://docs.microfocus.com/doc/397/26.4/installertempfolderlocationwindows
10. Talep: "Studio'da Git işlemi 'The system cannot find the file specified' hatası veriyor."
    - Belirti: Studio\Git\bin\git yolu bulunamıyor.
    - Kaynak: https://docs.microfocus.com/doc/397/26.4/gitoperationerror
11. Talep: "Studio'da klasör commit edilemiyor (kilit hatası)."
    - Belirti: Klasör çok taşınıp orijinal konuma geri alınmış.
    - Kaynak: https://docs.microfocus.com/doc/397/26.4/commitfoldererror
12. Talep: "Central'da worker kaydedilemiyor."
    - Belirti: Load balancer'da compression açık; worker bağlantısı kopuyor.
    - Kaynak: https://docs.microfocus.com/doc/397/26.4/workerregistration

---

## Notlar

- Integrate bölümü bu doküman setinde yalnızca bir sayfa ve bir dış ürün matrisi olarak var. Paket ayrıntıları (Base content, SSH, PowerShell/WinRM vb.) burada bulunmadığından bölüm A'daki beceri aileleri ürün adlarından ve örnek akışlardan türetilmiştir.
- 26.4'te desteklenmeyen/kaldırılan platformlar için Bölüm C0'a bakılmalı.
- Okuma sayısı: 184 sayfa gövdesi + 1 entegrasyon matrisi.
