"""Gerçek laboratuvarla uçtan uca sınamalar (python -m filo lab kur). Laboratuvar yoksa atlanır."""
import pytest

from filo import lab
from filo.beceri import Katalog
from filo.denetim import Denetim
from filo.envanter import Envanter
from filo.motor import BeceriMotoru
from filo.politika import Politika
from filo.yurutme import Yurutucu

pytestmark = pytest.mark.lab


@pytest.fixture
def gercek(tmp_path):
    env = Envanter()
    d = Denetim(tmp_path / "denetim.jsonl")
    y = Yurutucu(env, denetim=d)
    return env, y, BeceriMotoru(Katalog(denetim=d), env, y, Politika("bench", {"varsayilan": "onayla"}, denetim=d), denetim=d)


def test_hostname_pa(gercek):
    env, y, _ = gercek
    sonuc = y.is_yurut(env.dondur("PA*")["sunucular"], "hostname; uname -r", 30)
    assert [r["durum"] for r in sonuc] == ["basarili"] * 4
    assert all(r["stdout"].startswith(r["sunucu"]) for r in sonuc)


def test_kapali_konteyner_erisilemedi(gercek):
    env, y, _ = gercek
    assert lab.konteyner_durdur("filo-pc-batch-01")
    try:
        r = y.is_yurut(["PC-BATCH-01", "PB-APP-01"], "hostname", 20, yeniden_deneme=1)
        assert r[0]["durum"] == "erisilemedi" and r[1]["durum"] == "basarili"
    finally:
        lab.konteyner_baslat("filo-pc-batch-01")
        lab.ssh_bekle(sure=60)


def test_betik_xml_posta_mailpit(gercek):
    _, _, m = gercek
    konu = "filo-test-uctan-uca"
    baglam = {"adimlar": []}
    for ad, p, h in (("betik_calistir", {"betik": "uygulama_surumu"}, "PA*"), ("sonucu_donustur", {"bicim": "xml"}, None),
                     ("eposta_gonder", {"alici": "ops@lab.yerel", "konu": konu}, None)):
        a = m.yurut(m.plan(ad, p, h), baglam)
        baglam["adimlar"].append(a)
        assert a["durum"] == "basarili", a
    postalar = [x for x in lab.posta_listesi(20) if x["konu"] == konu]
    assert postalar and postalar[0]["ekler"][0]["ad"].endswith(".xml")
    ek = lab.posta_eki(postalar[0]["id"], postalar[0]["ekler"][0]["parca"])
    assert ek.count("<sunucu ") == 4 and "1.4.2" in ek


def test_calistirma_kimligi_gercek_sudo(gercek):
    """C1: root ve 'uygulama' kimliği sudo ile; PC-BATCH-01'de filo yalnız root'a geçebilir → 'yetki yok'."""
    _, _, m = gercek
    a = m.yurut(m.plan("komut_calistir", {"komut": "id -un"}, "PA-APP-01,PA-APP-02,PA-DB-01,PC-BATCH-01",
                       kimlik="uygulama"))
    r = {x["sunucu"]: x for x in a["sonuclar"]}
    assert all(r[s]["stdout"].strip() == "uygulama" for s in ("PA-APP-01", "PA-APP-02", "PA-DB-01"))
    assert r["PC-BATCH-01"]["yetki_yok"] and "password is required" in r["PC-BATCH-01"]["neden"]
    b = m.yurut(m.plan("komut_calistir", {"komut": "id -un"}, "PC-BATCH-01", kimlik="root"))
    assert b["sonuclar"][0]["stdout"].strip() == "root"


def test_aile_farki_paket_dogrula(gercek):
    _, _, m = gercek
    a = m.yurut(m.plan("paket_dogrula", {"paketler": ["sudo"]}, "PA-APP-01,PA-APP-02,PA-DB-01"))
    assert a["durum"] == "basarili"
    assert all(r["veri"][0]["surum"] != "yok" for r in a["sonuclar"])
