# Filo

Sunucularda aynı işi yüzlerce makinede yapıp sonucu toplayan, adminlik görevlerini bir yapay zekâ ajanına yaptıran bir harness.

> "PA ile başlayan sunucularda uygulama sürümü betiğini çalıştır, sonucu XML yap, ops@lab.yerel adresine gönder."

Filo bu talebi düz Türkçeyle alır. Hedef sunucuları çözer ve listeyi dondurur, işi hazır becerilere ya da bir akışa
böler, riski ve onayı kontrol eder, sonra çalıştırır. Hangi sunucunun başarılı, hangisinin hatalı ya da erişilemez
olduğunu tek tek raporlar. Her karar ve eylem değiştirilemeyen bir denetim izine yazılır.

Filo model bağımsızdır: yerel bir model de, bir API modeli de aynı yolu izler. Modelin işi dili anlamak, plan kurmak
ve hatayı yorumlamaktır. Hedef çözümü, yetki, onay, şema denetimi ve yürütme koddadır; model onları atlayamaz.

![Filo konsolu: Kalfa iş konsolu](docs/resim/kalfa.png)

## Neden

Adminlik işlerinin çoğu aynı kalıbı taşır: bir grup sunucu seç, bir işi çalıştır, sonuçları topla, eksikleri ayır,
rapor gönder. Bu iş elle yapıldığında yavaş ve hata çıkmaya açık olur; bir betik yazıldığında da hatalı sunucuyu
gizleyebilir ya da yanlış hedefi seçebilir. Filo bu adımların her birini açık, ölçülebilir ve geri izlenebilir yapar.

## Nasıl çalışır

![Filo mimarisi](docs/resim/mimari.png)

Talep iki ajandan birine gider:

| Ajan | Ne yapar | Ne zaman |
|---|---|---|
| **Kalfa** | Yalnız hazır becerilerle çalışır. Beceriyi seçer, parametreleri doldurur, hedefi dondurur, planı gösterir, onaydan sonra yürütür. Beceriyi değiştirmez. | İş tanımlıysa ve tekrar edecekse |
| **Kaptan** | Talepten bir akış kurar ve adım adım yürütür. Hata ya da beklenmeyen çıktıda teşhis koyar, gerekirse beceriyi yeni sürüm olarak değiştirir, sınırlı yeniden dener, olmazsa insana devreder. | Yeni ya da karmaşık işlerde |

Kaptan'ın ne kadar serbest davranacağını operatör **inisiyatif düzeyi** ile belirler:

- **0:** yalnız önerir, hiçbir şey çalıştırmaz.
- **1:** salt okunur teşhis yapar.
- **2:** geri alınabilir onarım yapar.
- **3:** beceri ve servis ya da paket değişikliği yapar.

Yıkıcı işler (risk düzeyi 4) her düzeyde insan onayı ister. Sınırı model değil, kod uygular.

Başarılı bir akış tek adımda **beceriye dönüşür**; benzer bir sonraki talep Kalfa tarafından doğrudan yürütülür.

## Ekran görüntüleri

| Kaptan: akış tuvali ve inisiyatif düzeyi | Zamanlanmış işler |
|---|---|
| ![Kaptan](docs/resim/kaptan.png) | ![Zamanlama](docs/resim/zamanlama.png) |

| Bench: koşuların yan yana karşılaştırması |
|---|
| ![Bench](docs/resim/bench.png) |

## Neler var

- **Hedefleme:** ad kalıbı (`PA*`), grup, öznitelik, işletim sistemi. Hedef listesi iş başlamadan dondurulur.
- **Çalıştırma:** sunucular arasında paralel yürütme, sunucu başına zaman aşımı, çıktı boyut sınırı.
- **Sonuç:** her sunucu için tek biçimli durum (başarılı, hatalı, zaman aşımı, erişilemedi, iptal), kısmi başarısızlığın açık raporu, yalnız başarısızları yeniden deneme.
- **Çıktı:** CSV, XML, JSON, HTML dönüşümü ve e-posta.
- **Zamanlama:** tek seferlik ve tekrarlı işler, bakım ve yasak pencereleri. "Her gece 02:00'de" gibi bir ifade zamanlamaya çevrilir ve sonraki üç çalışma zamanı gösterilir.
- **Çalıştırma kimliği:** bağlantı kullanıcısı, root (sudo) ya da adı verilen bir kullanıcı; izinli olmayan kimlik reddedilir.
- **Denetim:** duraklat, sürdür, iptal, devret ve adımdan devam. Denetim izi her eylemi kaydeder.
- **Yeni sunucu teslimi:** yeni kaydolan sunucu ad kalıbına göre bir profile düşer; standart kurulum kendiliğinden başlar.
- **Go ajanı (`filo-ajan`):** sunucuda çalışır, dışarı doğru bağlanır, imzalı işleri alır. Ajan yoksa iş SSH üzerinden gider ve hangi yolla gidildiği sonuçta yazar.
- **Model bağlantıları:** yerel modeller (Ollama, OpenAI uyumlu sunucular), Claude API ve Claude Code aboneliği. Anahtarlar git dışında tutulur ve arayüzde geri gösterilmez.

## Hızlı başlangıç

Gereksinimler: Python 3.11 ve laboratuvar için Docker. Yerel model kullanacaksan Ollama.

```bash
git clone https://github.com/Proaiml/filo.git
cd filo
python -m filo lab kur          # 8 Linux konteyneri ve posta sunucusu
python -m filo web --port 8790  # http://127.0.0.1:8790
```

Komut satırından bir talebi yalnız planlamak için:

```bash
python -m filo talep --ajan kalfa --plan "PA ile başlayan sunucularda uygulama sürümünü göster"
```

Testler:

```bash
python -m pytest -q             # laboratuvar gerektirmeyenler; laboratuvarla birlikte tam takım
```

Laboratuvarı kapatmak için `python -m filo lab kapat`.

## Ölçüm

Filo'nun asıl iddiası, küçük bir modelin harness ile güçlü bir modele yakın sonuç vermesidir. Bunu yardımsız modelle
karşılaştırarak ölçüyoruz: aynı model, aynı senaryolar, aynı hakem.

45 senaryo, qwen3:8b, tek koşu, laboratuvarda:

| Kol | Geçen | Zararlı sonuç |
|---|---|---|
| Kaptan | 37 / 45 | 2 |
| Kalfa | 34 / 45 | 3 |
| Yardımsız model | 6 / 37 (37 senaryoda ölçüldü) | — |

Bu bir ilk ölçümdür: tek koşu, küçük bir yerel model, kendi laboratuvarımız. Tekrar ve güven aralığı henüz yok.
Senaryolar yazılım ve ağ hatalarını taklit eder; üretim ortamının yerini tutmaz. Ayrıntılar `docs/ilerleme.md` içinde.

## Sınırlar

- **Windows:** Go ajanının Windows ikilisi ve WinRM yolu gerçek bir Windows makinesinde denenmedi. Windows hedefleri şu an öykünücüden cevaplanabilir.
- **Model:** ölçümler yalnız qwen3:8b ile yapıldı. Daha güçlü modellerle tam koşu henüz yapılmadı.
- **Yetki:** rol ve izin modeli yok; devir yalnızca bir ad kaydeder, kimin sürdürebileceğini kısıtlamaz.
- **Yama ve uyum:** yama durumu ve yazılım politikası üzerinde çalışılıyor, uygulama tarafı yarım. Dördüncü tur `dorduncu-tur` dalında.
- **Denetim izi:** bütünlük kontrolü eski kayıtlarla "bozuk" gösterebiliyor; düzeltme sürüyor.
- **Laboratuvar dışı:** bu sürüm yalnız kendi laboratuvarında ölçüldü. Gerçek bir ortamda kullanmadan önce kendi sunucularında deneyin.

## Yol haritası

1. Denetim izi bütünlük kontrolünü düzeltmek ve yetki modelini (rol, müşteri, kiracı) eklemek.
2. Yama uygulamasını ve yazılım politikasını (istenen durum, sapma, önizleme, remediation) tamamlamak.
3. Windows'ta gerçek WinRM ve Go ajanı sınamalarını yapmak.
4. Daha güçlü modellerle tam bench koşusu ve tekrarlı ölçüm.

## Belgeler

- `docs/00-devir-notu.md`: tasarım kararları, kurallar ve ajanların rolleri.
- `docs/ilerleme.md`: her turun ne yaptığı, nasıl doğrulandığı ve ne eksik kaldığı.
- `docs/11-ozellik-haritasi.md`: hangi yeteneklerin var, kısmi ya da yok olduğu.
- `docs/arastirma/`: araştırma notları ve forum vakaları. Her iddianın yanında kaynak bağlantısı var.

## Lisans

Henüz lisans seçilmedi. Lisans eklenene kadar kodu kullanmak, değiştirmek ya da yeniden dağıtmak için sahibiyle
konuşun.
