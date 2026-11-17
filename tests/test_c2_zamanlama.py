"""C2: zamanlayıcı ve bakım/yasak pencereleri. Saat sahtedir; gerçek bekleme yoktur."""
import datetime as dt

import pytest

from filo.gateway import FakeModel
from filo.zamanlayici import (Pencereler, Zamanlayici, ZamanlamaHatasi, metinden_zamanlama, okunakli,
                              sonraki_zamanlar, zamanlama_dogrula)

from test_ajanlar import Senaryo, erisimli, kayit, posta  # noqa: F401

SALI = dt.datetime(2026, 11, 17, 15, 0)          # 17 Kasım 2026 salı


class Saat:
    def __init__(self, an):
        self.an = an

    def __call__(self):
        return self.an


def pencereler(saat, ek=()):
    return Pencereler(saat=saat, veri={"yasak_politikasi": "bekle", "pencereler": [
        {"ad": "web-cumartesi", "tur": "bakim", "kapsam": "grup:web",
         "tekrar": {"tur": "haftalik", "gunler": ["cumartesi"], "baslangic": "02:00", "sure_dk": 240}},
        {"ad": "pb-dondurma", "tur": "yasak", "kapsam": "grup:pb",
         "tekrar": {"tur": "tek", "baslangic": "2026-11-17T14:00", "bitis": "2026-11-17T18:00"}}, *ek]})


def test_zamanlama_turleri_ve_sonraki_uc():
    assert SALI.weekday() == 1
    gun = sonraki_zamanlar({"tur": "gunluk", "saat": "2:00"}, SALI, n=3)
    assert gun == [dt.datetime(2026, 11, 18, 2, 0), dt.datetime(2026, 11, 19, 2, 0), dt.datetime(2026, 11, 20, 2, 0)]
    assert sonraki_zamanlar({"tur": "haftalik", "gunler": ["Cumartesi"], "saat": "03:30"}, SALI, n=2) == \
        [dt.datetime(2026, 11, 21, 3, 30), dt.datetime(2026, 11, 28, 3, 30)]
    assert sonraki_zamanlar({"tur": "aylik", "gun": 31, "saat": "02:00"}, SALI, n=2) == \
        [dt.datetime(2026, 11, 30, 2, 0), dt.datetime(2026, 12, 31, 2, 0)]          # kısa ayda son gün
    assert sonraki_zamanlar({"tur": "cron", "ifade": "0 2 * * 1-5"}, SALI, n=3)[2] == dt.datetime(2026, 11, 20, 2, 0)
    assert sonraki_zamanlar({"tur": "tek", "zaman": "2026-11-17T10:00"}, SALI) == []
    pen = pencereler(Saat(SALI))
    assert sonraki_zamanlar({"tur": "pencere", "pencere": "web-cumartesi"}, SALI, pen, 1) == [dt.datetime(2026, 11, 21, 2, 0)]
    assert okunakli({"tur": "haftalik", "gunler": ["cumartesi"], "saat": "03:30"}) == "her Cumartesi 03:30"
    for kotu in ({"tur": "gunluk", "saat": "25:00"}, {"tur": "haftalik", "saat": "02:00"}, {"tur": "cron", "ifade": "0 2 *"},
                 {"tur": "aylik", "gun": 40, "saat": "01:00"}, {"tur": "pencere", "pencere": "pb-dondurma"}):
        with pytest.raises(ZamanlamaHatasi):
            zamanlama_dogrula(kotu, pen)


def test_metinden_zamanlama(envanter):
    pen = pencereler(Saat(SALI))
    c = lambda t, h=None: metinden_zamanlama(t, SALI, pen, envanter, h)[0]  # noqa: E731
    assert c("Her gece 02:00'de PA sunucularının diskini raporla") == {"tur": "gunluk", "saat": "02:00"}
    assert c("her gece saat 2'de çalıştır") == {"tur": "gunluk", "saat": "02:00"}
    assert c("Her cumartesi 03:30'da yama durumunu topla") == {"tur": "haftalik", "gunler": ["cumartesi"], "saat": "03:30"}
    assert c("Yarın 23:30'da PB-WEB-01'de webd'yi yeniden başlat") == {"tur": "tek", "zaman": "2026-11-18T23:30"}
    assert c("her ayın 1'i 02:00'de rapor") == {"tur": "aylik", "gun": 1, "saat": "02:00"}
    assert c("PA-WEB-01'e jq paketini cumartesi bakım penceresinde kur", ["PA-WEB-01"]) == \
        {"tur": "pencere", "pencere": "web-cumartesi"}
    assert c("PA-APP-01'e jq kur ama bakım penceresinde", ["PA-APP-01"]) is None      # app için bakım penceresi yok


def test_pencere_acik_yasak_ve_sonu(envanter):
    pen = pencereler(Saat(SALI))
    y = pen.yasakta(envanter, ["PB-WEB-01", "PA-WEB-01"])
    assert set(y) == {"PB-WEB-01"} and y["PB-WEB-01"]["pencere"] == "pb-dondurma"
    assert pen.yasak_sonu(envanter, ["PB-WEB-01"]) == dt.datetime(2026, 11, 17, 18, 0)
    assert pen.acik_mi(pen.getir("web-cumartesi"), dt.datetime(2026, 11, 21, 5, 59))[0]
    assert not pen.acik_mi(pen.getir("web-cumartesi"), dt.datetime(2026, 11, 21, 6, 0))[0]
    assert pen.bakim_penceresi_bul(envanter, ["PA-WEB-01", "PB-WEB-01"]) == "web-cumartesi"
    with pytest.raises(ZamanlamaHatasi):
        Pencereler.dogrula({"ad": "x", "tur": "bakim", "kapsam": "grup:yok", "tekrar": {"tur": "gunluk", "baslangic": "01:00",
                                                                                     "sure_dk": 30}}, envanter)


def _zm(tmp_path, saat, cagri, pen=None, envanter=None, risk=3):
    return Zamanlayici(tmp_path / "z.json", saat=saat, pencereler=pen or pencereler(saat),
                       envanter_fn=(lambda: envanter) if envanter else None,
                       calistirici=lambda z, an, oo, n, ist=None: cagri.append((z["kimlik"], an, oo, n, ist)) or
                       {"is": f"is{len(cagri)}", "durum": "basladi"},
                       risk_fn=lambda t: (risk, risk >= 3, ["PB-WEB-01"]))


TANIM = {"tur": "beceri", "beceri": "servis_yeniden_baslat", "parametreler": {"servis": "webd"}, "hedef_secici": "PB-WEB-01"}


def test_tik_tekrarli_kacirilan_ve_onay(tmp_path):
    saat, cagri = Saat(dt.datetime(2026, 11, 17, 1, 0)), []
    z = _zm(tmp_path, saat, cagri)
    a = z.ekle("gece", TANIM, {"tur": "gunluk", "saat": "02:00"}, dondurulmus={"sunucular": ["PB-WEB-01"]})
    assert a["sonraki"] == "2026-11-17T02:00" and a["onay_gerekli"] and not a["onay_gecerli"]
    assert z.tik(dt.datetime(2026, 11, 17, 1, 59)) == [] and not cagri
    z.onayla(a["kimlik"], "web:operatör")
    olay = z.tik(dt.datetime(2026, 11, 17, 2, 0))
    assert olay[0]["olay"] == "calisti" and cagri[0][2]["veren"] == "web:operatör" and cagri[0][2]["tanim_surumu"] == 1
    assert z.getir(a["kimlik"])["sonraki"] == "2026-11-18T02:00"
    # tanım değişince onay düşer
    saat.an = dt.datetime(2026, 11, 17, 2, 5)
    z.degistir(a["kimlik"], zamanlama={"tur": "gunluk", "saat": "03:00"})
    b = z.getir(a["kimlik"])
    assert b["tanim_surumu"] == 2 and b["onay"] is None and any(g["olay"] == "onay_dustu" for g in b["gecmis"])
    assert b["sonraki"] == "2026-11-17T03:00"
    z.tik(dt.datetime(2026, 11, 17, 3, 0))
    assert cagri[1][2] is None                                    # onaysız koşu: onay koşu anında istenecek
    # konsol kapalıydı: 3 gün sonra açıldı → atla politikası koşmaz, sonrakini kurar
    z.tik(dt.datetime(2026, 11, 21, 10, 0))
    assert len(cagri) == 2 and z.getir(a["kimlik"])["gecmis"][-1]["olay"] == "kacirildi"
    assert z.getir(a["kimlik"])["sonraki"] == "2026-11-22T03:00"
    z.degistir(a["kimlik"], kacirilan="hemen")
    z.tik(dt.datetime(2026, 11, 23, 9, 0))
    assert len(cagri) == 3 and "kaçırılan koşu hemen" in cagri[2][3]


def test_yasak_pencere_politikalari(tmp_path, envanter):
    saat, cagri = Saat(dt.datetime(2026, 11, 17, 15, 0)), []
    z = _zm(tmp_path, saat, cagri, envanter=envanter)
    a = z.ekle("bekle", TANIM, {"tur": "tek", "zaman": "2026-11-17T15:00"}, yasak_politikasi="bekle",
               dondurulmus={"sunucular": ["PB-WEB-01"]})
    olay = z.tik(dt.datetime(2026, 11, 17, 15, 0))
    assert olay[0]["olay"] == "ertelendi" and not cagri and z.getir(a["kimlik"])["sonraki"] == "2026-11-17T18:00"
    z.tik(dt.datetime(2026, 11, 17, 18, 0))
    assert len(cagri) == 1 and z.getir(a["kimlik"])["son_calisma"]["plan_zamani"] == "2026-11-17T15:00"
    s = z.ekle("sor", TANIM, {"tur": "tek", "zaman": "2026-11-17T16:00"}, yasak_politikasi="sor",
               dondurulmus={"sunucular": ["PB-WEB-01"]})
    z.tik(dt.datetime(2026, 11, 17, 16, 0))
    assert z.getir(s["kimlik"])["bekleyen_soru"] and len(cagri) == 1
    z.tik(dt.datetime(2026, 11, 17, 16, 1))
    assert len(cagri) == 1                                        # soru cevaplanmadan çalışmaz
    z.soru_cevapla(s["kimlik"], "simdi", "web:operatör")
    assert len(cagri) == 2 and cagri[1][4]["kim"] == "web:operatör"   # yasak istisnası motor'a gider
    t = z.ekle("atla", TANIM, {"tur": "gunluk", "saat": "17:00"}, yasak_politikasi="atla",
               dondurulmus={"sunucular": ["PB-WEB-01"]})
    z.tik(dt.datetime(2026, 11, 17, 17, 0))
    assert len(cagri) == 2 and z.getir(t["kimlik"])["sonraki"] == "2026-11-18T17:00"
    # salt-okur iş yasaktan etkilenmez
    z2 = _zm(tmp_path / "b", saat, cagri, envanter=envanter, risk=0)
    r = z2.ekle("oku", {**TANIM, "beceri": "servis_durumu"}, {"tur": "tek", "zaman": "2026-11-17T15:00"},
                dondurulmus={"sunucular": ["PB-WEB-01"]})
    z2.tik(dt.datetime(2026, 11, 17, 15, 0))
    assert len(cagri) == 3 and cagri[-1][0] == r["kimlik"]


def test_motor_yasak_pencerede_degisiklik_baslamaz(motor_kur, envanter):
    m, t = motor_kur(erisimli(lambda s, b: (0, "servis=webd\ndurum=active\n", "")))
    m.pencereler = pencereler(Saat(SALI))
    plan = m.plan("servis_yeniden_baslat", {"servis": "webd"}, "PA-WEB-01,PB-WEB-01")
    a = m.yurut(plan, {})
    r = {x["sunucu"]: x for x in a["sonuclar"]}
    assert r["PB-WEB-01"]["durum"] == "iptal" and r["PB-WEB-01"]["yasak"]["pencere"] == "pb-dondurma"
    assert r["PA-WEB-01"]["durum"] == "basarili" and a["durum"] == "kismi"
    assert not any(s == "PB-WEB-01" for s, _ in t.cagrilar)       # yasaktaki sunucuya hiçbir komut gitmedi
    a2 = m.yurut({**m.plan("servis_durumu", {"servis": "webd"}, "PB-WEB-01")}, {})
    assert a2["durum"] == "basarili"                              # salt-okur iş etkilenmez


def test_kalfa_talepten_zamanlar_ve_zamaninda_calisir(motor_kur, tmp_path, posta):
    from filo.zamanli import risk_fn, tanim_yurut
    from filo.kalfa import Kalfa
    m, t = motor_kur(erisimli(lambda s, b: (0, "/|1000|400|40|/\n", "")))
    saat = Saat(SALI)
    m.pencereler = pencereler(saat)
    kosular = []
    z = Zamanlayici(tmp_path / "z.json", saat=saat, pencereler=m.pencereler, envanter_fn=lambda: m.envanter,
                    risk_fn=risk_fn(m),
                    calistirici=lambda zz, an, oo, n, ist=None: kosular.append(
                        tanim_yurut(zz, m, None, oo, n, ist, kayit=kayit(tmp_path, "z", "kalfa"))) or {"is": kosular[-1].kimlik})
    talep = "Her gece 02:00'de PA-APP-01 sunucusunun disk doluluğunu ops@lab.yerel adresine bildir"
    sc = Senaryo(beceri={"secim": "disk_durumu"}, hedef={"ad": "PA-APP-01"}, param={})
    model = FakeModel(islev=sc)
    k = Kalfa(model, m, kayit(tmp_path, talep, "kalfa"), zamanlayici=z).planla(talep)
    assert k.durum == "plan_hazir" and k.plan["zamanlama"]["zamanlama"] == {"tur": "gunluk", "saat": "02:00"}
    assert k.plan["zamanlama"]["sonraki"] == ["2026-11-18T02:00", "2026-11-19T02:00", "2026-11-20T02:00"]
    k = Kalfa(model, m, k, zamanlayici=z).yurut()
    assert k.durum == "zamanlandi" and "her gün 02:00" in k.rapor and not t.cagrilar and not posta
    zis = z.liste()[0]
    assert zis["tanim"]["beceri"] == "disk_durumu" and zis["dondurulmus_liste"] == ["PA-APP-01"]
    cagri_once = model.cagri
    z.tik(dt.datetime(2026, 11, 18, 2, 0))
    assert kosular and kosular[0].durum == "bitti", kosular[0].rapor
    assert model.cagri == cagri_once                              # zamanlanmış koşu model çağırmaz
    assert posta and posta[0]["alici"] == "ops@lab.yerel"


def test_kaptan_yasak_pencerede_erteler(motor_kur, tmp_path):
    from filo.kaptan import Kaptan
    m, t = motor_kur(erisimli(lambda s, b: (0, "servis=webd\ndurum=active\n", "")))
    saat = Saat(SALI)
    m.pencereler = pencereler(saat)
    z = Zamanlayici(tmp_path / "z.json", saat=saat, pencereler=m.pencereler, envanter_fn=lambda: m.envanter)
    talep = "PB-WEB-01'de webd servisini yeniden başlat"
    sc = Senaryo(akis={"adimlar": ["servis_yeniden_baslat"]}, hedef={"ad": "PB-WEB-01"}, param={"servis": "webd"})
    k = Kaptan(FakeModel(islev=sc), m, kayit(tmp_path, talep, "kaptan"), zamanlayici=z, inisiyatif=3,
               akis_dizini=tmp_path / "a").calistir(talep)
    assert k.durum == "ertelendi" and "2026-11-17T18:00" in k.rapor
    assert not any("webd" in b for _, b in t.cagrilar)
    e = z.liste()[0]
    assert e["tanim"]["tur"] == "akis" and e["dondurulmus_liste"] == ["PB-WEB-01"]


def test_kalfa_yasak_pencerede_erteler(motor_kur, tmp_path):
    from filo.kalfa import Kalfa
    m, t = motor_kur()
    saat = Saat(SALI)
    m.pencereler = pencereler(saat)
    z = Zamanlayici(tmp_path / "z.json", saat=saat, pencereler=m.pencereler, envanter_fn=lambda: m.envanter)
    talep = "PB-WEB-01'de webd servisini yeniden başlat"
    sc = Senaryo(beceri={"secim": "servis_yeniden_baslat"}, hedef={"ad": "PB-WEB-01"}, param={"servis": "webd"})
    k = Kalfa(FakeModel(islev=sc), m, kayit(tmp_path, talep, "kalfa"), zamanlayici=z).calistir(talep)
    assert k.durum == "ertelendi" and "2026-11-17T18:00" in k.rapor
    assert not any("webd" in b for _, b in t.cagrilar)
    e = z.liste()[0]
    assert e["zamanlama"] == {"tur": "tek", "zaman": "2026-11-17T18:00"} and e["dondurulmus_liste"] == ["PB-WEB-01"]


def test_pazar_pazartesi_ve_cuma_cumartesi_karismaz():
    """Konsolda görüldü: "her pazar 04:00" → "her Pazartesi 04:00" oluyordu (gün öneki eşleşmesi)."""
    assert zamanlama_dogrula({"tur": "haftalik", "gunler": ["pazar"], "saat": "04:00"})["gunler"] == ["pazar"]
    assert metinden_zamanlama("her pazar 04:00", SALI)[0] == {"tur": "haftalik", "gunler": ["pazar"], "saat": "04:00"}
    assert metinden_zamanlama("her cuma 04:00", SALI)[0]["gunler"] == ["cuma"]
