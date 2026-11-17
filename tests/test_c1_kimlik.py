"""C1: çalıştırma kimliği (bağlantı kullanıcısı / root / adı verilen kullanıcı). Laboratuvar sınaması ayrı (lab)."""
import pytest

from filo.gateway import FakeModel
from filo.kalfa import Kalfa
from filo.kimlik import izinli_kimlikler, kimlik_sor, metinden_kimlik, sar
from filo.motor import PlanHatasi

from test_ajanlar import Senaryo, erisimli, kayit


def test_izinli_kimlikler_ve_sarma(envanter):
    assert izinli_kimlikler(envanter["PA-APP-01"]) == ["baglanti", "root", "uygulama"]
    assert izinli_kimlikler(envanter["PW-WIN-01"]) == ["baglanti"]
    s = envanter["PA-APP-01"]
    assert sar("id -un", None, s) == "id -un" and sar("id -un", "filo", s) == "id -un"
    b = sar("id -un\n", "root", s)
    assert "sudo -n -u root -- true" in b and "exec sudo -n -u root -- sh -s <<'FILO_KIMLIK_" in b and "\nid -un\n" in b


def test_plan_kimligi_denetler_ve_yazar(motor_kur, denetim):
    m, t = motor_kur()
    p = m.plan("komut_calistir", {"komut": "id -un"}, "PA-APP-01,PC-BATCH-01", kimlik="uygulama")
    assert p["kimlik_calistirma"] == "uygulama"
    a = m.yurut(p, {})
    assert all("sudo -n -u uygulama" in b for s, b in t.cagrilar if "filo-erisim-ok" not in b)
    assert a["kimlik_calistirma"] == "uygulama"
    assert '"calistirma_kimligi": "uygulama"' in denetim.yol.read_text(encoding="utf-8")
    with pytest.raises(PlanHatasi, match="postgres.*izinli değil"):
        m.plan("komut_calistir", {"komut": "id -un"}, "PA-APP-01", kimlik="postgres")
    with pytest.raises(PlanHatasi, match="izinli değil"):
        m.plan("servis_durumu", {"servis": "uygulama"}, "PW-WIN-01", kimlik="root")
    assert "kimlik_calistirma" not in m.plan("komut_calistir", {"komut": "id -un"}, "PA-APP-01", kimlik="baglanti")


def test_yetki_yok_sinifi_yeniden_denenmez(motor_kur):
    def dav(s, b):
        if "filo-erisim-ok" in b:
            return 0, "filo-erisim-ok\n", ""
        if s.ad == "PC-BATCH-01":
            return 126, "", "filo-kimlik-reddi: uygulama: sudo: a password is required\n"
        return 0, "uygulama\n", ""
    m, t = motor_kur(dav, yeniden=2)
    a = m.yurut(m.plan("komut_calistir", {"komut": "id -un"}, "PA-APP-01,PC-BATCH-01", kimlik="uygulama"), {})
    r = {x["sunucu"]: x for x in a["sonuclar"]}
    assert r["PC-BATCH-01"]["durum"] == "hatali" and r["PC-BATCH-01"]["yetki_yok"] and r["PC-BATCH-01"]["deneme"] == 1
    assert "yetki yok" in r["PC-BATCH-01"]["neden"] and "password is required" in r["PC-BATCH-01"]["neden"]
    assert a["durum"] == "kismi"


def test_talepten_kimlik():
    assert metinden_kimlik("PA-APP-01'de root olarak dosyayı göster") == "root"
    assert metinden_kimlik("webops kullanıcısıyla çalıştır") == "webops"
    assert metinden_kimlik("Sonucu XML olarak gönder") is None
    assert metinden_kimlik("raporcu adında bir kullanıcı hesabı aç") is None
    assert metinden_kimlik("işi batchops kimliğiyle çalıştır") == "batchops"
    # ipucu var ama kod çözemedi: model dar soruya cevap verir; talepte geçmeyen ad (uydurma) reddedilir
    model = FakeModel([{"kimlik": "deploy"}, {"kimlik": "baglanti"}])
    assert kimlik_sor(model, "bunu kendi kullanıcısıyla çalıştır", []) is None and model.cagri == 2
    assert kimlik_sor(None, "PB-APP-01 disk durumu", []) is None


def test_kalfa_root_olarak_ve_izinsiz_kimlik(motor_kur, tmp_path):
    m, t = motor_kur(erisimli(lambda s, b: (0, "anahtar_surumu=7\n", "")))
    talep = "PA-APP-01'de root olarak /etc/uygulama/anahtar.conf dosyasını cat ile göster"
    sc = Senaryo(beceri={"secim": "komut_calistir"}, hedef={"ad": "PA-APP-01"},
                 param={"komut": "cat /etc/uygulama/anahtar.conf"})
    model = FakeModel(islev=sc)
    k = Kalfa(model, m, kayit(tmp_path, talep, "kalfa")).calistir(talep)
    assert k.durum == "bitti" and k.plan["ana"]["kimlik_calistirma"] == "root"
    assert any("sudo -n -u root" in b for _, b in t.cagrilar)
    assert "çalıştırma kimliği" not in sc.sorulan                 # kimliği kod çözdü
    talep2 = "PA-APP-01'de postgres kullanıcısıyla id komutunu çalıştır"
    sc2 = Senaryo(beceri={"secim": "komut_calistir"}, hedef={"ad": "PA-APP-01"}, param={"komut": "id"})
    n = len(t.cagrilar)
    k2 = Kalfa(FakeModel(islev=sc2), m, kayit(tmp_path, talep2, "kalfa")).calistir(talep2)
    assert k2.durum == "hata" and "postgres" in k2.rapor and "izinli değil" in k2.rapor
    assert len(t.cagrilar) == n                                   # hiçbir şey çalışmadı
