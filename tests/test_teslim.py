"""B3: yeni sunucu teslimi (politika, ön onay, insan onayı, Kaptan devralması). Sahte taşıyıcı ve FakeModel."""
import json

import pytest

from filo import teslim as teslim_mod
from filo.envanter import Envanter
from filo.gateway import FakeModel
from filo.teslim import Teslim, politika_denetle, politikalar, profil_bul

from test_ajanlar import Senaryo


class YeniWeb:
    """Yeni bir web sunucusu: paketler yok, webops yok, webd duruyor. depo_bozuk ise paket kurulamaz."""

    def __init__(self, depo_bozuk=False):
        self.depo_bozuk, self.paket, self.kullanici, self.webd, self.depo_onarildi = depo_bozuk, set(), set(), False, False

    def __call__(self, s, b):
        if "filo-erisim-ok" in b:
            return 0, "filo-erisim-ok\n", ""
        if "deb.debian.org" in b and "apt-get update" in b:
            self.depo_bozuk, self.depo_onarildi = False, True
            return 0, "depo=standart\nguncelleme=tamam\n", ""
        if "apt-get install -y" in b:
            if self.depo_bozuk:
                return 100, "jq|yok\ntree|yok\n", "E: Unable to locate package jq"
            self.paket |= {"jq", "tree"}
            return 0, "jq|1.6\ntree|2.1\n", ""
        if "dpkg-query -W" in b:
            return 0, "".join(f"{p}|{'1.0' if p in self.paket else 'yok'}\n" for p in ("jq", "tree")), ""
        if "useradd" in b:
            self.kullanici.add("webops")
            return 0, "kullanici=webops\ndurum=acildi\nuid=1001\n", ""
        if "base64 -d" in b:
            import hashlib
            from conftest import KOK
            o = hashlib.sha256((KOK / "skills" / "_dosyalar" / "motd.txt").read_bytes()).hexdigest()
            return 0, f"hedef=/etc/motd\nozet={o}\n", ""
        if "systemctl start" in b:
            self.webd = True
            return 0, "servis=webd\ndurum=active\n", ""
        if "is-active" in b:
            return 0, f"servis=webd\ndurum={'active' if self.webd else 'inactive'}\n", ""
        if "sudo -n true" in b:
            return 0, f"sunucu={s.ad}\nkullanici=filo\ncalisma_suresi=5\nsudo=var\n", ""
        if "os-release" in b:
            return 0, "sunucu=PA-WEB-01\nisletim=Debian\ncekirdek=6\nislemci=1\nbellek_mb=128\nkok_doluluk=10\ncalisma_suresi=5\n", ""
        return 0, "", ""


@pytest.fixture
def posta(monkeypatch):
    gonderilen = []
    from filo import rapor
    monkeypatch.setattr(rapor, "eposta_gonder", lambda alici, konu, govde, ekler=(), ayar=None:
                        gonderilen.append({"alici": alici, "konu": konu, "ekler": list(ekler)}) or "<id>")
    return gonderilen


def _paket_dogrula_cevabi(lab):
    return lab


def test_politika_gecerli_ve_kurallar(katalog_dizini):
    from filo.beceri import Katalog
    pol = politikalar()
    assert politika_denetle(pol, Katalog(katalog_dizini)) == []
    env = Envanter()
    assert profil_bul(env["PA-WEB-01"], pol)[0] == "web"
    assert profil_bul(env["PB-APP-01"], pol)[0] == "uygulama"
    assert profil_bul(env["PC-BATCH-01"], pol)[0] is None


def test_teslim_on_onayli_adimlar_onaysiz_digerleri_insana(motor_kur, tmp_path, posta, denetim):
    lab = YeniWeb()
    # insan (bench politikası) her onayı REDDEDER: yalnız ön onaylı adımlar onaysız geçer
    m, t = motor_kur(lab, kural={"varsayilan": "reddet"})
    from filo.isler import IsKaydi
    k = Teslim(m, "PA-WEB-01", "web", kayit=IsKaydi("t", "teslim", dizin=tmp_path / "isler")).yurut()
    assert lab.paket == {"jq", "tree"}                      # paket_kur ön onaylı: çalıştı
    assert not lab.kullanici and not lab.webd               # kullanici_ac ön onaylı değil: reddedildi, zincir durdu
    assert k.durum == "devredildi" and "kullanici_ac" in k.rapor
    on = [r for r in denetim.oku(500) if r["tur"] == "onay_verildi" and r.get("on_onay")]
    assert [r["beceri"] for r in on] == ["paket_kur"] and on[0]["onaylayan"] == "teslim_politikasi:web"
    assert posta and "PA-WEB-01" in posta[0]["konu"] and posta[0]["ekler"][0][0].endswith(".html")


def test_teslim_insan_onayiyla_tamamlanir(motor_kur, tmp_path, posta):
    lab = YeniWeb()
    m, t = motor_kur(lab, kural={"varsayilan": "onayla"})
    from filo.isler import IsKaydi
    k = Teslim(m, "PA-WEB-01", "web", kayit=IsKaydi("t", "teslim", dizin=tmp_path / "isler")).yurut()
    assert k.durum == "bitti", k.rapor
    assert lab.paket == {"jq", "tree"} and lab.kullanici == {"webops"} and lab.webd
    assert "(bitti)" in posta[0]["konu"]


def test_teslim_yarida_kalirsa_kaptan_devralir(motor_kur, tmp_path, posta, monkeypatch):
    import filo.kaptan
    monkeypatch.setattr(filo.kaptan, "AKISLAR", tmp_path / "akislar")
    lab = YeniWeb(depo_bozuk=True)
    m, t = motor_kur(lab, kural={"varsayilan": "onayla"})
    sc = Senaryo(akis={"adimlar": ["paket_kur", "kullanici_ac", "dosya_dagit", "servis_baslat"], "gerekce": "kalanlar"},
                 hedef={"ad": "PA-WEB-01"}, teshis={"beceri": "yok"},
                 karar={"karar": "onarim:depo_onar", "gerekce": "paket bulunamıyor: depo bozuk"},
                 **{"param:paket_kur": {"paketler": ["jq", "tree"]}, "param:kullanici_ac": {"kullanici": "webops"},
                    "param:dosya_dagit": {"dosya": "motd.txt", "hedef": "/etc/motd"},
                    "param:servis_baslat": {"servis": "webd"}, "param:depo_onar": {}})
    from filo.isler import IsKaydi
    t_ = Teslim(m, "PA-WEB-01", "web", kayit=IsKaydi("t", "teslim", dizin=tmp_path / "isler"),
                model_fabrikasi=lambda: FakeModel(islev=sc))
    k = t_.yurut()
    devralan = json.loads((tmp_path / "isler" / f"{k.ek['devralan_is']}.json").read_text(encoding="utf-8"))
    assert devralan["ajan"] == "kaptan" and devralan["inisiyatif"]["duzey"] == 3
    assert "PA-WEB-01" in devralan["talep"] and "paket_kur" in devralan["talep"]
    assert lab.depo_onarildi and lab.paket == {"jq", "tree"} and lab.kullanici == {"webops"} and lab.webd
    assert any(x["beceri"] == "depo_onar" and x["karar"] == "izinli" for x in devralan["inisiyatif"]["kararlar"])
    assert k.durum == "bitti", k.rapor
    assert "Kaptan devraldı" in k.rapor


def test_isaretsiz_sunucu_teslim_edilmez(monkeypatch):
    """Çalışan bir sunucuya ajan kurmak teslim başlatmaz (teslim=bekliyor işareti yok)."""
    cagrildi = []
    monkeypatch.setattr(teslim_mod, "Teslim", lambda *a, **k: cagrildi.append(a))
    teslim_mod.kapi_dinleyicisi()({"sunucu": "PA-WEB-01", "kimlik": "ajan-x"})
    assert not cagrildi
