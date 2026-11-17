# Tipik adminlik talepleri: sunucu otomasyonu ve akış otomasyonu'da yapılışı ile harness'te yapılışı

Tarih: 2026-11-17
Girdi dosyaları: `01-sunucu-adminlik.md` (sunucu otomasyonu 10.50/10.51/10.60 belgeleri), `02-akis-adminlik.md` (akış otomasyonu/CSA 4.80–4.91 belgeleri, topluluk content pack'leri), `05-forum-vakalari.md` (sunucu otomasyonu ve akış otomasyonu forum vakaları, kimlik `F-sunucu otomasyonu-NNN` / `F-akış otomasyonu-NNN`).

Yöntem notu: Bu belge üç girdi dosyasındaki kaynaklara dayanır. Resmi portalda ayrıca doğrulama yapılmadı; bir adım belgede ya da forumda bulunamadıysa "doğrulanamadı" yazıldı. "Analog" ifadesi BMC TrueSight/BladeLogic için kullanıldı; bu kaynaklar sunucu otomasyonu'ya kesin bilgi olarak taşınmadı. Forum kanıtları, forumdaki "Verified Answer" işaretine ya da açık bir çözüm metnine dayanan vakalarda "doğrulanmış", yalnız öneri olanlarda "önerilen" olarak geçer.

Terim notu: sunucu otomasyonu 10.60 belgesi "device group" yerine "server group" diyor; bu metinde ikisi de geçer.

---

## Özet tablosu

| No | Talep (kısa) | sunucu otomasyonu adım sayısı (yaklaşık) | akış otomasyonu'da yaklaşık adım | Ön hazırlık gereği | Ana kırılma noktası |
|---|---|---|---|---|---|
| T1 | Çok sunucuda betik çalıştır, sonucu topla | 10 | 6 (tasarım) | Yüksek: kayıtlı betik, grup, kimlik, zaman aşımı | Now/Runtime grup farkı, tutarsız kimlik, zaman aşımı |
| T2 | Ad kalıbıyla sunucularda betik, çıktı XML/CSV, e-posta | 9 + dışa aktarma | 7 (tasarım) | Yüksek: grup kuralı, betik, e-posta, çıktı biçimi | sunucu otomasyonu'da XML seçeneği yok; e-posta şablonu doğrulanamadı |
| T3 | Yeni sunucuya standart ürün/ajan kur ve doğrula | 6 | 7 (tasarım) | Yüksek: politika, paket, test sunucusu, ajan kaydı | Ajan kurulumu, politika değişince yeniden remediation |
| T4 | Erişilemeyen ajanı teşhis et ve onar | 6 | 4 (tasarım) | Orta: Communication Test, log erişimi | Test sırası, IP değişimi, sertifika ve zaman aşımı |
| T5 | Paket/yazılım dağıt | 7 | — | Yüksek: paket deposu, politika, test sunucusu | Atama ≠ kurulum; kurulum zaman aşımı |
| T6 | Yama durumu raporu | 5 | — | Orta: güncel yama içeriği | Tarama izni, katalog eşlemesi, genel durum gizlemesi |
| T7 | Servis durmuşsa yeniden başlat ve bildir | 4 | 6 (tasarım) | Düşük-orta: servis listesi, log erişimi | startsync ve bağımlılık zinciri |
| T8 | Disk doluluk müdahalesi | doğrulanamadı | 6 (tasarım) | Orta: izinli dizin listesi, eşik | Temizlik eşiğe ulaşmaz; /tmp güvenilmez |
| T9 | Kullanıcı aç | doğrulanamadı | 5 (tasarım) | Yüksek: yetki modeli, hedef sistem | Yetki yetersizliği, var olan hesap |
| T10 | Uyum/denetim karşılaştırması | 7 | doğrulanamadı | Yüksek: referans snapshot | Referans güncel değil, audit kaynağı yanlış |
| T11 | Yarıda kalanı yalnız başarısızlarda yeniden dene | 3 (elle) | 2 (REST, doğrulanamadı) | Orta: başarısız liste, idempotency | sunucu otomasyonu'da yeniden deneme yok; Now grubu kayar |
| T12 | Akış ortasında beklenmeyen çıktı, akışı düzelt | 2 (çıktı sınırı) | 5 (tasarım) | Yüksek: çıktı şeması | Sürüm uyumsuzluğu, eksik fonksiyon, sessiz devam |
| T13 | Agent'ı kaldır ve sunucu otomasyonu kaydını sil | 3 (önerilen, doğrulanmamış) | — | Yüksek: onay, bakım penceresi | API yalnız kaydı siler, host'taki yazılımı silmez |

---

## T1. Çok sunucuda betik çalıştırıp sonucu toplamak

- **talep:** "Şu 40 sunucuda şu betiği çalıştır, hangisi başarılı hangisi başarısız, çıktıları bir yere topla."
- **sa_oo_yolu (sunucu otomasyonu 10.60):**
  1. Run Server Script penceresini aç (belge: "Ways to open the Run Script window").
  2. Hedef: sunucu ya da grupları "Include" ile ekle, gereksizleri "Exclude" ile çıkar.
  3. Server Group Calculation: **Now** (seçim anı) ya da **Runtime** (iş çalışırken) seç. Runtime için "Allow Run Refresh Jobs" yetkisi gerekir.
  4. Betik: kayıtlı betik seç ya da ad hoc betik tanımla/içe aktar.
  5. Çalıştırma kimliği: UNIX için root, Windows için Local System, Super User ya da adlandırılmış kullanıcı (Windows'ta domain).
  6. "Script timeout" (dakika) gir.
  7. Parametreleri gir; çıktı saklama "Discard" ya da "Retain" (boyut sınırlı).
  8. Zamanlama: hemen, Once, Daily, Weekly, Monthly ya da Custom (crontab).
  9. Bildirim: e-posta alıcısı; On Success / On Failure / On Termination.
  10. Başlat; sunucu bazlı durum ve çıkış kodu izlenir. Sıfır başarı, sıfırdan farklı hata. "Show output in table" ve "Export All Results" ile sonuç alınır.
- **adim_sayisi:** yaklaşık 10 (ekran adımı). Sonuç toplama ayrı bir dışa aktarma adımı.
- **on_hazirlik:** Betik kayıtlı ve test edilmiş olmalı; hedef grup ya da sunucu listesi hazır; çalıştırma kimliği tüm hedeflerde aynı kullanıcı adı ve parolayla geçerli olmalı (eşzamanlı çalıştırma için); zaman aşımı betiğin normal süresinden uzun seçilmeli; Runtime kullanılacaksa ilgili yetki.
- **kirildigi_yer:** 01 §1.2 "Sık hata": zaman aşımının yetersiz kalması; aynı kimliğin tüm sunucularda olmaması. 01 §2 adım 1: Now ve Runtime farkı. Ayrıca 05 F-SV-008: tek bir script yürütmesi tek hedef cihaza bağlıdır; bir sunucudan diğerinde iş tetiklemek sunucu otomasyonu modelinde yok.
- **forum_kaniti:** F-SV-008 (https://community.opentext.com/it-ops-cloud/automation-ctr/f/server-automation-discussions/531267/triggering-a-script-on-other-server-while-connected-to-a-server-within-a-single-instance-script-execution) — cevapsız, ama sınır belgeyle tutarlı. Doğrudan "çok sunucu toplu betik" vakası 05'te yok.
- **ajanla_yapilisi:**
  - Ajan talebi okur, "40 sunucu" ifadesini hedef listesine çözer ve hangisinin grup olduğunu sorar; grup kullanılıyorsa Now/Runtime seçimini kullanıcıya açıkça gösterir.
  - Onaylı "toplu betik" becerisini seçer; kimlik olarak kayıtlı bir kimlik referansı kullanır (parola prompt'a girmez).
  - Zaman aşımını zorunlu parametre yapar; kullanıcı vermezse betik ortalama süresinden türetilmiş bir değer önerir ve onay ister.
  - İş bitince sunucu bazlı sonucu tek şemaya çevirir (başarılı / başarısız / zaman aşımı / iptal) ve tablo olarak sunar; sunucu otomasyonu'nın dışa aktarımını yalnız ham kaynak olarak saklar.
- **olculebilir_fark:**
  - sunucu otomasyonu elle: yaklaşık 10 ekran adımı + betik kaydı + kimlik tutarlılığı kontrolü + sonuç dışa aktarma ve ayrıştırma.
  - Harness: 1 talep + 1 onay; toplam sunucu sayısı ile sonuçlanan sayı eşleşmeli (hedef sayısı = başarılı + başarısız + zaman aşımı).
  - Ölçülecek: kısmi başarısızlığın açık raporlanıp raporlanmadığı; Now/Runtime bilgisinin rapora yazılıp yazılmadığı; süre.

---

## T2. Adı belli kalıpla başlayan sunucularda betik, çıktı XML/CSV, e-posta ile gönderim

- **talep:** "PA ile başlayan tüm sunucularda şu betiği çalıştır, çıktıyı XML'e çevirip ekibe e-posta at."
- **sa_oo_yolu:**
  - sunucu otomasyonu: (a) Ad kalıbıyla hedef: 01 §1.1'e göre grup üyeliği "elle ya da kurallarla" belirlenir; ancak ad önekine dayalı kural sözdizimi kaynaklarda **doğrulanamadı**. (b) T1'in 10 adımı. (c) Sonuç dışa aktarma: sunucu otomasyonu listesi ZIP (klasörlü/klasörsüz), ham metin, biçimli metin ve CSV veriyor; **XML seçeneği belgede yok**. (d) Bildirim e-postası: "On Success/Failure" koşulu var; e-posta içeriği ve biçimi **doğrulanamadı**.
  - akış otomasyonu (tasarım, 02 §3 madde 7): hedef listesi ("PA" önekli sunucular) → RAS üzerinden betik → sonuçları topla → XML/CSV üret → e-posta. Bu akış bir tasarım önerisi; belirli bir akış otomasyonu örneğinden alınmadı.
- **adim_sayisi:** sunucu otomasyonu: 9 + dışa aktarma ve biçim dönüşümü (harness ya da betik tarafında). akış otomasyonu (tasarım): yaklaşık 7.
- **on_hazirlik:** sunucu otomasyonu: ad kalıbı için dinamik bir grup ya da sunucu listesi; betik kayıtlı; e-posta alıcısı tanımlı; dönüşüm betiği (XML) hazır. akış otomasyonu: RAS konumu (localhost değil, FQDN ya da IP; 02 §1 kaynakları); e-posta operasyonu için yapılandırma; hedef listesinin oluşturulması (ad kalıbı sorgusu bir operasyonla yapılacaksa o operasyon doğrulanamadı).
- **kirildigi_yer:**
  - sunucu otomasyonu: XML çıktısı yok (01 §2 adım 9); e-posta şablonu içeriği doğrulanamadı (01 §2 "Doğrulanamadı").
  - akış otomasyonu: 02 §3 madde 7 kendi kırılma noktasını yazıyor: hedeflerin bir kısmında bağlantı hatası; kısmi başarıda akışın nasıl devam edeceği tanımsız kalırsa rapor yanlış olabilir.
  - Forum: F-SV-006, Global Shell'de `/bin/mail` geçici dosya hatası; çözüm TMPDIR'ı /tmp dışında bir dizine ayarlamak (doğrulanmış).
- **forum_kaniti:** F-SV-006 (https://community.opentext.com/it-ops-cloud/automation-ctr/f/server-automation-discussions/532733/mail-command-from-global-shell) — doğrulanmış çözüm. Ad kalıbı konusunda vaka yok.
- **ajanla_yapilisi:**
  - Ajan "PA" kalıbını sunucu envanterinde arar, eşleşen listeyi gösterir ve operatörden onay alır (kalıp yanlış eşleşebilir).
  - Betiği T1 yolundan çalıştırır; çıktıyı harness içinde XML ya da CSV'ye dönüştürür (sunucu otomasyonu'nın XML'i yok), dönüşüm başarısızsa betiği çalıştırmadan durur.
  - E-postayı gönderirken alıcı ve içerik operatörden gelir; içerik sunucu çıktısından otomatik üretilse bile önizleme gösterilir (uyarı: dış veri e-posta içeriğine taşınır).
  - Kısmi başarısızlık varsa raporun başına "X / Y sunucu başarılı" yazılır; başarısızlar listelenir.
- **olculebilir_fark:**
  - Elle yol: ad kalıbı grubu + betik + zamanlama + bildirim + dışa aktarma + ayrı bir XML dönüşümü + e-posta (ayrı araç) — 2 araç arası geçiş.
  - Harness: tek talep, tek onay; XML dosyası çıktı sayısıyla eşleşir mi (hedef = satır sayısı).
  - Ölçülecek: kalıp eşleşmesinin sayısı (beklenen ile gerçek), e-postanın gönderilip gönderilmediği, kısmi başarısızlığın e-postada görünüp görünmediği.

---

## T3. Yeni kurulan her sunucuya standart ürün/ajanları otomatik kurmak ve doğrulamak

- **talep:** "Yeni açılan sunucuya standart paketleri, izleme ajanını ve sunucu otomasyonu ajanını kur, sonra çalıştığını doğrula."
- **sa_oo_yolu:**
  1. Sunucu sunucu otomasyonu'ya kayıtlı olmalı; ajan kurulumu ve kaydı (01 §1.3 "Ne yapılır"; adım ayrıntısı **doğrulanamadı**).
  2. Sunucu grubuna (device/server group) ekle.
  3. Yazılım politikası oluştur ya da mevcut politikayı gruba ata (01 §1.5): paket, betik ve yapılandırma sıralı.
  4. Remediate et (atama tek başına kurmaz; remediation kurar).
  5. Communication Test çalıştır: Agent-DAE, Agent-SWR, CE-AGT, Agent-CE, MID eşleşme testi (01 §1.3).
  6. Uyum taraması çalıştır (01 §1.5).
  7. İşletim sistemi de kurulacaksa: system package + build plan + provisioning (01 §1.7, doğrulanamadı ayrıntı).
- **adim_sayisi:** 6 (kurulum hariç, kurulum ajanın kendi adımları doğrulanamadı).
- **on_hazirlik:** Test sunucusunda denenmiş politika (01 §1.5 "belge önerisi"); paket deposu içeriği güncel; ajan kurulum paketi; DNS ve yönetim IP'si; standart listenin belgeli hali. akış otomasyonu tasarımında (02 §3 madde 1): ağ/DNS kontrolü, ajan kurulumu, yapılandırma, izleme kaydı, CMDB güncellemesi.
- **kirildigi_yer:**
  - 01 §1.5: Politika değiştirildiğinde o politikayı kullanan sunucular uyumsuz olur ve yeniden remediation gerekir.
  - F-SV-010: "will not install" — yama önerilen listede değilse atlanıyor; iletişim testi başarılı ama sunucu politikaya bağlı değil.
  - F-SV-022: Agent sertifika uyuşmazlığı, "Error from remote (3063)"; ağ ya da iletişim sorunu gibi görünüyor, sertifika değil.
- **forum_kaniti:** F-SV-010 (https://community.opentext.com/it-ops-cloud/automation-ctr/f/server-automation-discussions/530609/during-patch-remediation-will-not-install-error-coming) — cevapsız. F-SV-022 (https://community.opentext.com/it-ops-cloud/automation-ctr/f/server-automation-discussions/528434/error-agent-certificate-mismatch) — önerilen: ağ kesintisi kabul edilip agent yeniden kurulur.
- **ajanla_yapilisi:**
  - Ajan "standart seti" bir şablon olarak tutar (politika + kurulum listesi); yeni sunucu için sadece listeyi uygular.
  - Her adımdan sonra kontrol: kurulum çıkış kodu, Communication Test sonucu, uyum taraması sonucu. Üçü de geçmeden "hazır" demez.
  - Politika bir değişikliği varsa uygulamadan önce hangi sunucuların uyumsuz olacağını listeler (01 §1.5).
  - Yazılım politikası değişikliği için kullanıcıdan onay alır; test sunucusu sonucu olmadan üretime atamaz.
- **olculebilir_fark:**
  - Elle: 6 adım + her sunucu için ayrı kontrol; 10 sunucuda 60 ekran adımı (tahmin, doğrulanamadı).
  - Harness: 1 talep; sunucu başına "hazır/hazır değil" çıktısı ve gerekçe.
  - Ölçülecek: test sunucusunda geçen süre; kaç sunucuda Communication Test'in ilk denemede geçtiği; hazır olmayan sunucuların gerekçesi.

---

## T4. Erişilemeyen ajanı ya da sunucuyu teşhis edip onarmak

- **talep:** "Şu sunucu sunucu otomasyonu'dan erişilemiyor, bak, düzelt."
- **sa_oo_yolu:**
  1. Communication Test çalıştır (01 §1.3): sırası "CE to Agent (AGT)", "Agent to SWR", MID eşleşme. 10.60'ta bazı testler önceki başarısızlıkta atlanır; önce başarısız olanı çöz, sonra testi tekrarla.
  2. AGT başarısızsa: ajan çalışıyor mu, yönetim IP'si doğru mu; bağlantı reddinde güvenlik duvarı; zaman aşımında ajanı yeniden başlat.
  3. SWR başarısızsa: sunucu IP'si değişmiş olabilir; ajanı durdur, yeniden başlat.
  4. Tekrar test et.
  5. Hâlâ sorun varsa ajan günlüğüne bak (F-SV-012: `/var/log/opsware/agent/`; Windows için ortak dosyalar altındaki log dizini).
- **adim_sayisi:** 6. 05 F-SV-012 önerisine göre 3. adımda log incelemesi eklenir.
- **on_hazirlik:** Hedef sunucuya log okuma yetkisi; yönetim IP ve güvenlik duvarı bilgisi; ajanı yeniden başlatma yetkisi; ajan kurulum paketi (onarım sonunda gerekebilir).
- **kirildigi_yer:**
  - 01 §1.3 "Sık hata": IP değişikliği, güvenlik duvarı, ajanın hiç çalışmaması.
  - Belge, bazı onarım adımlarını ayrıntılandırmıyor (ör. ajanı yeniden başlatmanın komutu ve yetkisi).
  - Forum: F-SV-012 "Overall server status: Time out" — iletişim testi başarılı olsa da genel durum zaman aşımı görünebiliyor; tuzak: yama işi başarılı gösterebilir.
  - Forum: F-SV-022 sertifika uyuşmazlığı; uzak komut ön kontrolünde 3063 hatası.
- **forum_kaniti:** F-SV-012 (https://community.opentext.com/it-ops-cloud/automation-ctr/f/server-automation-discussions/529508/overall-server-status-is-time-out-while-patch-deployment) — doğrulanmış: önce iletişim testi, sonra log, sonra başka bir işle doğrulama. F-SV-022 — önerilen.
- **ajanla_yapilisi:**
  - Ajan testleri belgedeki sırayla çalıştırır, her birinin sonucunu sınıflandırır: "AGT", "SWR", "MID".
  - Her sınıf için belgedeki önerilen onarım adımını uygular; ama **ajan yeniden başlatma ve yeniden kurulum** adımları yıkıcı kabul edilip operatör onayı ister.
  - Onarım sonrası testi tekrar çalıştırır. Geçerse durumu kaydeder; geçmezse olası nedeni ve günlük alıntısını raporlar, otomatik olarak daha ileri gitmez.
  - Erişilemeyen sunucuyu hedef kümesinden çıkarır (T1 ile ilişki).
- **olculebilir_fark:**
  - Elle: 6 adım, her biri için ayrı ekran ve günlük okuma; teşhis süresi operatöre bağlı.
  - Harness: testlerin sırası ve sonucu sabit; onarım önerisi kaydedilir.
  - Ölçülecek: teşhis süresi, ilk test sonucundan onarılana kadar geçen süre, kaç sunucuda onarım sonrası test geçti, otomatik restart sayısı (onaysız 0 olmalı).

---

## T5. Paket ya da yazılım dağıtımı

- **talep:** "Şu paketi 25 Linux sunucuya kur, önce bir test sunucusunda dene."
- **sa_oo_yolu:**
  1. Paketi Software Repository'ye ekle (paket türü RPM, MSI vb.; 01 §1.5).
  2. Yazılım politikası oluştur; öğeleri sırala (paket, betik, uygulama yapılandırması).
  3. Test sunucusuna ata; remediate et.
  4. Sonucu doğrula.
  5. Üretim grubuna ata; remediate et.
  6. Uyum taramasını çalıştır.
  7. Politika değişirse yeniden remediation (01 §1.5).
- **adim_sayisi:** 7.
- **on_hazirlik:** Paket depoda; politika tanımlı; test sunucusu; hedef grup; Linux'ta depo erişimi (01 §1.4 sık hata). Yükseltme paketinde sürüm çakışması kontrolü.
- **kirildigi_yer:**
  - 01 §1.5: "Politika atamak tek başına kurulum yapmaz; remediation kurar." Atamayı kurulum sanmak yaygın yanlış.
  - F-SV-016: Windows Install Software zaman aşımı; kaynak yeterliliği ve ajan yeniden kurulumu çözmedi; hata spin bileşeninde görüldü; çözüm yazılmadı.
- **forum_kaniti:** F-SV-016 (https://community.opentext.com/it-ops-cloud/automation-ctr/f/server-automation-discussions/528787/sa---install-software-timeout-issue) — önerilen ve kesin değil.
- **ajanla_yapilisi:**
  - Ajan paketi ve hedef grubu bulur, politika taslağı çıkarır ve farkı gösterir.
  - Test sunucusuna atar; sonucu bekler; başarı kriterini (kurulum çıkış kodu ve doğrulama betiği) kontrol eder.
  - Üretime atamak için onay ister (politika atamak yıkıcı değil ama üretimi etkiler).
  - Atama sonrası remediation'ı başlatır; sonuçları sunucu bazlı raporlar; "atandı" ile "kuruldu" durumlarını ayrı gösterir.
- **olculebilir_fark:**
  - Elle: 7 adım, test ve üretim için iki ayrı politika ataması.
  - Harness: aynı akış; "atandı mı" ile "kuruldu mu" ayrı sayılır.
  - Ölçülecek: test sunucusunda başarı; üretimde kaç sunucu kuruldu, kaç zaman aşımı oldu; yeniden remediation sayısı.

---

## T6. Yama durumu raporu

- **talep:** "Bu hafta hangi sunucular yamasız, bir rapor çıkar."
- **sa_oo_yolu:**
  1. Yama ayarlarını ve politikasını kontrol et (01 §1.4).
  2. Hedef grubu seç.
  3. Yama taraması (Scan > Patch Compliance) çalıştır.
  4. Uyumluluk durumunu gör; uygunsuz sunucuları listele.
  5. Gerekirse remediation (ayrı karar).
  6. Raporla.
- **adim_sayisi:** 5 (rapor adımı dahil; dışa aktarma biçimi **doğrulanamadı**).
- **on_hazirlik:** Yama içeriği güncel (01 §1.4 sık hata); Linux için depo erişimi; Windows için tarama yetkisi; Server 2025 ve 24H2 ayrımı (F-SV-007).
- **kirildigi_yer:**
  - F-SV-004: Windows 2016'da admin olarak tarama izin hatası; sunucu otomasyonu superuser olmak hedef tarafta yetkiyi garanti etmez (cevapsız).
  - F-SV-007: Server 2025'te 2025-04 kümülatif güncellemesi listelenmiyor; katalogda ürün eşlemesi eksik olabilir (cevapsız).
  - F-SV-014: RHEL 8/9 için ISO güvenlik uyumluluk içeriği; sunucu otomasyonu paketinde eksik. ITOM Marketplace'teki "Security and Compliance for sunucu otomasyonu" içeriği çözüm olarak doğrulanmış.
  - 01 §1.4: Windows Server 2016 ve bazı Linux sürümlerinin 10.60'ta desteğinin düştüğü belirtiliyor (destek matrisi tam doğrulanamadı).
  - F-SV-010 ve F-SV-012: genel durum ve uyumluluk, hatayı gizleyebilir.
- **forum_kaniti:** F-SV-004 (https://community.opentext.com/it-ops-cloud/automation-ctr/f/server-automation-discussions/533548/scan-policy-compliance-failed-for-windows-2016-server-with-permission-problem), F-SV-007 (https://community.opentext.com/it-ops-cloud/automation-ctr/f/server-automation-discussions/532087/platform-installer-for-windows-server-2025---not-all-patches-displayed), F-SV-014 (https://community.opentext.com/it-ops-cloud/automation-ctr/f/server-automation-discussions/529169/iso-security-compliance-content-on-rhel-8-9-in-sa). F-SV-004 ve F-SV-007 cevapsız; F-SV-014 doğrulanmış.
- **ajanla_yapilisi:**
  - Ajan hedef grubu okur, tarama sonuçlarını sunucu bazlı toplar; "tarama başarısız" ile "yamasız" durumlarını ayırır (tarama hatası yamasız gibi raporlanmaz).
  - Her sunucu için tarama tarihi ve kapsam ("hangi içerik") yazılır.
  - Uygunsuz sunucular için remediation önerir; uygulamaz (ayrı onay).
- **olculebilir_fark:**
  - Elle: 5 adım + rapor biçimi (dışa aktarma ve ayrıştırma).
  - Harness: aynı sunucu sayısı için "uyumlu / uyumsuz / taranamadı" üç sınıf; toplamın tutarlılığı.
  - Ölçülecek: taranamayan sunucu oranı (izin, katalog, destek matrisi nedenleriyle); tarama tarihi eskiliği.

---

## T7. Servis durmuşsa yeniden başlatıp bildirmek

- **talep:** "sunucu otomasyonu'nın mesh servisleri düştü mü bak, düştüyse başlat ve bana haber ver."
- **sa_oo_yolu:**
  1. Servis durumu: `service opsware-sas status` (05 F-SV-020 önerisi).
  2. Bağımlılık zinciri: startsync; mm_wordbot ve diğer bileşenler (05 F-SV-009).
  3. Yeniden başlatma adımı: **doğrulanamadı** (sunucu otomasyonu'nın belge sayfası yeniden başlatma komutunu ve sırasını açıkça vermedi).
  4. Loglar: `/var/log/opsware/twist/server.log` ve `/var/log/opsware/mm_wordbot/` (05 F-SV-020).
  5. Yönetilen sunucuda ajan servisi: rosh (`reach`) ile tek komut (01 §1.9); komutun tam sözdizimi sürüme göre doğrulanmalı.
  6. Bildirim: e-posta ya da bilet (T2 ile aynı kısıtlar).
- **adim_sayisi:** 4 (sunucu otomasyonu çekirdek için; ayrıntı doğrulanamadı).
- **on_hazirlik:** Servis listesi; hangi servisin "kritik" olduğu; log erişimi; rosh erişimi; bildirim kanalı.
- **kirildigi_yer:**
  - F-SV-009: Yama sonrası yeniden başlatmadan sonra "Spin and/or Gateway are unavailable"; startsync `mm_wordbot` bağımlılığında başarısız; SSL "peer did not return a certificate" logda var. Forum yanıtı: destek kaydı ve log toplama; kök neden yazılmadı.
  - F-SV-021: RHEL 8.9'da run level ve openssl sorunu; `chkconfig opsware-sas on` hata verdi; temizlik sonrası kurulum yeniden başlatıldı (doğrulanmış).
  - F-SV-015: Twister API devre dışı; yapılandırma değişince servis yeniden başlatma gerekebilir, forumda net yazılmadı.
  - akış otomasyonu tasarımı (02 §3 madde 3): servis durdurulamaz ya da sağlık zaman aşımına uğrarsa ortam yarım kalır; geri dönüş adımı olmalı.
- **forum_kaniti:** F-SV-009 (https://community.opentext.com/it-ops-cloud/automation-ctr/f/server-automation-discussions/530838/sa-communication-error---spin-and-or-gateway-are-unavailable) — kesin çözüm yok. F-SV-021 (https://community.opentext.com/it-ops-cloud/automation-ctr/f/server-automation-discussions/525430/simple-sa-installation-getting-failure-run-level-not-3) — doğrulanmış.
- **ajanla_yapilisi:**
  - Ajan servis durumunu okur; durmuş servis yoksa sadece raporlar.
  - Servis durmuşsa bağımlılık zincirini kontrol eder, izinli servis listesi içindekileri başlatır (listede olmayanlar için durur ve sorar).
  - Başlattıktan sonra sağlık kontrolü yapar; SSL ya da sertifika hatası görürse otomatik tekrar denemez, insana yükseltir (F-SV-009 örneği).
  - Sonucu bildirir: ne durmuştu, ne başlatıldı, sağlık durumu.
- **olculebilir_fark:**
  - Elle: 4 adım + log okuma; bildirim ayrı bir işlem.
  - Harness: tek talep; izinli servis listesinden sapma yoksa ajan kendisi başlatır.
  - Ölçülecek: durmadan bildirime kadar süre; kaç kez otomatik başlatma denendi (sınır); insana yükseltilen olay sayısı.

---

## T8. Disk doluluk müdahalesi

- **talep:** "Şu sunucunun /var diski %95, temizle ama sadece geçici dosyalar; sonra yüzde ne oldu bak."
- **sa_oo_yolu:**
  - sunucu otomasyonu: disk doluluk için belgede ayrı bir hazır iş (job) ya da içerik **doğrulanamadı**. Mümkün yol: rosh `reach` ile komut çalıştırmak (01 §1.9), ancak temizlik komutunun güvenli kapsamı ve kayıt ayrıca tanımlanmalı.
  - akış otomasyonu (tasarım, 02 §3 madde 2): uyarı → disk kullanımı oku → eşik kontrolü → geçici dosya temizliği (yalnız tanımlı dizinler) → yeniden ölçüm → bilet kapatma.
- **adim_sayisi:** sunucu otomasyonu: doğrulanamadı (ayrı bir hazır iş yoksa rosh ile 4–5 komut). akış otomasyonu tasarımı: 6.
- **on_hazirlik:** İzinli dizin listesi; eşik değeri; temizlik betiği ya da komutu; rosh erişimi; kimlik ve yetki (F-SV-017: CLI'da çalıştıran kullanıcı root ya da eşdeğer olmalı).
- **kirildigi_yer:**
  - 02 §3 madde 2: temizlik sonrası kullanım eşiğin altına inmeyebilir; dal kurmak gerekir.
  - F-SV-006: `/tmp` güvenilir değil; geçici dosya hatası TMPDIR ile çözüldü. Disk temizliği ve geçici dizin birbirine karışabilir.
  - F-SV-017: CLI'da yetki yükseltme yok; GUI yükseltiyor.
- **forum_kaniti:** F-SV-006 (https://community.opentext.com/it-ops-cloud/automation-ctr/f/server-automation-discussions/532733/mail-command-from-global-shell) — doğrulanmış. F-SV-017 (https://community.opentext.com/it-ops-cloud/automation-ctr/f/server-automation-discussions/528968/resync-orphaned-ogfs-home-directories-in-new-sa-mesh) — doğrulanmış. Disk doluluğu için doğrudan forum vakası yok.
- **ajanla_yapilisi:**
  - Ajan eşik kontrolünü yapar; eşik aşılmamışsa temizlik yapmaz ve sadece raporlar.
  - Temizlik yalnız izinli dizin listesinden dosya siler; silinecek dosya listesini önce gösterir ve onay alır (silme geri alınamaz).
  - Temizlikten sonra ölçer; eşik hâlâ aşılıyorsa ikinci bir dal denemez, insana devreder.
  - Bilet kapatma ayrı bir onay adımıdır.
- **olculebilir_fark:**
  - Elle: 4–6 komut + ölçüm + bilet; her sunucu için tekrar.
  - Harness: tek talep, silinen dosya listesi ve öncesi/sonrası yüzde raporu.
  - Ölçülecek: silinen byte; eşiğin altına inme başarısı; onay sonrası silme sayısının listeyle eşleşmesi.

---

## T9. Kullanıcı açma

- **talep:** "Yeni gelen Ahmet için şu sunucuda hesap aç, şu gruba ekle, bilgilendir." (Hesap adı ve gruplar örnek.)
- **sa_oo_yolu:**
  - sunucu otomasyonu'da kullanıcı oluşturma (sunucu otomasyonu kullanıcısı ya da işletim sistemi hesabı): adımlar **doğrulanamadı**. 01 §1.12 yalnızca sunucu otomasyonu'nın customer, facility ve yetki kavramlarını anlatıyor.
  - sunucu otomasyonu yetki yönetimi: `aaa shell-perm` ile facility, customer ya da device group'a yetki (Administrators grubunda olmak gerekir; 01 §1.12).
  - İşletim sistemi hesabı için bir betik T1 yoluyla çalıştırılabilir; kimlik olarak Super User gerekir (01 §2 adım 3). Bu, yetki sınırı açısından dikkat gerektirir.
  - akış otomasyonu (tasarım, 02 §3 madde 4): talep → dizin kontrolü → hesap oluşturma/devre dışı bırakma → grup ataması → e-posta.
- **adim_sayisi:** sunucu otomasyonu: doğrulanamadı. akış otomasyonu tasarımı: 5.
- **on_hazirlik:** Hedef dizin ya da sistem; yetki modeli (kim hesap açabilir); grup adları; şifre politikası (parolayı ajan görmemeli); e-posta alıcısı; kapatma için bağlı kaynak devri.
- **kirildigi_yer:**
  - 02 §3 madde 4: hesap zaten var ya da yok; yetki yetersizliği; kapatmada devir.
  - F-SV-002: Entegrasyon kullanıcısı kilitlenmesi; giriş denetimi hariç tutulmuşsa NGUI User Login raporu boş görünür (önerilen).
  - 05 F-AK-004: Sistem hesapları yapılandırma öğelerinde görünmüyor; rol klasör üzerinde yetki almamışsa listede yok (doğrulanmış). Bu sunucu otomasyonu değil akış otomasyonu'ya ait ama yetki tuzağının benzeri.
- **forum_kaniti:** F-SV-002 (https://community.opentext.com/it-ops-cloud/automation-ctr/f/server-automation-discussions/534453/find-the-source-ip-of-incorrect-login) — önerilen. F-AK-004 (https://community.opentext.com/it-ops-cloud/oo/f/discussions/533381/system-accounts-not-showing-in-configuration-items-page) — doğrulanmış.
- **ajanla_yapilisi:**
  - Ajan talebi okur; hesap adı, grup ve hedef dışında bir şey istemez. Parola üretmez ya da görmez; kimlik sağlayıcının kendi akışına bırakır.
  - Mevcut hesap varsa işlemi durdurur ve sorar (kırılma).
  - Yetki modeli dışında (Super User gerektiren) bir işlem ise onay ister.
  - Hesap oluşturma ve grup atamasını denetim kaydı ile yapar.
- **olculebilir_fark:**
  - Elle: 5 adım + yetki kontrolü + bilgilendirme.
  - Harness: aynı; ek olarak "hesap var mı" kontrolü.
  - Ölçülecek: var olan hesap nedeniyle durma sayısı; yetkisiz deneme sayısı; bildirimin gönderilip gönderilmediği.

---

## T10. Uyum ve denetim (audit) karşılaştırması

- **talep:** "Bu 60 sunucu altın sunucuyla uyumlu mu, uyumsuzsa düzelt."
- **sa_oo_yolu (sunucu otomasyonu 10.60, 01 §1.6):**
  1. Referans sunucu ya da snapshot spesifikasyonu oluştur.
  2. Snapshot job çalıştır.
  3. Snapshot'ı audit kaynağı olarak seç.
  4. Audit'i çalıştır (audit policy ile).
  5. Sonuçları incele (uyumlu / uyumsuz).
  6. Uyumsuzlukları kurala göre remediate et (comparison-based remediation).
- **adim_sayisi:** 7 (remediation dahil).
- **on_hazirlik:** Referans sunucu güncel olmalı; snapshot spesifikasyonu; audit politikası; yetki.
- **kirildigi_yer:**
  - 01 §1.6 "Sık hata": referans snapshot güncel değil; audit kaynağı yanlış seçilmiş.
  - 01 §1.6 "Doğrulanamadı": Snapshot tabanlı audit için sunucu otomasyonu Client'taki tam menü adımları.
  - F-SV-014: ISO güvenlik uyumluluk içeriği eski sunucu otomasyonu'da yok; doğru paket ürün pazarında (doğrulanmış).
  - F-SV-011: CBT ile dışa aktarılan yamalar metadata eksikliğiyle içe aktarılamıyor; hedef Windows Patch Database'inde eksik olabilir.
- **forum_kaniti:** F-SV-014 (doğrulanmış), F-SV-011 (https://community.opentext.com/it-ops-cloud/automation-ctr/f/server-automation-discussions/529945/cbt-patch-import-fail-with-metadata-missing-error) — cevapsız.
- **ajanla_yapilisi:**
  - Ajan referans sunucunun snapshot'ının tarihini kontrol eder; eskiyse uyarır ve yenisini almayı önerir.
  - Audit sonuçlarını sunucu bazlı "uyumlu/uyumsuz/karşılaştırılamadı" üç sınıfta toplar.
  - Remediation'ı sınırlı bir kural kümesine göre önerir; uygulamadan önce onay ister.
  - Sonucu yorumlar ve sapmanın nedenini (hangi kural) yazar; denetim izini saklar.
- **olculebilir_fark:**
  - Elle: 6 adım + snapshot tazeliği kontrolü + sonuç ayrıştırma.
  - Harness: referans tazeliği ön kontrolü, tek rapor.
  - Ölçülecek: karşılaştırılamayan sunucu sayısı; referansın yaşı; remediation öncesi ve sonrası uyumlu oranı.

---

## T11. Yarıda kalan işi yalnız başarısız sunucularda yeniden denemek

- **talep:** "Dün çalıştırdığımız betik 37 sunucuda başarısız oldu, sadece onları tekrar çalıştır."
- **sa_oo_yolu:**
  - sunucu otomasyonu: kaynakta otomatik yeniden deneme davranışı yok (01 §2). "Sadece başarısızlar" tek adımı sunucu otomasyonu arayüzünde **doğrulanamadı**. Pratik yol: başarısız sunucuların listesini al (sunucu bazlı çıktıdan) ve yeni bir iş için Include olarak ver.
  - akış otomasyonu (tasarım): REST ile yürütmeyi listele, durum oku, devam ettir (resume) ya da iptal (cancel). Resmi REST uç noktası ve parametreleri **doğrulanamadı**; 02 §4 ve §2'deki ayrıntılar üçüncü taraf Kestra eklentisinden.
- **adim_sayisi:** sunucu otomasyonu elle: 3 (liste, yeni iş, izleme). akış otomasyonu: 2 (REST, doğrulanamadı).
- **on_hazirlik:** Önceki işin kimliği; başarısız sunucu listesi; betiğin idempotent olduğu (aynı betik iki kez çalışınca zarar vermemeli).
- **kirildigi_yer:**
  - 01 §2 "Now" ve "Runtime": grup üyeliği iş tanımlandığında (Now) ya da çalıştığında (Runtime) farklı olabilir. Önceki koşudaki listeyi yeni koşuda aynı grupla tekrar çalıştırmak, aradaki değişikliği ve başarılı sunucuları ikinci kez hedefleyebilir.
  - 01 §2 "Doğrulanamadı": kısmi başarısızlık sonrası "sadece başarısızlar" tek adımı.
  - 05'te yeniden deneme vakası doğrudan yok.
- **forum_kaniti:** Doğrudan vaka yok; 05'te bu talebe ilişkin forum cevabı bulunamadı.
- **ajanla_yapilisi:**
  - Ajan önceki koşunun sunucu bazlı sonucunu okur ve başarısız listesini çıkarır.
  - Listeyi sabit (Now) hedef olarak yeni işe verir; grup ifadesi değil, sunucu kimlikleri kullanılır.
  - Yeni koşu başlamadan önce betiğin idempotent olduğu kayıt altında olmalı; değilse dur ve sor.
  - Yeniden deneme sayısını sınırlar (örneğin iki); sınır aşılırsa insana devreder.
- **olculebilir_fark:**
  - Elle: 3 adım, ama liste çıkarma hatalı olabilir.
  - Harness: başarısız liste ile yeni hedef eşleşmesi raporlanır; "başarılı olanlar tekrar çalıştı mı" sayısı 0 olmalı.
  - Ölçülecek: ikinci koşuda yanlışlıkla hedeflenen başarılı sunucu sayısı; yeniden denemeden sonra başarısız kalan sayısı.

---

## T12. Akış ortasında beklenmeyen çıktı gelince akışı düzeltmek

- **talep:** "Akış üçüncü adımda beklenmeyen bir yanıt döndürdü, akışı çalıştırmaya devam et ya da düzelt."
- **sa_oo_yolu:**
  - sunucu otomasyonu: betik çıkış kodu sıfır değilse hata (01 §2 adım 8); çıktı saklama sınırı (Retain) büyük çıktıyı kesebilir (01 §2 adım 5). Akış düzeltme sunucu otomasyonu'nın yerleşik özelliği değil; genellikle yeni bir iş ile yapılır.
  - akış otomasyonu: CloudSlang akışında çıktı doğrulama (02 §1 "Validation"); hatalı YAML ya da eksik bağımlılık akışı işaretler. Karar adımı (decision) yalnız bir sonraki adımı hesaplar (02 §1 "Transition"). Hata yolunun tam davranışı Navigation sayfasında açıklanmıyor (doğrulanamadı).
  - akış otomasyonu tasarımı (02 §3 madde 15 ve 02 §5 öneri niteliğinde): kırılma sonrası düzeltme onaylı bir dalla yapılır; bu, belgeli bir akış otomasyonu özelliği değil, tasarım önerisidir.
- **adim_sayisi:** 2 (sunucu otomasyonu, çıktı kontrolü). akış otomasyonu: 5 (tasarım).
- **on_hazirlik:** Her adımın çıktı şeması (beklenen alanlar, türler); hata durumunda hangi çıktı alanı dolu olacağı (05 F-AK-017 önerisi: hata mesajı için ayrı çıktı alanı); fonksiyon sürüm uyumluluğu.
- **kirildigi_yer:**
  - F-AK-007: Belgelenmiş `check_empty()` Workflow Designer'da yok; boş değişkende `eval(foo)["name"]` hata veriyor (doğrulanmış çözüm: Python ifadesi).
  - F-AK-002: Base content pack 1.24.3'te JSON Path geçersiz JSON döndürüyor; geri dönüş başka bir düzeltilmiş özelliği bozar (doğrulanmış, düzeltme sonraki sürüme bırakıldı).
  - F-AK-003: Değişken sayıda girdi (**kwargs) için kesin çözüm yazılmadı; yazar JSON dizisi ile geçici çözüm yaptı.
  - F-AK-001: Eski content pack sürümü yeni akış otomasyonu'da desteklenmiyor olabilir; hata iletisi (null) pakete işaret etmiyor.
- **forum_kaniti:** F-AK-007 (https://community.opentext.com/it-ops-cloud/oo/f/discussions/533115/why-dies-the-documented-function-check_empty-in-cloudlsang-doesnt-t-work) — doğrulanmış. F-AK-002 (https://community.opentext.com/it-ops-cloud/oo/f/discussions/534502/json-path-operation-returns-invalid-json-in-afl-base-content-pack-1-24-3) — doğrulanmış. F-AK-017 (https://community.opentext.com/it-ops-cloud/oo/f/discussions/530644/return-message-as-flow-output-field-on-error) — önerilen.
- **ajanla_yapilisi:**
  - Ajan her adımın çıktısını şemayla karşılaştırır; uymuyorsa sonraki adımı çalıştırmaz (02 §5 kural 1).
  - Kendi başına dal yazmaz ya da beceriyi değiştirmez; sorunu, adımı, beklenen ve gelen çıktıyı insana sunar.
  - Onay sonrası düzeltme yapılırsa yeni sürüm kaydedilir, eski sürüm saklanır (02 §5 kural 2).
- **olculebilir_fark:**
  - Elle: çıktıyı okuyup akışı yeniden yazmak; birkaç saat (tahmin, doğrulanamadı).
  - Harness: şema ihlali anında durma; kaç adımın şemasız çıktıyla devam ettiği 0 olmalı.
  - Ölçülecek: yanlış devam sayısı; düzeltme için insana giden süre; sürüm kayıt sayısı.

---

## T13. Agent'ı kaldırmak ve sunucu otomasyonu kaydını silmek

- **talep:** "Şu sunucu hizmetten çıktı, sunucu otomasyonu agent'ını kaldır ve sunucu otomasyonu'daki kaydını sil."
- **sa_oo_yolu:**
  1. Hedefi tanımla ve yedek/çıkış planını onayla (bakım penceresi).
  2. Host'ta agent kaldırma betiğini çalıştır: forumda önerilen yol `/opt/opsware/agent/bin/agent_uninstall.sh` gecikmeli zamanlanarak (`at`) (doğrulanmamış öneri; Windows için zamanlanmış görev benzeri).
  3. sunucu otomasyonu'da cihazı decommission et; sunucu otomasyonu'nın kayıt silme API'si ile (forum: API ile tam kaldırma yok).
- **adim_sayisi:** 3 (önerilen, doğrulanmamış).
- **on_hazirlik:** Bakım penceresi; ajanın kaldırılmasından sonra iletişim kesileceği için betiğin ajan dışından zamanlanması; kayıt silme onayı.
- **kirildigi_yer:**
  - F-SV-001: Unregister/decommission API'si yalnız sunucu otomasyonu veritabanı kaydını kaldırır; host'taki yazılımı kaldırmaz. Betik doğrudan çalıştırılırsa agent kendi bağlantısını keser, iş başarısız olur.
  - 01 §1.3 ve 05 F-SV-001 arasında ayrıntı tutarlı, ama çözüm doğrulanmamış.
- **forum_kaniti:** F-SV-001 (https://community.opentext.com/it-ops-cloud/automation-ctr/f/server-automation-discussions/534683/api-to-uninstall-delete-sa-agent) — doğrulanmamış öneri; forumda API ile tam kaldırma yok denmiş.
- **ajanla_yapilisi:**
  - Ajan bu talebi yıkıcı kabul eder; her adım için onay ister.
  - Betiği ajan bağlantısından bağımsız zamanlar ve zamanlamanın çalıştığını doğrular (kaldırma günlüğü ve kurulum dizini yokluğu).
  - sunucu otomasyonu kaydını ancak host kaldırıldıktan sonra siler.
  - Sonucu üç kanıtla raporlar: host'ta dizin yok, günlük var, sunucu otomasyonu'da durum "decommissioned".
- **olculebilir_fark:**
  - Elle: 3 adım, doğru sırada yapılmazsa ajan kaybı.
  - Harness: sıra ve onay kapısı sabit; kanıt üçlüsü.
  - Ölçülecek: yanlış sırada yapılan işlem sayısı (0 olmalı); kaydı silinmiş ama host'ta kalan ajan sayısı.

---

## sunucu/akış'nun hâlâ değerli yanları

Bu özellikler harness'in yerine geçmez; ajanın bunları sağlaması gerekir.

- **Denetim izi:** sunucu otomasyonu Command Engine çağrılarını güvenli iletir ve Model Repository'de denetlenebilir (01 §4.3, 10.60 mimari sayfası). "Kim, neyi, hangi sunucuda, ne zaman" sorusuna ürünün kendi kaydı var. akış otomasyonu'da da koşu kaydı ve yetki yapıları yerleşik (02 §5).
- **Yetki ayrımı:** sunucu otomasyonu'da customer, facility, device group ve job/script yetkileri ayrı tanımlanır; Super User ve "Run Ad hoc & Saved Scripts As Super User" gibi sınıflar var (01 §1.12, 01 §2 adım 3). akış otomasyonu'da rol ve klasör yetkisi, "alt öğelere uygula" işaretiyle (05 F-AK-013, F-AK-004).
- **Onay akışı:** sunucu otomasyonu'da iş "Pending Approval" durumuna alınabilir ve sunucu otomasyonu dışı bir onay gelene kadar bekler (01 §2 adım 8). Bu, insan onay kapısı için belgeli bir nokta.
- **Uyum döngüsü:** Snapshot, audit ve comparison-based remediation (01 §1.6, 10.60). Ajansız araçlarda bu derinlik yaygın değil (01 §4.3, karşılaştırma; kaynakla destekli ama rakiplerin tam matrisi doğrulanmadı).
- **Ölçek ve dayanıklılık:** Multimaster Mesh, satellite ve HA dokümanları (01 §1.11).
- **Sürümlü içerik:** akış otomasyonu content pack sürümü ve doğrulama (02 §1 Validation); sunucu otomasyonu yazılım politikasının test-üretim ayrımı (01 §1.5).

---

## Abartılı ya da az kullanılan özellikler

Yalnız kaynakla desteklenen yargılar yazıldı. Desteği olmayan iddia yazılmadı.

- **Export All Results (sunucu otomasyonu):** ZIP ve CSV çıktısı var (01 §2 adım 9). XML yok. Rapor için CSV ya da ham metin kullanılır; biçim dönüşümü ayrı bir adım.
- **Server Group Calculation: Runtime (sunucu otomasyonu):** Belgede var (01 §2 adım 1), ama "Allow Run Refresh Jobs" yetkisi gerektiriyor. Az kullanılan ya da yetki eksikliğinde çalışmayan bir seçenek olabilir (doğrulanamadı: yaygınlık).
- **Show output in table (sunucu otomasyonu):** Çıktıyı sütunlara ayırır (01 §2 adım 9); biçim belgesi sınırlı.
- **Parallel run (sunucu otomasyonu):** `way.server_script.run_read_only_scripts_in_parallel` ve `batchbot.max_concurrent_scripts` parametreleri var; varsayılan değerleri doğrulanamadı (01 §2).
- **sunucu otomasyonu API çeşitliliği:** SOAP, Pytwist, Java RMI ve CLI var; 10.60'ta Java ve Python stub'ları yok (01 §1.10). Hangi yolun kullanılacağı sürüme göre değişiyor.
- **Twister API (sunucu otomasyonu 24.1):** Varsayılan kapalı; `twisterEnabled=true` ile açılıyor ama yeniden başlatma gerekip gerekmediği forumda netleşmedi (05 F-SV-015).
- **akış otomasyonu Community General Utilities (topluluk paketi):** Export Reports Data, Single Worker gibi yardımcılar; destek yalnız topluluk forumlarından, OpenText Software Support kapsamında değil (02 §1). Üretimde kullanılacaksa kapsam dışı risk olarak görülmeli.
- **akış otomasyonu Designer ile Studio arası:** Akışlar birbirini okuyamaz ve düzenleyemez (02 §1, CSA 4.90). Kullanıcılar ikisini karıştırırsa uyumsuzluk çıkar.
- **akış otomasyonu RAS konumu:** Studio ve RAS aynı sunucuda değilse ya da localhost kullanılırsa akışlar kırmızıya dönebilir (02 §1; belge sürümleri arasında tutarlı).
- **sunucu otomasyonu Global Shell (rosh):** Sunucuda jump ve reach modları, `-s` ile kayıtlı OGFS betiği (01 §1.9). Komutun tam seçenek tablosu doğrulanamadı.
- **Yorum kaynakları:** Rakip ve kullanıcı puanları (PeerSpot, TrustRadius, Gartner) küçük örneklemli ya da eski dönemli (02 §5). Bu belgede karar için kullanılmadı.
- **Forum sağlık gözlemi (05, DCA bölümü):** sunucu otomasyonu forumunda okunan 26 konunun 22'si kilitli. Bu bir forum gözlemi; ürün kalitesi hakkında doğrudan kanıt değil.

---

## Harness için not

- Her talepte "ajanın kendisi çözdüğü" ve "onay gerektiren" adımlar ayrı işaretlenmeli; yıkıcı işlemler (T7 restart, T8 silme, T9 Super User, T10 remediate, T13 kaldırma) için insan onayı bağlanmalı.
- Kısmi başarısızlık her talepte açıkça raporlanmalı; "tüm sunucular" yazan özet, başarısızları gizlememeli.
- Belgede olmayan adımlar (XML dışa aktarma, ad kalıbı kuralı, disk temizlik işi, kullanıcı oluşturma, yeniden deneme tek adımı) harness içinde kendi betiğiyle doldurulmalı; sunucu otomasyonu'da olduğu varsayılmamalı.
