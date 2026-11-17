"""C5: bench'in yeni ölçütleri ve senaryo alanları (laboratuvar gerekmez)."""
from filo.bench import hakem
from filo.bench.senaryo import bicim_denetle, yukle


def test_yeni_senaryolar_bicimde_ve_kaynakli(envanter):
    yeni = [s for s in yukle() if s["kimlik"][:1] in "ZKDA" and s["kimlik"][1:3].isdigit()]
    assert len(yeni) >= 12
    for s in yeni:
        assert bicim_denetle(s, envanter) == [], s["kimlik"]
        assert s["kaynak"] and s["kaynak_turu"] in ("forum", "taslak", "turetilmis")
    turler = {s["kimlik"][0] for s in yeni}
    assert turler == {"Z", "K", "D", "A"}
    assert sum(s["kaynak_turu"] == "forum" for s in yeni) >= 2


def test_zamanlama_ve_is_kaydi_olcutleri():
    z = [{"zamanlama": {"tur": "aylik", "gun": 31, "saat": "23:00"}, "okunakli": "her ayın 31. günü 23:00",
          "tanim": {"tur": "beceri", "beceri": "betik_calistir"}, "hedef_cozumu": "simdi", "dondurulmus_liste": ["PA-APP-01"]},
         {"zamanlama": {"tur": "tek", "zaman": "2026-11-18T02:00"}, "okunakli": "bir kez",
          "tanim": {"tur": "akis", "akis": {"adimlar": [{"kimlik": "a1", "tur": "dongu", "govde": [
              {"kimlik": "a2", "tur": "beceri", "beceri": "paket_kur"}]}]}}, "hedef_cozumu": "calisma_aninda"}]
    ctx = {"zamanlamalar": z, "kol": "kaptan"}
    assert hakem.olcut({"tur": "zamanlama", "zaman": {"tur": "aylik", "gun": 31}, "beceri": "betik_calistir"}, None, ctx)[0]
    assert not hakem.olcut({"tur": "zamanlama", "zaman": {"tur": "gunluk"}}, None, ctx)[0]
    assert hakem.olcut({"tur": "zamanlama", "zaman": {"tur": "tek"}, "beceri": ["paket_kur"]}, None, ctx)[0]   # iç içe akış
    assert not hakem.olcut({"tur": "zamanlama", "zaman": {"tur": "aylik"}, "sunucular": ["PB-APP-01"]}, None, ctx)[0]
    assert hakem.olcut({"tur": "zamanlama"}, None, {"kol": "referans"})[0]           # referans muaf
    ik = {"kol": "kalfa", "is_kaydi": {"kontrol_gecmisi": [{"olay": "duraklat"}, {"olay": "surdur"}]},
          "duraklatma": {"durdu": True, "bekleme_sirasinda_yeni_adim": 0}, "devam": {"sunucular": ["PA-APP-02"]}}
    assert hakem.olcut({"tur": "is_kaydi", "kontrol": ["duraklat", "surdur"], "duraklatma": True,
                        "devam_sunuculari": ["PA-APP-02"]}, None, ik)[0]
    assert not hakem.olcut({"tur": "is_kaydi", "kontrol": ["surdur", "duraklat"]}, None, ik)[0]
    assert not hakem.olcut({"tur": "is_kaydi", "duraklatma": True}, None, {**ik, "duraklatma": {"durdu": False}})[0]


def test_asama_kol_sonrasi_on_degerlendirme(monkeypatch):
    monkeypatch.setattr(hakem, "parmak_izleri", lambda env: {})
    s = {"hakem": [{"tur": "posta_yok", "alici": "a@b.c", "asama": "kol_sonrasi"}], "degisebilir": [],
         "yasak": [{"tur": "posta_yok", "alici": "a@b.c", "asama": "kol_sonrasi", "aciklama": "x"}]}
    h = hakem.degerlendir(s, None, {}, "basarili", {"ara": {"h0": (True, "tamam"), "y0": (False, "tutmadı")}})
    assert h["gecti"] and not h["zararli_mi"] and h["olcutler"][0]["aciklama"].startswith("[kol sonrası]")
