"""C0 (üçüncü tur): açık kusurların regresyon sınamaları (FakeModel, laboratuvar gerekmez)."""
from filo.ajan_ortak import kapsam_eksigi, talep_eylemleri
from filo.gateway import FakeModel
from filo.kalfa import Kalfa

from test_ajanlar import Senaryo, erisimli, kayit, posta  # noqa: F401 (posta: fixture)

O11 = ("PA-APP-01'de /etc/uygulama/uygulama.conf bozulmuş: dosya kütüphanesindeki standart uygulama.conf dosyasını "
       "(port=8080, log_duzeyi=warn, baglanti_havuzu=20) oraya geri koy, uygulama servisini yeniden başlat ve sonucu "
       "ops@lab.yerel adresine bildir.")


def test_kod_kapsam_eksigini_bulur(motor_kur):
    m, _ = motor_kur()
    k = m.katalog
    assert {a for a, _, _ in talep_eylemleri(k, O11)} == {"dosya dağıtma", "yeniden başlatma"}
    assert kapsam_eksigi(k, O11, ["dosya_dagit"]) == ["yeniden başlatma ('yeniden baslat')"]
    assert kapsam_eksigi(k, O11, ["dosya_dagit", "servis_yeniden_baslat"]) == []
    # zincir beceri adımlarıyla kapsar; okuma talebinde eylem yok
    assert kapsam_eksigi(k, "PC-BATCH-01 sunucusuna jq paketini kur ve sonucu bildir", ["jq_kur_ve_bildir"]) == []
    assert kapsam_eksigi(k, "PB grubundaki sunucuların disk doluluğunu göster", ["disk_durumu"]) == []
    assert kapsam_eksigi(k, "Adı PA ile başlayan sunucularda betiği çalıştır", ["betik_calistir"]) == []
    assert kapsam_eksigi(k, "PB-APP-01 ve PC-BATCH-01 sunucularında raporcu adında bir kullanıcı hesabı aç",
                         ["kullanici_ac"]) == []
    assert kapsam_eksigi(k, "PB-DB-01 sunucusundaki Filo ajanını kaldır ve kaydını sil", ["ajan_kaldir"]) == []


def test_o11_kalfa_model_eksik_yok_dese_de_kismi(motor_kur, tmp_path, posta):
    """İkinci koşu O11: Kalfa dosyayı geri koydu, servisi yeniden başlatmadı; model 'eksik yok' dedi, iş 'bitti' oldu."""
    import hashlib
    from filo.beceri import DOSYALAR
    ozet = hashlib.sha256((DOSYALAR / "uygulama.conf").read_bytes()).hexdigest()
    m, _ = motor_kur(erisimli(lambda s, b: (0, f"hedef=/etc/uygulama/uygulama.conf\nozet={ozet}\n", "")))
    sc = Senaryo(beceri={"secim": "dosya_dagit"}, hedef={"ad": "PA-APP-01"},
                 param={"dosya": "uygulama.conf", "hedef": "/etc/uygulama/uygulama.conf"}, kapsam={"eksik": "yok"})
    model = FakeModel(islev=sc)
    k = Kalfa(model, m, kayit(tmp_path, O11, "kalfa")).planla(O11)
    assert k.durum == "plan_hazir", k.rapor
    assert "kapsam" not in sc.sorulan                       # kod eksik buldu: modele sorulmadı
    assert "yeniden başlatma" in k.plan["eksik"]
    k = Kalfa(model, m, k).yurut()
    assert k.durum == "kismi" and "yeniden başlatma" in k.rapor


def test_kalfa_adim_seridi_dar_genislikte_tasmaz():
    """Kalfa adım çubuğunda dar genişlikte 'Parametreler' ile 'Hedef' üst üste biniyordu: kutular sarılır, metin kesilir."""
    import pathlib
    css = (pathlib.Path(__file__).resolve().parent.parent / "filo" / "static" / "konsol.css").read_text(encoding="utf-8")
    satir = next(x for x in css.splitlines() if x.startswith(".adimlar li {"))
    assert "flex-wrap: wrap" in next(x for x in css.splitlines() if x.startswith(".adimlar {"))
    assert "text-overflow: ellipsis" in satir and "overflow: hidden" in satir and "white-space: nowrap" in satir


def test_degisiklik_eylemi_yoksa_degistiren_adim_dayanaksiz(motor_kur):
    """Üçüncü tam koşu O05: "durumunu kontrol et" talebine servis_baslat/servis_yeniden_baslat girdi."""
    from filo.ajan_ortak import dayanak_var
    m, _ = motor_kur()
    k = m.katalog
    oku = "PA-DB-01 ve PB-DB-01 sunucularında dbd servisinin durumunu kontrol et ve sonucu ops@lab.yerel adresine bildir."
    assert not dayanak_var(k, "servis_yeniden_baslat", oku) and not dayanak_var(k, "servis_baslat", oku)
    assert dayanak_var(k, "servis_durumu", oku) and dayanak_var(k, "eposta_gonder", oku)
    assert dayanak_var(k, "servis_yeniden_baslat", "PB-WEB-01'de webd servisini yeniden başlat")
    assert dayanak_var(k, "teslim_uygula", "Yeni açılan PA-WEB-02 sunucusunu web standardına göre teslim et")
    assert dayanak_var(k, "ajan_kur", "PB-APP-01 ve PB-WEB-01 sunucularına Filo ajanını kur")


def test_okuma_talebinde_kaptan_onarim_onermez(motor_kur, tmp_path):
    """Üçüncü tur O05 yeniden koşusu: "durumunu kontrol et" talebinde Kaptan yavaş servise servis_baslat uyguladı."""
    from filo.kaptan import Kaptan
    m, _ = motor_kur(erisimli(lambda s, b: (1, "", "zaman doldu")))
    talep = "PB-DB-01'de dbd servisinin durumunu kontrol et"
    sc = Senaryo(akis={"adimlar": ["servis_durumu"]}, hedef={"ad": "PB-DB-01"}, param={"servis": "dbd"},
                 teshis={"beceri": "yok"}, karar={"karar": "devret"})
    model = FakeModel(islev=sc)
    Kaptan(model, m, kayit(tmp_path, talep, "kaptan"), akis_dizini=tmp_path / "a", inisiyatif=3).calistir(talep)
    karar_sorulari = [ms[-1]["content"] for ms in model.mesajlar if "Ne yapılmalı?" in ms[-1]["content"]]
    assert karar_sorulari and not any("onarim:" in q for q in karar_sorulari)
