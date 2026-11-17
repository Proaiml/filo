"""Adımdan devam (akış otomasyonu'daki rerun point'in kolay hâli) ve yarıda kalan işi sürdürme.

Her tamamlanan üst düzey adım kendiliğinden bir devam noktasıdır. Bir işin kaydından (results/isler/<kimlik>.json,
`devam` alanı) devam noktaları çıkarılır; seçilen noktadan:
    kapsam "basarisiz"  yalnız o adımda ya da sonrasında başarısız olan sunucular
    kapsam "hepsi"      o adıma giren bütün sunucular
ile yeni bir koşu kurulur. Önceki adımların sonuçları (koşullar ve dönüştürme/e-posta için) kayıttan gelir; önceki
adımlar yeniden çalışmaz. Yapılı akışta bileşik düğüm (dal, döngü, paralel) bütünüyle tek adımdır.
"""
import copy


def _kes(baglam, uzunluk):
    b = copy.deepcopy(baglam or {"adimlar": []})
    adimlar = b.get("adimlar", [])[:uzunluk] if uzunluk is not None else b.get("adimlar", [])
    out = {"adimlar": adimlar}
    uzak = [a for a in adimlar if a.get("beceri") not in ("sonucu_donustur", "eposta_gonder") and a.get("sonuclar")]
    if uzak:
        out["son_uzak_adim"] = uzak[-1]
    if adimlar:
        out["son_adim"] = adimlar[-1]
    belge = [a.get("belge") for a in adimlar if a.get("belge")]
    if belge:
        out["belge"] = belge[-1]
    return out


def _kaptan_akisi(d):
    from .akis_motoru import BICIM, duz_akis
    akis = (d.get("plan") or {}).get("akis") or {}
    if akis.get("bicim") == BICIM:
        return akis
    return duz_akis(akis.get("adimlar", []))


def devam_noktalari(d):
    """İşin devam noktaları: [{"adim", "ad", "durum", "sunucular", "basarisiz"}]."""
    dv = d.get("devam") or {}
    if dv.get("tur") == "kalfa":
        plan = d.get("plan") or {}
        adlar = plan.get("adimlar") or []
        giren = (dv.get("adim_girisi") or {}).get("0") or ((plan.get("ana") or {}).get("hedef") or {}).get("sunucular") or []
        ana = next((a for a in (dv.get("baglam") or {}).get("adimlar", []) if a.get("beceri") == adlar[0]), None) if adlar else None
        basarisiz = [r["sunucu"] for r in (ana or {}).get("sonuclar", []) if r["durum"] != "basarili" and not r.get("yasak")]
        sonraki = dv.get("sonraki", 0)
        out = [{"adim": 0, "ad": adlar[0] if adlar else "?", "durum": "tamam" if sonraki > 0 else "yapilmadi",
                "sunucular": giren, "basarisiz": basarisiz if sonraki > 0 else giren}]
        for i, ad in enumerate(adlar[1:], 1):
            out.append({"adim": i, "ad": ad, "durum": "tamam" if sonraki > i else "yapilmadi", "sunucular": [],
                        "basarisiz": []})
        return out
    if dv.get("tur") == "kaptan":
        st = dv.get("akis_durumu") or {}
        akis = _kaptan_akisi(d)
        from .akis_motoru import _dugum_metni
        out = []
        for i, dugum in enumerate(akis.get("adimlar", [])):
            giren = (st.get("adim_girisi") or {}).get(str(i)) or (st.get("adim_girisi") or {}).get(i) or []
            basarisiz = [s for s, v in (st.get("devredilen") or {}).items()
                         if s != "(yerel)" and int(v.get("ust", 0)) >= i and s in giren]
            ust = st.get("ust", 0)
            bitti = d.get("durum") in ("bitti", "kismi", "devredildi", "basarisiz") and not st.get("durma")
            out.append({"adim": i, "ad": _dugum_metni(dugum), "kimlik": dugum.get("kimlik"),
                        "durum": "tamam" if (i < ust or (i == ust and bitti)) else ("yarida" if i == ust else "yapilmadi"),
                        "sunucular": giren, "basarisiz": basarisiz})
        return out
    return []


def devam_hazirla(d, adim, kapsam="basarisiz"):
    """(baslangic, sunucular, onceki) — seçilen devam noktasından yeni koşu için."""
    if kapsam not in ("basarisiz", "hepsi"):
        raise ValueError("kapsam basarisiz ya da hepsi olmalı")
    dv = d.get("devam") or {}
    noktalar = devam_noktalari(d)
    if not noktalar:
        raise ValueError("bu işin devam bilgisi yok (üçüncü turdan önceki iş ya da hiç yürütülmemiş)")
    if not 0 <= int(adim) < len(noktalar):
        raise ValueError(f"geçersiz adım: {adim} (0-{len(noktalar) - 1})")
    adim = int(adim)
    n = noktalar[adim]
    uzunluk = (dv.get("baglam_uzunlugu") or {}).get(str(adim))
    if dv.get("tur") == "kalfa":
        if adim == 0:
            sunucular = n["sunucular"] if kapsam == "hepsi" else n["basarisiz"]
            if not sunucular:
                raise ValueError("bu adımda başarısız sunucu yok; 'hepsi' kapsamını seçin")
            return 0, sunucular, {"baglam": {"adimlar": []}, "baglam_uzunlugu": {}}
        if uzunluk is None:
            raise ValueError("bu adıma hiç gelinmemiş; önceki adımdan devam edin")
        return adim, None, {"baglam": _kes(dv.get("baglam"), uzunluk), "baglam_uzunlugu": {}}
    st = copy.deepcopy(dv.get("akis_durumu") or {})
    sunucular = n["sunucular"] if kapsam == "hepsi" else n["basarisiz"]
    if not sunucular:
        raise ValueError("bu adımda başarısız sunucu yok; 'hepsi' kapsamını seçin" if kapsam == "basarisiz"
                         else "bu adıma giren sunucu yok")
    st["devredilen"] = {s: v for s, v in (st.get("devredilen") or {}).items() if int(v.get("ust", 0)) < adim}
    st["durma"], st["bitis"] = None, None
    return adim, sunucular, {"akis_durumu": st, "baglam": _kes(dv.get("baglam"), uzunluk),
                             "baglam_uzunlugu": {k: v for k, v in (dv.get("baglam_uzunlugu") or {}).items()
                                                 if int(k) <= adim}, "yapilan": []}


def surdurme_hazirla(d):
    """Konsol yeniden başladıktan sonra yarıda kalmış/duraklatılmış işi kaldığı adımdan sürdürmek için."""
    dv = d.get("devam") or {}
    if dv.get("tur") == "kalfa":
        s = int(dv.get("sonraki", 0))
        if s == 0:
            giren = (dv.get("adim_girisi") or {}).get("0") or []
            return 0, giren, {"baglam": {"adimlar": []}}
        return s, None, {"baglam": _kes(dv.get("baglam"), (dv.get("baglam_uzunlugu") or {}).get(str(s))),
                         "baglam_uzunlugu": dv.get("baglam_uzunlugu")}
    if dv.get("tur") == "kaptan":
        st = copy.deepcopy(dv.get("akis_durumu") or {})
        ust = int(st.get("ust", 0))
        giren = (st.get("adim_girisi") or {}).get(str(ust)) or []
        st["devredilen"] = {s: v for s, v in (st.get("devredilen") or {}).items() if int(v.get("ust", 0)) < ust}
        st["durma"], st["bitis"] = None, None
        return ust, giren, {"akis_durumu": st, "baglam": _kes(dv.get("baglam"),
                                                              (dv.get("baglam_uzunlugu") or {}).get(str(ust))),
                            "baglam_uzunlugu": dv.get("baglam_uzunlugu"), "yapilan": dv.get("yapilan") or []}
    raise ValueError("bu işin sürdürme bilgisi yok")
