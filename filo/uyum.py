"""Uyum denetimi ve anlık görüntü (D3).

sunucu otomasyonu'nın audit/compliance ve snapshot özelliklerinin genel hâli:
    kural        tek bir beklenti: dosya (var/yok, izin üst sınırı, sahip, içerik deseni olmalı/olmamalı), paket (kurulu/
                 yok, en az sürüm), servis durumu, kullanıcı/grup var/yok, sysctl değeri, port açık/kapalı, komut çıktısı
                 (komut salt-okur izin listesinden geçmek zorunda). İsteğe bağlı düzeltme eylemi (`duzelt` eylemi) —
                 geri alınabilir olup olmadığını kod söyler.
    kural seti   adlı kural listesi (ör. "temel-sertlestirme"), sürümlü (`ayarlar/uyum_kurallari.json`)
    istisna      kural + sunucu seçici + gerekçe + bitiş tarihi; süresi dolan istisna uygulanmaz ve raporda görünür
    denetim      sunucu başına uyum puanı (geçen / uygulanabilir), ihlal listesi, istisnalar; sonuç kayda girer
    düzeltme     ihlallerin düzeltme eylemleri (isteğe bağlı yalnız geri alınabilenler) D2 ile aynı yoldan (`duzelt`)
Anlık görüntü: sunucunun paketleri, servisleri, kullanıcıları, açık portları, seçili dosyaların özetleri ve sysctl
değerleri kaydedilir; iki sunucu (altın sunucu karşılaştırması) ya da bir sunucunun iki zamanı karşılaştırılır.
"""
import datetime
import json
import re

from . import durum, duzelt
from .erisim import salt_okur_denetle
from .yama import kaynak_hatasi, sonuc

def uyum_sonuc():
    return durum.sonuc_yolu("uyum")
KURAL_TURLERI = ("dosya", "paket", "servis", "kullanici", "grup", "sysctl", "port", "komut")
GORUNTU_DOSYALARI = ["/etc/passwd", "/etc/group", "/etc/sudoers.d/filo", "/etc/ssh/sshd_config", "/etc/motd",
                     "/etc/uygulama/uygulama.conf", "/opt/uygulama/surum.txt", "/etc/login.defs", "/etc/issue.net"]
GORUNTU_SYSCTL = ["kernel.randomize_va_space", "net.ipv4.ip_forward", "net.ipv4.conf.all.accept_redirects"]


def kayit():
    return durum.kayit_oku("kural_setleri") or {}


def kural_setleri():
    return kayit().get("kural_setleri", {})


def istisnalar():
    return kayit().get("istisnalar", [])


def kural_dogrula(k):
    h = []
    if not re.match(r"^[a-z0-9-]{2,40}$", str(k.get("kimlik", ""))):
        h.append(f"kural kimliği geçersiz: {k.get('kimlik')}")
    if k.get("tur") not in KURAL_TURLERI:
        h.append(f"{k.get('kimlik')}: tür {KURAL_TURLERI} olmalı")
    if k.get("tur") == "komut":
        neden = salt_okur_denetle(str(k.get("komut", "")))
        if neden:
            h.append(f"{k.get('kimlik')}: komut salt-okur izin listesine uymuyor: {neden}")
    if k.get("duzeltme"):
        try:
            duzelt.dogrula(dict(k["duzeltme"]))
        except duzelt.EylemHatasi as e:
            h.append(f"{k.get('kimlik')}: düzeltme geçersiz: {e}")
    return h


def kural_seti_kaydet(ad, kurallar, aciklama="", kim="operatör"):
    h = [x for k in kurallar for x in kural_dogrula(k)]
    if len({k["kimlik"] for k in kurallar}) != len(kurallar):
        h.append("aynı kural kimliği iki kez")
    if h:
        raise ValueError("; ".join(h))
    return durum.surumlu_kaydet("kural_setleri", "kural_setleri", ad, {"aciklama": aciklama, "kurallar": kurallar}, kim)


def istisna_ekle(kural_seti, kural, sunucu, gerekce, bitis=None, kim="operatör"):
    if not str(gerekce).strip():
        raise ValueError("istisna gerekçe ister")
    if bitis:
        datetime.date.fromisoformat(str(bitis)[:10])
    v = kayit()
    v.setdefault("istisnalar", []).append({"kural_seti": kural_seti, "kural": kural, "sunucu": sunucu, "gerekce": gerekce,
                                           "bitis": bitis, "ekleyen": kim, "zaman": datetime.datetime.now().isoformat(timespec="seconds")})
    durum.kayit_yaz("kural_setleri", v)
    return v["istisnalar"][-1]


def toplama_istegi(kurallar):
    i = {"paketler": any(k["tur"] == "paket" for k in kurallar), "servisler": any(k["tur"] == "servis" for k in kurallar),
         "kullanicilar": any(k["tur"] in ("kullanici", "grup") for k in kurallar),
         "portlar": any(k["tur"] == "port" for k in kurallar),
         "dosyalar": sorted({k["yol"] for k in kurallar if k["tur"] == "dosya"}),
         "icerik": {k["kimlik"]: (k["yol"], k.get("icerir") or k.get("icermez")) for k in kurallar
                    if k["tur"] == "dosya" and (k.get("icerir") or k.get("icermez"))},
         "sysctl": sorted({k["anahtar"] for k in kurallar if k["tur"] == "sysctl"}),
         "komutlar": {k["kimlik"]: k["komut"] for k in kurallar if k["tur"] == "komut"}}
    return i


def _surum_buyuk_esit(a, b):
    def parca(x):
        return [int(p) if p.isdigit() else p for p in re.split(r"[.\-+~r]", str(x)) if p != ""]
    try:
        return parca(a) >= parca(b)
    except TypeError:
        return str(a) >= str(b)


def degerlendir(k, g):
    """(sonuç: gecti|ihlal|uygulanamaz, açıklama)."""
    t = k["tur"]
    if k.get("aileler") and g.get("aile") not in k["aileler"]:
        return "uygulanamaz", f"yalnız {k['aileler']}"
    if t == "dosya":
        d = (g.get("dosyalar") or {}).get(k["yol"]) or {}
        if not d.get("var"):
            if k.get("var") is False:
                return "gecti", "dosya yok"
            return ("uygulanamaz", "dosya yok") if k.get("yoksa") == "uygulanamaz" else ("ihlal", "dosya yok")
        if k.get("var") is False:
            return "ihlal", "dosya var (olmamalı)"
        if k.get("mod_en_cok") and int(str(d.get("mod") or "0"), 8) & ~int(str(k["mod_en_cok"]), 8):
            return "ihlal", f"izin {d.get('mod')} (en çok {k['mod_en_cok']})"
        if k.get("sahip") and d.get("sahip") != k["sahip"]:
            return "ihlal", f"sahip {d.get('sahip')} (beklenen {k['sahip']})"
        if k.get("icerir") or k.get("icermez"):
            v = (g.get("icerik") or {}).get(k["kimlik"])
            if v == "yok":
                return "ihlal", "dosya okunamadı"
            if k.get("icerir") and v != "1":
                return "ihlal", f"'{k['icerir']}' deseni yok"
            if k.get("icermez") and v == "1":
                return "ihlal", f"'{k['icermez']}' deseni var (olmamalı)"
        return "gecti", f"izin {d.get('mod')}"
    if t == "paket":
        v = (g.get("paketler") or {}).get(k["ad"])
        if k.get("kurulu", True) is False:
            return ("ihlal", f"kurulu ({v})") if v else ("gecti", "kurulu değil")
        if not v:
            return "ihlal", "kurulu değil"
        if k.get("surum_en_az") and not _surum_buyuk_esit(v, k["surum_en_az"]):
            return "ihlal", f"sürüm {v} (en az {k['surum_en_az']})"
        return "gecti", f"sürüm {v}"
    if t == "servis":
        v = (g.get("servisler") or {}).get(k["ad"], "tanımsız")
        return ("gecti" if v == k.get("durum", "active") else "ihlal"), f"durum {v}"
    if t == "kullanici":
        var = k["ad"] in (g.get("kullanicilar") or {})
        return ("gecti" if var == k.get("var", True) else "ihlal"), ("hesap var" if var else "hesap yok")
    if t == "grup":
        uyeler = (g.get("gruplar") or {}).get(k["ad"])
        if uyeler is None:
            return ("gecti", "grup yok") if k.get("var") is False else ("ihlal", "grup yok")
        fazla = [u for u in uyeler if u in (k.get("uyeler_yok") or [])]
        return ("ihlal", f"istenmeyen üyeler: {fazla}") if fazla else ("gecti", f"üyeler: {uyeler}")
    if t == "sysctl":
        v = (g.get("sysctl") or {}).get(k["anahtar"])
        if v in (None, ""):
            return "uygulanamaz", "okunamadı"
        return ("gecti" if v == str(k["deger"]) else "ihlal"), f"{k['anahtar']}={v}"
    if t == "port":
        acik = k["port"] in (g.get("portlar") or [])
        return ("gecti" if acik == k.get("acik", False) else "ihlal"), ("açık" if acik else "kapalı")
    if t == "komut":
        c = (g.get("komutlar") or {}).get(k["kimlik"]) or {}
        cikti = (c.get("cikti") or "").strip()
        if k.get("rc") is not None and c.get("rc") != k["rc"]:
            return "ihlal", f"çıkış kodu {c.get('rc')}"
        if k.get("beklenen") and not re.search(k["beklenen"], cikti):
            return "ihlal", f"çıktı beklenene uymuyor: {cikti[:80]!r}"
        return "gecti", cikti[:80]
    return "uygulanamaz", "bilinmeyen tür"


def _istisna(set_adi, kural, sunucu, env, bugun):
    for x in istisnalar():
        if x.get("kural_seti") not in (None, set_adi) or x.get("kural") != kural:
            continue
        try:
            kapsam = env.dondur(x["sunucu"])["sunucular"]
        except Exception:  # noqa: BLE001
            continue
        if sunucu in kapsam:
            gecerli = not x.get("bitis") or str(x["bitis"])[:10] >= bugun.isoformat()
            return x, gecerli
    return None, False


def denetle_goruntu(set_adi, kurallar, sunucu, g, env, bugun=None):
    bugun = bugun or datetime.date.today()
    satirlar = []
    for k in kurallar:
        s, a = degerlendir(k, g)
        ist, gecerli = _istisna(set_adi, k["kimlik"], sunucu, env, bugun) if s == "ihlal" else (None, False)
        if ist and gecerli:
            s, a = "istisna", f"{a} — istisna: {ist['gerekce']} (bitiş {ist.get('bitis') or 'yok'})"
        elif ist:
            a += f" — istisnanın süresi doldu ({ist.get('bitis')})"
        geri = None
        if k.get("duzeltme"):
            ge, notu = duzelt.geri_eylem(dict(k["duzeltme"]), g)
            geri = ge is not None
        satirlar.append({"kural": k["kimlik"], "baslik": k.get("baslik", k["kimlik"]), "onem": k.get("onem", "orta"),
                         "sonuc": s, "aciklama": a, "duzeltilebilir": bool(k.get("duzeltme")), "geri_alinabilir": geri,
                         "oneri": k.get("oneri") or (duzelt.aciklama(k["duzeltme"]) if k.get("duzeltme") else "")})
    uyg = [x for x in satirlar if x["sonuc"] in ("gecti", "ihlal")]
    gecen = sum(1 for x in uyg if x["sonuc"] == "gecti")
    puan = round(100 * gecen / len(uyg)) if uyg else 100
    return {"sunucu": sunucu, "zaman": g.get("zaman"), "puan": puan, "gecen": gecen,
            "ihlal": sum(1 for x in satirlar if x["sonuc"] == "ihlal"),
            "istisna": sum(1 for x in satirlar if x["sonuc"] == "istisna"),
            "uygulanamaz": sum(1 for x in satirlar if x["sonuc"] == "uygulanamaz"), "kurallar": satirlar}


def _kosu_kaydet(set_adi, surum, sonuclar):
    UYUM_SONUC = uyum_sonuc()
    UYUM_SONUC.mkdir(parents=True, exist_ok=True)
    zaman = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    v = {"kural_seti": set_adi, "surum": surum, "zaman": datetime.datetime.now().isoformat(timespec="seconds"),
         "sunucular": sonuclar}
    (UYUM_SONUC / f"{zaman}-{set_adi}.json").write_text(json.dumps(v, ensure_ascii=False, indent=1), encoding="utf-8")
    yol = UYUM_SONUC / "son.json"
    try:
        son = json.loads(yol.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        son = {}
    son.setdefault(set_adi, {}).update(sonuclar)
    yol.write_text(json.dumps(son, ensure_ascii=False, indent=1), encoding="utf-8")


def _ihlal_metni(d):
    return "; ".join(f"{x['kural']} ({x['aciklama']})" for x in d["kurallar"] if x["sonuc"] == "ihlal") or "-"


def isleyici_denetle(sunucular, p, kuru=False, durdurma=None, motor=None, plan=None, gozlemci=None):
    ks = kural_setleri().get(p["kural_seti"])
    if not ks:
        return [sonuc(s.ad, "hatali", {}, f"kural seti yok: {p['kural_seti']}") for s in sunucular]
    t = durum.topla(motor, [s.ad for s in sunucular], toplama_istegi(ks["kurallar"]), (plan or {}).get("is_kimligi"), gozlemci)
    out, kayit_ = [], {}
    for s in sunucular:
        x = t[s.ad]
        if not x["goruntu"]:
            out.append(kaynak_hatasi(s.ad, x["sonuc"]))
            continue
        d = denetle_goruntu(p["kural_seti"], ks["kurallar"], s.ad, x["goruntu"], motor.envanter)
        kayit_[s.ad] = d
        out.append(sonuc(s.ad, "basarili", {"puan": d["puan"], "gecen": d["gecen"], "ihlal": d["ihlal"],
                                            "istisna": d["istisna"], "ihlaller": _ihlal_metni(d)}, kaynak=x["sonuc"]))
    if kayit_:
        _kosu_kaydet(p["kural_seti"], ks.get("surum"), kayit_)
    return out


def isleyici_duzelt(sunucular, p, kuru=False, durdurma=None, motor=None, plan=None, gozlemci=None):
    """İhlallerin düzeltme eylemlerini uygular; `yalniz_geri_alinabilir` ise geri alınamayanlar yalnız raporlanır."""
    ks = kural_setleri().get(p["kural_seti"])
    if not ks:
        return [sonuc(s.ad, "hatali", {}, f"kural seti yok: {p['kural_seti']}") for s in sunucular]
    is_k = (plan or {}).get("is_kimligi") or "uyum"
    secili = set(p.get("kurallar") or [])
    kurallar = ks["kurallar"]
    t = durum.topla(motor, [s.ad for s in sunucular], toplama_istegi(kurallar), is_k, gozlemci)
    out, plan_e, bilgi = {}, {}, {}
    for s in sunucular:
        x = t[s.ad]
        if not x["goruntu"]:
            out[s.ad] = kaynak_hatasi(s.ad, x["sonuc"])
            continue
        d = denetle_goruntu(p["kural_seti"], kurallar, s.ad, x["goruntu"], motor.envanter)
        yap, birak = [], []
        for r in d["kurallar"]:
            if r["sonuc"] != "ihlal" or (secili and r["kural"] not in secili):
                continue
            k = next(k for k in kurallar if k["kimlik"] == r["kural"])
            if not k.get("duzeltme"):
                birak.append(f"{r['kural']}: düzeltme tanımı yok ({r['oneri'] or 'elle'})")
            elif p.get("yalniz_geri_alinabilir", True) and not r["geri_alinabilir"]:
                birak.append(f"{r['kural']}: geri alınamaz ({duzelt.GERI_ALINAMAZ.get(k['duzeltme']['tur'], '')}); yapılmadı")
            else:
                yap.append((r["kural"], dict(k["duzeltme"])))
        bilgi[s.ad] = (d, yap, birak, x)
        if kuru or not yap:
            out[s.ad] = sonuc(s.ad, "basarili", {"duzeltilen": 0, "kalan_ihlal": d["ihlal"],
                                                 "yapilacak": "; ".join(f"{a}: {duzelt.aciklama(e)}" for a, e in yap) or "-",
                                                 "birakilan": "; ".join(birak) or "-",
                                                 "not": "önizleme; hiçbir şey değişmedi" if kuru else "düzeltilecek ihlal yok"},
                              kaynak=x["sonuc"])
            continue
        plan_e[s.ad] = [e for _, e in yap]
    if kuru or not plan_e:
        return [out[s.ad] for s in sunucular]
    uyg = duzelt.uygula(motor, plan_e, is_k, gozlemci, zaman_asimi=300)
    sonra = durum.topla(motor, list(uyg), toplama_istegi(kurallar), is_k, None)
    for a, u in uyg.items():
        d, yap, birak, x = bilgi[a]
        geri = []
        for e in u["eylemler"]:
            if e["durum"] == "basarili":
                ge, _ = duzelt.geri_eylem({k: v for k, v in e.items() if k not in ("rc", "durum", "hata")}, x["goruntu"], is_k)
                if ge:
                    geri.insert(0, ge)
        duzelt.kaydet(is_k, "uyum_duzelt", a, u["eylemler"], geri, {"kural_seti": p["kural_seti"]})
        g2 = (sonra.get(a) or {}).get("goruntu")
        d2 = denetle_goruntu(p["kural_seti"], kurallar, a, g2, motor.envanter) if g2 else d
        hedef_kurallar = {k for k, _ in yap}
        kalan_hedef = [r for r in d2["kurallar"] if r["kural"] in hedef_kurallar and r["sonuc"] == "ihlal"]
        satir = {"duzeltilen": len(hedef_kurallar) - len(kalan_hedef), "kalan_ihlal": d2["ihlal"],
                 "puan": f"{d['puan']} → {d2['puan']}",
                 "yapilacak": "; ".join(f"{k}: {duzelt.aciklama(e)}" for k, e in yap), "birakilan": "; ".join(birak) or "-"}
        if kalan_hedef or u["sonuc"]["durum"] != "basarili":
            out[a] = sonuc(a, "hatali", satir, "düzeltilemeyen: " + "; ".join(f"{r['kural']} ({r['aciklama']})" for r in kalan_hedef)
                           + (f" {u['sonuc'].get('neden')}" if u["sonuc"].get("neden") else ""), u["sonuc"])
        else:
            out[a] = sonuc(a, "basarili", satir, kaynak=u["sonuc"])
        _kosu_kaydet(p["kural_seti"], ks.get("surum"), {a: d2})
    return [out[s.ad] for s in sunucular]


# ---------------------------------------------------------------- anlık görüntü
def _goruntu_istegi(dosyalar=None):
    return {"paketler": True, "servisler": True, "kullanicilar": True, "portlar": True,
            "dosyalar": list(dosyalar or GORUNTU_DOSYALARI), "sysctl": GORUNTU_SYSCTL}


def isleyici_goruntu_al(sunucular, p, kuru=False, durdurma=None, motor=None, plan=None, gozlemci=None):
    t = durum.topla(motor, [s.ad for s in sunucular], _goruntu_istegi(p.get("dosyalar")), (plan or {}).get("is_kimligi"), gozlemci)
    out = []
    for s in sunucular:
        x = t[s.ad]
        if not x["goruntu"]:
            out.append(kaynak_hatasi(s.ad, x["sonuc"]))
            continue
        g = x["goruntu"]
        k = durum.goruntu_kaydet(g, p.get("etiket") or "")
        out.append(sonuc(s.ad, "basarili", {"goruntu": k, "paket": len(g["paketler"]), "servis": len(g["servisler"]),
                                            "kullanici": len(g["kullanicilar"]), "port": len(g["portlar"])}, kaynak=x["sonuc"]))
    return out


def isleyici_karsilastir(sunucular, p, kuru=False, durdurma=None, motor=None, plan=None, gozlemci=None):
    """referans = bir sunucu adı (altın sunucu: hedefler ona göre) ya da 'onceki' (her hedef kendi son kayıtlı görüntüsüne
    göre). Hedeflerin görüntüsü şimdi alınır ve kaydedilir."""
    ref = str(p.get("referans") or "onceki").strip()
    is_k = (plan or {}).get("is_kimligi")
    adlar = [s.ad for s in sunucular]
    ref_ad = None
    if ref.lower() != "onceki":
        ref_ad = next((a for a in motor.envanter.sunucular if a.upper() == ref.upper()), None)
        if not ref_ad:
            return [sonuc(a, "hatali", {}, f"referans sunucu envanterde yok: {ref}") for a in adlar]
    hepsi = sorted(set(adlar) | ({ref_ad} if ref_ad else set()))
    onceki = {a: durum.son_goruntu(a) for a in adlar} if not ref_ad else {}
    t = durum.topla(motor, hepsi, _goruntu_istegi(p.get("dosyalar")), is_k, gozlemci)
    if ref_ad and not t[ref_ad]["goruntu"]:
        return [sonuc(a, "hatali", {}, f"referans sunucu {ref_ad} okunamadı: {t[ref_ad]['sonuc'].get('neden')}") for a in adlar]
    out = []
    for a in adlar:
        x = t[a]
        if not x["goruntu"]:
            out.append(kaynak_hatasi(a, x["sonuc"]))
            continue
        durum.goruntu_kaydet(x["goruntu"], "karşılaştırma")
        if ref_ad:
            if a == ref_ad:
                out.append(sonuc(a, "basarili", {"referans": ref_ad, "fark": 0, "farklar": "referans sunucunun kendisi"},
                                 kaynak=x["sonuc"]))
                continue
            f = durum.karsilastir(t[ref_ad]["goruntu"], x["goruntu"])
            referans = ref_ad
        else:
            if not onceki.get(a):
                out.append(sonuc(a, "basarili", {"referans": "onceki", "fark": 0,
                                                 "farklar": "önceki görüntü yoktu; ilk görüntü şimdi kaydedildi"}, kaynak=x["sonuc"]))
                continue
            f = durum.karsilastir(onceki[a], x["goruntu"])
            referans = f"{a} @ {onceki[a].get('zaman')}"
        out.append(sonuc(a, "basarili", {"referans": referans, "fark": f["toplam"],
                                         "farklar": " | ".join(durum.fark_metni(f, 25)) or "fark yok"}, kaynak=x["sonuc"]))
    return out


ISLEYICILER = {"uyum_denetle": isleyici_denetle, "uyum_duzelt": isleyici_duzelt,
               "uyum_geri_al": None, "anlik_goruntu_al": isleyici_goruntu_al, "goruntu_karsilastir": isleyici_karsilastir}


def _geri_al_bagla():
    from .yazilim_politikasi import geri_al_isleyicisi
    ISLEYICILER["uyum_geri_al"] = geri_al_isleyicisi(["uyum_duzelt"], "uyum düzeltmesi")


_geri_al_bagla()
