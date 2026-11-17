"""Ajan kapısı: imza, kayıt, kalp, uzun yoklama, iş/sonuç, taşıyıcı seçimi (sahte ajanla; laboratuvar gerekmez)."""
import json
import threading
import time
import urllib.error
import urllib.request
import uuid

import pytest

from filo import ajan_istemci
from filo.ajan_kapisi import (AjanKapisi, Defter, anahtar_turet, is_zarfi, istek_imzasi, yanit_imzasi)
from filo.denetim import Denetim
from filo.envanter import Envanter, Sunucu
from filo.erisim import Durdurma, SSHTasiyici, tasiyici_sec
from filo.yurutme import Yurutucu

GIZLI = "11" * 32


def test_capraz_dil_imza_ornegi():
    # ajan/ajan_test.go TestCaprazDilImzaOrnegi ile aynı değerler
    ist, is_a = anahtar_turet(GIZLI)
    assert istek_imzasi(ist, "POST", "/ajan/v1/kalp", "1700000000", "abc", b'{"a":1}') == \
        "f2afbca3d724ce59c012cafd270d78e81f384934d247f31ff4c63edc467cc51e"
    assert yanit_imzasi(is_a, "abc", b'{"a":1}') == "6ecc4b57561c813290ed33942b82f5e034e15a260d544f32be5569af8564b24d"
    z = is_zarfi(is_a, {"kimlik": "x"})
    assert z["govde"] == '{"kimlik":"x"}' and z["imza"] == "bd19c45e981e7b75241cb419ffcbbc39a09e1e70a972361e0718701fb6475833"


class SahteAjan:
    """Go ajanının protokolünü Python'da konuşan sınama ajanı."""

    def __init__(self, adres):
        self.adres, self.kimlik, self.gizli = adres, None, None

    def _istek(self, yol, govde=None, yontem="POST", imzala=True, nonce=None, zaman=None, anahtar=None):
        veri = json.dumps(govde).encode() if govde is not None else b""
        req = urllib.request.Request(self.adres + yol, data=veri if yontem == "POST" else None, method=yontem)
        n = nonce or uuid.uuid4().hex
        if imzala and self.kimlik:
            ist, _ = anahtar_turet(anahtar or self.gizli)
            z = str(int(zaman or time.time()))
            req.add_header("X-Filo-Ajan", self.kimlik)
            req.add_header("X-Filo-Zaman", z)
            req.add_header("X-Filo-Nonce", n)
            req.add_header("X-Filo-Imza", istek_imzasi(ist, yontem, yol.split("?")[0], z, n, veri))
        with urllib.request.urlopen(req, timeout=40) as r:
            ham = r.read()
            if imzala and self.kimlik:
                _, is_a = anahtar_turet(self.gizli)
                assert r.headers["X-Filo-Imza"] == yanit_imzasi(is_a, n, ham), "cevap imzası tutmuyor"
            return json.loads(ham) if r.headers.get("Content-Type", "").startswith("application/json") else ham

    def kayit(self, belirtec, sunucu):
        c = self._istek("/ajan/v1/kayit", {"belirtec": belirtec, "sunucu": sunucu, "surum": "test", "sistem": {}},
                        imzala=False)
        self.kimlik, self.gizli = c["ajan_kimligi"], c["gizli"]
        return c

    def is_dongusu(self, n=1, islev=None):
        """n işi alıp `islev(iş) -> sonuç` ile cevaplar."""
        _, is_a = anahtar_turet(self.gizli)
        yapilan = 0
        while yapilan < n:
            c = self._istek("/ajan/v1/yokla", {"bekle": 5})
            for z in c["isler"]:
                import hmac
                import hashlib
                assert hmac.compare_digest(hmac.new(is_a, ("is\n" + z["govde"]).encode(), hashlib.sha256).hexdigest(),
                                           z["imza"])
                is_ = json.loads(z["govde"])
                self._istek("/ajan/v1/sonuc", {"kimlik": is_["kimlik"], **islev(is_)})
                yapilan += 1


@pytest.fixture
def kapi(tmp_path):
    d = Denetim(tmp_path / "denetim.jsonl")
    k = AjanKapisi(port=0, defter=Defter(tmp_path / "ajanlar", tmp_path / "ajan_gizli.json"), denetim=d,
                   durdurma=Durdurma(tmp_path / "DURDUR")).baslat()
    yield k
    k.durdur()


def _adres(k):
    return f"http://127.0.0.1:{k.port}"


def test_belirtec_tek_kullanimlik_ve_sunucuya_bagli(kapi):
    b = kapi.belirtec_uret("PA-APP-01")
    a = SahteAjan(_adres(kapi))
    with pytest.raises(urllib.error.HTTPError) as e:
        a.kayit(b, "PA-APP-02")
    assert e.value.code == 403
    b2 = kapi.belirtec_uret("PA-APP-01")
    a.kayit(b2, "PA-APP-01")
    assert a.kimlik.startswith("ajan-")
    with pytest.raises(urllib.error.HTTPError) as e:
        SahteAjan(_adres(kapi)).kayit(b2, "PA-APP-01")
    assert e.value.code == 401
    # belirteç diskte yalnız özet olarak durur
    assert b2 not in (kapi.defter.belirtec_yolu.read_text(encoding="utf-8"))
    assert a.gizli not in kapi.defter.kayit_yolu.read_text(encoding="utf-8")


def test_imzasiz_sahte_ve_tekrarlanan_istek_reddedilir(kapi):
    a = SahteAjan(_adres(kapi))
    a.kayit(kapi.belirtec_uret("PA-APP-01"), "PA-APP-01")
    assert a._istek("/ajan/v1/kalp", {"surum": "t"}) == {"iptal": []}
    for kw in ({"imzala": False}, {"anahtar": "22" * 32}, {"zaman": time.time() - 600}):
        with pytest.raises(urllib.error.HTTPError) as e:
            if kw.get("imzala") is False:
                a2 = SahteAjan(_adres(kapi))
                a2._istek("/ajan/v1/kalp", {"surum": "t"}, imzala=False)
            else:
                a._istek("/ajan/v1/kalp", {"surum": "t"}, **kw)
        assert e.value.code == 401
    a._istek("/ajan/v1/kalp", {"surum": "t"}, nonce="ayni-nonce")
    with pytest.raises(urllib.error.HTTPError) as e:
        a._istek("/ajan/v1/kalp", {"surum": "t"}, nonce="ayni-nonce")
    assert e.value.code == 401


def test_is_ajandan_gider_sonuc_ayni_semada(kapi):
    a = SahteAjan(_adres(kapi))
    a.kayit(kapi.belirtec_uret("PA-APP-01"), "PA-APP-01")
    t = threading.Thread(target=a.is_dongusu, args=(1, lambda is_: {
        "durum": "basarili", "cikis_kodu": 0, "stdout": "PA-APP-01\n" if "hostname" in is_["betik"] else "",
        "stderr": "", "sure": 0.1, "kesildi": True}), daemon=True)
    t.start()
    tas = ajan_istemci.AjanTasiyici(Durdurma(kapi.defter.dizin / "DURDUR"), _adres(kapi), kapi.yerel_anahtar)
    s = Sunucu("PA-APP-01", "linux", "debian", "127.0.0.1")
    rc, out, err = tas.calistir(s, "hostname", 10)
    assert (rc, out) == (0, "PA-APP-01\n") and tas.kesildi
    t.join(5)


def test_ajan_almazsa_ssh_yedegine_duser(kapi, monkeypatch):
    a = SahteAjan(_adres(kapi))
    a.kayit(kapi.belirtec_uret("PA-APP-01"), "PA-APP-01")
    kapi.alim_suresi = 1                     # sahte ajan yoklamıyor: iş 1 sn içinde alınmaz
    yt = ajan_istemci.YedekliTasiyici()
    yt.ajan = ajan_istemci.AjanTasiyici(Durdurma(kapi.defter.dizin / "DURDUR"), _adres(kapi), kapi.yerel_anahtar)
    monkeypatch.setattr(SSHTasiyici, "calistir", lambda self, s, b, z=60: (0, "ssh-yolu\n", ""))
    s = Sunucu("PA-APP-01", "linux", "debian", "127.0.0.1")
    rc, out, err = yt.calistir(s, "hostname", 10)
    assert out == "ssh-yolu\n" and yt.ad == "ssh" and "SSH'a düşüldü" in yt.not_


def test_tasiyici_secimi_ve_denetim_izinde_yol(tmp_path, monkeypatch):
    s = Sunucu("PA-APP-01", "linux", "debian", "127.0.0.1", kimlik="lab-anahtar")
    assert isinstance(tasiyici_sec(s, ajan_sor=lambda ad: False), SSHTasiyici)
    assert isinstance(tasiyici_sec(s, ajan_sor=lambda ad: True), ajan_istemci.YedekliTasiyici)

    class Sahte:
        ad = "ajan"
        not_ = ""
        kesildi = False

        def calistir(self, sunucu, betik, zaman_asimi=60):
            return 0, "tamam\n", ""
    d = Denetim(tmp_path / "d.jsonl")
    y = Yurutucu(Envanter(sunucular=[s]), denetim=d, tasiyici_fn=lambda x: Sahte())
    r = y.yelpaze(["PA-APP-01"], "true", 10)
    assert r[0]["tasiyici"] == "ajan"
    satir = [x for x in d.oku(10) if x["tur"] == "yurutme"][0]
    assert satir["sunucular"]["PA-APP-01"]["tasiyici"] == "ajan"


def test_durdurma_ajan_isini_iptal_eder(kapi):
    a = SahteAjan(_adres(kapi))
    a.kayit(kapi.belirtec_uret("PA-APP-01"), "PA-APP-01")
    dur = Durdurma(kapi.defter.dizin / "DURDUR")
    tas = ajan_istemci.AjanTasiyici(dur, _adres(kapi), kapi.yerel_anahtar)
    sonuc = {}

    def calis():
        try:
            tas.calistir(Sunucu("PA-APP-01", "linux", "debian", "127.0.0.1"), "sleep 30", 60)
        except Exception as e:  # noqa: BLE001
            sonuc["hata"] = type(e).__name__
    th = threading.Thread(target=calis, daemon=True)
    th.start()
    c = a._istek("/ajan/v1/yokla", {"bekle": 5})
    assert len(c["isler"]) == 1
    dur.bas("test")
    th.join(10)
    assert sonuc.get("hata") == "Iptal"


def test_kaldirilan_ajan_410_alir(kapi):
    a = SahteAjan(_adres(kapi))
    a.kayit(kapi.belirtec_uret("PA-APP-01"), "PA-APP-01")
    assert kapi.kaldir("PA-APP-01") == 1
    with pytest.raises(urllib.error.HTTPError) as e:
        a._istek("/ajan/v1/kalp", {"surum": "t"})
    assert e.value.code == 410
    assert kapi.durumlar() == {}
