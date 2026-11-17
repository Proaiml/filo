# OpenText akış otomasyonu (akış otomasyonu) ve Runbook / BT Süreç Otomasyonu Araştırması

Tarih: 2026-11-17. Bu rapor web araması ve belge sayfalarının okunmasıyla hazırlandı. Kaynağı bulunamayan veya doğrulanamayan her madde "doğrulanamadı" olarak işaretlendi.

## Önemli sınırlamalar

- Resmi akış otomasyonu 10.x belge portalı (docs.microfocus.com/doc/akış otomasyonu/...) WebFetch ile açıldığında yalnızca başlık döndü. akış otomasyonu 10.x'in Central, RAS, Studio ve REST API ayrıntıları için çoğu kaynak ya da CSA (Cloud Service Automation) 4.80–4.91 belgeleri oldu. CSA'da akış otomasyonu gömülü bir bileşen olarak geçer; bu yüzden akış otomasyonu Designer ile ilgili bulgular CSA sürümlerinden gelir ve akış otomasyonu 10.x'e birebir uymayabilir.
- akış otomasyonu'ya özgü arama sonuçları zayıftı. Yönetici kılavuzundaki "run explorer", "group alias", "schedule", "purge", LDAP/SAML, sertifika ve yükseltme ayrıntıları için doğrulanabilir kaynak bulunamadı; bu başlıklar aşağıda ilgili bölümde "doğrulanamadı" olarak işaretlidir.
- Kaynak kodu ya da çalışan bir akış otomasyonu örneği incelenmedi.

## 1. akış otomasyonu mimarisi ve kavramları

**Bileşenler (kaynaklı):**
- **akış otomasyonu Central**: Akışların yönetildiği, çalıştırıldığı ve raporlandığı çalışma zamanı ortamı. Akışlar akış otomasyonu Designer'da yazılır, Central'da çalışır. Kaynak: https://docs.microfocus.com/CSA/4.90/Content/OO_Designer/Intro.htm
- **akış otomasyonu Designer**: Tarayıcı tabanlı akış yazma aracı; Windows/Linux'ta bağımsız ürün olarak ve CSA arayüzüne gömülü olarak gelir. Aynı kaynak.
- **akış otomasyonu Desktop Studio**: Ayrı, kurulan bir yazma aracı. Designer ile Studio arasında akışlar birbirini okuyamaz ve düzenleyemez. Kaynak: https://docs.microfocus.com/CSA/4.90/Content/OO_Designer/Intro.htm
- **RAS (Remote Action Server)**: akış otomasyonu Central'ın uzak yürütme için kullandığı RAS URL'si (`RAS_Operator_Path`, örnek: `https://<FQDN>:9004/RAS/services/RCAgentService`). Kaynak: https://docs.microfocus.com/CSA/4.80/Content/Installation_and_Configuration/Configuration_Guide/HPOOSettings_Configure_mng.htm
- RAS'ın Studio ile aynı sistemde çalışması gerektiği; yapılmazsa akışların kırmızıya dönebileceği ve "cryptic" hatalar üretebileceği belirtiliyor. localhost yerine FQDN veya IP kullanılmalı. Kaynak: aynı sayfa ve https://docs.microfocus.com/CSA/4.81/Content/Installation_and_Configuration/Configuration_Guide/HPOOSettings_Configure_mng.htm (arama özeti)
- Studio'nun ayrı bir makinede çalıştırılmasının hata ve kırmızı akışlara yol açtığı CSA 4.91 notunda geçiyor (arama özeti). Kaynak: https://docs.microfocus.com/CSA/4.91/Content/Installation_and_Configuration/Configuration_Guide/HPOOSettings_Configure_mng.htm

**Kavramlar (kaynaklı):**
- **Flow (akış)**: CloudSlang dilinde yazılan, adım zincirinden oluşan iş akışı. Kaynak: https://docs.microfocus.com/CSA/4.90/Content/OO_Designer/Intro.htm
- **Operation (işlem)**: Belirli bir eylemin girdi, çıktı, yanıt ve özelliklerini tanımlar. Akışa adım olarak yerleştirilebilir. Kaynak: aynı sayfa.
- **Step (adım)**: Bir operation, decision veya flow'un akıştaki örneği. Adımı düzenlemek orijinali değiştirmez. Girdiler bir önceki adımın çıktısından ya da akış başlarken girilerek gelebilir. Kaynak: aynı sayfa ve https://docs.microfocus.com/CSA/4.90/Content/OO_Designer/Step_inputs_outputs.htm (arama özeti)
- **Transition (geçiş) / navigation line**: Adımlar arasındaki bağlantılar. Decision adımları yalnızca bir sonraki adımı hesaplar ve Designer'da salt okunurdur (arama özeti). Başarı ve hata yollarının tam davranışı Navigation sayfasında açıklanmıyor: "doğrulanamadı" (ayrıntı için CloudSlang DSL referansı gerekir: https://cloudslang-docs.readthedocs.io/en/v1.0/cloudslang_dsl_reference.html).
- **Flow input/output ve results**: Akış Properties panelinde tanımlanır; Results sekmesinde sonuçlar ve açıklamaları düzenlenir. Kaynak: https://docs.microfocus.com/CSA/4.90/Content/OO_Designer/Navigation.htm
- **Content pack (içerik paketi)**: Operation, flow, action (Java veya .NET tabanlı), yerelleştirme verisi ve konfigürasyon öğelerini içeren dosya. Designer'da ya da Studio'da üretilir, akış otomasyonu Central'a dağıtılır ve veritabanında saklanır. Kaynak: aynı Intro sayfası.
- **System account (sistem hesabı)**: CSA'da `CSA_REST_CREDENTIALS` gibi sistem hesapları tanımlanır; kullanıcı adının ilgili sistem özelliğiyle (`CSA_OO_USER`) eşleşmesi gerekir. Kaynak: https://docs.microfocus.com/CSA/4.80/Content/Installation_and_Configuration/Configuration_Guide/HPOOSettings_Configure_mng.htm
- **System property (sistem özelliği)**: `CSA_REST_URI`, `CSA_OO_USER` gibi özellikler; akış otomasyonu 9.07'de "Property Value", akış otomasyonu 10.50'de "Override Value" alanından yönetiliyor. Aynı kaynak.
- **Group alias, schedule, run explorer, AFL**: "doğrulanamadı" işaretli. Not: Marketplace'teki "akış otomasyonu OpenText Solutions Content Pack (AFL)" adı, AFL'nin ne anlama geldiğini açıklamıyor (https://marketplace.opentext.com/itom/content/oo-opentext-solutions-content-pack-afl).
- **Validation (doğrulama)**: Designer akış, operation ve sistem özelliklerindeki hataları işaretler; eksik bağımlılıkları ve bozuk YAML'ı da gösterir. Doğrulanmamış (geçersiz) içerik content pack'e aktarılmaz; uyarılar yalnızca bilgilendirir. Kaynak: https://docs.microfocus.com/CSA/4.90/Content/OO_Designer/validating_flows.htm
- **CloudSlang**: YAML 1.2 tabanlı akış dili. Akış dosyaları `.sl`, `.sl.yaml` veya `.sl.yml` uzantılıdır. Operation içindeki action Python veya Java ile yazılabilir. Kaynak: https://cloudslang-docs.readthedocs.io/en/v1.0/cloudslang_dsl_reference.html ve Designer Intro sayfası.
- **REST API (/oo/rest/...)**: Kaynak olarak Kestra akış otomasyonu eklentisi kullanıldı (üçüncü taraf): Classic modu REST v2 ve HTTP Basic Auth; Containerized modu REST v1 ve tenant ID + X-Auth-Token. Kaynak: https://kestra.io/plugins/plugin-ee-hpoo. Resmi `/oo/rest/v2/executions` uç noktası ve parametreleri **doğrulanamadı**; resmi belge sayfasına ulaşılamadı. Operasyonlar (üçüncü taraftan): flow çalıştırma (UUID ile, opsiyonel polling), execution özeti alma, listeleme (filtreler: akış yolu, durum, sahip, başlangıç zamanı), duraklatma, devam ettirme, iptal.
- **sunucu otomasyonu entegrasyonu**: CSA (sunucu otomasyonu / Cloud Service Automation) ile akış otomasyonu entegrasyonu, CSA sistem özellikleri ve REST kimlik bilgileriyle yapılır (yukarıdaki kaynaklar). sunucu otomasyonu'ın akış otomasyonu ile ilişkisi, Automation Center sayfasında yer alıyor: https://www.opentext.com/products/automation-center (arama özeti). Genel sunucu otomasyonu content pack ayrıntıları doğrulanamadı.

**Yardımcı content pack örnekleri (topluluk tarafından):**
- Community General Utilities (sürüm 1.5.0, 29 Mart 2018): Export Reports Data (akış otomasyonu 10.x Central verisini CSV olarak dışa aktarır), Central Usage Monitor, Single Worker (HA kurulumda bir alias üzerinden tek ve garanti erişilebilir worker'a yönlendirme), SVN Manager. Destek yalnızca topluluk forumlarından; OpenText Software Support kapsamında değil. Desteklenen sürümler 10.20–10.80. Kaynak: https://marketplace.opentext.com/itom/content/community-general-utilities

## 2. Adminlik ve geliştirme iş kataloğu

Aşağıdaki iş kalemleri, yukarıdaki kaynaklardaki bileşenlere göre tanımlanmıştır. Frekans ve sıklık tahmini genel uygulama pratiğidir, kaynakla doğrulanmadı.

| İş | Girdi | Tipik adımlar | Çıktı | Sık hata biçimleri |
|---|---|---|---|---|
| İçerik paketi dağıtımı | Paket dosyası (JAR), hedef sürüm | Designer'da doğrulama, paket indirme, Central'a yükleme, dağıtım sonrası çalıştırma testi | Paket dağıtılmış, akışlar listede | Geçersiz akış paketlenmez; uyarılar gözden kaçar (Designer doğrulama kaynağı). Bağımlı paket sırası yanlış (CSA kılavuzu: önce temel paketler) |
| Sürüm yükseltme | Yeni akış otomasyonu sürümü, mevcut içerik | Yedek alma, ayarları yeniden girme (Override Value), RAS/Central durdurma, yükseltme, RAS artifact cache temizleme | Yeni sürüm çalışır | Sürüm bazlı alan adı değişiklikleri (Property Value → Override Value). RAS artifact cache kalıntısı (CSA 4.9 kılavuzu) |
| Flow yazma | Gereksinim, operasyonlar | Designer'da akış oluşturma, girdi/çıktı tanımlama, adım bağlama, doğrulama, dışa aktarma | Content pack | Studio ve Designer akışları arasında uyumsuzluk; decision ve geçiş mantığı tanımsız dallar; geçersiz YAML |
| Hata ayıklama | Başarısız koşu kimliği | Debugger'da Run Tree açma, Context Inspector ile düğüm bağlamını okuma | Hatanın adımı ve bağlamı | Kırmızı akış, ortam/RAS konumu hatası; localhost kullanımı (kaynak: ayarlar sayfası) |
| Tetikleme ve zamanlama | Akış UUID, girdiler | REST ile çalıştırma (Classic v2 / Containerized v1), veya zamanlayıcı (doğrulanamadı) | Execution kimliği | Yanlış kimlik doğrulama modu; girdi eksikliği |
| Duraklamış/başarısız koşuları sürdürme | Execution kimliği, branch kimliği, girdi | REST ile listeleme, durum okuma, devam ettirme (resume) ya da iptal (cancel) | Koşu tamamlanır ya da iptal edilir | Input-required duraklamada girdi bağlamalarının eksik olması (Kestra eklentisi kaynağı) |
| Sistem hesabı ve kimlik bilgisi yönetimi | Hesap adı, şifre | Sistem hesabını oluşturma, sistem özelliğiyle eşleştirme, test | Hesap çalışır | Kullanıcı adı eşleşmesi bozulursa CSA çağrıları kırılır (kaynak: ayarlar sayfası). Varsayılan parolalar değiştirilmez (CSA kılavuzunda varsayılan şifre örneği var; güvenlik açısından değiştirilmeli) |
| RAS ve worker grup yönetimi | RAS sunucusu, FQDN | RAS'ı Studio ile aynı sunucuda kurma, operatör yolunu ayarlama, artifact cache temizleme | Akışlar yeşil | localhost kullanımı; Studio ayrı makinedeyken kırmızı akış. Worker grup kurulumu: doğrulanamadı |
| Yetki yönetimi (rol, içerik izinleri) | Kullanıcı/grup | Rol atama, içerik izni verme | Erişim | Doğrulanamadı; benzer ürünlerde grup izinleri yalnızca çalıştırma (Run) izni içerebiliyor (VMware Aria kaynağı) |
| Veritabanı temizliği (purge) | Saklama süresi, koşu kriteri | Doğrulanamadı | Doğrulanamadı | Doğrulanamadı |
| Sertifika, LDAP/SAML | Sertifika, IdP bilgisi | Doğrulanamadı | Doğrulanamadı | Doğrulanamadı |
| ITSM (ServiceNow, SM) entegrasyonu | Bilet bilgisi, API kimliği | Doğrulanamadı (ITSM content pack'leri mevcut olabilir; bu araştırma onları doğrulamadı) | Doğrulanamadı | Doğrulanamadı |
| E-posta, SSH, PowerShell/WinRM, REST, veritabanı operasyonları | Hedef, kimlik, komut | Operations ve içerik paketleri üzerinden çağrı (Community General Utilities ve OpenText Solutions AFL paketlerinde ilgili operasyonlar olduğu belirtiliyor) | Çıktı değişkenleri | Kimlik doğrulama reddi, zaman aşımı, RAS erişim sorunları. Ayrıntılı operasyon listesi doğrulanamadı |

**Kaynaklar:** https://docs.microfocus.com/CSA/4.80/Content/Installation_and_Configuration/Configuration_Guide/HPOOSettings_Configure_mng.htm ; https://docs.microfocus.com/CSA/4.90/Content/OO_Designer/validating_flows.htm ; https://marketplace.opentext.com/itom/content/community-general-utilities ; https://marketplace.opentext.com/itom/content/oo-opentext-solutions-content-pack-afl

## 3. Tipik akış örnekleri

Aşağıdaki akışlar, akış otomasyonu'nun kullanıldığı genel BT operasyonu senaryolarıdır. Adım zincirleri tasarım önerisidir; belirli bir akış otomasyonu örneğinden alınmamıştır, bu nedenle "kaynak" yerine "tasarım" olarak işaretlenmiştir. Kırılma noktaları genel pratik ve yukarıda belirtilen akış otomasyonu davranışlarına (doğrulama, RAS konumu, sistem hesabı eşleşmesi) dayanır.

1. **Sunucu teslim (provisioning sonrası standart kurulum)**: Sunucu bilgisi → ağ/DNS kontrolü → ajan kurulumu → yapılandırma → güvenlik sertleştirme → izleme kaydı → CMDB güncelleme. Kırılma: ajan kurulumu sırasında hedefin erişilemez olması; sonraki adımların çıktısına bağımlılık.
2. **Disk doluluk müdahalesi**: Uyarı → disk kullanımı okuma → eşik kontrolü → geçici dosya temizliği (yalnızca tanımlı dizinler) → yeniden ölçüm → bilet kapatma. Kırılma: temizlik sonrası kullanım eşiğin altına inmez; dal kurmak gerekir.
3. **Servis yeniden başlatma**: Servis durumu → bağımlılık kontrolü → durdurma → bekleme → başlatma → sağlık ölçümü. Kırılma: servis durdurulamaz, sağlık kontrolü zaman aşımına uğrar; geri dönüş (rollback) adımı yoksa ortam yarım kalır.
4. **Kullanıcı açma/kapatma**: Talep → dizin kontrolü → hesap oluşturma/devre dışı bırakma → grup ataması → e-posta bildirimi. Kırılma: hesap zaten var/yok; yetki yetersizliği; kapatmada bağlı kaynakların devri.
5. **Yama öncesi kontrol**: Envanter → servis yedeği → disk alanı → bekleyen yeniden başlatma kontrolü → sağlık ölçümü → rapor. Kırılma: yama sonrası karşılaştırma için önceki durumun kaydı yoksa.
6. **Yama sonrası doğrulama**: Yama sürümü → servis sağlığı → uygulama testi → sürüm raporu → geri alma kararı. Kırılma: sağlık metriklerinde yanlış pozitif; insan onayı olmadan geri alma.
7. **Toplu script çalıştırma ve rapor e-postası**: Hedef listesi (örn. "PA" önekli sunucular) → RAS üzerinden script → sonuçları toplama → XML/CSV üretme → e-posta. Kırılma: hedeflerin bir kısmında bağlantı hatası; kısmi başarıda akışın nasıl devam edeceği tanımsız kalırsa tüm rapor yanlış olabilir.
8. **Olay (incident) zenginleştirme**: Bilet alma → CI tanımlama → sahip ve servis bilgisi → son değişiklikler → ilgili uyarılar → biletin notlarına yazma. Kırılma: CMDB'de kayıt yoksa ya da birden çok eşleşme varsa.
9. **Sertifika süresi kontrolü**: Sunucu listesi → uç nokta TLS okuma → kalan süre → eşik altı uyarısı → yenileme talebi bileti. Kırılma: erişilemeyen sunucular; özel CA'lar.
10. **Veritabanı yedek kontrolü**: Yedek zamanı → boyut → geri yükleme testi (sandbox) → sonuç raporu. Kırılma: yedek alanı dolu; test ortamı yoksa adım atlanır.
11. **Log toplama ve arşivleme**: Kaynak listesi → log dosyası boyutu → sıkıştırma → arşiv → eski kayıtları silme (onaylı). Kırılma: silme adımı geri alınamaz; onay kapısı şart.
12. **Güvenlik grubu / firewall kuralı talebi**: Talep → kural doğrulama → değişiklik onayı → uygulama → ping/port testi → geri alma tanımı. Kırılma: onay eksik ya da test başarısız olursa kuralın geri alınması gerekir.
13. **Konfigürasyon sapması (drift) onarımı**: Referans değer → mevcut değer → fark → düzeltme (onaylı) → doğrulama. Kırılma: referans değer güncel değilse toplu düzeltme yanlış ortamı değiştirir.
14. **Ortam kopyalama (test/prod eşitleme)**: Kaynak durum → veri maskeleme → hedef temizleme (onaylı) → kopyalama → doğrulama. Kırılma: maskeleme eksikliği; hedef temizlemesi geri alınamaz.
15. **Acil durum (on-call) runbook'u**: Uyarı → zenginleştirme → öneri (ilgili runbook) → insan onayı → yürütme → sonuç kaydı → bilet güncelleme. Kırılma: onay gecikmesi; yürütme sonrası kanıt zinciri.

## 4. Benzer ürünler ve kısa karşılaştırma

Kaynak notları: aşağıdaki karşılaştırma yalnızca yukarıdaki aramalardan ve belge özetlerinden çıkarılmıştır. Her ürün için tam özellik matrisi çıkarılmadı; "doğrulanamadı" işaretleri bunu gösterir.

- **akış otomasyonu (OpenText)**: Akış dili CloudSlang (YAML tabanlı, `.sl`). Hata modeli: adım yönlendirmesi, decision ve başarı/hata yolları; ayrıntısı doğrulanamadı. İnsan onayı: yerleşik onay adımı doğrulanamadı. Güçlü yan: kurumsal tecrübe, Designer/Central ayrımı, content pack dağıtımı, RAS ile uzak yürütme. Zayıf yan: Studio/Designer uyumsuzluğu, RAS yerleşimi kısıtı, topluluk dışı destek sınırlı.
- **Rundeck / PagerDuty Process Automation**: İş tanımları ve iş seçenekleri (Job Options; metin, tarih, gizli giriş türleri). Koşullu adımlar için ruleset workflow strategy. PagerDuty entegrasyon adımları olay notu, tetikleme, onaylama ve çözme işlemlerini kapsar. Onay adımı için resmi bir yerleşik özellik bulunamadı; bir Google Doc önerisinde kullanıcı girdi adımı yer alıyor ama uygulanmış sayılamaz. İnsan onayı: PagerDuty sayfası, yıkıcı işlemler için onay kapısı önerir (arama özeti). Kaynaklar: https://docs.rundeck.com/docs/learning/getting-started/jobs/job-options.html ; https://docs.rundeck.com/docs/manual/jobs/workflow-strategies/ruleset.html ; https://docs.rundeck.com/docs/manual/workflow-steps/pagerduty.html
- **StackStorm**: Sensör (olay izleyen Python eklentisi) → kural (trigger → action/workflow eşleştirme) → action/workflow. Her kuralda yalnızca bir action bölümü olabilir; birden çok action için workflow ya da birden çok kural gerekir. Orquesta workflow motoru (sıralı, fork, join, veri dönüşümü). Resmi belge: yeni workflow'ların Orquesta ile yazılması öneriliyor, Mistral desteği sonlanmış. Kaynak: https://docs.stackstorm.com/workflows.html ; https://st2docs.readthedocs.io/en/stable/rules.html ; https://st2docs.readthedocs.io/en/stable/orquesta/development/index.html. Güçlü yan: olay odaklı otomasyon. Zayıf yan: YAML ve Python bilgisi gerektirir.
- **Ansible Automation Platform + Event-Driven Ansible (EDA)**: Olay kaynağı → kural kitabı (rulebook) koşulları → playbook. Red Hat Lightspeed tarafında AI, öneri üretir; onaylı playbook çalışır. Aynı RBAC, onay ve denetim izi her kaynak için geçerli (Techzine kaynağı). Güçlü yan: geniş kurumsal ekosistem, denetim. Zayıf yan: AI asistanı bazı özellikler önizleme (tech preview) aşamasında. Kaynaklar: https://www.redhat.com/en/blog/red-hat-lightspeed-2025-observability-actionable-automation ; https://www.techzine.eu/news/infrastructure/141317/red-hat-makes-ansible-the-trusted-execution-layer-for-agentic-ai/
- **VMware Aria Automation Orchestrator (vRO)**: Grup izinleri çalışabilir içeriğe erişimi yönetir; vSphere kimlik doğrulamasında grup izinleri yalnızca Run izni destekler. Akış dili JavaScript tabanlı (doğrulanamadı). Kaynak: https://docs.vmware.com/en/VMware-Aria-Automation/8.16/Using-Automation-Orchestrator/GUID-D0FFDD2A-3D6C-485C-850B-FCD445391365.html . Diğer ayrıntılar doğrulanamadı.
- **Microsoft System Center Orchestrator**: Yetki SQL Server veritabanı rolleri üzerinden; grup varsayılan olarak runbook oluşturma, görüntüleme, değiştirme ve çalıştırma yetkisine sahip. Kaynak: https://learn.microsoft.com/en-us/system-center/orchestrator/security-plan?view=sc-orch-2025
- **Kestra**: YAML tabanlı akış; akış otomasyonu için Enterprise Edition eklentisi var (Classic ve Containerized modları). Kaynak: https://kestra.io/plugins/plugin-ee-hpoo . Diğer özellikler doğrulanamadı.
- **Temporal**: Dayanıklı çalıştırma (durable execution); başarısız aktivite geri çekilimle (backoff) yeniden denenir, çalışan düşerse yeniden planlanır. Onay deseni (Approval): sinyallerle dış karar beklenir. Dış yan etkiler "tam bir kez" garanti edilmez; idempotency gerekir. Kaynak: https://docs.temporal.io/design-patterns ; https://docs.temporal.io/encyclopedia/failures-and-error-handling.md . Güçlü yan: kod tabanlı, dayanıklı. Zayıf yan: BT operasyon ekipleri için geliştirici gerektirir.
- **ServiceNow Flow Designer / Orchestration, BMC TrueSight Orchestration, Resolve Actions, n8n**: Doğrulanamadı (bu araştırmada resmi belgelerinden özellik çıkarılmadı).

## 5. Zayıflıklar, kullanıcı şikâyetleri ve agentic otomasyon

**Kullanıcı görüşleri (kaynaklı, küçük örneklem):**
- Olumlu: iş akışı otomasyonu ve entegrasyon; kayıt aracı (recorder) ile teknik olmayan kullanıcıların da otomasyon üretebilmesi; hazır kütüphanelerin çokluğu. Kaynak: https://origin.peerspot.com/products/opentext-operations-orchestration-reviews/page-3 ; https://www.trustradius.com/products/operations-orchestration/reviews
- Olumsuz: destek almada zorluk, maliyet ve uygulama/destek kaynağı ihtiyacı, üçüncü taraf entegrasyonlarının yavaşlığı, kurulum karmaşıklığı ve uzmanlık gereksinimi. Kaynak: aynı PeerSpot sayfası; https://www.itqlick.com/hp-operations-orchestration
- Puanlar: PeerSpot karşılaştırmasında OpenText akış otomasyonu ortalama 7,8 (26 değerlendirme); Gartner'da eski "HP OSS Orchestration" 4,3 (4 değerlendirme); TrustRadius 10/10 ama yalnızca 3 değerlendirme. Kaynak: https://www.peerspot.com/products/comparisons/microsoft-system-center-orchestrator_vs_opentext-operations-orchestration ; https://www.gartner.com/reviews/product/hp-oss-orchestration
- Uyarı: en çok atıf yapılan yorumların birçoğu 2016 dönemine ait ve OpenText geçişinden önce. Örneklem küçük.

**Statik akış motorlarının yapısal zayıflıkları:**
- Kırılganlık: Adımın çıktı biçimi değişirse sonraki adımlar kırılır. Kaynak doğrudan akış otomasyonu için doğrulanamadı; kaynaklı destek: akış otomasyonu Designer doğrulamasının eksik bağımlılıkları ve bozuk YAML'ı yakalaması, yani değişime duyarlılık belgelenmiş (https://docs.microfocus.com/CSA/4.90/Content/OO_Designer/validating_flows.htm).
- Her istisna için dal çizme: Kaynaklı destek: StackStorm kuralında yalnızca tek action bölümü olduğu için çoklu dallar workflow veya ek kurallarla çözülür (https://st2docs.readthedocs.io/en/stable/rules.html). akış otomasyonu'da benzer bir kısıt kaynakla doğrulanamadı.
- Sürükle-bırak bakım yükü, içerik paketi sürüm yönetimi ve hata ayıklama güçlüğü: Kaynaklı destek yok. Yalnızca topluluk yorumlarında "kaynak ve destek yükü" ifadeleri var. Bu maddeler genel gözlemdir.
- Öğrenme eğrisi: Kaynaklı destek: "uzmanlık gerektirir" (ITQlick).
- Ortam değişimi: Kaynaklı destek: RAS konumu ve localhost kullanımı gibi ortam bağımlı yapılandırma hataları (ayarlar sayfası).

**Agentic (LLM tabanlı) otomasyon: bu alana nasıl giriyor?**
- **Red Hat Ansible Lightspeed + EDA (2025)**: AI bir durumu analiz edip bir eylem önerir; çalışacak olan insan tarafından onaylanmış playbook'tur. Olay → kural → playbook. Aynı RBAC, onay ve denetim izi uygulanır. Kaynak: https://www.redhat.com/en/blog/red-hat-lightspeed-2025-observability-actionable-automation ; https://www.techzine.eu/news/infrastructure/141317/red-hat-makes-ansible-the-trusted-execution-layer-for-agentic-ai/
- **PagerDuty**: İnsan-döngüde (human-in-the-loop) mimari; ekipler ajanın otonom mu yoksa onay bekleyerek mi çalışacağını seçer. Yıkıcı işlemler için onay kapısı, RBAC ve denetim önerilir. Kaynak: https://www.pagerduty.com/resources/incident-management-response/learn/incident-management-transformation-guide/ (arama özeti). Üçüncü taraf bir yazının PagerDuty için verdiği "%70 gürültü azaltma, %40 MTTR düşüşü" iddiası doğrulanamadı; kullanılmamalı.
- **Açık kaynak ve uygulamacı kılavuzları (blog düzeyi)**: Tipik korumalar: tipli parametreler, yıkıcı işlemler için kuru çalıştırma (dry-run), geri döndürülemez işlemler için insan onayı, imzalı işlem günlükleri, kill-switch; LLM yalnızca onaylı runbook'lar arasından seçim yapar, komut uydurmaz; aynı olay için tekrar sınırı (örnekte iki denemeden sonra insana yükseltme). Rollback planı zorunlu sayılıyor. Kaynak (zayıf, blog): https://www.callsphere.ai/blog/ai-agent-runbook-automation-converting-human-procedures-automated-workflows ; https://dev.to/nimay_04/agentic-ai-in-devops-useful-only-after-you-add-guardrails-2ea3
- **Akademik kaynak (Amazon Science)**: İnsan-döngüde runbook iyileştirme; ajan operatöre yol gösterir ve runbook düzenlemesi önerir, otonom çalışmaz; runbook'un ajan sisteminden ayrıştırılabilir olması açıklanabilirliği korur. Kaynak: https://cdn.amazon.science/78/ae/133af2444c9f98d4dd40d025751f/scipub-approval152129-40856700-humanintheloop-runbook-improvement-with-agentic-support-automation.pdf

**Statik akışın hâlâ üstün olduğu yerler (yorum; kaynak destekli kısımlar belirtildi):**
- Tekrarlanabilirlik: Aynı girdi her zaman aynı adımları izler. LLM'nin çıktısı her koşuda değişebilir.
- Denetim izi ve uyumluluk: akış otomasyonu ve Microsoft SCO gibi araçlar yetki ve koşu kaydı için yerleşik yapılar sunar (kaynaklar yukarıda). Agentic sistemlerde bunu sağlamak ek iş gerektirir.
- Onay: Statik akışta onay noktası açıkça tanımlanır; ajan yaklaşımında insan onayı bir koruma olarak eklenmelidir (PagerDuty ve Red Hat kaynakları bunu önerir).
- Ön denetim (review): Statik içerik bir kez gözden geçirilir ve sürümlenir; LLM kararları koşudan koşuya değişebilir.

## 6. Deneme kurulumu

- **akış otomasyonu deneme sürümü / Community Edition**: Doğrulanamadı. TrustRadius listesinde "Free Trial: No, Free/Freemium: No" yazıyor, ancak bu bilgi güncel olmayabilir. akış otomasyonu, OpenText Automation Center içinde sunuluyor; ücretsiz deneme yalnızca talep üzerine ve bir OpenText ya da satış ortağı üzerinden olabilir (UK kamu pazaryeri ilanı "talep üzerine ücretsiz deneme" diyor). Kaynak: https://www.trustradius.com/products/opentext-operations-orchestration ; https://www.opentext.com/products/automation-center ; https://www.applytosupply.digitalmarketplace.service.gov.uk/g-cloud/services/676691564886164
- **akış otomasyonu içerik paketleri**: OpenText Marketplace'ten indirilebilir; Marketplace koşullarının kabulü gerekir. Lisanslı akış otomasyonu platformu için değerlendirme lisansı bulunamadı. Kaynak: https://marketplace.opentext.com/itom/content/operations-orchestration-content-sdk (arama özeti)
- **Sistem gereksinimleri**: Doğrulanamadı (akış otomasyonu Support Requirements sayfası CSA 4.80 belgesinde anılıyor ancak içeriği çekilemedi: https://docs.microfocus.com/CSA/4.80/Content/Support_Matrix/Reference_Websites_and_Downloads.htm).
- **Konteyner / Docker**: akış otomasyonu Containerized modu mevcut; Designer ve Containerized REST ayrıntıları üçüncü taraf kaynaklarda geçiyor (Kestra). akış otomasyonu'nun resmi konteyner imajı ve kurulum adımları **doğrulanamadı**.
- **CloudSlang (açık kaynak) Docker**: Doğrulandı. `cloudslang/cloudslang` (hafif: Java, CLI, standart içerik) ve `cloudslang/cloudslang-dev` (Python, Git, SSH, editörler). Örnek: `docker run --rm cloudslang/cloudslang run --f ... --i text=...`. CLI komutları: run, inspect, list, inputs, env --setAsync. Girdi dosyası `--if` (YAML), sistem özellikleri dosyası `--spf`, bağımlılık dizini `--cp`. Kaynak: https://cloudslang-docs.readthedocs.io/en/latest/cloudslang/cloudslang_cli.html ; https://cloudslang-docs.readthedocs.io/en/latest/overview/get_started.html . Projenin etkin bakımı doğrulanamadı.
- **Öneri (harness prototipi için)**: CloudSlang CLI ve dev konteyneri, akış otomasyonu'nun dağıtım ve Designer bağımlılığı olmadan, akış dili ve içerik modeli üzerinde deney yapmak için yararlı görünüyor. akış otomasyonu'nun gerçek davranışı (RAS, Central, yetki) için bir akış otomasyonu örneği gerekir, bu araştırma ile doğrulanamadı.

## Harness için çıkarımlar

1. Dinamik ajan, bir adım beklenmeyen çıktı ürettiğinde önce çıktı şemasını doğrulamalı; şema uymuyorsa beceriyi ya da akışı değiştirmeden insana yükseltmelidir.
2. Beceri değişimi (skill mutation) yalnızca onaylı bir sürüm kaydıyla yapılmalı; değişen beceri eski sürümle birlikte saklanmalı ki geri alınabilsin.
3. Yıkıcı işlemler (silme, geri dönüşsüz değişiklik, üretim değişikliği) için her zaman insan onayı kapısı olmalı; ajan bu adımı kendi başına geçemez.
4. Her yıkıcı eylemin önünde kuru çalıştırma (dry-run) modu bulunmalı ve sonucu insana gösterilmeli.
5. Her eylemin geri alma (rollback) tanımı olmalı; geri alma tanımı yoksa eylem reddedilmeli.
6. Aynı olay için yeniden deneme sayısı sınırlanmalı (örneğin iki deneme); sınır aşılırsa ajan durup insana devretmeli.
7. LLM yalnızca onaylı beceri ya da runbook kataloğu arasından seçim yapmalı; komut ya da betik üretip doğrudan çalıştırmamalı.
8. Her ajan kararı ve eylemi, değiştirilemez bir denetim izine (girdi, seçilen beceri, çıktı, onaylayan) yazılmalı.
9. Beceri tanımları tipli girdi-çıktı şemasıyla yazılmalı; şemaya uymayan çağrı çalıştırılmamalı.
10. Kill-switch: operatör tüm ajan eylemlerini tek adımda durdurabilmeli.
11. Kısmi başarı durumu açıkça modellenmeli (örnek: 100 sunucudan 37'si başarısız); ajan sessizce devam etmemeli, sonucu raporlamalı.
12. Kimlik bilgileri ajan bağlamına hiç girmemeli; bunun yerine yetki veren bir sistem hesabı kullanılmalı (akış otomasyonu'nun sistem hesabı modeli bu fikri destekliyor).
13. Ajan, tekrarlanabilirlik için bir olası akış planı üretip onaylandığında bu planı sabit bir akış olarak kaydedebilmeli; bu sayede aynı işin sonraki koşuları deterministik olur.
14. Dal yazmak yerine hata durumunda ajanın "neden başarısız oldu" açıklamasını ve önerilen düzeltmeyi insana sunması, akışın kırılganlığını azaltır; ancak öneri yalnızca onaydan sonra uygulanmalıdır.
15. Harness testleri, gerçek akış otomasyonu ya da hedef ortamlara bağlanmadan önce CloudSlang CLI gibi kapalı bir ortamda yapılmalı; üretim ortamına geçiş için ayrı bir onay kapısı tanımlanmalı.

## Kaynak listesi

- https://docs.microfocus.com/CSA/4.90/Content/OO_Designer/Intro.htm
- https://docs.microfocus.com/CSA/4.90/Content/OO_Designer/Navigation.htm
- https://docs.microfocus.com/CSA/4.90/Content/OO_Designer/validating_flows.htm
- https://docs.microfocus.com/CSA/4.90/Content/OO_Designer/Step_inputs_outputs.htm
- https://docs.microfocus.com/CSA/4.80/Content/Installation_and_Configuration/Configuration_Guide/HPOOSettings_Configure_mng.htm
- https://docs.microfocus.com/CSA/4.81/Content/Installation_and_Configuration/Configuration_Guide/HPOOSettings_Configure_mng.htm
- https://docs.microfocus.com/CSA/4.91/Content/Installation_and_Configuration/Configuration_Guide/HPOOSettings_Configure_mng.htm
- https://kestra.io/plugins/plugin-ee-hpoo
- https://cloudslang-docs.readthedocs.io/en/latest/cloudslang/cloudslang_cli.html
- https://cloudslang-docs.readthedocs.io/en/latest/overview/get_started.html
- https://cloudslang-docs.readthedocs.io/en/v1.0/cloudslang_dsl_reference.html
- https://marketplace.opentext.com/itom/content/community-general-utilities
- https://marketplace.opentext.com/itom/content/oo-opentext-solutions-content-pack-afl
- https://www.opentext.com/products/automation-center
- https://www.trustradius.com/products/opentext-operations-orchestration
- https://origin.peerspot.com/products/opentext-operations-orchestration-reviews/page-3
- https://www.itqlick.com/hp-operations-orchestration
- https://www.gartner.com/reviews/product/hp-oss-orchestration
- https://www.peerspot.com/products/comparisons/microsoft-system-center-orchestrator_vs_opentext-operations-orchestration
- https://docs.rundeck.com/docs/learning/getting-started/jobs/job-options.html
- https://docs.rundeck.com/docs/manual/jobs/workflow-strategies/ruleset.html
- https://docs.rundeck.com/docs/manual/workflow-steps/pagerduty.html
- https://docs.stackstorm.com/workflows.html
- https://st2docs.readthedocs.io/en/stable/rules.html
- https://st2docs.readthedocs.io/en/stable/orquesta/development/index.html
- https://www.redhat.com/en/blog/red-hat-lightspeed-2025-observability-actionable-automation
- https://www.techzine.eu/news/infrastructure/141317/red-hat-makes-ansible-the-trusted-execution-layer-for-agentic-ai/
- https://docs.vmware.com/en/VMware-Aria-Automation/8.16/Using-Automation-Orchestrator/GUID-D0FFDD2A-3D6C-485C-850B-FCD445391365.html
- https://learn.microsoft.com/en-us/system-center/orchestrator/security-plan?view=sc-orch-2025
- https://docs.temporal.io/design-patterns
- https://docs.temporal.io/encyclopedia/failures-and-error-handling.md
- https://www.pagerduty.com/resources/incident-management-response/learn/incident-management-transformation-guide/
- https://cdn.amazon.science/78/ae/133af2444c9f98d4dd40d025751f/scipub-approval152129-40856700-humanintheloop-runbook-improvement-with-agentic-support-automation.pdf
- https://www.callsphere.ai/blog/ai-agent-runbook-automation-converting-human-procedures-automated-workflows
- https://dev.to/nimay_04/agentic-ai-in-devops-useful-only-after-you-add-guardrails-2ea3
- https://www.applytosupply.digitalmarketplace.service.gov.uk/g-cloud/services/676691564886164
