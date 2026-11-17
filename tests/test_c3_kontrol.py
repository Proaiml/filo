"""C3: duraklat, sürdür, iptal, devret, adımdan devam ve konsol yeniden başlayınca sürdürme (laboratuvar gerekmez)."""
import json
import threading
import time

from filo import kontrol as kontrol_mod
from filo.devam import devam_hazirla, devam_noktalari, surdurme_hazirla
from filo.gateway import FakeModel
from filo.isler import IsKaydi
from filo.kalfa import Kalfa
from filo.kaptan import Kaptan

from conftest import FakeTasiyici
from test_ajanlar import Senaryo, erisimli, kayit, posta  # noqa: F401


def bekle(kosul, sure=5.0):
    son = time.time() + sure
    while time.time() < son:
        if kosul():
            return True
        time.sleep(0.05)
    return False


def test_yelpazede_duraklat_calisan_biter_kalanlar_bekler(envanter, denetim, durdurma, tmp_path):
    from filo.yurutme import Yurutucu
    k = IsKaydi("x", "kalfa", dizin=tmp_path)
    kt = kontrol_mod.kontrol(k.kimlik, k)
    cagri = []

    def dav(s, b):
        if "filo-erisim-ok" in b:
            return 0, "filo-erisim-ok\n", ""
        cagri.append(s.ad)
        if len(cagri) == 1:
            kt.duraklat("sınama")              # birinci sunucu çalışırken duraklatıldı
        return 0, s.ad + "\n", ""
    t = FakeTasiyici(dav)
    y = Yurutucu(envanter, eszamanli=1, denetim=denetim, durdurma=durdurma, tasiyici_fn=lambda s: t)
    out = {}
    th = threading.Thread(target=lambda: out.update(r=y.is_yurut(["PA-APP-01", "PA-APP-02", "PA-DB-01"], "hostname", 10,
                                                                  is_kimligi=k.kimlik)))
    th.start()
    assert bekle(lambda: k.durum == "duraklatildi")
    time.sleep(0.4)
    assert cagri == ["PA-APP-01"]                # çalışan bitti, sıradakiler başlamadı
    kt.surdur("sınama")
    th.join(5)
    assert cagri == ["PA-APP-01", "PA-APP-02", "PA-DB-01"] and all(r["durum"] == "basarili" for r in out["r"])
    assert [x["olay"] for x in k.kontrol_gecmisi] == ["duraklat", "surdur"]


def _iki_adim(m, tmp_path, talep, kt_ref=None, durakla=False, devir=None):
    sayac = {"servis": 0, "disk": 0}

    def dav(s, b):
        if "filo-erisim-ok" in b:
            return 0, "filo-erisim-ok\n", ""
        if "df " in b or "df -P" in b or "/veri" in b:
            sayac["disk"] += 1
            return 0, "/|1000|400|40|/\n", ""
        sayac["servis"] += 1
        if durakla and kt_ref:
            kt_ref[0].duraklat("sınama")
        return 0, "servis=uygulama\ndurum=active\n", ""
    return dav, sayac


SC2 = dict(akis={"adimlar": ["servis_durumu", "disk_durumu"]}, hedef={"ad": "PA-APP-01"},
           **{"param:servis_durumu": {"servis": "uygulama"}, "param:disk_durumu": {}})


def test_kaptan_adim_sinirinda_durur_kayittan_surer_ve_iptal(motor_kur, tmp_path):
    talep = "PA-APP-01'de uygulama servisinin durumuna ve disk doluluğuna bak"
    k = kayit(tmp_path, talep, "kaptan")
    ref = [kontrol_mod.kontrol(k.kimlik, k)]
    dav, sayac = _iki_adim(None, tmp_path, talep, ref, durakla=True)
    m, _ = motor_kur(erisimli(dav))
    model = FakeModel(islev=Senaryo(**SC2))
    kap = Kaptan(model, m, k, akis_dizini=tmp_path / "a", inisiyatif=1)
    kap.planla(talep)
    th = threading.Thread(target=kap.yurut, daemon=True)
    th.start()
    assert bekle(lambda: k.durum == "duraklatildi")
    d = json.loads((tmp_path / "isler" / f"{k.kimlik}.json").read_text(encoding="utf-8"))
    assert d["durum"] == "duraklatildi" and d["devam"]["akis_durumu"]["ust"] == 1
    assert sayac == {"servis": 1, "disk": 0}
    # konsol "yeniden başladı": eski iş parçacığı iptal edilir, kayıt yeni bir yürütücüyle kaldığı adımdan sürer
    ref[0].iptal("sınama")
    th.join(5)
    assert k.durum == "iptal"
    kontrol_mod.birak(k.kimlik)
    k2 = IsKaydi.yukle(d, dizin=tmp_path / "isler")
    bas, sun, onceki = surdurme_hazirla(d)
    assert bas == 1 and sun == ["PA-APP-01"]
    k2 = Kaptan(model, m, k2, akis_dizini=tmp_path / "a", inisiyatif=1).yurut(bas, sun, onceki)
    assert k2.durum == "bitti", k2.rapor
    assert sayac == {"servis": 1, "disk": 1}            # ilk adım yeniden çalışmadı


def test_devret_ve_surdur(motor_kur, tmp_path):
    talep = "PA-APP-01'de uygulama servisinin durumuna ve disk doluluğuna bak"
    k = kayit(tmp_path, talep, "kaptan")
    kt = kontrol_mod.kontrol(k.kimlik, k)
    dav, sayac = _iki_adim(None, tmp_path, talep)

    def dav2(s, b):
        r = dav(s, b)
        if sayac["servis"] == 1 and sayac["disk"] == 0 and kt.durum == "calisiyor" and not k.kontrol_gecmisi:
            kt.devret("vardiya-2", "operatör-a", "gece ekibine bırakıyorum")
        return r
    m, _ = motor_kur(erisimli(dav2))
    kap = Kaptan(FakeModel(islev=Senaryo(**SC2)), m, k, akis_dizini=tmp_path / "a", inisiyatif=1)
    kap.planla(talep)
    th = threading.Thread(target=kap.yurut, daemon=True)
    th.start()
    assert bekle(lambda: k.durum == "devredildi")
    assert k.sahip == "vardiya-2" and sayac["disk"] == 0
    kt.surdur("vardiya-2", "devraldım")
    th.join(5)
    assert k.durum == "bitti" and sayac["disk"] == 1
    assert [x["olay"] for x in k.kontrol_gecmisi] == ["devret", "surdur"]


def test_kaptan_insana_devir_bekler_operator_karariyla_surer(motor_kur, tmp_path):
    durum = {"duzeldi": False}

    def dav(s, b):
        if "filo-erisim-ok" in b:
            return 0, "filo-erisim-ok\n", ""
        if "apt-get" in b and not durum["duzeldi"]:
            return 100, "", "E: Unable to locate package jq"
        return 0, "jq|1.6\n", ""
    m, _ = motor_kur(erisimli(dav))
    talep = "PA-APP-01'e jq kur"
    sc = Senaryo(akis={"adimlar": ["paket_kur"]}, hedef={"ad": "PA-APP-01"}, param={"paketler": ["jq"]},
                 teshis={"beceri": "yok"}, karar={"karar": "yeniden_dene"})
    k = kayit(tmp_path, talep, "kaptan")
    kap = Kaptan(FakeModel(islev=sc), m, k, akis_dizini=tmp_path / "a", inisiyatif=3, devir_bekle_sn=30)
    kap.planla(talep)
    th = threading.Thread(target=kap.yurut, daemon=True)
    th.start()
    assert bekle(lambda: k.durum == "devredildi")
    assert k.ek["devir"]["sunucular"] == ["PA-APP-01"] and "Unable to locate" in k.ek["devir"]["neden"]
    durum["duzeldi"] = True
    kontrol_mod.kontrol(k.kimlik).surdur("operatör", "depo ayarını elle düzelttim", karar="yeniden_dene")
    th.join(10)
    assert k.durum == "bitti", k.rapor
    assert any(g["soru"].startswith("operatör kararı") for g in k.gerekce)


def test_kaptan_adimdan_devam_yalniz_basarisizlar(motor_kur, tmp_path):
    cagri, bozuk = [], {"PA-APP-02"}

    def dav(s, b):
        if "filo-erisim-ok" in b:
            return 0, "filo-erisim-ok\n", ""
        adim = "kur" if ("apt-get" in b or "dnf" in b or "apk add" in b) else "dogrula"
        cagri.append((adim, s.ad))
        if adim == "kur" and s.ad in bozuk:
            return 1, "", "E: depo erişilemedi"
        return 0, "jq|1.6\n", ""
    m, _ = motor_kur(erisimli(dav))
    talep = "PA-APP-01 ve PA-APP-02'ye jq kur ve doğrula"
    sc = Senaryo(akis={"adimlar": ["paket_kur", "paket_dogrula"]}, hedef={"ad": "PA-APP-01,PA-APP-02"},
                 param={"paketler": ["jq"]})
    k = Kaptan(FakeModel(islev=sc), m, kayit(tmp_path, talep, "kaptan"), akis_dizini=tmp_path / "a", inisiyatif=3,
               deneme_siniri=0).calistir(talep)
    assert k.durum == "kismi"
    d = k.sozluk()
    n = devam_noktalari(d)
    assert [x["basarisiz"] for x in n] == [["PA-APP-02"], []] and n[0]["sunucular"] == ["PA-APP-01", "PA-APP-02"]
    bozuk.clear()
    once = list(cagri)
    bas, sun, onceki = devam_hazirla(d, 0, "basarisiz")
    assert (bas, sun) == (0, ["PA-APP-02"])
    k2 = IsKaydi(talep, "kaptan", "fake", dizin=tmp_path / "isler")
    k2.plan = d["plan"]
    k2 = Kaptan(FakeModel(islev=sc), m, k2, akis_dizini=tmp_path / "a", inisiyatif=3).yurut(bas, sun, onceki)
    assert k2.durum == "bitti", k2.rapor
    yeni = cagri[len(once):]                      # (paket_kur önce kuru çalıştırılır: "kur" iki kez görünür)
    assert {s for _, s in yeni} == {"PA-APP-02"} and list(dict.fromkeys(a for a, _ in yeni)) == ["kur", "dogrula"]
    # ikinci adımdan "hepsi": birinci adım yeniden çalışmaz
    bas, sun, onceki = devam_hazirla(k2.sozluk(), 1, "hepsi")
    k3 = IsKaydi(talep, "kaptan", "fake", dizin=tmp_path / "isler")
    k3.plan = d["plan"]
    once = len(cagri)
    Kaptan(FakeModel(islev=sc), m, k3, akis_dizini=tmp_path / "a", inisiyatif=3).yurut(bas, sun, onceki)
    assert all(a == "dogrula" for a, _ in cagri[once:]) and len(cagri[once:]) == 1


def test_kalfa_adimdan_devam_ve_iptal(motor_kur, tmp_path, posta):
    bozuk = {"PA-APP-02"}

    def dav(s, b):
        if "filo-erisim-ok" in b:
            return 0, "filo-erisim-ok\n", ""
        return (1, "", "hata") if s.ad in bozuk else (0, "/|1000|400|40|/\n", "")
    m, t = motor_kur(erisimli(dav))
    talep = "PA-APP-01 ve PA-APP-02 disk doluluğunu ops@lab.yerel adresine bildir"
    sc = Senaryo(beceri={"secim": "disk_durumu"}, hedef={"ad": "PA-APP-01,PA-APP-02"}, param={})
    k = Kalfa(FakeModel(islev=sc), m, kayit(tmp_path, talep, "kalfa")).calistir(talep)
    assert k.durum == "kismi" and len(posta) == 1
    d = k.sozluk()
    assert devam_noktalari(d)[0]["basarisiz"] == ["PA-APP-02"]
    bozuk.clear()
    bas, sun, onceki = devam_hazirla(d, 0, "basarisiz")
    k2 = IsKaydi(talep, "kalfa", "fake", dizin=tmp_path / "isler")
    k2.plan = d["plan"]
    n = len(t.cagrilar)
    k2 = Kalfa(None, m, k2).yurut(bas, sun, onceki)
    assert k2.durum == "bitti" and {s for s, b in t.cagrilar[n:] if "filo-erisim-ok" not in b} == {"PA-APP-02"}
    assert len(posta) == 2 and "PA-APP-02" in posta[1]["govde"]
    # yalnız e-posta adımından devam: sunucuya hiçbir komut gitmez
    bas, sun, onceki = devam_hazirla(k2.sozluk(), 1, "hepsi")
    k3 = IsKaydi(talep, "kalfa", "fake", dizin=tmp_path / "isler")
    k3.plan = d["plan"]
    n = len(t.cagrilar)
    Kalfa(None, m, k3).yurut(bas, sun, onceki)
    assert len(t.cagrilar) == n and len(posta) == 3


def test_konsol_yeniden_baslayinca_duraklatilmis_is_surer(monkeypatch, tmp_path, posta):
    """Kayıttaki duraklatılmış Kalfa işi yeni Ofis tarafından yüklenir ve 'Sürdür' ile kaldığı adımdan biter."""
    from filo import isler, web
    monkeypatch.setattr(isler, "ISLER", tmp_path / "isler")
    monkeypatch.setattr(web, "ISLER", tmp_path / "isler")
    plan_ana = {"is_kimligi": "x", "beceri": "disk_durumu", "surum": 1, "baslik": "Disk", "tur": "uzak", "parametreler": {},
                "hedef": {"secici": {"ad": "PA-APP-01"}, "sunucular": ["PA-APP-01"], "sayi": 1}, "risk": 0,
                "onay_gerekli": False, "kuru_once": False, "zaman_asimi": 30}
    adim = {"beceri": "disk_durumu", "durum": "basarili", "sonuclar": [{"sunucu": "PA-APP-01", "durum": "basarili",
            "cikis_kodu": 0, "stdout": "/|1000|400|40|/\n", "veri": [{"bolum": "/", "doluluk": 40}]}]}
    k = IsKaydi("PA-APP-01 diski bildir", "kalfa", "operatör (model yok)", dizin=tmp_path / "isler")
    k.plan = {"ana": plan_ana, "bicim": None, "alici": "ops@lab.yerel", "adimlar": ["disk_durumu", "eposta_gonder"]}
    k.devam = {"tur": "kalfa", "sonraki": 1, "baglam": {"adimlar": [adim], "son_uzak_adim": adim},
               "baglam_uzunlugu": {"0": 0, "1": 1}, "adim_girisi": {"0": ["PA-APP-01"]}}
    k.durum = "duraklatildi"
    k.kaydet()
    ofis = web.Ofis(zamanlama_yolu=tmp_path / "z.json")
    v = ofis.isler[k.kimlik]
    assert v.get("uyuyan") and v["kayit"].durum == "duraklatildi"
    ofis.kontrol_eylem(k.kimlik, "surdur", "konsol yeniden başladı")
    assert bekle(lambda: v["kayit"].durum == "bitti", 10), v["kayit"].rapor
    assert posta and posta[0]["alici"] == "ops@lab.yerel"
