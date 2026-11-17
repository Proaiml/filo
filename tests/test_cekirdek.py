"""A1: envanter, erişim izin listesi, yürütücü, denetim izi."""
import pytest

from conftest import FakeTasiyici
from filo.envanter import SeciciHatasi, secici_coz
from filo.erisim import Erisilemedi, Oykunucu, ZamanAsimi, salt_okur_denetle
from filo.yurutme import DURUMLAR, SONUC_ALANLARI, Yurutucu, ozetle


# ---------------------------------------------------------------- envanter
def test_ad_kalibi_ve_dondurma(envanter):
    adlar = [s.ad for s in envanter.sec("PA*")]
    assert adlar == ["PA-APP-01", "PA-APP-02", "PA-DB-01", "PA-WEB-01"]
    d = envanter.dondur("PA*")
    assert d["sunucular"] == adlar and d["sayi"] == 4 and d["ozet"]


def test_secici_kosullari(envanter):
    assert [s.ad for s in envanter.sec("grup:web")] == ["PA-WEB-01", "PB-WEB-01"]
    assert [s.ad for s in envanter.sec("os:windows")] == ["PW-WIN-01"]
    assert [s.ad for s in envanter.sec("aile:alpine ortam=prod")] == ["PB-APP-01", "PC-BATCH-01"]
    assert [s.ad for s in envanter.sec("PA* !PA-DB-01")] == ["PA-APP-01", "PA-APP-02", "PA-WEB-01"]
    assert [s.ad for s in envanter.sec({"ad": "PA-APP-01,PB-DB-01"})] == ["PA-APP-01", "PB-DB-01"]
    assert secici_coz("PA* grup:web x=1 !Y") == {"ad": "PA*", "grup": "web", "oznitelik": {"x": "1"}, "haric": ["Y"]}


def test_secici_hatalari(envanter):
    with pytest.raises(SeciciHatasi):
        envanter.sec("grup:yok")
    with pytest.raises(SeciciHatasi):
        envanter.sec({})
    with pytest.raises(SeciciHatasi):
        envanter.dondur("ZZ*")


# ---------------------------------------------------------------- salt-okur izin listesi
@pytest.mark.parametrize("komut", ["hostname; uname -r", "df -h | grep veri", "cat /etc/os-release",
                                   "systemctl status uygulama", "rc-service uygulama status", "ls /veri 2>/dev/null",
                                   "dpkg -l | grep jq", "rpm -qa"])
def test_salt_okur_kabul(komut):
    assert salt_okur_denetle(komut) is None


@pytest.mark.parametrize("komut", ["rm -rf /", "echo x > /etc/passwd", "sudo cat /etc/shadow", "systemctl restart x",
                                   "hostname; reboot", "cat $(echo /etc/x)", "find / -delete", "sleep 10 &",
                                   "rc-service x restart", "apk add jq", "`id`"])
def test_salt_okur_ret(komut):
    assert salt_okur_denetle(komut)


def test_oykunucu_etiketli(envanter):
    rc, out, err = Oykunucu().calistir(envanter["PW-WIN-01"], "#filo:servis\n$s = Get-Service -Name uygulama")
    assert rc == 0 and "durum=active" in out
    rc, out, err = Oykunucu().calistir(envanter["PW-WIN-01"], "Get-Bilinmeyen")
    assert rc == 1 and "öykünücü" in err


# ---------------------------------------------------------------- yürütücü
def _yurutucu(envanter, denetim, durdurma, davranis, **kw):
    t = FakeTasiyici(davranis)
    return Yurutucu(envanter, denetim=denetim, durdurma=durdurma, tasiyici_fn=lambda s: t, **kw), t


def test_tek_sema_ve_durumlar(envanter, denetim, durdurma):
    def d(s, b):
        if s.ad == "PA-APP-02":
            return 3, "", "hata"
        if s.ad == "PA-DB-01":
            raise ZamanAsimi("5 sn")
        if s.ad == "PA-WEB-01":
            raise Erisilemedi("Connection refused")
        return 0, "tamam\n", ""
    y, t = _yurutucu(envanter, denetim, durdurma, d)
    sonuc = y.yelpaze(["PA-APP-01", "PA-APP-02", "PA-DB-01", "PA-WEB-01"], "x", 5, yeniden_deneme=2)
    assert [r["durum"] for r in sonuc] == ["basarili", "hatali", "zaman_asimi", "erisilemedi"]
    for r in sonuc:
        assert set(SONUC_ALANLARI) <= set(r) and r["durum"] in DURUMLAR
    # yalnız başarısızlar yeniden denendi, deneme sayısı sınırlı (1 + 2)
    sayac = {}
    for ad, _ in t.cagrilar:
        sayac[ad] = sayac.get(ad, 0) + 1
    assert sayac == {"PA-APP-01": 1, "PA-APP-02": 3, "PA-DB-01": 3, "PA-WEB-01": 3}
    oz = ozetle(sonuc)
    assert oz["kismi"] and oz["basarili"] == 1 and oz["toplam"] == 4
    assert denetim.oku(tur="yurutme")


def test_yeniden_denemede_duzelen(envanter, denetim, durdurma):
    say = {"n": 0}

    def d(s, b):
        say["n"] += 1
        if say["n"] == 1:
            raise Erisilemedi("geçici")
        return 0, "ok", ""
    y, t = _yurutucu(envanter, denetim, durdurma, d)
    r = y.yelpaze(["PA-APP-01"], "x", 5, yeniden_deneme=2)[0]
    assert r["durum"] == "basarili" and r["deneme"] == 2


def test_zaman_asimi_zorunlu(envanter, denetim, durdurma):
    y, _ = _yurutucu(envanter, denetim, durdurma, lambda s, b: (0, "", ""))
    with pytest.raises(ValueError):
        y.yelpaze(["PA-APP-01"], "x", 0)


def test_cikti_siniri_kesildi(envanter, denetim, durdurma):
    y, _ = _yurutucu(envanter, denetim, durdurma, lambda s, b: (0, "a" * 5000, ""), cikti_siniri=1000)
    r = y.yelpaze(["PA-APP-01"], "x", 5)[0]
    assert r["kesildi"] is True and len(r["stdout"]) == 1000


def test_durdurma_dugmesi_iptal(envanter, denetim, durdurma):
    y, t = _yurutucu(envanter, denetim, durdurma, lambda s, b: (0, "ok", ""))
    durdurma.bas("test")
    sonuc = y.yelpaze(["PA-APP-01", "PA-APP-02"], "x", 5)
    assert [r["durum"] for r in sonuc] == ["iptal", "iptal"] and not t.cagrilar
    durdurma.kaldir()
    assert y.yelpaze(["PA-APP-01"], "x", 5)[0]["durum"] == "basarili"


def test_erisim_sinamasi_ayirir(envanter, denetim, durdurma):
    def d(s, b):
        if s.ad == "PA-DB-01":
            raise Erisilemedi("Connection refused")
        return 0, "filo-erisim-ok\n" if "filo-erisim-ok" in b else "is\n", ""
    y, t = _yurutucu(envanter, denetim, durdurma, d)
    sonuc = y.is_yurut(["PA-APP-01", "PA-DB-01"], "is", 5)
    assert [(r["sunucu"], r["durum"]) for r in sonuc] == [("PA-APP-01", "basarili"), ("PA-DB-01", "erisilemedi")]
    assert sonuc[1].get("on_sinama") is True
    # erişilemeyene asıl iş gönderilmedi
    assert not any(ad == "PA-DB-01" and "filo-erisim-ok" not in b for ad, b in t.cagrilar)


def test_os_icin_komut_yoksa_tekrar_denenmez(envanter, denetim, durdurma):
    y, t = _yurutucu(envanter, denetim, durdurma, lambda s, b: (0, "", ""))
    r = y.yelpaze(["PW-WIN-01"], lambda s: None, 5, yeniden_deneme=2)[0]
    assert r["durum"] == "hatali" and r["deneme"] == 1


# ---------------------------------------------------------------- denetim izi
def test_denetim_zinciri_ve_maskeleme(denetim):
    denetim.yaz("talep", metin="x", parola="gizli123", alt={"api_key": "abc"})
    denetim.yaz("plan", beceri="disk_durumu", ozet={"basarili": 3}, onceki="x")   # yük alanı zincir alanını ezmez
    ok, n, _ = denetim.dogrula()
    assert ok and n == 2
    assert denetim.oku(tur="plan")[0]["ozet"] == {"basarili": 3}
    metin = denetim.yol.read_text(encoding="utf-8")
    assert "gizli123" not in metin and "abc" not in metin
    satirlar = metin.splitlines()
    satirlar[0] = satirlar[0].replace('"metin": "x"', '"metin": "y"')
    denetim.yol.write_text("\n".join(satirlar) + "\n", encoding="utf-8")
    assert denetim.dogrula()[0] is False
