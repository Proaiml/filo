# OpenText akış otomasyonu 26.4 - Ozellik Envanteri

Kaynak kok: https://docs.microfocus.com/doc/397/26.4/home
Tarih: 2026-11-17 (ajan oturumu)

## 1. Kapsam ozeti

- Bu turda (ucuncu tur) 26 Studio/Designer sayfasi okundu: studiomajorsteps, transitions, createflowloop, parallelsplitsteps, multiinstancesteps, subflows, setresponses, designeradddecisionflow, robotgroupflow, workergroupstep, designervalidateflow, designerdebugflow, designerhybridauthoring, pythonoperations, setreturnsteps, regularexpressions, debuggingcomplexflows, customzingflowtransitions, advancedauthoring, usescriptletsflow, whatusesthis, inputsource, testingdebuggingflows, versionhistory, creatingcontentpack, cloudslangcontentflows. Kumulatif yaklasik 113 sayfa. 150 hedefi bu turda tutturulamadi; kalan okunmamis bolumler bolum 6'da.
- Okunan tekil sayfa (ana sayfa dahil): ilk turda yaklasik 62; ikinci turda 25 ek (ana sayfa, Integrate, Integration Central listesi, 21 entegrasyon sayfasi, tocflat.json). Toplam yaklasik 87. Her sayfanin metninin ilk 400-900 karakteri ve baslik/baglanti yapisi okundu; tam bolumler icin alt konularin hepsi ziyaret edilmedi.
- Tam sayilabilecek bolumler (kendi alt konulari ziyaret edildi): Use > akış otomasyonu Workflow Designer (ana akis konulari), Use > akış otomasyonu Central (calistirma, zamanlama, izleme, rerun, Flow Library, sistem ayarlari, guvenlik, topoloji, yedekleme, veri temizligi), Develop (genel bakis, CloudSlang gelistirme, REST API - Flow Execution kategorisi).
- Kismi kalan bolumler: Use > akış otomasyonu Studio (ana konu ve gelismis yazim alt konularinin bir kismi), Use > Wizards (3 of 5 wizard adi okundu), Use > Self-Service X (3 alt konu), Administer (Central tarafinin buyuk kismi; Designer admin gorevleri ve guvenlik sertlestirme okunmadi).
- Ikinci turda kapanan: Integrate bolumu (Integration Central listesinden 21 sayfa okundu, bkz 2.8); tam sayfa haritasi (bkz 5); REST API kategorileri ve akış komut aracı/akış yönetim aracı basliklari (bkz 2.6); Administer ve Studio/Designer alt konu basliklari (bkz 2.7 ve 5; sayfalarin cogu okunmadi, yalniz basliklar).
- Hala eksik: Integrate listesindeki ~20 entegrasyon (Hyper-V, SCVMM, KVM, Nutanix, Network Automation, NNM, NOM, Infoblox, F5, Efficient IP, Foreman, OpenNetAdmin, Zabbix, SAP LaMa, SAP S/4, OCI, Oracle Cloud DB, ABBYY, AIOps containerized, vSphere/vCenter - vSphere sayfasi bos dondu); Base content ve sunucu otomasyonu ayrintilari; Administer ve Designer icerik sayfalarinin govdeleri (IdM, LDAP, SAML, guvenlik sertlestirme, yedek, Patroni); Studio/Designer alt konularinin govdeleri; RPA Robot ve Recorder ayrintilari; Troubleshoot ve Release notes sayfalarinin govdeleri (basliklar bolum 4 ve 5'te).
- Not: Eski navigasyon eksigi giderildi. Portalin kendi kaynagi https://docs.microfocus.com/397/26.4/tocflat.json (546 kayit, ust duzey 10 bolum) okundu; bolum 5'te sayfa haritasi olarak ozetlendi. Bu kaynaktan alinan basliklar okunmus sayfa sayilmaz; agirlik ve ne_yapar sutunlari basliktan tahmindir.

Kisaltmalar: "sik" = sik kullanilan, "cekirdek" = temel, "seyrek" = nadir, "niş" = ozel senaryo. Agirlik sutunu tahmindir; belgenin kendisi bunu siniflandirmiyor.

## 2. Ozellik tablosu

### 2.1 Use > akış otomasyonu Workflow Designer

| ozellik | ne_yapar | admin_isi | kaynak | agirlik |
|---|---|---|---|---|
| Calisma alani kurulumu | Kullaniciya ozel calisma alani ve projeler; birden fazla kullanici ayni bilgisayari kullaniyorsa her biri kendi calisma alanini gorur. | Akis gelistiricinin ilk ortam kurulumu. | https://docs.microfocus.com/doc/397/26.4/setupworkspace | cekirdek (tahmin) |
| SCM (Git) baglantisi | Calisma alani basina bir Git deposu baglanir; cok yazarli calisma, degisiklik geri alma. Uzak depo olarak GitHub gibi servisler belirtilmis. | Gelistirici icin depo baglama ve yetki yonetimi. | https://docs.microfocus.com/doc/397/26.4/scmsetup | sik (tahmin) |
| Proje ve klasor olusturma | Proje/klasor adlarinda kurallar: harf, rakam, tire, alt cizgi; bosluk ve parantez yok; buyuk-kucuk harf duyarsiz; Windows ayrilmis adlari (CON, NUL, COM1 vb.) yasak. | Proje yapisinin standartlastirilmasi. | https://docs.microfocus.com/doc/397/26.4/setupdesignerproject | cekirdek (tahmin) |
| Akis olusturma | Yeni akis, adim ekleme, baslangic adimi secme, girdi/cikti tanimlama. | Akis gelistirici. | https://docs.microfocus.com/doc/397/26.4/designercreateflows | cekirdek (tahmin) |
| Gecis (navigation line) | Adimin yanit portlarini (Success, Failure, Custom) sonraki adima veya sonuc adimina baglar. Success ve Custom yanitlarin mutlaka baglanmasi gerekir; Failure baglanmasi istege baglidir. | Akis dallanmasi ve hata yollarini tasarlama. | https://docs.microfocus.com/doc/397/26.4/transitions | cekirdek (tahmin) |
| Sonuc adimlari | Akisin sonucunu veren bitis adimlari; baglanmamis Failure portu varsayilan basarisizlik adimina duser; bu varsayilan adim yapilandirilabilir. | Hata sonucu ve bitis durumlarini tanimlama. | https://docs.microfocus.com/doc/397/26.4/startendsteps | cekirdek (tahmin) |
| Dongu adimi (loop) | Bir koleksiyon uzerinde senkron dongu calistirir. Ayrica paralel dongu (asenkron, farkli baglamlarda es zamanli) vardir. | Toplu islem (ornek: liste uzerinde kontrol). | https://docs.microfocus.com/doc/397/26.4/createflowloop | sik (tahmin) |
| Akis ozellikleri (girdi/cikti) | PROPERTIES sekmesinde akis girdileri, ciktilari ve adim girdileri tanimlanir; akis alt akis olarak kullanilirsa adim girdileri de bunlardan gelir. | Veri akisini tasarlama. | https://docs.microfocus.com/doc/397/26.4/flowinputsoutputs | cekirdek (tahmin) |
| Akis hata ayiklama | Designer icinde veya akış otomasyonu Central uzerinde uzaktan debug. Uzaktan debug icin Remote Debugging izni, akış otomasyonu Central ile Designer'in ayni surumde ve ayni icerik paketi surumlerinde olmasi gerekir. | Akis gelistirme ve sorun cozme. | https://docs.microfocus.com/doc/397/26.4/designerdebugflow | sik (tahmin) |
| Icerik paketi olusturma ve dagitma | Projeyi content pack olarak disa aktarir; once gecerlilik kontrolu (gecersiz akis, karar, operasyon ya da sistem ozelligi varsa uyari). | Icerik paketini Central'a tasima. | https://docs.microfocus.com/doc/397/26.4/designercreatedeploycp | cekirdek (tahmin) |
| Operasyon yazma | Operation (CloudSlang tabanli) olusturma ve duzenleme. | Yeni operasyon yazma. | https://docs.microfocus.com/doc/397/26.4/designerauthoroperations | sik (tahmin) - okunmadi, baslik |
| Sistem ozellikleri yazma | Akislarda kullanilan sistem ozelliklerini (system properties) tanimlama ve yonetme. Belge, bu alanlara hassas olmayan bilgi konmasini onerir. | Akislarda ortak yapilandirma degerlerini merkezi tanimlama. | https://docs.microfocus.com/doc/397/26.4/authorsystemproperties | sik (tahmin) - okunmadi, baslik |
| Dis CloudSlang dosyalarini kullanma | Projeye harici CloudSlang dosyalari eklenmesi. | Harici icerik kullanimi. | https://docs.microfocus.com/doc/397/26.4/useexternalcloudslangfiles | seyrek (tahmin) - okunmadi, baslik |
| Klavye kisayollari | Designer icin klavye kisayollari listesi. | Gelistirici verimliligi. | https://docs.microfocus.com/doc/397/26.4/designerkeyboardshortcuts | seyrek (tahmin) - okunmadi, baslik |
| Proje bagimliliklari paneli | Projenin baglandigi icerik paketlerini ve bagimliliklari gosterir. | Bagimlilik kontrolu. | https://docs.microfocus.com/doc/397/26.4/designerdependenciespane | sik (tahmin) - okunmadi, baslik |

### 2.2 Use > akış otomasyonu Central (calistirma, izleme, yonetim)

| ozellik | ne_yapar | admin_isi | kaynak | agirlik |
|---|---|---|---|---|
| Central oturum acma | Kimlik dogrulama acikken giris ekrani gelir; birden fazla domain varsa secim yapilir. Kullanici adinda ":" karakteri olamaz. | Kullanici erisimi. | https://docs.microfocus.com/doc/397/26.4/centralintroduction | cekirdek |
| Dashboard / Insights-ROI | Eski (Legacy) dashboard: popular akislar, sonuc dagilimi, calisma suresi, ROI. Insights gorunumune gecis anahtari vardir. "View Dashboard" izni gerekir. | Yonetici raporlama. | https://docs.microfocus.com/doc/397/26.4/oodashboard | sik |
| Akis baslatma (Flow Launcher) | Run Management icinde agactan akis secilir, filtrelenir, girdiler girilir, kosu adi verilir ve calistirilir. | Son kullanicinin ya da operatorun akisi calistirmasi. | https://docs.microfocus.com/doc/397/26.4/runflow | cekirdek |
| Hibrit akis calistirma | CloudSlang akisinin icinde native (Studio) icerik akisi alt adimi olarak cagrilabilir (do_external etiketi ile). | Iki model arasi gecis; eski icerikle yeni akisi birlestirme. | https://docs.microfocus.com/doc/397/26.4/hybridflowexecution | niş |
| Zamanlama (Schedule) | Akis icin tek seferlik veya tekrarli zamanlama olusturma; SCHEDULER sekmesi; View Schedules ve Manage Schedules izinleri. | Periyodik kontroller (ornek: sunuculara ping). | https://docs.microfocus.com/doc/397/26.4/scheduleflowruns | cekirdek |
| Run Explorer | Calisan ve gecmis kosulari izler; otomatik yeniler; kendi ve baskalarinin kosularini yonetir. Kosu adi, zamanlama adi gosterilir. | Operasyon izleme. | https://docs.microfocus.com/doc/397/26.4/trackmanageflowruns | cekirdek |
| Adimdan yeniden calistirma (Rerun) | Basarisiz ya da iptal edilmis kosuyu belirli bir adimdan devam ettirir. Sistem ayarinda acilip kapatilir; Studio'da adim once rerun noktasi olarak isaretlenmeli. Icerdeki adimlar icin sinirlamalar vardir. | Kurtarma. | https://docs.microfocus.com/doc/397/26.4/rerunflow | sik |
| Flow Library (akis kutuphanesi) | Deploy edilmis icerik paketlerindeki akislari listeler, meta veri gosterir, son calisma raporu, persistence seviyesi, run timeout ve icerik izinlerini duzenler (Manage Content Settings izni). | Icerik yonetimi. | https://docs.microfocus.com/doc/397/26.4/manageflowlibrary | cekirdek |
| CloudSlang icerik akislari | CloudSlang 1.0 ve 2.0 surumleriyle yazilmis icerigi deploy edip calistirma; flow map; configuration item kurulumu. | CloudSlang icerigini isletmek. | https://docs.microfocus.com/doc/397/26.4/cloudslangcontentflows | sik |
| Icerik paketi yayinlama (Promote) | Op Admin icerik paketlerini yayinlar; deploy ve yonetim, akis kutuphanesi, configuration item, test/sorun giderme, Patroni sertlestirme alt konulari. | Uretime alma. | https://docs.microfocus.com/doc/397/26.4/promotecp | cekirdek |
| Rol tabanli erisim (RBAC) | Yetki (permission) tanimli rolleri olusturup kullanicilara atama. Ornek: FLOW MANAGER, END USER rolleri. | Yetki modeli. | https://docs.microfocus.com/doc/397/26.4/setuproles | cekirdek |
| Genel sistem ayarlari | Baslik metni, ROI aciklamasi, proxy/ters proxy/yuk dengeleyici ayarlari ve genel varsayilanlar. | Genel yapilandirma. | https://docs.microfocus.com/doc/397/26.4/setsystemsettings | cekirdek |
| Sistem konfigurasyonu (ust) | Guvenlik (LDAP, SAML, LW-SSO, dahili kullanicilar), topoloji (worker, RAS), lisans, DB boyutu, bildirim ve diger sistem ayarlarinin toplu sayfasi. | Kurulum sonrasi yonetim. | https://docs.microfocus.com/doc/397/26.4/setupsystemconfigurationoo | cekirdek |
| SAML 2.0 kimlik dogrulama | Non-IdM modunda SAML 2.0 ile tek oturum acma. | Kurumsal kimlik entegrasyonu. | https://docs.microfocus.com/doc/397/26.4/setupsaml | sik |
| LW-SSO | Lightweight SSO; SM ve BSM gibi diger OpenText urunleriyle paylasilan cerezle tek oturum. | Urun aile entegrasyonu. | https://docs.microfocus.com/doc/397/26.4/setupsecuritylwsso | sik |
| Dahili kullanicilar | akış otomasyonu kullanici adi ve parolasi ile dahili kullanici tanimlama; roller atanir. | Harici kimlik yoksa erisim. | https://docs.microfocus.com/doc/397/26.4/setupusers | sik |
| Worker ve RAS topolojisi | TOPOLOGY sekmesinde worker ve RAS dugumlerini yapilandirma; View/Manage Topology izinleri. | Yurutme altyapisini kurma. | https://docs.microfocus.com/doc/397/26.4/setupworkers | cekirdek |
| RAS otomatik yukseltme | RAS'i Central arayuzunden otomatik, ya da komut satirindan elle yukseltme. | Yurutucu bakimi. | https://docs.microfocus.com/doc/397/26.4/setupras | sik |
| Insights Service | SERVICES sekmesinde widget sablonlari ile istatistik; kumelenmez, tek bir akış otomasyonu dugumunde yapilandirilir. | Raporlama. | https://docs.microfocus.com/doc/397/26.4/setupinsightservice | sik |
| Database Health | Veritabani boyutunu zaman icinde izler; execution, debugger ve audit kullanimini ayirir. | Kapasite izleme. | https://docs.microfocus.com/doc/397/26.4/databasehealth | sik |
| Veri temizligi (purge) | akış otomasyonu OpenText Solutions icerik paketindeki purge akislarini zamanlayarak veritabani boyutunu kontrol etme. | Bakim, DB boyutu. | https://docs.microfocus.com/doc/397/26.4/datacleanup | cekirdek |
| Yedekleme ve kurtarma | akış otomasyonu Central ve Workflow Designer icin yedek alma ve geri yukleme adimlari. | Felaket oncesi koruma. | https://docs.microfocus.com/doc/397/26.4/backupoo | sik |
| Felaket kurtarma | Ikincil veri merkezi icin veritabani, sema ve guvenlik/yapilandirma dosyalarini replike etme. | Is surekliligi. | https://docs.microfocus.com/doc/397/26.4/disasterrecovery | seyrek |
| Baslangic ve periyodik idare gorevleri | Baslangic: IdM, sistem konfigurasyonu, worker/RAS, RabbitMQ kuyrugu, lisans, Python executor, dil, log seviyesi, servis adi, oturum zaman asimi, veri temizligi, iletisim protokolleri. Periyodik: parola sifreleme, DB parola/IP degisimi, host IP, LB URL, yedekleme, tuning. | Kurulum ve bakim kontrol listesi. | https://docs.microfocus.com/doc/397/26.4/initialootasks , https://docs.microfocus.com/doc/397/26.4/recurringootasks | cekirdek |
| PostgreSQL HA (Patroni) | Patroni kumesi ile PostgreSQL yuksek erisilebilirlik. | Veritabani HA. | https://docs.microfocus.com/doc/397/26.4/postgresqlha | niş |

### 2.3 Use > akış otomasyonu Self-Service X

| ozellik | ne_yapar | admin_isi | kaynak | agirlik |
|---|---|---|---|---|
| Web arayuzu erisimi | Son kullanici web arayuzu (https://<fqdn>:8446/oo-ssx) ve PA Mobile uzerinden erisim. Yayinlanmis senaryolari arayip birkac tiklamayla calistirir. | Son kullanici kanali. | https://docs.microfocus.com/doc/397/26.4/accessselfservicex | cekirdek |
| Kategori ve senaryo yonetimi | Yonetici arayuzunde kategori olusturma (ad, aciklama, ikon) ve senaryo yonetimi. Kategori/senaryo icin Central rolunde manageCategory / manageScenario izni gerekir. Kategoriler Swagger API ile de yonetilebilir. | Katalog duzenleme. | https://docs.microfocus.com/doc/397/26.4/managessx | sik |
| Kategori alt konulari | Kategoriler sayfasi (okunmadi, sadece baslik). | Katalog. | https://docs.microfocus.com/doc/397/26.4/selfservicexcategories | sik (tahmin) - okunmadi |
| SSX guvenlik sertlestirme | Guvenlik sertlestirme alt konusu (okunmadi, sadece baslik). | Guvenlik. | https://docs.microfocus.com/doc/397/26.4/useselfserviceorchestration | sik (tahmin) - okunmadi |

### 2.4 Use > akış otomasyonu Studio (masaustu yazim araci)

| ozellik | ne_yapar | admin_isi | kaynak | agirlik |
|---|---|---|---|---|
| Studio bagimsiz yazim | Akis olusturma, duzenleme, test etme ve icerik paketi uretme icin bagimsiz program. Ekran ogeleri, ana adimlar, dil ayarlari. | Akis gelistirici masaustu araci. | https://docs.microfocus.com/doc/397/26.4/studioauthoring | cekirdek |
| Alt akis (subflow) | Akisin bir kismini alt akis adimi olarak ayirir; parcalari ayri test etme ve yeniden kullanma. | Modulerlik. | https://docs.microfocus.com/doc/397/26.4/subflows | cekirdek |
| Paralel bolunme (parallel split) | Her biri bir serit (lane) olan adim dizilerini es zamanli calistirir; farkli isleri bagimsiz yapmak icin. | Paralel is kollari. | https://docs.microfocus.com/doc/397/26.4/parallelsplitsteps | cekirdek |
| Coklu ornek adimi (multi-instance) | Bir adim veya adim grubunu girdi listesindeki her hedef icin es zamanli calistirir (ornek: 100 sunucuda ayni tani akisi). | Toplu hedef uzerinde calistirma. | https://docs.microfocus.com/doc/397/26.4/multiinstancesteps | cekirdek |
| Duzenli ifade (regex) | Sonuc/cikti filtreleri ile veri ayiklama, degiskene kaydetme. | Veri ayrıstirma. | https://docs.microfocus.com/doc/397/26.4/regularexpressions | sik |
| Scriptlet kullanimi | Operasyon/akis icinde Nashorn veya Rhino JavaScript scriptlet; girdi/sonuclari filtreler, yanit belirler, alt akis verisini ana akisa hazirlar. Global degiskenler: ${execution_userid}, ${run_id}, ${execution_thread_id}. Sistem ozelligine tam yolla referans verilir. Sablonlar ve Configuration\Scriptlets klasoru. | Ozel mantik ve veri donusumu. | https://docs.microfocus.com/doc/397/26.4/usescriptletsflow | sik (okundu) |
| Gecis ozellestirme | Gecis cizgisini yuvarlak/duz yapma, koseleri ve ara noktalari (vertex) duzenleme; gorsel duzen. Kosul ya da mantik degil. | Akis gorseli. | https://docs.microfocus.com/doc/397/26.4/customzingflowtransitions | seyrek (okundu) |
| Return adimlari | Akis sonu adimlari: Resolved, Diagnosed, No Action Taken, Error. Ad "Error: failure" bicimindedir ve yanit degistirilebilir. Akis birden fazla return adimi tasiyabilir. | Akis sonucu ve hata sonuclari. | https://docs.microfocus.com/doc/397/26.4/setreturnsteps | cekirdek (okundu) |
| Akis dogrulama (Problems) | Problems panelinde hatalari listeler; konum ve aciklama verir. | Kalite kontrol. | https://docs.microfocus.com/doc/397/26.4/debuggingflows | cekirdek |
| Test ve hata ayiklama | Debugger ile hata nedenini izleme; karmasik akis debug ve uzak Central ile debug. | Sorun cozme. | https://docs.microfocus.com/doc/397/26.4/debuggingflows | cekirdek |
| Bellek sinirlamasi uyarisi | Sonsuz dongu gibi sinirsiz buyuyen akislar Run History'yi buyutur ve bellek tukenir; bu tip akislardan kacinilmali. | Tasarim kisiti. | https://docs.microfocus.com/doc/397/26.4/advancedauthoring | kisit |
| Dongu ayrintilari (okundu) | Dongu adimi: For degiskeni, In koleksiyonu (akis degiskeni, sistem ozelligi, virgullu metin, Python ifadesi), Break On sonuc noktalari, cikti toplama icin Python ifadesi. Son iterasyonun degeri varsayilan cikti. Paralel dongu AFL adimlarinda desteklenmez. | Toplu isleme ve kirma kosulu. | https://docs.microfocus.com/doc/397/26.4/createflowloop | sik |
| Paralel bolunme kisitlari (okundu) | Serit (lane) icinde response adimi olamaz; paralel bolunme engellemeyen (non-blocking) degildir; bitis yaniti done ile sonraki adima baglanir. Serit siralamasi gorsel olup calisma sirasini etkilemez. | Paralel is kollari tasarimi. | https://docs.microfocus.com/doc/397/26.4/parallelsplitsteps | cekirdek |
| Coklu ornek ayrintilari (okundu) | Her ornek girdi listesinin bir elemaniyla calisir; ornekler baglam kopyasi alir; bir ornekteki hata yalniz o orneği durdurur. Eszamanli ornek sayisi sabit ya da ${degisken} ile sinirlanabilir (sistem ozelligi olamaz). Ornek degiskenleri ancak sonuc (result) veya kapsam ile disari aktarilir. | Hedef listesi uzerinde toplu calisma. | https://docs.microfocus.com/doc/397/26.4/multiinstancesteps | cekirdek |
| Alt akis sonuclari (okundu) | Alt akisin sonuclari akis cikti alani olarak ust akisa verilir. Atama eylemleri: OVERWRITE, APPEND, PREPEND, ADD, SUB, MULTIPLY, DIVIDE. | Veri aktarimi. | https://docs.microfocus.com/doc/397/26.4/subflows | cekirdek |
| Yanit tipleri ve kurallari (okundu) | Operasyon yanit tipleri: Resolved, Diagnosed, No Action Taken, Error. Yanit kurali kosula baglanir; sirayla degerlendirilir, ilk eslesen secilir. Default ve On-Fail isaretleri vardir. | Sonuc yonlendirme. | https://docs.microfocus.com/doc/397/26.4/setresponses | cekirdek |
| Karar adimi (okundu) | Decision read-only bir adimdir; Dependencies panelinden suruklenir; akis yonunu hesaplar; ad kurallari: alfasayisal ve alt cizgi; parantez, koseli parantez, suslu parantez, tire, bosluk ve nokta yok. | Dallanma hesabi. | https://docs.microfocus.com/doc/397/26.4/designeradddecisionflow | sik |
| Robot ve worker grubu (okundu) | RPA etkinligi bir robot grubuna atanabilir; grup yoksa RabbitMQ'da kuyruk olusur. Worker grubu icin Set Worker Group; Force override in subflows secenegi alt akislara uygulanir. | Yurutme yonlendirme. | https://docs.microfocus.com/doc/397/26.4/robotgroupflow ve workergroupstep | sik |
| Yerel ve uzak debug (okundu) | Yerel debug yalniz CloudSlang akis ve operasyonlarinda; breakpoint, girdi istemi (input prompt) destekler. Uzak debug icin Remote Debugging izni, Central ve Designer ayni surum ve ayni icerik paketi surumleri. Kisayollar Alt+F11 (baslat), Alt+F12 (iptal). | Sorun cozme. | https://docs.microfocus.com/doc/397/26.4/designerdebugflow | sik |
| Dogrulama (okundu) | Akis hatalari kirmizi alt cizgi, bayrak ve Problems ile gosterilir; hatali icerik paketi disa aktarilmaz; eksik bagimlilik gri seritli adim olarak gorunur. | Kalite kontrol. | https://docs.microfocus.com/doc/397/26.4/designervalidateflow | cekirdek |
| Hibrit yazim (okundu) | Native akış otomasyonu icerik paketi adimlari ve CloudSlang adimlari ayni akista baglanabilir; sistem hesabi, sistem ozelligi ve yapilandirma ogesi baglantisi native adimlarda devre disi. | Iki model gecisi. | https://docs.microfocus.com/doc/397/26.4/designerhybridauthoring | niş |
| Python operasyonu (okundu) | Yeni operasyonlar Python 3.x; yeni Jython operasyonu olusturulamaz, mevcut Jython operasyonlari calismaya devam eder. | Python ile operasyon yazma. | https://docs.microfocus.com/doc/397/26.4/pythonoperations | sik |
| Regex filtreleri (okundu) | Java tarzi duzenli ifade; tum girdi veya satir satir filtre; buyuk-kucuk harf yok sayma. Cikti ayiklama, degiskene kaydetme, girdi dogrulama. | Veri ayiklama. | https://docs.microfocus.com/doc/397/26.4/regularexpressions | sik |
| Referans analizi (okundu) | "What uses this?" ve "What does this use?" ile operasyon/akis bagimliliklari gorulur; degisiklik oncesi kontrol onerilir. | Degisiklik etkisi analizi. | https://docs.microfocus.com/doc/397/26.4/whatusesthis | sik |
| Surum gecmisi (okundu) | Her kaydetmede yeni yerel surum; onceki surumu acma, farkli adla kaydetme, geri yukleme, iki surumu karsilastirma. SCM ile paylasilan depo surumleri icin onerilmez. | Yerel geri alma. | https://docs.microfocus.com/doc/397/26.4/versionhistory | cekirdek |
| Icerik paketi olusturma (okundu) | Gecersiz akis/operasyon (ornegin yinelenen UUID) pakete girmez. Her paketleme varsayilan olarak bir sonraki surum numarasini alir; klasor iceren yapilandirma bolumleri eski Studio surumlerinde iceri alinamaz. | Yayin hazirligi. | https://docs.microfocus.com/doc/397/26.4/creatingcontentpack | cekirdek |
| CloudSlang 1.0 ve 2.0 icerik akislari (okundu) | CloudSlang 1.0 ve 2.0 icerigi deploy edilip calistirilabilir; dosya uzantilari .sl, .sl.yaml, .sl.yml; operasyon eylemi Python ya da Java ile yazilir. | Eski CloudSlang icerigini isletme. | https://docs.microfocus.com/doc/397/26.4/cloudslangcontentflows | sik |
| Girdi kaynagi (okundu) | Girdi kaynaklari: sabit deger, ayni adli degisken, baska bir girdi, ifade. Degisken yoksa "Otherwise" (varsayilan Use Constant). | Veri akisi tasarimi. | https://docs.microfocus.com/doc/397/26.4/inputsource | cekirdek |
| Debug test ve kurulum (okundu) | Debugger akis agacini, adim sonuclarini ve degiskenleri gosterir; breakpoint ve yanit zorlama. Sifreli/gizli girdi degerleri ******** olarak gorunur ve yeniden girilmelidir. Central kimlik dogrulamasi acikken debug kimlik bilgisi ister. | Sorun giderme. | https://docs.microfocus.com/doc/397/26.4/testingdebuggingflows | cekirdek |
| Paralel ve coklu ornek debug sinirlari (okundu) | Debugger, paralel ve coklu ornekleri gercek calismayi birebir yansitmaz; sonuc sirasi kontrol edilebilir; staging ortaminda ayrica test onerilir. | Test stratejisi. | https://docs.microfocus.com/doc/397/26.4/debuggingcomplexflows | cekirdek |

### 2.5 Use > Wizards, CLI, PA Mobile

| ozellik | ne_yapar | admin_isi | kaynak | agirlik |
|---|---|---|---|---|
| akış otomasyonu Wizards (5 adet) | Studio'da sihirbazlar: REST wizard (URL veya yerel API tanimindan akis uretir), Third Party Content Pack wizard (3. parti jar'lu icerik paketi), Web Services wizard (servis tanimindan akis), Shell wizard ve PowerShell wizard (PowerShell remoting ve sorun giderme alt konulari var). Shell ve PowerShell sihirbazlari yalniz basliktan bilinir (tocflat); icerik okunmadi. | Entegrasyon akislarini hizli uretme. | https://docs.microfocus.com/doc/397/26.4/wizardsuse | sik |
| Komut satiri (akış komut aracı / akış yönetim aracı) | akış komut aracı ile Central komutlari; akış yönetim aracı ile Studio yazim komutlari terminalden calistirilir. PowerShell sihirbazi sorun giderme bolumu var. | Otomasyon ve toplu islem. | https://docs.microfocus.com/doc/397/26.4/commandlineinterface | sik |
| PA Mobile | Process Automation Mobile uygulamasi (iOS, Android): Central dashboard ve Self-Service X'e mobil erisim. | Mobil izleme. | https://docs.microfocus.com/doc/397/26.4/usepamobile | seyrek |

### 2.6 Develop (icerik gelistirme ve API)

| ozellik | ne_yapar | admin_isi | kaynak | agirlik |
|---|---|---|---|---|
| Icerik gelistirme (extension) | Java, .NET veya Python ile action yazilip extension olarak paketlenir; Central veya Workflow Designer'a dagitilir. Operasyonlar bu action'lar uzerine kurulur. | Yeni yetenek ekleme. | https://docs.microfocus.com/doc/397/26.4/developcontent | cekirdek |
| CloudSlang icerik gelistirme | Maven artifact'lari ile CloudSlang icerik gelistirme. Gereksinimler: Java 1.8, Maven 3.3.9. Action gelistirme Java veya Python bilgisi ister. | Icerik gelistirici. | https://docs.microfocus.com/doc/397/26.4/cloudslangcontentdevelopment | sik |
| REST API (v2) | Public API HTTP tabanli, RESTful, JSON. Surum on eki: /oo/rest/v2/ (ornek: /oo/rest/v2/executions). Yeni surumlerde opsiyonel alanlar eklenebilir. | Dis sistemlerle entegrasyon. | https://docs.microfocus.com/doc/397/26.4/apiintro | cekirdek |
| Flow Execution API | Akis calistirma ve izleme endpoint'leri: GET /executions (sayfalama: pageNum, pageSize; filtre: flowPath, status); execution summary, execution step count, steps (sayfali, filtreli), tek adim, adimlar CSV ya da metin olarak, execution log, rerunnable steps, rerun from step, delete rerun data, delete steplog data, get akış otomasyonu version, "Execute a flow by UUID". | Otomasyonun akis baslatmasi ve izlemesi. | https://docs.microfocus.com/doc/397/26.4/restapis | cekirdek |
| Flow Execution - ek uclar (baslik) | Durum degistirme (changeexecutionstatus), akis durumu (flowexecutionstatus), akis girdisi (flowinput), debugger olaylarini ve adim verisini temizleme (purgedebuggerexecution, purgeexecutionstepdata), adim logu silme (deletesteplogdata). Yalniz basliklardan bilinir. | Calisan kosulari yonetme ve veri temizligi. | https://docs.microfocus.com/doc/397/26.4/restapis (tocflat) | sik (tahmin) - okunmadi |
| Flow Library API (baslik) | Akis kutuphanesi uzerinden REST erisimi. | Akis katalogu sorgulama. | https://docs.microfocus.com/doc/397/26.4/flowlibrary (tocflat) | sik (tahmin) - okunmadi |
| Scheduler API (baslik) | Zamanlanmis kosu yonetimi icin REST uclari. | Zamanlama otomasyonu. | https://docs.microfocus.com/doc/397/26.4/scheduler (tocflat) | sik (tahmin) - okunmadi |
| Deployment API (baslik) | Deployment sureci dosyasi yukleme, deployment calistirma, surec nesnesini alma ve icerik paketini surecten silme (deploycontentpacks, uploaddeploymentprocess, runspecificdeployment, getdeploymentprocess, deletedeploymentcp). | Icerik paketi dagitimini API ile yapma. | https://docs.microfocus.com/doc/397/26.4/deploymentcp (tocflat) | orta (tahmin) - okunmadi |
| Queue, Content packs, Configuration items API (baslik) | RabbitMQ kuyruk yapilandirmasi, icerik paketi listesi, yapilandirma ogeleri (configuration items) uclari. | Icerik ve yapilandirma yonetimi. | https://docs.microfocus.com/doc/397/26.4/queueconfigrabbitmq , contentpacks , configurationitemscontent (tocflat) | orta (tahmin) - okunmadi |
| Audit events API (baslik) | Denetim olaylarini sorgulama. | Denetim ve uyumluluk raporu. | https://docs.microfocus.com/doc/397/26.4/auditevents (tocflat) | orta (tahmin) - okunmadi |
| LDAP, LW-SSO, User authentication, Users, Roles API (baslik) | LDAP yapilandirmasi, LWSSO yapilandirmasi, kullanici kimlik dogrulamasi, kullanici ve rol uclari. | Kimlik ve yetki otomasyonu. | https://docs.microfocus.com/doc/397/26.4/ldapconfiguration , lwssoconfiguration , userauthentication , users , roles (tocflat) | orta (tahmin) - okunmadi |
| Workers, Firewall friendly APIs, Target tracking, RPA Robot APIs (baslik) | Worker listesi ve durumu, guvenlik duvari dostu API seti, hedef izleme, RPA Robot API'leri. | Topoloji ve RPA entegrasyonu. | https://docs.microfocus.com/doc/397/26.4/workers , firewallfriendlyapis , gettargets , robotapis (tocflat) | seyrek (tahmin) - okunmadi |
| System information, log level, akış otomasyonu version, System notifications API (baslik) | Sistem bilgisi ve ayarlari, sistem log seviyesi, akış otomasyonu surum bilgisi (getooversion), sistem bildirimleri. | Izleme ve surum raporu. | https://docs.microfocus.com/doc/397/26.4/systeminformationsettings , getsystemloglevel , getooversion , systemnotifications (tocflat) | orta (tahmin) - okunmadi |
| Dashboard, Basic authentication, CSRF API notlari | Dashboard verisi, temel kimlik dogrulama ve CSRF korumasi icin API notlari. | API guvenlik ayarlari. | https://docs.microfocus.com/doc/397/26.4/dashboard , basicauthentication , csrfprotectionoo (tocflat) | orta (tahmin) - okunmadi |
| Self-Service X API (baslik) | Self-Service X kategori ve senaryo API'si (Swagger). | Katalog otomasyonu. | https://docs.microfocus.com/doc/397/26.4/selfservicexapis (tocflat) | sik (tahmin) - okunmadi |
| akış komut aracı (komut satiri, Central) (baslik) | Central komutlari: baglanti, icerik yonetimi, run management, sistem konfigurasyonu, akış komut aracı yukseltme. | Betikli Central yonetimi. | https://docs.microfocus.com/doc/397/26.4/oosh (tocflat) | sik (tahmin) - okunmadi |
| akış yönetim aracı (komut satiri, Studio) (baslik) | Studio yazim komutlari: giris, komut satiri kullanimi, icerik paketi olusturma (packaging), platform dogrulama (validate platform), icerik paketi tarama (scan content pack). | CI hattinda dogrulama ve paketleme. | https://docs.microfocus.com/doc/397/26.4/oosha (tocflat) | sik (tahmin) - okunmadi |
| Icerik gelistirme (ek alt konular, baslik) | AFL icerigi, Java action'lari icin plugin gelistirme, en iyi uygulamalar, scriptlet ve deprecation klasoru, CloudSlang plugin'leri, Maven ile icerik paketi derleme (buildcpmaven), icerik paketi surumleme, Maven proje yapisi, islem sirasi. | Icerik gelistiricinin standart kaynaklari. | https://docs.microfocus.com/doc/397/26.4/developcontent alt konulari (tocflat) | orta (tahmin) - okunmadi |

### 2.7 Administer (ek, okunmadi bolumler)

| ozellik | ne_yapar | admin_isi | kaynak | agirlik |
|---|---|---|---|---|
| Designer admin gorevleri | Designer yonetimi (okunmadi, sadece baslik). | Designer yonetimi. | https://docs.microfocus.com/doc/397/26.4/oodesigneradmintasks | sik (tahmin) - okunmadi |
| Guvenlik sertlestirme | Central icin sertlestirme (okunmadi, sadece baslik). | Guvenlik. | https://docs.microfocus.com/doc/397/26.4/securehardenintro | sik (tahmin) - okunmadi |
| IdM yonetimi | Kimlik yonetimi (IdM) kurulumu (okunmadi, sadece baslik). | Kimlik. | https://docs.microfocus.com/doc/397/26.4/administeridm | sik (tahmin) - okunmadi |
| Python executor | Python executor yapilandirmasi (okunmadi, sadece baslik). | Python yurutme. | https://docs.microfocus.com/doc/397/26.4/configurepythonexecutor | seyrek (tahmin) - okunmadi |
| RPA kuyruk yapilandirmasi | RabbitMQ kuyrugu (okunmadi, sadece baslik). | Kuyruk. | https://docs.microfocus.com/doc/397/26.4/rpaqueueconfig | seyrek (tahmin) - okunmadi |
| IdM ve kimlik dogrulama alt konulari (tocflat basliklari) | Kullanici ekleme (adduserscenario), kullanici/grup/rol yonetimi, izin gorunumu; kimlik dogrulama: LDAP, SAML, OAuth (Azure AD) yapilandirmasi. | Kimlik ve erisim kurulumu. | https://docs.microfocus.com/doc/397/26.4/administeridm , manageauthentication , ldapauthentication , samlauthentication , oauthconfiguration (tocflat) | sik (tahmin) - okunmadi |
| Guvenlik sertlestirme alt konulari (tocflat basliklari) | Guvenlik kavramlari, guvenli kurulum ve dagitim, ag guvenligi, yonetim arayuzu guvenligi, kullanici yonetimi, yetkilendirme, IdM moduna gecis, sifreleme, sertlestirme onerileri, sunucu/istemci sertifikasi, TLS yapilandirmasi, dosya sistemi kisitlama (minimizerisk), Java guvenlik yoneticisi, HTTPS yonlendirme, CSRF devre disi birakma. | Guvenlik sertlestirme kontrol listesi. | https://docs.microfocus.com/doc/397/26.4/securehardenintro , hardeningoo , configtls , minimizerisk , enableredirect (tocflat) | sik (tahmin) - okunmadi |
| Yedekleme, felaket kurtarma, tuning, Patroni (tocflat basliklari) | Central ve Designer yedekleme, veri merkezi felaket kurtarma, sistem ayarlama, Patroni kumesi kurulum ve sertlestirme. | Is surekliligi ve PostgreSQL HA. | https://docs.microfocus.com/doc/397/26.4/backupoo , disasterrecovery , systemtuningoo , postgresqlha , installpatronicluster (tocflat) | orta (tahmin) - okunmadi |
| Designer yonetimi alt konulari (tocflat basliklari) | Proxy yapilandirmasi, RPA Recorder portu, kayit-calistirma ayarlari, terminal emulatoru, Git deposu olusturma, icerik paketi import boyutu, Designer guvenligi ve sertlestirmesi, Designer veri yedegi, sifreleme, guvenlik soru-cevaplari. | Designer kurulum ve bakim. | https://docs.microfocus.com/doc/397/26.4/oodesigneradmintasks alt konulari (tocflat) | orta (tahmin) - okunmadi |
| Self-Service X guvenlik sertlestirme (tocflat basligi) | SSX icin guvenlik ve sertlestirme. | SSX guvenligi. | https://docs.microfocus.com/doc/397/26.4/setupsechardeningssx (tocflat) | orta (tahmin) - okunmadi |
| Akis yonetimi ve icerik paketi yayinlama (tocflat basliklari) | Icerik paketi yayinlama adimlari, dagitim ve yonetim, akis kutuphanesi yonetimi, akis grafigi, yapilandirma ogeleri, test ve sorun giderme. | Uretime alma sureci. | https://docs.microfocus.com/doc/397/26.4/promotecp alt konulari (tocflat) | sik (tahmin) - okunmadi |
| Central, RAS ve robot yonetim gorevleri (tocflat basliklari) | Worker ve robot topolojisi, kimlik bilgisi sifreleme, DB parola/IP degisimi, host IP ve LB URL degisimi, dil ve log seviyesi, oturum zaman asimi, iletisim protokolleri. | Periyodik bakim. | https://docs.microfocus.com/doc/397/26.4/recurringootasks , initialootasks (tocflat) | orta (tahmin) - okunmadi |

### 2.8 Integrate (entegrasyon sayfalari, ikinci tur)

Kaynak: https://docs.microfocus.com/integration/Operations_Orchestration/all (Integration Central listesi) ve her entegrasyonun kendi sayfasi (URL: .../all/<AdiAltCizgili>). Her satir genel bakis sayfasindan alindi; "agirlik" tahmindir. Surum desteği tablolari okundu ama ayrintili akis listesi tek tek acilmadi.

| ozellik | ne_yapar | admin_isi | kaynak | agirlik |
|---|---|---|---|---|
| Amazon AWS | EC2 ve RDS kullanim durumlari icin akis ve operasyonlar. Surumler 2022.05-2023.05. Content pack OpenText Marketplace'ten indirilir. | Bulut sanal makine ve veritabani otomasyonu. | .../all/Amazon_AWS | sik (tahmin) |
| Alibaba Cloud | Alibaba Cloud yonetim akislari ve operasyonlari (veri depolama, iliskisel veritabani, CDN, Anti-DDoS vb. hizmetler icin). | Bulut yonetimi. | .../all/Alibaba_Cloud | seyrek (tahmin) |
| Google Cloud Platform | Sanal makine baslatma, yeniden baslatma, olcekleme ve yonetimi. | Bulut VM yasam dongusu. | .../all/Google_Cloud | seyrek (tahmin) |
| Microsoft Azure | Azure Active Directory: Microsoft Graph API ile kullanici ve lisans yonetimi. | Kimlik ve lisans otomasyonu. | .../all/Microsoft_Azure | orta (tahmin) |
| Microsoft 365 | Microsoft Graph API ile e-posta ve kullanici yonetimi. | Office 365 hesap islemleri. | .../all/Microsoft_365 | orta (tahmin) |
| Citrix XenServer | Citrix XenServer sanal makine, sunucu, ag ve depolama yonetimi. akış otomasyonu Virtualization Content Pack'in parcasi (Zen Server 5.0). | Sanallastirma yonetimi. | .../all/Citrix_XenServer | seyrek (tahmin) |
| Cloud Management (HCMX) | Design and Deploy icinde containerized akış otomasyonu ile gorev plani is akislari; bildirim gonderme ve is kurali aksiyonlari. | Kurumsal bulut hizmet tasarimi. | .../all/Cloud_Management | orta (tahmin) |
| CyberArk PAM | Ayricalikli hesap kesfi, tanimlama (onboarding) ve yonetimi (CyberArk 12.x). | Hesap ve parola otomasyonu. | .../all/CyberArk | niş (tahmin) |
| Data Center Automation (DCA) | DCA ile uzak agda akış otomasyonu RAS uzerinden ajansiz (agentless) yonetim. | Uzak ag operasyonlari. | .../all/Data_Center_Automation | orta (tahmin) |
| Docker | Docker bilesenlerini (17.03) otomatik yonetme akis ve operasyonlari. | Konteyner yonetimi. | .../all/Docker | seyrek (tahmin) |
| Hashicorp Terraform | Terraform modullerini deploy, undeploy ve guncelleme (0.12.x). | Altyapi kodu entegrasyonu. | .../all/Hashicorp_Terraform | seyrek (tahmin) |
| Kubernetes | Namespace, Node, Pod, Service, ReplicationController ve Deployment nesneleri icin akis ve operasyonlar. | Kubernetes is yuku yonetimi. | .../all/Kubernetes | orta (tahmin) |
| ServiceNow | Change, Incident, Problem ve Generic Record yonetimi (Istanbul, Geneva, Fuji ve sonrasi, Helsinki). | ITSM kaydi otomasyonu. | .../all/ServiceNow | sik (tahmin) |
| Service Manager (SM) | Change Management icinde RFC olusturma, guncelleme, kapatma ve sorgulama. | ITSM degisiklik otomasyonu. | .../all/Service_Manager | sik (tahmin) |
| Service Management (SMAX) | REST API ile ITIL kayitlarinin otomasyonu. | ITSM kaydi otomasyonu. | .../all/Service_Management | sik (tahmin) |
| Universal Discovery and CMDB (UCMDB) | akış otomasyonu akislari ile UCMDB arasinda iletisim. | CMDB sorgu ve guncelleme. | .../all/Universal_Discovery_and_CMDB | orta (tahmin) |
| Operations Manager (OBM) | OBM operatorlerinin akış otomasyonu ile arastirma araclari ve servis iyilestirme betiklerini calistirmasi. | Olay yanit otomasyonu. | .../all/Operations_Manager | orta (tahmin) |
| Oracle Database Server | CloudSlang Base Content Pack ile SQL sorgulari, betikler ve komutlar (12c, 18c, 19c, 21c). | Veritabani sorgu otomasyonu. | .../all/Oracle_Database_Server | orta (tahmin) |
| PostgreSQL | PostgreSQL sunucu saglama (Windows Server ve RedHat). | Veritabani kurulum otomasyonu. | .../all/PostgreSQL | seyrek (tahmin) |
| Veritas NetBackup | Politika tabanli SLA yedekleme, isteğe bagli yedekleme yasam dongusu ve worker group'a gore saglayici yapilandirmasi. | Yedekleme otomasyonu. | .../all/Veritas_NetBackup | orta (tahmin) |
| VMware vSphere | Sayfa acildi ama icerik donmedi (okunamadi). | Sanallastirma yonetimi. | .../all/vmWare_vSphere | (okunamadi) |

Entegrasyon listesinde olup bu turda okunmayanlar: Hyper-V, SCVMM, KVM, Nutanix Prism, Network Automation, Network Node Manager, Network Operations Management, Infoblox, F5 BigIP, Efficient IP DDI, Foreman, OpenNetAdmin, Zabbix, SAP Landscape Management, SAP S/4 HANA, Oracle Cloud Databases, Oracle Cloud Infrastructure, ABBYY Cloud OCR, AI Operations Management (Containerized), VMware vCenter. Base content, sunucu otomasyonu (sunucu otomasyonu) ve SSH/PowerShell/WinRM ayrintilari Integration listesinde ayri bir kalem olarak gorulmedi; bunlar Integrate ana sayfasinda "Integration Central" yonlendirmesiyle geciyor.

## 3. Dinamik bir otomasyon ajaninin karsilamasi gereken yetenekler

Bu liste yukaridaki envanterden turetilmistir. Tekrarsiz, numarali.

### 3.1 Akis motoru yetenekleri (ayrik alt baslik)

1. Dallanma: adimin Success/Failure/Custom yanitlarina gore farkli adima gecis (Transitions). Ornek: "Basarisiz olursa yedek sunucuya gec, basarili olursa raporla."
2. Varsayilan basarisizlik sonucu: baglanmamis Failure yanitinda varsayilan hata sonucu ve bu sonucun ozellestirilmesi. Ornek: "Hata olunca ozel bildirim gonder."
3. Sonuc adimlari (result steps): akisin bitis durumunu ve ciktilarini belirleme. Ornek: "Akis sonucu 'Tamamlandi' ya da 'Kismi' olarak donsun."
4. Paralel bolunme (parallel split): birbirinden bagimsiz is kollarini es zamanli calistirma. Ornek: "Ayni anda hem DNS hem disk kontrolu yap."
5. Coklu ornek (multi-instance): ayni adimi bir hedef listesi uzerinde es zamanli calistirma. Ornek: "Bu betigi 100 sunucunun tamamina ayni anda uygula."
6. Senkron dongu (loop): koleksiyon uzerinde sirayla islem. Ornek: "Her IP icin ping at ve sonucu topla."
7. Paralel dongu: koleksiyon uzerinde asenkron islem. Ornek: "Her hesap icin es zamanli parola sifirlama baslat."
8. Alt akis (subflow): tekrar kullanilabilir parca olarak akis cagirma. Ornek: "Windows saglik kontrolunu alt akis olarak diger akislara bagla."
9. Hibrit akis: CloudSlang akisi icinde native icerik alt adimi calistirma. Ornek: "Yeni CloudSlang akisi icinde eski Studio akisini cagir."
10. Duraklat ve surdurme: okunan 26 Studio/Designer sayfasinda duraklatma/surdurme adimi bulunamadi. Baslikta yalniz "Flows enter into Pause - No Workers in Group" ve "Paused - No Robots in Group" hata durumlari var (bkz bolum 4). Belgede bulunamadi.
11. Insan onayi: okunan sayfalarda kullanici onayi, insan girdisi isteme veya devretme adimi bulunamadi. Yalniz CloudSlang girdi istemi (input prompt) yerel debug icinde geciyor; bu bir calisma zamani onay adimi degil. Belgede bulunamadi.
12. Zamanlama (schedule): tek seferlik ve tekrarli calistirma. Ornek: "Her gece 02:00'de veritabani purge akisini calistir."
13. Hata isleme (error handling): Failure yanitlari, sonuc adimlari, varsayilan hata sonucu. Ornek: "Failure olursa e-posta bildirimi yap ve kaydi kapat."
14. Yeniden deneme (retry): okunan sayfalarda adim duzeyinde retry alani bulunamadi; yeniden calistirma yalnizca adimdan rerun ile (madde 15). Belgede bulunamadi.
15. Adimdan yeniden calistirma (rerun from step): basarisiz/iptal kosuyu belirli bir adimdan devam ettirme; rerun noktasi Studio'da isaretlenir. Ornek: "Dun 3. adimda biten kosuyu 3. adimdan devam ettir."
16. Bellek ve dongu kisiti: sonsuz dongu ve sinirsiz gelisen akislardan kacinma. Ornek: "Uzun sureli izleme icin dongu yerine zamanlama kullan."
17. Regex ile cikti ayiklama: sonuc/cikti filtresi ve degiskene kaydetme. Ornek: "Komut ciktisindan IP adresini ayikla."
18. Scriptlet kullanimi: akis icinde script parcasi. Ornek: "Bir degeri ozel formatta donusturmek icin scriptlet calistir."
19. Gecis ozellestirme: adim gecislerinin kosullarini ozellestirme. Ornek: "Sadece belirli durumda ek adima git."
20. Return adimi: akistan erken donus. Ornek: "Ön koşul saglanmazsa akisi hemen bitir."
21. Akis girdi ve ciktileri: akis duzeyinde tanimli degerler, adim girdi/ciktilari. Ornek: "Akis girdisi olarak sunucu adini al, ciktisi olarak sonucu don."
22. Akis ozellikleri ve sistem ozellikleri: akislar arasi ortak degerleri merkezi tanimlama (belge hassas bilgi icin bu alanlari onermez). Ornek: "Ortak hedef ortam adini sistem ozelligi olarak tanimla."
23. Hata ayiklama (debug): Designer ya da Central uzerinde adim adim izleme. Ornek: "Basarisiz akisi uzaktan debug ederek hangi adimda koptugunu bul."
24. Dogrulama (Problems): kayit oncesi hata kontrolu. Ornek: "Yayinlamadan once tum gecersiz baglantilari listele."
25. Icerik paketi olusturma/dagitma: akisi tasinabilir pakete cevirme. Ornek: "Gelistirme ortamindaki akisi uretim ortamina paketle."

### 3.2 Yonetim ve operasyon yetenekleri

26. Akis kutuphanesinde arama ve filtreleme. Ornek: "Adinda 'SQL' gecen tum akislari listele."
27. Akis baslatma (Flow Launcher): girdileri girerek calistirma. Ornek: "Yetkili kullanici sunucu adini girip disk temizligi akisini baslatsin."
28. Calisma adi (run name) verme ve izleme. Ornek: "Bu kosuyu 'Ocak bakim' adiyla isaretle."
29. Run Explorer ile kosu izleme ve yonetme. Ornek: "Son 1 saatte basarisiz olan kosulari getir."
30. Kosu iptal etme ve kosu duraklatma ile devam ettirme. Belgede iptal (cancel) isleminin varligi ima edilir (Run Management); duraklatma/surdurme acik dogrulanmadi.
31. Gecmis kosu raporu (Flow Library uzerinden son calisma raporu). Ornek: "Bu akisin son 30 gundeki calisma sonuclarini goster."
32. Akis persistence seviyesi ve run timeout ayari. Ornek: "Bu akisin calisma suresini 30 dakika ile sinirla."
33. Icerik izinleri (content permissions). Ornek: "Yalnizca Ekip A bu akisi calistirabilsin."
34. Akis zamanlama (create, view, manage). Ornek: "Haftalik zamanlama olustur ama duzenleme yetkisini sadece yoneticilere ver."
35. Calisma verilerini purge ile temizleme. Ornek: "90 gunden eski kosu kayitlarini sil."
36. Veritabani boyutu izleme (Database Health). Ornek: "Veritabani buyumesini son 6 ay icin grafikle goster."
37. Dashboard ve Insights/ROI raporlari. Ornek: "Ayin en cok calisan 5 akisini ve tahmini tasarrufu goster."
38. Insights Service ile widget istatistikleri. Ornek: "Akis sonuc dagilimi widget'ini yeni sablonla ekle."
39. Rol olusturma ve atama (RBAC). Ornek: "FLOW MANAGER rolune akis calistirma ve zamanlama izinleri ver."
40. Dahili kullanici olusturma. Ornek: "Dis sistem icin dahili bir servis kullanicisi olustur."
41. LDAP kimlik dogrulama. Ornek: "Kullanicilar kurumsal dizin hesabiyla girsin."
42. SAML 2.0 ile tek oturum acma. Ornek: "Kurumsal IdP uzerinden SSO ile giris."
43. LW-SSO ile urun aile arasi tek oturum acma. Ornek: "SM web istemcisinden gecen kullanici akış otomasyonu'ya otomatik girsin."
44. Worker ve RAS topolojisi yonetimi. Ornek: "Yeni RAS dugumunu topolojiye ekle."
45. RAS otomatik yukseltme. Ornek: "Tum RAS'lari yeni surume otomatik yukselt."
46. Sistem ayarlari (proxy, ters proxy, LB, genel). Ornek: "Central'in arkasina yeni yuk dengeleyici URL'sini tanimla."
47. Lisans kurulumu ve izleme. Ornek: "Lisans suresi dolmadan once uyari al."
48. Sistem bildirimleri ve e-posta bildirimi. Ornek: "Bir akis basarisiz olunca yonetici e-postasina bildirim gonder."
49. Dil ayarlari (akış otomasyonu bilesenleri ve tarayici dili). Ornek: "Arayuzu Turkce goster."
50. Log seviyesi ayarlama. Ornek: "Gecici olarak debug log seviyesini ac."
51. Oturum zaman asimi ayari. Ornek: "Oturumu 30 dakika bosta kalinca kapat."
52. Servis adi degistirme. Ornek: "Central servis adini kuruma uygun isimle guncelle."
53. Parola sifreleme/obfuscation. Ornek: "Yapilandirma dosyasindaki veritabani parolasini sifrele."
54. Veritabani parolasi ve IP degisikligi. Ornek: "Veritabani sunucusu tasindiginda baglanti bilgisini guncelle."
55. Yedekleme ve geri yukleme. Ornek: "Gece yedegi al ve test ortaminda geri yukleme dene."
56. Felaket kurtarma replikasyonu. Ornek: "Ikincil veri merkezine veritabani ve guvenlik dosyalarini replike et."
57. Icerik paketi yayinlama (promote). Ornek: "Test icerik paketini uretime yayinla."
58. Icerik paketi dagitma ve akis kutuphanesine alma. Ornek: "Yeni paketi yukle ve akislarini kutuphanede goster."
59. Configuration item tanimlama (icerik paketi icin). Ornek: "Akis icin hedef sunucu adini yapilandirma ogesi olarak tanimla."
60. Akis grafigi (flow map) goruntuleme. Ornek: "Bu akisin adim grafigini goster."
61. Akis test ve sorun giderme (icerik paketi duzeyi). Ornek: "Yeni paketi uretim oncesi test kosusuyla dogrula."

### 3.3 Gelistirici ve entegrasyon yetenekleri

62. Akis gelistirme (Designer ve Studio). Ornek: "Yeni akis olustur, 3 adim ekle, basari ve hata yollarini bagla."
63. Operasyon yazma (CloudSlang). Ornek: "Yeni bir HTTP cagrisi operasyonu yaz ve akisa bagla."
64. Java, .NET, Python action yazma ve extension paketleme. Ornek: "Python ile ozel bir action yaz ve Central'a dagit."
65. Maven ile CloudSlang icerik gelistirme. Ornek: "Maven projesi ile yeni CloudSlang icerigi derle."
66. Git (SCM) ile surum kontrolu. Ornek: "Proje degisikliklerini uzak depoya gonder ve geri al."
67. Icerik paketi olusturma ve disa aktarma. Ornek: "Projeyi 1.2 surumu icerik paketi olarak paketle."
68. Sablonlardan akis uretme (REST wizard). Ornek: "Bu API tanimindan otomatik akis uret."
69. Web Services wizard ile akis uretme. Ornek: "WSDL'den servis cagrisi akislari olustur."
70. Ucuncu parti icerik paketi sihirbazi. Ornek: "Eksik bir jar icin 3. parti icerik paketi uret."
71. Komut satirindan Central komutu calistirma (akış komut aracı). Ornek: "Betik icinden akis baslat ve sonucu bekle."
72. Komut satirindan Studio komutu calistirma (akış yönetim aracı). Ornek: "CI hattinda akisi dogrula."
73. Akis calistirma REST API ile (UUID ile). Ornek: "Dis sistem UUID ile akisi baslatsin."
74. Kosu listesi REST API ile sayfalama ve filtreleme. Ornek: "Akisa gore son 500 kosuyu cek."
75. Kosu ozeti ve log cekme REST API ile. Ornek: "Basarisiz kosunun logunu ticket sistemine ekle."
76. Adim listesi ve tek adim bilgisi REST API ile. Ornek: "Kosunun adim sonuclarini CSV olarak indir."
77. Adim listesi CSV ve metin disa aktarimi. Ornek: "Gunluk raporu CSV olarak arsivle."
78. Rerunnable adimlari listeleme ve adimdan yeniden calistirma (REST). Ornek: "Basarisiz kosu icin yeniden calistirilabilir adimlari getir ve 4. adimdan baslat."
79. Rerun verisini silme. Ornek: "Eski rerun verilerini temizle."
80. Steplog verisini silme. Ornek: "Eski adim loglarini temizle."
81. akış otomasyonu surum bilgisini sorgulama (REST). Ornek: "Kurulu akış otomasyonu surumunu otomasyon raporuna ekle."
82. Self-Service X kategori ve senaryo yonetimi (Swagger API). Ornek: "Yeni 'Ag' kategorisini ve senaryolarini API ile olustur."
83. Self-Service X son kullanici akis calistirma. Ornek: "Yetkili kullanici katalogdan 'Parola sifirla' senaryosunu baslatsin."
84. PA Mobile ile dashboard ve SSX erisimi. Ornek: "Nobetci mobil cihazdan basarisiz kosulari gorsun."
85. Remote debugging (uzaktan hata ayiklama) izni. Ornek: "Yalnizca gelistirici rolune uzaktan debug izni ver."
86. Yeni surumlerde opsiyonel API alanlarina dayanikli istemci. Ornek: "Dis entegrasyon bilinmeyen alanlari yok saysin."

### 3.4 Dis sistem entegrasyonu (belgede gorulen kapsam)

87. REST tabanli entegrasyon ve REST wizard. Ornek: "Bir REST API'sini akış otomasyonu akisina cevir."
88. Web servisi entegrasyonu (Web Services wizard). Ornek: "SOAP servisini cagiran akis uret."
89. Sistem bildirim e-postasi. Ornek: "Basarisiz kosu icin e-posta gonder."
90. Ters proxy ve yuk dengeleyici arkasinda calisma. Ornek: "akış otomasyonu'yu kurumsal ters proxy arkasina al."
91. CloudSlang icerigi calistirma (1.0 ve 2.0 surumleri). Ornek: "Eski CloudSlang 1.0 akisini calistir."
92. Hibrit icerik (CloudSlang + native). Ornek: "Yeni akis icinde eski native alt adimi cagir."
93. Remote Action Server uzerinden yurutme (RAS). Ornek: "Uzak ağdaki sunucuda komut calistir."
94. Worker uzerinden yurutme. Ornek: "Belirli bir worker grubunda calisan akis."

(Not: Ikinci turda entegrasyon listesi ve 21 entegrasyon sayfasi okundu; bkz 2.8. Bu yeteneklerin tam kapsami icin asagidaki 3.5 bolumune bakin. SSH, PowerShell/WinRM ve e-posta icin ayri sayfa bu turda dogrulanmadi.)

### 3.5 Ikinci turda eklenen yetenekler (entegrasyon ve API)

87. Bulut VM ve RDS yonetimi (AWS, Google Cloud, Alibaba). Ornek: "Gece bakim penceresinde test VM'lerini durdur, sabah baslat."
88. Microsoft Graph uzerinden kullanici, lisans ve e-posta yonetimi (Azure AD, Microsoft 365). Ornek: "Ayrilan calisanin hesabini ve lisansini kaldir."
89. ITSM degisiklik kaydi acma, guncelleme ve kapatma (Service Manager RFC). Ornek: "Onayli degisiklik icin RFC acip sonucu kapat."
90. ITIL kayitlarini REST ile yonetme (SMAX). Ornek: "Olay kaydini SMAX'te ac ve atamayi ayarla."
91. ServiceNow incident, change, problem ve generic record islemleri. Ornek: "Monitoring alarmindan ServiceNow incident'i olustur."
92. UCMDB ile CMDB sorgu ve guncelleme. Ornek: "Yeni sunucu kaydini CMDB'ye isle."
93. OBM olay yanit betigi olarak akis tetikleme. Ornek: "Operatör OBM'den disk temizligi akisini baslatsin."
94. Kubernetes nesneleri uzerinde islem (Pod, Deployment, Service vb.). Ornek: "Deployment'i yeniden olceklendir."
95. Terraform modulu deploy, undeploy ve guncelleme. Ornek: "Gelistirme ortaminda Terraform modulunu kaldir."
96. Veritabanina SQL sorgusu ve betik calistirma (Oracle). Ornek: "Gunluk tablo boyutunu sorgula ve raporla."
97. PostgreSQL sunucu saglama (Windows Server ve RedHat). Ornek: "Yeni PostgreSQL sunucusunu hazirla."
98. Politika tabanli yedekleme ve isteğe bagli yedekleme (NetBackup). Ornek: "Kritik sunucu icin on-demand yedek baslat."
99. DCA uzerinden RAS ile ajansiz uzak ag yonetimi. Ornek: "Uzak agdaki sunucuda yama durumunu kontrol et."
100. Citrix XenServer VM, host ve depolama yonetimi. Ornek: "Host'taki VM'leri bakim icin tasi."
101. CyberArk ile ayricalikli hesap onboarding ve yonetimi. Ornek: "Yeni servis hesabini kasaya ekle."
102. Cloud Management (HCMX) gorev plani akislari ile is kurali aksiyonlari. Ornek: "Talep onaylaninca bildirim gonder ve gorevi baslat."
103. REST ile deployment sureci yukleme ve calistirma (Deployment API). Ornek: "Icerik paketini otomatik dagit."
104. Denetim olaylarini sorgulama (Audit events API). Ornek: "Son 7 gunde yapilan kimlik degisikliklerini getir."
105. akış otomasyonu surum bilgisini ve sistem log seviyesini REST ile okuma. Ornek: "Her gece akış otomasyonu surumunu ve log seviyesini raporla."
106. Scheduler REST API ile zamanlanmis kosular. Ornek: "Zamanlamayi API ile listele ve duraklat."
107. Flow Library REST API ile akis katalogu sorgulama. Ornek: "Bu icerik paketindeki akislari listele."
108. Calisan kosunun durumunu degistirme ve debugger/adim verisi temizleme (Flow Execution ek uclari). Ornek: "Takili kalan kosuyu durdur ve adim verisini temizle."
109. akış komut aracı ile Central komutlari (baglanti, icerik, run management). Ornek: "CI betiginden kosu baslat ve sonucu bekle."
110. akış yönetim aracı ile icerik paketi olusturma, platform dogrulama ve tarama. Ornek: "Paketi uretmeden once platform dogrulamasi yap."
111. Self-Service X API ile katalog kategori ve senaryo yonetimi. Ornek: "Yeni senaryo kaydini Swagger ile olustur."
112. Shell ve PowerShell sihirbazlariyla akis uretme (basliklardan). Ornek: "PowerShell komutlarini akış otomasyonu akisina cevir."
113. Java action icin plugin gelistirme ve Maven ile icerik paketi derleme. Ornek: "Maven ile yeni CloudSlang icerik paketi derle."
114. Icerik paketi surumleme ve Maven proje yapisi. Ornek: "Paket surum numarasini artirip derle."
115. Yapilandirma ogeleri (configuration items) ile icerik paketine parametre tanimlama. Ornek: "Hedef ortam adini yapilandirma ogesi yap."
116. Sistem bildirimleri ile e-posta uyari gonderme (admin). Ornek: "Kritik hatada yonetici e-postasina bildirim."
117. Worker ve robot topolojisi ile is yukunu gruplara ayirma. Ornek: "Robot grubunu bolgeye gore ayir."

118. Karar adimi (Decision): read-only karar adimi, akis yonunu hesaplar. Ornek: "Ping suresi esigi asildiysa uyari dalina, degilse bitise git."
119. Dongu kirma (Break On): dongu, secilen sonuc noktasinda erken biter. Ornek: "Ilk bos sunucu bulununca donguyu kir."
120. Dongu toplama: cikti Python ifadesiyle tum iterasyonlar uzerinden hesaplanir. Ornek: "Her IP icin ping suresini toplayip ortalama don."
121. Paralel dongu kisiti: AFL adimlarinda paralel dongu desteklenmez. Ornek: "AFL akisini paralel dongude calistirmaya calis (belgede yasak)."
122. Coklu ornek kisma (throttling): ayni anda calisan ornek sayisini sabit ya da degiskenle sinirla. Ornek: "100 sunucuyu ayni anda degil 10'ar 10'ar calistir."
123. Coklu ornek sonuc toplama: ornek sonuclarini OVERWRITE, APPEND, PREPEND, ADD, SUB, MULTIPLY, DIVIDE ile birlestir. Ornek: "Her sunucunun hata sayisini topla."
124. Paralel bolunme kisiti: serit icinde yanit adimi yok; bitis yalniz done ile ilerler. Ornek: "Paralel bolunmede bir serit kosulu ile akisi erken bitirme." (belgede yasak)
125. Yanit kurali ve sira: yanit kurallari sirayla degerlendirilir; ilk eslesen yanit secilir; Default ve On-Fail isaretleri. Ornek: "Port acik ise Basarili, degilse Hata yanitini sec."
126. Return tipleri: Resolved, Diagnosed, No Action Taken, Error. Ornek: "Esik degeri asilmadiginda 'Error: threshold not met' sonucu don."
127. Gecis ROI degeri: her navigasyona ROI degeri atanir ve Central ROI istatistiginde toplanir. Ornek: "Otomatik onarim dalina 15 dk ROI degeri ver."
128. Yerel ve uzak debug: CloudSlang akislari yerelde breakpoint ile; uzak debug icin Remote Debugging izni ve surum uyumu. Ornek: "Uretimdeki akisi Central'da uzaktan debug et."
129. Scriptlet globalleri: ${execution_userid}, ${run_id}, ${execution_thread_id} okunabilir. Ornek: "Kosu kimligini log satirina yaz."
130. Regex tabanli cikti ayiklama: Java tarzi ifade; satir satir ya da tum girdi; buyuk-kucuk harf yok sayma. Ornek: "Komut ciktisindan IP adreslerini cikar."
131. Hibrit yazim: native ve CloudSlang adimlari ayni akista. Ornek: "Eski native alt akisi yeni CloudSlang akisina bagla."
132. Python 3.x operasyon: yeni Python operasyonu olustur; Jython olusturulamaz. Ornek: "Yeni bir Python operasyonu yaz ve akisa ekle."
133. Icerik paketi dogrulamasi: duplicate UUID ve gecersiz ogeler pakete girmez. Ornek: "Paketlemeden once gecersiz ogeleri listele."
134. Surum gecmisi: yerel surumleri goruntule, geri yukle, farklari karsilastir. Ornek: "Dunku surume don ve farklari goster."
135. Referans analizi: bir akisi degistirmeden once onu kullanan akislari listele. Ornek: "Bu operasyonu kullanan tum akislari bul."
136. Girdi kaynagi ve varsayilan: girdi sabit, degisken, baska girdi ya da ifade olabilir; degisken yoksa Otherwise. Ornek: "Degisken yoksa 'varsayilan' sabitini kullan."
137. Worker grubu zorlamasi: Set Worker Group ile adim ya da alt akis grubu zorla. Ornek: "Bu akisin tum adimlarini Bolge-B worker grubunda calistir."
138. Robot grubu atamasi: RPA adimini robot grubuna ata; grup yoksa kuyruk olusur. Ornek: "SAP islemlerini SAP robot grubuna yonlendir."
139. CloudSlang 1.0/2.0 calistirma: eski surum icerigi ayni yurutucuyle calistirma. Ornek: "Eski 1.0 akisini mevcut Central'da calistir."
140. Akis doğrulama kapsami: belgede akis tasarim kisitlari (alan adlari, ekran buyuklugu 1280x1024 onerisi) var. Ornek: "Akisin tuvale sigip sigmadigini kontrol et."

### 3.6 Kapsam notu ve dogrulanmamis yetenekler

- Insan etkilesimi (onay, kullanici girdisi isteme, devretme, gecit): okunan 26 Studio/Designer sayfasinda yok; tocflat basliklarinda da yok. Belgede bulunamadi.
- Adim duzeyinde retry: okunan sayfalarda bulunamadi. Belgede bulunamadi.
- Duraklat/surdur: okunan sayfalarda bulunamadi (bkz madde 10). Belgede bulunamadi.

## 4. Belgede duyurulan sinirlar, kaldirilanlar, bilinen sorunlar

Kaynak: Enhancements, Deprecation and obsolescence, General troubleshooting ve ilgili konu sayfalari.

- Kaldirilan ozellik (deprecation): RPA bilesenleri Robot ve Recorder 26.2.1'den itibaren kullanimdan kaldirilmis (deprecated). Surekli desteklenir, yeni kurulum icin onerilmez; yeni ozellik gelmez.
- Obsolete (artik desteklenmeyen) ortam: PostgreSQL 14.x (26.4), SUSE Enterprise Linux 12.x (25.4), PostgreSQL 13.x (25.4), Windows 2012 ve 2012 R2 (25.2, yukseltme senaryolari dahil), RHEL 7.9 (24.4), PostgreSQL 12.x (24.4), CentOS 7.9 (24.1.1), PostgreSQL 11.x (listede kesildi, tam liste okunmadi).
- Enhancements (26.4): Multi-Instance (MI) Recovery iyilestirmesi - yinelenen dal birlestirmelerini onleme, kurtarma ile ilgili yurutme mesajlarinin tamamlanmasi, kurtarma islemesinin optimize edilmesi, bellek kullaniminin azaltilmasi.
- Sinir: Central kullanici adinda ":" karakteri kabul etmez.
- Sinir: Insights Service kumelenemez; tek bir akış otomasyonu dugumunde yapilandirilmalidir.
- Sinir: Akislarda sonsuz dongu ve sinirsiz buyuyen tasarimlar bellek tukenmesine yol acar.
- Sinir: Uzaktan debug icin Central ve Designer ayni surumde ve ayni icerik paketi surumlerinde olmalidir.
- Sinir: Adimdan yeniden calistirma icin adim Studio'da rerun noktasi olarak isaretlenmelidir; belgede icerideki adimlar icin ek bir sinirlama vardir (tam metin okunamadi).
- Sinir: Self-Service X'te kategori yonetimi icin Central'da manageCategory ve senaryo icin manageScenario izinleri gerekir; kategoriler icin Swagger API onerilir.
- Sinir: Designer'da ad kurallari (bosluk ve parantez yasak, Windows ayrilmis adlari yasak).
- Sinir: Failure yanitlari zorunlu degildir, ancak Success ve Custom yanitlar mutlaka baglanmalidir.
- Sorun giderme: Genel sorun giderme sayfasi, yukseltme basarisiz olursa kurtarma ve geri alma (rollback) adimlarini kapsar. Central, RAS, Designer, Studio, RPA Robot, RPA Recorder, Self-Service X, RAS ve Studio sihirbazlari icin ayri sorun giderme sayfalari vardir; bunlarin icerigi okunmadi.
- Kapsam notu: Release notes ana sayfasi ve "Fixed issues" bolumu okunmadi; bu nedenle surum bazinda duzeltilen hatalarin listesi eksiktir.
- Sorun giderme basliklari (tocflat; sayfalar okunmadi, yalniz baslik): OOM Metaspace hatasi; "insufficient entropy pool" nedeniyle akış otomasyonu baslangici takilmasi; Python 3.12 sozdizimi degisiklikleri; yukseltme sonrasi yedek bozulmasi ve IdM/SAML yukseltme sorunlari; RPA Central 25.2 Java 17 yukseltmesi; RC4 sifre paketi guvenlik riski; "Flows enter into Pause - No Workers in Group" durumu; "Paused - No Robots in Group" durumu; multi-instance akislarin RUNNING'de takilmasi; Central IdM modunda akis kutuphanesi donmasi; Designer'da Linux uzerinde .Net operasyon sorunu; Studio'da SCM (Git/SVN) hatalari.
- Dikkat: "Pause - No Workers in Group" ve "No Robots in Group" durumlari, duraklatma/surdurme yeteneginin (3.1 madde 10) belgede bir tur oldugunu gosteriyor; ancak bu sorunlar yetenek degil, hata durumlaridir.
- Studio/Designer'da "Mapping group alias" ve worker/robot grubu eslestirme sorunlari, Designer'da adim grup atamasi (robotgroupflow, workergroupstep) ile iliskilidir (basliktan).

## 5. Sayfa haritasi (tocflat.json, 546 kayit)

Kaynak: https://docs.microfocus.com/397/26.4/tocflat.json . Asagida seviye 2 dugumleri ve altlarindaki slug'lar (sayfa adi = https://docs.microfocus.com/doc/397/26.4/<slug>). Basliklar okunmadigi icin bu bolum yalniz adres haritasidir.

- Home: home
- Release notes: releasenotes; enhancements, fixeddefects, deprecations, releaselog
- Get started: getstarted; processes, personas, ooarchitecture, ooui, licenses, ooglossary
- Install: install; plan (deploymentarchitecture, planauthentication, performancebenchmark, supportmatrix, virtualsystem, performancesizinginfo); prepare (preinstallationtasks, setupqueevn, setupdatabaseoo [sqloo, sqlmaintenanceoo, oracledb, oraclemaintenanceoo, deploypostgresoo, postgresmaintenanceoo, otherdboo], setupdatabaseood [sqlserverdesigner, oracledesigner, postgresdesigner, otherdbdesigner], setupssxdatabase [deploymssqldbssx, deployoraclessx, deploypostgresssx, otherdbssx]); deploy (cleaninstallation [installcentral, oorobotinstall, installcleandesigner, oorecorderinstall, installrasclean, installselfserviceorchestration, installstudioclean, cleaninstallall, clusterinstallation], silentinstall [silentinstalloo, silentinstalldesigner, silentinstallssx, silentinstallrecorder, silentinstallrobot]); oophshelpconfig; postinstallation (runooservicesnonadmin, dbpurging); uninstalloo; silentuninstalloocomponents
- Upgrade: upgradeintroduction; upgradetonewversions (setupras); upgraderollback
- Integrate: integrate (alt sayfalar Integration Central'da, bkz 2.8)
- Administer: administer; oocentraladmintasks [initialootasks (administeridm [adduserscenario, manageusers, managegroups, manageroles, viewpermissionsidm, manageauthentication [ldapauthentication, samlauthentication, oauthconfiguration]]), setupsystemconfigurationoo [securitysettings, setuproles, setupsystemmgmt, setupusers, setupsaml, setupsecuritylwsso [lwsso]], rpaqueueconfig, setsystemsettings, configurepythonexecutor, setupoolicense, databasehealth, sendemailnotifications, setupinsightservice, changelanguage, setbrowserlanguage, logginglevels, changeservicename, timeout, datacleanup, specifycommunicationprotocols]; recurringootasks [setupworkers, setuptopologyrobot, obfuscateencrypt, changedatabasepassword, changedbip, changehostnameip, raschangeurl, backupoo, disasterrecovery, systemtuningoo]; postgresqlha [postgesqlhapatroni, installpatronicluster, hardeningpatronicluster]; promotecp [promotecpsteps, deploymanagecp, manageflowlibrary, flowmap, setupconfigitems, testtroubleshootcp]; securehardenintro [securityconceptsoo, secureimpldepl, installationsecurity, networksecurity, adminsecurity, usersecurity, authorization, idmmode, encryption, hardeningoo [hardeningrecommendations, replacesslcert, authenticateservercertificate, clientcertificate, signingoocontent, verifyingintegrity, configtls, minimizerisk, addingjsm, enableredirect, csrfoo]]; oorobotadmintasks [advancedconfigsysprop, configurerobotexecutionresultsarchive]; oodesigneradmintasks [initialdesignertasks (configureproxydesigner, configureoorecorderport, configurerecordrunsettings [configureterminalemulator]), recurringdesignertasks (creategitrepository, configurecpimportsize), securehardendesigner (securityconceptsdesigner, securedepldesigner, installationsecuritydesigner, networksecuritydesigner, usersecuritydesigner, backupdesignerdata, encryptiondesigner, securityqadesigner, hardendesigner [hardeningrecommendationsdesigner, replacesslcertdesigner, authenticatecertificatedesigner])]; setupsechardeningssx
- Use: useoodesigner [designerkeyboardshortcuts, managedatabaseuser, setupworkspace, scmsetup, setupdesignerproject, designerdependenciespane, useexternalcloudslangfiles, designerauthoring [designercreateflows (useunderlyingvariables, newflow, createstepsflow, transitions, startendsteps, flowinputsoutputs, stepinputsoutputs, expressioneditor, extractandmodifyoutputvalues, designeradddecisionflow, robotgroupflow, workergroupstep, startstep, createflowloop, viewcloudslangcode, yamlfiletextual, designervalidateflow, cloudslangprompts), designerauthoroperations [pythonoperations], designerhybridauthoring, authorsystemproperties, designerdebugflow, authoraflprojectswfd [viewaflflowswfd, editaflflowswfd, stepinspectorwkfdesigner, aflmiedit]], useoorecorder [rpaactivityadvancededit], objectidentificationdesigner, designercreatedeploycp, generatecontentrestapi]; usingcentral [centralintroduction, oodashboard, runningflows (runflow, hybridflowexecution, rerunflow, scheduleflowruns, trackmanageflowruns, filterflows, testtroubleshootflowrun, embedcentralui)]; useselfserviceorchestration [accessselfservicex, managessx, selfservicexcategories]; studioauthoring [studioscreenelements, studiomajorsteps, navigatingoostudio, workingdifferentlanguages, workingprojects (workingmultipleworkspaces, managingprojects, managingfolders), workingsourcecontrol (workingsvn, workinggit), workingcontentpacks (importingcontentpacks, managingcontentpacks, creatingcontentpack), configuringproject (workingcis, configurecategory, configuredomainterm, configuregroupaliases, configurerolealiases, configurescriptlet, configureselectionlist, configuresystemaccount, configureevaluator, configuresystemfilter, configuresystemproperty), authoringflow (creatingflowsteps, creatingnewflow, addingoperationsflow, appearanceflow, modifyflow, setinput [inputsource, evaluatingdata], settransitions, setresponses, setouptutresults [setoutputs, setresults, filters], setflowvariables, setreturnsteps), advancedauthoring (subflows, parallelsplitsteps, multiinstancesteps, usescriptletsflow, regularexpressions, customzingflowtransitions), debuggingflows (validateflows, testingdebuggingflows, debuggingcomplexflows, debuggingcentralstudio), managingflowsoperations (createoperation, findingflow, globalsearchreplace, copyflow, whatusesthis, generatingdocumentation, versionhistory, bookmarkflowoperation), studioproperties]; usepamobile
- Troubleshoot: gentroubleshoot [failedupgrade, insufficiententropypool, oomerror, pythonexpressionsnotworking, secondrpainstallerfails, installertempfolderlocationlinux, installertempfolderlocationwindows, pythonsyntaxerror, troubleshootinglocalization [gibberishcharactersinui, japanesecharactersissues], troubleshootupgrades [backupcorruption, iconerror, browserfavicon, postupgradeidmissue, posthotfixupgradefails, centralupgradefailidmcreate, upgradeafterrollbackissue, java8samlupgrade, jvmparamsupgradeissue, cconfigchange]]; troubleshootingcentral [uprdrpajava17, specialcharacters, sslhandshakeerror, pluginsnotdeleted, slowexecution, lowresolutionff, contentdeploymentslow, oolockout, remhostrc4, mapworkgroup, contentdeploy, inconsistentstart, helplinkissue, lowresolution, workerregistration, scrambledview, deployexception, serviceunavailable, deployerror, filecorrupted, nopermission, npeooexistingidm, scrambledviewsteps, win2016cpdeployissue, unexperror, errormsg, serverror, flowlaunch, resetpwaccessissue, oofails, unabletoremoverabbitmq, erlangnotcompatible, incorrectsamlsetup, miflowsstuck, workerrecovery, centralidmmodeissue, websocketlongpolling, rpacentralerror, clusterencryptionissues]; robottroubleshooting [norobots, incorrectsecondexecutionactivity, uftcrashfailsactivityrun, robotrdp, pendingrobot]; troubleshootingstudio [oostudiohighdpi, remotecertissue, multiprojectimporterror, editxmloperationfailure, debuggerflowsnotvisible, importcpoomerror, inconsistentcp, parentfoldererror, commitfoldererror, projectinconsistentstate, validationfailureduplicateuuid, scmerror, emptygitrepoissue, gitmergeoperationissue, gitoperationerror, svnprojectupdateissues, missingdlls, scmoperationissue, scmdetachissue, studiowithnobrandlogo, scmlockeditem, scmupdaterefreshissue, studioimportjava17issue]; workflowdesignertroubleshooting [dotnetissuedesignerlinux, designererrorolaccess, runbuttondisabled, passwordissue, doubleinstancerunning, designerprojecttreemissing, bponloopnotworking, idmldapuserissue, modifyidmproperror, lowresolutionffdesigner, dragselectparallelsteps, promptuserinputsissue, longdescriptionssaveissue, plugindownloadfailure, gitrepazureissue]; troubleshootingoorecorder [diffusercantrec, recordernotworking, recorderunexpectedfailure, recordernotlocalized, uftconfigfailure]; troubleshootingssx [activityunknownstate, activityrefresh, ssxnotaccessible, pwdchange]; rastroubleshooting [nologsgenerated, rasupgradeerror, rasinstallertlserror]; troubleshootstudiowizards [soaprequestfailure, pshellwizardstartissue, middlewaresapcpissue]
- Develop: develop; apiintro [basicauthentication, dashboard, csrfprotectionoo, restapis (getexecutionsummary, getexecutionstepcount, getexecutionstepspagination, exportexecutionsummariescsv, getsingleexecutionstep, getexecutionstepscsv, getexecutionstepstext, getrerunnablesteps, rerunfromstep, deletererundata, executionpauses, getexecutionlog, changeexecutionstatus, executeflowuuid, flowexecutionstatus, flowinput, purgedebuggerexecution, purgeexecutionstepdata, deletesteplogdata), flowlibrary, scheduler, deploymentcp (deploycontentpacks, uploaddeploymentprocess, runspecificdeployment, getdeploymentprocess, deletedeploymentcp, addingcontentpackfiles), queueconfigrabbitmq, contentpacks, configurationitemscontent, auditevents, ldapconfiguration, workers, firewallfriendlyapis, users, lwssoconfiguration, userauthentication, roles, systeminformationsettings (getsystemloglevel, getooversion), systemnotifications, robotapis, gettargets]; selfservicexapis; developcontent [aflcontentdevelopment (bestpracticescontent, developpluginsjava, flowauthoring, operations, scriptlets, deprecation, creatingoperationsactionannotation), cloudslangcontentdevelopment (bestpracticescs, developcsplugins, builscp [buildcpmaven], flowauthoringcs, cloudslangcontentflows), contentpackversioning, bestpracticesmavenprojects, listflowsoperations, internalexecutionorder]
- Ek: usepamobile, commandlineinterface (oosh, oosha) ust duzeyde Use altindadir.

## 6. Bu turda kalan okunmamis bolumler (oncelik sirasina gore)

- Studio/Designer: designerauthoroperations, authorsystemproperties, designercreatedeploycp (kismi), createstepsflow, newflow, expressioneditor, extractandmodifyoutputvalues, startstep, viewcloudslangcode, yamlfiletextual, cloudslangprompts, setoutputs, setresults, filters, setflowvariables, setinput/evaluatingdata, managingflowsoperations (copyflow, globalsearchreplace, generatingdocumentation, bookmarkflowoperation), creatingoperation, workingcis, configuresystemaccount, configuregroupaliases, configurerolealiases, configuresystemfilter, configureselectionlist, configuresystemproperty, configurescriptlet, authoraflprojectswfd (aflmiedit, viewaflflowswfd, editaflflowswfd), useexternalcloudslangfiles, designerkeyboardshortcuts, designerdependenciespane, workingsourcecontrol (workinggit, workingsvn), workingcontentpacks (importingcontentpacks, managingcontentpacks).
- REST API kategorileri: scheduler, flowlibrary, deploymentcp (deploycontentpacks, uploaddeploymentprocess, runspecificdeployment, getdeploymentprocess, deletedeploymentcp), contentpacks, configurationitemscontent, auditevents, ldapconfiguration, lwssoconfiguration, userauthentication, users, roles, workers, firewallfriendlyapis, systeminformationsettings (getooversion, getsystemloglevel), systemnotifications, robotapis, gettargets, queueconfigrabbitmq, selfservicexapis, flow execution ek uclari (changeexecutionstatus, flowexecutionstatus, flowinput, purgedebuggerexecution, purgeexecutionstepdata, deletesteplogdata, executionpauses).
- Administer: securehardenintro ve alt konulari (hardeningoo, configtls, minimizerisk, enableredirect, csrfoo), administeridm ve alt konulari (adduserscenario, manageusers, managegroups, manageroles, manageauthentication, ldap/saml/oauth), setupsystemconfigurationoo (securitysettings, setuproles, setupusers, setupsaml, lwsso), databasehealth, datacleanup, backupoo, disasterrecovery, systemtuningoo, postgresqlha (patroni), setupworkers, setuptopologyrobot, oodesigneradmintasks alt konulari.
- Integrate: 21 entegrasyon sayfasinda okunmamis olanlar (Hyper-V, SCVMM, KVM, Nutanix, Network Automation, NNM, NOM, Infoblox, F5, Efficient IP, Foreman, OpenNetAdmin, Zabbix, SAP LaMa, SAP S/4, OCI, Oracle Cloud DB, ABBYY, AIOps, vCenter). vSphere sayfasi bos dondu. Base content, sunucu otomasyonu, SSH, PowerShell/WinRM, e-posta, dosya/FTP, veritabani ve HTTP/REST ayrintilari hic okunmadi.
- Troubleshoot ve Release notes: govdeleri okunmadi; yalniz basliklar bolum 4'te.
- Use > Wizards ve Self-Service X alt konulari (shell/PowerShell sihirbazi, kategoriler, guvenlik) okunmadi; akış komut aracı/akış yönetim aracı komut listesi okunmadi.
