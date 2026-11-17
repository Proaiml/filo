# Filo: özellik haritası ve eksik listesi

Tarih: 2026-11-17. Girdi: `docs/arastirma/08-sunucu-ozellik-envanteri.md`, `09-akis-ozellik-envanteri.md`, `09b-akis-api-ve-yonetim.md`, `09c-akis-icerik-ve-sorunlar.md`. Filo durumu: `docs/00-devir-notu.md`, `docs/ilerleme.md` (son bölüm), `skills/*/beceri.json` (23 beceri, 5 betik, 3 dağıtım dosyası), `filo/` modüllerinin başlık açıklamaları.

Bu belge okuma anının görüntüsüdür. Depoda başka bir ajan çalışıyor (Go ajanı, teslim politikası, inisiyatif düzeyi, beceriye dönüştürme eklendi); o modüller de burada okundu, ama kod ayrıntısı taranmadı.

Atıf biçimi: `08§3#n` = 08 dosyasında 3. bölümün n. maddesi (sunucu otomasyonu yetenek listesi); `09§3#n` = 09 dosyasında 3. bölümün n. maddesi (akış otomasyonu). `09§2.4`, `09b§2.2` gibi atıflar bölüm başlıklarını gösterir. Öncelik: 1 çekirdek, 2 sık, 3 seyrek, 4 niş. Durum: var = Filo'da karşılığı çalışıyor; kısmi = bir parçası var; yok = karşılığı yok.

---

## 1. Özet

**İncelenen yetenekler.** sunucu otomasyonu 183 yetenek (`08§3`). akış otomasyonu 151 yetenek (`09§3` 148 madde + `09b§6`'dan 3 ek madde). `09§3`'te 87-94 ve 87-140 numaraları çakışıyor; sayım konu bazında yapıldı. Ayrıca `09c`'de yaklaşık 130 sorun giderme ve sürüm satırı, `08` ve `09b`'de yaklaşık 130 REST uç noktası ve 40 CLI komutu var. Bunlar yetenek sayısına girmedi; aile tablosunda ve bench adaylarında kullanıldı.

**Madde durumu (334 yetenek).**

| | var | kısmi | yok | toplam |
|---|---|---|---|---|
| sunucu otomasyonu (`08§3`) | 3 | 39 | 141 | 183 |
| akış otomasyonu (`09§3` + `09b§6`) | 14 | 42 | 95 | 151 |
| Toplam | 17 | 81 | 236 | 334 |

**Aile durumu (36 aile, bölüm 2).** var 4, kısmi 17, yok 15.

**Yorum.** Filo bugün en iyi şekilde tek seferlik sunucu işlerinde çalışır: komut, onaylı betik, dosya dağıtımı, paket kurulumu, servis, ajan kurulumu ve denetim izi. Boşluk üç yerde yoğunlaşıyor: akış motorunun yapıları (döngü, alt akış, duraklatma, devretme), sunucu/akış'nun toplu bakım işleri (yama, uyum, zamanlama, politika) ve kurumsal kimlik ile yetki modeli. Bulut, ITSM, ağ ve sanallaştırma tarafı tamamen boş.

**En önemli 10 eksik.**

1. ~~Yazılım politikası ve remediation~~ (dördüncü tur; kurulum sırası ve politika betikleri eksik) (aile 07).
2. ~~Yama yönetimi~~ (dördüncü tur, Linux; Windows yaması eksik) (aile 08).
3. ~~Uyum denetimi ve düzeltme~~ (dördüncü tur) (aile 09).
4. ~~Zamanlama ve bakım penceresi~~ (üçüncü tur) (aile 18).
5. ~~Akış yapıları~~ (üçüncü tur) (aile 28).
6. ~~Duraklat, sürdür, devret ve adımdan devam~~ (üçüncü tur; kayıt temizleme eksik) (aile 29).
7. Rol, izin ve müşteri (kiracı) modeli: yok (aile 15).
8. Kurumsal kimlik ve sertifika: LDAP, SAML, TLS yok (aile 16).
9. Yapılandırma şablonu ve sapma izleme: yalnız düz dosya kopyalanıyor (aile 11).
10. ~~Anlık görüntü ve karşılaştırma~~ (dördüncü tur) (aile 10).

**Üçüncü tur (17 Kasım 2026).** Bölüm 3'te zamanlayıcı, bakım/yasak pencereleri, duraklat/sürdür/iptal/devret, adımdan devam, akış yapıları (dal, sunucu dalı, döngü, paralel, alt akış, bekleme, onay, bildirim) ve çalıştırma kimliği satırları güncellendi ("üçüncü tur" diye işaretli). Bölüm 1 sayıları ilk okumanın görüntüsüdür, yeniden sayılmadı.

**Dördüncü tur (17 Kasım 2026).** Aile 07 (yazılım politikası), 08 (yama), 09 (uyum), 10 (anlık görüntü) ve 06/12 satırları güncellendi. "En önemli 10 eksik"ten kapananlar: 1 (yazılım politikası; kısmi: sıra/betik yok), 2 (yama; Linux), 3 (uyum), 4 (zamanlama, üçüncü tur), 5-6 (akış yapıları, duraklat/devret, üçüncü tur), 10 (anlık görüntü). Açık kalanlar: 7 rol/izin/kiracı, 8 kurumsal kimlik ve sertifika, 9 yapılandırma şablonu (Application Configuration: şablon + değer kümesi; bugün yalnız kütüphane dosyası ve içerik özeti var). Laboratuvar yerel paket deposuna geçti (internetsiz). Ayrıntı: `docs/ilerleme.md` "Dördüncü tur".

**Önemli not.** `09` ile `09b` duraklatma ve devretme konusunda çelişiyor. Bu belgede duraklatma, sürdürme, iptal, devretme ve gated geçiş "var" kabul edildi, çünkü `09b` bunları kaynak sayfa adlarıyla veriyor. Ayrıntı bölüm 8'de.

---

## 2. Beceri aileleri haritası

Her aile, ürün adından bağımsız bir genel beceri ailesi. Kapsadığı sunucu/akış maddeleri `08§3` ve `09§3` numaralarıyla gösterildi.

| aile | kapsadığı sunucu/akış özellikleri (kaynak) | Filo karşılığı | durum | genelleştirilmiş beceri önerisi | öncelik | lab uygunluğu |
|---|---|---|---|---|---|---|
| 01 Hedefleme ve gruplar | sunucu otomasyonu: statik ve dinamik cihaz grubu, dinamik grubu statiğe çevirme, grup üyeliği (`08§2.6`, `08§3#47-48`, `#111-113`) | `envanter.py` hedef seçici (ad kalıbı, grup, öznitelik, işletim sistemi, aile, dışlama); hedef dondurma. Dinamik kural ve yeniden hesaplama yok | kısmi | `hedef_grup_yonet`: grup oluştur, üye ekle ve çıkar, kuralla hesapla, statiğe çevir. Girdi grup adı ve kural ya da üye listesi. Risk 1 | 1 | evet |
| 02 Sunucu envanteri ve öznitelikler | sunucu otomasyonu: Device Explorer, özel alan ve öznitelik, Namespace, extensible discovery (`08§2.2`, `08§3#47`, `#49-50`) | `envanter.py` öznitelik alanları; `sistem_envanteri` (işletim sistemi, çekirdek, işlemci, bellek, disk, çalışma süresi). Özel alan ve namespace yok | kısmi | `sunucu_ozniteligi_yaz` (ad, ad alanı, değer; yerel envanter) ve `envanter_sorgu` (filtreli okuma, çıktı biçimi). Keşif betikleri `betik_calistir` ile | 1 | evet |
| 03 Toplu komut ve betik çalıştırma | sunucu otomasyonu: Run Script (çalışma kullanıcısı, zaman aşımı, salt-okur betiklerin paralel çalışması), betik kütüphanesi (`08§2.2`, `08§3#51`, `#114-116`) | `betik_calistir` (onaylı kütüphane), `komut_calistir` (salt-okur), `yurutme.py` paralel çalıştırma. Öznitelik ikamesi yok | var | Çalıştırma kimliği (root / kullanıcı, sunucu/grup başına izinli kimlik) üçüncü turda eklendi (bütün uzak becerilerde). Eklenecek: `komut_calistir` için onaylı yazma kipi (aile 04) | 1 | evet |
| 04 Uzak kabuk ve tek komut | sunucu otomasyonu: Global Shell (aaa, rosh, bash ve diğer kabuklar), uzak terminal (`08§2.2`, `08§3#52-53`, `#117-118`) | `komut_calistir` yalnız salt-okur izin listesinde. rosh ve etkileşimli terminal yok | kısmi | `komut_calistir` için onaylı yazma kipi (risk 3). Dosya okuma için salt-okur `dosya_oku`. Etkileşimli terminal alınmaz (bölüm 5) | 2 | evet |
| 05 Dosya dağıtımı ve kütüphane | sunucu otomasyonu: dosya kütüphanesi ve dağıtım, OGFS dosya görünümü (`08§2.6`, `08§3#5`, `#52`) | `dosya_dagit` (kütüphane dosyası, hedefe kopya, `.filo-yedek`, özet doğrulama). Ajan dosya alma | var | `dosya_geri_al`: yedekten geri yükleme, özet doğrulama (risk 2) | 1 | evet |
| 06 Paket kur, kaldır, doğrula, onar | sunucu otomasyonu: ad-hoc yazılım kurulum ve kaldırma, paket türleri (RPM, RPM modülü, Solaris IPS ve SVR4, Ubuntu, Windows MSI, ZIP), paket içe aktarma (`08§2.2`, `08§3#68`, `#70`, `#125-126`, `#173`) | `paket_kur` (apt-get, dnf, apk), `paket_dogrula`, `paket_onar`, `depo_onar` (dördüncü turda kurum standardına döner, RHEL dahil). Kaldırma ve sürüm sabitleme yazılım politikası remediation'ında (`paket_kaldir`, `paket_surum` eylemleri). Windows, Solaris, HP-UX paket türleri yok | kısmi | `paket_kaldir` (risk 3). Paket yöneticisi farkı beceri içinde çözülür. Solaris ve HP-UX adaptörleri sonra | 1 | kısmi (Debian, Alma, Alpine evet; Solaris ve HP-UX hayır) |
| 07 Yazılım politikası ve remediation | sunucu otomasyonu: yazılım politikası ve şablonu, 3 aşamalı remediation (analiz, indirme, kurulum), kurulum sırası, reboot ve pre/post betik, düşük disk kontrolü (`08§2.2`, `08§2.6`, `08§3#67`, `#69`, `#167-171`) | Dördüncü tur: `yazilim_politikasi.py` — sürümlü istenen durum (atamalar, paketler kurulu/yok + sürüm, servisler, kullanıcılar, kütüphane dosyaları), sapma taraması, önizleme, yalnız farkı kapatan idempotent remediation (aşamalı, test grubu), geri alma; talepten politika (dar listeler, kod denetimi); teslim profilleri bu nesneyi kullanır. Kurulum sırası, politika içinde ön/son betik, düşük disk denetimi yok | kısmi | Eklenecek: politika içinde ön/son betik ve kurulum sırası; disk alanı ön denetimi; indirme ve kurulumun ayrı zamanlanması | 1 | evet (Linux paketleri, yerel depo) |
| 08 Yama yönetimi | sunucu otomasyonu: Windows, Solaris, Ubuntu ve Debian, RHEL errata ve kanal, SUSE, diğer Unix ve HP-UX yamaları; tarama, politika, kurulum, kaldırma, uyum, zamanlama (`08§2.2`, `08§2.6`, `08§3#54-60`, `#108-109`, `#119-124`, `#148-162`) | Dördüncü tur: `yama.py` — `yama_durumu` (bekleyen, güvenlik sınıfı: Debian güvenlik deposu / RHEL updateinfo / Alpine secdb, yeniden başlatma gereği), yama politikası (hedef, kapsam, gerekçeli/süreli hariç tutma ve istisna, test grubu, yeniden başlatma politikası), `yama_uyumu`, `yama_uygula` (kuru önizleme, aşamalı, ön/son kontrol + otomatik geri iniş, asla/gerekirse/bakım penceresinde yeniden başlatma), `yama_geri_al`, `sunucu_yeniden_baslat`; laboratuvarda yerel paket deposu. Windows/Solaris/HP-UX yaması yok | kısmi | Eklenecek: Windows Update (WinRM), indirme/kurulum aşamalarının ayrı zamanlanması, yama kaldırma (paket değil yama kimliğiyle) | 1 | kısmi (Linux evet; Windows öykünme; RHEL errata ve Solaris yok) |
| 09 Uyum denetimi ve düzeltme | sunucu otomasyonu: audit kuralları, istisnalar, düzeltme eylemleri, özel betik kuralı, uyum eşiği, uyum panosu, pluggable check (`08§2.2`, `08§2.6`, `08§3#61-64`, `#127-129`, `#152`, `#176-178`) | Dördüncü tur: `uyum.py` — kural setleri (dosya/izin/içerik, paket/sürüm, servis, kullanıcı/grup, sysctl, port, salt-okur komut çıktısı), sunucu başına puan ve ihlaller, gerekçeli ve süreli istisna, düzeltme (yalnız geri alınabilir seçeneği), geri alma, konsolda Uyum sayfası (matris). Hazır CIS/ISO içerik paketi ve uyum eşiği yok | var | Eklenecek: hazır içerik paketleri (CIS benzeri), uyum eşiği ve alarm, zamanlanmış denetim örnekleri | 1 | evet |
| 10 Anlık görüntü ve karşılaştırma | sunucu otomasyonu: snapshot tanımı, kayıt, arşiv, dışa ve içe aktarma, zamanlanmış snapshot işi (`08§2.2`, `08§3#63`, `#130`, `#180`) | Dördüncü tur: `anlik_goruntu_al` (paketler, servisler, kullanıcılar, portlar, seçili dosyaların özeti/izni, sysctl) ve `goruntu_karsilastir` (altın sunucuya ya da kendi önceki görüntüsüne göre); konsolda iki görüntü karşılaştırması. Arşiv/dışa aktarma yok | var | Eklenecek: görüntü arşivi ve dışa/içe aktarma, görüntü saklama süresi | 2 | evet |
| 11 Yapılandırma şablonu ve sapma | sunucu otomasyonu: Application Configuration (CML ve XML/DTD şablonu, değer kümesi, push ve zamanlı push, out-of-sync, geri alma, audit) (`08§2.2`, `08§2.3`, `08§3#76-80`, `#96-97`, `#133`, `#145`, `#175-178`) | `dosya_dagit` düz dosya kopyalar. Şablon, değer, sapma ve geri alma yok | yok | `yapilandirma_uygula` (şablon ve değer kümesinden dosya üretir, önceki sürümü saklar; risk 2) ve `yapilandirma_sapma_denetle` (risk 0). Şablon dili: basit anahtar=değer ve YAML. CML'in tam dili alınmaz | 2 | evet |
| 12 Sunucu teslimi ve OS provisioning | sunucu otomasyonu: build plan, OS kurulumu (Debian, SLES, Windows, Solaris, ESXi), boot server, DHCP, UEFI Secure Boot, maintenance mode, provisioning sorun giderme (`08§2.2`, `08§2.5`, `08§3#65-66`, `#131-132`, `#181-183`) | `standart_sunucu_teslimi` ve `teslim.py`; dördüncü turda teslim profilinin değiştiren adımları bağlı yazılım politikasından üretilir (tek kavram). Bare-metal kurulum yok | kısmi | Teslim profillerinin genişletilmesi. `standart_sunucu_teslimi` korunur. Bare-metal kurulum için karar (bölüm 7, dalga 3) | 2 | kısmi (konteynerde işletim sistemi kurulumu yok; kayıt ve yapılandırma teslimi denenebilir) |
| 13 Ajan yaşam döngüsü | sunucu otomasyonu: ajan kurma (ADT, CLI, WSUS, üçüncü taraf mod), kaldırma, yükseltme, durum, tanı ve iletişim testi, agentsız keşif, agent yeniden sertifikalama (`08§2.1`, `08§2.2`, `08§3#13-14`, `#41-46`) | `ajan_kur`, `ajan_durumu`, `ajan_onar`, `ajan_kaldir` (var). Ajan yükseltmesi, anahtar döndürme ve agentsız keşif yok | kısmi | `ajan_yukselt` (risk 3, sürüm kaydı), `ajan_anahtar_dondur` (risk 3), `agentsiz_kesif` (risk 1, ağ taraması) | 1 | evet |
| 14 Hesap yönetimi | sunucu otomasyonu: kullanıcı açma, parola sıfırlama, gruptan çıkarma, pasif hesabı askıya alma, parola politikası (`08§2.1`, `08§3#1-2`, `#8-9`) | `kullanici_ac` (yerel hesabı açar, varsa dokunmaz). Parola, kilit, gruptan çıkarma ve silme yok | kısmi | `kullanici_yonet`: ekle, parola değiştir, gruptan çıkar, kilitle; silme risk 4. Parola modele ve kayda girmez | 2 | evet |
| 15 Rol, izin ve müşteri modeli | sunucu otomasyonu: süper yönetici, grup izinleri (eylem, kaynak, klasör, OGFS), müşteri ve müşteri grupları, kullanıcı ve güvenlik raporu (`08§2.1`, `08§2.6` izin tabloları, `08§3#3-7`, `#11`, `#39-40`). akış otomasyonu: RBAC rolleri, içerik izinleri, Designer klasör izinleri (`09§3#33`, `#39`; `09b§4.1`) | Yok. Konsol 127.0.0.1'de girişsiz çalışır. Politika onaylayan kimliğini yazar, rol modeli yok | yok | Beceri değil, çekirdek: rol, izin (beceri x hedef grubu x risk), kiracı (müşteri = hedef grubu + kimlik profili). Kalfa ve Kaptan bu tabloya bakar | 2 | evet (kod içi sınama) |
| 16 Kimlik doğrulama, sertifika ve sıkılaştırma | sunucu otomasyonu: LDAP, SAML, RADIUS, CAC, SecurID, core sertifika yenileme, iç iletişim TLS (`08§2.1`, `08§3#10`, `#13`). akış otomasyonu: LDAP, SAML, LW-SSO, OAuth, TLS sürümü, HTTPS yönlendirme, istemci sertifikası, jarsigner (`09§2.2`, `09b§4.2`, `09b§4.8`) | Ajan kanalında imza, zaman damgası, nonce ve tek kullanımlık kayıt belirteci (var). Konsol girişi, LDAP, TLS ve sertifika yok | yok | Çekirdek: LDAP bağlama ve kimlik sağlayıcı adaptörü; ajan kanalı için TLS. `sertifika_yenile` (risk 3, hedef sunucu TLS) | 2 | kısmi (LDAP konteyneri kurulabilir; CAC ve SAML sağlayıcı yok) |
| 17 Kimlik bilgisi kasası ve sistem hesapları | sunucu otomasyonu: envanterde ayrı kalem yok (parola politikası için bkz. aile 14). akış otomasyonu: sistem hesapları, sistem özellikleri, parola gizleme, CyberArk (`09§3#53`, `09b§4.8`, `09c` genelleştirilmiş aile 11, `09§2.8` CyberArk) | `ayarlar/kimlikler.json` (profil adı); anahtar ortam değişkeninde ya da `gizli.json`'da; denetim izinde maskeleme. Kasa adaptörü yok | kısmi | Çekirdek: `kimlik_profili` ve kasa adaptörleri (ortam değişkeni, dosya, sonra CyberArk). Beceri girdisine yalnız profil adı girer | 1 | evet (dosya ve ortam değişkeni); CyberArk hayır |
| 18 Zamanlama ve bakım penceresi | sunucu otomasyonu: zamanlanmış yama, yazılım, audit, snapshot, AC push ve iptal (`08§3#69`, `#77`, `#119`, `#133`, `#150`, `#180`). akış otomasyonu: akış zamanlaması, tek sefer ve tekrarlı, zamanlamayı etkinleştirme ve silme (`09§3#12`, `#34`; `09b§2.1` Schedules). Envanterde "blackout" kavramı yok | Üçüncü tur: `zamanlayici.py` (tek/tekrarlı/cron/bakım penceresi, kalıcı, kaçırılan koşu, önceden onay), bakım ve yasak pencereleri, talepten zamanlama; arayüzde iki sayfa. Pencere sonunda adımı durdurma yok | var | Çekirdek `zamanlayici`: tek sefer ve tekrarlı iş, iş kaydı, onay. `bakim_penceresi` kısıtı: pencere dışında başlamaz, pencere sonunda kalan adım durur | 1 | evet (konteyner içi zamanlayıcı) |
| 19 Bildirim ve rapor | sunucu otomasyonu: bildirim yapılandırması, iş e-postası, sunucu otomasyonu Client raporları (`08§2.1`, `08§2.2`, `08§3#91`, `#103`). akış otomasyonu: sistem e-postası, Dashboard, Insights ve ROI, OPTIC (`09§2.2`, `09§3#37-38`, `#48`, `#90`; `09b§4.5`) | `rapor.py` (CSV, XML, JSON, HTML), `eposta_gonder`, `sonucu_donustur`, teslim raporu e-postası. Olay kuralı, pano ve ROI yok | kısmi | `olay_bildirimi` (iş bitti, kısmi, başarısız olaylarında e-posta; risk 1) ve `pano_ozeti` (sonuç dağılımı; risk 0) | 1 | evet (Mailpit) |
| 20 Sanal makine ve bulut | sunucu otomasyonu: VM ve şablon yaşam döngüsü, vCenter, SCVMM, Solaris zone (`08§2.2`, `08§2.6`, `08§3#72-75`). akış otomasyonu: vSphere, Hyper-V, KVM, Nutanix, Citrix XenServer, AWS, Azure, Google Cloud, OCI, Alibaba (`09§2.8`, `09c` bölüm A, `09§3.5#87`, `#100`) | Yok | yok | Sağlayıcı başına beceri: `vm_olustur`, `vm_guc`, `vm_sablon`; bulut için `ornek_yonet` (risk 3-4). Sağlayıcı konektörü ayrı katman | 3 | hayır (hipervizör ve bulut yok) |
| 21 Bilet ve ITSM | akış otomasyonu: ServiceNow, Service Manager, Service Management (SMAX), OBM olay yanıtı, Cloud Management, change ve incident kayıtları (`09§2.8`, `09c` bölüm A, `09§3.5#89-93`) | Yok | yok | `bilet_ac`, `bilet_guncelle`, `bilet_kapat` (dış yazma, risk 2). ITSM adaptörü REST üzerinden | 3 | kısmi (sahte REST servisi konteynerde; gerçek ITSM yok) |
| 22 HTTP/REST ve web servisi çağrısı | sunucu otomasyonu: REST ve PowerShell REST ile sorgu (`08§3#92`, `#138`, `#140`). akış otomasyonu: REST ve Web Services sihirbazları, HTTP SSL el sıkışma sorunu (`09§2.5`, `09§3#87-88`, `09c` aile 2 ve `09c` C3 sslhandshakeerror) | Yok. Genel HTTP beceri yok; `gateway.py` yalnız model sağlayıcılarına bağlanır | yok | `http_istegi`: metot, adres izin listesi, başlık, gövde. GET risk 0, yazma risk 2. Token kimlik profilinden | 2 | evet (konteyner içi HTTP servisi) |
| 23 Veritabanı sorgusu ve bakımı | sunucu otomasyonu: core veritabanı karşılaştırma ve düzeltme araçları (`08§3#37-38`). akış otomasyonu: Oracle DB sorgusu, PostgreSQL sağlama, DB parola ve IP değişimi, DB temizliği (`09§2.8`, `09b§4.10`, `09§3.5#96-97`) | Yok | yok | `db_sorgu` (izinli sorgu listesi, salt-okur; risk 0) ve `db_bakim` (risk 3). Bağlantı bilgisi kimlik profilinden | 3 | kısmi (PostgreSQL konteyneri olur; Oracle ve SQL Server olmaz) |
| 24 Konteyner, IaC ve Ansible | sunucu otomasyonu: Ansible playbook, değişkenler, facts (`08§2.2`, `08§2.3`, `08§3#82-83`, `#134-135`). akış otomasyonu: Docker, Kubernetes, Terraform (`09§2.8`, `09§3.5#94-95`). sunucu otomasyonu Chef entegrasyonu 25.4'te kullanımdan kalktı (`08§4.1`) | `betik_calistir` ile elle. Ansible, Docker, Kubernetes, Terraform yok | yok | `ansible_calistir`: playbook kütüphanesi, envanterden envanter dosyası üretir, risk 3. `konteyner_yonet` ve `iac_uygula` (risk 3-4) sonra | 2 | kısmi (Ansible evet; Docker ve Kubernetes iç içe konteyner ister) |
| 25 Ağ cihazı, DNS-IP ve yük dengeleyici | akış otomasyonu: F5 BigIP, Infoblox, Efficient IP DDI, OpenNetAdmin, NNM, Network Automation, Network Operations Management (`09§2.8`, `09c` bölüm A, `09c` genelleştirilmiş aileler 5-6) | Yok | yok | `lb_havuz_guncelle`, `dns_kaydi`, `ag_cihazi_yedek` (risk 2-3). Cihaz API adaptörleri | 4 | hayır (ağ cihazı yok; sahte API ile kısmi) |
| 26 Yedekleme, DR ve HA | sunucu otomasyonu: core yedekleme ve geri yükleme, HA, DR, mesh (`08§3#32-33`, `#100-101`). akış otomasyonu: yedekleme, DR, Patroni HA, NetBackup (`09§2.2`, `09b§4.6-4.7`, `09§2.8` NetBackup) | `depo_onar` yedek bırakır (`/var/backups/filo-depo`). Filo'nun kendi verisi için yedek yok | yok | `yedek_al` (risk 1; arşiv ve özet), `yedek_geri_yukle` (risk 3, onay). Filo'nun kendi durum yedeği çekirdekte | 2 | evet |
| 27 Servis yönetimi ve sağlık denetimi | sunucu otomasyonu: core servis başlat, durdur, durum; HCM, sistem tanılama, bileşen log seviyesi, destek paketi (`08§3#25-27`, `#105-107`). akış otomasyonu: start/stop betiği, log seviyesi (`09b§4.5`) | `servis_durumu`, `servis_baslat`, `servis_yeniden_baslat` (var). `servis_durdur` yok. Destek paketi yok. `disk_durumu` ve `erisim_sinamasi` kısmi sağlık kontrolü | kısmi | `servis_durdur` (risk 3) ve `destek_paketi_topla` (risk 1; sistem envanteri, log parçaları, sır maskeleme) | 1 | evet |
| 28 Akış yapıları | akış otomasyonu: dallanma, sonuç adımları, paralel bölünme, çoklu örnek, döngü, alt akış, karar, yanıt kuralları, scriptlet, regex, girdi ve çıktı (`09§3#1-9`, `#17-24`, `#118-130`; `09§2.4`). sunucu otomasyonu: karşılığı yok | Üçüncü tur: `akis_motoru.py` yapılı akış sürüm 2 (dal, sunucu dalı, döngü, paralel kol, alt akış, bekleme, onay, bildirim, bitir; kodla şema doğrulaması), Kaptan'ın dar kararlarla kurması (`akis_kurucu.py`), tuvalde çizim; teşhis dalı sürüyor. Scriptlet/regex yok (tasarım) | var | Çekirdek düğümler: `dal`, `dongu`, `alt_akis`, `paralel_kol`. Regex ve scriptlet yerine beceri çıktı şeması | 1 | evet (bench senaryosu ile) |
| 29 Akış yürütme ve kayıt yönetimi | akış otomasyonu: Run Explorer, iptal, duraklat ve sürdür, devret, adımdan yeniden çalıştırma, zaman aşımı, persistence, run log, purge, rerun ve adım log silme (`09§3#10`, `#14-15`, `#30-32`, `#35`, `#75-80`; `09b§2.2`, `09b§3`). sunucu otomasyonu: iş kaydı ve arama, iş iptali, iş zaman aşımı, sunucu başına sonuç (`08§2.2` job log, `08§2.6` aktif işi sonlandırma, `08§3#136`, `#137`, `#172`, `#179`) | `isler.py` (iş kaydı, zaman çizgisi, canlı ızgara, JSON kayıt). `yurutme.py` (zaman aşımı, tek şema). Durdurma düğmesi tüm işleri keser. Üçüncü tur: duraklat, sürdür, iş bazlı iptal, devret, adımdan devam (kalıcı durum, konsol yeniden başlarsa sürer). Kayıt temizleme (purge) yok | kısmi | Çekirdek: `is_duraklat` ve `is_surdur` (adım sınırında), `is_devret` (sahip ataması), `adimdan_devam` (yalnız idempotent adımlarla), `kayit_temizle` (saklama süresi, denetim izi korunur) | 1 | evet |
| 30 İnsan onayı, kapılar ve inisiyatif | akış otomasyonu: gated geçiş (rol bazlı), handoff (girdi isteme), insan girdisi (`09§3#11`; `09b§2.2`, `09b§3`). sunucu otomasyonu: iş onayı envanterde ayrı kalem olarak yok (belirsiz). Bakım penceresi kullanım cümlelerinde geçer (`08§3#137`) | `politika.py`: risk 3-4 onay, onay kaydı, Onaylar sekmesi, `filo onay ver`. Kaptan inisiyatif düzeyi 0-3. Teslim politikasında ön onay. Rol bazlı kapı ve girdi isteme yok | kısmi | `onay_iste`: adımda insan girdisi ya da onay, cevap iş kaydına yazılır. Adım tanımında `onaylayan_rol` alanı; `politika.py` rol denetimi | 1 | evet |
| 31 Dağıtık yürütme altyapısı | sunucu otomasyonu: core, agent ve satellite mimarisi, satellite önbelleği ve mirror, peer cache, bant genişliği (`08§2.1`, `08§3#18-23`). akış otomasyonu: worker ve RAS grupları, robot grupları, topoloji, ters RAS, RAS yükseltme (`09§2.2`, `09§3#44-45`, `#137-138`; `09b§4.7`) | `yurutme.py` (eşzamanlılık sınırı, sunucu başına zaman aşımı, tek şema, erişim sınaması, durdurma düğmesi). `erisim.py` (SSH, WinRM, öykünücü). `ajan_kapisi.py` ve Go ajanı (imzalı kanal, yedekli taşıyıcı) | var | Çekirdek (beceri değil). Eklenecek: bölge (ağ segmenti) ve taşıyıcı profili. Satellite önbelleği alınmaz (bölüm 5) | 1 | evet (Linux); Windows WinRM kısmi |
| 32 Beceri kataloğu, sürümleme ve paketleme | akış otomasyonu: içerik paketi oluşturma, sürümleme (X.Y.Z), ortamlar arası terfi, içe ve dışa aktarma, akış kütüphanesi, SCM (`09§2.1`, `09§2.2` Promote, `09§3#57-61`, `#66-67`; `09c` bölüm B3-B4). sunucu otomasyonu: içerik kütüphanesi ve klasörler (`08§2.2` Kütüphane) | `skills/` kataloğu (beceri.json, sürüm, risk, geri alma, kuru çalıştırma). `beceri liste`, `goster`, `gecmis`, `fark`, `geri-al`, `sinifla` (var). Paket dışa aktarma, ortam terfisi ve SCM bağlantısı yok | kısmi | Çekirdek: `beceri_paketi` (beceri, betik ve dosyalardan imzalı arşiv; içe ve dışa aktarma), ortam terfisi (test'ten üretime, risk 2 onay). Sürümleme dış git deposuyla | 2 | evet |
| 33 Beceri üretme ve dönüştürme | akış otomasyonu: REST, Web Services, Shell, PowerShell ve üçüncü taraf paket sihirbazları (`09§2.5`, `09§3#68-70`, `#112`; `09b§5.3`; `09c` bölüm B). sunucu otomasyonu: yok | `donustur.py` (başarılı işten beceri; düz dil tarifinden taslak; sınama sunucusunda kuru çalıştırma; risk ve geri alma denetimi). Kaptan `beceriyi_degistir` (yeni sürüm) | kısmi | `openapi_beceri_uret` (tanım dosyasından taslak, sınama sunucusunda kuru çalıştırma) ve `komut_beceri_uret` (kabuk komutundan şema). `donustur.py` kaynak türleri olarak | 2 | evet (OpenAPI dosyası konteynerde) |
| 34 Dış API, CLI ve self-service yüzeyi | sunucu otomasyonu: REST, Pytwist, PowerShell API, sunucu otomasyonu CLI, OCLI (`08§2.3`, `08§2.5`, `08§2.6`, `08§3#36`, `#92-94`, `#139-141`). akış otomasyonu: REST API (yaklaşık 130 uç), akış komut aracı ve akış yönetim aracı, Self-Service X kataloğu, PA Mobile (`09§2.3`, `09§2.6`, `09§3#71-86`; `09b§2.1`, `09b§5`) | `python -m filo` CLI (talep, beceri, iş, bench, denetim, durdur). Web konsolu 127.0.0.1'de, JSON API, POST için `X-Filo` başlığı. Kimlikli dış API ve son kullanıcı kataloğu yok | kısmi | `filo_api` (kimlikli, izinli uçlar; talep ve iş durumu). Son kullanıcı kataloğu: beceri listesi ve talep formu, aynı onay kapısından geçer | 2 | evet |
| 35 Denetim izi | sunucu otomasyonu: sıkı denetim, dijital imzalı denetim izi, kullanıcı etkinlik kaydı, Global Shell denetim logları (`08§2.1`, `08§3#12`). akış otomasyonu: denetim yapılandırması ve kayıtları, audit events API (`09b§4.3`, `09§3#104`) | `denetim.py` (eklemeli JSON satırları, özet zinciri, alan maskeleme, `doğrula`). Sorgu ve dışa aktarma sınırlı | var | `denetim_sorgu` (tarih, iş, sunucu, beceri filtreleri; risk 0) ve `denetim_disa_aktar` (risk 1) | 1 | evet |
| 36 Ürün kurulumu, lisans ve ürün bakımı | sunucu otomasyonu: kurulum ve yükseltme planı, AutoPass, core yama ve bakım, HA kurulumu, kimlik değiştirme (`08§2.1`, `08§2.5`, `08§3#33`, `#41`). akış otomasyonu: kurulum ve yükseltme, lisans, başlangıç görevleri, IP ve DB parola değişimi, RAS yükseltme (`09§2.5`, `09§4.9`, `09b§4.4-4.10`, `09c` C2) | `lab kur`, `durum`, `sifirla`, `kapat`; kendi sürüm bilgisi. Ürün kurulumu ve lisans kavramı yok, çünkü Filo sunucu otomasyonu ve akış otomasyonu'yu yönetmez | yok | Filo'nun kendi kurulumu çekirdekte. sunucu otomasyonu ve akış otomasyonu ürün bakımı beceri olarak alınmaz (bölüm 5) | 4 | hayır |

---

## 3. Akış motoru ve çekirdek yetenekleri

Kaptan (akış otomasyonu karşılığı) ve çekirdek için. Yetenekler akış otomasyonu akış özellikleri ile sunucu otomasyonu iş özelliklerinden alındı. Kaptan bugün tek bir dinamik akış kuruyor ve hata olunca teşhis dalı çalıştırıyor. Diğer yapılar çekirdeğe eklenecek.

| yetenek | kaynak | Filo karşılığı | durum | önerilen tasarım |
|---|---|---|---|---|
| Dallanma (Success, Failure, Custom geçişleri) | `09§3#1-2`, `09§2.1` | `akis_motoru` `dal` (akış düzeyi: adım durumu/sayısı, değişken) ve `sunucu_dal` (başarılılar/başarısızlar ayrı kola); Kaptan'ın teşhis dalı ayrıca sürer | var (üçüncü tur) | Custom geçiş yerine koşul nesnesi; görsel geçiş yok |
| Sonuç adımları ve return | `09§3#3`, `#20` | Sonuç durumları: basarili, kismi, basarisiz, iptal | kısmi | Akış sonu sınıfları: cozuldu, teshis, islem_yok, hata (akış otomasyonu'nun yanıt türleri) |
| Paralel bölünme (adım kolları) | `09§3#4`, `09§2.4` | `paralel` düğümü: kollar aynı anda, hepsi bitince birleşme | var (üçüncü tur) | Kol başına ayrı hedef yok (aynı sunucu kümesi) |
| Çoklu örnek (hedef başına) | `09§3#5`, `09c` genelleştirilmiş aileler | `yurutme.py` sunucu başına paralel, eşzamanlılık sınırı | var | Mevcut. Adım başına eşzamanlılık ve hata izolasyonu beceri tanımına girer |
| Döngü (senkron ve paralel) | `09§3#6-7` | `dongu`: liste üzerinde ya da koşul sağlanana kadar; `en_cok` zorunlu (≤ 50); "hata olsa da devam" | kısmi (üçüncü tur) | Paralel döngü yok (çoklu örnek sunucu düzeyinde var) |
| Alt akış | `09§3#8`, `09§2.4` | `alt_akis`: kayıtlı sabit akış adım olarak, girdi/çıktı eşlemesi, döngü denetimi | var (üçüncü tur) | Çıktı eşlemesi yalnız değişken düzeyinde |
| Karar adımı | `09§3#118` | `dal` koşulu (şema alanı, adım sonucu, sunucu özelliği; Python ifadesi yok) | var (üçüncü tur) | — |
| Scriptlet ve regex | `09§3#17-18`, `#130` | Yok | yok | Çıktı ayrıştırma beceri `cikti` şemasında (anahtar_deger, satirlar). Scriptlet alınmaz |
| Girdi, çıktı ve atama | `09§3#21`, `#136` | Beceri girdi ve çıktı şeması, varsayılan değer | var | Mevcut. Akış düzeyi değişkenler için çekirdekte `baglam` sözlüğü |
| Sistem özellikleri ve sistem hesapları | `09§3#22`, `09c` aile 11 | `ayarlar/*.json`, kimlik profili (ortam değişkeni) | kısmi | `kimlik_profili` ve `ortam_degiskeni` çekirdek varlıkları |
| Duraklat ve sürdür | `09§3#10`, `09b§2.2` | `kontrol.py`: adım sınırında ve yelpazede sunucu başlamadan önce; durum kalıcı, konsol yeniden başlarsa kayıttan sürer | var (üçüncü tur) | Pencere sonunda otomatik duraklatma yok |
| İptal | `09§3#30`, `09b§2.2` | İş bazlı iptal (kalan sunucular/adımlar çalışmaz) + durdurma düğmesi | kısmi (üçüncü tur) | Çalışan uzak süreç iş bazlı iptalde öldürülmez |
| Devretme (reassign) | `09b§2.2`, `09b§6` #5 | `devret` (kime + not, iş sahibi, iş geçmişi); Kaptan insana devredince iş bekler, operatör kararı Kaptan'a girdi | kısmi (üçüncü tur) | Rol/izin modeli yok: kimin sürdürebileceği kısıtlanmaz |
| Gated geçiş ve insan onayı | `09§3#11`, `09b§3` | `politika.py` onay kapısı, inisiyatif düzeyi ve akışta `onay` düğümü (her düzeyde insan; reddedilirse bloğu) | kısmi (üçüncü tur) | `onaylayan_rol` yok |
| Girdi isteme (handoff) | `09b§2.2` | İnsana devirde operatör notu/kararı (yeniden_dene / kaptan / atla) | kısmi (üçüncü tur) | Serbest biçimli girdi formu (değişken isteme) yok |
| Zamanlayıcı | `09§3#12`, `09b§2.2` | `zamanlayici.py`: tek/günlük/haftalık/aylık/cron/bakım penceresi; kalıcı; kaçırılan koşu politikası; önceden onay | var (üçüncü tur) | Saat dilimi tek (yerel) |
| Rerun point ve adımdan devam | `09§3#15`, `09b§2.2` | `devam.py`: her tamamlanan üst düzey adım devam noktası; yalnız başarısızlarla ya da hepsiyle | var (üçüncü tur) | Bileşik düğümün içinden devam yok; adımların yeniden çalıştırılabilir olduğu varsayılır |
| Yeniden deneme | `09§3#14` | `deneme_siniri` (varsayılan 2) | var | Mevcut |
| Zaman aşımı ve persistence | `09§3#32`, `09c` | Zaman aşımı beceri ve sunucu başına; koşu durumu iş kaydında kalıcı (`devam`) | kısmi (üçüncü tur) | Akış düzeyinde toplam zaman aşımı yok |
| Görsel geçiş, flow map, çizim | `09§3#19`, `09§2.4`, `#60` | Yok | yok | Alınmaz (bölüm 5) |
| Worker, RAS ve robot grupları | `09§3#44-45`, `#137-138` | Ajan kapısı ve yedekli taşıyıcı. Grup yok | kısmi | Bölge ve taşıyıcı profili (aile 31) |
| Döngü kısıtı (sonsuz döngü) | `09§3#16` | `en_cok` zorunlu; şema doğrulaması üst sınırsız döngüyü reddeder | var (üçüncü tur) | — |
| Zamanlama (sunucu otomasyonu: yama, yazılım, audit, snapshot, AC push) | `08§3#69`, `#77`, `#133`, `#180` | Her beceri/akış zamanlanabilir (`zamanlayici`) | kısmi (üçüncü tur) | Yama/audit/snapshot becerileri yok; aşama zamanlama yok |
| İş onayı (sunucu otomasyonu) | Envanterde ayrı kalem yok (belirsiz) | `politika.py` onayı; zamanlanmış işte önceden onay (kim, ne zaman, tanım sürümü) | kısmi (üçüncü tur) | Onay kapısına bekleme süresi ayarı (30 dk sabit) |
| Bakım penceresi ve blackout (sunucu otomasyonu) | `08§2.6` aktif işi sonlandırma, `08§3#137`. Envanterde "blackout" yok | `Pencereler`: bakım ve yasak pencere, sunucu/grup kapsamı; yasakta değiştiren iş başlamaz (bekle/sor/atla); "bakım penceresinde çalıştır" | kısmi (üçüncü tur) | Pencere sonunda kalan adımın durdurulması yok |
| Bildirim (sunucu otomasyonu) | `08§2.1` sunucu otomasyonu bildirimleri, `08§3#103` | `eposta_gonder`, teslim e-postası | kısmi | Olay bazlı kural (aile 19) |
| İş kaydı ve arama (sunucu otomasyonu) | `08§2.6` iş günlüğü ve arama, `08§3#136` | `isler.py` zaman çizgisi, JSON kayıt. Arama yok | kısmi | İş kaydında alan ve metin filtresi |
| İş bloklama (akış otomasyonu ile) | `08§3#85` | Yasak pencere aynı işi görür | kısmi (üçüncü tur) | Elle bakım kilidi (anlık blok) ayrı yok; tek seferlik yasak pencere tanımlanır |
| Aşama zamanlama (indirme ve kurulum ayrı) | `08§2.2`, `08§3#119`, `#170` | Yok | yok | Politika aşamaları ayrı adım ve ayrı zamanlama (aile 07) |
| Hata işleme (kısmi başarısızlıkta devam) | `08§3#171` | `yurutme.py` kısmi başarısızlıkta sürer | var | Mevcut. "Hatada dur" seçeneği eklenir |

---

## 4. Kurumsal gereksinimler

| gereksinim | sunucu/akış karşılığı (kaynak) | Filo durumu | gereken en küçük karşılık |
|---|---|---|---|
| Yetki modeli: rol, müşteri ya da tesis, klasör izni | sunucu otomasyonu: grup izinleri, müşteri, klasör izni (`08§2.1`, `08§2.6`). akış otomasyonu: RBAC, içerik izinleri (`09b§4.1`) | yok | Rol ve izin tablosu (beceri x hedef grubu x risk) ve kiracı (grup + kimlik profili). Çekirdek (aile 15) |
| Kimlik doğrulama: LDAP, SAML | sunucu otomasyonu: LDAP, SAML, RADIUS (`08§2.1`). akış otomasyonu: LDAP, SAML, LW-SSO (`09b§4.2`) | yok. Konsol girişsiz, 127.0.0.1 | Konsol girişi (yerel parola veya OS kullanıcısı) ve LDAP bağlama adaptörü. 127.0.0.1 kısıtı sürer (aile 16) |
| Denetim | sunucu otomasyonu: sıkı denetim, imzalı denetim (`08§2.1`). akış otomasyonu: denetim kayıtları (`09b§4.3`) | var. `denetim.py` zinciri ve doğrulaması | Denetim sorgu ve dışa aktarma (aile 35). İz dosyasının yedeği |
| Yüksek erişilebilirlik | sunucu otomasyonu: mesh, HA veritabanı (`08§2.1`, `08§3#33`). akış otomasyonu: Patroni, RAS topolojisi (`09b§4.7`) | yok. Tek çekirdek, laboratuvarda tek kopya (`00-devir-notu`) | Çekirdek durumunun kopyası ve yeniden başlatmada yarım iş kurtarma. Tam HA alınmaz (bölüm 5) |
| Yedekleme ve DR | sunucu otomasyonu: core yedek ve DR (`08§3#32`). akış otomasyonu: yedek, DR (`09b§4.6`) | kısmi. `depo_onar` yedeği, Filo verisi için yok | `yedek_al`, `yedek_geri_yukle` (aile 26) |
| API | sunucu otomasyonu: REST, Pytwist, PowerShell, SOAP (`08§2.3`). akış otomasyonu: REST, akış komut aracı (`09b§2.1`, `09b§5`) | kısmi. CLI var, web JSON yerel | Kimlikli dış API ve sürümlü uçlar (aile 34). SOAP alınmaz (bölüm 5) |

---

## 5. Bilerek alınmayacaklar

Her madde için kaynak ve gerekçe verildi. Gerekçe ya kaynağın kendi kullanımdan kaldırma notu, ya da tasarım kararıdır. Tasarım gerekçesi olarak işaretlendi.

| özellik | kaynak | gerekçe |
|---|---|---|
| RPA Robot ve Recorder (UFT tabanlı GUI otomasyonu) | `09` bölüm 4; `09c` C0, C4, C7 | Kaynak kullanımdan kaldırma notu veriyor: 26.2.1'den itibaren kullanımdan kaldırılmış, yeni özellik gelmiyor. |
| SOAP API ve Perl/C# Web Services istemcileri, PowerShell SOAP | `08§2.3`, `08§2.6`, `08§4.1` | Kaynak: 25.4'te tümü kullanımdan kaldırıldı, REST yerine geçti. REST karşılığı aile 34'te. |
| Chef entegrasyonu (cookbook, Run Chef Recipe) | `08§2.2`, `08§4.1` | Kaynak: 25.4'te kullanımdan kaldırıldı. Yerine Ansible (aile 24). |
| Etkileşimli uzak terminal (sunucu otomasyonu Remote terminal, UNIX terminal ya da RDP penceresi) | `08§2.2`, `08§3#118` | Tasarım gerekçesi: insan etkileşimi. Ajan tek komut ya da onaylı betik çalıştırır (aile 04). |
| Sürükle-bırak akış çizimi, görsel geçiş özelleştirme, flow map | `09§2.1`, `09§2.4` (görsel geçiş "koşul ya da mantık değil"), `09§3#19`, `#60`, `09c` B5 | Tasarım gerekçesi: akış beceri şeması ve Kaptan'ın dinamik kurmasıyla yazılıyor. Çizim arayüzü ajanın işini değiştirmez. Salt izleme gerekirse konsolda gösterilebilir. |
| Designer dosya sistemi SCM protokolü, Studio içinde SVN | `09c` B3 | Kaynak: Designer dosya sistemi protokolü 2022.11'de kaldırıldı. Sürümleme Filo'da beceri kataloğu ve dış git ile yapılır (aile 32). |
| Ürün yerelleştirmesi (akış otomasyonu Studio'da Fransızca, Almanca, Japonca, İspanyolca, Çince) | `09c` B5 | Tasarım gerekçesi: arayüz Türkçe ve tek sayfa (`00-devir-notu`). |
| Desteği kalkmış platformlar: Ubuntu 14.04, 16.04, 18.04; OEL 6; RHEL 6; CentOS 7; AIX 7.1; Windows 8.1 ve 2012 x86_64; VMware ESX 6.5; HP-UX 11.31 PA-RISC ve IA-64 | `08§4.1`, `08§4.2`; `09c` C0 | Kaynak: 25.4 ve önceki sürümlerde yönetilen ya da desteklenen platformdan çıkarıldı. Filo hedef aile tanımı desteklenmeyen sürümü reddeder (bench B04). |
| Niş kimlik sağlayıcıları: CAC/PIV akıllı kart, RSA SecurID, RADIUS | `08§2.1` (niş) | Kaynak: niş olarak işaretli. Kurumsal ortama bağlı. LDAP ve SAML (aile 16) karşılar. Talep olursa adaptör eklenir. |
| Marketplace içerik akışı, Operations Platform, OPTIC ve DCA entegrasyonu | `08§2.4`, `09§2.8`, `09c` bölüm A | Tasarım gerekçesi: Filo sunucu otomasyonu ve akış otomasyonu'ya bağlı değil; bağımsız harness. |
| Ürün kurulumu, yükseltme ve ürün lisansı (AutoPass, kurulum planı, RAS yükseltme, başlangıç görevleri) | `08§2.1`, `08§2.5`; `09§2.5`, `09§4.9`; `09b§4.4-4.10` | Kaynak: Filo sunucu otomasyonu ve akış otomasyonu'yu yönetmez (`00-devir-notu`, 17 Kasım kararı). Filo'nun kendi kurulumu çekirdekte. |
| sunucu otomasyonu satellite önbelleği, mirror ve peer cache | `08§2.1`, `08§3#21-23` | Tasarım gerekçesi: sunucu otomasyonu'ya özgü dağıtım topolojisi. Ajan kanalı doğrudan çekirdeğe gider (aile 31). Küçük şube ihtiyacı doğarsa yeniden değerlendirilir. |
| akış otomasyonu Java ve .NET action yazımı, Jython operasyonu | `09§3#64`, `09§2.4` ("yeni Jython operasyonu oluşturulamaz") | Tasarım gerekçesi: Filo beceri dili shell ve Python. Kaynak: yeni Jython operasyonu oluşturulamıyor. |

---

## 6. Yeni bench senaryosu adayları

Her aday: talep (bir cümle), beklenen sonuç, kaynak. Mevcut 15 senaryo (T01-T04, O01-O06, I01-I05) ile çakışmıyor. Analog olanlar, kaynaktaki sorunun Filo'daki karşılığına çevrildi.

- **B01** Talep: Disk alanı dolu bir sunucuya `paket_kur` ile paket kur. Beklenen: kurulum başlamadan disk denetimi başarısız, sunucu hatalı, diğerleri sürer, sahte başarı yok. Kaynak: `08` bölüm 6 madde 14.
- **B02** Talep: Salt-okur komut kipinde yazan bir komut (`rm`, yönlendirme) çalıştır. Beklenen: komut reddedilir, sunucuya dokunulmaz, denetim izine düşer. Kaynak: `08§4.3` OCTCR19XW2721402 (analog).
- **B03** Talep: Ön kurulum betiği hata veren bir sunucuya ajan kur. Beklenen: `ajan_kur` geri alır, sunucu "kayıtsız" raporlanır. Kaynak: `08§4.3` OCTCR19XW2713861 (analog).
- **B04** Talep: Desteği kalkmış eski bir dağıtımda (Ubuntu 14.04 benzeri) ajan kur. Beklenen: aile tanınmaz ya da desteklenmez, iş başlamadan durur, neden raporlanır. Kaynak: `08§4.2`; `09c` C0.
- **B05** Talep: Kilitli bir dosya içeren geçici dizinde `gecici_dosya_temizle` çalıştır. Beklenen: kilitli dosya atlanır ve raporlanır, diğer dosyalar silinir, kalan doluluk gösterilir. Kaynak: `08` bölüm 6 madde 10 (analog).
- **B06** Talep: Süresi dolmuş bir kimlik profiliyle zamanlanmış betik işi çalıştır. Beklenen: iş kimlik hatasıyla durur, sahte başarı yok, denetim kaydı düşer. Kaynak: `08` bölüm 6 madde 8.
- **B07** Talep: Sürümü eski (0.1.0) bir ajanı olan sunucuda `ajan_onar` çalıştır. Beklenen: sürüm farkı tespit edilir, ajan yeniden kurulur ya da yükseltme önerilir. Kaynak: `08§4.3` OCTCR19L1058047 (analog); `ilerleme.md` (ajan sürümü).
- **B08** Talep: Aynı adla iki beceri içeren bir katalogla `kalfa`'yı çalıştır. Beklenen: katalog denetimi çift kimliği reddeder, hiçbir iş başlamaz. Kaynak: `09c` sorun giderme madde 2 ve C6 deployerror.
- **B09** Talep: Üç sunucuda betik çalıştır ve hepsi bitince iş kaydının kapandığını izle. Beklenen: iş bitti ya da kısmi ile kapanır, "çalışıyor" durumunda kalmaz. Kaynak: `09c` sorun giderme madde 3 (miflowsstuck).
- **B10** Talep: Bir sunucunun saat dilimi farklıyken zamanlanmış işin zaman damgalarını raporla. Beklenen: zaman damgaları tek dilimde tutarlı, rapor çelişmez. Kaynak: `09c` sorun giderme madde 4 (inconsistentstart).
- **B11** Talep: Ajan kapısının önüne kalp atışlarını kesen bir vekil koy ve iş gönder. Beklenen: ajan "yok" sayılır, iş SSH yedeğinden tamamlanır, hangi yolla gittiği raporlanır. Kaynak: `09c` sorun giderme madde 12 (workerregistration, analog); `ilerleme.md` (8 sn yedek).
- **B12** Talep: Hiçbir sunucuya uymayan bir hedef seçiciyle iş başlat. Beklenen: iş başlamaz, "hedef boş" durumu, sahte başarı yok. Kaynak: `09c` C4 norobots (analog).
- **B13** Talep: Yedeği bozulmuş bir dosyayı önceki sürüme geri al. Beklenen: özet uyuşmazlığı görülür, geri alma durur, bozuk yedek korunur ve raporlanır. Kaynak: `09c` C2 backupcorruption (analog).
- **B14** Talep: Kırık bağımlılığı olan bir paketi kur. Beklenen: `paket_kur` başarısız, `paket_onar` bir kez dener, olmazsa insana devredilir, sahte başarı yok. Kaynak: `08` bölüm 6 madde 15 (analog); `08§2.6` manuel yama.
- **B15** Talep: Yeni kurulan ajanın kalp atışı hiç gelmezse `ajan_kur` ne yapar? Beklenen: belirli bir zaman aşımından sonra ağ, kayıt ve ikili ayrımıyla teşhis edip durur. Kaynak: `08` bölüm 6 madde 2 (analog).
- **B16** Talep: Süresi dolmuş bir kayıt belirteciyle ajan kurmayı dene. Beklenen: kayıt reddedilir, temiz hata, ikili hedefte bırakılmaz. Kaynak: `ilerleme.md` (15 dakika geçerli belirteç); `08` bölüm 6 madde 5 (analog).
- **B17** Talep: Hedef dizini (`/var/tmp` benzeri) olmayan bir sunucuya dosya dağıt. Beklenen: `dosya_dagit` o sunucuda hata verir, diğer sunucular sürer, kısmi raporlanır. Kaynak: `08` bölüm 6 madde 7 (SMTool).
- **B18** Talep: Dördüncü adımda hata veren bir akışı dördüncü adımdan sürdür. Beklenen: Filo'da bu yetenek yok; senaryo eksik yeteneği ölçer. İlk üç adım tekrar etmemeli. Kaynak: `09§3#15`; `09b§2.2`.
- **B19** Talep: Tamamlanmış bir işi yeniden tetikle. Beklenen: aynı iş ikinci kez çalışmaz ya da kontrollü tekrar ve kayıt olur. Kaynak: `09c` C4 incorrectsecondexecutionactivity.
- **B20** Talep: Komut çıktısında bir parola değeri çıkarsa raporu ve denetim izini üret. Beklenen: değer maskelenir, rapor ve denetim izinde açık metin yok. Kaynak: `09§3#53` (parola gizleme); `denetim.py` maskeleme (mevcut).

---

## 7. Uygulama sırası

Dalgalar ilkeye göre dizildi: önce çekirdek (akış, onay, zamanlama, politika), sonra veri ve kimlik, en sonda dış sistemler. Dış sistemler laboratuvarda sahte servisle denenir. Öncelik değerleri bölüm 2'den alındı.

**Dalga 1 (12 beceri ya da yetenek)**

1. Akış yapıları: `dal`, `dongu`, `alt_akis`, `paralel_kol` (aile 28)
2. Duraklat, sürdür, devret, adımdan devam (aile 29)
3. Zamanlayıcı ve bakım penceresi (aile 18)
4. Onay ve girdi isteme: `onay_iste` (aile 30)
5. Yazılım politikası: `politika_uygula` (aile 07)
6. Yama: `yama_tara`, `yama_uygula` (aile 08)
7. Uyum: `uyum_denetle`, `uyum_duzelt` (aile 09)
8. Olay bildirimi ve pano özeti (aile 19)
9. Paket kaldırma: `paket_kaldir` (aile 06)
10. Ajan yükseltme: `ajan_yukselt` (aile 13)
11. Komut kipinde onaylı yazma: `komut_calistir` risk 3 (aile 04)
12. Servis durdurma ve destek paketi: `servis_durdur`, `destek_paketi_topla` (aile 27)

**Dalga 2 (12 beceri ya da yetenek)**

13. Kimlik profili ve kasa adaptörü (aile 17)
14. Rol, izin ve kiracı çekirdeği (aile 15)
15. Yapılandırma şablonu: `yapilandirma_uygula`, `yapilandirma_sapma_denetle` (aile 11)
16. Anlık görüntü: `goruntu_al`, `goruntu_karsilastir` (aile 10)
17. Dosya geri alma: `dosya_geri_al` (aile 05)
18. Hedef grupları: `hedef_grup_yonet` (aile 01)
19. Sunucu öznitelikleri: `sunucu_ozniteligi_yaz`, `envanter_sorgu` (aile 02)
20. Denetim sorgusu ve dışa aktarma (aile 35)
21. Yedekleme: `yedek_al`, `yedek_geri_yukle` (aile 26)
22. HTTP istemcisi: `http_istegi` (izin listeli) (aile 22)
23. Ansible: `ansible_calistir` (aile 24)
24. Beceri paketi ve ortam terfisi (aile 32)

**Dalga 3 (11 beceri ya da yetenek)**

25. Beceri üretme kaynakları: `openapi_beceri_uret`, `komut_beceri_uret` (aile 33)
26. ITSM adaptörü: `bilet_ac`, `bilet_guncelle`, `bilet_kapat` (aile 21)
27. Veritabanı: `db_sorgu`, `db_bakim` (aile 23)
28. Sanal makine ve bulut: `vm_olustur`, `vm_guc`, `vm_sablon` (aile 20)
29. Konteyner ve IaC: `konteyner_yonet`, `iac_uygula` (aile 24)
30. Ağ cihazı ve yük dengeleyici: `lb_havuz_guncelle`, `dns_kaydi` (aile 25)
31. Ajan keşfi ve anahtar döndürme: `agentsiz_kesif`, `ajan_anahtar_dondur` (aile 13)
32. Sertifika yenileme ve LDAP: `sertifika_yenile` ve kimlik sağlayıcı adaptörü (aile 16)
33. Dış API ve son kullanıcı kataloğu: `filo_api` (aile 34)
34. Hesap yönetimi: `kullanici_yonet` (aile 14)
35. Bare-metal OS provisioning: karar bekliyor. Bölüm 5'te alınmaz diye tanımlanmadı, kullanıcı kararı gerekir (aile 12)

---

## 8. Belirsiz eşleşmeler ve kaynak sorunları

- **Duraklatma ve devretme çelişkisi.** `09§3#10` ve `#11` ile `09§3` bölüm 3.6, duraklatma, sürdürme, handoff ve gated geçişin belgede bulunamadığını yazıyor. `09b§2.2` ve `09b§3` aynı yetenekleri kaynak sayfa adlarıyla veriyor (`changeexecutionstatus`, `trackmanageflowruns`, `runflow`). Bu belgede var kabul edildi. `09` güncellenmeli. Ürün indirilemediği için (`ilerleme.md`) canlı doğrulama yok.
- **Numaralama çakışması.** `09§3` bölüm 3.4 ile 3.5 aynı numaraları kullanıyor (87-94 ve 87-117). Sayım konu bazında yapıldı.
- **Ağırlık sütunları tahmin.** `08` ve `09` bölüm 2'deki ağırlık değerleri kaynakta tahmin olarak işaretli. Bu belgedeki öncelikler ürün sahibinin ilkesine göre verildi (`00-devir-notu`: sunucu otomasyonu ve akış otomasyonu'nun hiçbir özelliği eksik kalmayacak, özellikler genelleştirilecek).
- **sunucu otomasyonu'da iş onayı ve blackout.** `08` envanterinde iş onayı ayrı bir kalem olarak yok. Blackout kavramı da yok. Bu iki eşleşme belirsiz işaretlendi (aile 18, 30).
- **Okunmayan sayfalar.** `08` (§1): 27 sorun giderme alt sayfası, Install ve Upgrade alt adımları, Release notes ana sayfası okunmadı. `09` (§2.8, §6): Integrate'in 21 entegrasyon sayfası ve vSphere sayfası okunamadı; Administer ve Designer'ın bazı alt sayfaları yalnız başlıktan biliniyor. `09c`: Fixed issues tek kayda indi. Bu alanlardaki eşleşmeler başlık düzeyinde ve belirsiz.
- **Filo tarafı.** Eşleşmeler `skills/*/beceri.json` açıklamalarından, `filo/` modüllerinin başlık açıklamalarından ve `kaptan.py` için bir anahtar kelime taramasından yapıldı. Modül içleri ayrıntılı okunmadı. Bu yüzden "var" işaretleri en az düzeyde doğrulandı.
- **Bu okuma anı.** Depoda başka bir ajan yeni beceriler ve modüller ekliyor. Aile durumları bu anı yansıtır; değişikliklerden sonra yeniden taranmalı.
