"""B4: Kaptan'ın inisiyatif düzeyi. Aynı arıza (yanlış yapılandırma + duran servis), aynı model cevapları; yalnız düzey
değişir. İnsan (bench politikası) her onay isteğini reddeder: onay gerekirse iş orada durur."""
import hashlib

import pytest

from filo.gateway import FakeModel
from filo.kaptan import DUZEYLER, Kaptan, inisiyatif_karari

from conftest import KOK
from test_ajanlar import Senaryo, kayit

TALEP = "PA-APP-01'de uygulama servisi yanlış yapılandırmayla duruyor: durumuna bak, uygulama.conf dosyasını /etc/uygulama/uygulama.conf olarak yeniden dağıt ve uygulama servisini yeniden başlat"
OZET = hashlib.sha256((KOK / "skills" / "_dosyalar" / "uygulama.conf").read_bytes()).hexdigest()


class Ariza:
    def __init__(self):
        self.dagitildi = self.baslatildi = False

    def __call__(self, s, b):
        if "filo-erisim-ok" in b:
            return 0, "filo-erisim-ok\n", ""
        if "base64 -d" in b:
            self.dagitildi = True
            return 0, f"hedef=/etc/uygulama/uygulama.conf\nozet={OZET}\n", ""
        if "systemctl restart" in b:
            self.baslatildi = True
            return 0, "servis=uygulama\ndurum=active\n", ""
        if "durum=degisecek" in b or "yapilacak=" in b:          # kuru çalıştırma
            return 0, "durum=degisecek\n", ""
        if "is-active" in b:
            return 0, f"servis=uygulama\ndurum={'active' if self.baslatildi else 'inactive'}\n", ""
        return 0, "", ""


def senaryo():
    return Senaryo(akis={"adimlar": ["servis_durumu", "dosya_dagit", "servis_yeniden_baslat"], "gerekce": "önce bak, sonra düzelt"},
                   hedef={"ad": "PA-APP-01"},
                   **{"param:servis_durumu": {"servis": "uygulama"},
                      "param:dosya_dagit": {"dosya": "uygulama.conf", "hedef": "/etc/uygulama/uygulama.conf"},
                      "param:servis_yeniden_baslat": {"servis": "uygulama"}})


def kos(motor_kur, tmp_path, duzey):
    ariza = Ariza()
    m, t = motor_kur(ariza, kural={"varsayilan": "reddet"})
    k = Kaptan(FakeModel(islev=senaryo()), m, kayit(tmp_path, TALEP, "kaptan"), akis_dizini=tmp_path / "akislar",
               inisiyatif=duzey).calistir(TALEP)
    kararlar = {(x["beceri"], x["amac"]): x for x in k.inisiyatif["kararlar"]}
    return k, ariza, t, kararlar


def test_duzey_0_hicbir_sey_calistirmaz(motor_kur, tmp_path):
    k, ariza, t, kararlar = kos(motor_kur, tmp_path, 0)
    assert k.durum == "oneri" and not t.cagrilar          # hiçbir sunucuya tek komut gitmedi
    assert {x["karar"] for x in k.inisiyatif["kararlar"]} == {"onerildi"}
    assert "dosya_dagit" in k.rapor and "risk 3" in k.rapor and "hiçbir sunucuda" in k.rapor


def test_duzey_1_teshis_calisir_degisiklik_onay_ister(motor_kur, tmp_path):
    k, ariza, t, kararlar = kos(motor_kur, tmp_path, 1)
    assert kararlar[("servis_durumu", "adım")]["karar"] == "izinli"
    assert kararlar[("dosya_dagit", "adım")]["karar"] == "onay_gerekli"
    assert kararlar[("dosya_dagit", "adım")]["sonuc"] == "reddedildi"
    assert not ariza.dagitildi and not ariza.baslatildi and k.durum == "reddedildi"


def test_duzey_2_geri_alinabilir_onarim_serbest_servis_onay_ister(motor_kur, tmp_path):
    k, ariza, t, kararlar = kos(motor_kur, tmp_path, 2)
    assert kararlar[("dosya_dagit", "adım")]["karar"] == "izinli" and ariza.dagitildi
    assert kararlar[("servis_yeniden_baslat", "adım")]["karar"] == "onay_gerekli"
    assert not ariza.baslatildi and k.durum == "reddedildi"


def test_duzey_3_servis_degisikligi_serbest(motor_kur, tmp_path):
    k, ariza, t, kararlar = kos(motor_kur, tmp_path, 3)
    assert all(x["karar"] == "izinli" for x in k.inisiyatif["kararlar"])
    assert ariza.dagitildi and ariza.baslatildi and k.durum == "bitti", k.rapor


def test_yikici_is_duzey_3te_bile_onay_ister(motor_kur, tmp_path):
    m, t = motor_kur(lambda s, b: (0, "filo-erisim-ok\n", "") if "filo-erisim-ok" in b else (0, "silinen=3\n", ""),
                     kural={"varsayilan": "reddet"})
    talep = "PA-APP-01'de /veri altındaki geçici dosyaları temizle"
    sc = Senaryo(akis={"adimlar": ["gecici_dosya_temizle"]}, hedef={"ad": "PA-APP-01"},
                 **{"param:gecici_dosya_temizle": {"dizin": "/veri"}})
    k = Kaptan(FakeModel(islev=sc), m, kayit(tmp_path, talep, "kaptan"), akis_dizini=tmp_path / "akislar",
               inisiyatif=3).calistir(talep)
    x = k.inisiyatif["kararlar"][0]
    assert x["risk"] == 4 and x["karar"] == "onay_gerekli" and x["sonuc"] == "reddedildi"
    assert k.durum == "reddedildi"


def test_beceri_degistirme_duzey_3_ister(motor_kur, tmp_path):
    """Düzey 2'de model 'beceriyi_degistir' dese de kod kabul etmez; katalog değişmez."""
    from test_ajanlar import SahteLab
    m, t = motor_kur(SahteLab())
    talep = "PA-APP-02'de uygulama_surumu betiğini çalıştır"
    sc = Senaryo(akis={"adimlar": ["betik_calistir"]}, hedef={"ad": "PA-APP-02"},
                 **{"param:betik_calistir": {"betik": "uygulama_surumu"}}, teshis={"beceri": "yok"},
                 karar={"karar": "beceriyi_degistir"}, degisiklik={"yeni_icerik": "#!/bin/sh\necho surum=1\n"})
    k = Kaptan(FakeModel(islev=sc), m, kayit(tmp_path, talep, "kaptan"), akis_dizini=tmp_path / "akislar",
               inisiyatif=2).calistir(talep)
    assert not k.degisiklikler and m.katalog.betik_meta("uygulama_surumu")["surum"] == 1
    assert "degisiklik" not in sc.sorulan                    # değişiklik metni hiç istenmedi
    assert any(x["karar"] == "kapali" for x in k.inisiyatif["kararlar"])
    assert k.durum == "devredildi"


def test_duzey_tablosu_ve_karar_islevi():
    assert sorted(DUZEYLER) == [0, 1, 2, 3]
    with pytest.raises(ValueError):
        Kaptan(None, None, inisiyatif=4)
    assert inisiyatif_karari(3, 4)[0] == "onay_gerekli" and inisiyatif_karari(2, 2)[0] == "izinli"
    assert inisiyatif_karari(1, 2)[0] == "onay_gerekli" and inisiyatif_karari(0, 0)[0] == "onerildi"
