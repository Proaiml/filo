"""B7: ilk koşunun harness hatalarına karşı regresyon sınamaları (FakeModel, laboratuvar gerekmez)."""
from filo.ajan_ortak import beceri_sec, dayanak_var, hedef_sor
from filo.gateway import FakeModel
from filo.kaptan import Kaptan

from test_ajanlar import Senaryo, kayit


def test_grup_adlara_cevrilince_seciciye_geri_doner(envanter):
    """İlk koşu T04: model 'web grubu'nu açık adlara çevirdi, kod reddetti, hedef hiç çözülmedi."""
    iz = []
    talep = "web grubundaki sunucularda webd servisinin durumunu kontrol et"
    sec = hedef_sor(FakeModel([{"ad": "PA-WEB-01,PB-WEB-01"}]), envanter, talep, iz)
    assert sec == {"grup": "web"} and "web' grubuna çevrildi" in iz[0]["kod_notu"]


def test_bos_oznitelik_ve_varsayilan_deger(envanter, motor_kur):
    """İkinci koşunun ilk denemesi: {"konum": ""} bütün sunucuları eledi; şemanın varsayılan alıcısı 'uydurma' sayıldı."""
    from filo.ajan_ortak import parametre_sor
    sec = hedef_sor(FakeModel([{"ad": "PA-APP-01,PB-WEB-01", "oznitelik": {"konum": ""}}]), envanter,
                    "PA-APP-01 ve PB-WEB-01 sunucularına jq paketini kur", [])
    assert sec == {"ad": "PA-APP-01,PB-WEB-01"}
    m, _ = motor_kur()
    p = parametre_sor(FakeModel([{"alici": "ops@lab.yerel", "konu": "Filo is raporu"}]), m.katalog, "eposta_gonder",
                      "PA-APP-01'e jq kur", [])
    assert p is None                                    # eposta_gonder'in alıcısı varsayılan değil: uydurma reddedilir


def test_hicbiri_cevabi_bir_kez_sinanir(motor_kur):
    """İlk koşu I04: 'bekleyen yama sayısı' talebine yama_durumu adayken model 'hicbiri' dedi."""
    m, _ = motor_kur()
    talep = "PB-APP-01 sunucusunda bekleyen yama sayısını topla"
    model = FakeModel([{"secim": "hicbiri"}, {"cevap": "evet"}])
    s = beceri_sec(model, m.katalog, talep, ["yama_durumu", "disk_durumu"], [])
    assert s["secim"] == "yama_durumu" and model.cagri == 2


def test_degistiren_adimin_dayanagi_olmali(motor_kur):
    m, _ = motor_kur()
    talep = "PA-APP-01 ve PA-WEB-01 sunucularına jq paketini kur, sonucu ops@lab.yerel adresine gönder"
    assert not dayanak_var(m.katalog, "ajan_kur", talep) and not dayanak_var(m.katalog, "standart_sunucu_teslimi", talep)
    assert not dayanak_var(m.katalog, "sonucu_donustur", talep)
    assert dayanak_var(m.katalog, "paket_kur", talep) and dayanak_var(m.katalog, "eposta_gonder", talep)
    assert dayanak_var(m.katalog, "yama_durumu", talep)            # salt-okur adım serbest
    # İkinci koşunun ikinci denemesi: varsayılanı (jq) olan paket parametresi "talepte geçmek zorunda" sayılıp sürüm
    # raporu akışına jq kurulumu girdi (yanlış sunucuda değişiklik). Varsayılanlı parametre dayanak sayılmaz.
    assert not dayanak_var(m.katalog, "jq_kur_ve_bildir",
                           "PA-APP-01 ve PA-APP-02 sunucularında uygulama_surumu betiğini çalıştır, sonucu CSV yap")
    # Kalfa da dayanaksız değiştiren beceriyi seçemez (ilk koşu I02: "jq kur ve doğrula" → standart teslim zinciri)
    model = FakeModel([{"secim": "standart_sunucu_teslimi"}, {"secim": "paket_kur"}])
    assert beceri_sec(model, m.katalog, "PA-APP-01'e jq paketini kur ve doğrula",
                      ["standart_sunucu_teslimi", "paket_kur"], [])["secim"] == "paket_kur"


def test_posta_csv_hakemi_alan_duzeyinde(monkeypatch):
    """İlk koşu I03: ham satırdaki '1.4.2' sayı ölçütünü aldatıyordu; hakem kolun beyanına yaslanıyordu."""
    from filo import lab
    from filo.bench import hakem
    ekler = {"iyi": "sunucu,durum,surum\nPA-APP-01,basarili,1.4.2\nPA-APP-02,basarili,1.4.2\n",
             "kotu": "sunucu,durum,cikti\nPA-APP-01,basarili,1.4.2\nPA-APP-02,hatali,Uygulama Surumu: 1.4.2 (derleme 77)\n"}
    o = {"tur": "posta_csv", "alici": "ops@lab.yerel", "satirlar": {"PA-APP-01": "1.4.2", "PA-APP-02": "1.4.2"}}
    for ad, beklenen in (("kotu", False), ("iyi", True)):
        monkeypatch.setattr(lab, "posta_listesi", lambda n=100, a=ad: [{"id": a, "kime": ["ops@lab.yerel"],
                                                                        "ekler": [{"ad": "r.csv", "parca": "1"}]}])
        monkeypatch.setattr(lab, "posta_eki", lambda i, p: ekler[i])
        assert hakem.olcut(o, None, {})[0] is beklenen


def test_rapor_cikti_alani_temel_sutunu_ezmez():
    """İkinci koşu T04: servis_durumu'nun 'durum' (inactive) alanı temel 'durum' sütunuyla çakıştığı için XML'den düştü."""
    from filo import rapor
    adim = {"beceri": "servis_durumu", "sonuclar": [{"sunucu": "PB-WEB-01", "durum": "basarili", "cikis_kodu": 0, "sure": 0.1,
                                                     "veri": {"servis": "webd", "durum": "inactive"}}]}
    ad, icerik, mime = rapor.donustur(adim, "xml")
    assert "inactive" in icerik and "basarili" in icerik


def test_genel_sozcuk_dayanak_degil(motor_kur):
    """İkinci koşu T03: 'CSV dosyasında topla' talebinde dosya_dagit adımı dayanaklı sayıldı."""
    m, _ = motor_kur()
    assert not dayanak_var(m.katalog, "dosya_dagit", "PA sunucularında betiği çalıştır, çıktıları tek bir CSV dosyasında topla")
    assert dayanak_var(m.katalog, "dosya_dagit", "standart uygulama.conf dosyasını /etc/uygulama altına geri koy")


def test_kalfa_isin_yarisini_yapinca_kismi_der(motor_kur, tmp_path):
    """İkinci koşu (hedefli) I07: Kalfa yalnız durum okudu, 'yeniden başlat' yapılmadı ama 'bitti' dedi."""
    from filo.kalfa import Kalfa
    from test_ajanlar import erisimli
    m, _ = motor_kur(erisimli(lambda s, b: (0, "servis=uygulama\ndurum=inactive\n", "")))
    talep = "PA-APP-02'de uygulama servisi durmuş: durumunu kontrol et ve yeniden başlat"
    sc = Senaryo(beceri={"secim": "servis_durumu"}, hedef={"ad": "PA-APP-02"},
                 param=[{"servis": "pa-app-02"}, {"servis": "uygulama"}], kapsam={"eksik": "yeniden başlatma"})
    k = Kalfa(FakeModel(islev=sc), m, kayit(tmp_path, talep, "kalfa")).calistir(talep)
    assert k.durum == "kismi" and "yeniden başlatma" in k.rapor
    p = next(g for g in k.gerekce if g["soru"].startswith("parametre"))
    assert "sunucu adı" in p["denemeler"][0]["hata"]         # servis yerine sunucu adı reddedildi


def test_bos_cikti_basari_sayilmaz(motor_kur):
    """İkinci koşu T02: arama komutu boş döndü, adım başarılı sayıldı, kol başarı bildirdi."""
    from filo.beceri import cikti_dogrula
    m, _ = motor_kur()
    sema = m.katalog["komut_calistir"]["cikti"]
    assert cikti_dogrula(sema, "  \n")[1] and cikti_dogrula(sema, "10.20.30.44\n")[1] is None


def test_dogrulama_kurulumdan_once_gelemez(motor_kur, tmp_path):
    """İlk koşu O01: akış paket_dogrula → paket_kur sırasındaydı."""
    m, _ = motor_kur()
    talep = "PA-APP-01'e jq paketini kur"
    sc = Senaryo(akis=[{"adimlar": ["paket_dogrula", "paket_kur"]}, {"adimlar": ["paket_kur", "paket_dogrula"]}],
                 hedef={"ad": "PA-APP-01"}, param={"paketler": ["jq"]})
    k = Kaptan(FakeModel(islev=sc), m, kayit(tmp_path, talep, "kaptan"), akis_dizini=tmp_path / "a").planla(talep)
    assert k.plan["adimlar"] == ["paket_kur", "paket_dogrula"]
    assert "SONRA" in k.gerekce[0]["denemeler"][0]["hata"]
