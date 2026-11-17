"""A3: Kalfa ve Kaptan, FakeModel ve sahte taşıyıcıyla (laboratuvar ve gerçek model gerekmez)."""
import json

import pytest

from filo import rapor
from filo.gateway import FakeModel, json_ayikla, sor_json
from filo.isler import IsKaydi
from filo.kalfa import Kalfa
from filo.kaptan import Kaptan, akis_listesi, akis_yurut


def soru(mesajlar):
    return mesajlar[-1]["content"] if mesajlar[-1]["role"] == "user" else ""


def ilk_soru(mesajlar):
    return next(m["content"] for m in mesajlar if m["role"] == "user")


class Senaryo:
    """Soru türüne göre cevap veren FakeModel işlevi. cevaplar: {anahtar: [cevap, ...]} sırayla tüketilir."""
    ANAHTAR = [("ANA işini", "beceri"), ("seçiciyle yaz", "hedef"), ("akışı kur", "akis"), ("Teşhis için", "teshis"),
               ("Ne yapılmalı?", "karar"), ("düzeltilmiş tam hâlini", "degisiklik"), ("2-3 cümlelik", "yorum"),
               ("hangi biçimde", "bicim"), ("Seçilen beceri:", "param"), ("DIŞINDA", "kapsam")]

    def __init__(self, **cevaplar):
        self.cevaplar = {k: list(v) if isinstance(v, list) else [v] for k, v in cevaplar.items()}
        self.sorulan = []

    def __call__(self, mesajlar):
        ilk = ilk_soru(mesajlar)
        tur = next((t for a, t in self.ANAHTAR if a in ilk), "bilinmiyor")
        if tur == "param":
            tur = "param:" + ilk.split("Seçilen beceri:", 1)[1].split("—")[0].strip()
        self.sorulan.append(tur)
        liste = self.cevaplar.get(tur) or self.cevaplar.get(tur.split(":")[0])
        if not liste:
            return {"yorum": "yok"} if tur == "yorum" else {"eksik": "yok"} if tur == "kapsam" else {}
        return liste.pop(0) if len(liste) > 1 else liste[0]


@pytest.fixture
def posta(monkeypatch):
    gonderilen = []
    monkeypatch.setattr(rapor, "eposta_gonder", lambda alici, konu, govde, ekler=(), ayar=None:
                        gonderilen.append({"alici": alici, "konu": konu, "govde": govde, "ekler": list(ekler)}) or "<id>")
    return gonderilen


def erisimli(d):
    def f(s, b):
        if "filo-erisim-ok" in b:
            return 0, "filo-erisim-ok\n", ""
        return d(s, b)
    return f


def kayit(tmp_path, talep, ajan):
    return IsKaydi(talep, ajan, "fake", dizin=tmp_path / "isler")


# ---------------------------------------------------------------- kapı
def test_json_ayikla_ve_onarim():
    assert json_ayikla('<think>x</think> tamam: {"a": 1} bitti') == {"a": 1}
    m = FakeModel(["bozuk", {"secim": "x"}, {"secim": "b"}])
    iz = []
    deger, k = sor_json(m, "s", "u", lambda v: (v["secim"], None) if v.get("secim") == "b" else (None, "b yaz"), iz=iz)
    assert deger == "b" and len(k["denemeler"]) == 3 and m.cagri == 3
    m = FakeModel([{"secim": "x"}] * 3)
    assert sor_json(m, "s", "u", lambda v: (None, "hayır"), onarim=2)[0] is None and m.cagri == 3


def test_baglanti_anahtari_geri_donmez(tmp_path):
    from filo.gateway import Baglantilar
    b = Baglantilar(tmp_path / "b.json", tmp_path / "gizli.json")
    oz = b.kaydet({"ad": "api", "tur": "anthropic", "model": "m"}, anahtar="sk-gizli-123")
    assert oz["anahtar_var"] and "sk-gizli-123" not in json.dumps(oz)
    assert "sk-gizli-123" not in (tmp_path / "b.json").read_text(encoding="utf-8")
    assert b.anahtar(b.getir("api")) == "sk-gizli-123"
    with pytest.raises(Exception):
        b.kaydet({"ad": "x", "tur": "anthropic", "anahtar_ortam": "sk-ant-SAHTE-test-degeri"})


# ---------------------------------------------------------------- Kalfa
TALEP = "Adı PA ile başlayan sunucularda uygulama_surumu betiğini çalıştır, sonucu XML yap, ops@lab.yerel adresine gönder"


def test_kalfa_uctan_uca(motor_kur, posta, tmp_path):
    m, t = motor_kur(erisimli(lambda s, b: (0, f"sunucu={s.ad}\nsurum=1.4.2\n", "")))
    sc = Senaryo(beceri=[{"secim": "disk"}, {"secim": "betik_calistir", "gerekce": "betik isteniyor"}],
                 hedef={"ad": "PA*"}, param={"betik": "uygulama_surumu"})
    model = FakeModel(islev=sc)
    k = Kalfa(model, m, kayit(tmp_path, TALEP, "kalfa")).calistir(TALEP)
    assert k.durum == "bitti", k.rapor
    assert k.plan["ana"]["beceri"] == "betik_calistir" and k.plan["ana"]["hedef"]["sunucular"][0] == "PA-APP-01"
    assert [a["beceri"] for a in k.adimlar] == ["betik_calistir", "sonucu_donustur", "eposta_gonder"]
    assert posta[0]["alici"] == "ops@lab.yerel" and posta[0]["ekler"][0][0].endswith(".xml")
    assert len(k.gerekce[0]["denemeler"]) == 2       # ilk seçim reddedildi, onarıldı
    assert "bicim" not in sc.sorulan                  # tek biçim adı geçti: kod seçti, model çağrılmadı
    assert (tmp_path / "isler" / f"{k.kimlik}.json").exists()


def test_kalfa_uygun_beceri_yok(motor_kur, tmp_path):
    m, t = motor_kur()
    k = Kalfa(FakeModel(islev=Senaryo(beceri={"secim": "hicbiri"})), m,
              kayit(tmp_path, "veritabanı yedeğini geri yükle", "kalfa")).calistir("veritabanı yedeğini geri yükle")
    assert k.durum == "beceri_yok" and "beceri yok" in k.rapor and not t.cagrilar


def test_kalfa_uydurma_parametreyi_reddeder(motor_kur, tmp_path):
    m, _ = motor_kur(erisimli(lambda s, b: (0, "servis=uygulama\ndurum=active\n", "")))
    talep = "PB-WEB-01 üzerinde uygulama servisinin durumuna bak"
    sc = Senaryo(beceri={"secim": "servis_durumu"}, hedef={"ad": "PB-WEB-01"},
                 param=[{"servis": "nginx"}, {"servis": "uygulama"}])
    k = Kalfa(FakeModel(islev=sc), m, kayit(tmp_path, talep, "kalfa")).calistir(talep)
    assert k.durum == "bitti"
    p = next(g for g in k.gerekce if g["soru"].startswith("parametre"))
    assert "talepte geçmiyor" in p["denemeler"][0]["hata"] and p["sonuc"] == {"servis": "uygulama"}


def test_kalfa_onaysiz_degisiklik_yapmaz(motor_kur, tmp_path, onaylar):
    m, t = motor_kur(erisimli(lambda s, b: (0, "jq|1.6\n", "")), kip="etkilesimli")
    talep = "PA-APP-01 sunucusuna jq paketini kur"
    sc = Senaryo(beceri={"secim": "paket_kur"}, hedef={"ad": "PA-APP-01"}, param={"paketler": ["jq"]})
    k = Kalfa(FakeModel(islev=sc), m, kayit(tmp_path, talep, "kalfa")).calistir(talep)
    assert k.durum == "onay_bekliyor" and onaylar.liste("bekliyor")
    assert not any("apt-get install -y" in b for _, b in t.cagrilar)


def test_kalfa_kismi_basarisizligi_soyler(motor_kur, tmp_path):
    def d(s, b):
        if s.ad == "PA-DB-01":
            return 1, "", "df: hata"
        return 0, "/|100|50|50|normal\n", ""
    m, _ = motor_kur(erisimli(d))
    talep = "PA sunucularının disk doluluğunu göster"
    sc = Senaryo(beceri={"secim": "disk_durumu"}, hedef={"ad": "PA*"}, param={}, yorum={"yorum": "PA-DB-01'de df hata verdi."})
    k = Kalfa(FakeModel(islev=sc), m, kayit(tmp_path, talep, "kalfa")).calistir(talep)
    assert k.durum == "kismi" and "3/4" in k.rapor and "PA-DB-01" in k.rapor and k.yorum


# ---------------------------------------------------------------- Kaptan
class SahteLab:
    """Durumlu sahte sunucular: dpkg kesik, surum dosyası biçimi değişmiş vb."""

    def __init__(self):
        self.dpkg_kesik = {"PA-APP-01"}
        self.kurulu = set()
        self.yeni_bicim = {"PA-APP-02"}

    def __call__(self, s, b):
        if "filo-erisim-ok" in b:
            return 0, "filo-erisim-ok\n", ""
        if "dpkg --configure -a" in b:
            self.dpkg_kesik.discard(s.ad)
            return 0, "onarildi=evet\n", ""
        if "apt-get install -y" in b or "dnf install -y" in b or "apk add -q" in b:
            if s.ad in self.dpkg_kesik:
                return 100, "jq|yok\n", "E: dpkg was interrupted, you must manually run 'dpkg --configure -a'"
            self.kurulu.add(s.ad)
            return 0, "jq|1.6\n", ""
        if "GERILEME" in b:          # yeni biçimde çalışan ama eski biçimi bozan betik
            return 0, (f"sunucu={s.ad}\nsurum=1.4.2\n" if s.ad in self.yeni_bicim else f"sunucu={s.ad}\n"), ""
        if "HALA_BOZUK" in b:
            return 0, f"sunucu={s.ad}\n1.4.2\n", ""
        if "cat /opt/uygulama/surum.txt" in b or "Surumu" in b:
            if s.ad in self.yeni_bicim and "sed" not in b:
                return 0, f"sunucu={s.ad}\nUygulama Surumu: 1.4.2 (derleme 77)\n", ""
            return 0, f"sunucu={s.ad}\nsurum=1.4.2\n", ""
        if "sh -c" in b:
            return 0, "Uygulama Surumu: 1.4.2 (derleme 77)\n", ""
        return 0, "", ""


def test_kaptan_onarim_ile_devam(motor_kur, tmp_path):
    lab = SahteLab()
    m, t = motor_kur(lab)
    talep = "PA-APP-01 ve PA-APP-02 sunucularına jq paketini kur"
    sc = Senaryo(akis={"adimlar": ["paket_kur"]}, hedef={"ad": "PA-APP-01,PA-APP-02"}, param={"paketler": ["jq"]},
                 teshis={"beceri": "yok"}, karar={"karar": "onarim:paket_onar", "gerekce": "dpkg kesilmiş"},
                 **{"param:paket_onar": {}})
    r = Kaptan(FakeModel(islev=sc), m, kayit(tmp_path, talep, "kaptan"), akis_dizini=tmp_path / "akislar")
    k = r.calistir(talep)
    assert k.durum == "bitti", k.rapor
    assert lab.kurulu == {"PA-APP-01", "PA-APP-02"}
    assert any(a["beceri"] == "paket_onar" for a in k.adimlar)
    kayitli = akis_listesi(tmp_path / "akislar")
    assert [a["beceri"] for a in kayitli[0]["adimlar"]] == ["paket_onar", "paket_kur"] or \
        [a["beceri"] for a in kayitli[0]["adimlar"]] == ["paket_kur", "paket_onar"] or kayitli


def test_kaptan_sema_uyumsuzlugunda_beceriyi_degistirir(motor_kur, tmp_path, posta):
    lab = SahteLab()
    m, t = motor_kur(lab)
    talep = "PA-APP-01 ve PA-APP-02'de uygulama_surumu betiğini çalıştır, CSV yap, ops@lab.yerel adresine gönder"
    yeni = ('#!/bin/sh\necho "sunucu=$(hostname)"\n'
            "sed -n 's/^surum=//p; s/.*Surumu: \\([0-9.]*\\).*/\\1/p' /opt/uygulama/surum.txt | head -1 | sed 's/^/surum=/'\n")
    sc = Senaryo(akis={"adimlar": ["betik_calistir", "sonucu_donustur", "eposta_gonder"]},
                 hedef={"ad": "PA-APP-01,PA-APP-02"},
                 **{"param:betik_calistir": {"betik": "uygulama_surumu"}, "param:sonucu_donustur": {"bicim": "csv"},
                    "param:eposta_gonder": {"alici": "ops@lab.yerel"}},
                 teshis=[{"beceri": "komut_calistir", "parametreler": {"komut": "cat /opt/uygulama/surum.txt"}},
                         {"beceri": "yok"}],
                 karar={"karar": "beceriyi_degistir"}, degisiklik={"yeni_icerik": yeni, "gerekce": "biçim değişmiş"})
    k = Kaptan(FakeModel(islev=sc), m, kayit(tmp_path, talep, "kaptan"), akis_dizini=tmp_path / "akislar", inisiyatif=3).calistir(talep)
    assert k.durum == "bitti", k.rapor
    d = k.degisiklikler[0]
    assert d["kayit"] == "betik" and d["yeni_surum"] == 2 and d["risk_yeni"] == 0 and "sed -n" in d["fark"]
    assert m.katalog.betik_meta("uygulama_surumu")["surum"] == 2
    assert posta and "2/2" in posta[0]["govde"]


def test_kaptan_deneme_siniri_ve_devir(motor_kur, tmp_path):
    m, t = motor_kur(erisimli(lambda s, b: (1, "", "E: Unable to locate package jq")))
    talep = "PA-APP-01'e jq kur"
    sc = Senaryo(akis={"adimlar": ["paket_kur"]}, hedef={"ad": "PA-APP-01"}, param={"paketler": ["jq"]},
                 teshis={"beceri": "yok"}, karar={"karar": "yeniden_dene"},
                 yorum={"yorum": "Depo erişimi bozuk görünüyor."})
    k = Kaptan(FakeModel(islev=sc), m, kayit(tmp_path, talep, "kaptan"), akis_dizini=tmp_path / "akislar", inisiyatif=3).calistir(talep)
    assert k.durum == "devredildi" and "İnsana devredilen" in k.rapor and "PA-APP-01" in k.rapor
    assert sc.sorulan.count("karar") == 2                       # en çok 2 onarım denemesi
    assert not akis_listesi(tmp_path / "akislar")                # başarısız akış kaydedilmez


def test_kaptan_riski_yukselten_degisiklik_onaysiz_calismaz(motor_kur, tmp_path):
    lab = SahteLab()
    m, t = motor_kur(lab, kural={"varsayilan": "onayla", "beceriler": {"betik_calistir": "reddet"}})
    talep = "PA-APP-02'de uygulama_surumu betiğini çalıştır"
    sc = Senaryo(akis={"adimlar": ["betik_calistir"]}, hedef={"ad": "PA-APP-02"},
                 **{"param:betik_calistir": {"betik": "uygulama_surumu"}}, teshis={"beceri": "yok"},
                 karar={"karar": "beceriyi_degistir"},
                 degisiklik={"yeni_icerik": "#!/bin/sh\nrm -rf /opt/uygulama\necho surum=yok\necho sunucu=x\n"})
    k = Kaptan(FakeModel(islev=sc), m, kayit(tmp_path, talep, "kaptan"), akis_dizini=tmp_path / "akislar", inisiyatif=3).calistir(talep)
    assert k.degisiklikler[0]["risk_yeni"] == 4 and k.degisiklikler[0]["risk_yukseldi"]
    assert k.durum == "reddedildi"
    assert not any("rm -rf" in b for _, b in t.cagrilar)


def test_sabit_akis_kayitli_sirayla_yurur(motor_kur, tmp_path):
    lab = SahteLab()
    lab.dpkg_kesik.clear()
    m, t = motor_kur(lab)
    talep = "PA-APP-01'e jq kur"
    sc = Senaryo(akis={"adimlar": ["paket_kur"]}, hedef={"ad": "PA-APP-01"}, param={"paketler": ["jq"]})
    Kaptan(FakeModel(islev=sc), m, kayit(tmp_path, talep, "kaptan"), akis_dizini=tmp_path / "akislar", inisiyatif=3).calistir(talep)
    ad = akis_listesi(tmp_path / "akislar")[0]["ad"]
    lab.kurulu.clear()
    k = akis_yurut(m, ad, "PA-APP-02", kayit(tmp_path, talep, "sabit"), dizin=tmp_path / "akislar")
    assert k.durum == "bitti" and lab.kurulu == {"PA-APP-02"}


def _surum_senaryosu(yeni_icerikler):
    return Senaryo(akis={"adimlar": ["betik_calistir"]}, hedef={"ad": "PA-APP-01,PA-APP-02"},
                   **{"param:betik_calistir": {"betik": "uygulama_surumu"}}, teshis={"beceri": "yok"},
                   karar={"karar": "beceriyi_degistir"},
                   degisiklik=[{"yeni_icerik": y, "gerekce": "deneme"} for y in yeni_icerikler])


def test_kaptan_duzeltmeyen_degisikligi_geri_alir(motor_kur, tmp_path):
    m, t = motor_kur(SahteLab())
    talep = "PA-APP-01 ve PA-APP-02'de uygulama_surumu betiğini çalıştır"
    eski = m.katalog.betik_oku("uygulama_surumu")
    sc = _surum_senaryosu(["#!/bin/sh\n# HALA_BOZUK 1\necho x\n", "#!/bin/sh\n# HALA_BOZUK 2\necho y\n"])
    k = Kaptan(FakeModel(islev=sc), m, kayit(tmp_path, talep, "kaptan"), akis_dizini=tmp_path / "akislar", inisiyatif=3).calistir(talep)
    assert k.durum == "kismi" and len(k.degisiklikler) == 2
    assert all(d.get("geri_alindi") for d in k.degisiklikler)
    assert m.katalog.betik_oku("uygulama_surumu") == eski          # katalog bozuk sürümle kalmadı
    assert [g["surum"] for g in m.katalog.gecmis("betik", "uygulama_surumu")] == [1, 2, 3, 4, 5]


def test_kaptan_gerileme_sinamasi(motor_kur, tmp_path):
    m, t = motor_kur(SahteLab())
    talep = "PA-APP-01 ve PA-APP-02'de uygulama_surumu betiğini çalıştır"
    eski = m.katalog.betik_oku("uygulama_surumu")
    sc = _surum_senaryosu(["#!/bin/sh\n# GERILEME\necho z\n"])
    k = Kaptan(FakeModel(islev=sc), m, kayit(tmp_path, talep, "kaptan"), akis_dizini=tmp_path / "akislar", inisiyatif=3).calistir(talep)
    d = k.degisiklikler[0]
    assert "gerileme" in d["geri_alindi"]["neden"] and m.katalog.betik_oku("uygulama_surumu") == eski
    assert k.durum == "kismi" and "PA-APP-02" in k.rapor
