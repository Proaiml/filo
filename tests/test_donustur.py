"""B5: beceriye dönüştürme. (a) Kaptan akışı / tek seferlik betik işi → katalogda yeni beceri; benzer talebi Kalfa 2-3
model çağrısında yürütür. (b) Düz dil tarifinden taslak: kod denetimi + kuru çalıştırma geçmeden kataloğa girmez."""
import pytest

from filo import donustur
from filo.ajan_ortak import aday_beceriler
from filo.gateway import FakeModel
from filo.kalfa import Kalfa
from filo.kaptan import Kaptan

from test_ajanlar import Senaryo, kayit

TALEP = "PA-APP-01 ve PA-APP-02'de uygulama_surumu betiğini çalıştır, sonucu CSV yap, ops@lab.yerel adresine gönder"


def surum_lab(s, b):
    if "filo-erisim-ok" in b:
        return 0, "filo-erisim-ok\n", ""
    return 0, f"sunucu={s.ad}\nsurum=1.4.2\n", ""


@pytest.fixture
def posta(monkeypatch):
    gonderilen = []
    from filo import rapor
    monkeypatch.setattr(rapor, "eposta_gonder", lambda alici, konu, govde, ekler=(), ayar=None:
                        gonderilen.append({"alici": alici, "konu": konu, "ekler": list(ekler)}) or "<id>")
    return gonderilen


def kaptan_isi(m, tmp_path):
    sc = Senaryo(akis={"adimlar": ["betik_calistir", "sonucu_donustur", "eposta_gonder"]}, hedef={"ad": "PA-APP-01,PA-APP-02"},
                 **{"param:betik_calistir": {"betik": "uygulama_surumu"}, "param:sonucu_donustur": {"bicim": "csv"},
                    "param:eposta_gonder": {"alici": "ops@lab.yerel"}})
    k = Kaptan(FakeModel(islev=sc), m, kayit(tmp_path, TALEP, "kaptan"), akis_dizini=tmp_path / "akislar").calistir(TALEP)
    assert k.durum == "bitti", k.rapor
    return k


def test_kaptan_akisi_beceriye_donusur_ve_kalfa_benzerini_yurutur(motor_kur, tmp_path, posta):
    m, t = motor_kur(surum_lab)
    k = kaptan_isi(m, tmp_path)
    yeni = donustur.isten_beceri(m.katalog, m.envanter, k.sozluk(), baslik="Uygulama sürüm raporu")
    assert yeni["tur"] == "zincir" and yeni["surum"] == 1 and yeni["kaynak"]["is"] == k.kimlik
    assert [a["beceri"] for a in yeni["adimlar"]] == ["betik_calistir", "sonucu_donustur", "eposta_gonder"]
    assert yeni["girdi"]["betik"]["varsayilan"] == "uygulama_surumu" and yeni["girdi"]["bicim"]["varsayilan"] == "csv"
    assert yeni["girdi"]["alici"]["varsayilan"] == "ops@lab.yerel"
    assert yeni["risk"] == m.katalog.etkin_risk(m.katalog[yeni["ad"]])[0] == 1
    assert "PA-APP-01" not in str(yeni["adimlar"])                    # sunucu adı beceriye gömülmedi
    assert yeni["ad"] in m.katalog

    talep2 = "PB sunucularında uygulama sürüm raporunu CSV olarak ops@lab.yerel adresine gönder"
    assert yeni["ad"] in aday_beceriler(m.katalog, talep2)
    sc = Senaryo(beceri={"secim": yeni["ad"], "gerekce": "hazır rapor becerisi"}, hedef={"ad": "PB*"},
                 **{"param:" + yeni["ad"]: {"alici": "ops@lab.yerel"}})
    model = FakeModel(islev=sc)
    posta.clear()
    k2 = Kalfa(model, m, kayit(tmp_path, talep2, "kalfa")).calistir(talep2)
    assert k2.durum == "bitti", k2.rapor
    assert model.cagri <= 3, sc.sorulan                       # beceri + hedef + parametre
    assert len(posta) == 1 and posta[0]["ekler"][0][0].endswith(".csv")   # zincir kendi postasını attı, Kalfa ikinci atmadı
    assert {s for s, _ in t.cagrilar if "surum" in _} >= {"PB-APP-01", "PB-DB-01", "PB-WEB-01"}


def test_duruma_ozgu_onarim_kalici_adim_olmaz(motor_kur):
    m, _ = motor_kur(surum_lab)
    is_ = {"kimlik": "k1", "ajan": "kaptan", "durum": "bitti", "talep": "PA-APP-01'e jq paketini kur, ops@lab.yerel adresine bildir",
           "ek": {"yapilan": [{"beceri": "paket_onar", "parametreler": {}, "onarim": True},
                              {"beceri": "paket_kur", "parametreler": {"paketler": ["jq"]}},
                              {"beceri": "eposta_gonder", "parametreler": {"alici": "ops@lab.yerel"}}]}}
    t = donustur.isten_beceri(m.katalog, m.envanter, is_)
    assert [a["beceri"] for a in t["adimlar"]] == ["paket_kur", "eposta_gonder"]
    assert "paket_onar" in t["aciklama"] and "jq" in t["etiketler"]


def test_tek_seferlik_betik_isi_beceri_olur(motor_kur, tmp_path):
    m, _ = motor_kur(surum_lab)
    is_ = {"kimlik": "x1", "ajan": "kalfa", "durum": "bitti", "talep": "PA sunucularında uygulama sürümünü oku",
           "adimlar": [{"beceri": "betik_calistir", "durum": "basarili", "parametreler": {"betik": "uygulama_surumu"}}]}
    yeni = donustur.isten_beceri(m.katalog, m.envanter, is_)
    assert yeni["tur"] == "uzak" and "{yol}" in yeni["komut"]["linux"]
    assert yeni["girdi"]["yol"]["varsayilan"] == "/opt/uygulama/surum.txt" and yeni["risk"] == 0
    assert yeni["cikti"]["bicim"] == "anahtar_deger"
    with pytest.raises(donustur.DonusturmeHatasi):
        donustur.isten_beceri(m.katalog, m.envanter, {**is_, "durum": "kismi"})


IYI = {"ad": "acik_dosya_sayisi", "baslik": "Açık dosya sayısı", "aciklama": "Sistemdeki açık dosya tanıtıcısı sayısı",
       "etiketler": ["açık dosya", "fd"], "risk": 0, "girdi": {},
       "cikti": {"bicim": "anahtar_deger", "alanlar": {"acik": "tamsayi"}},
       "komut": {"linux": "echo acik=$(cut -f1 /proc/sys/fs/file-nr)"}}


def test_tariften_taslak_kod_denetimi_ve_kuru_calistirma(motor_kur, tmp_path):
    m, t = motor_kur(lambda s, b: (0, "acik=1234\n", "") if "file-nr" in b else (0, "", ""))
    eksik = {**IYI, "komut": {"linux": "echo acik=$(cut -f1 {dosya})"}}           # tanımsız yer tutucu
    yazan = {**IYI, "ad": "x_yazar", "komut": {"linux": "echo 1 > /etc/x"}}         # yazan komut, beyan risk 0
    model = FakeModel([eksik, yazan, IYI])
    r = donustur.tariften_beceri(model, m, "açık dosya tanıtıcısı sayısını raporla", "PA-APP-01")
    assert r["durum"] == "katalogda" and "acik_dosya_sayisi" in m.katalog, r
    hatalar = [d.get("hata") or "" for d in r["iz"][0]["denemeler"]]
    assert "tanımsız yer tutucu" in hatalar[0] and "kuru çalıştırma" in hatalar[1]
    assert m.katalog["acik_dosya_sayisi"]["kaynak"]["sinama"]["sunucu"] == "PA-APP-01"


def test_kuru_calistirmadan_gecmeyen_taslak_kataloga_girmez(motor_kur, tmp_path, monkeypatch):
    monkeypatch.setattr(donustur, "TASLAKLAR", tmp_path / "taslaklar")
    m, t = motor_kur(lambda s, b: (0, "beklenmeyen çıktı\n", "") if "file-nr" in b else (0, "", ""))
    r = donustur.tariften_beceri(FakeModel([IYI]), m, "açık dosya sayısı", "PA-APP-01")
    assert r["durum"] == "taslak" and "şemaya uymuyor" in r["neden"]
    assert "acik_dosya_sayisi" not in m.katalog and list((tmp_path / "taslaklar").glob("*.json"))
