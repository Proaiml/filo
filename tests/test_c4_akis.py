"""C4: yapılı akış — biçim doğrulaması, yürütme (dal, sunucu dalı, döngü, paralel, alt akış, bekleme, onay, bildirim)
ve küçük model için dar kararlarla kurulum (FakeModel, laboratuvar gerekmez)."""
import json
import threading
import time

from filo.akis_motoru import BICIM, SURUM, akis_ozeti, dogrula, eski_akistan
from filo.gateway import FakeModel
from filo.isler import IsKaydi
from filo.kaptan import Kaptan, akis_listesi, akis_yurut

from test_ajanlar import Senaryo, erisimli, kayit, posta  # noqa: F401


class Senaryo4(Senaryo):
    ANAHTAR = [("insan onayını hangi adımdan", "onay"), ("ayrım hangi sunucuları", "kosul_secenek"), ("ayrım hangi adımın", "kosul_adim"), ("Koşulu yaz", "kosul"),
               ("YALNIZ koşulu", "kol"), ("HER öğe için", "dongu"), ("AYNI ANDA", "paralel"), ("kayıtlı '", "alt"),
               ("beklemeyi hangi adımdan", "bekle")] + Senaryo.ANAHTAR


def akis(*adimlar, girdi=None):
    return {"bicim": BICIM, "surum": SURUM, "girdi": girdi or {}, "adimlar": list(adimlar)}


def b(kimlik, beceri, **p):
    return {"kimlik": kimlik, "tur": "beceri", "beceri": beceri, "parametreler": p}


def test_dogrulama_reddeder(motor_kur, tmp_path):
    m, _ = motor_kur()
    k = m.katalog
    assert dogrula(akis(b("a1", "servis_durumu", servis="uygulama")), k) == []
    h = dogrula(akis({"kimlik": "d1", "tur": "dongu", "kadar": {"adim": "a1", "olcu": "durum", "esit": "basarili"},
                      "govde": [b("a1", "servis_durumu", servis="x")]}), k)
    assert any("üst sınır" in x and "sonsuz döngü" in x for x in h)
    h = dogrula(akis({"kimlik": "z", "tur": "bitir"}, b("a1", "servis_durumu", servis="x")), k)
    assert any("erişilemeyen adım" in x for x in h)
    h = dogrula(akis(b("a1", "paket_kur", paketler="{paket_listesi}")), k)
    assert any("tanımsız değişken" in x for x in h)
    h = dogrula(akis(b("a1", "servis_durumu", servis="{paketler}"), girdi={"paketler": {"tip": "liste"}}), k)
    assert any("tip uyuşmazlığı" in x for x in h)
    h = dogrula(akis(b("a1", "disk_durumu"), {"kimlik": "d", "tur": "dal", "kosul": {"adim": "a1", "olcu": "basarili_sayisi",
                                                                                   "buyuk": "çok"}, "evet": [b("a2", "disk_durumu")]}), k)
    assert any("sayı ister" in x for x in h)
    h = dogrula(akis({"kimlik": "d", "tur": "dal", "kosul": {"adim": "a9", "olcu": "durum", "esit": "basarili"},
                      "evet": [b("a2", "disk_durumu")]}), k)
    assert any("tanımsız ya da sonra gelen" in x for x in h)
    h = dogrula(akis({"kimlik": "w", "tur": "bekle", "kosul": {"beceri": "servis_durumu", "alan": "durum", "esit": "active"}}), k)
    assert any("zaman aşımı" in x for x in h)
    (tmp_path / "x.json").write_text(json.dumps(akis({"kimlik": "s", "tur": "alt_akis", "akis": "x"})), encoding="utf-8")
    assert any("alt akış döngüsü" in x for x in dogrula(akis({"kimlik": "s0", "tur": "alt_akis", "akis": "x"}), k, tmp_path))
    v1 = {"ad": "eski", "adimlar": [{"beceri": "disk_durumu", "parametreler": {}}]}
    assert dogrula(eski_akistan(v1), k) == [] and akis_ozeti(eski_akistan(v1)) == "disk_durumu"


def _servis_lab(durumlar):
    cagri = []

    def dav(s, bt):
        if "filo-erisim-ok" in bt:
            return 0, "filo-erisim-ok\n", ""
        if "restart" in bt:
            cagri.append(("restart", s.ad))
            durumlar[s.ad] = "active"
            return 0, "servis=uygulama\ndurum=active\n", ""
        if "is-active" in bt or "status" in bt:
            return 0, f"servis=uygulama\ndurum={durumlar.get(s.ad, 'active')}\n", ""
        return 0, "", ""
    return dav, cagri


def test_kaptan_dar_kararlarla_sunucu_dali_kurar_ve_yurutur(motor_kur, tmp_path):
    durumlar = {"PA-APP-02": "inactive"}
    dav, cagri = _servis_lab(durumlar)
    m, _ = motor_kur(erisimli(dav))
    talep = "PA-APP-01 ve PA-APP-02'de uygulama servisinin durumuna bak; çalışmayanlarda servisi yeniden başlat"
    sc = Senaryo4(akis={"adimlar": ["servis_durumu", "servis_yeniden_baslat"]}, hedef={"ad": "PA-APP-01,PA-APP-02"},
                  param={"servis": "uygulama"}, kosul_adim={"secim": "a1"},
                  kosul_secenek={"secim": "durum_degil_active"}, kol={"secim": ["a2"]})
    k = Kaptan(FakeModel(islev=sc), m, kayit(tmp_path, talep, "kaptan"), akis_dizini=tmp_path / "a", inisiyatif=3)
    k.planla(talep)
    a = k.kayit.plan["akis"]
    assert a["bicim"] == BICIM and a["adimlar"][1]["tur"] == "dal" and a["adimlar"][1]["evet"][0]["beceri"] == "servis_yeniden_baslat"
    assert any(g["soru"] == "akış yapısı (kod)" and "dal[" in str(g["sonuc"]) for g in k.kayit.gerekce)
    r = k.yurut()
    assert r.durum == "bitti", r.rapor
    assert set(cagri) == {("restart", "PA-APP-02")}               # çalışan sunucu yeniden başlatılmadı (kuru dahil)
    assert r.ek["akis_izleri"]["dal1"]["evet"] == ["PA-APP-02"]


def test_ipucu_yoksa_yapi_sorulmaz(motor_kur, tmp_path):
    m, _ = motor_kur()
    talep = "PA-APP-01'de disk doluluğunu göster"
    sc = Senaryo4(akis={"adimlar": ["disk_durumu"]}, hedef={"ad": "PA-APP-01"}, param={})
    model = FakeModel(islev=sc)
    k = Kaptan(model, m, kayit(tmp_path, talep, "kaptan"), akis_dizini=tmp_path / "a").planla(talep)
    assert "bicim" not in k.plan["akis"] and not any("yapı" in g["soru"] for g in k.gerekce)   # yapı sorusu yok


def test_dongu_hata_olsa_da_devam_ve_kismi(motor_kur, tmp_path):
    kurulan = []

    def dav(s, bt):
        if "filo-erisim-ok" in bt:
            return 0, "filo-erisim-ok\n", ""
        if "yokpaket" in bt and ("install" in bt or "-s" in bt):
            return 100, "", "E: Unable to locate package yokpaket"
        for p in ("jq", "tree"):
            if f" {p}" in bt and "install" in bt and "-s " not in bt and "--simulate" not in bt:
                kurulan.append((s.ad, p))
        return 0, "jq|1.6\n", ""
    m, _ = motor_kur(erisimli(dav))
    talep = "PB-WEB-01'e jq, yokpaket ve tree paketlerini tek tek kur; biri başarısız olursa diğerlerine devam et"
    sc = Senaryo4(akis={"adimlar": ["paket_kur"]}, hedef={"ad": "PB-WEB-01"}, param={"paketler": ["jq", "yokpaket", "tree"]},
                  dongu={"secim": "a1.paketler"})
    k = Kaptan(FakeModel(islev=sc), m, kayit(tmp_path, talep, "kaptan"), akis_dizini=tmp_path / "a", inisiyatif=3,
               deneme_siniri=0)
    k.planla(talep)
    d = k.kayit.plan["akis"]["adimlar"][0]
    assert d["tur"] == "dongu" and d["liste"] == ["jq", "yokpaket", "tree"] and d["govde"][0]["hata_durumunda"] == "devam"
    r = k.yurut()
    assert r.durum == "kismi" and "yokpaket" in r.rapor and "Devam edilen hatalar" in r.rapor
    assert {p for _, p in kurulan} == {"jq", "tree"}


def test_paralel_kollar_ayni_anda(motor_kur, tmp_path):
    bas, bitis, kilit = {}, {}, threading.Lock()

    def dav(s, bt):
        if "filo-erisim-ok" in bt:
            return 0, "filo-erisim-ok\n", ""
        ad = "disk" if "df" in bt else "servis"
        with kilit:
            bas[ad] = time.monotonic()
        time.sleep(0.3)
        with kilit:
            bitis[ad] = time.monotonic()
        return (0, "/|1000|400|40|/\n", "") if ad == "disk" else (0, "servis=uygulama\ndurum=active\n", "")
    m, _ = motor_kur(erisimli(dav))
    k = IsKaydi("paralel", "sabit-akis", dizin=tmp_path / "i")
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "saglik.json").write_text(json.dumps(akis(
        {"kimlik": "p1", "tur": "paralel", "kollar": [[b("a1", "disk_durumu")], [b("a2", "servis_durumu", servis="uygulama")]]}),
        ensure_ascii=False), encoding="utf-8")
    r = akis_yurut(m, "saglik", "PA-APP-01", k, dizin=tmp_path / "a")
    assert r.durum == "bitti", r.rapor
    assert bas["disk"] < bitis["servis"] and bas["servis"] < bitis["disk"]          # kollar çakıştı (aynı anda)


def test_alt_akis_girdi_ciktisi_ve_bekleme_sahte_saat(motor_kur, tmp_path):
    dav, cagri = _servis_lab({})
    m, t = motor_kur(erisimli(dav))
    d = tmp_path / "a"
    d.mkdir()
    (d / "servis-tazele.json").write_text(json.dumps({**akis(b("s1", "servis_yeniden_baslat", servis="{servis}"),
                                                             girdi={"servis": {"tip": "metin", "varsayilan": "webd"}})}),
                                          encoding="utf-8")
    saat = {"t": 0.0}
    ana = akis({"kimlik": "c", "tur": "alt_akis", "akis": "servis-tazele", "girdi": {"servis": "uygulama"}},
               {"kimlik": "w", "tur": "bekle", "sure_sn": 300},
               {"kimlik": "y", "tur": "bekle", "kosul": {"beceri": "servis_durumu", "parametreler": {"servis": "uygulama"},
                                                        "alan": "durum", "esit": "active"}, "zaman_asimi_sn": 60})
    assert dogrula(ana, m.katalog, d) == []
    (d / "ana.json").write_text(json.dumps(ana), encoding="utf-8")
    k = IsKaydi("alt", "sabit-akis", dizin=tmp_path / "i")
    kap = Kaptan(None, m, k, inisiyatif=3, deneme_siniri=0, akis_dizini=d, saat=lambda: saat["t"],
                 uyu=lambda s: saat.__setitem__("t", saat["t"] + s), yapi_kur=False)
    kap._kayit(k.talep)
    k.plan = {"akis": ana, "hedef": m.envanter.dondur("PA-APP-01"), "adimlar": ["alt_akis", "bekle", "bekle"]}
    t0 = time.monotonic()
    r = kap.yurut()
    assert r.durum == "bitti", r.rapor
    assert set(cagri) == {("restart", "PA-APP-01")} and any("sudo" in x or "restart" in x and "uygulama" in x for _, x in t.cagrilar)
    assert saat["t"] >= 300 and time.monotonic() - t0 < 5             # 300 sn bekleme sahte saatle, gerçek bekleme yok


def test_onay_adimi_reddedilirse_degisiklik_yok_bildirim_gider(motor_kur, tmp_path, posta):
    dav, cagri = _servis_lab({"PB-WEB-01": "inactive"})
    m, _ = motor_kur(erisimli(dav), kural={"varsayilan": "onayla", "beceriler": {"insan_onayi": "reddet"}})
    talep = "PB-WEB-01'de webd servisini yeniden başlatmadan önce benden onay al ve sonucu ops@lab.yerel adresine bildir"
    sc = Senaryo4(akis={"adimlar": ["servis_yeniden_baslat", "eposta_gonder"]}, hedef={"ad": "PB-WEB-01"},
                  **{"param:servis_yeniden_baslat": {"servis": "webd"}, "param:eposta_gonder": {"alici": "ops@lab.yerel"}})
    k = Kaptan(FakeModel(islev=sc), m, kayit(tmp_path, talep, "kaptan"), akis_dizini=tmp_path / "a", inisiyatif=3)
    k.planla(talep)
    a = k.kayit.plan["akis"]["adimlar"]
    assert a[0]["tur"] == "onay" and a[0]["reddedilirse"][0]["tur"] == "bildirim"   # tek seçenek: model sorulmadı
    r = k.yurut()
    assert r.durum == "reddedildi" and not cagri                     # düzey 3 olsa da onay adımı insan ister
    assert posta and "onay verilmedi" in posta[0]["konu"]


def test_yapili_akis_sabit_akis_olarak_kaydedilir_ve_eski_akis_listelenir(motor_kur, tmp_path):
    durumlar = {"PA-APP-02": "inactive"}
    dav, cagri = _servis_lab(durumlar)
    m, _ = motor_kur(erisimli(dav))
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "eski.json").write_text(json.dumps({"ad": "eski", "talep": "x", "adimlar": [
        {"beceri": "servis_durumu", "parametreler": {"servis": "uygulama"}}]}), encoding="utf-8")
    talep = "PA-APP-01 ve PA-APP-02'de uygulama servisinin durumuna bak; çalışmayanlarda servisi yeniden başlat"
    sc = Senaryo4(akis={"adimlar": ["servis_durumu", "servis_yeniden_baslat"]}, hedef={"ad": "PA-APP-01,PA-APP-02"},
                  param={"servis": "uygulama"}, kosul_adim={"secim": "a1"},
                  kosul_secenek={"secim": "durum_degil_active"}, kol={"secim": ["a2"]})
    Kaptan(FakeModel(islev=sc), m, kayit(tmp_path, talep, "kaptan"), akis_dizini=tmp_path / "a", inisiyatif=3).calistir(talep)
    liste = {x["ad"]: x for x in akis_listesi(tmp_path / "a")}
    yeni = next(x for ad, x in liste.items() if ad != "eski")
    assert yeni["yapili"] and yeni["surum"] == 2 and "dal[" in yeni["ozet"] and liste["eski"]["surum"] == 1
    durumlar["PA-APP-01"] = "inactive"
    cagri.clear()
    r = akis_yurut(m, yeni["ad"], "PA-APP-01,PA-APP-02", IsKaydi("t", "sabit-akis", dizin=tmp_path / "i"), dizin=tmp_path / "a",
                   inisiyatif=3)
    assert r.durum == "bitti" and set(cagri) == {("restart", "PA-APP-01")}


def test_kalfa_kosullu_degisikligi_butun_hedefe_uygulamaz(motor_kur, tmp_path):
    """Duman koşusu A01: Kalfa "çalışmayanlarda yeniden başlat" talebinde çalışan servisi de yeniden başlattı."""
    from filo.ajan_ortak import kosul_destegi
    from filo.kalfa import Kalfa
    m, t = motor_kur()
    talep = "PA grubundaki sunucularda uygulama servisinin durumuna bak; çalışmayanlarda uygulama servisini yeniden başlat"
    sc = Senaryo4(beceri={"secim": "servis_yeniden_baslat"}, hedef={"ad": "PA*"}, param={"servis": "uygulama"})
    k = Kalfa(FakeModel(islev=sc), m, kayit(tmp_path, talep, "kalfa")).calistir(talep)
    assert k.durum == "beceri_yok" and "Kaptan" in k.rapor and not t.cagrilar
    # "uygulama servisi" rol=uygulama koşuluna dayanak değildir (hedef sessizce daralıyordu)
    assert kosul_destegi({"oznitelik": {"rol": "uygulama"}}, talep) == ["rol=uygulama"]
    assert kosul_destegi({"oznitelik": {"rol": "uygulama"}}, "uygulama sunucularında disk durumu") == []
