# OpenText sunucu otomasyonu (sunucu otomasyonu) 25.4 - Özellik Envanteri

Kaynak kök: https://docs.microfocus.com/doc/419/25.4/home
Tarih: 2026-11-17. Bu dosya yalnızca okuma ile üretildi; giriş, indirme, form gönderme yapılmadı.

## 1. Kapsam ve okuma durumu

Yöntem: Portal JavaScript ile çiziliyor. Tam içindekiler ağacı `/419/25.4/tocflat.json` (1490 sayfa kaydı) üzerinden alındı. Sayfa gövdeleri aynı portalın `/419/25.4/<sayfa>/default-<revizyon>.json` dosyalarından okundu. Tarayıcı sekmesi tab-4 ile çalışıldı.

- Toplam sayfa kaydı (TOC): 1490. Kapsamdaki bölümler (Use 930, Administer 282, Develop 66, Integrate 20) toplam 1298 kayıt.
- İkinci tur (bu tur): tocflat `https://docs.microfocus.com/419/25.4/tocflat.json` adresinden alındı (`/doc/419/` yolu 403 verdi). Home sayfası navigasyonla açıldı, ardından aynı origin'den `default-<revizyon>.json` gövdeleri `fetch` ile okundu. Tek sekme: tab-7. Yaklaşık 75 gövde okundu; 2,5 sn aralıkla; 429 ve bot kontrolü yok.
- İlk tur (önceki): 3 tam sayfa (home, use, serverautomationuserguide) ve yaklaşık 165 içerik sayfası yazılmıştı; bu sayı ikinci turda yeniden doğrulanmadı.
- Gövdesi okunan sayfa (ilk tur): 150 adet üçüncü seviye (L3) sayfa (Integrate ve Administer'ın TOC sırasındaki ilk 150'si), 11 bölüm giriş sayfası (Use, Develop, Administer hub'ları), Release notes'tan Known issues, Deprecation and Obsolescence, Enhancements, ve Troubleshoot'tan Troubleshoot sunucu otomasyonu services.
- İkinci turda okunanlar: Use L3 sayfalarından device group (statik, dinamik, Explorer, dönüştürme), Run Script ve betik kütüphanesi, Global Shell/aaa/rosh/remote terminal, Windows-Ubuntu-Red Hat-Solaris yama, yazılım politikası ve remediation, audit/snapshot/compliance, build plan, VM yaşam döngüsü, Application Configuration, Ansible, job log; Develop'tan REST, Pytwist, PowerShell REST/SOAP, sunucu otomasyonu CLI, APX, Agent Tools, pluggable checks, CML/XML; Release notes > Fixed issues (ilk kısım).
- Eksik kalan (ikinci tur sonrası; üçüncü turda aşağıdaki kısmı kapatıldı, bkz. 2.7 ve 6): Use L3-L4 sayfalarının çoğu (Windows yama ayrıntıları, Chef, OCLI, Server Agent kurulum alt sayfaları, OS provisioning ayrıntıları); Develop'ta Java RMI, Web Services örnekleri, APX alt sayfaları ve pluggable check ayrıntıları, Administer'ın 150. sayfadan sonraki komut/araç sayfaları, Administer içinde gövdesi okunmayan L2 sayfaları (AutoPass, facility, notifications, HA vb.).
- Eksik kalan (güncel): Get started, Install ve Upgrade için ikinci turda üst düzey sayfalar okundu, alt adım sayfaları okunmadı. Troubleshoot alt sayfalarının 12'si üçüncü turda okundu (2.7 ve 6); 27'si hâlâ okunmadı (başlık düzeyinde). Release notes ana sayfası okunmadı; Fixed issues ilk kısmı okundu.
- Ağırlık sütunundaki değerler belgeden çıkarılmış değil, tahmindir. Yalnızca başlıktan çıkarılan satırlar için "tahmin (başlık)" olarak işaretlendi.
- Üçüncü tur (bu tur, 2026-11-17): tocflat'tan Use L3-L4 yama, yazılım, audit, snapshot, provisioning, Application Configuration ve Solaris/HP-UX/Ubuntu/RHEL/SUSE sayfaları (212 gövde), ardından Troubleshoot 12 alt sayfa ve Administer izin modeli ile komut sayfalarından 46 gövde okundu. Bu turda toplam 258 gövde okundu; 1 sayfa (patch_mgmt/deleting_a_patch_policy_windows) 403 döndü ve atlandı. Önceki turlarla örtüşme tekilleştirilmedi; kümülatif tahmin yaklaşık 450 gövde.
- Üçüncü turda da okunmayan: Administer komut sayfalarından dgdump, dgoptimizer, dgtree, dgusage, fixdevicerealm, fixorphanedunits, fixorphanedagentdevice, fixsatellitemirrorsync, forceresolve, deleteplatformunits, deletev12nserver, fakevcenter, ddl, recertcora, usermigrator, cli; izin alt sayfalarından apxpermissions ve javarmiclients. Develop'ta Java RMI ve Web Services örnekleri, Install/Upgrade alt adımları ve Release notes ana sayfası okunmadı.

Kısaltmalar: sunucu otomasyonu = sunucu otomasyonu; L3 = TOC üçüncü seviye; DAE = Data Access Engine; MM = Multimaster.

## 2. Özellik envanteri

Sütunlar: ozellik · ne_yapar · admin_isi · kaynak · agirlik. Kaynak adresleri https://docs.microfocus.com/doc/419/25.4/<sayfa> biçimindedir; kısalık için kökü yazmadan sayfa adı verilmiştir (ör. `managinguserssaclient` = https://docs.microfocus.com/doc/419/25.4/managinguserssaclient).

### 2.1 Yönetim (Administer)

| ozellik | ne_yapar | admin_isi | kaynak | agirlik |
|---|---|---|---|---|
| Kullanıcı yönetimi | sunucu otomasyonu kullanıcısı oluşturur, düzenler, parolasını değiştirir, gruba atar. | Kullanıcı açma, devretme, parola sıfırlama. | managinguserssaclient | çekirdek (tahmin) |
| Kullanıcı grupları | Rol olarak tanımlı grup oluşturur, kopyalar, siler, üye ekler. | Role göre erişim verme. | managingusergroupssaclient, aboutsausersusergroups | çekirdek (tahmin) |
| Grup izinleri (action, resource, folder, OGFS) | Her gruba eylem, kaynak, klasör ve OGFS izinlerini atar. | Hangi rolün neyi yapabileceğini sınırlama. | settingpermsusergroups | çekirdek (tahmin) |
| Süper yöneticiler | Tam yetkili yönetici hesaplarını ve grup atamasını yönetir. | Yönetici atama ve kaldırma. | managingsuperadminssaclient | seyrek (tahmin) |
| Müşteri (customer) yönetimi | Sunucuları müşterilere böler, müşteri yöneticisi ve müşteri grupları tanımlar. | Çok kiracılı erişim sınırı kurma. | managingcustadminscustgroupssaclient | sık (tahmin) |
| Parola, hesap ve oturum politikaları | Parola süresi, eski parola yasağı, kilitleme, pasif hesap ve oturum kilidi kurar. | Parola ve oturum sıkılaştırma. | setpassword | sık (tahmin) |
| LDAP dizin entegrasyonu | Kullanıcıları harici LDAP'tan içe alır, SSL ile doğrular. | Merkezi kimlik doğrulama. | authenticatingexternalldapdirectoryservice | sık (tahmin) |
| CAC/PIV akıllı kart | Akıllı kart sertifikasıyla sunucu otomasyonu girişi kurar. | Askeri/kamu ortamında kart tabanlı giriş. | sacac | niş (tahmin) |
| RSA SecurID | İki faktörlü doğrulama entegrasyonu. | 2FA talebi. | sarsasecuridintegration | niş (tahmin) |
| RADIUS | RADIUS sunucusu ile kimlik doğrulama. | Ağ kimlik altyapısı entegrasyonu. | radiusintegration | niş (tahmin) |
| Kullanıcı ve güvenlik raporları | Client ve özellik izinlerinin sunucular genelindeki özetini üretir. | Erişim denetimi raporu. | userandsecurityreports | sık (tahmin) |
| Sıkı denetim ve hesap verebilirlik | Salt okunur, dijital imzalı denetim izleri; imzalı SHA; rol tabanlı yetki; kullanıcı etkinlik kaydı. | Denetçiye kanıt sunma. | enforcingcontrolandaccountability | çekirdek (tahmin) |
| İç iletişim güvenliği | Core bileşenleri, agent ve core arası TLS iletişimi. | TLS politikası uyumu. | securingsainternalcommunications, sacorecommunicationsinfrastructure | sık (tahmin) |
| Satellite mimari güvenliği | Satellite'in güvenlik modeli ve ağ sınırı. | Uzak lokasyon güvenlik onayı. | sasatellitearchitecturesecurity | seyrek (tahmin) |
| SELinux politikası (agent) | Agent için SELinux politikası. | Sıkı Linux ortamında agent kurulumu. | selinuxsecuritypolicyagent | niş (tahmin) |
| Core sertifika yönetimi ve recertification | PKI sertifikalarını yönetir; üçüncü taraf sertifika modunda core'u yeniden sertifikalar (Full ve Simplified). | Sertifika süresi dolmadan yenileme. | certificatemanagement, sacorerecertification, usesacorerecertification | sık (tahmin, periyodik) |
| Agent recertification | Core recertification dışında agent'ları yeniden sertifikalar. | Agent sertifikası yenileme. | saagentrecertification | seyrek (tahmin) |
| Multimaster mesh durumu | Tesisler arası işlem durumunu ve çakışmaları gösterir. | Mesh sağlığı izleme. | viewingstatemultimastermeshsaclient | sık (tahmin) |
| Mesh çakışmalarını çözme | Çakışan işlemleri sunucu otomasyonu Client'tan çözer. | Çoklu core çakışma onarımı. | resolvingmeshconflictssaclient, advancedtypescausesmeshconflicts | sık (tahmin) |
| Mesh e-posta uyarıları | Çakışma ve bileşen sorunlarında e-posta gönderir. | Uyarı alıcılarını yapılandırma. | multimasteremailalerts | sık (tahmin) |
| MM Central taşıma | MM Central rolünü bir core'dan diğerine taşır. | Mesh merkezini değiştirme. | mmcentralrelocation | seyrek (tahmin) |
| Satellite başlat, durdur, doğrula | Satellite servisini başlatır/durdurur; Core Management Gateway iletişimini doğrular. | Uzak lokasyon satellite bakımı. | startingrestartingsatellite, stoppingsatellite, verifysatelliteprimarycore | sık (tahmin) |
| Satellite bilgi ve izleme | Facility, realm, gateway bilgisi, bant genişliği/link maliyeti değişimi, gateway tanı çıktısı. | Satellite durum sorgusu. | viewingsatelliteinformation, satellitemonitoring | sık (tahmin) |
| Satellite yazılım deposu önbelleği | Satellite'in paketleri çekirdekten önbelleğe alması; tam mirror modu; core doğrudan senkron. | Düşük bant genişlikli lokasyonda yazılım dağıtımı. | satelliteswrepositorycache, satellitefullmirrormode, satellitecoredirectsync | sık (tahmin) |
| Bant genişliği yönetimi (BCM) | Uzak bağlantılarda trafik sınırlama; BCM aracı, grammar. | Uzak bağlantı kotası. | bandwidthmgmtremoteconnections, bandwidthconfigmanagementtool | seyrek (tahmin) |
| Yönetilen sunucu peer önbelleği | Küçük sahalarda peer cache ile satellite yerine yerel önbellek. | Küçük lokasyon kurulumu. | managedserverpeercontentcaching | seyrek (tahmin) |
| IPv6 desteği | IPv4/IPv6 çift yığın ve IPv6 kapsamı. | IPv6 ağ geçişi. | ipv6insa | seyrek (tahmin) |
| Agent yapılandırma parametreleri | Agent CPU affinity ve sistem parametreleri. | Agent davranış ayarı. | saagentconfigurationparameters | seyrek (tahmin) |
| Çoklu veri erişim motoru ve paralel uygulama | DAE örnekleri arasında atama; MM işlemlerini paralel uygulama. | Yük ve performans ayarı. | multipledataaccessengine, dbaccessengineconfiguration, paralleltransactionapplication | seyrek (tahmin) |
| Yazılım deposu mirror ayarı | Mesh veya tesis düzeyinde yazılım deposu aynalamayı açar/kapatır. | DR ve yedeklilik için depo senkronu. | changingswrepositorymirroringparameters, enablingdisablingsoftwarerepositorymirroring | sık (tahmin) |
| Audit sonuçlarını ve snapshot'ları temizleme | Biriken audit sonuçlarını ve snapshot'ları zamanlanmış temizler. | Depo şişmesini önleme. | schedulingauditresults | sık (tahmin) |
| Bileşen izleme (portlar, süreçler, loglar) | Agent, Agent Cache, Command Center, DAE, WS DAE, Command Engine, Software Repository, Model Repository, OGFS, Spoke, Gateway, OS Boot/Media Server için port, süreç ve log kılavuzu. | Her bileşen için sağlık kontrolü. | agentmonitoring, commandenginemonitoring, softwarerepositorymonitoring, modelrepositorymonitoring, gatewaymonitoring | çekirdek (tahmin) |
| Health Check Monitor (HCM) | Core için yerel ve global test paketi; HCM testlerini genişletme. | Otomatik core sağlık denetimi. | corehealthcheckmonitorhcm, extendingthehealthcheckmonitor | sık (tahmin) |
| Sistem tanılama (System Diagnosis) | Core bileşenleri, DAE, Software Repository, Command Engine ve agent etkileşimini test eder. | Arıza giderme öncesi tanı. | runningasystemdiagnosis, systemdiagnostictests | sık (tahmin) |
| Start/Stop script | Core bileşenlerini başlatma, durdurma, durum sorgulama; bağımlılık kontrolü; Oracle DB dahil. | Servis yönetimi. | thesastartstopscript | sık (tahmin) |
| Bileşen log seviyesi | Log seviyesini geçici yükseltme. | Tanı için ayrıntılı log. | changingcomponentloglevel | sık (tahmin) |
| Global Shell denetim logları | Shell olaylarını, akış ve script loglarını, dijital imzaları kaydeder. | Kim neyi değiştirdi sorusu. | globalshellauditlogs | sık (tahmin) |
| Oturum verisi çıkarma | "Way session" kayıtlarını listeler ve dump_session ile biçimlendirir. | İş geçmişi ve olay sorgusu. | extractingsessiondata, dumpsession | seyrek (tahmin) |
| İzin referansları | Sunucu nesnesi, cihaz grubu, agent kurulumu, sanallaştırma, OS provisioning, yazılım, Chef, Application Configuration, yama (Windows, Ubuntu, Solaris, diğer UNIX), audit, compliance, iş, script ve akış otomasyonu flow izinleri. | Rol-izin eşlemesi. | permissionsreference ve alt izin sayfaları | çekirdek (tahmin) |
| Yama (Windows) temizliği | Windows yama kayıtlarını temizler. | Yama katalog bakımı. | cleaningwindowspatches | seyrek (tahmin) |
| Yönetilen platform desteği | Desteklenen platform matrisi. | Platform uygunluk kontrolü. | managedplatformsupport | sık (tahmin, başlık) |
| Core yedekleme ve geri yükleme | Yedekleme ve geri yükleme en iyi uygulamaları. | Felaket kurtarma. | sabackuprestorepractices | sık (tahmin, başlık) |
| Yüksek erişilebilirlik (HA) | HA veritabanı ve core yapılandırması. | Kesintisiz çalışma. | sahighavailability | sık (tahmin, başlık) |
| Public cloud agent'ları | Bulut sunucularında agent. | Bulut envanteri. | saagentspubliccloud | seyrek (tahmin, başlık) |
| Multimaster mesh yönetimi (genel) | Ağ yönetimi, e-posta, mesh yapılandırması. | Çoklu lokasyon yönetimi. | multimastermeshadministration, networkadminmultimastermesh | sık (tahmin, başlık) |
| Tesis (facility) yönetimi | Tesis tanımlama ve yönetimi. | Lokasyon modeli. | facilityadministration | sık (tahmin, başlık) |
| sunucu otomasyonu bildirimleri | Bildirim yapılandırması. | Olay bildirimi. | sanotificationconfiguration | sık (tahmin, başlık) |
| Core bileşen ayarı değişiklikleri | sunucu otomasyonu kurulum değişiklikleri, bakım. | Kurulum sonrası ayar. | samaintenance | seyrek (tahmin, başlık) |
| Uzak iletişim (remote communications) | Uzak agent iletişimi yönetimi. | Uzak erişim. | saremotecommunicationsadministration | seyrek (tahmin, başlık) |
| AutoPass lisanslama | Lisans yönetimi. | Lisans etkinleştirme ve izleme. | saautopassintegration | çekirdek (tahmin, başlık) |
| Patch sunucu otomasyonu core sonrası | Yayın sonrası core yaması. | Core bakım yaması. | patchsacore | sık (tahmin, başlık) |
| Destek araçları | Destek paketi ve tanı araçları. | Destek vakası için veri toplama. | support | sık (tahmin, başlık) |
| Komut satırı core araçları (bakım) | cli, cora, check_way_obj_sigs, clear_conflicts, compare_db, conflicting_checker, coreServerCount, cascade, ddl, dep_sorted_classes, deletePlatformUnits, deleteV12nServer, fixDeviceRealm, fixOrphanedAgentDevice, fixOrphanedUnits, fixSatelliteMirrorSync, force_resolve, getDevicePatchDetails, dgTree, dgUsage, dgDump, dgOptimizer, fakeVCenter, caMigrate. | Veri bütünlüğü onarımı, mesh çakışma çözümü, cihaz grubu analizi, cihaz kaydı düzeltme. | Sayfa adları: cli, cora, checkwayobjsigs, clearconflicts, comparedb, conflictingchecker, coreservercount, cascade, ddl, depsortedclasses, deleteplatformunits, deletev12nserver, fixdevicerealm, fixorphanedagentdevice, fixorphanedunits, fixsatellitemirrorsync, forceresolve, getdevicepatchdetails, dgtree, dgusage, dgdump, dgoptimizer, fakevcenter, camigrate | seyrek (tahmin) |
| Device group dinamik kural araçları | Dinamik grup kurallarını dökümler, optimize eder, kullanımını bulur. | Dinamik grup kural sorunları. | dgdump, dgoptimizer, dgusage | seyrek (tahmin) |
| DET (cbt) dışa aktarma ve içe aktarma | RDF/XML olarak içerik dışa aktarır, hedef mesha içe aktarır; delta export/import; filtre dosyaları; silinmiş içerik yönetimi. | Mesh'ler arası içerik taşıma ve senkron. | dcml, detcommands, detusage, importingcontent, policyimportingcontent, synchronizingmultimaster, exportingfilters | seyrek (tahmin) |
| IDK ve ISM paketleme | ISM (yazılım modülü) paketi oluşturma, build, upload; ISM denetimleri. | Özel yazılım paketi üretme. | idkoverview, idkbuild, idkscripts, idkcommands, ismcontrolsreference | seyrek (tahmin) |
| Komut satırı CLI | Nesne ve eylem tabanlı CLI (`cli [options] object action`). | Betik ile toplu nesne işlemi. | cli | sık (tahmin) |

### 2.2 Kullanım (Use)

Not: İkinci turda Use'un kritik sayfalarının gövdeleri okundu; "(okundu)" işaretli satırlar gövdeye dayanır, detay için 2.6'ya bakın. Diğer satırlar hâlâ başlık/tahmindir.

| ozellik | ne_yapar | admin_isi | kaynak | agirlik |
|---|---|---|---|---|
| sunucu otomasyonu Client başlangıcı ve arayüz | Client başlatıcıyı kurar, arayüz, seçenekler, arama, koyu tema, iş logu gösterimi. | Operatör oturumu açma ve gezinme. | serverautomationuserguide (ve Getting started with sunucu otomasyonu Client alt sayfaları) | çekirdek (tahmin) |
| Kütüphane (sunucu otomasyonu Library) | Klasör yönetimi; yazılım ve politika öğelerinin yeri. | İçerik düzenleme. | Explore the sunucu otomasyonu library alt sayfası | sık (tahmin) |
| Sunucu ve cihaz grubu keşfi | Sunucu envanteri, ilişkiler, politika, cihaz grupları (statik ve dinamik), Device Group Explorer. | Sunucu gruplama ve hedefleme. | Explore servers and device groups in the sunucu otomasyonu Client | çekirdek (okundu) |
| Server Agent yönetimi | Agent keşfi, ADT ile kurulum, üçüncü taraf modu, WSUS bağlantısı, agentsız keşif, yükseltme, başlat/durdur, tanı ve iletişim testleri. | Agent kurma ve sorun giderme. | Manage the Server Agent ve alt sayfalar | çekirdek (tahmin) |
| Müşteri (customer) görevleri | Müşteri tanımlama ve görevleri. | Çok kiracılı sunucu ayrımı. | Create and managing customers | sık (tahmin) |
| Extensible discovery ve özel alanlar | Extension çalıştırma, extensible discovery, özel alan (custom field) ve özel öznitelik (custom attribute) yönetimi. | Ek envanter verisi toplama. | Run sunucu otomasyonu extensions | sık (okundu) |
| Script çalıştırma | Script yönetimi ve sunucuda çalıştırma süreci. | Uzaktan script yürütme. | Execute scripts | çekirdek (okundu) |
| sunucu otomasyonu Global Shell ve OGFS | Sunucuları dosya sistemi gibi gösteren OGFS; rosh uzak kabuk; komutlar; sunucu filtreleme; uzak terminal; tutorial ve örnekler; karakter kodlaması. | Sunuculara yönetimsel komut ve dosya erişimi. | sunucu otomasyonu Global Shell, OGFS directories, Global Shell utilities syntax (aaa, rosh, swenc) | çekirdek (okundu) |
| sunucu otomasyonu Command Line Interface (OCLI) | CLI kurulumu, çalıştırma, komut sözdizimi. | Komut satırı otomasyonu. | sunucu otomasyonu Command Line Interface (OCLI) | sık (tahmin) |
| CLI ile agent kurulumu ve yükseltme | Agent'ı CLI ile kurar, üçüncü taraf modunda kurar, WSUS, ek bilgi, kaldırma, yükseltme. | Otomatik agent dağıtımı. | Agent installation and upgrade utilities | sık (tahmin) |
| sunucu otomasyonu Client raporları | Rapor özellikleri, izinler, rapor çalıştırma, parametre değiştirme, sonuç görüntüleme. | Envanter ve uyum raporu. | serverautomationreportsoverview, sunucu otomasyonu Client Reports | çekirdek (okundu) |
| Windows yama yönetimi | Yama politikası, sunucu otomasyonu entegrasyonu, yama süreci, yönetim. | Windows yama uyumu. | Patch management for Windows | çekirdek (tahmin) |
| HP-UX yama yönetimi | Depo, yazılım kataloğu, politika, yama kurulum ve kaldırma, uyum. | HP-UX yama. | Patch management for HP-UX | niş (tahmin) |
| Solaris yama yönetimi | Yama kurulum, uyum taraması, yama politikası; Solaris 11 yama akışı. | Solaris yama. | Patch management for Solaris, Patch management for Solaris 11 | sık (okundu) |
| Debian ve Ubuntu yama yönetimi | Debian metadata, Ubuntu yama politikası, rol, locale, kurulum. | Debian ailesi yama. | Patch management for Debian, Patch management for Ubuntu | sık (okundu) |
| Unix yama yönetimi | Yama izleme, arama, yazılım politikası ile yama, kurulum ve kaldırma. | Diğer UNIX yamaları. | Patch management for Unix | sık (tahmin) |
| Red Hat ve Oracle Linux yama | Red Hat errata ve kanal içe aktarma, tarama, politika, uyum; OEL başlangıcı. | RHEL yama. | Patch management for Red Hat Linux Enterprise, Patch management for Oracle Enterprise Linux | çekirdek (okundu) |
| SUSE yama | SUSE patch içe aktarma, errata ve kanal politikaları. | SUSE yama. | Patch management for SUSE Linux Enterprise | sık (tahmin) |
| RPM remediation (mrc_calc) | RPM düzeltme için en iyi uygulama aracı. | Minimum RPM düzeltme hesabı. | RPM remediation best practice - Using the mrc_calc Tool | seyrek (tahmin) |
| Audit ve uyum | Audit kuralları, audit politikaları, audit sonuçları, kural istisnaları, remediation eylemleri, dosya dahil/hariç kuralları. | Yapılandırma uyum taraması ve düzeltme. | Audits, audit policies, and audit results ve alt sayfalar | çekirdek (okundu) |
| Snapshot ve snapshot spesifikasyonu | Snapshot tanımlama, görüntüleme, arşivleme, silme, dışa ve içe aktarma, zamanlanmış snapshot işleri. | Yapılandırma sürümü ve karşılaştırma. | Snapshots, snapshot specifications, and snapshot jobs | sık (okundu) |
| Uyum panosu (Compliance) | Kategoriler, uyum durumları, yama, audit, yazılım ve yapılandırma uyumu, uyum taramaları. | Yönetici uyum görünümü. | Compliance | çekirdek (okundu) |
| sunucu otomasyonu Provisioning (OS kurulum) | OS yapı planları (build plan), ortam hazırlama, hedef sunucu hazırlama, ağ ayarı, Windows domain, UEFI Secure-Boot, Debian/SUSE/Windows/Linux/Solaris/ESXi yapılandırmaları, DHCP. | Bare metal sunucuya standart OS kurma. | Perform sunucu otomasyonu provisioning, sunucu otomasyonu Provisioning common use cases, Create sunucu otomasyonu build plans, sunucu otomasyonu Provisioning administration | çekirdek (okundu) |
| Yazılım yönetimi (Software Management) | Yazılım politikası oluşturma, paket yönetimi, uzaktan kurulum ve kaldırma, zamanlama, iptal, yükleme zaman aşımı, RPM modülleri, düşük disk alanında kurulum. | Paket dağıtımı ve uyum. | Software Management, Quick start, Create and manage software policies, Manage software packages, Remediate and install software | çekirdek (okundu) |
| Paket türü referansı | RPM, RPM modülü, LPP, HP-UX, Solaris (eski ve 11), Ubuntu, Windows, ZIP, uygulama medyası paketleri. | Paket türü seçimi. | Package type reference | sık (tahmin) |
| Sanallaştırma yönetimi | vCenter ve SCVMM hizmetleri, VM ve VM şablonu yaşam döngüsü (oluşturma, klonlama, taşıma, güç, askıya alma, şablona dönüştürme, silme), Solaris zone yönetimi, genealogy görünümü. | VM ve zone yaşam döngüsü. | Virtualization management ve alt sayfalar | sık (okundu) |
| Application Configuration | Yapılandırma dosyası şablonları (CML, XML, DTD), değer kümeleri, değer editörü, şablon içe aktarma, Application Configuration'ı sunuculara itme ve zamanlama, uyum ve audit, eski sürüme dönüş, karşılaştırma. | Uygulama yapılandırma dosyalarını standartlaştırma ve dağıtma. | quickstartapplicationconfiguration ve Application Configuration tasks alt sayfaları | sık (okundu) |
| Chef Cookbook yönetimi | Chef cookbook görüntüleme ve yönetimi, Run Chef Recipe işi, paket deposu, yerelleştirme, izinler. | Chef tarifi çalıştırma. | chefcookbooksinsa | seyrek (tahmin); 25.4'te Chef entegrasyonu kullanımdan kaldırıldı |
| Ansible Playbook | Ansible kurulumu, playbook yönetimi, çalıştırma, değişkenler, fact toplama. | Playbook çalıştırma. | ansibleplaybooks | sık (okundu) |

### 2.3 Geliştirme (Develop)

Not: İkinci turda Develop'un REST, Pytwist, PowerShell, sunucu otomasyonu CLI, APX, Agent Tools, pluggable checks ve CML/XML sayfalarının gövdeleri okundu (bkz. 2.6). Java RMI ve Web Services örnekleri okunmadı.

| ozellik | ne_yapar | admin_isi | kaynak | agirlik |
|---|---|---|---|---|
| sunucu otomasyonu Platform | sunucu otomasyonu API'lerini ve çalışma zamanını sunar; denetim, Windows yama, OS provisioning gibi servisleri açar. | Entegrasyon geliştirme. | serverautomationplatform | çekirdek (okundu) |
| APX (Automation Platform Extensions) | Program APX ve Web APX oluşturma, yapı, izinler, apxtool, geliştirme ortamı, öğreticiler. | Özel sunucu otomasyonu eklentisi geliştirme. | serverautomationplatform (APX alt sayfaları) | sık (okundu, başlık) |
| sunucu otomasyonu CLI metotları | sunucu otomasyonu CLI ile metot çağırma, parametre ve dönüş değeri, arama filtreleri, örnek scriptler. | Betik ile otomasyon. | serverautomationplatform (sunucu otomasyonu CLI methods) | sık (okundu, başlık) |
| Web Services (SOAP) istemcileri | Perl ve C# istemcileri, SOAP erişimi. Entire SOAP API 25.4'te kullanımdan kaldırıldı. | Eski entegrasyonlar. | serverautomationplatform (Web Services clients) | seyrek (tahmin); kullanımdan kaldırıldı |
| REST API | 25.4'te SOAP'ın yerine geçen REST API. | Modern API entegrasyonu. | serverautomationplatform (REST API) | çekirdek (okundu) |
| Pytwist (Python API) | Python ile sunucu otomasyonu API erişimi. | Python otomasyonu. | serverautomationplatform (Python API access with Pytwist) | sık (okundu, başlık) |
| Java RMI istemcileri | Java tabanlı erişim. | Java entegrasyonu. | serverautomationplatform (Java RMI clients) | niş (tahmin, başlık) |
| PowerShell entegrasyonu | Windows PowerShell'den REST ve SOAP ile sunucu otomasyonu erişimi. | Windows yöneticisi otomasyonu. | serverautomationplatform (PowerShell via REST/SOAP) | sık (okundu, başlık) |
| Agent Tools, pluggable checks | Agent araçları, pluggable ve gelişmiş pluggable kontroller, arama filtre sözdizimi. | Özel kontrol yazma. | serverautomationplatform (Agent Tools, Pluggable checks) | seyrek (okundu, başlık) |
| Uygulama yapılandırma geliştirme (CML, XML) | CML şablon dili, XML/DTD şablonları, örnekler ve öğreticiler. | Yapılandırma şablonu yazma. | applicationconfigurationdevelop | sık (okundu) |

### 2.4 Entegrasyonlar (Integrate)

| ozellik | ne_yapar | admin_isi | kaynak | agirlik |
|---|---|---|---|---|
| akış otomasyonu ile entegrasyon | akış otomasyonu akışlarını ve işlerini sunucu otomasyonu ile kurar; sunucu otomasyonu işlemlerini akış otomasyonu akışlarında kullanır; iş engelleme (job blocking) kuralları. | Akış tabanlı süreç otomasyonu ve iş bloklama. | oosaintegration, setupintegration, usecasessaooflows, usecasessaoojobs | sık (okundu) |
| uCMDB entegrasyonu (sunucu otomasyonu-uCMDB Connector) | Connector'ı başlatır, durdurur, durum gösterir; sunucu otomasyonu verisini uCMDB'ye aktarır; mapping dosyası ile özelleştirme; CI ilişkileri; SSL. | CMDB ile sunucu envanteri eşitleme. | saucmdbintegration, settingupsaucmdbintegration, howtos, usecases | sık (okundu) |
| Marketplace Connector (MPc) | Servis ve stream tanımlar; içerik ve güvenlik stream'leri; içerik indirir ve içe aktarır; komut satırı seçenekleri, önizleme, log. | Yazılım ve içerik akışı. | samarketplaceintegration, setupyourintegration, commandlineimportingcontent, troubleshootingmarketplace | sık (okundu) |
| Operations Platform entegrasyonu | Operations Platform kurar, sunucu otomasyonu'yı entegre eder, sunucu otomasyonu metadata'yı içe aktarır. Belgede 26.1 sürümüne atıf var. | Üst platform entegrasyonu. | integratesawithoperationplatform, saoperationsplatform261 | sık (başlık) |
| DMA (Database and Middleware Automation) | Veritabanı ve middleware otomasyonu entegrasyonu. | DB/middleware otomasyonu. | sadmaintegration | seyrek (tahmin, başlık) |
| DCA ile entegrasyon | Data Center Automation ile entegrasyon. | Veri merkezi otomasyonu. | sadcaintegration | seyrek (tahmin, başlık) |
| Network Automation (NA) | NA ile entegrasyon. | Ağ cihazı otomasyonu. | sana | seyrek (tahmin, başlık) |
| DCA OPTIC Reporting | sunucu otomasyonu operasyonel ve geçmiş verisini OPTIC Reporting'e aktarır; BVD ve BI araçları ile rapor. OBR alternatifi. | Özel rapor ve BI. | sacosointegration | sık (ana sayfa metni) |

### 2.5 Başlangıç, kurulum, yükseltme, sorun giderme (yalnızca özellik düzeyi)

| ozellik | ne_yapar | admin_isi | kaynak | agirlik |
|---|---|---|---|---|
| Kurulum planlama ve dağıtım | Boyutlandırma, sistem gereksinimleri, dağıtım stratejisi. | Kurulum planlama. | install, deploysa | çekirdek (tahmin, başlık) |
| Yükseltme | Ön hazırlık, ön koşul kontrolü, yükseltme. | Sürüm geçişi. | upgrade, upgradeprereqs, upgradesa | çekirdek (tahmin, başlık) |
| Sorun giderme (kurulum, provisioning, sunucu otomasyonu servisleri) | Kurulum, provisioning ve servis sorunları için kılavuz. | Sorun giderme. | troubleshoot, troubleshootsainstallation, troubleshootsaprovisioning, troubleshootsaservices | sık (tahmin, başlık) |
| Başlangıç kavramları ve lisans | Temel kavramlar, lisans haklandırması, kullanım senaryoları. | Lisans ve planlama. | getstarted, keyconcepts | sık (tahmin, başlık) |

### 2.6 İkinci tur: gövdesi okunan Use ve Develop sayfaları

Yöntem: TOC `https://docs.microfocus.com/419/25.4/tocflat.json` adresinden (sayfa betiğinin kullandığı yol; `/doc/419/...` yolu 403 verdi) alındı. Her sayfanın gövdesi `https://docs.microfocus.com/419/25.4/<sayfa>/default-<revizyon>.json` içindeki `parse.text` HTML'inden okundu. İstekler arası 2,5 sn. 429 veya bot kontrolü görülmedi.

| ozellik | ne_yapar | admin_isi | kaynak | agirlik |
|---|---|---|---|---|
| Statik cihaz grubu | Sunucuları elle eklenen bir sette toplar; grup eylemleri (yama, remediation, script) tüm üyelere birden uygulanır. Public Static türü de var. | Gruplama ve hedefleme. | aboutdevicegroups, aboutstaticdevicegroups | çekirdek (okundu) |
| Dinamik cihaz grubu ve kuralları | Kurallarla eşleşen sunucuları otomatik ekler/çıkarır (ad, IP, OS vb. öznitelikler). Her saat ve öznitelik değişiminde yeniden hesaplanır; elle "Recalculate" da mümkün. Çoklu kural desteği var. | Dinamik grup kuralı yazma ve doğrulama. | aboutdynamicdevicegroups, rulesdynamicdevicegroup, creatingdynamicdevicegroup, recalculatingmembersdynamicdevicegroup | çekirdek (okundu) |
| Dinamik grubu statiğe çevirme | Dinamik grubun o andaki üyelerini statik gruba sabitler; kurallar kaybolur. | Kural bağımlılığını kaldırma. | convertingdynamicgroup | sık (okundu) |
| Device Group Explorer | Grup özellikleri ve üye ekleme/çıkarma; Audit, Software, App Config ve Patch uyum özeti; uygulama yapılandırması ekleme; yama ve yazılım politikası görüntüleme; audit oluşturma; snapshot alma; özel öznitelik. | Grup yönetim ekranı. | devicegroupexplorer | çekirdek (okundu) |
| Sunucu Device Explorer | Sunucu başına ilişkiler, bağlı politikalar, özel öznitelikler, sanallaştırma hipervizörü/VM listesi, uzak terminal; Actions menüsünden operasyonlar. ESXi için bazı özellikler yok. | Sunucu inceleme. | serverssasclient | çekirdek (okundu) |
| Özel alan ve özel öznitelik | Özel alan (custom field) ve özel öznitelik (custom attribute) oluşturur; Namespace (ör. Ansible) ile betik ve araç erişimini belirler. | Ek envanter verisi ve betik değişkeni. | aboutcustomfields, creatingmanagingcustomers, ansiblevariables | sık (okundu) |
| Sunucu betiği çalıştırma (Run Script) | Kayıtlı veya ad-hoc betiği sunuculara çalıştırır. Options adımında Runtime User (root, Local System, Super User veya belirli kullanıcı), zaman aşımı, ek parametre ve çıktı seçenekleri ayarlanır. "Change Server=No" betikler paralel koşabilir (way.server_script.run_read_only_scripts_in_parallel, batchbot.max_concurrent_scripts). | Uzaktan betik yürütme ve çıktı alma. | runningsavedscriptadhocscript, executingscripts | çekirdek (okundu) |
| Betik kütüphanesi | Betik klasörleri ve klasör izinleri; oluşturma/yükleme, özellik düzenleme, sürüm geçmişi, dışa aktarma, yeniden adlandırma, silme; betiğin bağlı olduğu yazılım politikalarını görme. UTF-8 içe aktarmada karakter sorunu uyarısı var. | Betik yaşam döngüsü. | scriptsexecution, managingscripts | sık (okundu) |
| Betik özel öznitelik ikamesi | Betikte `opsw-template: yes` metadatası ile çalışma öncesi özel öznitelik değerleri yerleştirilir; varsayılan sınırlayıcı "@", Python/Shell için `{{ }}` tanımlanabilir. | Sunucuya özel betik. | customattributesubstitutioninscripts | sık (okundu) |
| OGFS dizin yapısı | Sunucu nesneleri dosya sistemi gibi görünür: id, attr, self, method dizinleri; method altındaki çalıştırılabilirler sunucu otomasyonu API metodlarını çağırır. | OGFS'de gezinme ve betik. | ogfsdirectories | çekirdek (okundu) |
| Global Shell izinleri (aaa) | launchGlobalShell, loginToServer, readServerFilesystem, readServerComplus, readServerMetabase vb. işlemler; sunucu veya login (kullanıcı) bazında verilir; /opsw/Permissions altında listelenir. | Shell yetki modeli. | globalshellutilities | çekirdek (okundu) |
| Global Shell komutları | Varsayılan bash; csh, ksh, sh, tcsh da var. /bin, /usr/bin ve sunucu otomasyonu'ya özgü /opsw/bin içindeki araçlar (rosh dahil) kullanılabilir. | Shell komut kapsamı. | commandsavailableglobalshell, differencesbetweenglobalshellunixshells | sık (okundu) |
| rosh (Remote sunucu otomasyonu Shell) | Global Shell içinden sunucuya login olup yerel komut çalıştırır. Sözdizimi: `rosh (-n server-name \| -i server-id) [-d dir] [-l login-name] [-s] [-t \| -T] [command]`. Ağ cihazları için -N, -C, -L, -P, -V seçenekleri. | Sunucuda tek komut çalıştırma. | roshutility, remotesashellroshutility | çekirdek (okundu) |
| Uzak terminal (Remote terminal) | sunucu otomasyonu Client'tan UNIX sunucuda terminal, Windows sunucuda RDP penceresi açar. OGFS erişimi yoktur. Bağlantı tercihleri Set Preferences'ta. | İnteraktif sunucu oturumu. | remoteterminal | sık (okundu) |
| Windows yama politikası | Aynı Windows OS'a ait yamaları içerir; yama ekleme/kaldırma; sunucuya veya gruba ekleme; yama istisnası (Never Install vb.) ekleme, kopyalama, kaldırma. | Yama grubu ve istisna yönetimi. | patchpolicy, createpatchpolicywindows, setpatchpolicyexception | çekirdek (okundu) |
| Windows yama uyumu | Uyum seviyesi belirler; uyum taramasını hemen veya zamanlı başlatır. Non-compliance nedenleri: istisna ile çakışma (ör. Never Install yüklü yama) ve önerilen superseded yamalar. | Uyum raporu ve sapma tespiti. | patchcompliancewindows, patchnoncompliance, setpatchcompliancelevel, schedulepatchcompliancescan | çekirdek (okundu) |
| Windows yama kurulumu zamanlama | İndirme ve kurulum aşamaları ayrı zamanlanabilir (Staged seçeneği); Run Task Immediately veya Run Task At; önizleme analizi. | Bakım penceresi planı. | schedulewindowspatchinstallation | çekirdek (okundu) |
| Ubuntu/Debian yama | Ubuntu'da yama = Debian paketi. Statik ve dinamik yama politikaları; ön/son kurulum betiği; zamanlanmış kurulum ve kaldırma. | Ubuntu paket güncellemesi. | patchmanagementubuntu, patchmanagementdebian | sık (okundu, kısmen) |
| Red Hat errata yönetimi | Yama = Red Hat errata; errata ve kanal içe aktarma (Red Hat Subscription Management veya Hybrid Cloud Console); tarama, politika ve uyum. | RHEL güvenlik ve paket uyumu. | patchmanagementredhat, rhelcontentimport | çekirdek (okundu) |
| Solaris yama ve IPS | Solaris 10 (Update 1-9) ve Solaris 11 için yama tanıma, kurma, kaldırma. Solaris 11'de yama birimi IPS paketidir. | Solaris yama uyumu. | patchmanagementsolaris | sık (okundu) |
| Yazılım politikası | Paket, yama, betik ve Application Configuration'ı tek politikada toplar; sunuculara veya device group'a eklenir; politika şablonu ve sıra (installation order) desteği. | Dağıtım tanımı. | aboutsoftwarepolicies, softwarepolicytemplates | çekirdek (okundu) |
| Remediation (düzeltme) | Üç aşama: Analysis (fark bulma), Download (kaynak indirme), Installation (sırayla kurma). Reboot, hata ve betik seçenekleri; önizleme; aşama zamanlama; iş durumu. | Politikayı sunucuya uygulama. | remediatingservers, remediatingmanagedservers | çekirdek (okundu) |
| Politikasız kurulum/kaldırma | Politika olmadan paket kurar veya kaldırır; ön/son betik, zaman aşımı, önizleme ve aşama zamanlama. | Ad-hoc paket işi. | installinguninstallingsoftwarewithoutsoftwarepolicy | sık (okundu) |
| RPM ve RPM modülü | Politikada RPM otomatik güncelleme; RPM modülü kurma ve kaldırma (politika ile veya ad-hoc). | Linux paket yaşam döngüsü. | installingupdatingrpmpackages, installingrpmmodulesoftware_policy | sık (okundu, başlık) |
| Audit kuralları ve istisnaları | Kurallar hedef sunucuda değerlendirilir; geçici veya kalıcı istisna; remediation eylemi; özel betik kuralı (custom scripts rule); dosya adı için özel öznitelik parametreleri. | Uyum istisnası yönetimi. | saauditsnapshotrules, saauditruleexceptions, configuringthecustomscriptsrule | çekirdek (okundu) |
| Audit zamanlama | Tek sefer veya tekrarlı; e-posta bildirimi; sürmekte olan audit işini iptal etme; zamanlamayı görüntüleme ve silme. | Periyodik uyum taraması. | schedulinganaudit | sık (okundu) |
| Snapshot ve snapshot spesifikasyonu | Spec tanımlar, kuralları ayarlar, audit policy olarak kaydeder ve çalıştırır; snapshot görüntüler, arşivler, siler, dışa/içe aktarır; tekrarlı snapshot job zamanlar. | Yapılandırma geçmişi ve karşılaştırma. | snapshotspecificationsintro, snapshotjobs, archivingasnapshot, exportingimportingsnapshot | sık (okundu) |
| Uyum panosu (Compliance) | Sunucu, çoklu sunucu ve grup düzeyinde uyum. Kategoriler: Audit, Audit Policy, Software, Patch, Configuration. Eşikler (thresholds), uyum taraması, düzeltme, otomatik kontrol sıklığı ve dışa aktarma. | Uyum durumunu izleme. | thecompliancedashboard, compliancestatuses, compliancescans | çekirdek (okundu) |
| Build plan (OS yapı planı) | Adımlar: Run Script, Install Zip, config dosyası yükleme, device group'a ekleme, Software/Patch policy ekleme, Remediate Server. Baseline plan değiştirilmez; kopya oluşturulup düzenlenir. | OS kurulum akışı tanımı. | creatingsabuildplans, buildplansteps, editingabuildplan | çekirdek (okundu) |
| Run Build Plan (provisioning çalıştırma) | Sihirbazla sunucu seçip build plan başlatır; çalışan ve tamamlanan Run Build Plan işlerini arar. Provisioning sorun giderme bölümü ayrıca var. | Bare metal kurulum. | performingsaprovisioning, phase3runningbuildplan | çekirdek (okundu) |
| Provisioning DHCP | sunucu otomasyonu DHCP IPv4 ve IPv6 sunucu yapılandırması; mevcut ISC ve Microsoft 2012 DHCP için kurulum; SPARC provisioning modu değiştirme. | Ağ hazırlığı. | dhcpconfiguration | sık (okundu) |
| VM ve VM şablonu yaşam döngüsü | Şablon oluşturma, VM oluşturma, yönetme, silme; VM sprawl ve uyum kaymasını kontrol. Sanallaştırma servisi (vCenter, SCVMM) eklenerek yönetilir. | VM yaşam döngüsü. | virtualmachinelifecycle, virtualizationservicetasks | sık (okundu) |
| Solaris zone yönetimi | Zone için OS provisioning ve agent kurulumu; zone yaşam döngüsü. | Zone yönetimi. | managingoraclesolariszones, osprovisioningagentinstallation | sık (okundu, başlık) |
| Application Configuration kavramları | Yapılandırma dosyalarını (tek dosya veya XML dahil uygulama seti) merkezi şablondan yönetir; dosya ile şablon arasındaki sapma (Out of Sync) izlenir. | Config standardı ve dağıtım. | applicationconfigurationconcepts | çekirdek (okundu) |
| App Config push zamanlaması | Hemen, gelecek tarihte veya tekrarlı (günlük, haftalık, aylık) push; durum Jobs and Sessions sekmesinde. | Config dağıtımı. | scheduleapplicationconfigurationpush, attachapplicationconfiguration | sık (okundu) |
| Yapılandırma betik şablonları | Configuration template ve script template; data manipulation betiğiyle ikili olmayan yapılandırma yönetimi; betikten şablon oluşturma. | Karmaşık config işleme. | createtemplatefromscript, managenontextconfigurations | sık (okundu, başlık) |
| Ansible playbook çalıştırma (Ansible Runner APX) | Sunucu veya device group seçilip Run Extension > Ansible Runner; Options'ta `-p <playbook_id>`. Playbook'ta `hosts` değişkeni all/* (veya linux_servers, windows_servers) olmalı; eşleşme yoksa hiçbir şey çalışmaz. | Playbook dağıtımı. | runansibleplaybooks | sık (okundu) |
| Ansible değişkenleri | Host değişkeni (Custom Attribute, Namespace=Ansible), değişken dosyaları, özel facts; device group'tan miras alınır. | Ansible değişken yönetimi. | ansiblevariables, gatheringfacts | sık (okundu) |
| İş günlüğü ve sonuç arama | Jobs and Sessions > Job Log; adım içinde Ctrl-F ile arama; push/restore dışındaki tüm iş türleri için filtre. | İş sonucu inceleme. | searchfilterjobresults | sık (okundu) |
| Aktif işi sonlandırma | Analyze tamamlanınca durur; Download/Install fazında davranış faza göre değişir; sonraki ve zamanlanmış fazlar iptal edilir. Yetki gerekir. | Acil durdurma ve bakım penceresi aşımı. | terminatingactivejobs | sık (okundu) |
| sunucu otomasyonu Client raporları | Rapor çalıştırma, parametre değiştirme ve zamanlama; DCA COSO Reporting ile birlikte kullanılır. | Envanter ve uyum raporu. | serverautomationreportsoverview | çekirdek (okundu) |
| sunucu otomasyonu Platform API | Audit compliance, Windows yama ve OS provisioning gibi servisleri API olarak sunar; çalışma zamanı OGFS üzerinde Global Shell betiklerini çalıştırır. | Entegrasyon zemini. | serverautomationplatform | çekirdek (okundu) |
| REST API | JSON ve HTTP; POST ile token alınır (duration parametresi isteğe bağlı); OpenAPI dokümanı docs.microfocus.com/api/Server_Automation altında. SOAP'ın yerine geçer. | Modern API entegrasyonu. | restapi | çekirdek (okundu) |
| SOAP Web Services (Perl, C#) | WSDL ile Perl ve C# istemcileri; kullanımdan kaldırıldı. | Eski entegrasyonlar. | webservices | seyrek (okundu, kullanımdan kaldırıldı) |
| Pytwist (Python API) | Java paket adını Python'a çevirir (com.opsware.server.ServerService -> server.ServerService); TwistServer ile servise erişim; findServerRefs ve getServerVO gibi metodlar. Python 3.8 hedefi (Agent ile aynı). Sunucuda DSE veya ISM kontrolü olarak çalıştırılabilir. | Python betiği ile API. | pytwist | sık (okundu) |
| PowerShell REST entegrasyonu | Windows PowerShell, sunucu otomasyonu'nın C# REST API kütüphanesini kullanır. | Windows yöneticisi otomasyonu. | powershellintegrationrest | sık (okundu) |
| PowerShell SOAP entegrasyonu | Eski yol; kullanımdan kaldırıldı. | Eski entegrasyon. | powershellsaintegration | seyrek (okundu, kullanımdan kaldırıldı) |
| sunucu otomasyonu CLI metotları | OGSH içinde OGFS'deki çalıştırılabilirler API metodunu çağırır; format specifier, value representation, arama filtresi ve örnek betikler. | Toplu ve tekrarlı işler. | cliconcepts, saclimethodtutorial, saclimethodparameters, searchfiltersandsacli | sık (okundu) |
| APX (Automation Platform Extensions) | Program APX (OGFS üzerinde script) ve Web APX (Apache, CGI veya PHP). Her APX'in tipi, benzersiz adı (ör. com.hpe.sa.RestartMyApp), görünen adı, sürümü ve dosya yapısı vardır. apxtool komutu, kullanıcı rolleri ve izinleri var. | Özel eklenti geliştirme ve çalıştırma. | automationplatformextensions, apxstructure, extensionmgmt | çekirdek (okundu) |
| Agent Tools | AGENTTOOLSPATH altındaki .sh, .bat ve Python betikleriyle sunucu özniteliği, custom field, customer ve custom attribute okunur veya değiştirilir. Sunucu tarafı betiklerde kullanılır. | Sunucu verisini betiğe taşıma. | agenttools | sık (okundu) |
| Pluggable checks | Audit kuralı geliştirme: check komut satırında oluşturulur, yüklenir ve audit policy'ye eklenir. Geliştirme ortamında kurulum önerilir. Gelişmiş pluggable check ayrı sayfa. | Özel uyum kuralı. | pluggablechecks, advancedpluggablechecks | seyrek (okundu) |
| CML şablonu | CML tag tipleri, type/range/global/regular option attribute'ları, sequence aggregation, partial template; /etc/hosts örneği; basit anahtar=değer ve tekrar eden değer kullanım durumları. | Config şablon yazma. | cmlprimer, cmlreference, cmlcreatetemplate | sık (okundu) |
| XML/DTD config şablonları | DTD tabanlı ve DTD'siz XML şablonları; element görüntüsünü özelleştirme; Travel Manager örneği. | XML config yönetimi. | managexmlconfigurationfiles | sık (okundu) |
| Sürüm düzeltmeleri (Fixed issues) | Kategoriye göre liste; örnekler: Server Patching paket remediation hatası (Missing Metadata); Ansible'da başka namespace'ten CA kullanımı, APX'e extra_vars girdisi, "Ansible Playbook" ve "Ansible Variables" betik türlerinin aramada görünmesi. | Sürüm riski takibi. | fixeddefects | çekirdek (okundu, kısmen) |
| Kurulum ve yükseltme planı | Tek host veya çok host core; multimaster mesh ve satellite. Yükseltmede veritabanı yükseltilmez; Oracle ile PostgreSQL arasında geçiş desteklenmez; standart core yükseltmesinde geri alma prosedürü yoktur, karmaşık kurulumlarda yedek planı önerilir. | Kurulum ve yükseltme öncesi karar. | install, upgradesa | çekirdek (okundu) |
| Sorun giderme (provisioning, kurulum) | Provisioning: Solaris x86 RHEL8/OEL8/CentOS8 core'da hata, maintenance mode, betik hatası, OS installer hatası, production agent Wait adımı. Kurulum: installer hatası, single-user modda remediation, Solaris yama hatası. | Arıza giderme. | troubleshootsaprovisioning, troubleshootsainstallation | sık (okundu) |

### 2.7 Üçüncü tur: yama, yazılım, audit, snapshot, provisioning, izin ve sorun giderme gövdeleri

Yöntem: Aynı TOC ve gövde yolu (`/419/25.4/<sayfa>/default-<revizyon>.json`, `parse.text` içindeki HTML). Bu turda gövdesi okunan satırlar "(okundu)" ile işaretli. Kaynak sütunu sayfa adlarıdır; kök https://docs.microfocus.com/doc/419/25.4/

| ozellik | ne_yapar | admin_isi | kaynak | agirlik |
|---|---|---|---|---|
| Windows yama politikası ve istisnalar (okundu) | Politika yamayı KB yerine Object ID ile tutar; yama istisnası (ör. Never Install) tekil sunucuya veya politikaya eklenir; politika seçenekleri kaldırmada onay mesajını yönetir. Offline Catalog (wsusscn2.cab) modunda "Windows Patch Installation Order" supplement yamalarının sırasını korur; WSUS modunda bu seçenek yoktur. | Politika ve istisna yönetimi; katalog modu seçimi. | windowspatchpolicyremediation, patchpolicyexception, patchpolicyoptions, addingitemstoawindow | çekirdek (okundu) |
| Windows yama kurulum zamanlama, önizleme ve bildirim (okundu) | Kurulum zamanlanır; Staged seçeneğiyle indirme ve kurulum ayrılır. Yeniden başlatma seçenekleri Patch Properties (Install Parameters) ve Remediate (Pre and Post Actions) adımlarında ayarlanır; Microsoft önerisi tercih edilir. Önizleme, iş ilerlemesi, bildirim ve kuruluma özel betik (install script) tanımlanır. | Bakım penceresi, yeniden başlatma planı. | schedulepatchinstallationremediation, setrebootoptionsremediationwindows, previewwindowspatchinstallation, jobprogresswindowspatch, emailnotificationsforwindowspatchinstallation, specifyinstallscriptswindows | çekirdek (okundu) |
| Windows yama kaldırma (okundu) | Kaldırma zamanlanabilir ya da hemen yapılabilir; önizleme ve iş ilerlemesi ayrı görünümlerde; bildirim ayrıca tanımlanır. | Kaldırma planı. | schedulewindowspatchuninstallation, previewstartwindowspatchuninstallation, jobprogresspatchuninstallation2, emailnotificationsforwindowspatchuninstallation | sık (okundu) |
| Windows yama uyum taraması ve kuralları (okundu) | Tarama hemen veya zamanlı başlatılır. Tek sunucu uyum kuralı: politikadaki bir öğe eşleşmiyorsa sunucu uyumsuzdur. Uyum seviyesi politika, istisna ya da ikisinin kapsamını belirler. Ikon tablosu uyum durumunu gösterir. | Uyum taraması planlama ve sapma tespiti. | startpatchcompliancescan, startpatchcompliancescanimmediately, patchcompliancescans, patchcompliancestatuscriteria, patchcompliancelevels, patchcompliancerules, patchcomplianceicons, patchcompliance | çekirdek (okundu) |
| Yama arama ve sunucu yama görünümü (okundu) | sunucu otomasyonu Client Search yama, politika ve sunucu arar. Sunucunun yamaları görünümü Windows Show seçenekleriyle filtrelenir. Yeni içe aktarılan yama "Limited" durumunda başlar; yalnız yetkili roller test eder. Yama kurulumu "Available" durum gerektirir. | Yama envanteri sorgusu. | patchpatchpolicysearch, patchesfortheserver, findserverswindowspatch, findserversnowindowspatch, supportforwindowspatch, installingapatch | sık (okundu) |
| Windows yama kurulum fazları ve bayrakları (okundu) | Kurulum iki faz: indirme (download) ve kurulum. Yama bayrakları (installation flags) Windows için sunucu otomasyonu varsayılanlarına ek olarak tanımlanır. | Kurulum akışı ve bayrak yönetimi. | patchinstallationwindows, installationflagswindows | çekirdek (okundu) |
| Windows sunucu görünümleri (okundu) | COM+ nesneleri ve Windows kayıt defteri salt okunur görünümde; kurulu paketler sunucu başına listelenir. | Sunucu içi tanı. | windowscomplusobjects, windowsregistry, installedpackages | seyrek (okundu) |
| Solaris yama politikası (okundu) | Solaris politikası oluşturulur, düzenlenir, yama ve küme/bundle eklenir. Politikadan çıkarma sunucudaki yamayı kaldırmaz. Politika geçmişi, ekli sunucular ve bağlı Build Plan'lar görülebilir. | Solaris politika yaşam döngüsü. | createsolarispatchpolicy, editsolarispatchpolicy, addsolarispatchtopatchpolicy, removepatchfromsolarispatchpolicy, viewingpatchpolicyhistory, viewingserversattached1, viewbuildplans, findsolarispatchpolicy, viewingasolarispatch, patchpolicymanagementsolaris, viewingsoftwarepolicies | sık (okundu) |
| Solaris yama kurulumu ve uyum (okundu) | Yama patchadd ile kurulur; patchadd ile kurulamayan firmware gibi yamalar elle kurulur. Yama kümeleri için Readme okunur ve gerekiyorsa passcode girilir. Install Mode Single User ise sunucu tek kullanıcı modunda yeniden başlatılır ve başarısızlıkta durum ayrıca izlenir. Offline volume ile kurulum örneği vardır. Uyum taraması politikaya göre yapılır. | Solaris yama uygulama ve sorun giderme. | installpatchsolaris, installpatchcluster, installmanualpatches, installpatchesusingofflinevolume, changesolarisinstallmode, remediatingserveragainstpatchpolicy, patchcompliancesolaris, runpatchcompliancescan, installpatchesusingpatchpolicy, uninstallingpatch | sık (okundu) |
| Solaris zone yönetimi (okundu) | Zone yamaları ve yönetimi; sunucu otomasyonu Client ile zone oluşturulursa agent otomatik kurulur. Mevcut non-global zone için agent kurulumu önkoşulu: zone çalışıyor olmalı. Zone bilgisi Solaris tarafında değişirse sunucu otomasyonu otomatik yeniler. | Zone yaşam döngüsü ve agent. | solariszones, osprovisioningagentinstallation, installingagentexistingunmanagednonglobalzone, reloadingoraclesolariszoneinformation | sık (okundu) |
| HP-UX yazılım ve yama politikası (okundu) | Katalog dosyası swa_catalog.xml (HP-UX Metadata betiği) ile yüklenir; HP-UX yazılım politikası oluşturulur, yama ve betik eklenir. Yama uyumu ve kurulumu indirme ve kurulum fazlarında yapılır. HP-UX yama kaldırma bu sürümde desteklenmez; yama doğrudan hedefte kaldırılır. Depot konteyner paketi (fileset içerir). | HP-UX politika ve katalog bakımı. | hpuxsoftwarecatalogfile, createhpuxsoftwarepolicy, viewinganhpuxsoftware, edithpuxsoftwarepolicy, addhpuxpatchsoftwarepolicy, patchcompliancehpux, patchinstallationhpux, patchuninstallationhpux, setrebootoptionshpux, hpuxpackages | niş (okundu) |
| Ubuntu/Debian yama politikası (okundu) | Statik ve dinamik politika; politika oluşturma, ekleme, bağlama, ayırma ve silme. Silme politikayı kaldırır, sunucudaki yamayı kaldırmaz; kullanımdaki politika silinemez. Remediation her yama için politika türüne göre çalışır; uyum doğrulaması ayrı. Ubuntu yama izinleri tek kullanıcıda birleşik (rol ayrımı yok). | Debian ailesi politika yönetimi. | policymanagementubuntu, ubunturemediationprocess, ubuntupatchingflows, createpatchpolicyubuntu, addpatchpolicyubuntu, attachpatchpolicyubuntu, detachpatchpolicyubuntu, deletepatchpolicyubuntu, remediatepatchpolicies, remediatepatchpolicydebian, verifyingpatchpolicycompliance, patchmanagementubuntupermissions | sık (okundu) |
| Ubuntu yama kurulum seçenekleri (okundu) | İndirme ve kurulum ayrı zamanlanabilir; hemen ya da ileri tarihte kurulum; önizleme; bildirim; iş ilerlemesi. Yeniden başlatma kuralları vendor önerisine göre; pre/post kurulum betikleri. | Ubuntu kurulum planı. | patchinstallationubuntu, installubuntupatch, setubuntuinstalloptions, scheduleubuntupatchinstallation, emailnotificationsforubuntupatchinstallation, previewubuntupatchinstallation, jobprogressubuntupatch, rebootoptionsubuntupatchinstallation, specifyinstallscriptsubuntu, preandpostinstallscriptsremediation | sık (okundu) |
| Ubuntu paket yönetimi (okundu) | Ubuntu paketleri .deb olarak içe aktarılır; paket özellikleri düzenlenebilir; paket hangi sunucularda kurulu, bulunup dışa aktarılabilir. | Paket envanteri. | ubuntupackages, editubuntupackageproperties, findubuntupackages, findserverubuntupackage, exportanubuntupackage, viewingubuntupackages | sık (okundu) |
| Red Hat, OEL ve SUSE kanal içe aktarma (okundu) | Red Hat içe aktarmada sertifikalar (RHN, RHSM, Hybrid Cloud Console) doğrulanır. OEL importer abone olunan kanalları içe aktarır. SUSE Manager importer (SLES 11 SP3 örneği) binary ile çalışır; sertifika `suse_manager_import` tarafından doğrulanır. | Kanal ve sertifika bakımı. | installredhatcacertificates, patchinstallationoel, suseimportermanager, installingsusemanagercacertificate | sık (okundu) |
| RPM dağıtımı ve remediation (okundu) | RPM bağımlılıklarını otomatik eklemeden dağıtma; YUM eklentisi analiz fazını yönetir; SUSE'de zypper analiz ve kurulum yapar. Dinamik yama politikası destekleyen platformlarda mrc_calc gerekmez. Politika RPM sürümünü otomatik güncelleyebilir. Kurulum ve yükseltme bayrakları ve Install Parameters paket özelliklerinden okunur. | RPM yaşam döngüsü. | rpmdeployment, remediatingobsoleterpmpackages, usingnativezypper, rpmremediationbp, automaticallyupdatingrpmssoftwarepolicy, upgradeoptionsforrpm, installuninstallflags, rpminstallationandupdate, uninstallingrpmpackages, installrpmmoduleadhoc | çekirdek (okundu) |
| Yazılım politikası ve remediation yardımcıları (okundu) | Politika kaynakları paket, yama, betik, AC ve sunucu nesneleridir. Kurulum sırası ve politika işi sırası türe göre belirlenir. Remediation üç fazlıdır (Analysis, Download, Remediate) ve aşamalar ayrı zamanlanabilir. Düşük disk alanında paket indirmeden önce kontrol yapılır; disk yetersizse indirme yapılmaz ve hata verilir. Politikasız kurulum/kaldırma ve önizleme ayrıdır. Betik metadatası karakter kodlamasına duyarlıdır. | Dağıtım tanımı ve hazırlık. | policybasedsoftwareinstallationmanagement, creatingsoftwarepoliciestemplates, specifyinginstallationuninstallationorder, policyordering, openingpolicyortemplate, remediatingandinstallingsoftware, installingsoftwareusingsoftwarepolicy, uninstallingsoftwareusingsoftwarepolicy, uninstallingsoftwarefromtheserverinventory, previewremediationjob, previewinstallationuninstallationjob, serverswithlowdiskspace, itemexpansionscheduled, allsoftwarepoliciesassociatedscript, viewingosbuildplans, characterencodingpackagemetadatascripts | çekirdek (okundu) |
| Remediation hata işleme, zaman aşımı ve iptal (okundu) | Hata işleme seçeneği: hatada devam etme veya atlama; yeniden başlatma ve pre/post betikler bu adımda seçilir. Zaman aşımı hata işleme ayarından bağımsızdır: çalışan iş belirlenen süre geçince durur. Remediation e-posta bildirimi ve iş durumu ayrıca izlenir. Zamanlanmış veya aktif kurulum, kaldırma, remediation işleri iptal edilebilir. | İş hata politikası. | specifyrebooterrorhandling, timeouthandlinginstallationuninstallation, scheduleremediationstages, setemailnotificationsremediation, runremediationviewjob, emailnotificationsforremediation, previewingandstartingremediation, cancellingscheduledinstallationuninstallationremediationjob, terminatingactiveinstallationuninstallationremediationjob | çekirdek (okundu) |
| Paket türleri (okundu, genişleme) | HP-UX depot, Solaris SVR4, Solaris 11 IPS, Windows MSI, Ubuntu .deb, RPM, AIM ZIP paketleri ayrı kurallarla işlenir. Windows yükleme performansı için TCP ayarı önerilir. | Paket türü seçimi. | hpuxpackages, priortosolaris11, solaris11packages, windowspackages, rpmpackages, applicationinstallationmediapackages, windowsperformanceuploadingpackages | sık (okundu) |
| Agent kaldırma (okundu) | UNIX için root, Windows için Administrator ile agent kaldırılır. | Agent yaşam döngüsü. | uninstallagentunixwindows | sık (okundu) |
| Application Configuration uyum ve audit (okundu) | AC uyumu: attach edilen yapılandırma değerleri sunucudaki dosya değerleriyle karşılaştırılır (Compliant, Out of Sync). Audit ile yapılandırma dosyası şablona göre denetlenir. AC bir politika içinde ideal durum olarak kullanılabilir. Şablon ve betik sırası belirlenebilir. Özel öznitelik ikamesi (customAttributeSubstitution) iş değerlerini sunucuya göre değiştirir. | Config sapma denetimi. | applicationconfigurationcompliance, auditapplicationconfigurations, useapplicationconfigurationsinsoftwarepolicies, addremovetemplates, specifytemplateorder, customattributesubstitutionswmgmt | çekirdek (okundu) |
| Audit remediation aksiyonları ve iptal (okundu) | Düzeltme sonunda özel betik çalıştırılabilir; reboot aksiyonu tüm kural düzeltmelerinden sonra çalışır. Aktif audit veya remediate audit sonucu işleri sonlandırılabilir. ESXi audit'leri entegrasyon kullanıcısı ve PowerCLI betikleriyle çalışır. Raporlama Operations Bridge Reporter'a bırakılır. | Audit düzeltme ve sonlandırma. | customscriptsremediateaction, configurerebootremediateaction, cancellinganactiveremediateauditresultsjob, cancellingactiveauditjob1, windowsvmwareesxiauditfunctions, aboutsoftwarepolicyreports | sık (okundu) |
| Snapshot zamanlama ve iptal (okundu) | Snapshot, sunucunun belirli andaki yapılandırmasını yakalar; spec tek sefer veya tekrarlı job olarak çalıştırılır. Zamanlama düzenlenir, silinir ve aktif snapshot işi iptal edilebilir. | Yapılandırma geçmişi. | snapshotssnapshotspecificationssnapshotjobs, snapshotjobs, schedulingrecurringsnapshotjob, vieweditsnapshotjobschedule, deletesnapshotjobschedule, cancelactivesnapshotjob | sık (okundu) |
| Provisioning boot server ve platform adımları (okundu) | sunucu otomasyonu Installer boot server'ı ve dhcpd bileşenini kurar. Debian 11/12, SLES 15 (Installer DVD ve paket DVD ayrı), SLES 16 (SLES 15'ten farklar), Windows Server 2012 R2 x64 network boot ve Solaris 11.1 x86 adımları ayrı sayfalarda. | Bare metal provisioning hazırlığı. | dhcpsoftwarebootserver, provisioning_debian_11, provisioningdebian12x8664, provisioningsuseenterpriselinuxserver15x8664, provisioningsuseenterpriselinuxserver16x8664, provisioningwindowsbasedservers, provisioningsolarisx86basedservers | sık (okundu) |
| Provisioning ve kurulum sorun giderme alt sayfaları (okundu, 12) | Sorun giderme sayfaları: kurulumu yeniden başlatma, staging dizini bağlama, Solaris install mode, Solaris provisioning, SMTool upload, recurring AC token ömrü, maintenance mode, ProLiant Gen8, OS installer ve Wait hataları, NGUI launcher. Her biri belirti, neden ve çözümü sıralar. | Arıza giderme. | restartinstall, mountingstagingdirectory, changesolarisinstallmode, solarisprovisioningfails, smtuploadfails, recurringappconfig, maintenancemode, proliantgen8, failurebeforeosinstalls, failureofosinstaller, failurewhenwaiting, nguilauncher | sık (okundu) |
| Core komut ve araçları (okundu) | cascade: yabancı anahtar üzerinden nesne hiyerarşisini dolaşır. check_way_obj_sigs: imzalı nesneleri kriptografik doğrular. clear_conflicts: çakışma raporlayan işlem tablolarını sıfırlar. compare_db: DB şema ve yetki bilgisini karşılaştırır. caMigrate: özel öznitelik verisini kaydeder ve geri yükler. coreServerCount: core'un yönettiği sunucu sayısını sayar. | Veri bütünlüğü ve bakım öncesi-sonrası doğrulama. | cascade, checkwayobjsigs, clearconflicts, comparedb, camigrate, coreservercount | seyrek (okundu) |
| cora (core bilgi arşivi) (okundu) | Core hakkında bilgi toplar, arşivler ve görüntüler. | Destek veri paketi. | cora | sık (okundu) |
| DET (cbt) ve DCML (okundu) | cbt, seçilen içeriği RDF/XML olarak dışa aktarır; hedef mesh'te içe aktarılabilir. cbtperm DET kullanım iznini verir. Çıktı DCML Framework v0.11 ile uyumludur. | Mesh arası içerik taşıma. | detusage, detcommands, detpermissionscommand, relationshiptodcml, dcml | seyrek (okundu) |
| ISM ve IDK komutları (okundu) | ISMTool --build ve --upload ISM dizinini paketler ve yükler. ISM betikleri Unix shell veya Windows komut satırında yazılır. ISM Control işi yönetilen sunucuda çalışır ve politikalara bağlanabilir. | Özel yazılım paketi üretme. | idkbuild, idkscripts, idkcommands, ismcontrolsreference, runningismcontrols, ismcontrolsinpolicies | seyrek (okundu) |
| İzin modeli: eylem, kaynak, klasör, OGFS (okundu) | Bir eylem için kullanıcı hem eylem hem kaynak iznine sahip bir gruba üye olmalıdır. Klasör izinleri sunucu otomasyonu Library klasörlerindeki politika ve şablonlara erişimi denetler. OGFS izni eylem izninden ayrıdır ve ilişkilidir. Grup izinleri ayarı ayrı bir süreçtir. | Rol ve izin tasarımı. | permissiontypesactionresourcefolder, aboutactionpermissions, aboutresourcepermissions, aboutfolderpermissions, globalfilesystempermissions, settingpermsusergroups | çekirdek (okundu) |
| Alan bazlı izin tabloları (okundu) | Sunucu nesnesi, sunucu özelliği ve yeniden başlatma, cihaz grubu, agent kurulumu, sanallaştırma, OS provisioning, yazılım, Chef, AC, Windows/Ubuntu/Solaris/UNIX yama, Solaris politika, audit ve remediation, uyum görünümü, iş, betik ve akış otomasyonu flow izinleri. Satellite yönetimi "Manage Gateway" iznine bağlıdır (varsayılan sunucu otomasyonu System Admin grubunda). CRL etkinleştirme/devre dışı için ayrı izinler gerekir. | Rol-izin eşlemesi. | permissionsreference, serverobjectspermission, serverpropertyrebootpermissions, devicegrouppermissions, serveragentdeploymentpermissions, virtualizationservicemanagementpermissions, osprovisioningpermissions, softwaremanagementpermissions, chefcookbookmanagementpermissions, appconfigurationmanagementpermissions, patchmanagementwindowspermissions, patchmanagementsolarispermissions, solarispatchpolicymanagementpermissions, patchmgmtotherunixpermissions, auditremediationpermissions, complianceviewpermissions, jobpermissions, scriptexecutionpermissions, flowpermissionshpoo, permissionsformanagingsatellites, crloperationspermissions | çekirdek (okundu) |

## 3. Bir otomasyon ajanının karşılaması gereken yetenekler

Envanterden türetilmiş, tekrarsız liste. Her madde ilgili özelliğe işaret eder. Örnek talep cümleleri operatörün bir ajana verebileceği istekleri temsil eder.

1. Kullanıcı oluşturma ve parola sıfırlama. Özellik: Kullanıcı yönetimi. Örnek: "Ayşe adında yeni bir sunucu otomasyonu kullanıcısı aç ve Patch Operators grubuna ekle."
2. Kullanıcıyı gruptan çıkarma. Özellik: Kullanıcı grupları. Örnek: "Mehmet'i Patch Operators grubundan çıkar."
3. Kullanıcı grubu oluşturma ve kopyalama. Özellik: Kullanıcı grupları. Örnek: "Web ekibi grubunu, Sistem ekibi grubunun kopyası olarak oluştur."
4. Grup için eylem izni verme. Özellik: Grup izinleri. Örnek: "Patch Operators grubuna yalnız yama kurulumu izni ver, politika düzenleme izni verme."
5. Grup için OGFS izni verme. Özellik: Grup izinleri (OGFS). Örnek: "Web grubu yalnız /opsw/Server/web01 altında okuma yapabilsin."
6. Süper yönetici atama ve kaldırma. Özellik: Süper yöneticiler. Örnek: "Kemal'e süper yönetici yetkisi ver."
7. Müşteri oluşturma ve müşteri grubuna bağlama. Özellik: Müşteri yönetimi. Örnek: "Müşteri A için yeni bir müşteri oluştur ve sunucu grubunu bağla."
8. Parola politikası ayarlama. Özellik: Parola, hesap ve oturum politikaları. Örnek: "Parola süresini 90 güne çıkar, son beş parolanın tekrarını yasakla."
9. Pasif hesabı askıya alma. Özellik: Hesap politikası. Örnek: "90 gündür giriş yapmayan hesapları askıya al."
10. LDAP kullanıcı içe aktarma. Özellik: LDAP entegrasyonu. Örnek: "LDAP grubundaki kullanıcıları sunucu otomasyonu'ya içe aktar."
11. Kullanıcı ve güvenlik raporu üretme. Özellik: Kullanıcı ve güvenlik raporları. Örnek: "Tüm sunucularda hangi grubun hangi izne sahip olduğunu raporla."
12. Denetim izini dışa aktarma. Özellik: Sıkı denetim, Global Shell denetim logları. Örnek: "Son 30 günde hangi kullanıcı hangi sunucuda shell komutu çalıştırdı?"
13. Core sertifika yenileme durumunu kontrol etme. Özellik: Core recertification. Örnek: "Core sertifika süresinin dolmasına 30 gün kaldığında uyar ve Simplified recertification planla."
14. Agent recertification çalıştırma. Özellik: Agent recertification. Örnek: "Eski sürüm agent'ları yeniden sertifikala."
15. Mesh durumunu sorgulama. Özellik: Multimaster mesh durumu. Örnek: "Mesh'te bekleyen veya çakışan işlem var mı?"
16. Mesh çakışması çözme. Özellik: Mesh çakışma çözme, force_resolve. Örnek: "Mesh çakışmalarını otomatik çözmeyi dene ve sonucu raporla."
17. Mesh e-posta uyarı alıcısı ayarlama. Özellik: Mesh e-posta uyarıları. Örnek: "Mesh uyarılarını ops-alias listesine gönder."
18. Satellite başlatma, durdurma, yeniden başlatma. Özellik: Satellite yönetimi. Örnek: "Ankara satellite'ini yeniden başlat ve gateway bağlantısını doğrula."
19. Satellite iletişimini doğrulama. Özellik: Satellite iletişim doğrulama. Örnek: "İzmir satellite'inin core ile iletişimini test et."
20. Satellite bant genişliği ayarlama. Özellik: Bant genişliği (BCM). Örnek: "İzmir bağlantısı için bant genişliğini 2 Mbit ile sınırla."
21. Satellite yazılım önbelleği yönetimi. Özellik: Satellite depo önbelleği. Örnek: "Satellite önbelleğini tam mirror moduna al."
22. Peer content cache kurma. Özellik: Peer content caching. Örnek: "Küçük şube için bir peer cache kur ve sunucuları ona bağla."
23. Yazılım deposu mirror ayarını değiştirme. Özellik: Depo mirror ayarı. Örnek: "Yalnız Frankfurt tesisinde yazılım deposu aynalamasını kapat."
24. Audit sonucu ve snapshot temizliği zamanlama. Özellik: Audit temizliği. Örnek: "Otuz günden eski audit sonuçlarını her gece temizle."
25. Bileşen sağlık denetimi çalıştırma. Özellik: HCM ve sistem tanılama. Örnek: "Core sağlık denetimini çalıştır ve başarısız testleri listele."
26. Servis başlatma, durdurma, durum sorgulama. Özellik: Start/Stop script. Örnek: "Tüm core bileşenlerinin durumunu göster ve Command Engine'i yeniden başlat."
27. Log seviyesini geçici yükseltme. Özellik: Bileşen log seviyesi. Örnek: "Command Engine log seviyesini 30 dakikalığına DEBUG yap."
28. Oturum (session) verisi çıkarma. Özellik: dump_session. Örnek: "Son 24 saatte başarısız olan iş oturumlarını dök."
29. Core içinde veri bütünlüğü onarımı. Özellik: fixOrphanedUnits, fixOrphanedAgentDevice, fixDeviceRealm. Örnek: "Yetim yazılım birimlerini tespit et ve düzelt."
30. Cihaz gerçeklik (realm) düzeltme. Özellik: fixDeviceRealm. Örnek: "Sunucu 1234'ün realm bilgisini doğru facility'ye taşı."
31. Dinamik cihaz grubu kurallarını analiz etme. Özellik: dgDump, dgOptimizer, dgUsage. Örnek: "Hangi dinamik grup CONTAINS kuralı kullanıyor, optimize et."
32. Sunucu sayısını sayma. Özellik: coreServerCount. Örnek: "Bu core'a bağlı sunucu sayısını say."
33. Mesh'ler arası içerik dışa aktarma. Özellik: DET (cbt) export. Örnek: "Prod mesh'in Patch politikalarını RDF/XML olarak dışa aktar."
34. Delta senkronizasyonu. Özellik: DET delta export/import. Örnek: "Yalnız değişen içeriği DR mesh'ine delta olarak aktar."
35. Özel yazılım paketi (ISM) oluşturma. Özellik: IDK. Örnek: "Kurumsal ajan için yeni bir ISM paketi oluştur ve yükle."
36. Core CLI ile nesne sorgulama ve değiştirme. Özellik: OCLI (cli). Örnek: "Tüm sunucu nesnelerini CLI ile listele, filtre uygula."
37. Yapılandırma sonrası düşük seviyeli doğrulama. Özellik: compare_db, check_way_obj_sigs. Örnek: "DB şema ve yetki farklarını karşılaştır."
38. Yazılım çakışma ve yetim kayıt temizliği. Özellik: deletePlatformUnits, fixSatelliteMirrorSync. Örnek: "Satellite'in gereksiz yazılımlarını temizle."
39. Sunucu/cihaz izni kontrolü. Özellik: İzin referansları. Örnek: "Yama politikası oluşturmak için hangi izinler gerekli?"
40. Kullanıcı ve grup yetki kontrolü. Özellik: Grup izinleri. Örnek: "Grup X hangi eylemleri yapabiliyor, listele."
41. Agent kurma (ADT ile). Özellik: Agent yönetimi. Örnek: "Bu 20 sunucuya agent kur, WSUS bağlantısını kullan."
42. Agent kurma (CLI ile). Özellik: CLI agent kurulumu. Örnek: "Sunucu listesinde üçüncü taraf modunda agent kur."
43. Agent yükseltme. Özellik: Agent yükseltme. Örnek: "Tüm Linux agent'larını en son sürüme yükselt."
44. Agent kaldırma. Özellik: Agent kaldırma. Örnek: "Bu sunucudan agent'ı kaldır."
45. Agentsız sunucu keşfi. Özellik: Agentsız keşif. Örnek: "Subnet 10.0.5.0/24 üzerinde agentsız sunucuları tara."
46. Agent sorun giderme. Özellik: Agent tanı ve iletişim testi. Örnek: "Sunucu 77 için iletişim testini çalıştır ve hatayı raporla."
47. Sunucu envanteri sorgusu. Özellik: Sunucu ve cihaz grubu envanteri. Örnek: "Tüm Windows 2019 sunucularının IP ve yama durumunu listele."
48. Cihaz grubu oluşturma. Özellik: Statik ve dinamik cihaz grupları. Örnek: "Tüm Prod RHEL 8 sunucularını içeren dinamik bir grup oluştur."
49. Özel alan ve özellik ekleme. Özellik: Custom field/attribute. Örnek: "Sunuculara 'owner' özel alanı ekle ve değerlerini doldur."
50. Extensible discovery çalıştırma. Özellik: Extensible discovery. Örnek: "Tüm sunucularda özel keşif betiğini çalıştır."
51. Script oluşturma ve çalıştırma. Özellik: Script yürütme. Örnek: "Tüm web sunucularında disk kullanımını ölçen betiği çalıştır."
52. Global Shell ile dosya okuma. Özellik: OGFS ve rosh. Örnek: "web01 sunucusunda /etc/hosts içeriğini oku."
53. Global Shell ile komut çalıştırma. Özellik: Global Shell. Örnek: "Dört web sunucusunda uptime komutunu çalıştır."
54. Windows yama tarama. Özellik: Windows yama yönetimi. Örnek: "Üretimdeki Windows sunucularında eksik kritik yamaları tara."
55. Windows yama politikası uygulama. Özellik: Windows yama politikası. Örnek: "Ayın ikinci Salı yamasını Test grubuna uygula."
56. Linux (RHEL) yama uyumu. Özellik: Red Hat yama. Örnek: "RHEL sunucularında errata uyumunu raporla."
57. SUSE yama uyumu. Özellik: SUSE yama. Örnek: "SUSE channel tabanlı politikayı tüm sunuculara uygula."
58. Solaris yama kurulumu. Özellik: Solaris yama. Örnek: "Solaris 11 sunucuları için yama tarama çalıştır."
59. Ubuntu/Debian yama uyumu. Özellik: Ubuntu/Debian yama. Örnek: "Ubuntu 22.04 sunucularında eksik güvenlik güncellemelerini listele."
60. Unix yama kaldırma. Özellik: Unix yama kaldırma. Örnek: "HP-UX sunucusundan yama KB123'ü kaldır."
61. Audit kuralı oluşturma ve çalıştırma. Özellik: Audit ve uyum. Örnek: "CIS sıkılaştırma kurallarını Prod grubunda audit et."
62. Audit sonucunu düzeltme. Özellik: Audit remediation. Örnek: "Audit'te başarısız olan sunucularda düzeltmeyi başlat."
63. Snapshot oluşturma ve karşılaştırma. Özellik: Snapshot. Örnek: "Web sunucularının bugünkü yapılandırmasının snapshot'ını al ve dünkü ile karşılaştır."
64. Uyum panosu özeti. Özellik: Uyum panosu. Örnek: "Yama, audit ve yazılım uyum oranlarını tek özet olarak ver."
65. Sunucu yapı planı çalıştırma (provisioning). Özellik: sunucu otomasyonu Provisioning. Örnek: "Yeni bir Linux sunucuyu standart build plan ile kur."
66. UEFI Secure-Boot provisioning. Özellik: UEFI Secure Boot. Örnek: "UEFI sunucuya güvenli önyüklemeli Linux kur."
67. Yazılım politikası oluşturma. Özellik: Software policy. Örnek: "Nginx 1.26 için yazılım politikası oluştur ve Web grubuna bağla."
68. Yazılım kurma ve kaldırma. Özellik: Yazılım yönetimi. Örnek: "Üç sunucuda Java 17 politikasını uygula, eski Java'yı kaldır."
69. Yazılım kurulumunu zamanlama ve iptal etme. Özellik: Yazılım zamanlama. Örnek: "Gece 02:00'de yazılım kurulumunu zamanla, planlananı iptal et."
70. Paket içe aktarma. Özellik: Paket yönetimi. Örnek: "Bu RPM paketini sunucu otomasyonu kütüphanesine içe aktar."
71. Düşük disk alanında kurulum. Özellik: Yazılım yönetimi. Örnek: "Disk alanı az olan sunucuya paketi kurmadan önce uyar."
72. VM oluşturma ve şablondan dağıtma. Özellik: Sanallaştırma. Örnek: "vCenter'da Ubuntu şablonundan 3 VM oluştur."
73. VM güç ve yaşam döngüsü işlemleri. Özellik: Sanallaştırma VM yönetimi. Örnek: "Test VM'lerini kapat ve askıya al."
74. VM şablonu yönetimi. Özellik: Sanallaştırma şablonları. Örnek: "VM'i şablona dönüştür ve eski şablonu sil."
75. Solaris zone yönetimi. Özellik: Solaris zone. Örnek: "Solaris host üzerinde yeni bir non-global zone oluştur."
76. Application Configuration şablonu oluşturma. Özellik: Application Configuration. Örnek: "/etc/hosts şablonunu CML ile oluştur ve Web grubuna ekle."
77. Application Configuration itme ve zamanlama. Özellik: Application Configuration push. Örnek: "Yapılandırmayı gece 01:00'de tüm web sunucularına it."
78. Yapılandırma geri alma. Özellik: Geri yükleme. Örnek: "web02 üzerindeki nginx.conf'u bir önceki sürüme döndür."
79. Yapılandırma karşılaştırma. Özellik: Application Configuration karşılaştırma. Örnek: "Şablon ile web05 üzerindeki yapılandırmayı karşılaştır."
80. Değer kümesi (value set) yönetimi. Özellik: Value set. Örnek: "Ortama göre farklı değer kümesi tanımla ve uygula."
81. Chef cookbook çalıştırma (25.4'te kullanımdan kaldırıldı). Özellik: Chef entegrasyonu. Örnek: "Üretimde bu Chef tarifini çalıştır." Not: 25.4'te Chef entegrasyonu deprecated.
82. Ansible playbook çalıştırma. Özellik: Ansible playbook. Örnek: "Web gruplarında nginx.yml playbook'unu çalıştır."
83. Ansible değişken tanımlama. Özellik: Ansible değişkenleri. Örnek: "Playbook değişkeni http_port'u 8443 yap."
84. akış otomasyonu akışı ile sunucu otomasyonu işlemi çalıştırma. Özellik: akış otomasyonu entegrasyonu. Örnek: "akış otomasyonu akışında sunucu otomasyonu yama işini başlat ve sonucu raporla."
85. Bir işi bloklama. Özellik: İş bloklama (akış otomasyonu entegrasyonu). Örnek: "Bakım penceresinde yama işlerini blokla."
86. uCMDB'ye veri gönderme. Özellik: uCMDB connector. Örnek: "sunucu otomasyonu sunucu verisini uCMDB'ye gönder ve durumunu göster."
87. uCMDB connector başlatma ve durdurma. Özellik: uCMDB connector yönetimi. Örnek: "uCMDB connector'ı ikinci core'da başlat."
88. MPc içerik indirme ve içe aktarma. Özellik: MPc. Örnek: "Güvenlik stream'indeki yeni içeriği indir ve içe aktar."
89. Operations Platform ile entegrasyon. Özellik: OP entegrasyonu (26.1 atfı). Örnek: "sunucu otomasyonu metadata'sını Operations Platform'a içe aktar."
90. OPTIC Reporting ile rapor. Özellik: DCA OPTIC Reporting. Örnek: "sunucu otomasyonu geçmişinden aylık yama uyum trendini BVD'de göster."
91. sunucu otomasyonu Client raporu çalıştırma. Özellik: sunucu otomasyonu Client raporları. Örnek: "Son 30 günün yama raporunu çalıştır, parametreleri değiştir."
92. REST API ile sunucu sorgusu. Özellik: REST API. Örnek: "REST ile sunucu otomasyonu'dan tüm sunucuları JSON olarak al."
93. Pytwist ile Python otomasyonu. Özellik: Pytwist. Örnek: "Python betiğiyle 100 sunucuda cihaz grubu ata."
94. PowerShell ile sunucu otomasyonu sorgusu. Özellik: PowerShell entegrasyonu. Örnek: "PowerShell ile sunucu otomasyonu'da bağlı Windows sunucularını listele."
95. APX geliştirme. Özellik: APX. Örnek: "Yerel bir Web APX oluştur ve test ortamında çalıştır."
96. CML ile yapılandırma şablonu yazma. Özellik: CML. Örnek: "Basit anahtar=değer dosyası için CML şablonu yaz."
97. XML/DTD yapılandırma şablonu. Özellik: XML şablonları. Örnek: "XML tabanlı uygulama yapılandırmasını DTD ile şablonlaştır."
98. Ayrı mesh'ler arası DET içe aktarma. Özellik: DET import. Örnek: "Dışa aktarılan filtreyi hedef mesh'e içe aktar, çakışmada 'skip' politikası uygula."
99. Yazılım paketi için ISM üretme. Özellik: IDK. Örnek: "Kurumsal bir ISM paketi üret ve yükle."
100. Core yedekleme ve geri yükleme planlama. Özellik: Yedekleme en iyi uygulamaları. Örnek: "Core yedekleme planını doğrula ve geri yükleme prosedürünü özetle."
101. HA kurulumu ve kontrolü. Özellik: HA. Örnek: "HA çiftinin durumunu ve veritabanı yapılandırmasını doğrula."
102. Bulut agent'ı yönetme. Özellik: Public cloud agent'ları. Örnek: "AWS EC2 örneklerine agent kur."
103. Bildirim yapılandırma. Özellik: sunucu otomasyonu bildirimleri. Örnek: "Başarısız yama işlerinde e-posta bildirimi ayarla."
104. Facility (tesis) tanımlama. Özellik: Tesis yönetimi. Örnek: "Yeni bir İzmir tesisi oluştur ve satellite'i bağla."
105. Sistem tanılama çalıştırma. Özellik: Sistem tanılama. Örnek: "Prod core için sistem tanılamasını çalıştır, başarısız testleri raporla."
106. Core log arşivi toplama. Özellik: cora. Örnek: "Destek vakası için core bilgi arşivi oluştur."
107. Destek paketi toplama. Özellik: Destek araçları. Örnek: "Vaka için destek verilerini topla."
108. Patch oluşturma ve kaldırma sonrası temizlik. Özellik: Windows yama temizliği. Örnek: "Eski Windows yama kayıtlarını temizle."
109. Yama kurulumu sonrası yeniden başlatma. Özellik: Sunucu yeniden başlatma izni ve yama. Örnek: "Kurulum sonrası sunucuyu otomatik yeniden başlatma seçeneğiyle yama uygula."
110. Yönetilen platform uygunluğu kontrolü. Özellik: Yönetilen platform desteği. Örnek: "Bu sunucunun işletim sistemi sunucu otomasyonu 25.4'te destekleniyor mu?"
111. Dinamik cihaz grubu kuralı ekleme ve yeniden hesaplama. Özellik: Dinamik cihaz grupları. Örnek: "Adı 'pro' ile başlayan sunucular için dinamik grup kuralı ekle ve üyeleri yeniden hesapla."
112. Dinamik grubu statiğe çevirme. Özellik: Dinamik grubu statiğe çevirme. Örnek: "Prod-Web dinamik grubunu, o anki üyeleriyle statik gruba çevir."
113. Statik grupta üye ekleme ve çıkarma. Özellik: Statik cihaz grubu. Örnek: "web05'i Prod-Web statik grubundan çıkar."
114. Betiği belirli runtime kullanıcıyla çalıştırma. Özellik: Run Script seçenekleri. Örnek: "Disk kullanım betiğini tüm Linux sunucularda root olarak çalıştır, çıktıyı dışa aktar."
115. Betiği sunucuya özel özniteliklerle çalıştırma. Özellik: Betik özel öznitelik ikamesi. Örnek: "Betikteki {{environment}} alanını her sunucunun 'environment' özniteliğiyle doldurup çalıştır."
116. Salt okunur betikleri paralel çalıştırma. Özellik: Betik paralelliği (way.server_script.run_read_only_scripts_in_parallel). Örnek: "Değişiklik yapmayan envanter betiklerini aynı anda çalıştır."
117. Sunucuda tek komutu rosh ile çalıştırma. Özellik: rosh ve Global Shell. Örnek: "web01'de rosh ile /etc/hosts içeriğini oku ve dört sunucuda uptime çalıştır."
118. Uzak terminal oturumu açma. Özellik: Remote terminal. Örnek: "web01 için UNIX terminal penceresi aç."
119. Windows yamasını indirme ve kurulumu ayrı zamanlama. Özellik: Windows yama kurulumu zamanlama. Örnek: "Yamayı gece indir, ikinci Salı bakım penceresinde kur."
120. Windows yama istisnası ekleme. Özellik: Windows yama politikası istisnası. Örnek: "KB123456 için Never Install istisnası ekle ve bu istisnanın etkisini raporla."
121. Yama uyum seviyesi belirleme. Özellik: Windows yama uyumu. Örnek: "Üretim grubunda uyum seviyesini kritik yamalara göre ayarla."
122. Ubuntu yama politikası uygulama. Özellik: Ubuntu/Debian yama. Örnek: "Ubuntu 22.04 sunucularına statik ve dinamik yama politikasını uygula."
123. Red Hat errata ve kanal içe aktarma. Özellik: Red Hat errata yönetimi. Örnek: "Red Hat kanalındaki yeni errata'ları içe aktar ve uyum taraması çalıştır."
124. Solaris 11 IPS paketi yönetimi. Özellik: Solaris yama ve IPS. Örnek: "Solaris 11 sunucularında eksik IPS paketlerini listele ve kur."
125. Yazılım politikasında RPM güncelleme veya RPM modülü yönetimi. Özellik: RPM ve RPM modülü. Örnek: "Nginx RPM'lerini politika ile otomatik güncelle; nodejs modülünü etkinleştir."
126. Politikasız paket kurma veya kaldırma. Özellik: Politikasız kurulum/kaldırma. Örnek: "Üç sunucudan eski Java paketini politika olmadan kaldır."
127. Audit istisnası ekleme (geçici veya kalıcı). Özellik: Audit kuralı istisnası. Örnek: "IIS kuralı için üç sunucuda 30 gün geçici istisna tanımla."
128. Özel betik audit kuralı yapılandırma. Özellik: Custom scripts rule. Örnek: "Kendi kontrol betiğimi audit kuralı olarak ekle ve düzeltme eylemini tanımla."
129. Uyum eşiği ayarlama. Özellik: Compliance status thresholds. Örnek: "Device group uyum eşiğini yüzde 95 olarak ayarla."
130. Snapshot spesifikasyonu oluşturma, kaydetme ve dışa aktarma. Özellik: Snapshot spesifikasyonu. Örnek: "Web sunucularının yapılandırmasını snapshot spec olarak kaydet, audit policy'e çevir ve dışa aktar."
131. Build plan kopyası oluşturup düzenleme. Özellik: Build plan. Örnek: "RHEL 9 baseline build plan'ı kopyala, ek paket adımı ekle; orijinali değiştirme."
132. Provisioning için DHCP yapılandırma. Özellik: sunucu otomasyonu DHCP. Örnek: "Yeni lokasyon için sunucu otomasyonu DHCP IPv4 yapılandırmasını hazırla."
133. Application Configuration push'unu tekrarlı zamanlama. Özellik: App Config push zamanlaması. Örnek: "Nginx yapılandırmasını her gün 01:00'de web gruplarına it."
134. Ansible playbook'u id ile çalıştırma. Özellik: Ansible Runner APX. Örnek: "Seçili sunucularda playbook id 42'yi çalıştır; hosts değişkenini linux_servers olarak ayarla."
135. Ansible host değişkeni ekleme. Özellik: Ansible değişkenleri. Örnek: "web01 için Ansible namespace'inde http_port özniteliği ekle."
136. İş sonuçlarında adım içi arama ve filtreleme. Özellik: Job log. Örnek: "Son başarısız yama işinde FAILED geçen adımları bul."
137. Çalışan işi sonlandırma. Özellik: Aktif iş sonlandırma. Örnek: "Bakım penceresi aşan yama işini durdur ve kalan fazları iptal et."
138. REST API ile token alma ve sorgu. Özellik: REST API. Örnek: "REST ile token al ve tüm sunucuların listesini JSON olarak çek."
139. Pytwist ile sunucu sorgusu ve düzenleme. Özellik: Pytwist ServerService. Örnek: "findServerRefs ile Windows 2019 sunucularını bul ve getServerVO ile özet çıkar."
140. PowerShell'den REST ile sunucu sorgusu. Özellik: PowerShell REST entegrasyonu. Örnek: "PowerShell ile sunucu otomasyonu'da bağlı Windows sunucularını listele."
141. sunucu otomasyonu CLI metoduyla arama filtresi kullanma. Özellik: sunucu otomasyonu CLI metotları. Örnek: "CLI ile adı 'web' içeren sunucuları filtreli listele."
142. Program APX ve Web APX oluşturma ve çalıştırma. Özellik: APX. Örnek: "Gelen istekleri OGFS betiğiyle işleyen bir Program APX yaz ve apxtool ile yükle."
143. Agent Tools ile sunucu özniteliği okuma. Özellik: Agent Tools. Örnek: "Sunucunun customer ve custom attribute bilgisini get_info ile çekip betiğe ver."
144. Pluggable check yükleme ve audit policy'ye ekleme. Özellik: Pluggable checks. Örnek: "Geliştirilen özel check'i yükle ve CIS-özel audit policy'ye ekle."
145. CML veya XML şablonu yazma. Özellik: CML ve XML config şablonları. Örnek: "Basit anahtar=değer dosyası için CML şablonu yaz; tekrar eden değerler için sequence aggregation kullan."
146. Yükseltme öncesi yedek planı hazırlama. Özellik: Kurulum ve yükseltme planı. Örnek: "Core yükseltmesi öncesi yedek ve geri dönüş planını çıkar; standart yükseltmede geri alma olmadığını not et."
147. Provisioning arızasını teşhis etme. Özellik: Provisioning sorun giderme. Örnek: "Solaris x86 provisioning hatasını RHEL8 core sınırlamasına göre sınıflandır."

148. Windows yama öğesini KB yerine Object ID ile ekleme. Özellik: Windows yama politikası. Örnek: "KB numarası yerine Object ID ile politikaya yama ekle; aynı KB'nin iki kaydı çakışmasın."
149. Offline Catalog modunda yama sırasını koruma. Özellik: Windows Patch Installation Order. Örnek: "wsusscn2.cab yamalarını ve supplement yamalarını doğru sırada kur."
150. Windows yama kaldırmayı zamanlama ve önizleme. Özellik: Windows yama kaldırma. Örnek: "KB123456 kaldırmasını yarın 03:00'e planla, önce önizleme yap."
151. Tekil sunucu veya grup için hemen uyum taraması başlatma. Özellik: Yama uyum taraması. Örnek: "Web grubunda hemen yama uyum taraması çalıştır ve uyumsuzları listele."
152. Uyumsuzluk nedenini açıklama. Özellik: Tek sunucu uyum kuralı. Örnek: "Sunucu 77 neden uyumsuz; politika öğesi mi eşleşmiyor, istisna mı çakışıyor, açıkla."
153. Solaris politikadan yama çıkarırken sunucu etkisini bildirme. Özellik: Solaris politika düzenleme. Örnek: "Yamayı Solaris politikasından çıkar; sunucudaki yamanın kalıp kalmadığını raporla."
154. Solaris yamasını tek kullanıcı modunda kurma ve hata durumunu yönetme. Özellik: Install Mode. Örnek: "Solaris yamasını tek kullanıcı modunda kur; başarısızlıkta sunucu durumunu raporla."
155. patchadd ile kurulamayan Solaris yamasını manuel akışla ele alma. Özellik: Manuel Solaris yama. Örnek: "Firmware yamasını yönetici talimatıyla kur; sunucu otomasyonu'da bu adımın otomatik olmadığını not et."
156. Solaris yama kümesinin Readme ve passcode gereksinimini kontrol etme. Özellik: Solaris yama kümesi. Örnek: "Yama kümesi için Readme'yi çıkar; passcode gerekiyorsa işi duraklat ve sor."
157. Solaris zone'u agent yönetimine alma. Özellik: Zone agent kurulumu. Örnek: "Mevcut bir non-global zone'u agent ile yönetime al; önce zone'un çalıştığını doğrula."
158. HP-UX katalog dosyasını içe aktarma ve yazılım politikası oluşturma. Özellik: HP-UX yazılım politikası. Örnek: "swa_catalog.xml'i yükle, HP-UX yazılım politikasına yama ekle."
159. HP-UX depot paketini inceleme. Özellik: HP-UX depot. Örnek: "Depot içindeki fileset'leri listele ve hangi ürüne ait olduğunu göster."
160. Ubuntu yama kurulumundan önce ve sonra betik çalıştırma. Özellik: Pre/post kurulum betiği. Örnek: "Ubuntu yama kurulumundan önce disk kontrolü betiği çalıştır; hata olursa kurulumu durdur."
161. Red Hat kanal içe aktarmada sertifika doğrulama. Özellik: Red Hat sertifikaları. Örnek: "RHSM içe aktarıcısının sertifika zincirini doğrula; hata varsa nedenini raporla."
162. SUSE Manager içe aktarıcı sertifikasını tanıtma. Özellik: SUSE Manager importer. Örnek: "SUSE Manager sertifikasını import binary'sine tanıt; doğrulamayı yeniden çalıştır."
163. RPM'i bağımlılıklarını otomatik eklemeden dağıtma. Özellik: rpmdeployment. Örnek: "nginx RPM'ini yalnız kendisi olarak dağıt; bağımlılık hatasını raporla."
164. RHEL'de dinamik yama politikasını mrc_calc yerine kullanma. Özellik: Dinamik yama politikası. Örnek: "RHEL 9 sunucusunda minimum RPM düzeltme hesabını dinamik politikayla yap."
165. Politikadaki RPM'leri otomatik güncelleme. Özellik: RPM otomatik güncelleme. Örnek: "Politikadaki RPM'leri en son release'e otomatik güncelle."
166. RPM kurulum ve yükseltme bayrağı tanımlama. Özellik: Install/uninstall flags. Örnek: "Bu politikanın RPM kurulumlarına özel komut bayrağı ekle; paket özelliklerini değiştirme."
167. Politika içindeki kurulum sırasını belirleme. Özellik: Kurulum sırası. Örnek: "Java paketini Nginx'ten önce kur; politika sırasını doğrula."
168. Düşük diskli sunucuları paket indirmeden önce listeleme. Özellik: Düşük disk alanı. Örnek: "Disk alanı yetersiz olan sunucuları paket indirmeden önce listele."
169. Remediation'ı uygulamadan önce önizleme. Özellik: Remediation önizleme. Örnek: "Politikayı uygulamadan önce hangi paketlerin kurulacağını önizle ve raporla."
170. Remediation aşamalarını ayrı zamanlama. Özellik: Analysis, Download, Remediate. Örnek: "Analiz öğlen, indirme 22:00, kurulum 02:00'ye planla."
171. Remediation hata işleme ve yeniden başlatmayı ayarlama. Özellik: Hata işleme ve reboot. Örnek: "Kritik olmayan hatalarda devam et; yeniden başlatmayı işlem sonunda yap."
172. Zaman aşımına uğrayan işi hata işlemeden ayrı yönetme. Özellik: Zaman aşımı. Örnek: "Zaman aşımına uğrayan remediation işini analiz et; hata ayarının zaman aşımını kapsamadığını raporla."
173. Paket türüne göre (IPS, MSI, AIM, depot) ayrı akış kurma. Özellik: Paket türleri. Örnek: "Solaris 11 IPS paketini, Windows MSI paketini ve AIM ZIP paketini ayrı içe aktar."
174. Agent'ı UNIX veya Windows sunucudan kaldırma. Özellik: Agent kaldırma. Örnek: "UNIX sunucudaki agent'ı root olarak kaldır; Windows için Administrator gerektiğini belirt."
175. Yapılandırma dosyası değerlerinin sapmasını izleme. Özellik: AC uyumu. Örnek: "Web gruplarında yapılandırma değerleri şablondan sapmış mı, Out of Sync olanları listele."
176. Yapılandırma dosyasını şablonla audit etme. Özellik: AC audit. Örnek: "sshd_config dosyasını şablona göre audit et; sapan sunucuları raporla."
177. Yapılandırma şablonlarını ve betik sırasını yönetme. Özellik: Şablon sırası. Örnek: "AC'deki iki şablonu ve betiği, çalışma sırasını koruyarak yeniden sırala."
178. Audit sonrası özel betik ve yeniden başlatma aksiyonu. Özellik: Custom scripts ve reboot action. Örnek: "Audit düzeltmesinin sonunda özel betik çalıştır ve sunucuyu yeniden başlat."
179. Çalışan audit veya remediation işini durdurma. Özellik: Aktif iş iptali. Örnek: "Çalışan audit işini durdur ve kısmi sonucu raporla."
180. Snapshot job zamanlamasını düzenleme ve silme. Özellik: Snapshot zamanlaması. Örnek: "Web sunucularının snapshot programını haftalık yap; eski zamanlamayı sil."
181. Provisioning için boot server kurma. Özellik: sunucu otomasyonu Installer boot server. Örnek: "Yeni lokasyonda sunucu otomasyonu Installer ile boot server kur; dhcpd bileşenini doğrula."
182. Debian 11/12 ve SLES 15/16 OS provisioning. Özellik: Platform provisioning adımları. Örnek: "SLES 16 x86_64 sunucusunu build plan ile kur; SLES 15'ten farkları kontrol et."
183. Windows Server 2012 R2 ve Solaris 11.1 x86 provisioning. Özellik: Network boot provisioning. Örnek: "Windows 2012 R2 sunucuyu network boot ile kur; Solaris 11.1 x86 için ayrı adımları uygula."

## 4. Belgede duyurulan sınırlar, kaldırılanlar, bilinen sorunlar

Kaynak: Release notes > Known issues, Deprecation and Obsolescence, Enhancements (https://docs.microfocus.com/doc/419/25.4/knownissues, /deprecations, /enhancements). Troubleshoot > Troubleshoot sunucu otomasyonu services (/troubleshootsaservices).

### 4.1 Kullanımdan kaldırılanlar (25.4 sürümünde)
- Chef entegrasyonu: "Chef integration in sunucu otomasyonu is now deprecated" (25.4).
- SOAP API: Tümü kullanımdan kaldırıldı; yerine REST API (25.4).
- Gateway bant genişliği sınırlama (BWT): Kullanımdan kaldırıldı (25.4).
- Yönetilen platformlar (25.4): VMware ESX 7.0, HP-UX 11.31 IA-64, Debian 10 x86_64. Sanallaştırma: vCenter 7.0 ve öncesi.
- OS Provisioning: ProLiant iLO entegrasyonu (24.1 ile kullanımdan kaldırıldı).

### 4.2 Desteği kaldırılanlar (obsolete)
- 25.4: Ubuntu Server 14.04, 16.04, 18.04 (x86_64); OEL 6; RHEL 6; AIX 7.1; Windows 8.1; Windows Server 2012 x86_64; CentOS 7; VMware ESX 6.5; HP-UX 11.31 PA-RISC; SCVMM Server 2008 R2; vCenter 6.5 ve öncesi.
- 25.4 SMO: HP-UX üzerinde Registered Software, UNIX Users and Groups, Extensible Discovery (APX) desteği kaldırıldı.
- 24.1: Ubuntu Server 14.04 ve 16.04 için OS provisioning desteği kaldırıldı. AIX 6.1 ve diğer eski platformlar.
- 24.1: CentOS 5, OEL 5, RHEL 5, SUSE Linux Enterprise Server 10 ve 11 gibi eski platformlar desteklenmiyor (belgede 24.1 olarak işaretli).
- YUM adaptörü varsayılan olarak kapalı; `way.analyze.yum` parametresi ile açılır (2020.11 kullanımdan kaldırma notu).
- rhn_import ikilisi kullanımdan kaldırıldı; yerine redhat_import (10.50).

### 4.3 Bilinen sorunlar (Known issues, belgedeki kayıtlar)
- OCTCR19XW2721402 (25.4): Salt okunur yama izni olan kullanıcı, izin kontrolünü atlayıp uyumlu sunucularda yama indirmesini tetikleyebilir. Kategori: Administration.
- OCTCR19XW2713861 (25.4): Ön kurulum özelleştirme betiği belirtilen ve satellite arkasında, OS Provisioning olmayan agent kurulumu başarısız olur. Kategori: Agent Deployment.
- OCTCR19XW2394790 (24.1): Oracle network encryption etkinleştirilemiyor. Kategori: Upgrade.
- OCTCR19XW2664581 (24.1): Ansible 12 ile entegrasyonda sunucu otomasyonu'dan Ansible playbook çalıştırılamıyor. Kategori: Ansible Integration.
- OCTCR19XW2395296 (24.1): Belirli Windows proxy ayarlarında sunucu otomasyonu Client core'a bağlanamıyor. Kategori: UI.
- OCTCR19L1742166 (2022.11): Secondary core'da yeniden başlatılan yükseltme, ön koşul kontrolünde import hatası veriyor. Workaround mevcut.
- OCTCR19L1055368 (2020.11): Solaris x86 provisioning RHEL8/OEL8/CentOS8 core'da başarısız. Workaround mevcut.
- OCTCR19L1148348 (2020.11): Service Automation Visualizer sunucuları tarayamıyor. Workaround yok.
- OCTCR19L1058047 (2020.11): Eski (2018.08 veya öncesi) launcher ile bağlanınca hata. Workaround mevcut.
- OCTCR19L1152128 (2020.11): Desteklenmeyen platformları elle etkinleştirmek yükseltmeyi bozabilir. Workaround yok.
- OCTCR19L292325 (2018.08): HPSA_linux_boot_cd_linux7 ISO'su CentOS osprov_ogfs_agent dosyasını indirmiyor. Workaround yok.
- OCTCR19L317243 (2018.08): NGUI Launcher 64-bit platformda jre.zip indirmiyor. Workaround mevcut.
- OCTCR19L289879 (2018.08): Core'a slice eklenince CSR'lar varsayılan crypto.key_length, crypto.hash_algorithm ve fips.mode ile üretiliyor. Workaround mevcut.
- OCTCR19L290576 (2018.08): Slave core'da Model Repository yükseltmesi "Unable to decrypt crypto DB" hatası veriyor. Workaround mevcut.
- OCTCR19L290802 (2018.08): RHEL8/OEL8 konuk işletim sistemi ile Create VM işi desteklenmeyen SCSI denetleyicisi kullanıyor. Workaround yok.
- OCTCR19L317231 (2018.08): cbt, root olmayan kullanıcıyla infra/slice/satellite'te CBT hatası veriyor. Workaround yok.
- OCTCR19L290218 (10.60): Gateway yeniden sertifikalama, üçüncü taraf sertifika moduna geçişte başarısız. Workaround yok.
- OCTCR19L291033 (10.60): Core recertification Phase 13 tüm sertifika ve gizli anahtarları silmiyor. Workaround yok.
- OCTCR19L291533 (10.60): Yükseltme sırasında Twist başlangıcı APXUserPermissionManager ile takılıyor. Workaround yok.
- OCTCR19L289979 (10.60): Devam eden core kurulumu security.conf değerlerini varsayılana sıfırlıyor. Workaround mevcut.
- OCTCR19L292319 (10.60): HA veritabanı ortamlarında hata toleransı iyileştirmesi gerekiyor. Workaround yok.

Not: Known issues sayfası bu listeden sonra da devam ediyor; listenin tamamı okunmadı (yaklaşık 3500 karakter alındı).

### 4.4 25.4 iyileştirmeleri (Enhancements, belgedeki kayıtlar)
- OCTCR19XW2400677: Yazılım politikası betiklerinde değer yerine koyma (templating) özelliği. Yazılım yönetimi.
- OCTCR19XW2388977: vCenter entegrasyonunu agent olmadan API ile destekleme. Sanallaştırma yönetimi.

### 4.5 Troubleshoot (sunucu otomasyonu servisleri) bilinen konular
- Eski (2018.08 veya öncesi) launcher ile 2020.11 core'a bağlanınca hata mesajı.
- .NET WSDL üzerinden fonksiyon üretilememesi.
- "Build Failed" yaşam döngüsü durumundaki sanal makineler silinemiyor.

### 4.6 Okunmayan konular (ikinci tur sonrası)
- Fixed issues sayfası ikinci turda okundu, ancak yalnızca ilk kısmı (yaklaşık 900 karakter) alındı; listenin tamamı yok.
- Release notes ana sayfası ve Enhancements'ın tam listesi bu turda yeniden taranmadı (4.4 önceki turdan).
- Patch management for Windows, Unix, SUSE, Oracle Linux ve HP-UX alt sayfalarının çoğu gövde olarak okunmadı.
- Audit ve uyum alt sayfalarının çoğu (kural türleri ayrıntısı, compliance check kategorileri) okunmadı.
- Get started, Install ve Upgrade için yalnızca üst düzey sayfalar okundu; Upgrade altındaki adım adım sayfalar ve Install alt sayfaları okunmadı.
- Troubleshoot alt sayfalarının gövdeleri okunmadı; yalnızca başlık listesi (4.5 ve 2.6 içinde) alındı.
- Administer komut ve araç sayfaları (OCLI, ISM, IDK, DET, dgDump, fixOrphanedUnits vb.) ikinci turda okunmadı; yalnızca başlıkla kaldı.
- Develop altındaki APX ve pluggable check ayrıntılı alt sayfaları ile Java RMI, Chef ve Web Services komut örnekleri okunmadı.
- Use altında Server Agent kurulum alt sayfaları (ADT, WSUS, agentsız keşif), OS provisioning ayrıntıları (UEFI, DHCP komutları), snapshot ayrıntıları ve Chef/Ansible kurulum adımları okunmadı.

## 5. Özet ölçüler
- Önceki tur (1. bölüm): 3 tam sayfa + yaklaşık 165 içerik sayfası yazılmıştı; bu sayı bu turda yeniden doğrulanmadı.
- Bu tur (ikinci tur): gövdesi okunan Use/Develop/Release/Troubleshoot sayfası yaklaşık 76 (tocflat erişimi üzerinden, her sayfa tek sefer). 2.6 bölümüne 56 satır eklendi. Önceki satırlarda 27 "tahmin" işareti "okundu" olarak düzeltildi.
- Yetenek listesi: 183 madde (111-147 ikinci turda, 148-183 üçüncü turda eklendi).
- Bütçe: 220 yükleme sınırının altında; 429 ya da bot kontrolü görülmedi.
- Üçüncü tur: 258 gövde okundu (2.7 ve 6), 1 sayfa 403 ile atlandı. Kaydetme: dosya 30 sayfa aralıklarıyla değil, okuma bittikten sonra tek seferde güncellendi (bu bir sapma).
- Üçüncü tur eklenen satır: 2.7 bölümünde 31 satır (okundu), 148-183 arası 36 yetenek maddesi ve 6. bölümde 20 vaka adayı.

## 6. Sorun giderme ve bilinen sorunlardan çıkan vaka adayları

Her aday bench senaryosu adayıdır: bir cümle talep, belirtinin kısa tarifi ve kaynak adresi. Kaynaklar gövdesi okunmuş sayfalardır ya da 4.3 bilinen sorun kaydıdır.

1. Talep: "Solaris x86 sunucuyu RHEL8 core'da provisioning et ve hatayı sınıflandır." Belirti: Sunucu maintenance mode'a girmiyor, Unprovisioned Servers listesinde görünmüyor; neden RHEL8/OEL8/CentOS8 core'da NFS v2 kapalı olması. Kaynak: https://docs.microfocus.com/doc/419/25.4/solarisprovisioningfails ; bilinen sorun OCTCR19L1055368.
2. Talep: "Sunucu maintenance mode'a girmedikten sonra Wait for sunucu otomasyonu Agent zaman aşımını teşhis et." Belirti: Sunucu sunucu otomasyonu'da görünmez, DHCP ve konsol kontrolü gerekir. Kaynak: https://docs.microfocus.com/doc/419/25.4/maintenancemode
3. Talep: "ProLiant Gen8 sunucusunda Boot adımı başarısızsa maintenance mode sorununu bul." Belirti: Boot başarılı, Wait zaman aşımı. Kaynak: https://docs.microfocus.com/doc/419/25.4/proliantgen8
4. Talep: "OS installer Monitoring veya Run setup adımında düşerse medyayı ve betiği doğrula." Belirti: Kurulum yeniden başlatmadan önce durur. Kaynak: https://docs.microfocus.com/doc/419/25.4/failureofosinstaller
5. Talep: "Production agent Wait adımı başarısızsa OS'nin ilk açılışta kurulup kurulmadığını kontrol et." Belirti: Sunucu konsolunda açılış görünmüyor, ilk boot hatası. Kaynak: https://docs.microfocus.com/doc/419/25.4/failurewhenwaiting
6. Talep: "Set Media Source veya Create Stub Partition hatasını çözmek için OS kurulum öncesi adımları incele." Kaynak: https://docs.microfocus.com/doc/419/25.4/failurebeforeosinstalls
7. Talep: "SMTool upload işi /var/tmp yokken çalıştırıldığında hatayı yeniden üret." Belirti: OSError Errno 2, /var/tmp/smtool.<pid> bulunamıyor. Kaynak: https://docs.microfocus.com/doc/419/25.4/smtuploadfails
8. Talep: "Recurring application configuration compliance işi bir yıl sonra durunca nedenini doğrula." Belirti: Jeton süresi dolduğu için tekrarlayan iş çalışmıyor. Kaynak: https://docs.microfocus.com/doc/419/25.4/recurringappconfig
9. Talep: "Solaris yamasını Single User Mode ile kurarken hata verildiğinde sunucunun durumunu izle." Belirti: Remediation başarısızsa sunucu tek kullanıcı modunda kalabilir. Kaynak: https://docs.microfocus.com/doc/419/25.4/changesolarisinstallmode
10. Talep: "Atipik dizinde kalan öğe tek kullanıcı modunda remediation'ı tıkıyor mu, test et." Belirti: Tek kullanıcı modunda dizin erişilemez, sonraki öğeler işlenmez. Kaynak: https://docs.microfocus.com/doc/419/25.4/mountingstagingdirectory
11. Talep: "Installer düzeltilebilir hatada durduğunda kurulumu yeniden başlatma adımlarını uygula." Kaynak: https://docs.microfocus.com/doc/419/25.4/restartinstall
12. Talep: "Eski NGUI launcher 64-bit platformda jre.zip güncellemesini yapmadan bağlanırsa ne olduğunu test et." Belirti: Eski JRE ile açılır. Kaynak: https://docs.microfocus.com/doc/419/25.4/nguilauncher
13. Talep: "Zaman aşımına uğrayan remediation işinde hata işleme ayarının uygulanıp uygulanmadığını doğrula." Belirti: Zaman aşımı hata işleme ayarından bağımsızdır, iş durur. Kaynak: https://docs.microfocus.com/doc/419/25.4/timeouthandlinginstallationuninstallation
14. Talep: "Düşük disk alanında paket indirme hatasını yakala ve raporla." Belirti: Yetersiz alanda hata mesajı, paket indirilmez. Kaynak: https://docs.microfocus.com/doc/419/25.4/serverswithlowdiskspace
15. Talep: "Solaris firmware yamasını patchadd ile kurmayı dene ve başarısızlığı sınıflandır." Belirti: patchadd firmware yamasını kuramaz. Kaynak: https://docs.microfocus.com/doc/419/25.4/installmanualpatches
16. Talep: "Windows yama politikasında Never Install istisnası yüklü yamayla çakışınca uyumsuzluk nedenini göster." Belirti: Uyumsuz sunucuda istisna çakışması. Kaynak: https://docs.microfocus.com/doc/419/25.4/patchnoncompliance
17. Talep: "Ubuntu pre-install betiği hata verdiğinde yama işinin nasıl davrandığını test et." Kaynak: https://docs.microfocus.com/doc/419/25.4/specifyinstallscriptsubuntu
18. Talep: "Salt okunur yama izni olan kullanıcının izin kontrolünü atlayıp atlayamayacağını doğrula." Belirti: Bilinen sorun OCTCR19XW2721402 (25.4): uyumlu sunucuda yama indirmesi tetiklenebilir. Kaynak: https://docs.microfocus.com/doc/419/25.4/knownissues
19. Talep: "Satellite arkasında ön kurulum betiği olan agent kurulumunun başarısız olduğunu yeniden üret." Belirti: OCTCR19XW2713861 (25.4), OS Provisioning olmayan kurulum başarısız. Kaynak: https://docs.microfocus.com/doc/419/25.4/knownissues
20. Talep: "Desteklenmeyen platformu elle etkinleştirmenin yükseltmeyi bozup bozmadığını test et." Belirti: OCTCR19L1152128 (2020.11), workaround yok. Kaynak: https://docs.microfocus.com/doc/419/25.4/knownissues
