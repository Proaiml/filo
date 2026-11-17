# OpenText akış otomasyonu 26.4: REST API, komut satiri araclari ve yonetim envanteri

Kaynak: https://docs.microfocus.com/doc/397/26.4/home (sayfa govdeleri: https://docs.microfocus.com/397/26.4/<slug>/default-<revizyon>.json)

## 1. Okunan ve okunmayan sayfalar

- Okunan sayfa sayisi: yaklasik 218.
  - Develop (REST API ve icerik gelistirme, 71 sayfa): REST uc noktalari icin tum sayfalar okundu; icerik gelistirme (AFL, CloudSlang, Java plugin) sayfalari yalnizca ozet duzeyinde okundu.
  - Administer (104 sayfa): tum sayfalarin ilk paragraflari ve baslik yapisi okundu. Designer ve SSX guvenlik sayfalarinin icerigi ozet duzeyinde.
  - Use > akış otomasyonu Central ve calisma yonetimi (11 sayfa), Central sistem ogeleri (12 sayfa), akış komut aracı ve akış yönetim aracı (14 sayfa), sihirbaz giris sayfalari (6 sayfa).
- Okunmayan: Install, Upgrade, Integrate, Troubleshoot ve Get started bolumleri (kapsam disi); akış otomasyonu Studio ve Workflow Designer akis yazma ayrintilari (kapsam disi); PA Mobile; Self-Service X'in Swagger ayrintilari (sayfa yalnizca Swagger arayuzune baglanti veriyor).
- Tarama notu: "retry" / "yeniden deneme" konusunda ayri bir sayfa veya uc nokta bulunamadi. Pause, resume, cancel, reassign ve rerun konulari asagida belgelerle yazilmistir.

## 2. Bolum A: Develop altindaki REST API

### 2.1 REST uc noktalari

Her kategori icin sayfa adresi: https://docs.microfocus.com/doc/397/26.4/<slug>. Asagidaki tablolarda slug kaynak sayfayi gosterir.

| kategori | yontem | yol | ne_yapar | kaynak slug |
|---|---|---|---|---|
| Uygulama giris | POST | /oo/rest/v2/executions | Flow calistirmak icin v2 istegi (UUID ve girdilerle) | apiintro |
| Flow yurutme | GET | /executions | Filtrelenebilir, sayfalanmis yurutme ozetleri listesi | restapis |
| Flow yurutme | POST | /executions | UUID ile flow calistirir | executeflowuuid |
| Flow yurutme | GET | /executions/{executionIds}/summary | Yurutme ozetini getirir (virgulle ayrilmis birden cok ID kabul eder) | getexecutionsummary |
| Flow yurutme | GET | /executions/statistics | Flow istatistikleri: ROI, yurutme sayisi, ortalama sure, sonuc dagilimi | dashboard |
| Flow yurutme | GET | /executions/reports | Yurutme ozetini CSV olarak, filtreyle verir | exportexecutionsummariescsv |
| Flow yurutme | GET | /executions/{executionId}/steps/count | Yurutulmus adim sayisini verir (bitenler ve calisan/duraklatilanlar dahil) | getexecutionstepcount |
| Flow yurutme | GET | /executions/{executionId}/steps | Adimlari sayfalanmis ve filtrelenebilir olarak listeler | getexecutionstepspagination |
| Flow yurutme | GET | /executions/{executionId}/steps/{stepPath} | Tek bir adimin verisini getirir | getsingleexecutionstep |
| Flow yurutme | GET | /executions/{executionId}/steps?mediaType=csv | Adimlari CSV olarak verir | getexecutionstepscsv |
| Flow yurutme | GET | /executions/{executionId}/steps?mediaType=text | Adimlarin metin temsilini verir | getexecutionstepstext |
| Flow yurutme | GET | /executions/{executionId}/execution-log | Genisletilmis yurutme ozeti ve ek bilgiler (log) | getexecutionlog |
| Flow yurutme | PUT | /executions/{executionIds}/status | Durum degistirir: CANCEL, PAUSE, REASSIGN, RESUME (action alani) | changeexecutionstatus |
| Yeniden calistirma | GET | /executions/{executionId}/rerunnable-steps | Yurutmenin hangi adimlardan yeniden calistirilabilecegini listeler | getrerunnablesteps |
| Yeniden calistirma | POST | /executions/rerun | Belirli bir adim yolundan yeniden calistirir | rerunfromstep |
| Yeniden calistirma | DELETE | /executions/rerun | Yeniden calistirma verisini siler (endedBefore, maxAmount ile) | deletererundata |
| Veri temizligi | DELETE | /executions | Yurutme verisini temizler (endedBefore, statuses, flowUuids, maxAmount, purgeItems) | purgeexecutionstepdata |
| Veri temizligi | DELETE | /steps-log | Adim log verisini temizler (endedBefore, maxAmount) | deletesteplogdata |
| Hata ayiklama | DELETE | /debugger-events | Uzak yurutmelerin debugger olaylarini temizler | purgedebuggerexecution |
| Hata ayiklama | DELETE | /debugger-event | Debugger olaylarini tarihe gore temizler | purgedebuggerexecution |
| Flow kutuphanesi | GET | /flows/library | Dagitilmis tum flow ve klasorleri siralanmis liste olarak verir | flowlibrary |
| Flow kutuphanesi | GET | /flows/tree/level | Flow agacini seviyeli olarak verir | flowlibrary |
| Flow kutuphanesi | GET | /flows/{uuid} | Tek flow bilgisi | flowlibrary |
| Flow kutuphanesi | GET | /flows/{uuid}/inputs | Flow girdileri | flowlibrary |
| Flow kutuphanesi | GET | /flows/inputs | Birden cok flow icin girdiler | flowlibrary |
| Flow kutuphanesi | GET | /flows/{uuid}/outputs | Flow ciktilari | flowlibrary |
| Flow kutuphanesi | GET / PUT | /flows/{uuid}/settings | Flow calistirma ayarlarini okur ve yazar | flowlibrary |
| Zamanlama | GET | /schedules | Zamanlamalari listeler | scheduler |
| Zamanlama | GET | /schedules/{id} | Tek zamanlama | scheduler |
| Zamanlama | POST | /schedules | Yeni zamanlama ekler (flow yurutmesi icin) | scheduler |
| Zamanlama | PUT | /schedules/{id} | Zamanlamayi gunceller | scheduler |
| Zamanlama | PUT | /schedules/{ids}/enabled | Zamanlamalari etkinlestirir veya devre disi birakir | scheduler |
| Zamanlama | DELETE | /schedules/{ids} | Zamanlamalari siler | scheduler |
| Icerik paketi | GET | /content-packs | Icerik paketlerini listeler (active=false ile pasifler dahil) | contentpacks |
| Icerik paketi | GET | /content-packs/{id} | Tek icerik paketi | contentpacks |
| Icerik paketi | GET | /content-packs/{id}/content-tree | Icerik paketinin agac yapisi | contentpacks |
| Icerik paketi | GET | /content-packs/statistics | Icerik paketi istatistikleri | contentpacks |
| Icerik paketi | GET | /content-packs/{id}/changes | Icerik paketindeki degisiklikler | contentpacks |
| Icerik paketi | PUT | /content-packs/{cpFileName} | Icerik paketini dagitir (deploy) | deploymentcp |
| Icerik paketi | DELETE | /content-packs/last | Sayfada ornek olarak geciyor; son paket silme davranisi sayfada ayrintili degil | addingcontentpackfiles |
| Icerik paketi | POST | /oo-designer/rest/v0/xfeatures/{workspace_id} | Calisma alani ozellikleri (Designer tarafi); sayfada ayrintisi sinirli | contentpacks |
| Dagitim sureci | POST | /deployments | Dagitim sureci nesnesi olusturur, ID dondurur | deploycontentpacks |
| Dagitim sureci | POST | /deployments/{deploymentProcessId}/files | Icerik paketi dosyalarini surece yukler | uploaddeploymentprocess |
| Dagitim sureci | GET | /deployments/{deploymentProcessId} | Surecin durumunu ve ayrintilarini verir | getdeploymentprocess |
| Dagitim sureci | PUT | /deployments/{deploymentProcessId} | Dagitim surecini calistirir (force=true secenegi var) | runspecificdeployment |
| Dagitim sureci | DELETE | /deployments/{deploymentProcessId}/files/{fileId} | Surecten icerik paketi dosyasini cikarir | deletedeploymentcp |
| Dagitim sureci | POST | /deployments/{deploymentProcessId}/cpsForDelete | Silinecek icerik paketi dosyalarini sürece ekler | addingcontentpackfiles |
| Yapilandirma ogeleri | GET | /config-items | Yapilandirma ogelerini listeler | configurationitemscontent |
| Yapilandirma ogeleri | GET | /config-items/{type} | Tur bazli liste (ornek: system-accounts) | configurationitemscontent |
| Yapilandirma ogeleri | GET | /config-items/{type}/{path} | Tek sistem hesabi veya sistem ozelligi | configurationitemscontent |
| Yapilandirma ogeleri | PUT | /config-items/{type}/{path} | Yapilandirma ogesini olusturur/gunceller | configurationitemscontent |
| Yapilandirma ogeleri | DELETE | /config-items/{type}/{path} | Yapilandirma ogesini siler | configurationitemscontent |
| Yapilandirma ogeleri | GET | /config-items/tree | Yapilandirma ogesi agaci | configurationitemscontent |
| Kuyruk | GET / POST | /queue-config | RabbitMQ kuyruk yapilandirmasini okur ve yazar | queueconfigrabbitmq |
| Kuyruk | POST | /queue-config/test | Kuyruk baglantisini test eder, surum hatalarini raporlar | queueconfigrabbitmq |
| Kuyruk | PATCH / POST | /v0/queue-config | Kuyruk yapilandirmasini (surum 0) kismen gunceller / olusturur | queueconfigrabbitmq |
| Sistem ayarlari | GET / POST | /config | Sistem yapilandirma ogelerini listeler / olusturur | systeminformationsettings |
| Sistem ayarlari | GET / PUT | /config/{key} | Tek sistem yapilandirma anahtarini okur / gunceller | systeminformationsettings |
| Sistem ayarlari | GET | /general-settings/{key} | Genel ayar degerini okur (ornek: system.level.flow.timeout) | systeminformationsettings |
| Sistem ayarlari | GET | /db-statistics | Veritabani istatistikleri | systeminformationsettings |
| Log seviyesi | GET / PUT | /loglevel | Sistem varsayilan yurutme log seviyesini (persistence) okur / degistirir | getsystemloglevel |
| Surum | GET | /version | akış otomasyonu surum bilgisi | getooversion |
| Bildirim | GET | /notifications | Kullanilabilir bildirimleri, aciklamalarini ve durumlarini listeler | systemnotifications |
| Bildirim | GET | /notification-channel/mail | E-posta bildirim kanali ayarlari | systemnotifications |
| Kullanici | POST | /users | Dahili kullanici ekler | users |
| Kullanici | GET | /users | Kullanicilari listeler (domain=internal filtresi) | users |
| Kullanici | GET | /users/me | Oturum acmis kullanici | users |
| Kullanici | PUT | /users/{username} | Kullaniciyi gunceller | users |
| Kullanici | DELETE | /users/{userNames} | Kullanicilari siler | users |
| Kimlik dogrulama | GET / PUT | /authns | Kimlik dogrulama durumunu okur / gunceller | userauthentication |
| Kimlik dogrulama | GET / PUT | /authns/lwsso-config | LW-SSO yapilandirmasini okur / gunceller | lwssoconfiguration |
| LDAP | GET | /authns/ldap-config | LDAP yapilandirmalarini listeler | ldapconfiguration |
| LDAP | POST | /authns/ldap-config | LDAP yapilandirmasi ekler | ldapconfiguration |
| LDAP | GET | /authns/ldap-config/{id} | Tek LDAP yapilandirmasi | ldapconfiguration |
| LDAP | PUT | /authns/ldap-config/{ldapId} | LDAP yapilandirmasini gunceller | ldapconfiguration |
| LDAP | GET / DELETE | /authns/ldap-config/default | Varsayilan LDAP yapilandirmasini okur / siler | ldapconfiguration |
| LDAP | POST | /authns/ldap-config/{id}/test | Kayitli LDAP yapilandirmasini test eder | ldapconfiguration |
| LDAP | POST | /authns/ldap-config/test | Girilen LDAP ayarlarini test eder | ldapconfiguration |
| LDAP | POST / PUT | /authns/ldap-root | LDAP kok (root) yapilandirmasini ekler / gunceller | ldapconfiguration |
| Roller | GET | /roles | Rolleri listeler | roles |
| Roller | POST | /roles | Rol olusturur | roles |
| Roller | GET / PUT / DELETE | /roles/{roleName} | Rolu okur / gunceller / siler | roles |
| Roller | GET | /roles/default-name | Varsayilan rol adi | roles |
| Roller | GET / PUT | /roles/{roleName}/entitlements/{path} | Bir rolun belirli kaynak yolundaki haklarini okur / yazar | roles |
| Denetim | GET / PUT | /audit/config | Denetim yapilandirmasini okur / gunceller | auditevents |
| Denetim | GET | /audit/records | Denetim kayitlarini sayfalar, siralar, tarih araligiyla filtreler (before/after) | auditevents |
| Denetim | DELETE | /audit/records | Denetim kayitlarini siler | auditevents |
| RAS (calistirici) | GET | /rases | Tum RAS'leri listeler | workers |
| RAS | POST | /rases/{uuids}/upgrade | RAS'leri yukseltir | workers |
| RAS | POST / GET / DELETE | /ras-upgrade-file | RAS yukseltme dosyasini yukler, surumunu gosterir, siler | workers |
| Worker | GET | /workers | Worker'lari listeler | workers |
| Worker | PUT / DELETE | /workers/{workerId} / {workersUuid} | Worker'i gunceller / siler | workers |
| Worker grubu | GET | /workers-groups | Worker gruplarini listeler | workers |
| Worker grubu | PUT / DELETE | /workers-groups/{name}/workers/{workersUuids} | Worker'i gruba ekler / gruptan cikarir | workers |
| Ters RAS | POST / PUT | /reverse-rases, /reverse-rases/{uuid} | Ters baglantili RAS kaydeder / gunceller | firewallfriendlyapis |
| Ters RAS | POST | /reverse-rases/test | Ters RAS baglantisini test eder | firewallfriendlyapis |
| Ters RAS | GET / POST / PUT / DELETE | /reverse-ras-proxy | Ters RAS proxy ayarlarini yonetir | firewallfriendlyapis |
| Robot | GET | /robots | Kayitli robotlari listeler | robotapis |
| Robot | GET / POST | /robot-groups | Robot gruplarini listeler / olusturur | robotapis |
| Robot | POST | /robots/assign | Robotu gruba atar | robotapis |
| Hedef izleme | GET | /targets/all | Central'in vurdugu hedefleri sayfalar | gettargets |
| Hedef izleme | GET | /targets/count | Hedef sayisi | gettargets |
| Denetim/guvenlik | (sayfa) | Basic authentication: istemcinin REST cagrilarinda kimlik bilgisi gondermesi; preemptive basic auth | basicauthentication |
| Guvenlik | (sayfa) | CSRF korumasi: REST/Web tarafinda CSRF korumasi ve kapatma yolu | csrfprotectionoo |

Not: Self-Service X icin ayri bir Swagger API vardir (selfservicexapis); uc noktalari bu sayfada listelenmiyor.

### 2.2 Yurutme durumlari, duraklat, sürdür, iptal, devret ve yeniden calistirma (REST)

- Durum degistirme (PUT /executions/{executionIds}/status): CANCEL, PAUSE, REASSIGN, RESUME. Kosullar: kullanicinin ilgili flow icin Run yetkisi olmasi; run'in kullaniciya atanmis olmasi veya "Manage Others' Runs" yetkisi. Tamamlanmis yurutme degistirilemez; ayni duruma gecis yapilamaz. Birden cok ID'ye tek action uygulanabilir.
- Yeniden calistirma (POST /executions/rerun): yalnizca basarisiz veya iptal edilmis yurutmeler, adim "rerun point" olarak isaretlenmisse. Paralel ve multi-instance seritlerinde yok; uzak debugger ile calisan flow'larda yok.
- Insan onayi / devretme (handoff): REST sayfalarinda ayrintili handoff uc noktasi yok. Central'da "handoff" gecisi ve "gated transition" (rol bazli erisim) kavramlari var (bkz. bolum 3).
- Otomatik yeniden deneme (retry): belgede bulunamadi.

## 3. Bolum C: Use > akış otomasyonu Central (yonetim sayfalari)

| ozellik | ne_yapar | admin_isi | kaynak | agirlik |
|---|---|---|---|---|
| Sistem hesaplari (configuresystemaccount) | Kullanici adi ve sifre gibi kimlik bilgilerini saklar; degerler yalnizca Studio kurulumunda gorunur. Izinler icerik paketi bazinda atanir | Bir kez kurulur, degisimde guncellenir | configuresystemaccount | cekirdek |
| Sistem ozellikleri (configuresystemproperty) | Tum flow'lar icin global degiskenler; degerleri degismez, yeniden tanimlama gerekmez | Ortam bazli degerler icin kurulum | configuresystemproperty | sik |
| Grup takma adlari (configuregroupaliases) | RAS gruplari tanimlar; flow adimlarini bir grup takma adina baglayarak mantiksal veri merkezi/ortam secimi yapar | Ortam (dev/test/prod) icin RAS grubu kurulumu | configuregroupaliases | cekirdek |
| Rol takma adlari (configurerolealiases) | Planlanan rolleri takma ad olarak tanimlar; gated transition'lara baglanir | Gated gecislerde rol eslemesi | configurerolealiases | sik |
| Worker gruplari ve takma ad | Worker'lara takma ad atanir; worker gruplari altinda duzenlenir. Adim bir worker grubuna atanabilir | Ag topolojisi ve grup yonetimi | setupworkers, workergroupstep | cekirdek |
| Zamanlayici (scheduleflowruns) | Bir flow icin zamanlama olusturur; tekrarlayan zamanlama kurulabilir; Scheduler'da gorunur; yetkiye gore goruntuleme | Zamanlama acma/kapama, silme | scheduleflowruns | cekirdek |
| Run Explorer: duraklat, sürdür, iptal, devret (trackmanageflowruns) | Calisan run'lari izler; tek veya coklu run icin Cancel, Pause, Reassign, Resume uygular. Duraklatma sirasinda "Pending pause" ara durumu gorulur | Operasyon ekibinin gunluk islemi | trackmanageflowruns | cekirdek |
| Flow Launcher (runflow) | Flow'u agactan secip calistirir; etkilesimli flow (kullanici girdisi), handoff gecisi, gated gecis ve "Paused-No Workers" etkilesimini destekler | Flow ve yetki kurulumu | runflow | cekirdek |
| Handoff gecisi (runflow) | Yurutme bir kullanici adimina gelir; mesajdaki talimatlara gore girdi girilip "handoff" ile devam ettirilir. Duraklatilmis yurutme bu adimda bekler | Insan onayi noktasi tasarimi | runflow | sik |
| Gated gecis (runflow) | Sonraki adima yalnizca belirli rolu olan kullanicilar gecebilir; bu roller ile devam ettirilebilir | Rol eslemesi | runflow | sik |
| Paused-No Workers etkilesimi (runflow) | Uygun worker yoksa yurutme duraklar; worker kullanilabilir olunca otomatik devam eder ("Auto-resume") | Worker kapasitesi izleme | runflow | sik |
| Yeniden calistirma (rerunflow) | Basarisiz veya iptal edilmis run'i secilen adimdan yeniden calistirir; yonetici bu ozelligi acip kapatir; adim once Studio'da rerun point olarak isaretlenmeli | Ozelligi etkinlestirme | rerunflow | sik |
| Filtreleme (filterflows) | Run Explorer'da durum, baslangic zamani, kullanici, run adi ve run ID ile filtre; sayfa basina en fazla 200 run | Gunluk izleme | filterflows | sik |
| Run detayi (testtroubleshootflowrun) | Drill down ile adim bazinda run ayrintisi; hata ayiklama | Hata ayiklama | testtroubleshootflowrun | sik |
| Dashboard ve Insights (oodashboard) | Eski Dashboard ve Insights gorunumu arasinda gecis; widget ekleme ve duzenleme; ROI metrikleri; CSV disa aktarma | Widget ve zaman araligi | oodashboard | sik |
| Central UI gomme (embedcentralui) | Flow Run ve Drill Down gorunumlerini dis web sayfasina gomer | Entegrasyon | embedcentralui | seyrek |
| Hibrit flow (hybridflowexecution) | CloudSlang flow'u icinde akış otomasyonu yerel icerik akislarini alt adim olarak calistirir | CloudSlang kurulumu | hybridflowexecution | niş |
| Kategoriler (configurecategory) | Flow'lara kategori atanir; Dashboard grafiklerinde kullanilir | Ilk kurulumda kategori tanimlari | configurecategory | sik |
| Alan terimleri (configuredomainterm) | Flow ve girdilere alan terimi atanir; raporlarda kullanilir | Ilk kurulum | configuredomainterm | sik |
| Scriptlet (configurescriptlet) | JavaScript ile islem sonucunu filtreleme veya yanitini degistirme | Gelistirici isi | configurescriptlet | seyrek |
| Secim listeleri (configureselectionlist) | Kullanici istemlerinde sunulan secenek listeleri | Icerik | configureselectionlist | sik |
| Degerlendiriciler (configureevaluator) | Girdi dogrulamasi icin metin formatlari (sistem hesaplari haric) | Icerik | configureevaluator | sik |
| Sistem filtreleri (configuresystemfilter) | Operasyon ciktisini veya adim sonucunu ayiklayan sistem geneli filtreler | Icerik | configuresystemfilter | sik |
| Yapilandirma ogeleri icerik paketinde | Icerik paketi dagitildiktan sonra sistem hesabi ve sistem ozelligi izinleri ile degerleri ayarlanir | Her ortam icin | setupconfigitems | sik |

## 4. Bolum B: Administer (yonetim) bolumu

### 4.1 Roller, izinler ve kullanicilar

| ozellik | ne_yapar | admin_isi | kaynak | agirlik |
|---|---|---|---|---|
| IdM yonetim konsolu | Kuruluş (organization), kullanici, grup, rol, izin ve kimlik dogrulama yonetimini akış otomasyonu Central icinden yapar | Konsolu kullanma | administeridm | cekirdek |
| Rolle kullanici olusturma | Hazir roller (ornek: ADMINISTRATOR, END_USER) veya ozel rol ile kullanici olusturur | Kullanici acma | adduserscenario | cekirdek |
| Kullanici yonetimi | Kullanici arama, ekleme, duzenleme, silme, sifre ekleme/degistirme/silme | Gunluk | manageusers | cekirdek |
| Grup yonetimi | Grup ekleme, duzenleme, silme; gruba rol eslemesi | Gunluk | managegroups | cekirdek |
| Rol yonetimi (RBAC) | Rol ekleme, duzenleme, silme; role grup eslemesi | Erisim tasarimi | manageroles, setuproles | cekirdek |
| Izinleri goruntuleme | IdM izinlerini listeler (ornek: Manage system settings, Manage organization) | Denetim | viewpermissionsidm | sik |
| Yetkilendirme modeli | Kullanici erisiminin akış otomasyonu kaynaklarina nasil baglandigini ve minimum izin kurallarini aciklar; varsayilan rol ve workspace erisimi | Tasarim | authorization | cekirdek |
| Icerik paketi izinleri (Flow Library) | Flow kutuphanesinde flow izinlerini duzenler; flow calistirma ayarlari | Icerik yonetimi | manageflowlibrary | sik |
| Icerik paketi ve rol eslemesi | Icerik paketinde izinler ve dagitim sonrasi yapilandirma ogeleri | Dagitim | setupconfigitems | sik |
| Guvenlik ayarlari | Kimlik dogrulamayi, denetimi, kimlik bilgisi yakalamayi ve guvenlik bandini acar/kapatir | Kurulum | securitysettings | cekirdek |
| Rol kurulumu | RBAC ile rol ekleme, gruba baglama | Kurulum | setuproles | cekirdek |
| Dahili kullanicilar | akış otomasyonu kullanici adi ve sifresi ile dahili kullanici ekler/duzenler/siler | Kurulum | setupusers | sik |

### 4.2 Kimlik dogrulama (LDAP, SAML, OAuth, LW-SSO, IdM)

| ozellik | ne_yapar | admin_isi | kaynak | agirlik |
|---|---|---|---|---|
| Kimlik dogrulama yonetimi (IdM) | IdM'de kimlik dogrulama kaynaklarini olusturur ve yonetir | Kurulum | manageauthentication | cekirdek |
| LDAP | LDAP yapilandirmasi ekler; IdM modunda da yapilandirilabilir; REST ile yonetilir | Kurulum | ldapauthentication, setupsystemmgmt | cekirdek |
| SAML | SAML meta verisi indirir, SAML sunucu ayarlarini IdM konsolunda yapar; load balancer'a SAML ekler | Kurulum | samlauthentication, setupsaml | sik |
| OAuth (Azure AD) | Azure AD client id/secret ile OAuth; erisim tokeni ile REST | Kurulum | oauthconfiguration | niş |
| LW-SSO | Tek oturum acma yapilandirmasi; uyari loglarini temizleme (yonetim URL'si) | Kurulum | setupsecuritylwsso, lwsso | sik |
| IdM moduna gecis | Native modundan IdM kimlik modu'na gecis; idm.properties ve rol eslemesi | Gecis | idmmode | seyrek |
| Kullanici kimlik dogrulama modeli | Dahili ve LDAP kullanicilari, veritabani dogrulamasi | Tasarim | usersecurity | sik |

### 4.3 Denetim (audit)

| ozellik | ne_yapar | admin_isi | kaynak | agirlik |
|---|---|---|---|---|
| Denetim acma | Guvenlik ayarlarinda denetimi (auditing) etkinlestirir | Kurulum | securitysettings | cekirdek |
| Denetim yapilandirmasi ve kayitlari | Denetim ayarini okur/yazar; kayitlari sayfalar, siralar, tarihe gore filtreler; kayit silinebilir | Denetim sorgusu | auditevents | cekirdek |

### 4.4 Veri temizligi

| ozellik | ne_yapar | admin_isi | kaynak | agirlik |
|---|---|---|---|---|
| Veritabani temizligi (planli) | Flow ve yurutme verisini planli siler; tarih ve adet sinirli temizlik; purge API'leri ile de calisir | Baslangictan itibaren zamanlanmali | datacleanup | cekirdek |
| Veritabani sagligi | Veritabani boyutunu izler; calistirma log seviyesini (persistence) belirler | Gunluk izleme | databasehealth | sik |
| Veri temizligi API'leri | DELETE /executions, /steps-log, /debugger-events, /executions/rerun | Otomasyon | (bolum 2.1) | sik |

### 4.5 Izleme, loglama ve bildirim

| ozellik | ne_yapar | admin_isi | kaynak | agirlik |
|---|---|---|---|---|
| Log seviyeleri | Tomcat ve akış otomasyonu log seviyelerini ayarlar; varsayilan INFO; ayrintili loglar performansi etkiler | Gerekince ayarlama | logginglevels | sik |
| Sistem ayarlari (timeout) | Oturum zaman asimi (varsayilan 30 dk) web.xml ile degistirilir | Kurulum | timeout | sik |
| Sistem bildirimleri (e-posta) | Sistem olaylarini e-posta ile bildirir; yeniden gonderme araligi; e-posta sablonlari; deneme lisansinda kapali | Kurulum | sendemailnotifications | sik |
| Bildirim protokolleri | Sistem bildirimi icin SMTP protokollerini belirler | Kurulum | specifycommunicationprotocols | seyrek |
| Insights servisi | Istatistik ve widget sablonlarini uretir; kumelenmis akış otomasyonu Central'da tek servis | Kurulum | setupinsightservice | sik |
| Sistem ayarlari (genel) | ROI aciklamasi, varsayilan run zaman asimi, icerik paketi ayarlari, UI ozellestirme | Kurulum | setsystemsettings | sik |
| Sistem ayarlari (JVM/is parcacigi) | JVM heap, is parcacigi sayisi, veritabani baglantilari (her Central ve RAS dugumu icin) | Performans ayari | systemtuningoo | sik |
| Hedef izleme | Central'in vurdugu hedefleri izler (REST) | Izleme | gettargets | seyrek |

### 4.6 Yedekleme ve felaket kurtarma

| ozellik | ne_yapar | admin_isi | kaynak | agirlik |
|---|---|---|---|---|
| akış otomasyonu Central ve Workflow Designer yedekleme | Veritabani ve yapilandirma yedegi alir; arizada gecmis yedekten kurtarma | Duzenli yedek | backupoo | cekirdek |
| Designer verisi yedegi | Sunucu verisini guvenli ortama yedekler | Duzenli yedek | backupdesignerdata | sik |
| Felaket kurtarma (DR) | Ikincil veritabani planlar; DR ile kurtarma adimlari | DR tatbikati | disasterrecovery | sik |
| Periyodik yonetim gorevleri | Duzenli veya olaya bagli yapilacak yonetim gorevlerinin listesi (yedek, temizlik vb. konulari toplar) | Periyodik | recurringootasks | sik |

### 4.7 Yuksek erisilebilirlik (HA)

| ozellik | ne_yapar | admin_isi | kaynak | agirlik |
|---|---|---|---|---|
| PostgreSQL HA (Patroni) | PostgreSQL + Patroni + etcd + HAProxy kumesi; tum bilesenler Linux'ta | Kurulum | postgresqlha, postgesqlhapatroni, installpatronicluster | sik |
| Patroni sertlestirme | Patroni, etcd ve HAProxy icin dahili ve harici iletisimi sertlestirme | Guvenlik | hardeningpatronicluster | sik |
| RAS ve worker topolojisi | Worker ve RAS topolojisi, takma adlar, gruplar | Kurulum | setupworkers | cekirdek |
| Robot topolojisi | Robot gruplari ve robot atamalari | Kurulum | setuptopologyrobot | sik |
| Load balancer URL'si | Load balancer arkasindaki akış otomasyonu Central URL'sini degistirir | Degisiklik | raschangeurl | seyrek |

### 4.8 Guvenlik sertlestirme

| ozellik | ne_yapar | admin_isi | kaynak | agirlik |
|---|---|---|---|---|
| Guvenlik kavramlari ve uygulama | Guvenli kurulum/dagitim, fiziksel guvenlik, kullanici guvenligi | Tasarim | securityconceptsoo, secureimpldepl | cekirdek |
| Kurulum guvenligi | Isletim sistemi sertlestirme, Tomcat sertlestirme, HTTP-only cerez, kurulum izinleri | Kurulum | installationsecurity | cekirdek |
| Ag ve iletisim guvenligi | TLS protokolleri, kanal guvenligi, RAS guvenligi | Kurulum | networksecurity | cekirdek |
| Yonetim arayuzu guvenligi | Yonetim arayuzune erisimi kimlik bilgisi veya istemci sertifikasi ile kontrol | Kurulum | adminsecurity | cekirdek |
| Yetkilendirme | Erisim modeli ve yetkilendirme yapilandirmasi | Kurulum | authorization | cekirdek |
| Sifreleme | Statik veri, aktarimdaki veri, sifreleme yonetimi, varsayilan yapilandirma | Kurulum | encryption | cekirdek |
| Sifre gizleme | Sifreleri sifreleme ve obfuscate etme | Kurulum | obfuscateencrypt | sik |
| Sertlestirme onerileri | En son surumu kurma, guvenlik onerileri listesi | Kurulum | hardeningrecommendations | cekirdek |
| TLS sertifikasi | Sunucu TLS sertifikasini degistirme; CA kok sertifikasini Central, RAS, akış komut aracı, Studio truststore'a ekleme | Kurulum/yenileme | replacesslcert, authenticateservercertificate | cekirdek |
| Istemci sertifikasi | X.509 istemci sertifikasi ile kimlik dogrulama (Central, RAS, akış komut aracı, Studio) | Kurulum | clientcertificate | sik |
| Icerik imzalama | Icerik paketlerini jarsigner ile imzalar | Gerekince | signingoocontent | sik |
| Arac JAR dogrulama | akış yönetim aracı ve sihirbaz JAR'larinin dijital imzasini dogrular | Gerekince | verifyingintegrity | sik |
| TLS surumu | Desteklenen TLS surumlerini belirler; varsayilan TLS v1 ve v1.1 da dahil | Sertlestirme | configtls | sik |
| Yerel dosya sistemi | Flow'larin Central/RAS yerel dosya sistemine erisimini engeller (wrapper ve java.policy) | Sertlestirme | minimizerisk | sik |
| Java guvenlik yoneticisi | Java security manager ekler (RAS ve gomulu worker) | Sertlestirme | addingjsm | sik |
| HTTPS yonlendirme | HTTP trafigini HTTPS'e yonlendirir | Sertlestirme | enableredirect | sik |
| CSRF korumasi | CSRF korumasini kapatma secenegi (guvenlik acisindan dikkat) | Gerekince | csrfoo | seyrek |
| Designer guvenligi | Designer icin ayni kategori: kurulum, ag, kullanici, sifreleme, sertlestirme, sertifika | Kurulum | securehardendesigner ve alt sayfalari | sik |
| Self-Service X sertlestirme | SSX icin sertlestirme onerileri | Kurulum | setupsechardeningssx | seyrek |
| Yonetici ortaminda kurulum | akış otomasyonu servislerini yonetici olmayan kullanici ile calistirma | Kurulum | runooservicesnonadmin | sik |

### 4.9 Lisans

| ozellik | ne_yapar | admin_isi | kaynak | agirlik |
|---|---|---|---|---|
| Lisans yonetimi (AutoPass) | Deneme lisansi, dugum tabanli lisans (node-based), eszamanli workflow lisanslari; lisans sunucu arayuzu | Kurulum ve yenileme | setupoolicense | cekirdek |
| Lisans dosyasi ve rapor (akış komut aracı) | license-file-import ve license-report komutlari | Otomasyon | ooshsystemconfiguration | sik |

### 4.10 Kurulum sonrasi sistem ayarlari

| ozellik | ne_yapar | admin_isi | kaynak | agirlik |
|---|---|---|---|---|
| Dil ayari | Kurulum dili ve tarayici dili; desteklenmeyen dilde Ingilizce | Kurulum | changelanguage, setbrowserlanguage | seyrek |
| Servis adi | central-wrapper.conf ile servis adini ve aciklamasini degistirir | Degisiklik | changeservicename | seyrek |
| Veritabani degisiklikleri | Veritabani IP'si, sifresi degisimi (Designer dahil) | Degisiklik | changedbip, changedatabasepassword | sik |
| Ana bilgisayar adi/IP | Central, RAS ve Designer icin ad/IP degisimi | Degisiklik | changehostnameip | sik |
| Python Executor | Central, RAS ve Designer'a gomulu Python calistirici; yerel worker ile iletisim | Yapilandirma | configurepythonexecutor | seyrek |
| RabbitMQ kuyrugu | Surum yukseltmede kuyruk yapilandirmasi | Yukseltme | rpaqueueconfig | sik |
| Icerik paketi import boyutu | Designer'a yuklenebilecek icerik paketi boyut siniri (varsayilan 200 MB) | Ayar | configurecpimportsize | seyrek |
| Designer proxy | Designer ayarlar panelinden proxy | Ayar | configureproxydesigner | seyrek |
| Git deposu | Yerel Git deposu olusturma (Designer) | Kurulum | creategitrepository | seyrek |
| Designer kayit ve calistirma ayarlari | RPA kaydedici portu ve Kaydet ve Calistir ayarlari | Kurulum | configureoorecorderport, configurerecordrunsettings | seyrek |
| Robot sonuc arsivi | Robot yurutme sonuclarini arsivleme | Ayar | configurerobotexecutionresultsarchive | seyrek |
| Gelismis sistem ozellikleri | Robot ve Recorder servislerinin yerel sistem hesabi veya bir yonetici hesabi ile calismasi | Kurulum | advancedconfigsysprop | seyrek |

### 4.11 Icerik paketi yonetimi (Administer)

| ozellik | ne_yapar | admin_isi | kaynak | agirlik |
|---|---|---|---|---|
| Icerik paketi tanitim (promosyon) | Ortamlar arasi (dev, test, prod) tasima, sonuc ongorulebilirligi | Dagitim sureci | promotecp, promotecpsteps | cekirdek |
| Icerik paketi dagitimi | Central'e icerik paketi dagitimi, dagitim istatistikleri | Dagitim | deploymanagecp | cekirdek |
| Akis kutuphanesi ve akis haritasi | Dagitilmis flow'lari gezme, filtreleme, akis grafigi | Gunluk | manageflowlibrary, flowmap | sik |
| Yapilandirma ogeleri | Dagitimdan sonra sistem hesabi ve ozelliklerini ayarlama | Her ortam | setupconfigitems | cekirdek |
| Test ve sorun giderme | Staging'de icerik paketini test etme | Dagitim oncesi | testtroubleshootcp | sik |

### 4.12 Operasyon ve sorun giderme

| ozellik | ne_yapar | admin_isi | kaynak | agirlik |
|---|---|---|---|---|
| Sistem yapilandirmasi kurulumu | Genel ayar, guvenlik ayarlari ve sistem yapilandirmasi | Kurulum | setupsystemconfigurationoo | cekirdek |
| Sistem ayarlari ve gunluk ayarlari | Yukardaki basliklar | Kurulum | setsystemsettings, logginglevels | sik |
| Yapilandirma ogeleri degisikligi | Kurulumda sistem ayari degistirme (akış komut aracı ssc komutu ile de) | Degisiklik | systeminformationsettings (REST), ooshsystemconfiguration | sik |

### 4.13 Use Designer tarafindaki yonetim (akış otomasyonu Workflow Designer)

| ozellik | ne_yapar | admin_isi | kaynak | agirlik |
|---|---|---|---|---|
| Designer yonetici gorevleri | Kurulum sonrasi ilk gorevler, tekrarlayan gorevler | Kurulum | initialdesignertasks, recurringdesignertasks | sik |
| IdM Admin kullanimi | IdM yonetici konsolu ile Designer kullanici yonetimi | Kurulum | managedatabaseuser | sik |
| Designer proxy ve Recorder | Proxy, RPA kaydedici ve terminal emulator yapilandirmasi | Kurulum | configureproxydesigner, configureoorecorderport, configureterminalemulator | seyrek |

## 5. Bolum: Komut satiri araclari

### 5.1 akış komut aracı (Central komutlari)

akış komut aracı komutlari (akış otomasyonu Central'a bagli calisir). Tam liste: ooshreferencetitle sayfasi. Kategoriler:

| kategori | komut | ne_yapar | kaynak |
|---|---|---|---|
| Baglanti | connect | Central sunucusuna baglanir (--url, --user, --password gibi argumanlar) | ooshcentralconnection |
| Baglanti | disconnect | Baglantiyi keser | ooshcentralconnection |
| Baglanti | show connection | Mevcut baglanti bilgisini gosterir | ooshcentralconnection |
| Icerik yonetimi | deploy | Icerik paketi dagitir (baglanti gerekir) | ooshcontentmanagement |
| Icerik yonetimi | lcp / list-content-packs | Icerik paketlerini listeler | ooshcontentmanagement |
| Icerik yonetimi | finfo / flow-info | Flow bilgisini verir | ooshcontentmanagement |
| Calistirma yonetimi | trigger | Flow calistirir (key=value girdiler) | ooshrunmanagement |
| Calistirma yonetimi | track | Run'i izler; durum, sonuc bilgisini gosterir | ooshrunmanagement |
| Sistem yapilandirma | ssc / set-sys-config | Sistem yapilandirmasi ayarlar (ornek: X-Frame-Options, sertifika subject/SAN ayarlari) | ooshsystemconfiguration |
| Lisans | license-file-import | Lisans dosyasini iceri alir | ooshsystemconfiguration |
| Lisans | license-report | Lisans raporunu verir | ooshsystemconfiguration |
| Yukseltme | import-historical-data / historical-data-status / historical-data-start-date | Gecmis veriyi iceri alir; durumu verir; baslangic tarihini belirler | ooshupgrade |
| Yukseltme | import-permissions / permissions-status / upload-permissions-file | Izinleri iceri alir; durum; dosya yukleme | ooshupgrade |
| Yukseltme | import-schedules | Zamanlamalari iceri alir | ooshupgrade |

### 5.2 akış yönetim aracı (Studio ve icerik gelistirme komutlari)

| komut | ne_yapar | kaynak |
|---|---|---|
| createCP | Studio veya CloudSlang projesinden icerik paketi olusturur (AFL ve CloudSlang icerigi dahil); test-project ve template-project ile proje olusturma | ooshapackaging |
| scan | Proje veya icerik paketini tarar | ooshascancp |
| validatePlatforms | Icerik paketini farkli akış otomasyonu platform surumlerine karsi dogrular | ooshavalidateplatform |
| help, exit/quit, cls/clear, version, date | Yardim, cikis, ekran temizleme, surum ve tarih | ooshacommandline |
| system properties | Sistem ozelliklerini gosterir | ooshacommandline |
| logs, sifreleme | akış yönetim aracı loglari; akış yönetim aracı sifreleme yapilandirmasi | ooshacommandline |

Kurulum: akış yönetim aracı bagimsiz kurulabilir veya akış otomasyonu ile birlikte gelir (ooshaintroduction).

### 5.3 Icerik uretme ve sihirbazlar

| arac | ne_yapar | kaynak |
|---|---|---|
| REST sihirbazi | Swagger, RAML, WADL tanimlarindan (URL veya yerel dosya) akış otomasyonu flow'lari uretir | restwizardintro |
| Icerik Ureticisi (REST) | Swagger 1.0, 2.0, 3.0 (OpenAPI) ve web uygulama tanimlarindan CloudSlang projesi uretir | generatecontentrestapi |
| Web servisi sihirbazi | WSDL'den akış otomasyonu flow'lari uretir (wswizard) | wswizardintro |
| Shell sihirbazi | Shell komutlarini akış otomasyonu flow'larina donusturur | shellwizardintro |
| PowerShell sihirbazi | Secilen PowerShell cmdlet'lerinden flow uretir; uzaktan calistirma destegi | powershellwizardintro |
| Ucuncu taraf icerik paketi sihirbazi | Gerekli ucuncu taraf JAR'lariyla icerik paketi uretir; komut satiri araci da var | thirdpartywizardintro |

## 6. Bir otomasyon ajaninin karsilamasi gereken yetenekler

1. Flow baslatma ve izleme: "Su flow'u su girdilerle baslat ve bitene kadar durumunu takip et." (POST /executions, GET /executions/{id}/summary veya akış komut aracı trigger/track)
2. Run duraklatma: "1234 numarali calisan run'i duraklat." (PUT /executions/{ids}/status, action=PAUSE; Run Explorer'da Pause)
3. Run surdurme: "Duraklatilmis run'i devam ettir." (action=RESUME)
4. Run iptali: "Takili kalan run'i iptal et." (action=CANCEL; geri alinamaz, insan onayi onerilir)
5. Run devretme: "Bu run'in sahipligini baska bir kullaniciya devret." (action=REASSIGN; Run Explorer'da Reassign). Yetki kosulu: run'a atanmis olmak veya Manage Others' Runs yetkisi.
6. Insan onayi / handoff: "Handoff bekleyen run'a onaylayiciyi ata ve girdiyi bekle." Not: belgede otomatik onay bildirimi veya REST ile handoff tetikleme uc noktasi bulunamadi; ajan yalnizca kullanici mesajina gore girdi girip "handoff" yapabilir (Central arayuzu veya run'in ilgili kullanici yetkisi gerekir).
7. Gated gecis onayi: "Rol gerektiren gecis icin rolu olan kullaniciyi bilgilendir." Not: gated gecis yalnizca belirli role sahip kullanicilarca devam ettirilebilir; ajanin rol yoksa devam ettirmesi beklenmez.
8. Yeniden calistirma: "Basarisiz run'i hata veren adimdan yeniden calistir." (GET /executions/{id}/rerunnable-steps, POST /executions/rerun). Kosul: adim rerun point olarak isaretli olmali.
9. Yeniden deneme (retry) politikasi: "Basarisiz run'i 3 kez dene." Belgede otomatik yeniden deneme yok; ajan kendi politikasini uygular ve her denemede yeniden calistirma veya yeni calistirma yapar.
10. Adim ve log inceleme: "Run'in adim listesini CSV olarak al." (GET /executions/{id}/steps?mediaType=csv) veya "Yurutme logunu getir." (GET /executions/{id}/execution-log)
11. Zamanlama yonetimi: "Bu flow'u her gun 08:00'de calistiracak zamanlama olustur." (POST /schedules); "Zamanlamayi devre disi birak." (PUT /schedules/{ids}/enabled)
12. Kullanici ve rol yonetimi: "Yeni kullaniciya END_USER rolu ata." (POST /users; roller ve gruplar)
13. Icerik paketi dagitimi: "Su icerik paketini dagitim surecine yukle ve calistir." (POST /deployments, POST /deployments/{id}/files, PUT /deployments/{id})
14. Sistem ayari degistirme: "General setting X degerini Y yap." (PUT /config/{key})
15. Veri temizligi: "90 gunden eski yurutme kayitlarini temizle." (DELETE /executions?endedBefore=...) Silme islemleri oldugu icin insan onayi onerilir.
16. Denetim sorgusu: "Son 24 saatteki denetim kayitlarini listele." (GET /audit/records, before/after parametreleri)
17. Worker ve RAS durumu: "Hangi RAS ve worker'lar aktif?" (GET /rases, GET /workers, GET /workers-groups)
18. Robot ve hedef izleme: "Kayitli robotlari ve hedef sayisini al." (GET /robots, GET /targets/count)
19. Lisans raporu: "Lisans raporunu al." (akış komut aracı license-report)
20. Veritabani sagligi: "Veritabani boyut raporunu al." (GET /db-statistics; databasehealth arayuzu)
21. Icerik paketi imzalama ve dogrulama: "Bu icerik paketini imzala ve arac JAR'larini dogrula." (jarsigner; verifyingintegrity)
22. Komut satiri otomasyonu: "akış komut aracı ile Central'a baglan, flow'u calistir, sonucu izle." (connect, trigger, track)

## 7. Ozet ve belgede bulunamayanlar

- REST uc noktasi sayisi (tabloda): yaklasik 130 yol-yontem cifti (tekil kayit, sayfalardan toplandi; bazi sayfalarda ornek uc noktalar ayrica yazilmis olabilir).
- Acik soru / belgede bulunamadi:
  - Otomatik yeniden deneme (retry) politikasi ve uc noktasi.
  - Handoff icin REST uc noktasi ve otomatik onay bildirimi.
  - Duraklatilmis run icin zaman asimi veya otomatik iptal (sayfalarda Paused-No Workers icin otomatik devam var, ancak zaman sinirı bulunamadi).
  - DELETE /content-packs/last ve POST /oo-designer/rest/v0/xfeatures/{workspace_id} uc noktalarinin ayrintili davranisi (sayfada ornek olarak geciyor).
