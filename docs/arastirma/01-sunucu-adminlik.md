# OpenText sunucu otomasyonu (sunucu otomasyonu) Adminlik İş Kataloğu ve Rakip Karşılaştırması

Tarih: 2026-11-17. Kaynakların büyük bölümü docs.microfocus.com üzerindeki sunucu otomasyonu 10.50, 10.51 ve 10.60 kullanıcı/yönetici belgeleri. docs.opentext.com üzerinde sunucu otomasyonu sayfası bulunamadı; arama sonuçları eski Micro Focus alan adına yöneldi.

Önemli not: BMC TrueSight sunucu otomasyonu (eski BladeLogic) ve HCL BigFix belgeleri aynı soyda ama başka ürünlerdir. Bu metinde bunlar "analog" olarak işaretlenmiştir ve sunucu otomasyonu için kesin bilgi sayılmamalıdır. Belgeler arasında terminoloji farkı var: 10.60 sayfası "device group" yerine "server group" diyor.

---

## 1. sunucu otomasyonu adminlik iş kataloğu

### 1.1 Sunucu grubu / device group yönetimi
- **Ne yapılır:** Sunucuları statik ya da dinamik gruplara koymak; grupları genel ya da özel yapmak; grupları erişim sınırı olarak kullanmak. Üyelik elle ya da kurallarla belirlenir.
- **Girdiler:** Sunucu listesi ya da kural ifadesi, grup adı, görünürlük.
- **Tipik adımlar:** Grup oluştur, sunucu ekle/çıkar, grubu müşteri ya da facility yetkisiyle eşle.
- **Çıktı:** Grup üyeliği; sonraki işlerin hedef kümesi.
- **Sık hata:** Grup üyeliğinin iş tanımlandığı anda mı, çalıştığı anda mı çözüldüğünü karıştırmak (aşağıda 2. bölüm).
- **Kaynak:** [sunucu otomasyonu 10.60 Run a server script](https://docs.microfocus.com/SA/10.60/Content/SA_UG_Server_Automation/script_execution/RunningaServerScriptSavedScriptorAdHocScript.htm); [Server management tasks 10.60](https://docs.microfocus.com/SA/10.60/Content/SA_UG_Server_Automation/servers_sas_client/BasicServerManagementTasks.htm); [sunucu otomasyonu User Guide 10.60](https://docs.microfocus.com/SA/10.60/Content/place_holders/Server_Automation_User_Guide.htm).

### 1.2 Run Server Script ve script kütüphanesi
- **Ne yapılır:** Kayıtlı ya da ad hoc betiği bir ya da birden çok sunucuda çalıştırmak, sonucu izlemek, dışa aktarmak. Betikleri kütüphanede yönetmek.
- **Girdiler:** Hedef sunucu/grup, betik, çalıştırma kullanıcısı, zaman aşımı, parametreler.
- **Tipik adımlar:** Hedef seç, betiği seç ya da tanımla, kullanıcı ve zaman aşımını ayarla, zamanla ya da hemen başlat, işi izle.
- **Çıktı:** Sunucu bazlı durum, çıkış kodu, betik çıktısı, dışa aktarılan rapor.
- **Sık hata:** Zaman aşımının yetersiz kalması; aynı kullanıcı adı ve parolanın tüm sunucularda aynı olmaması (eşzamanlı çalıştırmayı bozar).
- **Kaynak:** [Run a server script 10.60](https://docs.microfocus.com/SA/10.60/Content/SA_UG_Server_Automation/script_execution/RunningaServerScriptSavedScriptorAdHocScript.htm); [Ways to open the Run Script window 10.60](https://docs.microfocus.com/SA/10.60/Content/SA_UG_Server_Automation/script_execution/WaystoOpentheRunScriptWindow.htm).

### 1.3 Ajan (sunucu otomasyonu Agent) kurulumu, erişilemeyen ajanlar, Communication Test
- **Ne yapılır:** Sunucuya ajan kurmak ve kaydetmek; ajanın Core ile konuşup konuşmadığını test etmek; erişilemeyen ajanı onarmak.
- **Girdiler:** Sunucu adı ve IP, ajan kurulum paketi, yönetim IP'si.
- **Tipik adımlar:** Communication Test çalıştır; başarısız testi bul; ilgili bileşeni kontrol et; ajanı yeniden başlat; testi tekrar çalıştır.
- **Test bileşenleri (10.60):** Agent-DAE, Agent-SWR, CE-AGT, Agent-CE, MID eşleşme testi. Bazı testler önceki başarısızlıkta atlanır; önce başarısız olanlar çözülür, sonra test tekrarlanır.
- **Bilinen onarım önerileri (belgeden):** AGT başarısızlığında ajanın çalıştığını ve yönetim IP'sinin doğru olduğunu kontrol et; bağlantı reddi için güvenlik duvarına bak; zaman aşımında ajanı yeniden başlat. SWR başarısızlığında sunucunun IP'si değişmiş olabilir; ajanı durdurup yeniden başlat.
- **Sık hata:** IP değişikliği; güvenlik duvarı; ajanın hiç çalışmaması.
- **Kaynak:** [Troubleshooting server communication tests 10.60](https://docs.microfocus.com/SA/10.60/Content/SA_UG_Server_Automation/TroubleshootAgentUnreach/TroubleshootingServerCommunicationTests.htm); [CE to Agent (AGT) test](https://docs.microfocus.com/SA/10.60/Content/SA_UG_Server_Automation/TroubleshootAgentUnreach/CommandEnginetoAgentAGTTest.htm); [Agent to SWR test](https://docs.microfocus.com/SA/10.60/Content/SA_UG_Server_Automation/TroubleshootAgentUnreach/AgenttoSoftwareRepositorySWRTest.htm); [MID match test 10.60](https://docs.microfocus.com/SA/10.60/Content/SA_UG_Server_Automation/TroubleshootAgentUnreach/MachineIDMatchMIDTest.htm); [Running server communication tests 10.50](https://docs.microfocus.com/SA/10.50/Content/SA_UG_Server_Automation/agent_deployment/RunningServerCommunicationTests.htm).
- **Analog (BMC):** Ajan yükseltmesini "Agent Installer Job" ile yapma ve yükseltme sırasında başka iş çalıştırmama önerisi. [BMC: Upgrading the RSCD Agent](https://docs.bmc.com/docs/display/tssa2002/Upgrading+the+RSCD+Agent+using+an+Agent+Installer+Job). sunucu otomasyonu'daki karşılığı doğrulanamadı.

### 1.4 Yama (Windows/Linux patch policy, remediation)
- **Ne yapılır:** Yama ayarlarını ve yama politikalarını tanımlamak; sunucuları yama uyumuna göre taramak; eksik yamaları uygulamak (remediation).
- **Girdiler:** Yama kaynağı (Windows için yama içeriği, Linux için depo ya da SUSE için SMT ile içe aktarılan içerik), politika, hedef grup.
- **Tipik adımlar:** Yama ayarlarını yapılandır; yama politikasını oluştur ve gruba ata; tara; uygunsuz sunucuları remediate et; sonucu raporla.
- **Çıktı:** Uyumluluk durumu; uygulanan yama listesi; başarısız sunucular.
- **Sık hata:** Yama içeriğinin güncel olmaması; Linux'ta depo erişimi; SLES'te Zypper ile eski çekirdek seçilmesi (10.60'ta düzeltildiği yazıyor).
- **Kaynak:** [Patch Management Process 10.60](https://docs.microfocus.com/SA/10.60/Content/Patch_Mgmt/Patch_Management_Process.htm); [Patch Management Tasks Windows 10.60](https://docs.microfocus.com/SA/10.60/Content/Patch_Mgmt/Patch_Management_Tasks_Windows.htm); [About patching 10.60](https://docs.microfocus.com/SA/10.60/Content/Patch_Mgmt/AboutPatching.htm); [Specifying remediation options 10.60](https://docs.microfocus.com/SA/10.60/Content/SwProv_UG/software_remediation/SpecifyingRemediationOptions.htm); [10.60 What's new](https://docs.microfocus.com/SA/10.60/Content/Home.htm).
- **Doğrulanamadı:** Windows Server 2016 ve bazı Linux sürümlerinin 10.60'ta desteğinin düştüğü belirtiliyor; güncel destek matrisi için [sunucu otomasyonu 10.60 Support and Compatibility Matrix](https://docs.microfocus.com/SA/10.60/Content/Release_Notes/whats_new.htm) sayfasına ve HPE/OpenText destek portalına bakılmalı (sayfa desteği listesi tam çıkmadı).
- **Analog (BMC):** Yama kataloğu metadatası Windows için Shavlik, Linux için işletim sistemi satıcısı; üretim ortamında yama deposu için SUSE sunucu önerisi. [BMC patch management](https://docs.bmc.com/docs/display/bsadoc/Patch+management+overview+and+workflow). sunucu otomasyonu için doğrulanamadı.

### 1.5 Yazılım politikaları ve paket dağıtımı
- **Ne yapılır:** Bir sunucuda kurulacak paket, betik ve uygulama ayarlarının sıralı kümesi olan yazılım politikası tanımlamak, sunucu ya da gruba atamak, remediate etmek.
- **Girdiler:** Paketler (RPM, MSI vb.), betikler, uygulama yapılandırmaları, hedef.
- **Tipik adımlar:** Politika oluştur; öğeleri sırala; test sunucusunda dene; üretim grubuna ata; remediate et; uyumluluk taraması yap.
- **Önemli davranış:** Politika atamak tek başına kurulum yapmaz; remediation kurulumu yapar. Politika değiştirildiğinde o politikayı kullanan sunucular uyumsuz hale gelir ve yeniden remediation gerekir.
- **Kaynak:** [Policy-based software installation 10.60](https://docs.microfocus.com/SA/10.60/Content/SwProv_UG/software_management/AboutPolicy-BasedSoftwareInstallationandManagement.htm); [Creating and managing software policies 10.60](https://docs.microfocus.com/SA/10.60/Content/SwProv_UG/software_policies/CreatingandManagingSoftwarePolicies.htm); [Remediating servers with software policies 10.60](https://docs.microfocus.com/SA/10.60/Content/SwProv_UG/software_remediation/RemediatingServerswithSoftwarePolicies.htm); [Installing software using software policy 10.60](https://docs.microfocus.com/SA/10.60/Content/SwProv_UG/package_management/InstallingSoftwareUsingSoftwarePolicy.htm).
- **Belge önerisi:** Yeni politikayı önce test sunucusunda dene, sonra üretime uygula.

### 1.6 Audit, compliance, snapshot
- **Ne yapılır:** Bir "altın" sunucunun yapılandırmasını snapshot olarak almak; diğer sunucuları bu referansa ya da kurallara göre audit etmek; sapmaları remediate etmek.
- **Girdiler:** Referans sunucu ya da snapshot spesifikasyonu, audit politikası, kurallar.
- **Tipik adımlar:** Snapshot spec oluştur; snapshot job çalıştır; snapshot'ı audit kaynağı olarak seç; audit çalıştır; sonuçları incele; kurala göre remediate et.
- **Çıktı:** Audit sonucu (uyumlu/uyumsuz), snapshot kayıtları.
- **Sık hata:** Referans snapshot'ın güncel olmaması; audit kaynağının yanlış seçilmesi.
- **Kaynak:** [Snapshots and snapshot jobs 10.60](https://docs.microfocus.com/SA/10.60/Content/audit/snapshots/Snapshots_SnapshotSpecifications_SnapshotJobs.htm); [Audits and audit results 10.60](https://docs.microfocus.com/SA/10.60/Content/audit/audits/AuditsAuditPoliciesandAuditResults.htm); [Audit snapshot sources 10.60](https://docs.microfocus.com/SA/10.60/Content/audit/audits/AuditSnapshotSources.htm); [Remediating comparison-based audit results 10.60](https://docs.microfocus.com/SA/10.60/Content/audit/audits/RemediatingComparison-BasedAuditResults.htm); [Audit and remediation overview 10.60](https://docs.microfocus.com/SA/10.60/Content/SA_overview/feature_overview/AuditandRemediation.htm).
- **Doğrulanamadı:** Snapshot tabanlı audit için sunucu otomasyonu Client'taki tam menü adımları.

### 1.7 OS provisioning (build plan)
- **Ne yapılır:** Çıplak metal ya da mevcut sunucuya işletim sistemi kurmak; ardından batch job ile yapılandırma, dosya ve yazılım kurmak.
- **Girdiler:** Sistem paketi (her OS için), build plan, PXE/önyükleme sunucusu, MAC/donanım bilgisi.
- **Tipik adımlar:** Sistem paketi ve build plan oluştur; boot sunucusunu hazırla; sunucuyu provision et; post-install batch job çalıştır.
- **Platform notu (analog, eski sürüm):** Windows ve Linux için PXE; Solaris için JumpStart (11 için Automated Installer); AIX için NIM; HP-UX için Ignite.
- **Kaynak:** [About sunucu otomasyonu provisioning 10.60](https://docs.microfocus.com/SA/10.60/Content/SA_OS_Provisioning_Guide/AboutSAProvisioning.htm); [About sunucu otomasyonu provisioning 10.51](https://docs.microfocus.com/SA/10.51/Content/SA_OS_Provisioning_Guide/AboutSAProvisioning.htm); [BMC Planning for provisioning (analog)](https://docs.bmc.com/docs/display/bsadoc/Planning+for+provisioning).
- **Doğrulanamadı:** 10.51 yardım menüsündeki "Creating New sunucu otomasyonu Build Plans" konusunun içeriği; sunucu otomasyonu'da build plan'ın tam girdileri.

### 1.8 Uygulama dağıtımı
- **Ne yapılır:** Uygulama yapılandırma ve dağıtımı. sunucu otomasyonu belgelerinde ayrı bir "application configuration" bölümü var (Quick start to application configuration 10.60).
- **Kaynak:** [Quick start to application configuration 10.60](https://docs.microfocus.com/SA/10.60/Content/app_config/QuickStarttoApplicationConfiguration.htm).
- **Doğrulanamadı:** Uygulama dağıtımının ayrıntılı adımları ve girdileri (sayfa içeriği alınamadı).

### 1.9 Global Shell, rosh, OGFS
- **Ne yapılır:** Yönetilen sunuculara merkezi komut satırı üzerinden erişmek; dosya sistemi görünümü (OGFS) üzerinden çalışmak; betik ve yerel komut çalıştırmak.
- **Ana kullanım:** `rosh` iki modda çalışır: `jump` (sunucuda etkileşimli kabuk) ve `reach` (uzaktan tek komut). Sunucu adı/ID, dizin, giriş kullanıcısı seçenekleri var; OGFS yolu içindeyken bazıları çıkarımla bulunur. `-s` seçeneği kayıtlı OGFS betiğini sunucuya iter. Tırnaklı komutlar yerel komut olarak çalışır.
- **Erişim:** sunucu otomasyonu Client'tan ya da SSH ile (belgede port 2222 görünüyor).
- **Sık hata:** Remote terminal oturumunun OGFS erişimi vermediği; Windows'ta .BAT üretimi.
- **Kaynak:** [Global Shell 10.60](https://docs.microfocus.com/SA/10.60/Content/SA_UG_Server_Automation/global_shell/global_shell.htm); [Logging on to a managed server with rosh 10.60](https://docs.microfocus.com/SA/10.60/Content/SA_UG_Server_Automation/global_shell/LoggingontoaManagedServerWithrosh.htm); [rosh utility 10.60](https://docs.microfocus.com/SA/10.60/Content/SA_UG_Server_Automation/global_shell_utilities/roshUtility.htm); [Running OGFS scripts with rosh 10.50](https://docs.microfocus.com/SA/10.50/Content/SA_UG_Server_Automation/global_shell/RunningOGFSScriptsonManagedServersWithrosh.htm).
- **Doğrulanamadı:** rosh seçeneklerinin tam tablosu (arama parçalıydı; sürüme göre kontrol edilmeli).

### 1.10 API'ler (CLI, SOAP, REST, Pytwist, UAPI)
- **sunucu otomasyonu CLI (sa-cli):** Komut satırından provisioning, yama, audit gibi işler. Platform API'sinden üretildiği belirtiliyor; API'ye eklenen yeni özellikler CLI'a otomatik gelir.
- **SOAP Web Services:** HTTPS üzerinden, WSDL tanımlı. 10.60'ta Java ve Python için hazır stub yok.
- **Pytwist:** 10.60'ta Python istemcileri için SOAP stub yerine kullanılan yol; Core ya da yönetilen sunucularda çalışabiliyor.
- **Java RMI:** Üçüncü seçenek.
- **REST:** Aramada çıkan REST belgeleri HCL BigFix tabanlı sunucu otomasyonu ürününe ait; Micro Focus sunucu otomasyonu REST API'si doğrulanamadı.
- **UAPI:** Hiçbir kaynakta bulunamadı; doğrulanamadı.
- **Kaynak:** [API Unified: supported clients 10.60](https://docs.microfocus.com/SA/10.60/Content/API_Unified/Supported_Clients_1.htm); [Web services 10.60](https://docs.microfocus.com/SA/10.60/Content/API_Unified/web-services_1.htm); [sunucu otomasyonu platform 10.60](https://docs.microfocus.com/SA/10.60/Content/API_Unified/ServerAutomationPlatform.htm); [Components of the server 10.60](https://docs.microfocus.com/SA/10.60/Content/API_Unified/Components_of_the_Server_1.htm).

### 1.11 Core / mesh / satellite / gateway bakımı
- **Core:** Model Repository (Oracle gerektirir), Data Access Engine (XML-RPC arayüzü), Command Engine (Slice paketinde, Python betikleri), Software Repository (paket deposu; mirror özelliği var), Global File System, Command Center.
- **Mesh:** Çoklu Core'daki Model Repository'leri senkronize eder (Multimaster). Bir Core'un yedeği olarak kullanılabilir.
- **Gateway:** Core Gateway / Agent Gateway ajanlarla konuşur; Management Gateway Core'lar ve satellite'lar arası iletişimi yönetir.
- **Satellite:** Uzak siteler için yerel Software Repository Cache ve Satellite Agent Gateway içerir; ağ trafiğini azaltır.
- **Bakım:** Yedekleme, HA kurulumu, sürüm yükseltme (core ve ajanlar birlikte), sertifika yenileme (External PKI'ye geçişte core recertification job).
- **Kaynak:** [Architecture 10.60](https://docs.microfocus.com/SA/10.60/Content/SA_overview/adv_architecture/AdvancedSAArchitecture.htm); [Satellites 10.50](https://docs.microfocus.com/SA/10.50/Content/SA_overview/adv_architecture/SASatellites.htm); [High availability 10.60](https://docs.microfocus.com/SA/10.60/Content/admin_guide/HPSA_High_Availability.htm); [Satellite installation 10.60](https://docs.microfocus.com/SA/10.60/Content/Standard_Install_Guide/SatelliteInstallation1.htm); [sunucu otomasyonu maintenance 10.60](https://docs.microfocus.com/SA/10.60/Content/admin_guide/system_health/SAMaintenance.htm); [10.60 What's new](https://docs.microfocus.com/SA/10.60/Content/Home.htm).

### 1.12 Kullanıcı, grup, yetki (facility, customer)
- **Kavramlar:** Facility, bir sunucu otomasyonu core ya da satellite'in yönettiği tüm sunucular. Customer, facility'lerle ilişkilendirilir; sunucular customer'a yerleştirilir.
- **Yetkiler:** Customer oluşturmak/silmek için Super Administrator yetkisi; customer düzenlemek için Customers Feature yetkisi.
- **Yetki kapsamı:** Sunucu, device group, job, script execution yetkileri ayrı tanımlanır. `aaa shell-perm` yardımcı aracı facility, customer ya da device group'a yetki verir; bu aracı kullanmak için Administrators grubunda olmak gerekir.
- **Kaynak:** [Creating and managing customers 10.50](https://docs.microfocus.com/SA/10.50/Content/SA_UG_Server_Automation/customer_mgmt/AboutCustomers.htm); [aaa syntax 10.60](https://docs.microfocus.com/SA/10.60/Content/SA_UG_Server_Automation/global_shell_utilities/aaaSyntax.htm); [Permissions reference 10.60](https://docs.microfocus.com/SA/10.60/Content/admin_guide/permissions_ref/ServiceAutomationVisualizerPermissions.htm).
- **Doğrulanamadı:** Facility ve customer yetki adımlarının tam sayfası (10.60 için alınamadı; 10.50 özeti kullanıldı).

### 1.13 Raporlama
- **Doğrulanamadı.** Arama sunucu otomasyonu'ya özgü raporlama belgesi döndürmedi. Yalnızca analog (BMC Smart Reporting / Data Warehouse) sayfaları bulundu. sunucu otomasyonu tarafında hangi raporların hazır geldiği, rapor dışa aktarma biçimi (bunun için job log CSV dışa aktarımı var, aşağıda 2. bölüm) için ayrıca bakılmalı.

### 1.14 Sıklık sınıflandırması (belgelerden çıkarım, kesin değil)
- **Günlük:** Run Server Script, Communication Test ve erişilemeyen ajan onarımı, yama taraması, job izleme.
- **Haftalık:** Yama remediation, yazılım politikası uyumluluk taraması, audit.
- **Seyrek:** Provisioning build plan, satellite/gateway/core bakımı, yetki kurgusu, API entegrasyonu, yükseltme.

---

## 2. "N sunucuda script çalıştır ve sonucu topla" akışı (sunucu otomasyonu 10.60)

Kaynak ana sayfa: [Run a server script 10.60](https://docs.microfocus.com/SA/10.60/Content/SA_UG_Server_Automation/script_execution/RunningaServerScriptSavedScriptorAdHocScript.htm). Aşağıdaki adımlar bu sayfadan özetlenmiştir.

1. **Hedef seçimi:** Sunucu ya da sunucu grupları "Include" ile eklenir, "Exclude" ile çıkarılır. Grup için "Server Group Calculation" değeri iki seçenekten biridir: **Now** (seçim anındaki üyeler) ya da **Runtime** (işin çalıştığı andaki üyeler). Runtime için "Allow Run Refresh Jobs" yetkisi gerekir.
2. **Betik:** Kayıtlı betik seçilir ya da ad hoc betik tanımlanır/içe aktarılır.
3. **Çalıştırma kullanıcısı:** UNIX için root, Windows için Local System, ya da Super User; belirli bir kullanıcı için ad ve parola girilir (Windows'ta domain). Birden çok sunucuda eşzamanlı çalıştırma için kimlik bilgisi tüm sunucularda aynı olmalıdır. Super User betikleri ya da "Run Ad hoc & Saved Scripts As Super User" yetkisi kimlik girmeyi gereksiz kılar.
4. **Zaman aşımı:** "Script timeout" dakika cinsinden girilir. Süre dolunca betik durdurulur ve betik hatası sayılır. Değer, betiğin normal süresinden büyük seçilmelidir.
5. **Parametre ve çıktı saklama:** Parametreler girilir. Çıktı "Discard" ya da "Retain" olarak seçilir; saklanacak çıktı boyutu sınırlandırılabilir.
6. **Zamanlama:** Once, Daily, Weekly, Monthly ya da Custom (crontab). Saat dilimi ayarlanır.
7. **Bildirim:** E-posta alıcısı eklenir; "On Success", "On Failure", "On Termination" koşullarından seçilir; isteğe bağlı bilet numarası girilir.
8. **Başlatma ve durum:** İş başlatılır; her sunucunun durumu ve çıkış kodu görülür. **Sıfır çıkış kodu başarı, sıfırdan farklı kod hata** olarak yorumlanır. "Pending Approval" durumunda iş, sunucu otomasyonu dışı bir onay gelene kadar bekler.
9. **Sonuç görüntüleme ve dışa aktarma:** Sunucu bazlı çıktı görülür; "Show output in table" ile tüm sunucular tabloda (ayraç ile sütunlara bölünerek) gösterilir. **Export All Results** ile dışa aktarma: klasörlü ZIP, klasörsüz ZIP, birleştirilmiş ham metin, biçimli metin ya da CSV.
10. **İşi durdurma:** Çalışan iş için "End Job" yeni sunucuya betik göndermez, çalışanların bitmesine izin verir. Zamanlanmış iş "Cancel" ile iptal edilir.

**Eşzamanlılık ve paralellik:** Sunucuyu değiştirmeyen betikler (Change Server = No) `way.server_script.run_read_only_scripts_in_parallel` parametresiyle paralel çalışabilir; agent tarafında `batchbot.max_concurrent_scripts` en fazla eşzamanlı betik sayısını sınırlar. Bu parametrelerin varsayılan değerleri doğrulanamadı.

**Yeniden deneme:** Kaynakta yeniden deneme davranışı yok. sunucu otomasyonu'nın kendisinde otomatik yeniden deneme olduğu görülmedi; harness'in kendisi uygulamalı.

**Kısmi başarısızlık:** Sunucu bazlı durum ve çıkış kodu mevcut. Başarısız sunucuları bir e-posta içinde listeleme seçeneği var (BMC/TrueSight analogu; sunucu otomasyonu'da aynı seçenek doğrulanamadı).

**Job log dışa aktarımı (analog, BMC):** Job log CSV olarak dışa aktarılabilir; "Download Log Package" ile ajan ve Application Server logları paketlenir. Bu, sunucu otomasyonu'da birebir doğrulanamadı. [BMC Managing job logs](https://docs.helixops.ai/bin/Automation-DevSecOps/Server-Automation/TrueSight-Server-Automation/tssa263/Using/Managing-jobs/Managing-job-logs/) (bir mirror sitesi; analog).

**Doğrulanamadı:** Kısmi başarısızlık sonrası "sadece başarısız olanlara yeniden çalıştır" tek adımı sunucu otomasyonu arayüzünde var mı; sunucu otomasyonu'nın kendi e-posta şablonlarının içeriği.

---

## 3. Benzer ürünler (kısa karşılaştırma)

| Ürün | Hedefleme | Çalıştırma modeli | Sonuç toplama | Güçlü yan | Zayıf yan |
|---|---|---|---|---|---|
| **sunucu otomasyonu (OpenText/Micro Focus)** | Server/device group, customer ve facility kapsamı, Now/Runtime | Ajanlı (Server Agent, MID tabanlı) | Sunucu bazlı durum ve çıkış kodu; CSV/ZIP dışa aktarma; e-posta bildirimi | Yama, audit/snapshot, provisioning ve betik tek ürün içinde; onay akışı | Ağır kurulum (Oracle, Core); eğitim eğrisi; API yüzeyinin dağınıklığı |
| **BMC TrueSight / BladeLogic (analog)** | Device group, job | Ajanlı (RSCD) | Job log CSV, log paketi | sunucu otomasyonu ile aynı soy; yama ve compliance | Bu metinde yalnızca analog; yorumlar BladeLogic/TrueSight kullanıcılarından |
| **Red Hat Ansible / AWX** | Inventory ve `limit` (örn. `grup1:&grup2`, dışlama) | Ajansız (SSH/WinRM) | Job çıktısı ve API; yapılandırılmış sonuç | Açık kaynak tabanlı; ajan gerektirmez | Workflow'da limit değişkenlerle çalışmıyor (RFE); yama ve provisioning için ek bileşen gerekir |
| **Puppet Enterprise + Bolt** | Node listesi (örn. `winrm://` öneki) | Bolt ajansız (SSH/WinRM); PE ajanlı | `--format json`; komut sonucu exit code ve çıktı | Bolt ajansız ve JSON çıktı net | Ana belgeler bulunamadı; çoğu örnek üçüncü taraf bloğu; PE tarafı doğrulanamadı |
| **Chef (Agentless / Target Mode)** | Hedef adları, `chef-client -t` | Ajansız, Linux ağırlıklı | Chef run çıktısı | Ajansız çalışır | Yalnızca Linux hedefleri; zamanlama için cron gerekir |
| **SaltStack (salt-ssh)** | Salt hedefleme ifadeleri | Ajansız (SSH+Python) | Salt çıktısı | Hafif kurulum | Ajanlı modelden sonra eklenmiş; ölçek belgesi doğrulanamadı |
| **Rundeck / PagerDuty Process Automation** | Node filter (örn. `instanceId:...`) | Ajansız (SSH/WinRM) ve runner | Job çıktısı, API | Runbook ve olay entegrasyonu güçlü | Node filter ile job ayarında kayıp riski (tek kullanıcı raporu, 5.11.1) |
| **HCL BigFix** | Fixlet relevance ile hedefleme; Automation Plan | Ajanlı (BigFix ajanı) | Action sonucu, "Fixed/Failed/Not Relevant" durumları | Patch ve uyumluluk; geniş hedefleme | Durum raporlama tuhaflıkları (forum raporu: Failed görünen ama tüm satırlar Completed); karmaşık relevance |
| **Tanium** | Soru (question) tabanlı hedefleme; action group | Ajanlı, çok hızlı | Soru sonuçları, action durumu | Hızlı, ölçekli sorgulama | Action group izinleri ve yetki modeli ayrıca yönetilmeli; resmi belge sınırlı bulundu |
| **Microsoft SCCM / MECM** | Koleksiyonlar | Ajanlı | MECM raporları | Windows için derin entegrasyon; OS dağıtımı | Linux desteği kesildi (satıcı karşılaştırmasına göre 2019); ağır, on-prem |
| **Microsoft Intune** | Cihaz grupları | Bulut/MDM | Intune raporları | Bulut tabanlı | Windows Server yamalarını desteklemiyor; Linux yama desteği yok (satıcı karşılaştırması) |
| **AWS Systems Manager Run Command** | Tag tabanlı (`targets`), kaynak bazlı | Ajanlı (SSM agent) | S3 ve CloudWatch Logs'a çıktı | `--max-concurrency` ve `--max-errors` ile hız kontrolü; alarm ile durdurma | Yalnızca AWS yönetilen düğümler; on-prem için ek kurulum |

Notlar:
- Tablodaki tüm satırlar kaynakla doğrudur; ancak Puppet, Chef ve Salt satırlarının ayrıntısı arama özetlerine dayanır ve tam doğrulanmadı.
- Rakiplerin "güçlü/zayıf" yorumları çoğunlukla satıcı karşılaştırmaları ve üçüncü taraf bloglardan geldi; bağımsız bir ölçüt değildir.

Kaynaklar:
- [Ansible AWX inventories (mintlify)](https://www.mintlify.com/ansible/awx/guides/managing-inventories)
- [AAPRFE-2474](https://issues.redhat.com/browse/AAPRFE-2474)
- [Puppet Bolt JSON output](https://puppet.com/docs/bolt/latest/json_output_reference)
- [Puppet Bolt cmdlet reference](https://puppet.com/docs/bolt/latest/bolt_cmdlet_reference)
- [Chef Agentless](https://docs.chef.io/client/19/features/agentless/)
- [Salt SSH](https://docs.saltproject.io/en/getstarted/ssh/)
- [PagerDuty Automation Actions](https://support.pagerduty.com/docs/rundeck-actions)
- [Rundeck node filter örneği](https://docs.rundeck.com/docs/learning/howto/events-with-rba.html)
- [BigFix Automation Plan](https://help.hcl-software.com/bigfix/11.0/lifecycle/Lifecycle/ServerAutomation/SAUsersGuide/Server_Automation_plan/sa_createplan.html)
- [BigFix Fixlet ve Task](https://help.hcl-software.com/bigfix/9.5/platform/Platform/Console/c_introducing_fixlets_and_tasks.html)
- [Tanium developer: deploy actions](https://developer.tanium.com/site/global/docs/how_tos/deploy_actions/index.gsp)
- [AWS Run Command: targets ve rate control](https://docs.aws.amazon.com/systems-manager/latest/userguide/send-commands-multiple.html)
- [Intune ve SCCM karşılaştırması (Recast)](https://www.recastsoftware.com/?p=684518) ve [Automox karşılaştırma (vendor)](https://www.automox.com/blog/automated-patching-solutions-compared-2026)

---

## 4. Zayıflıklar ve "yapay zekâ çağında güdük kalma" tezi

### 4.1 Doğrulanan zayıflıklar
- **Kurulum ağırlığı:** sunucu otomasyonu 10.60 belgesi Model Repository için Oracle veritabanı gerektirdiğini söylüyor. Dağıtık kurulumların HPE Professional Services ya da sertifikalı danışman gerektirdiği ve müşteri tarafından desteklenmediği belirtiliyor. [Architecture 10.60](https://docs.microfocus.com/SA/10.60/Content/SA_overview/adv_architecture/AdvancedSAArchitecture.htm). Bu, küçük bir harness deneme kurulumu için ciddi bir engel.
- **Donanım:** Oracle sunucusu için aramada 32 GB RAM ve 12 CPU önerisi geçti; Core kökünde en az 72 GB boş disk. Kaynak: [Oracle system requirements 10.60](https://docs.microfocus.com/SA/10.60/Content/Standard_Install_Guide/SystemRequirements.htm) ve [Free disk space 10.60](https://docs.microfocus.com/SA/10.60/Content/Standard_Install_Guide/7ChecktheFreeDiskSpaceRequirements.htm). Arama özetinde kesin rakamlar tam görünmedi; doğrulanmalı.
- **Ağır API karmaşası:** SOAP, Pytwist, Java RMI ve CLI birlikte var. 10.60'ta Java ve Python stub'ları yok. Bu, LLM ajanına "tek bir API" öğretmeyi zorlaştırır. [Supported clients 10.60](https://docs.microfocus.com/SA/10.60/Content/API_Unified/Supported_Clients_1.htm).
- **Eğitim eğrisi:** Kullanıcı yorumlarında (BladeLogic/TrueSight, analog) betik deneyimi gerektiren bir öğrenme eğrisi ve yetersiz belge şikâyeti geçiyor. sunucu otomasyonu'ya özgü değil. [Capterra TrueSight Automation for Servers reviews](https://www.capterra.com/p/149668/BladeLogic-Server-Automation/reviews/).

### 4.2 Doğrulanamayan iddialar
- **Eski arayüz:** Belgeler arayüz modernliğine dair bir şey söylemiyor; "eski" nitelemesi kaynakla desteklenmiyor.
- **Pazar payı:** Bağımsız pazar payı verisi bulunamadı.
- **Yol haritası ve ömür:** sunucu otomasyonu'ya özgü end-of-life ya da yol haritası belgesi bulunamadı. OpenText ürün yaşam döngüsü sayfası dinamik yüklendiği için içeriği alınamadı. Micro Focus'un OpenText'e geçişi ve AMC'nin Rocket Software'e satışı gibi kurumsal değişiklikler var ama sunucu otomasyonu'yı doğrudan etkilediği görülmedi. [OpenText lifecycle](https://www.opentext.com/lifecycle).
- **Kullanıcı şikâyetleri (sunucu otomasyonu'ya özgü):** PeerSpot, G2 ve Gartner Peer Insights'ta sunucu otomasyonu'ya özgü yorum sayfası bulunamadı. Bulunanlar BMC/TrueSight ve HPE sistem yönetimi ürünleri içindi; bu nedenle yorum tabanlı bir sonuç çıkarılamaz.

### 4.3 Tezi çürüten veya zayıflatan bulgular (sunucu otomasyonu'nın hâlâ değerli olduğu alanlar)
- **Denetim izi:** Command Engine çağrıları güvenli iletilir ve Model Repository'de denetlenebilir (10.60 mimari sayfası). Harness için bu, "kim neyi hangi sunucuda ne zaman yaptı" sorusuna yerleşik bir cevap sağlar.
- **Yetki ayrımı:** Customer, facility, device group ve job/script yetkileri ayrı tanımlanır; Super User ve "Run Ad hoc & Saved Scripts As Super User" gibi yetki sınıfları var. Bu, LLM ajanının yetki sınırlarını ürünün kendisinden alabileceği anlamına gelir.
- **Onay akışı:** İş "Pending Approval" durumuna alınabilir; sunucu otomasyonu dışındaki bir süreç onaylayana kadar bloke kalır. Bu, insan onay kapısı için doğal bir nokta.
- **Ölçek ve dayanıklılık:** Multimaster Mesh, satellite ve HA dokümanları var; Slice ile yatay ölçekleme; Software Repository mirror'ı. Düzenli, çok sunuculu ortamlar için tasarlanmış.
- **Uyum ve yama:** Snapshot/audit/remediate döngüsü ve policy-based yama ile uyumluluk raporu üretme yeteneği (10.60). Ajansız araçlarda bu tür derin uyum kontrolü yaygın değil.
- **Kimlik ve güvenlik:** External PKI desteği ve AutoPass entegrasyonu (10.60 yenilikleri).

### 4.4 Sonuç
Kaynaklar "sunucu otomasyonu güdük" tezini doğrulamıyor, ancak çürütmüyor da. Belgelerde yeniden tasarım ya da yeni bir AI yüzeyi görülmedi; API'lerin çeşitliliği ve kurulum ağırlığı gerçek. Buna karşılık yama, audit/remediate, yetki ve denetim izi gibi özellikler hâlâ değerli. Dolayısıyla harness'in doğru tezi: "sunucu otomasyonu'nın kurumsal güven özelliklerini kullan, ama eğitim ve betik üretimini LLM'e bırak."

---

## 5. Deneme kurulumu

- **Deneme sürümü:** Doğrulanamadı. sunucu otomasyonu'ya özgü bir trial ya da değerlendirme indirme sayfası bulunamadı. Marketplace'te bir "capsule" (vCenter entegrasyonu) var; bu bir sunucu otomasyonu ürünü değil, eklenti. [Marketplace capsule](https://marketplace.opentext.com/itom/content/capsule-vmware-vcenter-with-server-automation). Mantıklı yol: OpenText satış ya da hesap temsilcisine başvurmak.
- **Sistem gereksinimi:** Core için kesin RAM/CPU sayısı bulunamadı; Oracle için 32 GB RAM ve 12 CPU önerisi var (arama özeti). Disk: Core kökünde 72 GB boş alan. Desteklenen işletim sistemleri 10.60 Support and Compatibility Matrix'te (HPE destek sitesi) ve sürümler arası değişiyor. [10.60 What's new](https://docs.microfocus.com/SA/10.60/Content/Release_Notes/whats_new.htm) bazı OS'lerin (Windows Server 2016, RHEL 6/7 HPC, SLES 12 s390x, ESXi 6.5, AIX 7.2, Ubuntu 16.04) 10.60'ta desteğinin düştüğünü söylüyor.
- **Docker/konteyner:** Doğrulanamadı. Kaynaklar konteyner kurulumunu desteklediğini ya da desteklemediğini söylemiyor. Core'un ağır bileşenler ve Oracle içermesi nedeniyle tam konteynerleştirme pratik olmayabilir; bu bir çıkarım, kaynak yok.
- **Hazır sanal makine imajı:** Doğrulanamadı. Yalnızca "HP sunucu otomasyonu Virtual Appliance" başlığı bir arama sonucunda görüldü, indirme bilgisi yok.
- **Sonuç:** Yerelde küçük bir deneme için gerçekçi yol bulunamadı; kurumsal bir sürüm ya da değerlendirme lisansı gerekebilir.

---

## Harness için çıkarımlar

1. Hedef çözümlemesinde "Now" ve "Runtime" seçeneklerini açıkça kaydet ve iş başlamadan kullanıcıya göster; grup üyeliği kayabilir.
2. Çalıştırma kimliği için root, Local System, Super User ya da adlandırılmış kullanıcı seçeneklerini ayrı bir politika olarak modelle; kimlik bilgisi loglara ve prompt'a girmesin.
3. Her iş için zaman aşımını zorunlu parametre yap (dakika); zaman aşımı sunucu otomasyonu'da betik hatası sayılır.
4. Sunucu bazlı sonucu tek bir şemaya normalleştir: sıfır çıkış kodu başarı, sıfırdan farklı hata; "Cancelled" ve "Succeeded" durumlarını ayrı tut.
5. Yeniden deneme mantığını harness'te yaz (sunucu otomasyonu'da kaynakta yok); yalnızca başarısız sunucular için yeniden çalıştır ve idempotency'yi betik tarafında doğrula.
6. Kısmi başarısızlıkta tam listeyi (başarılı/başarısız/zaman aşımı) üret; e-posta bildirimi yerine yapılandırılmış rapor tercih et.
7. Çıktı toplamada "Retain" boyut sınırını ve CSV/ZIP dışa aktarımını kullan; büyük çıktı kesilmesini ölç ve kaydet.
8. Onay kapısını ürünün "Pending Approval" durumuyla hizala; yıkıcı işler (remediate, delete, end job) için insan onayı zorunlu olsun.
9. Yetki sınırlarını sunucu otomasyonu'nın customer, facility, device group ve Super User modelinden al; ajanın yetkisi en az ayrıcalıkla sınırlı olsun.
10. Her iş öncesinde Communication Test (Agent-DAE, Agent-SWR, CE-AGT, MID) çalıştır; başarısız sunucuyu hedef kümeden çıkar ve ajanı onarmak için ayrı bir iş aç.
11. Yama ve yazılım politikalarını önce test sunucusunda dene; politika değişikliğinin uyumsuzluk yaratacağını ve yeniden tarama gerektireceğini harness'in planına koy.
12. Audit ve snapshot karşılaştırmasını yeniden icat etme; sunucu otomasyonu'nın golden-server ve audit döngüsünü kullan, harness yalnızca sonucu yorumlasın ve ilişkilendirsin.
13. Kendi denetim izini tut: her sunucu otomasyonu job ID'si, kim tarafından, hangi hedefle, hangi kimlik türüyle başlatıldı; sunucu otomasyonu'nın Command Engine denetimine ek olarak.
14. sunucu otomasyonu sürüm farkını (10.50, 10.51, 10.60) çalışma zamanında tespit et; API çağrıları ve komut sözdizimi sürüme göre değişiyor.
15. API yüzeyini tek bir adaptör katmanında soyutla (CLI, pytwist veya SOAP); LLM'e doğrudan ham API vermek yerine sınırlı, şemalı araçlar sun. Global Shell (rosh) komutlarını da şablonla sınırla, serbest kabuk erişimi verme.

---

Doğrulanamayan konular özeti: UAPI, sunucu otomasyonu REST API'si, Docker kurulumu, trial indirme, hazır VM imajı, rosh seçeneklerinin tam tablosu, facility/customer yetki adımlarının 10.60 sürümü, sunucu otomasyonu raporlama, sunucu otomasyonu'ya özgü kullanıcı yorumları ve sunucu otomasyonu'nın yol haritası/ömrü.
