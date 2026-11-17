# Forum vakaları: sunucu otomasyonu (sunucu otomasyonu) ve akış otomasyonu (akış otomasyonu)

## Okuma özeti

- Yüklenen sayfa: yaklaşık 61. sunucu otomasyonu liste sayfaları 5, akış otomasyonu liste sayfaları 3, konu sayfaları 52. Ayrıca bir WebFetch denemesi (boş döndü) ve bir engellenen konu isteği (aşağıya bakın).
- Okunan konu: 52. sunucu otomasyonu 26, akış otomasyonu 25, DCA 1 (DCA konusu sunucu/akış yolu altında değil, `automation-ctr/f/discussions` altında). Her konunun metni tarayıcıda açılıp okundu.
- Yöntem: WebFetch liste sayfasında boş döndü. Bunun üzerine tarayıcı (navigate + get_page_text) kullanıldı. Sayfalama `?pifragment-NNNNN=N` biçiminde; sunucu otomasyonu için 14975, akış otomasyonu için 15044. sunucu otomasyonu liste sayfaları 2-5 tarayıcı kökeninden alındı. Bir konu sayfasına yönelik aynı türde istek güvenlik sınıflandırıcısı tarafından reddedildi. Bu yüzden konu okumaları gezinme ile yapıldı; reddedilen isteği aşmaya çalışmadım.
- Takıldığım yerler: (1) WebFetch boş döndü. (2) get_page_text yanıtları 2200-3000 karakterde kesildi; birkaç konuda yanıtın alt kısmı görülmedi ve bu vakalarda "yanıt görünmedi" yazıyor. (3) Mutlak tarih yalnız sunucu otomasyonu liste sayfa 1'de (ilk 10 konu) var; diğer konularda forumun "over 2 years ago" gibi göreli ifadeleri kullanıldı.
- Forum yazarlarının kullanıcı adlarını ve kişisel bilgileri yazmadım. Çözüm alanları forum cevabından özetlenmiştir; "doğrulanmış" ifadesi forumdaki Verified Answer işaretine karşılık gelir, "önerilen" ise yalnız önerilen cevap olduğu anlamına gelir.
- Kapsam notu: `530887` (SiteScope config_tool) akış otomasyonu forumunda ama ürün SiteScope olduğu için vaka listesine alınmadı.

Ürün kodları: sunucu otomasyonu = sunucu otomasyonu, akış otomasyonu = akış otomasyonu, DCA = Data Center Automation.

Seviye: temel = düz tek iş; orta = çok adımlı, koşullu veya kısmi başarısızlık; ileri = bozuk ortamda teşhis ve akış değişikliği.

---

## Bench vakaları: sunucu otomasyonu

### F-SV-001 Agent'ı API ile kaldırma ve sunucu otomasyonu kaydını silme

- kimlik: F-SV-001
- seviye: orta
- urun: sunucu otomasyonu
- kaynak: https://community.opentext.com/it-ops-cloud/automation-ctr/f/server-automation-discussions/534683/api-to-uninstall-delete-sa-agent
- tarih: 2026-09-18 (liste sayfası)
- talep: Yönetilen bir Linux sunucudan sunucu otomasyonu agent'ını API ile hem kaldırmak hem de sunucu otomasyonu kaydını silmek istiyorum. Böyle bir API var mı?
- ortam_onkosulu: sunucu otomasyonu core ve bir yönetilen Linux sunucu. Agent kurulu. Yönetici API erişimi var.
- beklenen_sonuc: Agent yazılımı host'tan kalkar ve sunucu otomasyonu'da cihaz decommission edilir.
- denetlenebilir_olcut: Hedef host'ta agent kurulum dizini yok; sunucu otomasyonu'da cihaz durumu decommissioned; kaldırma günlüğü (agent_uninstall_*.log) hedefte oluşmuş.
- tuzak: Unregister/decommission API'si yalnız sunucu otomasyonu veritabanı kaydını kaldırır, host'taki yazılımı kaldırmaz. Betik doğrudan çalıştırılırsa agent kendi bağlantısını keser ve iş başarısız olur.
- gercek_cozum: Doğrulanmamış öneri: Host kaldırma için Run Server Script ile `at` üzerinden `/opt/opsware/agent/bin/agent_uninstall.sh` gecikmeli zamanlanır. Windows için schtasks benzeri yöntem önerildi. Forumda API ile tam kaldırma yoktur denildi.
- lab_uyarlamasi: Konteynerde sahte `/opt/opsware/agent/bin/agent_uninstall.sh` betiği ve `at` zamanlaması. Kayıt silme için lab'da kendi basit kayıt tablosu. Gerçek sunucu otomasyonu API'si yok, bu yüzden kayıt API'si yalnız simüle edilir.

### F-SV-002 Servis hesabı kilitlenmesinde yanlış parola denemesinin kaynak IP'sini bulma

- kimlik: F-SV-002
- seviye: temel
- urun: sunucu otomasyonu
- kaynak: https://community.opentext.com/it-ops-cloud/automation-ctr/f/server-automation-discussions/534453/find-the-source-ip-of-incorrect-login
- tarih: 2026-07-08 (liste sayfası)
- talep: Entegrasyon için kullanılan servis hesabı kilitleniyor. Yanlış parola denemelerinin hangi IP'den geldiğini bulamıyorum. Bir log ya da seçenek var mı?
- ortam_onkosulu: sunucu otomasyonu core. Entegrasyon kullanıcısı için giriş denetimi kapatılmış olabilir (twist yapılandırmasında ignore listesinde).
- beklenen_sonuc: Yanlış denemelerin kaynak IP'si ve zamanı bulunur.
- denetlenebilir_olcut: Kullanıcı giriş raporunda ilgili hesap için başarısız denemeler listelenir ve en az bir kaynak IP çıkarılır.
- tuzak: Entegrasyon kullanıcısı giriş denetiminden hariç tutulmuşsa rapor boş görünür. Rapor boşsa yapılandırma kontrol edilmeli.
- gercek_cozum: Önerilen: NGUI'de Reports > User > User Login raporu. Giriş denetimi kapalıysa çekirdekte twist yapılandırma dosyasındaki ignore listesinden kullanıcı geçici olarak çıkarılır, kaynak bulunduktan sonra geri konur.
- lab_uyarlamasi: Konteynerde sshd kimlik doğrulama günlüğü (auth.log) ve sahte yanlış parola denemeleri. Yapılandırma dosyasında giriş denetimini kapatan bir satır tuzağı. Gerçek NGUI yok, rapor yerine günlük satırlarından IP çıkarılır.

### F-SV-003 Marketplace Connector içe aktarma: kimlik doğrulama hatası

- kimlik: F-SV-003
- seviye: orta
- urun: sunucu otomasyonu
- kaynak: https://community.opentext.com/it-ops-cloud/automation-ctr/f/server-automation-discussions/533554/marketplace-connector-import-failed-with-error-error-unable-to-authenticate-spike-username-admin
- tarih: 2025-12-15 (liste sayfası)
- talep: Marketplace Connector içerik içe aktarması "Unable to authenticate spike.username admin" hatasıyla başarısız oluyor. Hangi ayarı kontrol etmeliyim?
- ortam_onkosulu: sunucu otomasyonu 2022.11 (RHEL 8.10), Marketplace Connector 1.1.008. Komut motoru (spike/way) kimlik bilgileri yapılandırmada yanlış ya da eski.
- beklenen_sonuc: `marketplace-connector.sh import` başarıyla tamamlanır ve içerik yüklenir.
- denetlenebilir_olcut: Komut 0 ile döner; marketplace-connector.log içinde authenticationFailed satırı yok; yapılandırmadaki kullanıcı adı komut motoru kullanıcısıyla eşleşir.
- tuzak: `cbt -s` çıktısında parola maskelenir; sorun parolada mı kullanıcı adında mı, çıktıdan anlaşılmaz. Ayrıca kullanıcı adı yapılandırmada `admin` olarak geçer, yetkili kullanıcı başka olabilir.
- gercek_cozum: Cevapsız. Forumda yanıt görünmedi.
- lab_uyarlamasi: Sahte bir kimlik doğrulama uç noktası yok. Konteynerde yapılandırma dosyasındaki kullanıcı adı ile sahte bir doğrulama betiği eşleştirilir; import betiği bu eşleşmeyi kontrol eder ve hata üretir.

### F-SV-004 Windows 2016 sunucuda yama uyumluluk taraması izin hatası

- kimlik: F-SV-004
- seviye: orta
- urun: sunucu otomasyonu
- kaynak: https://community.opentext.com/it-ops-cloud/automation-ctr/f/server-automation-discussions/533548/scan-policy-compliance-failed-for-windows-2016-server-with-permission-problem
- tarih: 2025-12-13 (liste sayfası)
- talep: Windows 2016 sunucusunda admin/superuser olarak GUI'den Scan > Patch Compliance çalıştırıyorum ve sürekli izin hatası alıyorum. Neden?
- ortam_onkosulu: sunucu otomasyonu 2022.11 (RHEL 8.10), Windows 2016 Server x64 agent sürümü 85.x. Hedef sunucuda tarama için gereken yetki eksik olabilir.
- beklenen_sonuc: Patch compliance taraması hatasız tamamlanır.
- denetlenebilir_olcut: Tarama işi başarılı durumda; sunucuda izin ile ilgili hata yok; tarama sonucu raporda görünür.
- tuzak: sunucu otomasyonu superuser olmak, hedef sunucuda agent'ın çalıştığı hesabın yetkisini garanti etmez. Yetki tuzağı hedef tarafta.
- gercek_cozum: Cevapsız. Forumda yanıt görünmedi.
- lab_uyarlamasi: Yalnız gerçek üründe. Windows agent ve offline patch kataloğu gerektirir; Linux konteyner filosunda yaşatılamaz.

### F-SV-005 Satellite işletim sistemi yükseltmesinden sonra smartboot fuse hatası

- kimlik: F-SV-005
- seviye: ileri
- urun: sunucu otomasyonu
- kaynak: https://community.opentext.com/it-ops-cloud/automation-ctr/f/server-automation-discussions/532924/sa-satellite-smartboot-fuse-error-post-upgrading-os-rhel-7-to-8
- tarih: 2025-08-26 (liste sayfası)
- talep: sunucu otomasyonu 2020.11 satellite sunucusunu RHEL 7.9'dan RHEL 8.8'e yükselttim; satellite servisleri gelmiyor, fuse modülü bağlanmıyor. Yerinde düzeltmek mümkün mü, yoksa yeni satellite mi kurmalıyım?
- ortam_onkosulu: RHEL 7.9 üzerinde sunucu otomasyonu satellite, işletim sistemi RHEL 8.8'e yükseltilmiş. Çekirdek 4.18 ama fuse eski 3.10 için derlenmiş.
- beklenen_sonuc: Satellite hizmeti yeniden çalışır ya da yönetilen sunucular kesintisiz başka bir satellite'a geçer.
- denetlenebilir_olcut: Yönetilen sunucuların satellite IP'si yeni satellite'a güncellenmiş; eski satellite decommission edilmiş; smartboot hatası kalmamış.
- tuzak: Yerinde yükseltme, satellite bileşenlerinin işletim sistemi sürümüne özgü olması nedeniyle çalışmaz; fuse modülü yeniden derlenemez.
- gercek_cozum: Doğrulanmış: Satellite bileşenleri yalnız üzerine kuruldukları işletim sistemiyle uyumludur. Yeni RHEL 8 satellite mevcut realm'e eklenir, yönetilen cihazların IP güncellenmesi beklenir (en fazla 24 saat), sonra eski RHEL 7 satellite decommission edilir.
- lab_uyarlamasi: Kısmi. Gerçek satellite ve fuse yok. Lab'da iki proxy konteyneri ("eski" ve "yeni") tanımlanır ve yönetilen konteynerlerin bağlantı hedefi değiştirilir. Fuse hatası simüle edilmez.

### F-SV-006 Global Shell'de mail komutu geçici dosya hatası

- kimlik: F-SV-006
- seviye: orta
- urun: sunucu otomasyonu
- kaynak: https://community.opentext.com/it-ops-cloud/automation-ctr/f/server-automation-discussions/532733/mail-command-from-global-shell
- tarih: 2025-07-28 (liste sayfası)
- talep: Global Shell'de `echo ... | /bin/mail` ile bir rapor göndermeye çalışıyorum; "temporary mail file: No such file or directory" hatası alıyorum. Raporu bu yolla göndermek mümkün mü?
- ortam_onkosulu: Linux yönetilen sunucu, Global Shell üzerinden çalışan betik. Varsayılan geçici dizin /tmp.
- beklenen_sonuc: Mail komutu 0 ile döner ve alıcıya ulaşır.
- denetlenebilir_olcut: Komut çıkış kodu 0; posta sunucusunda mesaj alınmış; geçici dosya hatası yok.
- tuzak: Aynı konu ayrı başlıklarda iki kez açılmış (532731 de aynı soruyu sorar). Asıl hata Global Shell ortamındaki /tmp'nin güvenilir olmamasıdır.
- gercek_cozum: Doğrulanmış: mail komutunun geçici dizinini belirten TMPDIR ortam değişkeni /tmp dışında bir dizine ayarlanır.
- lab_uyarlamasi: Konteynerde /tmp'yi salt okunur bağlamak ve sahte posta sunucusu (alıcı kutusu) kurmak. TMPDIR olmadan başarısız, ayarlıyken başarılı olur.

### F-SV-007 Windows Server 2025 için bazı yamalar listelenmiyor

- kimlik: F-SV-007
- seviye: orta
- urun: sunucu otomasyonu
- kaynak: https://community.opentext.com/it-ops-cloud/automation-ctr/f/server-automation-discussions/532087/platform-installer-for-windows-server-2025---not-all-patches-displayed
- tarih: göreli "over 2 years ago" (mutlak tarih okunamadı)
- talep: sunucu otomasyonu 24.1.007 ortamında Server 2025 eklendi ama 2025-04 kümülatif güncellemesi (KB5055523) Server 2025 yama listesinde görünmüyor. Yalnız 24H2 altında geçiyor.
- ortam_onkosulu: sunucu otomasyonu 24.1.007, Windows Server 2025 hedefler. Patch ürünleri ayarında hem Server 2025 hem 24H2 seçili.
- beklenen_sonuc: Server 2025 yama listesinde KB5055523 görünür.
- denetlenebilir_olcut: Patch kataloğunda ilgili KB, Server 2025 ürününe bağlı olarak listelenir.
- tuzak: wsusscn2.cab dosyasında yama olsa bile sunucu otomasyonu kataloğunda ürün eşlemesi eksik olabilir. Offline tarama çalışmış olması eşleme hatasını dışlamaz.
- gercek_cozum: Cevapsız. Konu kilitli ve destek kaydı açık olarak kaldı.
- lab_uyarlamasi: Yalnız gerçek üründe. Patch kataloğu ve wsusscn2.cab gerektirir.

### F-SV-008 Bir script içinden başka sunucuda script tetikleme

- kimlik: F-SV-008
- seviye: orta
- urun: sunucu otomasyonu
- kaynak: https://community.opentext.com/it-ops-cloud/automation-ctr/f/server-automation-discussions/531267/triggering-a-script-on-other-server-while-connected-to-a-server-within-a-single-instance-script-execution
- tarih: göreli "over 2 years ago" (mutlak tarih okunamadı)
- talep: Windows Server A üzerinde çalışan bir script, Server B'de paket indirme betiğini tetiklemeli. İki sunucu da Windows kümesinde. pytwist kütüphanesi bunu sağlıyor mu?
- ortam_onkosulu: sunucu otomasyonu 24.1 core, iki Windows Server 2019 (küme) yönetilen cihaz. Tek bir script yürütmesi içinde A'ya bağlanıp B'de iş çalıştırma ihtiyacı.
- beklenen_sonuc: B sunucusunda paket indirilir ve sonuç A tarafında alınır.
- denetlenebilir_olcut: B'de paket dosyası oluşur; işin çıktısı çağıran tarafa döner; iş tek bir sunucu otomasyonu yürütmesi içinde tamamlanır.
- tuzak: Script yürütmesi tek hedef cihaza bağlıdır. Hedef cihazdan başka cihaza doğrudan iş dağıtımı sunucu otomasyonu modelinin parçası değildir.
- gercek_cozum: Cevapsız. Forumda yanıt görünmedi.
- lab_uyarlamasi: İki Linux konteyneri A ve B. A'dan B'ye SSH ile betik çağrısı ve dosya oluşturma. sunucu otomasyonu tarafındaki tek hedef kısıtı lab'da yaşatılamaz; yalnız gerçek üründe kesin sonuç verilir.

### F-SV-009 Yeniden başlatma sonrası startsync hatası: spin ve gateway erişilemiyor

- kimlik: F-SV-009
- seviye: ileri
- urun: sunucu otomasyonu
- kaynak: https://community.opentext.com/it-ops-cloud/automation-ctr/f/server-automation-discussions/530838/sa-communication-error---spin-and-or-gateway-are-unavailable
- tarih: göreli "over 2 years ago" (mutlak tarih okunamadı)
- talep: Yama sonrası yeniden başlatmadan sonra sunucu otomasyonu servisleri başlamıyor: "Spin and/or Gateway are unavailable", bağımlılık kontrolü `mm_wordbot` için başarısız. Log'da SSL "peer did not return a certificate" var.
- ortam_onkosulu: Tek mesh, sunucu otomasyonu 24.1.003, RHEL 8.x. DB ve uygulama sunucusu aynı saat ve saat dilimi.
- beklenen_sonuc: `startsync` başarılı; tüm sunucu otomasyonu bileşenleri çalışır.
- denetlenebilir_olcut: Servis durumu tamamı çalışıyor; `mm_wordbot` bağımlılığı geçer; SSL hatası logda yok.
- tuzak: Hata bağımlılık zincirinin sonunda görünür ve kök neden başka bileşendedir. SSL hatası belirti olabilir, nedeni olmayabilir.
- gercek_cozum: Forum yanıtı: destek kaydı açılması ve log toplanması önerildi. Kök neden ve kalıcı çözüm yazılmadı.
- lab_uyarlamasi: Kısmi. sunucu otomasyonu yok. Lab'da systemd birimleri ile bağımlılık zinciri ve eksik sertifikayla başlamayan bir servis simüle edilebilir. Gerçek startsync ve mm_wordbot yaşatılamaz.

### F-SV-010 Windows yaması "will not install" hatası; bağlantı testi başarılı

- kimlik: F-SV-010
- seviye: orta
- urun: sunucu otomasyonu
- kaynak: https://community.opentext.com/it-ops-cloud/automation-ctr/f/server-automation-discussions/530609/during-patch-remediation-will-not-install-error-coming
- tarih: göreli "over 2 years ago" (mutlak tarih okunamadı)
- talep: Windows yama uygulamasında "this patch is not applicable because it is not recommended by windows update, so it will not be installed" hatası geliyor. İletişim testleri başarılı, sunucu uyumluluğu ve yazılım uyumluluğu da başarılı görünüyor ama sunucu hiçbir yazılım politikasıyla ilişkili değil.
- ortam_onkosulu: sunucu otomasyonu 2022/24 sürümü, Windows Server hedefleri, Windows Update önerilen listesiyle sunucu otomasyonu katalog farkı.
- beklenen_sonuc: Uygulanabilir yamalar kurulur veya uygulanamayanlar gerekçesiyle raporlanır.
- denetlenebilir_olcut: Yama işi tamamlanır; uygulanmayan yamalar için gerekçe raporda görünür; iletişim testi başarılı.
- tuzak: Yama "önerilen" değilse atlanıyor olabilir. Genel başarı durumları (overall, compliance) hatayı gizler.
- gercek_cozum: Cevapsız. Forumda yanıt görünmedi.
- lab_uyarlamasi: Yalnız gerçek üründe. Windows agent ve yama kataloğu gerekir.

### F-SV-011 Eski sunucu otomasyonu kurulumundan CBT ile taşınan yamalarda metadata eksik

- kimlik: F-SV-011
- seviye: orta
- urun: sunucu otomasyonu
- kaynak: https://community.opentext.com/it-ops-cloud/automation-ctr/f/server-automation-discussions/529945/cbt-patch-import-fail-with-metadata-missing-error
- tarih: göreli "over 2 years ago" (mutlak tarih okunamadı)
- talep: 2018.08 sunucu otomasyonu kurulumundan CBT ile dışa aktardığım 2023 yamalarını yeni sunucu otomasyonu 24.1'e almak istiyorum. Metadata yok hatası veriyor ve tüm cab dosyasını almak istemiyorum.
- ortam_onkosulu: Eski sunucu otomasyonu 2018.08 ile yeni sunucu otomasyonu 24.1 core. Dışa aktarılan Windows yamaları (ör. Q5012170, Q5030183 aileleri) hedefte Windows Patch Database içinde mevcut veya silinmiş olabilir.
- beklenen_sonuc: Eski yamalar yeni sunucu otomasyonu'ya tamamen olmasa da seçilen kapsamda aktarılır.
- denetlenebilir_olcut: İçe aktarma raporunda "metadata not found" satırı yok ya da bilinen istisna listesine indirgenmiş; seçili yamalar yeni sunucu otomasyonu'da listelenir.
- tuzak: Hedefte Windows Patch Database zaten varsa ve yama oradan kaldırılmış ya da elle silinmişse, cab içe aktarma metadata eksik olarak görünür. Sorun yama dosyasında değil, hedef veritabanındadır.
- gercek_cozum: Cevapsız. Forumda yanıt görünmedi.
- lab_uyarlamasi: Yalnız gerçek üründe. Windows patch metadata ve CBT dışa aktarma biçimi gerekir.

### F-SV-012 Yama dağıtımında "Overall server status: Time out"

- kimlik: F-SV-012
- seviye: orta
- urun: sunucu otomasyonu
- kaynak: https://community.opentext.com/it-ops-cloud/automation-ctr/f/server-automation-discussions/529508/overall-server-status-is-time-out-while-patch-deployment
- tarih: göreli "over 2 years ago" (mutlak tarih okunamadı)
- talep: Yama dağıtımından sonra sunucunun genel durumu "Time out" görünüyor. Diğer işler çalışıyor mu sorusu da var.
- ortam_onkosulu: sunucu otomasyonu 2022/24 core, etkilenen yönetilen sunucuda agent yanıt vermiyor ya da geç yanıt veriyor.
- beklenen_sonuc: Genel durum başarılı; yama işi tamamlanır.
- denetlenebilir_olcut: İletişim testi başarılı; agent günlüğünde zaman aşımı yok; aynı sunucuda başka bir iş başarılı tamamlanır.
- tuzak: Yama işinin başarılı göstermesi ya da uyumluluk durumu, genel durum zaman aşımının nedenini göstermez.
- gercek_cozum: Doğrulanmış: Önce agent'a iletişim testi yapılır. Ardından etkilenen sunucudaki agent günlükleri (`/var/log/opsware/agent/`, Windows için ortak dosyalar altındaki log dizini) incelenir. Aynı sunucuda başka bir sunucu otomasyonu işi çalıştırılarak agent'ın işleri alıp almadığı kontrol edilir.
- lab_uyarlamasi: Konteynerde agent simülasyonu (basit HTTP ya da SSH ajanı) ve zaman aşımına neden olan bağlantı kesintisi. Gerçek agent günlüğü ve genel durum yok; günlük dosyası ve iletişim testi benzeri kontrol betikle yapılır.

### F-SV-013 RHEL 8.8'den sunucu otomasyonu 22.11 ile 24.1 yükseltmesi: ORA-01461 ve Wayscript hatası

- kimlik: F-SV-013
- seviye: ileri
- urun: sunucu otomasyonu
- kaynak: https://community.opentext.com/it-ops-cloud/automation-ctr/f/server-automation-discussions/525987/sa-24-1-upgrade-issue
- tarih: göreli "over 3 years ago" (mutlak tarih okunamadı)
- talep: sunucu otomasyonu 22.11'i tek core mesh üzerinde 24.1'e yükseltirken yarıda hata veriyor: ORA-01461 (LONG değer bağlanamıyor) ve Wayscript kurulumu başarısız. DB ekibi hangi tabloyu sorduğunu bilmiyor.
- ortam_onkosulu: Oracle veritabanı, karakter seti UTF-8. Yükseltme sırasında slice bileşeni hata veriyor. Arşiv /var/tmp/oitmp/wayscripts.archive altında kalmış.
- beklenen_sonuc: Yükseltme tamamlanır, Wayscript kurulumu başarılı olur.
- denetlenebilir_olcut: Wayscript kurulumu 0 ile döner; yükseltme betiği hata vermeden biter; veritabanı karakter seti yükseltme gereksinimine uygun.
- tuzak: Hata iletisinde tablo adı yoktur; hatanın kaynağı karakter seti uyumsuzluğudur. Betiği elle yeniden çalıştırmak aynı hatayı üretir.
- gercek_cozum: Doğrulanmış (forum yanıtı): Veritabanı karakter seti UTF-8'den AL32UTF8'e çevrildi. Bu, sunucu otomasyonu 24.1 uyumluluğu için gerekliydi ve hata çözüldü.
- lab_uyarlamasi: Yalnız gerçek üründe. Oracle veritabanı ve sunucu otomasyonu yükseltme betiği gerekir.

### F-SV-014 Windows ve RHEL 8/9 için ISO güvenlik uyumluluk içeriği bulunamıyor

- kimlik: F-SV-014
- seviye: temel
- urun: sunucu otomasyonu
- kaynak: https://community.opentext.com/it-ops-cloud/automation-ctr/f/server-automation-discussions/529169/iso-security-compliance-content-on-rhel-8-9-in-sa
- tarih: göreli "over 2 years ago" (mutlak tarih okunamadı)
- talep: RHEL 8 için sunucu otomasyonu'da ISO güvenlik uyumluluk kontrolü seçeneği yok. RHEL 8 ve 9 için nasıl yapılır?
- ortam_onkosulu: sunucu otomasyonu core, RHEL 8 ve 9 yönetilen sunucular. Uyumluluk içeriği sunucu otomasyonu paketinde eksik.
- beklenen_sonuc: RHEL 8/9 için ISO tabanlı uyumluluk taraması yapılabilir.
- denetlenebilir_olcut: Uyumluluk içeriği ürün pazarından ya da ilgili belgeden içe aktarılır ve RHEL 8/9 hedeflerinde tarama çalışır.
- tuzak: Eski sunucu otomasyonu sürümlerinde içerik yok. Doğru içeriği bulmak için ürün pazarındaki paket adı bilinmeli.
- gercek_cozum: Doğrulanmış: ITOM Marketplace üzerindeki "Security and Compliance for sunucu otomasyonu" içeriği RHEL 8 ve 9 için güvenlik içeriğini sağlar.
- lab_uyarlamasi: Konteynerde OpenSCAP ya da benzeri betik taraması ile simüle edilebilir. Gerçek sunucu otomasyonu ISO içeriği yaşatılamaz; yalnız betik düzeyinde karşılaştırılır.

### F-SV-015 sunucu otomasyonu API'si 24.1'de devre dışı: "Making API calls from Twister is disabled"

- kimlik: F-SV-015
- seviye: temel
- urun: sunucu otomasyonu
- kaynak: https://community.opentext.com/it-ops-cloud/automation-ctr/f/server-automation-discussions/529466/sa-api-enable-in-24-1-version
- tarih: göreli "over 2 years ago" (mutlak tarih okunamadı)
- talep: sunucu otomasyonu 24.1'de Twister üzerinden bazı sınıflara erişmeye çalışıyorum; "Making API calls from Twister is disabled" hatası alıyorum. İki çekirdekli mesh'te nasıl etkinleştirilir?
- ortam_onkosulu: sunucu otomasyonu 24.1, iki çekirdekli mesh. Çekirdek yapılandırma dosyasına erişim var.
- beklenen_sonuc: Twister API çağrıları başarılı döner.
- denetlenebilir_olcut: Yapılandırma dosyasında twisterEnabled=true; API çağrısı hata vermez; gerekli servis yeniden başlatıldığında etkin.
- tuzak: Yapılandırma değişikliği yalnız dosyaya yazılınca etkili olmayabilir; servis yeniden başlatma gerekebilir. Forumda yeniden başlatma adımı net yazılmadı.
- gercek_cozum: Doğrulanmamış ama yanıtta önerilen: /etc/opt/opsware/twist/twist_custom.conf dosyasına twisterEnabled=true eklenir. Kullanıcı değişikliğin yapıldığını, ama hâlâ erişemediğini bildirdi; yeniden başlatma sorusu yanıtsız kaldı.
- lab_uyarlamasi: Yapılandırma dosyasını ve ortak bir "API etkin mi" kontrol betiği konteynerde yaşatılabilir. Gerçek Twister API'si yok.

### F-SV-016 Install Software zaman aşımı (Windows)

- kimlik: F-SV-016
- seviye: orta
- urun: sunucu otomasyonu
- kaynak: https://community.opentext.com/it-ops-cloud/automation-ctr/f/server-automation-discussions/528787/sa---install-software-timeout-issue
- tarih: göreli "over 2 years ago" (mutlak tarih okunamadı)
- talep: Windows makinede Install Software yapınca zaman aşımı hatası geliyor. RAM ve disk yeterli, agent yeniden kurulmuş (80.x sürümü).
- ortam_onkosulu: sunucu otomasyonu Windows hedef, agent 80.x. Spin bileşeni ile agent arasında iletişim sorunu olabilir.
- beklenen_sonuc: Yazılım kurulumu tamamlanır.
- denetlenebilir_olcut: Kurulum işi başarılı; spin ile agent arasında iletişim testi geçer; zaman aşımı yok.
- tuzak: Kaynak yeterliliği ve agent yeniden kurulumu sorunu çözmez. Hata son olarak spin bileşeninde görülüyor.
- gercek_cozum: Forum yanıtı (kısmen görünen, önerilen): spin bileşeninin yönetilen sunucudaki agent ile iletişim kuramadığı varsayılıp iletişim testi ve ağ kontrolü önerildi. Kesin çözüm yazılmadı.
- lab_uyarlamasi: Kısmi. Lab'da SSH tabanlı yazılım kurulum betiği ve bir ağ kesintisi simüle edilebilir; Windows agent ve spin yok.

### F-SV-017 OGFS ana dizinlerini yeniden eşitleme aracı CLI'da hata veriyor

- kimlik: F-SV-017
- seviye: orta
- urun: sunucu otomasyonu
- kaynak: https://community.opentext.com/it-ops-cloud/automation-ctr/f/server-automation-discussions/528968/resync-orphaned-ogfs-home-directories-in-new-sa-mesh
- tarih: göreli "over 2 years ago" (mutlak tarih okunamadı)
- talep: sunucu otomasyonu geçişinde eski mesh'in OGFS ana dizinlerini yeni mesh'e aktardım. `utilities.resyncOGFSuserFiles` aracı CLI'da FileNotFoundError ve GUI'de "Permission denied" veriyor.
- ortam_onkosulu: Yeni sunucu otomasyonu mesh, OGFS depolama yolu. Aracı çalıştıran kullanıcı kök olmayan bir hesap.
- beklenen_sonuc: Orphan ana dizinler yeniden eşitlenir.
- denetlenebilir_olcut: Doğrulama modunda hata yok; ana dizin listesi OGFS yolu ile eşleşir; GUI ve CLI aynı sonucu verir.
- tuzak: CLI'da yetki yükseltme yapılmaz; GUI yükseltir. CLI'da çalıştıran kullanıcının kök ya da eşdeğer okuma/yazma yetkisi olmalı.
- gercek_cozum: Doğrulanmış: CLI yetki yükseltmez, bu yüzden çalıştıran kullanıcının kök ya da eşdeğer okuma-yazma yetkisi olmalı. GUI yetki yükseltir.
- lab_uyarlamasi: Konteynerde OGFS benzeri dizin yapısı ve farklı kullanıcılarla (kök değil / kök) çalıştırma. Gerçek APX aracı yok, yalnız yetki farkı yaşatılır.

### F-SV-018 Bir zamanlanmış işin her ayın son gününde çalışması

- kimlik: F-SV-018
- seviye: temel
- urun: sunucu otomasyonu
- kaynak: https://community.opentext.com/it-ops-cloud/automation-ctr/f/server-automation-discussions/528295/how-to-schedule-script-ejecution-each-last-day-of-month
- tarih: göreli "over 2 years ago" (mutlak tarih okunamadı)
- talep: Bir script her ayın son gününde çalışsın istiyorum. Aylar 28, 29, 30 ya da 31 gün olabiliyor. Bunu tek bir değişkenle nasıl yaparım?
- ortam_onkosulu: sunucu otomasyonu zamanlanmış iş. Script yürütme planlaması destekleniyor.
- beklenen_sonuc: Her ay son günde çalışır, şubat dahil.
- denetlenebilir_olcut: Son 12 ayın her birinde iş ayın son günü çalışmış; ayın 31'i olmayan aylarda da çalışmış.
- tuzak: Ayın 31'i olmayan aylarda ayarlanan gün atlanabilir ya da ertelenebilir. Ayrıca yaygın çözüm "ay sonu" ayarı yoktur.
- gercek_cozum: Doğrulanmış: Gün 31 olarak ayarlanır; sunucu otomasyonu zamanlama mantığı ay gün sayısına göre günü otomatik düzeltir. Forum yanıtı kodu incelediğini belirtti; kendisi denemedi.
- lab_uyarlamasi: Konteynerde `cron` ya da zamanlanmış görev ile karşılaştırma ve 12 ay simülasyonu. Gerçek sunucu otomasyonu zamanlaması yok; sunucu otomasyonu davranışı yalnız gerçek üründe doğrulanır.

### F-SV-019 Sahte vCenter eklenince "Mismatched Server Realms" tanılama hatası

- kimlik: F-SV-019
- seviye: orta
- urun: sunucu otomasyonu
- kaynak: https://community.opentext.com/it-ops-cloud/automation-ctr/f/server-automation-discussions/528160/mismatched-server-realms-after-adding-vcenter-servers-with-fakevcenter
- tarih: göreli "over 2 years ago" (mutlak tarih okunamadı)
- talep: `fakevCenter` aracıyla vCenter sunucuları ekledikten sonra tanılama "Mismatched Server Realms" hatası veriyor ve CLI tanılama yarıda kesiliyor.
- ortam_onkosulu: sunucu otomasyonu üç realm'li (çekirdek, çekirdek-agents, çekirdek-mm). vCenter sunucuları yanlış realm'e atanmış.
- beklenen_sonuc: Tüm tanılama probları geçer; vCenter sunucuları doğru realm'de.
- denetlenebilir_olcut: Tanılama özetinde "7 of 7 probes passed" benzeri tam geçiş; vCenter kayıtları doğru realm kimliğiyle.
- tuzak: Araç `--realmid` vermeden varsayılan realm'e atar; eski kayıtlar silinmeden eklenirse hata sürer.
- gercek_cozum: Doğrulanmış: vCenter kayıtları devre dışı bırakılıp silinir, bekleme ve çöp toplama yapılır, sonra doğru `--realmid` ile yeniden eklenir.
- lab_uyarlamasi: Konteynerde realm kayıt tablosu ve benzer bir araç. Gerçek fakevCenter ve realm yapısı yok; mantık (varsayılan realm tuzağı) simüle edilir.

### F-SV-020 RHEL depo eşitlemesi (RHEL repo sync) hatası

- kimlik: F-SV-020
- seviye: orta
- urun: sunucu otomasyonu
- kaynak: https://community.opentext.com/it-ops-cloud/automation-ctr/f/server-automation-discussions/526076/rhel-patching-issue
- tarih: göreli "over 3 years ago" (mutlak tarih okunamadı)
- talep: RHEL depo eşitlemesi sırasında hata alıyorum. Ne yapmalıyım?
- ortam_onkosulu: sunucu otomasyonu core, RHEL yama içe aktarma aracı. Bazı sunucu otomasyonu bileşenleri çalışmıyor olabilir.
- beklenen_sonuc: Depo eşitlemesi hatasız tamamlanır.
- denetlenebilir_olcut: `service opsware-sas status` tüm bileşenleri çalışır gösterir; içe aktarma aracı yeniden çalıştığında hata ve uyarı satırı yok.
- tuzak: Hata iletisi genel; asıl neden sunucu otomasyonu bileşen durumu ya da günlüklerde gizli.
- gercek_cozum: Önerilen (öneri olarak işaretli): Tüm sunucu otomasyonu bileşenlerinin çalıştığı kontrol edilir; RHEL içe aktarma aracı yeniden çalıştırılır; `/var/log/opsware/twist/server.log` ve `/var/log/opsware/mm_wordbot/` günlükleri hata anında incelenir.
- lab_uyarlamasi: Konteynerde iki sahte servis (durum komutu) ve bir depo eşitleme betiği. Gerçek RHEL içe aktarma ve sunucu otomasyonu bileşenleri yok.

### F-SV-021 RHEL 8.9 üzerinde sunucu otomasyonu core kurulumu: "FAILURE run level not 3"

- kimlik: F-SV-021
- seviye: ileri
- urun: sunucu otomasyonu
- kaynak: https://community.opentext.com/it-ops-cloud/automation-ctr/f/server-automation-discussions/525430/simple-sa-installation-getting-failure-run-level-not-3
- tarih: göreli "over 3 years ago" (mutlak tarih okunamadı)
- talep: RHEL 8.9 makineye sunucu otomasyonu core kurmaya çalışıyorum; önkoşul kontrolünde "run level not 3" hatası var. systemctl get-default multi-user.target çıkıyor. Kurulum günlüğünde openssl bulunamadı hatası da var.
- ortam_onkosulu: RHEL 8.9, önceki başarısız kurulum denemesinden kalan dosyalar ve paketler. /opt/opsware altında kalıntı olabilir.
- beklenen_sonuc: Temiz kurulum tamamlanır; run level kontrolü geçer.
- denetlenebilir_olcut: Önkoşul kontrolü tamamen geçer; kurulum günlüğünde openssl hatası yok; `opsware-sas` servisi tanımlı.
- tuzak: Hata iletisi run level diyor ama asıl neden önceki kurulumdan kalan kalıntılar. Yalnız run level değiştirmek sorunu çözmez.
- gercek_cozum: Doğrulanmış: Önceki başarısız kurulumda kurulan Opsware RPM'leri ve /opt/opsware dizini temizlenir, sonra kurulum yeniden başlatılır. Forum yanıtı ayrıca `chkconfig opsware-sas on` denemesinin hata verdiğini kaydetti.
- lab_uyarlamasi: Konteynerde kurulum betiği simülasyonu; önceki denemeden kalan dizin ve eksik openssl yolu. Gerçek sunucu otomasyonu kurulum paketleri yok.

### F-SV-022 Agent sertifika uyuşmazlığı: recert eki "Error from remote (3063)" ile başarısız

- kimlik: F-SV-022
- seviye: orta
- urun: sunucu otomasyonu
- kaynak: https://community.opentext.com/it-ops-cloud/automation-ctr/f/server-automation-discussions/528434/error-agent-certificate-mismatch
- tarih: göreli "over 2 years ago" (mutlak tarih okunamadı)
- talep: Bir Windows agent'ta sertifika uyuşmazlığı var. Agent yeniden sertifikalandırma eki çalıştırılınca "Error from remote (3063)" ile başarısız oluyor; ProgramFiles değeri alınamıyor.
- ortam_onkosulu: sunucu otomasyonu core, tek Windows yönetilen sunucu. Yönetici hesabıyla uzaktan betik çalıştırma ağ ya da hizmet bağlantısı aracılığıyla.
- beklenen_sonuc: Agent'ın sertifikası yenilenir ve sunucu yeniden iletişim kurar.
- denetlenebilir_olcut: Yeniden sertifikalandırma işi başarılı; agent ile çekirdek arasında iletişim geçer; uzak komut hata 3063 vermez.
- tuzak: Hata uzak komut ön kontrolünde ortaya çıkar; bu, sertifika hatası değil iletişim sorunudur. Aynı ağ sorunu başka işlerde de çıkabilir.
- gercek_cozum: Önerilen (ilgili yanıt): Tek sunucuda sorun varsa ağ/iletişim kesintisi kabul edilip agent yeniden kurulur.
- lab_uyarlamasi: Kısmi. Lab'da SSH ile uzak komut ve bir sertifika uyuşmazlığı simüle edilebilir. Windows agent ve ttlg yapısı yok.

---

## Bench vakaları: akış otomasyonu

### F-AK-001 Content pack deploy istisnası: akış otomasyonu 2020.08'den 2022.11'e yükseltme sonrası

- kimlik: F-AK-001
- seviye: orta
- urun: akış otomasyonu
- kaynak: https://community.opentext.com/it-ops-cloud/oo/f/discussions/534694/exception-error-when-deploying-a-content-pack-after-upgrade-to-oo-2022-11
- tarih: göreli "2 months ago"; sunucu günlüğündeki zaman damgası 2026-09-23
- talep: akış otomasyonu 2020.08'den 2022.11'e yükselttim (Windows Server 2019). Yükseltmeden sonra content pack yüklemeye çalışınca deployment hatası alıyorum: "null must not be null".
- ortam_onkosulu: akış otomasyonu 2022.11 central, Windows Server 2019. Eski sürüm 1.22 base content pack denenmektedir.
- beklenen_sonuc: Content pack sorunsuz deploy olur.
- denetlenebilir_olcut: Deployment süreci "Ended" ve "Success" döner; sunucu günlüğünde ERROR satırı yok; deploy edilen paket sürümü akış otomasyonu sürümüyle uyumlu.
- tuzak: Eski content pack sürümü yeni akış otomasyonu sürümünde desteklenmeyebilir. Hata iletisi (null) doğrudan pakete işaret etmez.
- gercek_cozum: Forum yanıtı (yanıt doğrudan önerdi, doğrulanmadı): 1.22 sürümü akış otomasyonu 2022.11'de desteklenmiyor; daha yeni bir content pack denenmeli.
- lab_uyarlamasi: Yalnız gerçek üründe. Content pack deploy motoru gerekir. Lab'da yalnız "paket sürüm uyumluluğu" kontrolü betiği yazılabilir ama akış otomasyonu deploy'u yaşatılamaz.

### F-AK-002 Base content pack 1.24.3: JSON Path işlemi geçersiz JSON döndürüyor

- kimlik: F-AK-002
- seviye: temel
- urun: akış otomasyonu
- kaynak: https://community.opentext.com/it-ops-cloud/oo/f/discussions/534502/json-path-operation-returns-invalid-json-in-afl-base-content-pack-1-24-3
- tarih: göreli "4 months ago"
- talep: AFL Base content pack 1.24.2'den 1.24.3'e yükseltince JSON Path işlemi, JSON yerine düz bir eşleme döndürüyor. 1.24.2'ye geri dönemiyorum çünkü SSH özel anahtar sorunu yeni sürümde düzeltildi.
- ortam_onkosulu: akış otomasyonu Studio ve akış otomasyonu Central (ikisi de 26.2.0), Windows. Base content pack 1.24.3.
- beklenen_sonuc: JSON Path, JSON biçiminde çıktı verir.
- denetlenebilir_olcut: Sonuç geçerli JSON olarak ayrıştırılır; `$.values.item` sorgusu düz JSON nesnesi döner.
- tuzak: Hata content pack sürümüne bağlıdır; akış otomasyonu sürümü değişmemiştir. Geri dönüş, başka bir düzeltilmiş özelliği bozabilir.
- gercek_cozum: Doğrulanmış: Destek kaydı açıldı; hata Base content pack 1.24.3'te doğrulandı ve sonraki sürümde düzeltilmek üzere kabul edildi. Forum yanıtındaki sürüm numarası bir yazım hatası gibi görünüyor; kaynakta 1.24.3 yazıyor.
- lab_uyarlamasi: Kısmi. Lab'da JSON Path benzeri bir Python işlemi ile çıktı biçimi karşılaştırması yapılabilir. Gerçek content pack yok.

### F-AK-003 Python operasyonunda **kwargs ile dinamik girdi

- kimlik: F-AK-003
- seviye: orta
- urun: akış otomasyonu
- kaynak: https://community.opentext.com/it-ops-cloud/oo/f/discussions/533478/kwargs-in-python-operation
- tarih: göreli "11 months ago"
- talep: akış otomasyonu 25.2'de bir Python operasyonuna adları değişken sayıda girdi vermek istiyorum ve betikte **kwargs ile hepsini döngüye almak. Amaç, bir metne 1 ya da daha fazla düzenli ifade uygulamak ve ilk eşleşmeyi döndürmek.
- ortam_onkosulu: akış otomasyonu 25.2 Studio. Python operasyonu.
- beklenen_sonuc: Operasyon, değişken sayıda regex girdisini alır, ilk eşleşmeyi döndürür.
- denetlenebilir_olcut: n ≥ 1 regex girdisiyle çalışır; ilk eşleşme çıktıda; eşleşme yoksa tanımlı bir boş değer döner.
- tuzak: Değişken sayıda girdi, akış otomasyonu'nun önceden tanımlı girdi modelinde doğrudan yoktur. Eşleşme yokken `match` değişkeni tanımsız kalabilir.
- gercek_cozum: Doğrulanmış (yazarın kendi çözümü): Tek bir girdi, regex listesi JSON dizisi olarak verilir; betikte `json.loads` ile okunur. Yazar bunu "çirkin" olarak tanımladı; **kwargs ile ilgili kesin çözüm yazılmadı.
- lab_uyarlamasi: Konteynerde Python betiği ve sahte bir girdi aktarımı. Gerçek akış otomasyonu Python operasyonu yok; girdi modeli farkı yalnız gerçek üründe test edilir.

### F-AK-004 Content pack içindeki sistem hesapları yapılandırma öğelerinde görünmüyor

- kimlik: F-AK-004
- seviye: temel
- urun: akış otomasyonu
- kaynak: https://community.opentext.com/it-ops-cloud/oo/f/discussions/533381/system-accounts-not-showing-in-configuration-items-page
- tarih: göreli "over 1 year ago"
- talep: Content pack'in sistem hesapları, content pack sayfasında görünüyor ama yapılandırma öğeleri sayfasında yok. Studio'da sistem hesaplarını dahil etme seçeneği açık.
- ortam_onkosulu: akış otomasyonu Central, içe aktarılmış content pack. Sistem hesapları klasörü ve rol yetkileri var.
- beklenen_sonuc: Sistem hesapları yapılandırma öğelerinde görünür.
- denetlenebilir_olcut: İlgili rol, sistem hesaplarını klasör altında "görüntüleme" ve "çalıştırma" yetkisiyle görür; yapılandırma öğeleri listesinde hesaplar listelenir.
- tuzak: Hesaplar oluşturulmuş olsa bile rolün klasör üzerinde yetkisi yoksa listede görünmez.
- gercek_cozum: Doğrulanmış: Sistem hesapları klasörü için ilgili role görüntüleme ve çalıştırma yetkisi verilir ve "alt öğelere uygula" işaretlenir.
- lab_uyarlamasi: Yalnız gerçek üründe. akış otomasyonu rol ve klasör modeli lab'da yoktur. Lab'da yetki matrisi bir tablo olarak kurulabilir ama kesin davranış doğrulanmaz.

### F-AK-005 OAuth 1.0 ile çağrı yapılandırma

- kimlik: F-AK-005
- seviye: ileri
- urun: akış otomasyonu
- kaynak: https://community.opentext.com/it-ops-cloud/oo/f/discussions/533168/oauth-1-0-in-oo
- tarih: göreli "over 1 year ago"
- talep: akış otomasyonu'da OAuth 2 var ama eski siteler OAuth 1.0 kullanıyor. Tüketici anahtarı, özel anahtar, parola ve imza yöntemi elimde. akış otomasyonu içinde nasıl uygularım?
- ortam_onkosulu: akış otomasyonu flow; hedef REST servisi OAuth 1.0 imzası bekliyor.
- beklenen_sonuc: OAuth 1.0 imzalı istek hedef servisten kabul görür.
- denetlenebilir_olcut: İsteğin Authorization başlığı doğru imza ile gönderilir; hedef servis 401 döndürmez.
- tuzak: Yalnız nonce ve zaman damgası yetmez; URL kodlama, sıralama ve HMAC imzası gerekir. Yapay zekâ önerisi (yapılandırmayı tek başına açıklamıyor) eksik kalıyor.
- gercek_cozum: Cevapsız. Forumda tam bir kılavuz yazılmadı; yalnız yüzeysel bir başlık örneği ve "daha karmaşık" yorumu var.
- lab_uyarlamasi: Konteynerde küçük bir OAuth 1.0 imza betiği (HMAC-SHA1) ve sahte bir REST uç noktası. Gerçek akış otomasyonu flow adımları yaşatılamaz; imza hesabı bağımsız doğrulanır.

### F-AK-006 MetaLayerQuery ile sorgu zaman aşımı (java.sql.SQLTimeoutException)

- kimlik: F-AK-006
- seviye: orta
- urun: akış otomasyonu
- kaynak: https://community.opentext.com/it-ops-cloud/oo/f/discussions/533099/flow-execute-metalayerquery-command-error---the-query-has-timed-out
- tarih: göreli "over 1 year ago"
- talep: Flow'da veritabanı sorgusu zaman zaman zaman aşımına uğruyor. Veritabanı tarafında CPU, bellek ve kilit yok. akış otomasyonu ya da flow tarafında başka bir yapılandırma var mı?
- ortam_onkosulu: akış otomasyonu flow, SQL sorgu komutu (jtds sürücüsü). Veritabanı tarafında sorun görünmüyor.
- beklenen_sonuc: Sorgu zaman aşımına uğramadan tamamlanır.
- denetlenebilir_olcut: Sorgu süresi ölçülebilir ve zaman aşımı eşiğinin altında; sürücü zaman aşımı yapılandırması belgelenmiş değerde.
- tuzak: Hata akış otomasyonu tarafında görünür ama asıl neden flow tasarımı ya da sorgu planı olabilir. Aynı sorgu başka ortamda çalışıyor olabilir.
- gercek_cozum: Cevapsız. Forum yanıtı destek kaydı açmayı ve flow ile günlükleri paylaşmayı önerdi.
- lab_uyarlamasi: Konteynerde bir veritabanı (ör. küçük bir SQL sunucusu) ve yavaş sorgu simülasyonu. Gerçek jtds sürücü ve MetaLayerQuery yok; yalnız zaman aşımı mantığı yaşatılır.

### F-AK-007 check_empty() Cloudlsang işlevi çalışmıyor

- kimlik: F-AK-007
- seviye: temel
- urun: akış otomasyonu
- kaynak: https://community.opentext.com/it-ops-cloud/oo/f/discussions/533115/why-dies-the-documented-function-check_empty-in-cloudlsang-doesnt-t-work
- tarih: göreli "over 1 year ago"
- talep: Belgelenmiş check_empty() işlevi akış otomasyonu Designer 24.02'de çalışmıyor. Boş bir değişkenin `eval(foo)["name"]` ifadesi boş değişkende hata veriyor. Alternatif var mı?
- ortam_onkosulu: akış otomasyonu Designer 24.02 ve 25.2 karşılaştırması. Girdi bir yapı (JSON nesnesi) ya da boş değer olabilir.
- beklenen_sonuc: Boş girdi için boş değer döner, dolu girdi için alan okunur.
- denetlenebilir_olcut: Boş girdi hata vermez; dolu girdi doğru alanı döndürür.
- tuzak: Belgede yer alan bir işlev her sürümde Workflow Designer'da bulunmayabilir.
- gercek_cozum: Doğrulanmış: Python yerel ifadesi kullanılır: `eval(foo)["name"] if foo else ''`.
- lab_uyarlamasi: Konteynerde Python ifade değerlendirmesi ile tam karşılık. Cloudlsang motoru yok, yalnız ifade mantığı doğrulanır.

### F-AK-008 ssh-rsa (SHA-1) ile eski SSH anahtarı reddediliyor (akış otomasyonu 24.1)

- kimlik: F-AK-008
- seviye: orta
- urun: akış otomasyonu
- kaynak: https://community.opentext.com/it-ops-cloud/oo/f/discussions/532673/ssh-rsa-3072-sha256-key-failis-to-auth
- tarih: göreli "over 1 year ago"
- talep: akış otomasyonu 24.1'de Uzak Komut Çalıştırma operasyonu, SSH ve WMI karışık çalışıyor. Bir SSH bağlantısı "Auth fail for methods 'publickey,...'" hatası veriyor. OpenSSH ssh-rsa'yı kullanımdan kaldırdığı için akış otomasyonu'da bunu açmak gerektiğini düşünüyorum.
- ortam_onkosulu: akış otomasyonu 24.1, Base content pack 1.23.10 snapshot. Hedef Linux sunucu modern OpenSSH ile çalışıyor.
- beklenen_sonuc: Uzak komut anahtar tabanlı kimlikle başarılı bağlanır.
- denetlenebilir_olcut: Bağlantı kurulur; kimlik doğrulama hatası yok; sunucuda kullanılan anahtar algoritması ve akış otomasyonu'nun desteklediği algoritma kesişir.
- tuzak: Hedef sunucu ssh-rsa'yı kapatmış olabilir; akış otomasyonu tarafı yapılandırma açsa bile sunucu kabul etmez. Anahtar tipi (ör. rsa-sha2-256) ile ssh-rsa aynı şey değildir.
- gercek_cozum: Cevapsız. Forumda yanıt görünmedi.
- lab_uyarlamasi: Kısmi. Konteynerde iki sshd yapılandırması (ssh-rsa açık ve kapalı) ile istemci algoritması karşılaştırması. akış otomasyonu'nun iç SSH kütüphanesi yaşatılamaz.

### F-AK-009 akış otomasyonu 24.1'de SSH sırasında ArrayIndexOutOfBoundsException (jsch DH anahtar değişimi)

- kimlik: F-AK-009
- seviye: ileri
- urun: akış otomasyonu
- kaynak: https://community.opentext.com/it-ops-cloud/oo/f/discussions/532276/operations-orchestration-24-1-failing-with-arrayindexoutofboundsexception
- tarih: göreli "over 1 year ago"
- talep: akış otomasyonu 24.1 kurulumundan sonra flow'lar aralıklı olarak başarısız oluyor. Günlükte SSH oturumunun bağlantı adımında (jsch DH anahtar değişimi) ArrayIndexOutOfBoundsException var.
- ortam_onkosulu: akış otomasyonu 24.1 (lisanslı), SSH tabanlı uzak komut operasyonu. Hata aralıklı.
- beklenen_sonuc: SSH oturumları her seferinde tutarlı şekilde kurulur.
- denetlenebilir_olcut: Aynı uzak komut 50 kez çalıştırıldığında hata yok; günlükte jsch istisnası yok.
- tuzak: Hata sporadik; tek denemede geçmesi düzeltme değildir. Ağ ya da sunucu tarafı yanıt biçimi de tetikleyici olabilir.
- gercek_cozum: Cevapsız. Forum yanıtı görünen kısımda yoktu.
- lab_uyarlamasi: Kısmi. Lab'da farklı SSH sunucu yapılandırmaları ve yük testi ile aralıklı davranış taklit edilebilir; jsch hatası yaşatılamaz.

### F-AK-010 Uzak komut "Could not read/parse the process return code" (yerel host)

- kimlik: F-AK-010
- seviye: temel
- urun: akış otomasyonu
- kaynak: https://community.opentext.com/it-ops-cloud/oo/f/discussions/531742/could-not-read-parse-the-process-return-code-please-verify-that-the-user-has-the-proper-access-to-run-remote-commands
- tarih: göreli "over 2 years ago"
- talep: Yerel host üzerinde komut çalıştırırken "Could not read/parse the process return code. Please verify that the user has the proper access to run remote commands." hatası alıyorum.
- ortam_onkosulu: akış otomasyonu, hedef olarak akış otomasyonu'nun çalıştığı yerel host. Komut kimlik bilgisiyle çalışacak.
- beklenen_sonuc: Komut çalışır ve dönüş kodu okunur.
- denetlenebilir_olcut: İşlem dönüş kodu okunur; hata iletisi yok; komut yerel çıkış kodunu döndürür.
- tuzak: Yerel hedefi uzak bağlantı gibi kullanmak güvenlik ayarlarında başarısız olur.
- gercek_cozum: Önerilen: Yerelde farklı kimlik bilgileriyle impersonate edilir ya da komut başka bir hostta çalıştırılır.
- lab_uyarlamasi: Konteynerde yerel komut ile SSH üzerinden kendi kendine bağlantı denemesi. Gerçek akış otomasyonu uzak komut motoru yok; yalnız bağlantı yolu farkı gösterilir.

### F-AK-011 JRSFlowInvoke yerine akışı yol ile REST üzerinden tetikleme

- kimlik: F-AK-011
- seviye: orta
- urun: akış otomasyonu
- kaynak: https://community.opentext.com/it-ops-cloud/oo/f/discussions/531149/jrsflowinvoke-replacement
- tarih: göreli "over 2 years ago"
- talep: akış otomasyonu 2019.07'den 24.1'e geçiyoruz. Betiklerde JRSFlowInvoke kullanılıyor; akışı yol (klasör/akış adı) ile çağırabiliyorduk. 24.1'de PAS yolu yok. Komut satırı aracı ya da eski PAS.war'ı yeni Tomcat'e taşıma çözüm mü?
- ortam_onkosulu: akış otomasyonu 2019.07 üretimden akış otomasyonu 24.1'e geçiş. Betikler kullanıcı adı ve şifreli parola ile çağırıyor.
- beklenen_sonuc: Betikler akışı yoldan ya da UUID'den çağırır; çağrı başarılı döner.
- denetlenebilir_olcut: Yeni betik akışı başlatır, çıktı döner; akış UUID'si değişmemiş; eski betik sürümü yeni ortamda hata vermez.
- tuzak: Akış UUID'si yalnız akış silinip yeniden oluşturulursa değişir. SOAP API 9.x'ten 10.x'e geçiş için tutulmuş eski bir yöntemdi.
- gercek_cozum: Doğrulanmış: SOAP tabanlı eski API yerine REST API kullanılır. Forumda ayrıca bir yanıt, akış yolu yerine UUID ile JSON yükü oluşturan bir bash betiğinin çalıştığını bildirdi.
- lab_uyarlamasi: Konteynerde sahte bir REST uç noktası (run_async benzeri) ve bir betik. Gerçek akış otomasyonu yok; yalnız "yol yerine UUID ile çağırma" ve JSON yükü oluşturma adımı yaşatılır.

### F-AK-014 İki standalone akış otomasyonu Central'ı tek kümeye dönüştürme

- kimlik: F-AK-014
- seviye: ileri
- urun: akış otomasyonu
- kaynak: https://community.opentext.com/it-ops-cloud/oo/f/discussions/531126/converting-two-standalone-oo-central-installations-into-a-cluster
- tarih: göreli "over 2 years ago"
- talep: RHEL 8.9 üzerinde iki standalone akış otomasyonu Central 24.1 kurulumunu kümeye dönüştürmek istiyoruz. Birini düğüm olarak dönüştürmek mümkün mü, yoksa yeniden kurulum mu gerekir? Yük dengeleyici zorunlu mu?
- ortam_onkosulu: İki akış otomasyonu Central 24.1, RHEL 8.9. Ayrı veritabanı geçmişleri var.
- beklenen_sonuc: Tek küme; iş yükü iki worker arasında dağılır.
- denetlenebilir_olcut: Küme üyelikleri doğru; işler her iki worker'a dağılıyor; veritabanı geçmişi kayıpsız taşınmış ya da yeni kurulum bilinçli seçilmiş.
- tuzak: Standalone'u dönüştürmek veritabanı geçmişini kümeye taşımaz; dönüşümün kazancı sıfır olabilir.
- gercek_cozum: Doğrulanmış: Düğüm dönüşümü teknik olarak mümkün ama hata noktaları çok olduğu için yeniden kurulum daha hızlı. Yük dengeleyici zorunlu değil; iş dağılımı veritabanı üzerinden yapılır.
- lab_uyarlamasi: Kısmi. Lab'da iki konteyner ve paylaşılan bir veritabanı ile iş kuyruğu dağılımı modeli kurulabilir; akış otomasyonu Central kümeleme kurulumu yaşatılamaz.

### F-AK-012 .NET tabanlı operasyonlar Studio'da hata veriyor (getMetadata)

- kimlik: F-AK-012
- seviye: ileri
- urun: akış otomasyonu
- kaynak: https://community.opentext.com/it-ops-cloud/oo/f/discussions/531207/net-operations-failed-to-execute-method
- tarih: göreli "over 2 years ago"
- talep: akış otomasyonu Studio 2023.05 build 61'de .NET tabanlı tüm operasyonlar kırmızı altı çizili ve "Failed to execute method [getMetadata]" hatası veriyor. Java operasyonları çalışıyor. Aynı content pack diğer makinelerde sorunsuz. akış otomasyonu ve .NET Framework yeniden kurulunca düzelmedi.
- ortam_onkosulu: akış otomasyonu Studio 2023.05 build 61, Windows. .NET Framework 4.8.1 ve kalıntı .NET 8 kaldırılmış. Birden çok content pack (Virtualization, oo10-base-cp) etkilenmiş.
- beklenen_sonuc: .NET operasyonları yüklenir ve metaveri okunur.
- denetlenebilir_olcut: Operasyonların hiçbiri kırmızı altı çizili değil; getMetadata çağrısı hata vermez; Fusion günlüğünde eksik assembly yok.
- tuzak: Yeniden kurulum ve paket yeniden içe aktarma sorunu çözmez. Eksik ortam değişkeni ya da yanlış derleme sürümü gibi nedenler yerinde kontrol edilmeli.
- gercek_cozum: Cevapsız. Forum yanıtı (kısmen görünen) destek ekibinden yanıt bekleniyor gibi; kesin çözüm görünmedi.
- lab_uyarlamasi: Yalnız gerçek üründe. Windows ve .NET Framework olmadan yaşatılamaz.

### F-AK-013 Ekip bazlı klasör görünürlüğü: güvenlik ve BT desteği ayrımı

- kimlik: F-AK-013
- seviye: orta
- urun: akış otomasyonu
- kaynak: https://community.opentext.com/it-ops-cloud/oo/f/discussions/531275/permissions-to-user
- tarih: göreli "over 2 years ago"
- talep: İki ekip (Güvenlik ve BT Desteği) için ayrı akışlar yaptım. Her ekip yalnız kendi klasörünü görsün, diğerinin klasörünü görmesin istiyorum.
- ortam_onkosulu: akış otomasyonu Central 24.4.1, iki rol ve iki klasör. Kullanıcılar gruplara bağlı.
- beklenen_sonuc: Her ekip yalnız kendi klasörünü görür ve çalıştırır.
- denetlenebilir_olcut: A ekibi üyesi B klasörünü listede görmez; A ekibi kendi akışlarını çalıştırabilir; uzaktan hata ayıklama yetkisi olan rol yok.
- tuzak: Uzaktan hata ayıklama (remote debug) yetkisi kütüphanenin tamamını görünür yapar. "Alt öğelere uygula" işaretlenmezse değişiklik alt klasörlere ulaşmaz.
- gercek_cozum: Doğrulanmış: İki ayrı rol oluşturulur; tüm klasörler için çalıştırma, yalnız ilgili klasörler için görüntüleme; uzaktan hata ayıklama kapatılır; yetkiler klasör üzerinden verilir ve "alt öğelere uygula" işaretlenir.
- lab_uyarlamasi: Lab'da rol ve klasör yetki matrisi tablosu. Gerçek akış otomasyonu yetkilendirmesi yaşatılmaz; yetki çakışması kuralları lab'da simüle edilir.

### F-AK-016 akış otomasyonu Central 24.1 kurulumunda Java 17 Insights adımında classes.jsa NoSuchFileException (Windows)

- kimlik: F-AK-016
- seviye: orta
- urun: akış otomasyonu
- kaynak: https://community.opentext.com/it-ops-cloud/oo/f/discussions/531068/oo-24-1-installation-classes-jsa-nosuchfileexception
- tarih: göreli "over 2 years ago"; günlük tarihi 2025-01-27
- talep: akış otomasyonu Central 24.1 kurulumunda "Deploy Java 17 Insights" adımında classes.jsa dosyası kopyalanamıyor (NoSuchFileException). Geçici dizinde dosya var.
- ortam_onkosulu: Windows, akış otomasyonu Central 24.1, kurulum sırasında Java 17 Insights.
- beklenen_sonuc: Insights kopyalanır; kurulum tamamlanır.
- denetlenebilir_olcut: Kopyalama adımı hata vermeden biter; classes.jsa hedef dizinde.
- tuzak: Dosya geçici dizinde var görünür ama kurulumdan önce başka bir yazılım (izleme ajanı) tarafından engellenebilir.
- gercek_cozum: Doğrulanmış: Sorun, izleme ajanının (forumda Dynatrace OneAgent olduğu söyleniyor) kurulum dosyasını engellemesidir. Geçici çözüm: kurulum sırasında dosya yeniden adlandırılır, kurulum bittikten sonra geri adlandırılır.
- lab_uyarlamasi: Yalnız gerçek üründe. Windows ve akış otomasyonu kurulumu gerekir. Lab'da yalnız "dosya kilidi" davranışı Linux'ta simüle edilebilir.

### F-AK-015 akış otomasyonu Containerized 24.4: uploadimages aşamasında büyük imajlar başarısız

- kimlik: F-AK-015
- seviye: temel
- urun: akış otomasyonu
- kaynak: https://community.opentext.com/it-ops-cloud/oo/f/discussions/531048/oo-containerized-24-4---uploadimages-failed
- tarih: göreli "over 2 years ago"; günlük tarihi 2025-01-21
- talep: Helm chart 24.4 ile akış otomasyonu konteyner kurulumunda 13 imajı yerel kayıt defterine yüklerken "orchestration-downloader" (yaklaşık 25 GB) 40 dakika sonra başarısız oluyor. Kayıt depolama alanı yetersiz görünüyor.
- ortam_onkosulu: Çevrimdışı kurulum, yerel kayıt defteri. Depolama alanı sınırlı.
- beklenen_sonuc: 13 imaj yerel kayıt defterine tamamen yüklenir.
- denetlenebilir_olcut: uploadimages betiği 0 ile döner; tüm imajlar kayıt defterinde listelenir.
- tuzak: Hata iletisi genel; kimlik ya da proxy de sebep olabilir. Büyük imaj eşzamanlı yükleme ile zaman aşımına uğrayabilir.
- gercek_cozum: Doğrulanmış: uploadimages komutuna eşzamanlılık parametresi (-c 2) eklenerek yükleme tamamlandı.
- lab_uyarlamasi: Konteynerde yerel bir kayıt defteri ve büyük dosya yüklemesi simülasyonu; eşzamanlılık ve depolama sınırı. Gerçek akış otomasyonu imajları yok.

### F-AK-018 akış otomasyonu 2023.05'te Purge Execution Summary akışı kararsız

- kimlik: F-AK-018
- seviye: ileri
- urun: akış otomasyonu
- kaynak: https://community.opentext.com/it-ops-cloud/oo/f/discussions/529685/oo-2023-05---purge-execution-summary-flow-a-hit-and-miss
- tarih: göreli "over 2 years ago"
- talep: akış otomasyonu 2023.05'te "Purge Execution Summary" akışı bazen çalışıyor bazen çalışmıyor. maxAmount ve delayBetweenRequests değerleriyle oynadım. Akış, kayıt silinmemesine rağmen çalışmaya devam ediyor. Veritabanı Oracle 19c.
- ortam_onkosulu: akış otomasyonu 2023.05, Oracle 19c. Veritabanı bağlantı havuzu ayarları belirtilmiş.
- beklenen_sonuc: Akış, bitince kayıtları siler ve sonlanır.
- denetlenebilir_olcut: Akış belirli sürede biter; silinecek kayıt kalmayınca akış sonlanır; veritabanı yazma günlüğü taşmaz.
- tuzak: Akış, silme işi bittikten sonra da çalışmaya devam eder. Parametre ayarı tek başına çözüm değildir.
- gercek_cozum: Önerilen: Akışın en güncel content pack sürümü denenir (destek yanıtı). Bir kullanıcı ise kendi yazdığı, toplu silme yapan saklı yordamı ve zamanlanmış işi önerdi (doğrulanmamış çözüm).
- lab_uyarlamasi: Yalnız gerçek üründe. Lab'da yalnız toplu silme mantığı (partiler halinde silme, işlem günlüğünü şişirmeme) bir SQL tabanlı küçük veritabanında yaşatılabilir.

### F-AK-017 Flow hatasında bir çıktı alanında mesaj döndürme (SMAX isteği için)

- kimlik: F-AK-017
- seviye: orta
- urun: akış otomasyonu
- kaynak: https://community.opentext.com/it-ops-cloud/oo/f/discussions/530644/return-message-as-flow-output-field-on-error
- tarih: göreli "over 2 years ago"
- talep: Flow hata ile sonlandığında, SMAX'taki isteğe bir hata mesajını çıktı alanı üzerinden döndürmek istiyorum. Bağlam (context) çözüm mü?
- ortam_onkosulu: akış otomasyonu flow, SMAX isteği çağıran sistem. Hata yolunda çıktı alanı tanımlı.
- beklenen_sonuc: Hata durumunda çağıran sistem hata mesajını çıktı alanından alır.
- denetlenebilir_olcut: Hata yolu sonunda çıktı alanı dolu; çağıran sistem bu alanı okur; başarılı yolda error alanı boş.
- tuzak: Bağlam değişkenleri akış içi adımlar içindir; çağıran sisteme çıkış sağlamaz. Hata sonlandırmasında çıktı alanı açıkça tanımlanmalı.
- gercek_cozum: Önerilen (yanıt, yazarın kendi uygulaması): Flow'da iki çıktı alanı tanımlanır: "message" ve "error_message" (ya da "output" ve "error_output"). Hata mesajı bu alanlardan diğer sistemlere ya da bir günlük tablosuna yazılır.
- lab_uyarlamasi: Konteynerde iki çıktı alanlı bir betik ve çağıran bir istemci. Gerçek SMAX ve akış otomasyonu akışı yok; çıktı alanı sözleşmesi yaşatılır.

### F-AK-019 Konfigürasyon dışa/içe aktarma: akış otomasyonu 10.80'den 24.4'e

- kimlik: F-AK-019
- seviye: ileri
- urun: akış otomasyonu
- kaynak: https://community.opentext.com/it-ops-cloud/oo/f/discussions/530614/config-export-and-import-in-oo
- tarih: göreli "over 2 years ago"
- talep: akış otomasyonu 10.80 kurulumundan yapılandırmayı dışa aktarıp 24.4'e içe aktarmak istiyorum. Yol nedir?
- ortam_onkosulu: akış otomasyonu 10.80 üretim ortamı, akış otomasyonu 24.4 yeni kurulum.
- beklenen_sonuc: Yapılandırma ve akışlar yeni ortamda kullanılabilir hale gelir.
- denetlenebilir_olcut: Yeni ortamda akışlar, roller ve bağlantılar eski ortamla tutarlı; kayıp yapılandırma yok.
- tuzak: Sürüm farkı çok büyük. Doğrudan veri aktarımı desteklenmiyor; veri dönüşümleri gizli.
- gercek_cozum: Doğrulanmış: Çok büyük sürüm farkı nedeniyle veri aktarımı önerilmez. Mümkünse ara sürümlerle yükseltme yapılır; değilse yeni sürüm temiz kurulur ve eski ortama göre yapılandırılır.
- lab_uyarlamasi: Yalnız gerçek üründe. Lab'da iki sürümü taklit etmek anlamlı değil; yalnız "yapılandırma envanteri çıkarma ve karşılaştırma" adımı bir JSON envanteri ile yapılabilir.

### F-AK-020 ITOM Marketplace'ten SMAX content pack indirme hatası (RequestHeaderSectionTooLarge)

- kimlik: F-AK-020
- seviye: temel
- urun: akış otomasyonu
- kaynak: https://community.opentext.com/it-ops-cloud/oo/f/discussions/534323/unable-to-download-oo-micro-focus-smax-content-pack-requestheadersectiontoolarge-error
- tarih: göreli "5 months ago"
- talep: ITOM Marketplace'ten akış otomasyonu Micro Focus SMAX content pack indirilirken bağlantı XML hata sayfasına yönleniyor: "RequestHeaderSectionTooLarge". Başka biri indirebiliyor.
- ortam_onkosulu: Tarayıcı ile ITOM Marketplace indirmesi. Hata yerel tarayıcı ya da oturum çerezleriyle ilgili olabilir.
- beklenen_sonuc: Content pack dosyası indirilir.
- denetlenebilir_olcut: Dosya bütünlüğü doğrulanır; indirme tarayıcıdan tamamlanır.
- tuzak: Hata sunucu tarafında değil, istemci başlık boyutu (çerez birikimi) kaynaklı olabilir. Ağ da sebep olabilir.
- gercek_cozum: Önerilen (yanıt): Tarayıcı değiştirilir. Bir yanıt Mac/Edge ile sorunsuz indirildiğini bildirdi; kesin neden yazılmadı.
- lab_uyarlamasi: Yalnız gerçek ortam. Lab'da başlık boyutu sınırı olan bir vekil sunucu ile RequestHeaderSectionTooLarge benzeri 431 yanıtı simüle edilebilir.

---

## DCA lifecycle ve ürün sağlığı bulguları

Konu adresi (forumda bu yolda; akış otomasyonu yolu değil): https://community.opentext.com/it-ops-cloud/automation-ctr/f/discussions/534747/dca-lifecycle-has-development-stopped
Tarih: göreli "1 month ago". Kaynak: `automation-ctr/f/discussions` altında.

- Kim ne soruyor: sunucu otomasyonu'yı v6.5'ten beri kullanan uzun süreli bir müşteri. Kısmi bir DCA dağıtımı (OPTIC Reporting) stabil çalışmış, ama tam DCA kurulumu 5 sunuculu ortamda (2 worker, Postgres, Vertica) hiç kararlı duruma gelmemiş. Yaklaşık bir yıl boyunca 20 kurulum denemesinin tamamı yüzde 100 tamamlanmamış. Yazar, Qualys eklentisi ve remediation zamanlamasını önemli bulduğunu, ama "temel kurulumu destekleyemediği bir ürünü çalıştırmayacağını" belirtiyor. Yol haritası, DCA 23.4 yeni sürümü ve ürün değişimi hakkında bilgi istiyor.
- Resmi cevap: Forumda doğrulanmış ya da yetkili bir OpenText yanıtı görünmedi. Yanıt alanı boş, "Verified Answers" bölümünde kayıt yok.
- Yorum: Bu konu tek başına genellenemez, ama bir kullanıcının ürünü terk etme kararını açıkça yazması ve yol haritası sorusuna resmi yanıt gelmemesi, ürünün geleceği tezi için doğrudan kanıt niteliğindedir. Konu yalnız Automation Center genel tartışmaları altında olduğu için sunucu otomasyonu ve akış otomasyonu forumlarında bu sorunun daha dar bir kopyası aranmadı.

Ürün sağlığı gözlemleri (okunan konulara dayalı):

- sunucu otomasyonu forumundaki 26 okunan konunun 22'si "This discussion has been locked" (kilitli) durumunda. Kilitli konularda yeni yanıt yazılamıyor; birçok soru bu yüzden yanıtsız kalmış.
- Resmi cevap sık sık "destek kaydı açın" ya da "dokümantasyona bakın" biçimindedir. Örnekler: sunucu otomasyonu startsync (F-SV-009), Marketplace/Connector (F-SV-003), akış otomasyonu uzak komut (F-AK-006), akış otomasyonu 24.1 jsch (F-AK-009).
- Birçok cevap belgeye yönlendirir, ama "örnek senaryo" yoktur (ör. sunucu otomasyonu SOAP API ile betik tetikleme konusunda, 527362: yanıt yalnız belgeye yönlendirdi ve örnek olmadığını söyledi).
- Ürün dışına taşan ya da kaldırılan özellikler: akış otomasyonu'da Cloudlsang check_empty belgelenmiş ama Workflow Designer'da yok (F-AK-007). sunucu otomasyonu'da agent'ı API ile tam kaldırma yok (F-SV-001). akış otomasyonu sürümleri arası veri aktarımı destekli değil (F-AK-019).
- Platform bağımlılığı: Windows 2025 yama kapsamı (F-SV-007) ve Windows 2016 izinleri (F-SV-004) gibi konularda sunucu otomasyonu'nın işletim sistemi desteği bekleme ve destek kaydı gerektiriyor.

---

## Kırılım

Toplam vaka: 42. sunucu otomasyonu 22, akış otomasyonu 20. Bench eşiği (30) karşılandı.

- Ürüne göre: sunucu otomasyonu 22, akış otomasyonu 20, DCA ayrı bölümde (vaka sayılmadı).
- Seviyeye göre: temel 10, orta 22, ileri 10.
- Çözüm durumuna göre (gercek_cozum): doğrulanmış 19, önerilen ya da kısmi 11, cevapsız ya da yalnız destek kaydı 12.
- Lab uyarlaması: 12 vaka yalnız gerçek üründe test edilebilir; 8 vaka lab'da kısmen yaşatılabilir; kalan 22 vaka lab'da (sahte konteyner ve posta sunucusuyla) büyük ölçüde yaşatılabilir.

Okunan ama vaka olarak yazılmayan konular: 532731 (aynı Global Shell mail sorusu, 532733 vakasıyla birleştirildi), 530606 (reqcheck hash doğrulaması: cevapsız, kapsam dışı), 527362 ve 527083 (yalnız belgeye yönlendirme, örnek senaryo yok), 532413 ve 532885 (yalnız belgeye yönlendirme), 530707 (gitignore: forum yanıtı yalnız PIP iç git uygulamasını açıklıyor), 530738 (özel JavaScript kütüphanesi: cevapsız), 530887 (SiteScope ürünü, akış otomasyonu dışı).

Okunmayan ama liste sayfasında görülen konular (yalnız başlıkları bilinir): sunucu otomasyonu 534791 (emSign), 534498 (kod imzalama talebi), 533126 (DCA kafka-broker), 529310, 529256, 529336, 529312, 529032, 528188, 527375, 527360, 525904, 525478, 525160, 525077, 524932, 524845, 524796, 523995, 529070, 529437, 525617. akış otomasyonu liste sayfalarında 531950 ve 531116 de görüldü, okunmadı.
