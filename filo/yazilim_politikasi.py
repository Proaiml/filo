"""Yazılım politikası ve remediation (D2).

sunucu otomasyonu'nın yazılım politikası + remediation'ının genel hâli: politika bir "istenen durum"dur (hangi sunuculara atandığı +
kurulu olacak / olmayacak paketler (isteğe bağlı sürüm), çalışacak / duracak servisler, var olacak / olmayacak
kullanıcılar, kütüphaneden içeriği ve izni belli dosyalar). Sürümlüdür; her değişiklik eski sürümü saklar.

    sapma taraması   politika ile sunucu arasındaki fark, sunucu başına (salt-okur)
    önizleme         remediation'ın kuru çalıştırması: hangi eylem, hangi risk, geri alınabilir mi
    remediation      yalnız farkı kapatır (idempotent: ikinci koşu hiçbir şey yapmaz), aşamalı (test grubu), sonra
                     yeniden tarar; uygulanan her eylem geri alma eylemiyle kayda girer
    geri al          son remediation'ın tersini aynı yoldan yapar

Talepten politika: becerilerin satır içi alanları (paketler_kurulu, paketler_yok, servisler_calisiyor, ...) modelin
parametre olarak doldurduğu dar listelerdir; kod her adın talepte geçtiğini denetler (parametre denetimi), politikayı
sürümlü kaydeder ve hedefi atama olarak yazar. Teslim politikaları (B3) da bu nesneyi kullanır: teslim profili bir
yazılım politikasına bağlanır ve profilin değiştiren adımları politikadan üretilir (`teslim_adimlari`).
"""
from . import durum, duzelt
from .yama import asamali, kaynak_hatasi, sonuc

PAKET_DURUM = ("kurulu", "yok")
SERVIS_DURUM = ("calisiyor", "durmus")
KULLANICI_DURUM = ("var", "yok")
SATIR_ICI = ("paketler_kurulu", "paketler_yok", "servisler_calisiyor", "servisler_durmus", "kullanicilar_var")


def politikalar():
    return (durum.kayit_oku("yazilim_politikalari") or {}).get("politikalar", {})


def politika_dogrula(p, envanter=None):
    h = []
    for x in p.get("paketler", []):
        if x.get("durum", "kurulu") not in PAKET_DURUM or not x.get("ad"):
            h.append(f"paket girdisi geçersiz: {x}")
    for x in p.get("servisler", []):
        if x.get("durum", "calisiyor") not in SERVIS_DURUM or not x.get("ad"):
            h.append(f"servis girdisi geçersiz: {x}")
    for x in p.get("kullanicilar", []):
        if x.get("durum", "var") not in KULLANICI_DURUM or not x.get("ad"):
            h.append(f"kullanıcı girdisi geçersiz: {x}")
    for x in p.get("dosyalar", []):
        try:
            duzelt.dogrula({"tur": "dosya_yaz", **{k: v for k, v in x.items() if k in ("yol", "kaynak", "mod")}})
            duzelt.icerik_ozeti(x)
        except (duzelt.EylemHatasi, OSError) as e:
            h.append(f"dosya girdisi geçersiz: {x}: {e}")
    adlar = [x["ad"] for x in p.get("paketler", [])]
    if len(adlar) != len(set(adlar)):
        h.append("aynı paket iki kez")
    if not any(p.get(k) for k in ("paketler", "servisler", "kullanicilar", "dosyalar")):
        h.append("politika boş: en az bir paket, servis, kullanıcı ya da dosya olmalı")
    if envanter is not None:
        for s in p.get("atamalar", []):
            try:
                envanter.dondur(s)
            except Exception as e:  # noqa: BLE001
                h.append(f"atama seçicisi geçersiz ({s}): {e}")
    return h


def politika_kaydet(ad, p, kim="operatör", envanter=None, neden=""):
    h = politika_dogrula(p, envanter)
    if h:
        raise ValueError("; ".join(h))
    alanlar = ("aciklama", "atamalar", "paketler", "servisler", "kullanicilar", "dosyalar")
    return durum.surumlu_kaydet("yazilim_politikalari", "politikalar", ad, {k: p[k] for k in alanlar if k in p}, kim, neden)


def satir_icinden(p, ad, atama):
    """Becerinin satır içi alanlarından politika nesnesi (talepten politika)."""
    pol = {"aciklama": "talepten kuruldu", "atamalar": [atama] if atama else [],
           "paketler": [{"ad": x, "durum": "kurulu"} for x in p.get("paketler_kurulu") or []]
           + [{"ad": x, "durum": "yok"} for x in p.get("paketler_yok") or []],
           "servisler": [{"ad": x, "durum": "calisiyor"} for x in p.get("servisler_calisiyor") or []]
           + [{"ad": x, "durum": "durmus"} for x in p.get("servisler_durmus") or []],
           "kullanicilar": [{"ad": x, "durum": "var"} for x in p.get("kullanicilar_var") or []], "dosyalar": []}
    return {k: v for k, v in pol.items() if v or k in ("aciklama", "atamalar")}


def _secici_metni(hedef):
    s = (hedef or {}).get("secici")
    if isinstance(s, str):
        return s
    if isinstance(s, dict) and s.get("ad"):
        return s["ad"] if isinstance(s["ad"], str) else ",".join(s["ad"])
    return ",".join((hedef or {}).get("sunucular") or [])


def politika_coz(p, plan, motor):
    """(ad, politika) — `politika` adı verildiyse kayıttan; satır içi alanlar verildiyse yeni sürüm olarak kaydedilir."""
    if any(p.get(k) for k in SATIR_ICI):
        ad = p.get("ad") or ("talep-" + str((plan or {}).get("is_kimligi") or "politika"))
        pol = satir_icinden(p, ad, _secici_metni((plan or {}).get("hedef")))
        if p.get("politika") and p["politika"] in politikalar():
            # var olan politikaya ekleme: aynı adlı girdiler satır içi değerle değişir
            eski = politikalar()[p["politika"]]
            ad = p["politika"]
            for alan in ("paketler", "servisler", "kullanicilar"):
                yeni_adlar = {x["ad"] for x in pol.get(alan, [])}
                pol[alan] = [x for x in eski.get(alan, []) if x["ad"] not in yeni_adlar] + pol.get(alan, [])
            pol["dosyalar"] = eski.get("dosyalar", [])
            pol["atamalar"] = sorted(set(eski.get("atamalar", [])) | set(pol.get("atamalar", [])))
        kayit, _ = politika_kaydet(ad, pol, kim=(plan or {}).get("ajan") or "talep", envanter=motor.envanter,
                                   neden=((plan or {}).get("talep") or "")[:200])
        return ad, kayit
    ad = p.get("politika")
    if not ad or ad not in politikalar():
        raise ValueError(f"yazılım politikası yok: {ad!r} (kayıtlı: {sorted(politikalar())})")
    return ad, politikalar()[ad]


def toplama_istegi(pol):
    return {"paketler": True, "servisler": bool(pol.get("servisler")), "kullanicilar": bool(pol.get("kullanicilar")),
            "dosyalar": [x["yol"] for x in pol.get("dosyalar", [])]}


def sapma(pol, g):
    """Politika ile görüntü arasındaki farklar: [{tur, ad, istenen, mevcut, eylem, risk, geri_alinabilir, aciklama}]."""
    f = []

    def ekle(tur, ad, istenen, mevcut, eylem):
        ga, neden = duzelt.geri_eylem(eylem, g) if eylem else (None, "")
        f.append({"tur": tur, "ad": ad, "istenen": istenen, "mevcut": mevcut, "eylem": eylem,
                  "risk": duzelt.RISK.get(eylem["tur"], 0) if eylem else 0, "geri_alinabilir": ga is not None,
                  "geri_alma_notu": neden, "aciklama": duzelt.aciklama(eylem) if eylem else ""})
    paket = g.get("paketler", {})
    for x in pol.get("paketler", []):
        var = paket.get(x["ad"])
        if x.get("durum", "kurulu") == "kurulu":
            if var is None:
                ekle("paket", x["ad"], "kurulu" + (f" {x['surum']}" if x.get("surum") else ""), "yok",
                     {"tur": "paket_kur", "ad": x["ad"], **({"surum": x["surum"]} if x.get("surum") else {})})
            elif x.get("surum") and not str(var).startswith(str(x["surum"])):
                ekle("paket", x["ad"], f"sürüm {x['surum']}", var, {"tur": "paket_surum", "ad": x["ad"], "surum": x["surum"]})
        elif var is not None:
            ekle("paket", x["ad"], "yok", f"kurulu {var}", {"tur": "paket_kaldir", "ad": x["ad"]})
    servis = g.get("servisler", {})
    for x in pol.get("servisler", []):
        mevcut = servis.get(x["ad"], "tanımsız")
        if x.get("durum", "calisiyor") == "calisiyor" and mevcut != "active":
            ekle("servis", x["ad"], "çalışıyor", mevcut, {"tur": "servis_baslat", "ad": x["ad"]})
        elif x.get("durum") == "durmus" and mevcut == "active":
            ekle("servis", x["ad"], "durmuş", mevcut, {"tur": "servis_durdur", "ad": x["ad"]})
    kul = g.get("kullanicilar", {})
    for x in pol.get("kullanicilar", []):
        if x.get("durum", "var") == "var" and x["ad"] not in kul:
            ekle("kullanici", x["ad"], "var", "yok", {"tur": "kullanici_ac", "ad": x["ad"]})
        elif x.get("durum") == "yok" and x["ad"] in kul:
            ekle("kullanici", x["ad"], "yok", "var", {"tur": "kullanici_sil", "ad": x["ad"]})
    dos = g.get("dosyalar", {})
    for x in pol.get("dosyalar", []):
        d = dos.get(x["yol"]) or {}
        ozet = duzelt.icerik_ozeti(x)
        mod = str(x.get("mod") or "").lstrip("0") or None
        if not d.get("var") or d.get("ozet") != ozet:
            ekle("dosya", x["yol"], f"içerik {x.get('kaynak') or 'tanımlı'} ({ozet[:12]})",
                 "yok" if not d.get("var") else f"farklı içerik ({str(d.get('ozet'))[:12]})",
                 {"tur": "dosya_yaz", "yol": x["yol"], **({"kaynak": x["kaynak"]} if x.get("kaynak") else {"icerik": x.get("icerik", "")}),
                  **({"mod": x["mod"]} if x.get("mod") else {})})
        elif mod and str(d.get("mod") or "").lstrip("0") != mod:
            ekle("dosya", x["yol"], f"izin {x['mod']}", f"izin {d.get('mod')}", {"tur": "izin", "yol": x["yol"], "mod": x["mod"]})
    return f


def _fark_metni(ff):
    return "; ".join(f"{x['tur']} {x['ad']}: {x['mevcut']} → {x['istenen']}" for x in ff) or "-"


def _hedeftekiler(motor, pol, sunucular):
    """Politika atamaları verilmişse yalnız atanmış sunucular değerlendirilir; diğerleri 'atanmamış' raporlanır."""
    if not pol.get("atamalar"):
        return sunucular, []
    atanmis = set()
    for s in pol["atamalar"]:
        try:
            atanmis |= set(motor.envanter.dondur(s)["sunucular"])
        except Exception:  # noqa: BLE001
            continue
    return [s for s in sunucular if s.ad in atanmis], [s for s in sunucular if s.ad not in atanmis]


def isleyici_tara(sunucular, p, kuru=False, durdurma=None, motor=None, plan=None, gozlemci=None):
    try:
        ad, pol = politika_coz(p, plan, motor)
    except ValueError as e:
        return [sonuc(s.ad, "hatali", {}, str(e)) for s in sunucular]
    icerde, disarda = _hedeftekiler(motor, pol, sunucular)
    t = durum.topla(motor, [s.ad for s in icerde], toplama_istegi(pol), (plan or {}).get("is_kimligi"), gozlemci) if icerde else {}
    out = {s.ad: sonuc(s.ad, "basarili", {"uyum": "atanmamis", "sapma": 0, "farklar": "-", "politika": f"{ad} v{pol.get('surum')}"})
           for s in disarda}
    kayit = {}
    for s in icerde:
        x = t[s.ad]
        if not x["goruntu"]:
            out[s.ad] = kaynak_hatasi(s.ad, x["sonuc"])
            continue
        ff = sapma(pol, x["goruntu"])
        kayit[s.ad] = {"zaman": x["goruntu"]["zaman"], "farklar": ff, "politika": ad, "surum": pol.get("surum")}
        out[s.ad] = sonuc(s.ad, "basarili", {"uyum": "uyumlu" if not ff else "sapma", "sapma": len(ff),
                                             "farklar": _fark_metni(ff), "politika": f"{ad} v{pol.get('surum')}"},
                          kaynak=x["sonuc"])
    _sapma_kaydet(ad, kayit)
    return [out[s.ad] for s in sunucular]


def _sapma_kaydet(ad, kayit):
    import json
    if not kayit:
        return
    d = durum.sonuc_yolu("politika")
    d.mkdir(parents=True, exist_ok=True)
    yol = d / "sapma.json"
    try:
        eski = json.loads(yol.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        eski = {}
    eski.setdefault(ad, {}).update(kayit)
    yol.write_text(json.dumps(eski, ensure_ascii=False, indent=1), encoding="utf-8")


def isleyici_uygula(sunucular, p, kuru=False, durdurma=None, motor=None, plan=None, gozlemci=None):
    try:
        ad, pol = politika_coz(p, plan, motor)
    except ValueError as e:
        return [sonuc(s.ad, "hatali", {}, str(e)) for s in sunucular]
    is_k = (plan or {}).get("is_kimligi") or "politika"
    icerde, disarda = _hedeftekiler(motor, pol, sunucular)
    sabit = {s.ad: sonuc(s.ad, "basarili", {"duzeltilen": 0, "kalan": 0, "eylemler": "-",
                                            "not": f"{ad} bu sunucuya atanmamış; dokunulmadı"}) for s in disarda}

    def asama(grup, asama_adi):
        t = durum.topla(motor, [s.ad for s in grup], toplama_istegi(pol), is_k, gozlemci)
        out, plan_e, onceler, ff_ = {}, {}, {}, {}
        for s in grup:
            x = t[s.ad]
            if not x["goruntu"]:
                out[s.ad] = kaynak_hatasi(s.ad, x["sonuc"])
                continue
            ff = sapma(pol, x["goruntu"])
            ff_[s.ad] = ff
            if kuru or not ff:
                out[s.ad] = sonuc(s.ad, "basarili", {
                    "duzeltilen": 0, "kalan": len(ff), "asama": asama_adi,
                    "eylemler": "; ".join(f"{z['aciklama']} [risk {z['risk']}, {'geri alınabilir' if z['geri_alinabilir'] else 'geri alınamaz: ' + z['geri_alma_notu']}]"
                                          for z in ff) or "-",
                    "not": ("önizleme: hiçbir şey değiştirilmedi" if kuru else "sapma yok; yapılacak bir şey yok")},
                    kaynak=x["sonuc"])
                continue
            plan_e[s.ad] = [z["eylem"] for z in ff]
            onceler[s.ad] = x["goruntu"]
        if kuru or not plan_e:
            return out
        uyg = duzelt.uygula(motor, plan_e, is_k, gozlemci, zaman_asimi=600)
        sonra = durum.topla(motor, list(uyg), toplama_istegi(pol), is_k, None)
        for a, u in uyg.items():
            geri = []
            for e in u["eylemler"]:
                if e["durum"] == "basarili":
                    ge, _ = duzelt.geri_eylem({k: v for k, v in e.items() if k not in ("rc", "durum", "hata")}, onceler[a], is_k)
                    if ge:
                        geri.insert(0, ge)
            duzelt.kaydet(is_k, "yazilim_politikasi_uygula", a, u["eylemler"], geri, {"politika": ad, "surum": pol.get("surum")})
            g2 = (sonra.get(a) or {}).get("goruntu")
            kalan = sapma(pol, g2) if g2 else ff_[a]
            satir = {"duzeltilen": sum(1 for e in u["eylemler"] if e["durum"] == "basarili"), "kalan": len(kalan),
                     "asama": asama_adi, "eylemler": "; ".join(f"{duzelt.aciklama(e)}: {e['durum']}" for e in u["eylemler"]),
                     "politika": f"{ad} v{pol.get('surum')}"}
            if kalan:
                out[a] = sonuc(a, "hatali", satir, f"politika sağlanamadı; kalan fark: {_fark_metni(kalan)}"
                               + (f" ({u['sonuc'].get('neden')})" if u["sonuc"].get("neden") else ""), u["sonuc"])
            else:
                out[a] = sonuc(a, "basarili", satir, kaynak=u["sonuc"])
        return out

    sonuclar = asamali(motor, icerde, p.get("test_grubu"), asama) if icerde else []
    tum = {**sabit, **{r["sunucu"]: r for r in sonuclar}}
    return [tum[s.ad] for s in sunucular]


def geri_al_isleyicisi(beceriler, ad_):
    """Son düzeltmeyi (politika remediation'ı ya da uyum düzeltmesi) geri alan işleyici üretir."""
    def isleyici(sunucular, p, kuru=False, durdurma=None, motor=None, plan=None, gozlemci=None):
        is_k = (plan or {}).get("is_kimligi") or "geri"
        out, plan_e, kayit = {}, {}, {}
        for s in sunucular:
            k = duzelt.son_kayit(s.ad, beceriler)
            if not k or not k.get("geri"):
                out[s.ad] = sonuc(s.ad, "basarili", {"geri_alinan": 0, "eylemler": "-", "not": f"geri alınacak {ad_} kaydı yok"})
                continue
            kayit[s.ad], plan_e[s.ad] = k, k["geri"]
        if kuru:
            for a, ee in plan_e.items():
                out[a] = sonuc(a, "basarili", {"geri_alinan": 0, "eylemler": "; ".join(duzelt.aciklama(e) for e in ee)})
            return [out[s.ad] for s in sunucular]
        uyg = duzelt.uygula(motor, plan_e, is_k, gozlemci, zaman_asimi=600)
        for a, u in uyg.items():
            ok = u["sonuc"]["durum"] == "basarili"
            if ok:
                duzelt.geri_alindi_isaretle(kayit[a]["is"], a, is_k)
            out[a] = sonuc(a, "basarili" if ok else "hatali",
                           {"geri_alinan": sum(1 for e in u["eylemler"] if e["durum"] == "basarili"),
                            "eylemler": "; ".join(f"{duzelt.aciklama(e)}: {e['durum']}" for e in u["eylemler"])},
                           "" if ok else f"geri alma tamamlanmadı: {u['sonuc'].get('neden')}", u["sonuc"])
        return [out[s.ad] for s in sunucular]
    return isleyici


def isleyici_tanimla(sunucular, p, kuru=False, durdurma=None, motor=None, plan=None, gozlemci=None):
    """Talepten politika tanımlar (kaydeder ve hedefe atar); sunucuya dokunmaz."""
    try:
        ad, pol = politika_coz(p, plan, motor)
    except ValueError as e:
        return [sonuc(s.ad, "hatali", {}, str(e)) for s in sunucular]
    ozet = (f"paketler: {', '.join(x['ad'] + ':' + x.get('durum', 'kurulu') for x in pol.get('paketler', [])) or '-'}; "
            f"servisler: {', '.join(x['ad'] + ':' + x.get('durum', 'calisiyor') for x in pol.get('servisler', [])) or '-'}; "
            f"kullanıcılar: {', '.join(x['ad'] for x in pol.get('kullanicilar', [])) or '-'}")
    return [sonuc(s.ad, "basarili", {"politika": ad, "surum": pol.get("surum"), "atandi": "evet", "icerik": ozet})
            for s in sunucular]


def teslim_adimlari(pol, on_onayli=()):
    """Teslim profili için politikadan beceri adımları (B3 ile ortak kavram): paketler → paket_kur + paket_dogrula,
    kullanıcılar → kullanici_ac, dosyalar → dosya_dagit, çalışacak servisler → servis_baslat + servis_durumu."""
    a = []
    kur = [x["ad"] for x in pol.get("paketler", []) if x.get("durum", "kurulu") == "kurulu"]
    if kur:
        a.append({"beceri": "paket_kur", "parametre": {"paketler": kur}, "on_onayli": "paket" in on_onayli})
        a.append({"beceri": "paket_dogrula", "parametre": {"paketler": kur}})
    for x in pol.get("kullanicilar", []):
        if x.get("durum", "var") == "var":
            a.append({"beceri": "kullanici_ac", "parametre": {"kullanici": x["ad"], **({"aciklama": x["aciklama"]} if x.get("aciklama") else {})},
                      "on_onayli": "kullanici" in on_onayli})
    for x in pol.get("dosyalar", []):
        if x.get("kaynak"):
            a.append({"beceri": "dosya_dagit", "parametre": {"dosya": x["kaynak"], "hedef": x["yol"], **({"kip": x["mod"]} if x.get("mod") else {})},
                      "on_onayli": "dosya" in on_onayli})
    for x in pol.get("servisler", []):
        if x.get("durum", "calisiyor") == "calisiyor":
            a.append({"beceri": "servis_baslat", "parametre": {"servis": x["ad"]}, "on_onayli": "servis" in on_onayli})
            a.append({"beceri": "servis_durumu", "parametre": {"servis": x["ad"]}})
    for x in a:
        if not x.get("on_onayli"):
            x.pop("on_onayli", None)
    return a


ISLEYICILER = {"yazilim_politikasi_tara": isleyici_tara, "yazilim_politikasi_uygula": isleyici_uygula,
               "yazilim_politikasi_geri_al": geri_al_isleyicisi(["yazilim_politikasi_uygula"], "politika uygulaması"),
               "yazilim_politikasi_tanimla": isleyici_tanimla}
