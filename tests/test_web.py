"""A4: arayüz API'si üzerinden uçtan uca talep (gerçek HTTP sunucusu, FakeModel)."""
import json
import threading
import time
import urllib.error
import urllib.request

import pytest

from conftest import FakeTasiyici
from filo import web
from filo.gateway import FakeModel
from filo.kalfa import Kalfa
from filo.yurutme import Yurutucu


def _senaryo(mesajlar):
    ilk = next(m["content"] for m in mesajlar if m["role"] == "user")
    if "ANA işini" in ilk:
        return {"secim": "paket_kur", "gerekce": "paket kurulumu"}
    if "seçiciyle yaz" in ilk:
        return {"ad": "PB-WEB-01"}
    if "Seçilen beceri:" in ilk:
        return {"paketler": ["jq"]}
    return {"yorum": "-"}


@pytest.fixture
def sunucu(tmp_path, monkeypatch, denetim, onaylar):
    monkeypatch.setattr(web, "DENETIM", denetim)
    ofis = web.Ofis()
    ofis.onaylar = onaylar
    ofis.motor.politika.onaylar = onaylar
    ofis.motor.denetim = denetim
    ofis.motor.katalog.denetim = denetim
    monkeypatch.setattr(ofis, "_ajan", lambda ajan, baglanti, kayit: Kalfa(FakeModel(islev=_senaryo), ofis.motor, kayit,
                                                                           onay_bekle_sn=30))
    import http.server
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), web.make_handler(ofis))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield ofis, f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()


def _al(t, yol):
    with urllib.request.urlopen(t + yol, timeout=30) as r:
        return json.loads(r.read())


def _gonder(t, yol, govde, baslik=True):
    req = urllib.request.Request(t + yol, json.dumps(govde).encode(),
                                 {"Content-Type": "application/json", **({"X-Filo": "1"} if baslik else {})})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def _bekle(t, kimlik, durumlar, sure=60):
    son = time.time() + sure
    while time.time() < son:
        d = _al(t, f"/api/is?kimlik={kimlik}")
        if d["durum"] in durumlar:
            return d
        time.sleep(0.3)
    raise AssertionError(f"beklenen durum gelmedi: {d['durum']}")


def _uctan_uca(t):
    s, k = _gonder(t, "/api/talep", {"metin": "PB-WEB-01 sunucusuna jq paketini kur", "ajan": "kalfa"})
    assert s == 200
    d = _bekle(t, k["kimlik"], ("plan_hazir", "hata"))
    assert d["durum"] == "plan_hazir", d
    assert d["plan"]["ana"]["hedef"]["sunucular"] == ["PB-WEB-01"] and d["plan"]["ana"]["onay_gerekli"]
    assert _gonder(t, "/api/is/yurut", {"kimlik": k["kimlik"]})[0] == 200
    d = _bekle(t, k["kimlik"], ("onay_bekliyor",))
    bekleyen = _al(t, "/api/onaylar")
    assert bekleyen[0]["beceri"] == "paket_kur" and bekleyen[0]["kuru"]
    assert _gonder(t, "/api/onay", {"kimlik": d["onay"]["kimlik"], "karar": "ver"})[0] == 200
    return _bekle(t, k["kimlik"], ("bitti", "kismi", "basarisiz", "hata"), 240)


def test_web_talep_onay_yurutme_sahte_tasiyici(sunucu, envanter, denetim):
    ofis, t = sunucu
    kurulu = []

    def d(s, b):
        if "filo-erisim-ok" in b:
            return 0, "filo-erisim-ok\n", ""
        if "apt-get install -y" in b:
            kurulu.append(s.ad)
        return 0, "jq|1.6\n", ""
    tas = FakeTasiyici(d)
    ofis.motor.yurutucu = Yurutucu(envanter, denetim=denetim, tasiyici_fn=lambda s: tas)
    son = _uctan_uca(t)
    assert son["durum"] == "bitti" and kurulu == ["PB-WEB-01"]
    assert son["izgara"]["PB-WEB-01"]["durum"] == "basarili"
    turler = {r["tur"] for r in _al(t, "/api/denetim?limit=100")["satirlar"]}
    assert {"talep", "plan", "kuru_calistirma", "onay_istendi", "onay_verildi", "adim"} <= turler
    assert _al(t, "/api/denetim")["zincir"]["saglam"]


def test_web_kaptan_inisiyatif_ve_beceriye_donusturme(tmp_path, monkeypatch, denetim, onaylar, envanter, katalog_dizini):
    """/kaptan yolu: düzey 3 ile talep → akış → yürütme → bitti → Beceriye dönüştür → katalogda v1;
    sonra /kalfa 'beceriden başla' (model yok) yeni beceriyi yürütür."""
    from filo.beceri import Katalog
    from filo.kaptan import Kaptan
    from test_ajanlar import Senaryo
    from filo import rapor
    monkeypatch.setattr(web, "DENETIM", denetim)
    monkeypatch.setattr(rapor, "eposta_gonder", lambda *a, **k: "<id>")
    import filo.kaptan
    monkeypatch.setattr(filo.kaptan, "AKISLAR", tmp_path / "akislar")
    monkeypatch.setattr(web, "ISLER", tmp_path / "isler")
    import filo.isler
    monkeypatch.setattr(filo.isler, "ISLER", tmp_path / "isler")
    ofis = web.Ofis()
    ofis.onaylar = onaylar
    ofis.motor.politika.onaylar = onaylar
    ofis.motor.denetim = denetim
    ofis.katalog = ofis.motor.katalog = Katalog(katalog_dizini, denetim=denetim)
    tas = FakeTasiyici(lambda s, b: (0, "filo-erisim-ok\n", "") if "filo-erisim-ok" in b else (0, f"sunucu={s.ad}\nsurum=1.4.2\n", ""))
    ofis.motor.yurutucu = Yurutucu(envanter, denetim=denetim, tasiyici_fn=lambda s: tas)
    monkeypatch.setattr(ofis, "_taze_motor", lambda: ofis.motor)
    sc = Senaryo(akis={"adimlar": ["betik_calistir", "sonucu_donustur", "eposta_gonder"]}, hedef={"ad": "PA*"},
                 **{"param:betik_calistir": {"betik": "uygulama_surumu"}, "param:sonucu_donustur": {"bicim": "csv"},
                    "param:eposta_gonder": {"alici": "ops@lab.yerel"}})
    monkeypatch.setattr(ofis, "_ajan", lambda ajan, baglanti, kayit: Kaptan(FakeModel(islev=sc), ofis.motor, kayit,
                                                                            onay_bekle_sn=30))
    import http.server
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), web.make_handler(ofis))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    t = f"http://127.0.0.1:{httpd.server_address[1]}"
    try:
        talep = "PA sunucularında uygulama_surumu betiğini çalıştır, CSV yap, ops@lab.yerel adresine gönder"
        s, k = _gonder(t, "/api/talep", {"metin": talep, "ajan": "kaptan", "inisiyatif": 3})
        assert s == 200
        d = _bekle(t, k["kimlik"], ("plan_hazir", "hata"))
        assert d["durum"] == "plan_hazir" and d["inisiyatif"]["duzey"] == 3
        _gonder(t, "/api/is/yurut", {"kimlik": k["kimlik"]})
        d = _bekle(t, k["kimlik"], ("bitti", "kismi", "hata", "devredildi"))
        assert d["durum"] == "bitti", d["rapor"]
        assert {x["karar"] for x in d["inisiyatif"]["kararlar"]} == {"izinli"}
        s, b = _gonder(t, "/api/beceriye-donustur", {"kimlik": k["kimlik"], "ad": "surum_raporu", "baslik": "Sürüm raporu"})
        assert s == 200 and b["beceri"] == "surum_raporu" and b["surum"] == 1
        assert any(x["ad"] == "surum_raporu" for x in _al(t, "/api/beceriler")["beceriler"])
        s, a = _gonder(t, "/api/akis/kaydet", {"kimlik": k["kimlik"]})
        assert s == 200 and a["akis"]
        s, k2 = _gonder(t, "/api/kalfa/dogrudan", {"beceri": "surum_raporu", "parametreler": {"bicim": "xml"}, "hedef": "PB*"})
        assert s == 200
        d2 = _al(t, f"/api/is?kimlik={k2['kimlik']}")
        assert d2["plan"]["ana"]["parametreler"]["bicim"] == "xml" and d2["plan"]["ana"]["hedef"]["sayi"] == 3
        _gonder(t, "/api/is/yurut", {"kimlik": k2["kimlik"]})
        d2 = _bekle(t, k2["kimlik"], ("bitti", "kismi", "hata", "basarisiz"))
        assert d2["durum"] == "bitti" and d2["model_cagri"] == 0
        for sayfa in ("/", "/kalfa", "/kaptan", "/ajanlar", "/karsilastirma"):
            with urllib.request.urlopen(t + sayfa, timeout=10) as r:
                assert b"konsol.js" in r.read()
        assert _al(t, "/api/kaptan/duzeyler")["duzeyler"]["3"]["ad"]
    finally:
        httpd.shutdown()


def test_web_guvenlik(sunucu):
    _, t = sunucu
    assert _gonder(t, "/api/durdur", {}, baslik=False)[0] == 403
    s, v = _gonder(t, "/api/baglanti/kaydet", {"ad": "x", "tur": "yok"})
    assert s == 400


@pytest.mark.lab
def test_web_uctan_uca_gercek_lab(sunucu):
    from filo import lab
    _, t = sunucu
    lab.dexec("filo-pb-web-01", "apt-get remove -y jq >/dev/null 2>&1; true")
    son = _uctan_uca(t)
    assert son["durum"] == "bitti", son["rapor"]
    rc, out, err = lab.dexec("filo-pb-web-01", "dpkg-query -W -f='${Status}' jq")
    assert "install ok installed" in out
