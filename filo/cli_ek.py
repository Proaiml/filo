"""Komut satırının beceri, iş, onay, talep, bağlantı, web ve bench alt komutları."""
import json
import sys


def _yaz(veri):
    print(json.dumps(veri, ensure_ascii=False, indent=2, default=str))


def _param(liste):
    out = {}
    for x in liste or []:
        if "=" not in x:
            raise SystemExit(f"parametre ad=değer biçiminde olmalı: {x}")
        k, v = x.split("=", 1)
        out[k] = v
    return out


def motor_kur(kip="etkilesimli", kim=None, bench_kurali=None):
    from .beceri import Katalog
    from .envanter import Envanter
    from .motor import BeceriMotoru
    from .politika import Politika
    from .yurutme import Yurutucu
    env = Envanter()
    return BeceriMotoru(Katalog(), env, Yurutucu(env), Politika(kip, bench_kurali=bench_kurali, kim=kim))


# ---------------------------------------------------------------- beceri
def komut_beceri(a):
    from .beceri import Katalog
    k = Katalog()
    tur = "betik" if a.betik else "beceri"
    if a.eylem == "liste":
        if a.betik:
            for b in sorted(p.name for p in k.betik_dizini.iterdir() if (p / "betik.sh").exists()):
                m = k.betik_meta(b)
                print(f"{b:<22} v{m['surum']:<3} {m['aciklama']}")
            return 0
        print(f"{'BECERİ':<26} {'RİSK':<5} {'SÜRÜM':<6} {'TÜR':<7} BAŞLIK")
        for o in k.liste():
            yukseldi = "*" if o["risk"] > o["risk_beyan"] else ""
            print(f"{o['ad']:<26} {o['risk']}{yukseldi:<4} v{o['surum']:<5} {o['tur']:<7} {o['baslik']}")
        if k.hatalar:
            print("\nYüklenemeyen beceriler:", json.dumps(k.hatalar, ensure_ascii=False))
        return 0
    if not a.ad:
        raise SystemExit("beceri adı gerekli")
    if a.eylem == "goster":
        _yaz(k.ozet(a.ad) if not a.betik else {**k.betik_meta(a.ad), "betik": k.betik_oku(a.ad)})
    elif a.eylem == "gecmis":
        for g in k.gecmis(tur, a.ad):
            d = g.get("degisiklik") or {}
            print(f"v{g['surum']:<3} risk {g['risk']}  {'(güncel) ' if g['guncel'] else ''}{d.get('zaman', '')} "
                  f"{d.get('degistiren', '')} {d.get('neden', '')}")
    elif a.eylem == "fark":
        print(k.fark(tur, a.ad, a.s1, a.s2) or "(fark yok)")
    elif a.eylem == "geri-al":
        r = k.geri_don(tur, a.ad, a.s1, degistiren="komut_satiri")
        print(f"{a.ad}: v{a.s1} içeriği v{r['yeni_surum']} olarak yazıldı (risk {r['risk_onceki']} -> {r['risk_yeni']})")
    elif a.eylem == "sinifla":
        t = k[a.ad]
        print(json.dumps({"beyan": t["risk"], "etkin": k.etkin_risk(t)}, ensure_ascii=False))
    return 0


# ---------------------------------------------------------------- iş (beceriyi doğrudan yürütme)
def komut_is(a):
    from . import rapor
    from .yurutme import ozetle
    motor = motor_kur("komut_satiri" if a.onayla else "etkilesimli")
    p = _param(a.param)
    plan = motor.plan(a.beceri, p, a.hedef, talep=a.aciklama or f"komut satırı: {a.beceri}", ajan="operatör",
                      kimlik=a.kimlik)
    print(f"plan: {plan['beceri']} v{plan['surum']}  risk {plan['risk']} ({plan['risk_neden']})  "
          f"onay {'gerekli' if plan['onay_gerekli'] else 'gerekmez'}")
    if plan["hedef"]:
        print(f"hedef (donduruldu): {', '.join(plan['hedef']['sunucular'])}")
    if a.kuru:
        for r in motor.kuru_calistir(plan):
            print(f"--- {r['sunucu']} [{r['durum']}]\n{(r['stdout'] or r.get('neden') or r['stderr']).strip()}")
        return 0
    baglam = {"adimlar": []}
    adim = motor.yurut(plan, baglam)
    baglam["adimlar"].append(adim)
    _adim_yaz(adim)
    if adim["durum"] in ("onay_bekliyor", "reddedildi"):
        if adim["durum"] == "onay_bekliyor":
            print(f"onay bekleniyor: python -m filo onay ver {adim['onay']['kimlik']}  (ya da web arayüzünde Onaylar)")
        return 3
    is_k = plan["is_kimligi"]
    if a.bicim:
        d = motor.yurut(motor.plan("sonucu_donustur", {"bicim": a.bicim}, None, plan["talep"], "operatör", is_k), baglam)
        baglam["adimlar"].append(d)
        _adim_yaz(d)
        if a.cikti_dosyasi and d.get("belge"):
            open(a.cikti_dosyasi, "w", encoding="utf-8").write(d["belge"]["icerik"])
            print(f"belge yazıldı: {a.cikti_dosyasi}")
    if a.eposta:
        e = motor.yurut(motor.plan("eposta_gonder", {"alici": a.eposta, "konu": a.konu or f"Filo: {a.beceri}"}, None,
                                   plan["talep"], "operatör", is_k), baglam)
        baglam["adimlar"].append(e)
        _adim_yaz(e)
    print("\nÖzet:\n" + rapor.ozet_metni(baglam["adimlar"]))
    oz = ozetle(adim.get("sonuclar", []))
    return 0 if all(x["durum"] == "basarili" for x in baglam["adimlar"]) and not oz.get("kismi") else 1


def _adim_yaz(adim):
    from .__main__ import _tablo
    print(f"\n== {adim['beceri']} v{adim['surum']}: {adim['durum']}" + (f" - {adim['aciklama']}" if adim.get("aciklama") else ""))
    if adim.get("sonuclar"):
        _tablo([{**r, "stdout": r.get("sema_hatasi") or json.dumps(r.get("veri"), ensure_ascii=False)
                 if r.get("veri") not in (None, "") else r.get("stdout")} for r in adim["sonuclar"]])


# ---------------------------------------------------------------- onay
def komut_onay(a):
    from .politika import Onaylar
    o = Onaylar()
    if a.eylem == "liste":
        for k in o.liste("bekliyor" if not a.hepsi else None):
            print(f"{k['kimlik']}  {k['durum']:<10} {k['beceri']} v{k['surum']} risk {k['risk']}  hedef: {', '.join(k['hedefler'])}")
        return 0
    import getpass
    k = o.karar(a.kimlik, a.eylem == "ver", f"komut_satiri:{getpass.getuser()}", a.not_ or "")
    print("bulunamadı" if k is None else f"{k['kimlik']}: {k['durum']}")
    return 0 if k else 1


def ekle(alt):
    x = alt.add_parser("beceri", help="beceri kataloğu ve sürümleri")
    x.add_argument("eylem", choices=["liste", "goster", "gecmis", "fark", "geri-al", "sinifla"])
    x.add_argument("ad", nargs="?")
    x.add_argument("s1", nargs="?", type=int)
    x.add_argument("s2", nargs="?", type=int)
    x.add_argument("--betik", action="store_true", help="beceri yerine betik kütüphanesi kaydı")
    x.set_defaults(f=komut_beceri)

    x = alt.add_parser("is", help="bir beceriyi hedeflerde yürüt (isteğe bağlı dönüştür + e-posta)")
    x.add_argument("--beceri", required=True)
    x.add_argument("--hedef")
    x.add_argument("--param", action="append", help="ad=değer (birden çok kez)")
    x.add_argument("--kuru", action="store_true", help="yalnız kuru çalıştırma")
    x.add_argument("--onayla", action="store_true", help="düzey 3+ için operatör onayını şimdi ver")
    x.add_argument("--bicim", choices=["csv", "xml", "json", "html"])
    x.add_argument("--cikti-dosyasi")
    x.add_argument("--eposta")
    x.add_argument("--konu")
    x.add_argument("--aciklama")
    x.add_argument("--kimlik", help="çalıştırma kimliği: baglanti (varsayılan), root ya da kullanıcı adı")
    x.set_defaults(f=komut_is)

    x = alt.add_parser("onay", help="bekleyen onaylar")
    x.add_argument("eylem", choices=["liste", "ver", "reddet"])
    x.add_argument("kimlik", nargs="?")
    x.add_argument("--hepsi", action="store_true")
    x.add_argument("--not", dest="not_")
    x.set_defaults(f=komut_onay)

    try:
        from . import cli_ajan
        cli_ajan.ekle(alt)
    except ImportError:
        pass
    return alt


if __name__ == "__main__":
    sys.exit(0)
