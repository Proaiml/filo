"""D1-D3: yama, yazılım politikası, uyum denetimi ve anlık görüntü (birim + sahte taşıyıcı + gerçek laboratuvar)."""
import json

import pytest

from filo import durum, duzelt, uyum, yama, yazilim_politikasi as yp
from filo.ajan_ortak import kod_parametreleri, talep_eylemleri
from filo.zamanli import yeniden_baslatma_ifadesini_cikar
from test_web import sunucu  # noqa: F401 (fixture)

APT = """bilgi|aile|debian
bilgi|acilis|a1
paket|filo-araclar|1.0.0-1|installed
paket|filo-kutuphane|2.0.0-1|installed
apt|Inst filo-araclar [1.0.0-1] (1.1.0-1 Filo-Lab:filo-lab [all])
apt|Inst filo-kutuphane [2.0.0-1] (2.0.1-1 Filo-Lab-Security:filo-lab-security [all])
yeniden|0|
"""
DNF = """bilgi|aile|rhel
paket|filo-araclar|1.0.0-1
paket|filo-cekirdek|5.10.0-1
dnf|filo-araclar.noarch                       1.1.0-1                      filo-depo
dnf|filo-cekirdek.noarch                      5.10.1-1                     filo-depo
dnfsec|FILO-SV-2026:filo-cekirdek  Important/Sec. filo-cekirdek-5.10.1-1.noarch
yeniden|1|filo-cekirdek
"""
APK = """bilgi|aile|alpine
apkv|filo-kutuphane-2.0.0-r0
apkv|filo-izleme-3.2.0-r0
apk|Installed:                                Available:
apk|filo-izleme-3.2.0-r0                    < 3.3.0-r0
apk|filo-kutuphane-2.0.0-r0                 < 2.0.1-r0
secdb|{"packages": [{"pkg": {"name": "filo-kutuphane", "secfixes": {"2.0.1-r0": ["LAB-2026-0001"]}}}]}
"""


def test_toplayici_ayristirma_uc_aile():
    a = durum.ayristir(APT, "X")
    assert [(g["paket"], g["guvenlik"]) for g in a["guncellemeler"]] == [("filo-araclar", False), ("filo-kutuphane", True)]
    d = durum.ayristir(DNF, "Y")
    assert {g["paket"]: g["guvenlik"] for g in d["guncellemeler"]} == {"filo-araclar": False, "filo-cekirdek": True}
    assert d["yeniden_baslatma"] and d["guncellemeler"][1]["kurulu"] == "5.10.0-1"
    k = durum.ayristir(APK, "Z")
    assert k["paketler"] == {"filo-kutuphane": "2.0.0-r0", "filo-izleme": "3.2.0-r0"}
    assert {g["paket"]: g["guvenlik"] for g in k["guncellemeler"]} == {"filo-izleme": False, "filo-kutuphane": True}
    for aile in ("debian", "rhel", "alpine"):     # toplayıcı salt-okurdur: koddan risk sınıflaması 0 kalmalı
        from filo.beceri import risk_sinifla
        b = durum.toplayici(aile, {"portlar": True, "dosyalar": ["/etc/motd"], "sysctl": ["kernel.randomize_va_space"]})
        assert risk_sinifla([b])[0] == 0, aile


def test_kapsam_haric_istisna_ve_suresi_dolan():
    import datetime
    gg = durum.ayristir(DNF, "PB-DB-01")["guncellemeler"]
    s, d, dolmus = yama.kapsam_sec(gg, "PB-DB-01", "hepsi", haric=[{"paket": "filo-araclar", "gerekce": "sabit"}],
                                   istisnalar=[{"sunucu": "PB-DB-01", "paket": "filo-cekirdek", "gerekce": "sertifika",
                                                "bitis": "2026-12-31"}], bugun=datetime.date(2026, 11, 17))
    assert s == [] and {x["paket"] for x in d} == {"filo-araclar", "filo-cekirdek"}
    s, d, dolmus = yama.kapsam_sec(gg, "PB-DB-01", "guvenlik", istisnalar=[{"sunucu": "PB-DB-01", "paket": "filo-cekirdek",
                                   "gerekce": "x", "bitis": "2026-01-01"}], bugun=datetime.date(2026, 11, 17))
    assert [g["paket"] for g in s] == ["filo-cekirdek"] and dolmus and "süresi doldu" in dolmus[0]["neden"]
    u = yama.uyum_degerlendir({"kapsam": "guvenlik"}, "X", gg)
    assert u["uyum"] == "uyumsuz" and u["eksik"] == 1
    assert yama.politika_dogrula({"kapsam": "hepsi", "haric": [{"paket": "a"}]})      # gerekçesiz hariç tutma reddedilir


def test_politika_sapma_ve_geri_alma_eylemleri():
    g = {"paketler": {"telnet": "0.17", "jq": "1.6"}, "servisler": {"webd": "inactive"}, "kullanicilar": {},
         "dosyalar": {"/etc/motd": {"var": True, "ozet": "x", "mod": "644"}}}
    pol = {"paketler": [{"ad": "jq", "durum": "kurulu"}, {"ad": "tree", "durum": "kurulu"}, {"ad": "telnet", "durum": "yok"}],
           "servisler": [{"ad": "webd", "durum": "calisiyor"}], "kullanicilar": [{"ad": "webops", "durum": "var"}],
           "dosyalar": [{"yol": "/etc/motd", "kaynak": "motd.txt", "mod": "0644"}]}
    f = yp.sapma(pol, g)
    assert [(x["tur"], x["ad"], x["eylem"]["tur"]) for x in f] == [
        ("paket", "tree", "paket_kur"), ("paket", "telnet", "paket_kaldir"), ("servis", "webd", "servis_baslat"),
        ("kullanici", "webops", "kullanici_ac"), ("dosya", "/etc/motd", "dosya_yaz")]
    assert all(x["geri_alinabilir"] for x in f)
    ge, _ = duzelt.geri_eylem({"tur": "paket_kaldir", "ad": "telnet"}, g)
    assert ge == {"tur": "paket_surum", "ad": "telnet", "surum": "0.17"}
    assert duzelt.geri_eylem({"tur": "kullanici_sil", "ad": "x"}, g)[0] is None
    # talepten politika: satır içi listeler
    p = yp.satir_icinden({"paketler_kurulu": ["jq"], "paketler_yok": ["telnet"]}, "t", "grup:web")
    assert p["atamalar"] == ["grup:web"] and [x["durum"] for x in p["paketler"]] == ["kurulu", "yok"]
    # teslim profili politikadan üretilir: eski web profiliyle aynı adımlar
    a = yp.teslim_adimlari(pol, ["paket", "servis"])
    assert [x["beceri"] for x in a] == ["paket_kur", "paket_dogrula", "kullanici_ac", "dosya_dagit", "servis_baslat", "servis_durumu"]
    assert a[0]["on_onayli"] and "on_onayli" not in a[2]


def test_eylem_betikleri_risk_ve_dogrulama():
    from filo.beceri import risk_sinifla
    assert risk_sinifla([duzelt.betik("debian", [{"tur": "paket_yukselt", "paketler": ["a"]}], "is1")])[0] == 3
    assert risk_sinifla([duzelt.betik("alpine", [{"tur": "kullanici_sil", "ad": "a"}], "is1")])[0] == 4
    with pytest.raises(duzelt.EylemHatasi):
        duzelt.dogrula({"tur": "paket_kur", "ad": "a; rm -rf /"})
    with pytest.raises(duzelt.EylemHatasi):
        duzelt.dogrula({"tur": "izin", "yol": "/etc/../x", "mod": "0644"})
    s = duzelt.sonuclari_ayristir("eylem|0|0|\neylem|1|3|sürüm depoda yok: a 1.0\n", [{"tur": "paket_kur", "ad": "a"}] * 2)
    assert [x["durum"] for x in s] == ["basarili", "hatali"] and "depoda yok" in s[1]["hata"]


def test_uyum_kurallari_ve_istisna(monkeypatch):
    kurallar = uyum.kural_setleri()["temel-sertlestirme"]["kurallar"]
    assert not [h for k in kurallar for h in uyum.kural_dogrula(k)]
    g = {"aile": "debian", "dosyalar": {"/etc/shadow": {"var": True, "mod": "644"}, "/etc/login.defs": {"var": True, "mod": "644"}},
         "icerik": {"parola-yaslanma": "0"}, "kullanicilar": {"eskiadmin": {}}, "portlar": ["tcp:22"],
         "sysctl": {"kernel.randomize_va_space": "2"}, "komutlar": {"tek-kok-hesap": {"rc": 0, "cikti": "1\n"}}}
    s = {k["kimlik"]: uyum.degerlendir(k, g)[0] for k in kurallar}
    assert s["shadow-izni"] == "ihlal" and s["parola-yaslanma"] == "ihlal" and s["eski-hesap-yok"] == "ihlal"
    assert s["telnet-kapali"] == "gecti" and s["aslr-acik"] == "gecti" and s["tek-kok-hesap"] == "gecti"
    from filo.envanter import Envanter
    d = uyum.denetle_goruntu("temel-sertlestirme", kurallar, "PB-DB-01", g, Envanter())
    r = {x["kural"]: x for x in d["kurallar"]}
    assert r["parola-yaslanma"]["sonuc"] == "istisna" and r["eski-hesap-yok"]["geri_alinabilir"] is False
    assert r["shadow-izni"]["geri_alinabilir"] is True
    assert uyum.kural_dogrula({"kimlik": "x1", "tur": "komut", "komut": "rm -rf /tmp/a"})     # yazan komut reddedilir


def test_karsilastirma_ve_fark_metni():
    a = {"paketler": {"jq": "1.6", "tree": "2"}, "servisler": {"webd": "active"}, "kullanicilar": {"x": {}},
         "dosyalar": {"/etc/motd": {"var": True, "ozet": "a", "mod": "644"}}, "portlar": ["tcp:22"], "sysctl": {}}
    b = {"paketler": {"jq": "1.7"}, "servisler": {"webd": "inactive"}, "kullanicilar": {"x": {}, "y": {}},
         "dosyalar": {"/etc/motd": {"var": True, "ozet": "b", "mod": "644"}}, "portlar": ["tcp:22", "tcp:23"], "sysctl": {}}
    f = durum.karsilastir(a, b)
    assert f["toplam"] == 6
    m = " | ".join(durum.fark_metni(f))
    assert "tree" in m and "jq 1.6 → 1.7" in m and "tcp:23" in m and "webd active → inactive" in m and "y" in m


def test_talepten_kod_parametreleri_ve_zamanlama_ayirma():
    from filo.beceri import Katalog
    k = Katalog()
    adlar = ["PA-WEB-01", "PB-WEB-01", "PA-APP-01", "PB-APP-01"]
    t = ("web grubuna bekleyen yamaları önce PA-WEB-01'de dene, sorun yoksa diğerlerine uygula; yeniden başlatma bakım "
         "penceresinde olsun")
    p = kod_parametreleri(k["yama_uygula"]["girdi"], t, adlar)
    assert p == {"yeniden_baslatma": "pencerede", "kapsam": "hepsi", "test_grubu": "PA-WEB-01"}
    assert "bakım" not in yeniden_baslatma_ifadesini_cikar(t)
    assert kod_parametreleri(k["goruntu_karsilastir"]["girdi"], "PB-APP-01'i PA-APP-01'e göre karşılaştır", adlar) == \
        {"referans": "PA-APP-01"}
    assert kod_parametreleri(k["uyum_duzelt"]["girdi"], "temel sertleştirme denetimini çalıştır, yalnız geri alınabilir "
                             "olanları düzelt", adlar) == {"yalniz_geri_alinabilir": True, "kural_seti": "temel-sertlestirme"}
    assert [a for a, _, _ in talep_eylemleri(k, t)] == ["yeniden başlatma", "yama uygulama"]
    assert not talep_eylemleri(k, "PB-APP-01 ve PC-BATCH-01 sunucularında bekleyen yama sayısını topla, CSV yap")


class _Motor:
    """Toplu işleyicileri sahte yürütücüyle sınamak için en küçük motor."""
    def __init__(self, motor, davranis):
        self.m = motor
        self.envanter, self.katalog = motor.envanter, motor.katalog
        self.yurutucu = motor.yurutucu
        self.pencereler = None
        self._pencereler = motor._pencereler


def test_asamali_dagitim_test_grubu_duserse_kalanlar_baslamaz(motor_kur):
    cagri = []

    def dav(s, b):
        cagri.append((s.ad, "eylem" if "eylem|" in b else "toplama"))
        if "eylem|" in b:
            return (0, "eylem|0|100|E: kurulamadı\n", "") if s.ad == "PA-WEB-01" else (0, "eylem|0|0|\n", "")
        return 0, APT.replace("debian", s.aile), ""
    m, _ = motor_kur(dav)
    sonuc = yama.isleyici_uygula([m.envanter["PA-WEB-01"], m.envanter["PB-WEB-01"]],
                                 {"kapsam": "hepsi", "test_grubu": "PA-WEB-01", "yeniden_baslatma": "asla"},
                                 motor=m, plan={"is_kimligi": "deneme1"})
    r = {x["sunucu"]: x for x in sonuc}
    assert r["PA-WEB-01"]["durum"] == "hatali" and r["PB-WEB-01"]["durum"] == "iptal"
    assert "test grubu başarısız" in r["PB-WEB-01"]["neden"]
    assert ("PB-WEB-01", "eylem") not in cagri and ("PB-WEB-01", "toplama") not in cagri


# ---------------------------------------------------------------- gerçek laboratuvar
@pytest.fixture
def lab_motoru(tmp_path):
    from filo import lab
    from filo.denetim import Denetim
    from filo.teslim import motor_olustur
    lab.sifirla(["PA-WEB-01", "PB-APP-01", "PA-APP-02"])
    yield motor_olustur("bench", {"varsayilan": "onayla"}, Denetim(tmp_path / "d.jsonl"))
    lab.sifirla(["PA-WEB-01", "PB-APP-01", "PA-APP-02"])


def _kos(m, ad, p, hedef, kuru=False):
    plan = m.plan(ad, p, hedef)
    if kuru:
        return {r["sunucu"]: r for r in m.kuru_calistir(plan)}
    return {r["sunucu"]: r for r in m.yurut(plan, {})["sonuclar"]}


@pytest.mark.lab
def test_lab_yama_uygula_yeniden_baslat_geri_al(lab_motoru):
    from filo import lab
    m = lab_motoru
    d = _kos(m, "yama_durumu", {}, "PA-WEB-01,PB-APP-01,PA-APP-02")
    assert all("bekleyen=4" in d[a]["stdout"] and "guvenlik=2" in d[a]["stdout"] for a in d)
    k = _kos(m, "yama_uygula", {"kapsam": "guvenlik"}, "PA-WEB-01", kuru=True)
    assert "filo-kutuphane" in k["PA-WEB-01"]["stdout"]
    assert lab.dexec("filo-pa-web-01", "cat /usr/lib/filo-ornek/filo-kutuphane.surum")[1].strip() == "2.0.0"   # kuru: değişmedi
    u = _kos(m, "yama_uygula", {"kapsam": "guvenlik", "yeniden_baslatma": "gerekirse"}, "PA-WEB-01,PB-APP-01,PA-APP-02")
    for a, kont in (("PA-WEB-01", "filo-pa-web-01"), ("PB-APP-01", "filo-pb-app-01"), ("PA-APP-02", "filo-pa-app-02")):
        assert u[a]["durum"] == "basarili", u[a]
        assert "yeniden_baslatma=yapildi" in u[a]["stdout"]
        assert lab.dexec(kont, "cat /usr/lib/filo-ornek/filo-kutuphane.surum")[1].strip() == "2.0.1"
        assert lab.dexec(kont, "cat /usr/lib/filo-ornek/filo-araclar.surum")[1].strip() == "1.0.0"    # kapsam: yalnız güvenlik
        assert "yeniden_baslatma" in lab.dexec(kont, "cat /var/log/filo/yeniden-baslatma.log")[1]
    g = _kos(m, "yama_geri_al", {}, "PA-WEB-01,PB-APP-01,PA-APP-02")
    assert all(g[a]["durum"] == "basarili" for a in g), g
    assert lab.dexec("filo-pb-app-01", "cat /usr/lib/filo-ornek/filo-kutuphane.surum")[1].strip() == "2.0.0"


@pytest.mark.lab
def test_lab_politika_idempotent_ve_uyum_duzelt(lab_motoru):
    from filo import lab
    m = lab_motoru
    p = {"paketler_kurulu": ["jq"], "paketler_yok": ["filo-izleme"], "ad": "sinama-politikasi"}
    a = _kos(m, "yazilim_politikasi_uygula", p, "PA-WEB-01,PB-APP-01,PA-APP-02")
    assert all(x["durum"] == "basarili" and "duzeltilen=2" in x["stdout"] for x in a.values()), a
    b = _kos(m, "yazilim_politikasi_uygula", p, "PA-WEB-01,PB-APP-01,PA-APP-02")
    assert all("duzeltilen=0" in x["stdout"] for x in b.values())          # ikinci koşu hiçbir şey yapmaz
    geri = _kos(m, "yazilim_politikasi_geri_al", {}, "PB-APP-01")
    assert geri["PB-APP-01"]["durum"] == "basarili"
    assert lab.dexec("filo-pb-app-01", "apk info -e filo-izleme >/dev/null && echo var")[1].strip() == "var"
    d = _kos(m, "uyum_duzelt", {"kural_seti": "temel-sertlestirme"}, "PB-APP-01")
    assert "eski-hesap-yok: geri alınamaz" in d["PB-APP-01"]["stdout"]
    assert lab.dexec("filo-pb-app-01", "id eskiadmin >/dev/null 2>&1 && echo var")[1].strip() == "var"
    assert lab.dexec("filo-pb-app-01", "stat -c %a /etc/uygulama/uygulama.conf")[1].strip() == "640"
    c = _kos(m, "goruntu_karsilastir", {"referans": "PA-WEB-01"}, "PB-APP-01")
    assert "fark=" in c["PB-APP-01"]["stdout"]
    _ = json


def test_kalfa_yama_talebi_kod_parametreleri_ve_zamanlama_degil(motor_kur, tmp_path):
    """Y04 benzeri talep: model yalnız beceriyi ve hedefi seçer; kapsam, test grubu, yeniden başlatma politikası koddan
    gelir; 'yeniden başlatma bakım penceresinde' işin zamanlaması sayılmaz (iş şimdi çalışır)."""
    from filo.gateway import FakeModel
    from filo.kalfa import Kalfa
    from test_ajanlar import Senaryo, kayit
    talep = ("PA-WEB-01 ve PB-WEB-01 sunucularına bekleyen yamaları önce PA-WEB-01'de dene, sorun yoksa PB-WEB-01'e de "
             "uygula; yeniden başlatma bakım penceresinde olsun. Sonucu ops@lab.yerel adresine bildir.")
    m, _ = motor_kur()
    sc = Senaryo(beceri={"secim": "yama_uygula"}, hedef={"ad": "PA-WEB-01,PB-WEB-01"}, param={"haric": []})
    k = Kalfa(FakeModel(islev=sc), m, kayit(tmp_path, talep, "kalfa")).planla(talep)
    assert k.durum == "plan_hazir", k.rapor
    p = k.plan["ana"]["parametreler"]
    assert p["kapsam"] == "hepsi" and p["test_grubu"] == "PA-WEB-01" and p["yeniden_baslatma"] == "pencerede"
    assert not k.plan.get("zamanlama") and not k.plan.get("eksik")
    assert k.plan["ana"]["risk"] == 3


def test_konsol_yama_politika_uyum_uclari(sunucu, tmp_path):
    """D4: yeni sayfalar ve veri uçları; ayar kaydı yalıtılmış kopyada (depodaki ayarlar değişmez)."""
    from test_web import _al, _gonder
    import urllib.request
    _, t = sunucu
    durum.yalit(tmp_path / "yalit")
    try:
        for sayfa in ("/yama", "/politikalar", "/uyum"):
            with urllib.request.urlopen(t + sayfa, timeout=30) as r:
                assert b"uyum.js" in r.read()
        y = _al(t, "/api/yama")
        assert {p["ad"] for p in y["politikalar"]} >= {"guvenlik-standart", "web-aylik"}
        assert next(p for p in y["politikalar"] if p["ad"] == "web-aylik")["sunucular"] == ["PA-WEB-01", "PB-WEB-01"]
        p = _al(t, "/api/politikalar")
        assert next(x for x in p["politikalar"] if x["ad"] == "web-standardi")["teslim_profilleri"] == ["web"]
        u = _al(t, "/api/uyum")
        assert u["kural_setleri"][0]["ad"] == "temel-sertlestirme" and u["istisnalar"]
        s, r = _gonder(t, "/api/yama/politika", {"ad": "db-aylik", "politika": {"hedef": "grup:db", "kapsam": "hepsi",
                                                                               "haric": [{"paket": "x"}]}})
        assert s == 400 and "gerekçe" in r["hata"]
        s, r = _gonder(t, "/api/yama/politika", {"ad": "db-aylik", "politika": {"hedef": "grup:db", "kapsam": "hepsi"}})
        assert s == 200 and r["surum"] == 1
        s, r = _gonder(t, "/api/uyum/istisna", {"kural_seti": "temel-sertlestirme", "kural": "eski-hesap-yok",
                                                "sunucu": "PA-APP-01", "gerekce": "DEĞ-1", "bitis": "2027-01-01"})
        assert s == 200 and len(uyum.istisnalar()) == 2
        assert _gonder(t, "/api/yama/politika", {"ad": "x", "politika": {}}, baslik=False)[0] == 403
    finally:
        durum.yalitimi_kaldir()
    assert "db-aylik" not in yama.politikalar()          # depodaki ayar dosyası değişmedi