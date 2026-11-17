"""D0 (dördüncü tur): açık kusurların regresyon sınamaları."""
import json
import threading

from filo.ajan_ortak import kapsam_eksigi, talep_okumalari
from filo.gateway import FakeModel
from filo.kalfa import Kalfa

from test_ajanlar import Senaryo, erisimli, kayit, posta  # noqa: F401 (posta: fixture)

A03 = ("PA-DB-01 sunucusunda disk doluluğunu ve dbd servisinin durumunu aynı anda kontrol et, sonucu ops@lab.yerel "
       "adresine bildir.")


def test_salt_okur_kapsam_kodla(motor_kur):
    """Üçüncü tam koşu A03/kalfa: iki okuma işinden biri yapıldı, model 'eksik yok' dedi, sahte başarı."""
    k = motor_kur()[0].katalog
    assert {a for a, *_ in talep_okumalari(A03)} == {"disk doluluğu", "servis durumu"}
    assert kapsam_eksigi(k, A03, ["disk_durumu"]) == ["servis durumu okuması ('servisinin durumunu')"]
    assert kapsam_eksigi(k, A03, ["disk_durumu", "servis_durumu"]) == []
    # genel komut becerisi, parametresi iki okumayı da gösteriyorsa kapsar; yalnız birini gösteriyorsa kapsamaz
    assert kapsam_eksigi(k, A03, ["komut_calistir"], {"komut_calistir": {"komut": "df -P; filo-svc is-active dbd"}}) == []
    assert kapsam_eksigi(k, A03, ["komut_calistir"], {"komut_calistir": {"komut": "df -P"}}) != []
    # tek okumalı talepler: doğal beceri kapsar (yanlış "kısmi" olmasın)
    for talep, beceri in (("web grubundaki sunucularda webd servisinin durumunu kontrol et", "servis_durumu"),
                          ("PA ile başlayan sunucularda disk doluluğunu kontrol et", "disk_durumu"),
                          ("PB-APP-01 ve PB-WEB-01 sunucularına Filo ajanını kur ve ajanların durumunu bildir", "ajan_kur"),
                          ("pb grubundaki bütün sunucularda çalışma süresini (uptime) oku", "sistem_envanteri"),
                          ("PB-APP-01 ve PC-BATCH-01 sunucularında bekleyen yama sayısını topla", "yama_durumu"),
                          ("PA-APP-01'de uygulama servisini yeniden başlat, sonra servisin durumunu kontrol et",
                           "servis_yeniden_baslat"),
                          ("Yeni açılan PA-WEB-02 sunucusunu teslim et (webd servisi çalışır durumda)", "teslim_uygula")):
        assert kapsam_eksigi(k, talep, [beceri]) == [], talep


def test_a03_kalfa_model_eksik_yok_dese_de_kismi(motor_kur, tmp_path, posta):
    m, _ = motor_kur(erisimli(lambda s, b: (0, "/veri|16384|1024|6|tamam\n", "")))
    sc = Senaryo(beceri={"secim": "disk_durumu"}, hedef={"ad": "PA-DB-01"}, param={}, kapsam={"eksik": "yok"})
    model = FakeModel(islev=sc)
    k = Kalfa(model, m, kayit(tmp_path, A03, "kalfa")).planla(A03)
    assert k.durum == "plan_hazir", k.rapor
    assert "kapsam" not in sc.sorulan and "servis durumu" in k.plan["eksik"]
    k = Kalfa(model, m, k).yurut()
    assert k.durum == "kismi" and "servis durumu" in k.rapor


def test_defter_gecici_okuma_hatasinda_bos_saymaz(tmp_path, monkeypatch):
    """D0-c: belirteç deposu bir an okunamayınca boş sayılıyordu; paralel kurulumda geçerli belirteç reddediliyordu."""
    import pathlib
    from filo.ajan_kapisi import Defter
    d = Defter(tmp_path / "ajanlar", tmp_path / "gizli.json")
    d.belirtecler_yaz({"a": {"sunucu": "X", "son": 1e12}})
    asil = pathlib.Path.read_text
    sayac = {"n": 0}

    def kilitli(self, *a, **kw):
        if self.name == "belirtecler.json" and sayac["n"] < 3:
            sayac["n"] += 1
            raise PermissionError(13, "başka süreç açık tutuyor")
        return asil(self, *a, **kw)
    monkeypatch.setattr(pathlib.Path, "read_text", kilitli)
    assert d.belirtecler() == {"a": {"sunucu": "X", "son": 1e12}} and sayac["n"] == 3
    monkeypatch.setattr(pathlib.Path, "read_text", asil)
    assert Defter(tmp_path / "yok", tmp_path / "g2.json").belirtecler() == {}     # dosya yoksa boş


def test_kapida_paralel_belirtec_ve_kayit(tmp_path):
    """Aynı anda 8 belirteç üretilip 8 kayıt yapılınca hiçbiri kaybolmaz."""
    from filo.ajan_kapisi import AjanKapisi, Defter
    from filo.denetim import Denetim
    kapi = AjanKapisi(port=0, defter=Defter(tmp_path / "a", tmp_path / "g.json"), denetim=Denetim(tmp_path / "d.jsonl"))
    adlar = [f"S{i}" for i in range(8)]
    belirtec = {}
    th = [threading.Thread(target=lambda a=a: belirtec.__setitem__(a, kapi.belirtec_uret(a))) for a in adlar]
    [t.start() for t in th]
    [t.join() for t in th]
    sonuc = {}
    th = [threading.Thread(target=lambda a=a: sonuc.__setitem__(a, kapi.kayit({"belirtec": belirtec[a], "sunucu": a})))
          for a in adlar]
    [t.start() for t in th]
    [t.join() for t in th]
    assert len(sonuc) == 8 and len({v["ajan_kimligi"] for v in sonuc.values()}) == 8
    assert len(json.loads((tmp_path / "a" / "kayit.json").read_text(encoding="utf-8"))) == 8


def test_lab_kilidi_canli_surecte_ikinci_kullaniciyi_durdurur(tmp_path, monkeypatch):
    """D0-b: bench koşusu sürerken laboratuvar sınamaları (ya da ikinci koşu) laboratuvara dokunmaz."""
    import os
    import pytest
    from filo import lab
    monkeypatch.setattr(lab, "LAB_KILIDI", tmp_path / "LAB_KILIT")
    (tmp_path / "LAB_KILIT").write_text(json.dumps({"pid": os.getppid(), "amac": "bench koşusu"}), encoding="utf-8")
    assert lab.lab_kilidi_kimde()["amac"] == "bench koşusu"
    with pytest.raises(RuntimeError):
        lab.lab_kilidi_al("ikinci")
    (tmp_path / "LAB_KILIT").write_text(json.dumps({"pid": 999999, "amac": "ölü süreç"}), encoding="utf-8")
    assert lab.lab_kilidi_kimde() is None                  # ölü sürecin kilidi bayat
    lab.lab_kilidi_al("ben")
    assert json.loads((tmp_path / "LAB_KILIT").read_text(encoding="utf-8"))["pid"] == os.getpid()
    lab.lab_kilidi_birak()
    assert not (tmp_path / "LAB_KILIT").exists()


def test_hakem_parmak_izi_farki_ve_okunamayan():
    from filo.bench import hakem
    a, b = hakem.ParmakIzi("x"), hakem.ParmakIzi("y")
    a.satirlar, b.satirlar = ("batchd active 40", "uygulama active 38"), ("batchd active 77", "uygulama active 38")
    assert hakem.parmak_izi_farki(a, b) == ["- batchd active 40", "+ batchd active 77"]
