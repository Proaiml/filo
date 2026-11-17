"""A2: beceri şeması, risk sınıflaması, sürümleme, politika, motor, rapor."""
import json
import xml.etree.ElementTree as ET

import pytest

from filo import rapor
from filo.beceri import Katalog, SemaHatasi, cikti_dogrula, parametre_dogrula, risk_sinifla
from filo.motor import PlanHatasi

GEREKEN = {"erisim_sinamasi", "betik_calistir", "komut_calistir", "disk_durumu", "servis_durumu",
           "servis_yeniden_baslat", "paket_kur", "paket_dogrula", "dosya_dagit", "kullanici_ac", "yama_durumu",
           "sistem_envanteri", "sonucu_donustur", "eposta_gonder", "standart_sunucu_teslimi"}


def test_katalog_tam_ve_gecerli(katalog_dizini, denetim):
    k = Katalog(katalog_dizini, denetim=denetim)
    assert not k.hatalar
    assert GEREKEN <= set(k.beceriler) and len(k.beceriler) >= 14
    for ad, t in k.beceriler.items():
        if t["risk"] >= 2 and t["tur"] == "uzak":
            assert t.get("kuru") and t.get("geri_al"), ad
        # beyan edilen düzey koddan hesaplanandan düşük olmamalı
        assert k.etkin_risk(t)[0] == t["risk"], ad


def test_parametre_semasi():
    sema = {"esik": {"tip": "tamsayi", "varsayilan": 90, "en_az": 1, "en_cok": 100},
            "paketler": {"tip": "liste", "desen": "paket"}, "alici": {"tip": "eposta", "zorunlu": False},
            "hedef": {"tip": "yol", "izinli_onekler": ["/veri"], "zorunlu": False}}
    assert parametre_dogrula(sema, {"paketler": "jq, tree"}) == {"esik": 90, "paketler": ["jq", "tree"]}
    for kotu in ({"paketler": ["jq; rm -rf /"]}, {"paketler": ["jq"], "esik": 500}, {"paketler": ["jq"], "x": 1},
                 {}, {"paketler": ["jq"], "alici": "x@"}, {"paketler": ["jq"], "hedef": "/etc/passwd"},
                 {"paketler": ["jq"], "hedef": "/veri/../etc"}):
        with pytest.raises(SemaHatasi):
            parametre_dogrula(sema, kotu)
    with pytest.raises(SemaHatasi):
        parametre_dogrula({"komut": {"tip": "komut"}}, {"komut": "rm -rf /tmp"})


def test_cikti_semasi_ve_son_kosul():
    sema = {"bicim": "anahtar_deger", "alanlar": {"servis": "metin", "durum": "metin"}, "beklenen": {"durum": "active"}}
    assert cikti_dogrula(sema, "servis=x\ndurum=active\n")[1] is None
    assert "son koşul" in cikti_dogrula(sema, "servis=x\ndurum=inactive\n")[1]
    assert "beklenen alanlar yok" in cikti_dogrula(sema, "Uygulama Surumu: 1.4\n")[1]
    satir = {"bicim": "satirlar", "ayirici": "|", "alanlar": {"paket": "metin", "surum": "metin"}, "yasak": {"surum": "yok"}}
    assert cikti_dogrula(satir, "jq|1.6\n")[1] is None
    assert cikti_dogrula(satir, "jq|yok\n")[1]
    assert cikti_dogrula(satir, "jq 1.6\n")[1]
    assert cikti_dogrula({"bicim": "anahtar_deger", "alanlar": {"n": "tamsayi"}}, "n=abc")[1]


@pytest.mark.parametrize("metin,duzey", [("cat /etc/os-release", 0), ("ls 2>/dev/null; df -P | awk 'NR>1'", 0),
                                         ("echo x > /etc/uygulama/a.conf", 2), ("sudo -n systemctl restart x", 3),
                                         ("apk add jq", 3), ("useradd deneme", 3), ("rm -rf /veri", 4),
                                         ("dd if=/dev/zero of=/x", 4)])
def test_risk_sinifla(metin, duzey):
    assert risk_sinifla([metin])[0] == duzey


def test_surumleme_fark_geri_donus_ve_risk_yukselmesi(katalog_dizini, denetim):
    k = Katalog(katalog_dizini, denetim=denetim)
    t = json.loads((katalog_dizini / "servis_durumu" / "beceri.json").read_text(encoding="utf-8"))
    t["komut"]["debian"] += "\nsudo -n systemctl restart {servis}"
    with pytest.raises(SemaHatasi):   # yazan komut eklendi ama kuru çalıştırma / geri alma yok
        k.yeni_surum("beceri", "servis_durumu", {"beceri.json": json.dumps(t)}, "kaptan", "deneme")
    t["kuru"] = {"linux": "systemctl is-active {servis}"}
    t["geri_al"] = {"linux": "sudo -n systemctl start {servis}"}
    r = k.yeni_surum("beceri", "servis_durumu", {"beceri.json": json.dumps(t)}, "kaptan", "deneme")
    assert r["yeni_surum"] == 2 and r["risk_onceki"] == 0 and r["risk_yeni"] == 3 and r["risk_yukseldi"]
    assert "systemctl restart" in r["fark"]
    assert k["servis_durumu"]["surum"] == 2 and k.etkin_risk(k["servis_durumu"])[0] == 3
    assert [g["surum"] for g in k.gecmis("beceri", "servis_durumu")] == [1, 2]
    assert "restart" in k.fark("beceri", "servis_durumu", 1, 2)
    g = k.geri_don("beceri", "servis_durumu", 1)
    assert g["yeni_surum"] == 3 and "restart" not in json.dumps(k["servis_durumu"]["komut"])
    assert denetim.oku(tur="beceri_degisti")
    # betik kütüphanesi de sürümlenir
    b = k.yeni_surum("betik", "uygulama_surumu", {"betik.sh": k.betik_oku("uygulama_surumu") + "rm -rf /veri\n"},
                     "kaptan", "deneme")
    assert b["risk_yeni"] == 4 and (katalog_dizini / "_betikler" / "uygulama_surumu" / "gecmis" / "v1" / "betik.sh").exists()
    assert k.etkin_risk(k["betik_calistir"], {"betik": "uygulama_surumu"})[0] == 4


def test_gecersiz_yeni_surum_reddedilir(katalog_dizini, denetim):
    k = Katalog(katalog_dizini, denetim=denetim)
    t = dict(k["paket_kur"])
    t.pop("geri_al")
    with pytest.raises(SemaHatasi):
        k.yeni_surum("beceri", "paket_kur", {"beceri.json": json.dumps(t)}, "kaptan", "geri almayı sil")
    assert k["paket_kur"]["surum"] == 1


# ---------------------------------------------------------------- motor + politika
def _ok(cevap):
    def d(s, b):
        if "filo-erisim-ok" in b:
            return 0, "filo-erisim-ok\n", ""
        return cevap(s, b)
    return d


def test_plan_dondurur_ve_denetler(motor_kur, denetim):
    m, _ = motor_kur()
    p = m.plan("disk_durumu", {}, "PA*", talep="disk")
    assert p["hedef"]["sunucular"] == ["PA-APP-01", "PA-APP-02", "PA-DB-01", "PA-WEB-01"]
    assert p["parametreler"] == {"esik": 90} and p["risk"] == 0 and not p["onay_gerekli"]
    assert denetim.oku(tur="plan")[0]["beceri"] == "disk_durumu"
    with pytest.raises(SemaHatasi):
        m.plan("disk_durumu", {"esik": "çok"}, "PA*")
    with pytest.raises(PlanHatasi):
        m.plan("yok_boyle", {}, "PA*")


def test_onay_yoksa_hicbir_sey_calismaz(motor_kur, onaylar):
    m, t = motor_kur(_ok(lambda s, b: (0, "servis=uygulama\ndurum=active\n", "")), kip="etkilesimli")
    p = m.plan("servis_yeniden_baslat", {"servis": "uygulama"}, "PA-APP-01")
    a = m.yurut(p)
    assert a["durum"] == "onay_bekliyor"
    assert not any("restart" in b and "su_anki_durum" not in b for _, b in t.cagrilar)   # yalnız kuru çalıştı
    k = onaylar.liste("bekliyor")[0]
    assert k["beceri"] == "servis_yeniden_baslat" and k["hedefler"] == ["PA-APP-01"] and k["kuru"]
    onaylar.karar(k["kimlik"], True, "test")
    a = m.yurut({**p, "onay_kimligi": k["kimlik"], "kuru_yapildi": True})
    assert a["durum"] == "basarili" and any("restart" in b for _, b in t.cagrilar)


def test_bench_kurali_reddeder(motor_kur):
    m, t = motor_kur(_ok(lambda s, b: (0, "", "")), kural={"varsayilan": "reddet"})
    a = m.yurut(m.plan("paket_kur", {"paketler": ["jq"]}, "PA-APP-01"))
    assert a["durum"] == "reddedildi"
    assert not any("apt-get install -y" in b for _, b in t.cagrilar)


def test_surum_degisirse_plan_gecersiz(motor_kur):
    m, _ = motor_kur()
    p = m.plan("disk_durumu", {}, "PA-APP-01")
    t = dict(m.katalog["disk_durumu"])
    m.katalog.yeni_surum("beceri", "disk_durumu", {"beceri.json": json.dumps(t)}, "test", "sürüm")
    with pytest.raises(PlanHatasi):
        m.yurut(p)


def test_sema_uyumsuzlugu_hatali_sayilir(motor_kur):
    m, _ = motor_kur(_ok(lambda s, b: (0, "sunucu=x\nUygulama Surumu: 1.4.2\n", "")))
    a = m.yurut(m.plan("betik_calistir", {"betik": "uygulama_surumu"}, "PA-APP-01"))
    r = a["sonuclar"][0]
    assert a["durum"] == "basarisiz" and r["durum"] == "hatali" and "surum" in r["sema_hatasi"]


def test_komutlar_aileye_gore_ve_tirnakli(motor_kur):
    m, t = motor_kur(_ok(lambda s, b: (0, "jq|1.6\n", "")))
    m.yurut(m.plan("paket_kur", {"paketler": ["jq"]}, "PA-APP-01,PA-APP-02,PA-DB-01"))
    betikler = {ad: b for ad, b in t.cagrilar if "filo-erisim-ok" not in b and "install" in b or "apk add" in b}
    assert "apt-get install" in betikler["PA-APP-01"] and "dnf install" in betikler["PA-APP-02"]
    assert "apk add" in betikler["PA-DB-01"]


def test_zincir_dusen_sunucuyu_sonraki_adima_sokmaz(motor_kur):
    def d(s, b):
        if s.ad == "PB-DB-01" and ("apt-get" in b or "dnf install" in b):
            return 1, "", "depo yok"
        if "sunucu=$(hostname)" in b and "kullanici=" in b:
            return 0, f"sunucu={s.ad}\nkullanici=filo\ncalisma_suresi=5\nsudo=var\n", ""
        if "isletim=" in b:
            return 0, (f"sunucu={s.ad}\nisletim=x\ncekirdek=1\nislemci=1\nbellek_mb=1\nkok_doluluk=1\n"
                       "calisma_suresi=1\n"), ""
        if "for p in" in b:
            return 0, "jq|1.6\ntree|2.1\n", ""
        if "base64 -d" in b:
            import hashlib
            from filo.beceri import DOSYALAR
            return 0, f"hedef=/etc/motd\nozet={hashlib.sha256((DOSYALAR / 'motd.txt').read_bytes()).hexdigest()}\n", ""
        if "yeni_ozet" in b:
            return 0, "durum=degisecek\n", ""
        return 0, "servis=uygulama\ndurum=active\n", ""
    m, t = motor_kur(_ok(d))
    a = m.yurut(m.plan("standart_sunucu_teslimi", {}, "PB*"))
    durum = {r["sunucu"]: r["durum"] for r in a["sonuclar"]}
    assert durum == {"PB-APP-01": "basarili", "PB-DB-01": "hatali", "PB-WEB-01": "basarili"}
    assert a["durum"] == "kismi"
    assert not any(ad == "PB-DB-01" and "base64 -d" in b for ad, b in t.cagrilar)
    assert a["sonuclar"][1]["veri"]["paket_kur"] == "hatali"


@pytest.mark.parametrize("bicim", ["csv", "xml", "json", "html"])
def test_donusturme_kismi_basarisizligi_tasir(bicim):
    adim = {"beceri": "betik_calistir", "surum": 1, "is_kimligi": "x", "ozet": {"basarili": 1, "toplam": 2},
            "sonuclar": [{"sunucu": "A", "durum": "basarili", "cikis_kodu": 0, "sure": 0.1, "kesildi": False,
                          "oykunme": False, "veri": {"surum": "1.4.2"}},
                         {"sunucu": "B", "durum": "erisilemedi", "cikis_kodu": None, "sure": 0, "kesildi": False,
                          "oykunme": False, "neden": "Connection refused"}]}
    ad, icerik, mime = rapor.donustur(adim, bicim)
    assert ad.endswith(bicim) and "erisilemedi" in icerik and "1.4.2" in icerik
    if bicim == "xml":
        kok = ET.fromstring(icerik.split("\n", 1)[1])
        assert [s.get("ad") for s in kok.findall("sunucu")] == ["A", "B"]
    if bicim == "json":
        assert len(json.loads(icerik)["sunucular"]) == 2


def test_eposta_alan_adi_izni():
    with pytest.raises(rapor.PostaReddi):
        rapor.eposta_gonder("a@kotu.example.org", "k", "g", ayar={"izinli_alanlar": ["lab.yerel"], "kimden": "f@lab.yerel",
                                                                 "sunucu": "127.0.0.1", "port": 1})


def test_betik_donustur_eposta_zinciri(motor_kur, monkeypatch):
    gonderilen = []
    monkeypatch.setattr(rapor, "eposta_gonder", lambda alici, konu, govde, ekler=(), ayar=None:
                        gonderilen.append((alici, konu, govde, list(ekler))) or "<id@x>")
    m, _ = motor_kur(_ok(lambda s, b: (0, f"sunucu={s.ad}\nsurum=1.4.2\n", "")))
    baglam = {"adimlar": []}
    for ad, p, h in (("betik_calistir", {"betik": "uygulama_surumu"}, "PA*"), ("sonucu_donustur", {"bicim": "xml"}, None),
                     ("eposta_gonder", {"alici": "ops@lab.yerel"}, None)):
        a = m.yurut(m.plan(ad, p, h), baglam)
        baglam["adimlar"].append(a)
        assert a["durum"] == "basarili", a
    alici, konu, govde, ekler = gonderilen[0]
    assert alici == "ops@lab.yerel" and ekler[0][0].endswith(".xml") and "4/4" in govde
