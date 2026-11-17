"""Yama becerileri ailesi (D1): durum, politika, uyum, uygula (aşamalı, ön/son kontrol, yeniden başlatma politikası),
geri al, yeniden başlat.

sunucu otomasyonu'nın Windows/Solaris/Ubuntu/RHEL yama alt sistemlerinin genel ve kolaylaştırılmış hâli: bekleyen güncellemeyi dağıtımın
kendi paket yöneticisi bulur (apt/dnf/apk farkını `durum.toplayici` çözer), güvenlik sınıfını dağıtımın kendi verisi
söyler (Debian: güvenlik deposu; RHEL: updateinfo; Alpine: secdb), politika "hangi sunucuda hangi yamalar olmalı"
sorusunun cevabıdır (hedef seçici, kapsam, hariç tutulanlar ve gerekçeli, süreli istisnalar). Uygulama:
    tarama → (kuru: fark önizlemesi) → ön kontrol → yükseltme → doğrulama → son kontrol (düşerse eski sürüme iner) →
    yeniden başlatma politikası (asla | gerekirse | pencerede: bakım penceresine zamanlanır)
Aşamalı dağıtım: `test_grubu` verilirse önce o sunucular; hepsi başarılıysa kalanlar, değilse kalanlar başlamaz.
Geri alma: kayıttaki önceki sürümlere indirme. Eski sürüm depoda yoksa "geri alınamaz" açıkça yazılır.
"""
import datetime
import json
import time

from . import durum, duzelt
from .yurutme import bos_sonuc

def yama_sonuc():
    return durum.sonuc_yolu("yama")
KAPSAMLAR = ("guvenlik", "hepsi", "paketler")
YENIDEN = ("asla", "gerekirse", "pencerede")
CEKIRDEK_BENZERI = ("kernel", "linux-image", "cekirdek", "glibc", "systemd")


def _simdi():
    return datetime.datetime.now()


def sonuc(ad, durum_, satirlar, neden="", kaynak=None):
    """Yönetim işleyicilerinin sunucu başına sonucu (tek şema; stdout anahtar=değer satırları)."""
    r = bos_sonuc(ad, durum_, neden)
    k = kaynak or {}
    r.update(stdout="".join(f"{a}={str(v).replace(chr(10), ' ')}\n" for a, v in satirlar.items()),
             cikis_kodu=0 if durum_ == "basarili" else (k.get("cikis_kodu") or 1),
             sure=k.get("sure", 0.0), tasiyici=k.get("tasiyici"), deneme=k.get("deneme", 1),
             oykunme=k.get("oykunme", False))
    if k.get("tasiyici_notu"):
        r["tasiyici_notu"] = k["tasiyici_notu"]
    return r


def kaynak_hatasi(ad, r):
    """Toplayıcı/eylem yürütmesi düştüyse (erişilemedi, zaman aşımı, iptal) aynı durumla döner."""
    out = dict(r)
    out.setdefault("neden", "")
    return out


# ---------------------------------------------------------------- politika
def politikalar():
    return (durum.kayit_oku("yama_politikalari") or {}).get("politikalar", {})


def politika_dogrula(p, envanter=None):
    h = []
    if p.get("kapsam", "guvenlik") not in KAPSAMLAR:
        h.append(f"kapsam {KAPSAMLAR} olmalı")
    if p.get("kapsam") == "paketler" and not p.get("paketler"):
        h.append("kapsam 'paketler' ise paket listesi gerekli")
    if p.get("yeniden_baslatma", "asla") not in YENIDEN:
        h.append(f"yeniden_baslatma {YENIDEN} olmalı")
    for x in p.get("haric", []) + p.get("istisnalar", []):
        if not x.get("paket") or not str(x.get("gerekce", "")).strip():
            h.append(f"hariç tutma / istisna paket adı ve gerekçe ister: {x}")
        if x.get("bitis"):
            try:
                datetime.date.fromisoformat(str(x["bitis"])[:10])
            except ValueError:
                h.append(f"bitiş tarihi YYYY-AA-GG olmalı: {x['bitis']}")
    if envanter is not None:
        for alan in ("hedef", "test_grubu"):
            if p.get(alan):
                try:
                    envanter.dondur(p[alan])
                except Exception as e:  # noqa: BLE001 - seçici hatası politika hatasıdır
                    h.append(f"{alan} seçicisi geçersiz: {e}")
    return h


def politika_kaydet(ad, p, kim="operatör", envanter=None):
    h = politika_dogrula(p, envanter)
    if h:
        raise ValueError("; ".join(h))
    alanlar = ("aciklama", "hedef", "kapsam", "paketler", "haric", "istisnalar", "yeniden_baslatma", "test_grubu")
    return durum.surumlu_kaydet("yama_politikalari", "politikalar", ad, {k: p[k] for k in alanlar if k in p}, kim)


def _gecerli(x, bugun):
    return not x.get("bitis") or str(x["bitis"])[:10] >= bugun.isoformat()


def kapsam_sec(guncellemeler, sunucu, kapsam="guvenlik", paketler=(), haric=(), istisnalar=(), bugun=None):
    """(seçilenler, dışlananlar[{paket, neden}], süresi dolmuş istisnalar). Hariç tutma ve istisna gerekçesiyle kalır."""
    bugun = bugun or _simdi().date()
    secilen, dislanan, dolmus = [], [], []
    for g in guncellemeler:
        if kapsam == "guvenlik" and not g.get("guvenlik"):
            continue
        if kapsam == "paketler" and g["paket"] not in paketler:
            continue
        h = next((x for x in haric if (x.get("paket") if isinstance(x, dict) else x) == g["paket"]), None)
        if h is not None:
            if isinstance(h, dict) and not _gecerli(h, bugun):
                dolmus.append({"paket": g["paket"], "neden": f"hariç tutmanın süresi doldu ({h.get('bitis')})"})
            else:
                dislanan.append({"paket": g["paket"], "neden": "hariç: " + (h.get("gerekce", "") if isinstance(h, dict) else "talep")})
                continue
        i = next((x for x in istisnalar if x.get("paket") == g["paket"] and str(x.get("sunucu", "")).upper() == sunucu.upper()), None)
        if i is not None:
            if _gecerli(i, bugun):
                dislanan.append({"paket": g["paket"], "neden": f"istisna ({i.get('gerekce')}; bitiş {i.get('bitis') or 'yok'})"})
                continue
            dolmus.append({"paket": g["paket"], "neden": f"istisnanın süresi doldu ({i.get('bitis')})"})
        secilen.append(g)
    return secilen, dislanan, dolmus


def _paket_metni(gg):
    return "; ".join(f"{g['paket']} {g['kurulu']}>{g['aday']}" + (" [güvenlik]" if g.get("guvenlik") else "") for g in gg) or "-"


def _parametre_politikayla(p):
    """Politika verilmişse: varsayılanda bırakılmış parametreler politikadan dolar (talepte açıkça söylenen kazanır)."""
    pol = politikalar().get(p.get("politika") or "") if p.get("politika") else None
    if not pol:
        return dict(p), None
    out = dict(p)
    for alan, varsayilan in (("kapsam", "guvenlik"), ("yeniden_baslatma", "asla")):
        if out.get(alan) in (None, "", varsayilan) and pol.get(alan):
            out[alan] = pol[alan]
    for alan in ("paketler", "test_grubu"):
        if not out.get(alan) and pol.get(alan):
            out[alan] = pol[alan]
    out["haric"] = list(out.get("haric") or []) + list(pol.get("haric") or [])
    out["istisnalar"] = list(pol.get("istisnalar") or [])
    return out, pol


# ---------------------------------------------------------------- işleyiciler
def isleyici_durum(sunucular, p, kuru=False, durdurma=None, motor=None, plan=None, gozlemci=None):
    """yama_durumu: bekleyen güncellemeler, güvenlik sınıfı, yeniden başlatma gerekiyor mu (salt-okur)."""
    is_k = (plan or {}).get("is_kimligi")
    t = durum.topla(motor, [s.ad for s in sunucular], {"paketler": True, "servisler": False, "kullanicilar": False,
                                                        "guncellemeler": True, "yenile": p.get("yenile", True)}, is_k, gozlemci)
    out, ozet = [], {}
    for s in sunucular:
        x = t[s.ad]
        if not x["goruntu"]:
            out.append(kaynak_hatasi(s.ad, x["sonuc"]))
            continue
        g = x["goruntu"]
        gg = g["guncellemeler"]
        out.append(sonuc(s.ad, "basarili", {"bekleyen": len(gg), "guvenlik": sum(1 for u in gg if u["guvenlik"]),
                                            "yeniden_baslatma": "evet" if g["yeniden_baslatma"] else "hayir",
                                            "paketler": _paket_metni(gg)}, kaynak=x["sonuc"]))
        ozet[s.ad] = {"zaman": g["zaman"], "guncellemeler": gg, "yeniden_baslatma": g["yeniden_baslatma"],
                      "uyarilar": g["uyarilar"]}
    _durum_kaydet(ozet)
    return out


def _durum_kaydet(ozet):
    if not ozet:
        return
    YAMA_SONUC = yama_sonuc()
    YAMA_SONUC.mkdir(parents=True, exist_ok=True)
    yol = YAMA_SONUC / "durum.json"
    try:
        eski = json.loads(yol.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        eski = {}
    eski.update(ozet)
    yol.write_text(json.dumps(eski, ensure_ascii=False, indent=1), encoding="utf-8")


def uyum_degerlendir(pol, sunucu, guncellemeler, yeniden=False, bugun=None):
    secilen, dislanan, dolmus = kapsam_sec(guncellemeler, sunucu, pol.get("kapsam", "guvenlik"), pol.get("paketler", []),
                                           pol.get("haric", []), pol.get("istisnalar", []), bugun)
    neden = ("politika kapsamında bekleyen yama yok" if not secilen else
             f"politika kapsamında {len(secilen)} bekleyen yama: {_paket_metni(secilen)}")
    if dolmus:
        neden += "; " + "; ".join(f"{x['paket']}: {x['neden']}" for x in dolmus)
    return {"uyum": "uyumlu" if not secilen else "uyumsuz", "eksik": len(secilen), "istisna": len(dislanan),
            "yeniden_baslatma": "bekliyor" if yeniden else "yok", "neden": neden,
            "eksik_paketler": [g["paket"] for g in secilen], "dislanan": dislanan}


def isleyici_uyum(sunucular, p, kuru=False, durdurma=None, motor=None, plan=None, gozlemci=None):
    """yama_uyumu: politikaya göre her sunucu uyumlu mu, değilse neden (salt-okur)."""
    pol = politikalar().get(p["politika"])
    if not pol:
        return [bos_sonuc(s.ad, "hatali", f"yama politikası yok: {p['politika']}") for s in sunucular]
    kapsam = set(motor.envanter.dondur(pol["hedef"])["sunucular"]) if pol.get("hedef") else None
    icerde = [s for s in sunucular if kapsam is None or s.ad in kapsam]
    t = durum.topla(motor, [s.ad for s in icerde], {"paketler": True, "servisler": False, "kullanicilar": False,
                                                     "guncellemeler": True, "yenile": p.get("yenile", True)},
                    (plan or {}).get("is_kimligi"), gozlemci) if icerde else {}
    out, kayit = [], {}
    for s in sunucular:
        if s not in icerde:
            out.append(sonuc(s.ad, "basarili", {"uyum": "kapsam_disi", "eksik": 0, "istisna": 0, "yeniden_baslatma": "-",
                                                "neden": f"politika hedefi ({pol.get('hedef')}) bu sunucuyu kapsamıyor"}))
            continue
        x = t[s.ad]
        if not x["goruntu"]:
            out.append(kaynak_hatasi(s.ad, x["sonuc"]))
            continue
        u = uyum_degerlendir(pol, s.ad, x["goruntu"]["guncellemeler"], x["goruntu"]["yeniden_baslatma"])
        kayit[s.ad] = {**u, "zaman": x["goruntu"]["zaman"], "politika": p["politika"], "politika_surum": pol.get("surum")}
        out.append(sonuc(s.ad, "basarili", {k: u[k] for k in ("uyum", "eksik", "istisna", "yeniden_baslatma", "neden")},
                         kaynak=x["sonuc"]))
    if kayit:
        YAMA_SONUC = yama_sonuc()
        YAMA_SONUC.mkdir(parents=True, exist_ok=True)
        yol = YAMA_SONUC / "uyum.json"
        try:
            eski = json.loads(yol.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            eski = {}
        eski.setdefault(p["politika"], {}).update(kayit)
        yol.write_text(json.dumps(eski, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


def betik_kontrol(motor, adlar, betik, is_k, gozlemci=None):
    """Ön/son kontrol: kütüphanedeki betik her sunucuda çalışır; çıkış 0 değilse kontrol düşmüş sayılır."""
    if not betik or not adlar:
        return {a: (True, "") for a in adlar}
    metin = motor.katalog.betik_oku(betik)
    rr = motor.yurutucu.yelpaze(adlar, lambda s: metin, 120, yeniden_deneme=0, gozlemci=gozlemci, is_kimligi=is_k)
    return {r["sunucu"]: (r["durum"] == "basarili", (r.get("stderr") or r.get("stdout") or r.get("neden") or "")[-200:].strip())
            for r in rr}


def asamali(motor, sunucular, test_secici, asama_fn):
    """Önce test grubu, başarılıysa kalanlar. asama_fn(sunucular, asama_adi) -> {ad: sonuc}. Dönüş: sıralı sonuçlar."""
    adlar = [s.ad for s in sunucular]
    test = []
    if test_secici:
        test = [a for a in motor.envanter.dondur(test_secici)["sunucular"] if a in adlar]
    if not test or len(test) == len(adlar):
        tek = asama_fn(sunucular, "tek")
        return [tek[a] for a in adlar]
    tsonuc = asama_fn([s for s in sunucular if s.ad in test], "test")
    basarili = all(tsonuc[a]["durum"] == "basarili" for a in test)
    if not basarili:
        dusen = ", ".join(a for a in test if tsonuc[a]["durum"] != "basarili")
        kalan = {s.ad: bos_sonuc(s.ad, "iptal", f"test grubu başarısız ({dusen}); aşamalı dağıtım durdu, bu sunucuya dokunulmadı")
                 for s in sunucular if s.ad not in test}
        for r in kalan.values():
            r["stdout"] = "asama=kalan\ndurum=baslamadi\n"
        tsonuc.update(kalan)
        return [tsonuc[a] for a in adlar]
    ksonuc = asama_fn([s for s in sunucular if s.ad not in test], "kalan")
    return [{**tsonuc, **ksonuc}[a] for a in adlar]


def acilis_kimlikleri(motor, adlar, is_k):
    rr = motor.yurutucu.yelpaze(adlar, "cat /run/filo-acilis-kimligi 2>/dev/null || cat /proc/sys/kernel/random/boot_id",
                                30, yeniden_deneme=1, is_kimligi=is_k, denetle=False)
    return {r["sunucu"]: (r.get("stdout") or "").strip() if r["durum"] == "basarili" else None for r in rr}


def yeniden_baslat_ve_bekle(motor, adlar, is_k, bekle_sn=120, gozlemci=None):
    """Sunucuları yeniden başlatır ve açılış kimliği değişene kadar bekler. {ad: (tamam, açıklama)}"""
    if not adlar:
        return {}
    once = acilis_kimlikleri(motor, adlar, is_k)
    env = motor.envanter
    rr = motor.yurutucu.yelpaze(adlar, lambda s: duzelt.komut(s.aile, {"tur": "yeniden_baslat"}, is_k), 60,
                                yeniden_deneme=0, gozlemci=gozlemci, is_kimligi=is_k)
    bekleyen = {r["sunucu"] for r in rr if r["durum"] == "basarili" or r["durum"] == "erisilemedi"}
    out = {r["sunucu"]: (False, f"yeniden başlatma komutu düştü: {(r.get('stderr') or r.get('neden') or '')[:200]}")
           for r in rr if r["sunucu"] not in bekleyen}
    son = time.time() + bekle_sn
    time.sleep(4)
    while bekleyen and time.time() < son:
        simdi = acilis_kimlikleri(motor, sorted(bekleyen), is_k)
        for a, k in simdi.items():
            if k and k != once.get(a):
                out[a] = (True, "yeniden başlatıldı (açılış kimliği değişti)")
                bekleyen.discard(a)
        if bekleyen:
            time.sleep(3)
    for a in bekleyen:
        out[a] = (False, f"{bekle_sn} sn içinde yeniden açılmadı ya da açılış kimliği değişmedi")
    _ = env
    return out


def pencereye_zamanla(motor, adlar, is_k, neden):
    """Yeniden başlatmayı hedefleri kapsayan bakım penceresine zamanlar (C2). Dönüş: (zamanlama kimliği, zaman) ya da hata."""
    from .zamanlayici import ZamanlamaHatasi, Zamanlayici
    z = getattr(motor, "zamanlayici", None) or Zamanlayici(pencereler=motor._pencereler())
    try:
        ad = z.pencereler.bakim_penceresi_bul(motor.envanter, adlar)
    except ZamanlamaHatasi as e:
        return None, str(e)
    tanim = {"tur": "beceri", "beceri": "sunucu_yeniden_baslat", "parametreler": {}, "hedef_secici": {"ad": ",".join(adlar)},
             "talep": f"yama sonrası yeniden başlatma ({neden})"}
    try:
        k = z.ekle(f"Yama sonrası yeniden başlatma: {', '.join(adlar)}", tanim, {"tur": "pencere", "pencere": ad},
                   "simdi", "hemen", None, f"yama_uygula:{is_k}", on_onay=f"yama_uygula onayı (iş {is_k})",
                   dondurulmus={"secici": {"ad": ",".join(adlar)}, "sunucular": list(adlar)})
    except ZamanlamaHatasi as e:
        return None, str(e)
    return k["kimlik"], f"{ad} penceresinde {k.get('sonraki')}"


def isleyici_uygula(sunucular, p, kuru=False, durdurma=None, motor=None, plan=None, gozlemci=None):
    p, pol = _parametre_politikayla(p)
    is_k = (plan or {}).get("is_kimligi") or "yama"
    bugun = getattr(getattr(motor, "pencereler", None), "saat", _simdi)().date() if getattr(motor, "pencereler", None) else None

    def asama(grup, asama_adi):
        adlar = [s.ad for s in grup]
        t = durum.topla(motor, adlar, {"paketler": True, "servisler": False, "kullanicilar": False, "guncellemeler": True,
                                       "yenile": True}, is_k, gozlemci)
        out, plan_e, secimler = {}, {}, {}
        for s in grup:
            x = t[s.ad]
            if not x["goruntu"]:
                out[s.ad] = kaynak_hatasi(s.ad, x["sonuc"])
                continue
            secilen, dislanan, dolmus = kapsam_sec(x["goruntu"]["guncellemeler"], s.ad, p.get("kapsam", "guvenlik"),
                                                   p.get("paketler") or [], p.get("haric") or [], p.get("istisnalar") or [], bugun)
            secimler[s.ad] = (secilen, dislanan, x)
            if kuru:
                reboot = any(any(k in g["paket"] for k in CEKIRDEK_BENZERI) for g in secilen)
                out[s.ad] = sonuc(s.ad, "basarili", {"yuklenen": 0, "asama": asama_adi,
                                                     "yapilacak": _paket_metni(secilen),
                                                     "dislanan": "; ".join(f"{d['paket']} ({d['neden']})" for d in dislanan) or "-",
                                                     "yeniden_baslatma": ("gerekebilir (çekirdek benzeri paket)" if reboot else "gerekmeyebilir")
                                                     + f"; politika: {p.get('yeniden_baslatma', 'asla')}",
                                                     "paketler": _paket_metni(secilen)}, kaynak=x["sonuc"])
                continue
            if not secilen:
                out[s.ad] = sonuc(s.ad, "basarili", {"yuklenen": 0, "asama": asama_adi, "paketler": "-",
                                                     "dislanan": "; ".join(f"{d['paket']} ({d['neden']})" for d in dislanan) or "-",
                                                     "yeniden_baslatma": "gerekmiyor", "not": "kapsamda bekleyen yama yok"},
                                  kaynak=x["sonuc"])
                continue
            plan_e[s.ad] = [{"tur": "paket_yukselt", "paketler": [g["paket"] for g in secilen]}]
        if kuru or not plan_e:
            return out
        # ön kontrol
        on = betik_kontrol(motor, list(plan_e), p.get("on_kontrol"), is_k, gozlemci)
        for a, (ok, msg) in on.items():
            if not ok:
                out[a] = sonuc(a, "hatali", {"yuklenen": 0, "asama": asama_adi, "paketler": "-",
                                             "yeniden_baslatma": "-"}, f"ön kontrol başarısız ({p.get('on_kontrol')}): {msg}; yama yapılmadı")
                plan_e.pop(a)
        uyg = duzelt.uygula(motor, plan_e, is_k, gozlemci, zaman_asimi=600)
        sonra = durum.topla(motor, list(uyg), {"paketler": True, "servisler": False, "kullanicilar": False,
                                               "guncellemeler": True, "yenile": False}, is_k, None) if uyg else {}
        son_k = betik_kontrol(motor, [a for a in uyg if uyg[a]["sonuc"]["durum"] == "basarili"], p.get("son_kontrol"), is_k, gozlemci)
        yeniden_gerek = []
        for a, u in uyg.items():
            secilen, dislanan, x = secimler[a]
            once = x["goruntu"]
            geri = duzelt.yukseltme_geri(plan_e[a][0], once)
            g2 = (sonra.get(a) or {}).get("goruntu") or {}
            hala = [g for g in g2.get("guncellemeler", []) if g["paket"] in plan_e[a][0]["paketler"]]
            yuklenen = [g for g in secilen if g["paket"] not in {h["paket"] for h in hala}]
            duzelt.kaydet(is_k, "yama_uygula", a, u["eylemler"], geri,
                          {"paketler": [{"paket": g["paket"], "eski": g["kurulu"], "yeni": g["aday"]} for g in yuklenen],
                           "politika": p.get("politika")})
            satir = {"yuklenen": len(yuklenen), "asama": asama_adi, "paketler": _paket_metni(yuklenen),
                     "dislanan": "; ".join(f"{d['paket']} ({d['neden']})" for d in dislanan) or "-"}
            if u["sonuc"]["durum"] != "basarili" or hala:
                neden = u["sonuc"].get("neden") or ("hâlâ bekleyen: " + _paket_metni(hala))
                out[a] = sonuc(a, "hatali", {**satir, "yeniden_baslatma": "-"}, f"yama tamamlanmadı: {neden}", u["sonuc"])
                continue
            ok, msg = son_k.get(a, (True, ""))
            if not ok:
                ga = duzelt.uygula(motor, {a: geri}, is_k + "-geri", gozlemci)
                gd = ga.get(a, {}).get("sonuc", {}).get("durum") if geri else "yok"
                duzelt.geri_alindi_isaretle(is_k, a, is_k + "-geri")
                out[a] = sonuc(a, "hatali", {**satir, "yeniden_baslatma": "-",
                                             "geri_alma": "eski sürüme inildi" if gd == "basarili" else f"geri alma başarısız ({gd})"},
                               f"son kontrol başarısız ({p.get('son_kontrol')}): {msg}; yama geri alındı", u["sonuc"])
                continue
            if g2.get("yeniden_baslatma"):
                yeniden_gerek.append(a)
            out[a] = sonuc(a, "basarili", {**satir, "yeniden_baslatma": "gerekmiyor",
                                           "geri_alma": "mümkün (önceki sürüme indirme)"}, kaynak=u["sonuc"])
        if yeniden_gerek:
            pol_y = p.get("yeniden_baslatma", "asla")
            if pol_y == "asla":
                for a in yeniden_gerek:
                    out[a]["stdout"] = out[a]["stdout"].replace("yeniden_baslatma=gerekmiyor",
                                                                "yeniden_baslatma=gerekiyor (politika: asla; yapılmadı)")
            elif pol_y == "gerekirse":
                rb = yeniden_baslat_ve_bekle(motor, yeniden_gerek, is_k, gozlemci=gozlemci)
                for a, (ok, msg) in rb.items():
                    out[a]["stdout"] = out[a]["stdout"].replace("yeniden_baslatma=gerekmiyor", f"yeniden_baslatma=yapildi ({msg})"
                                                                if ok else f"yeniden_baslatma=basarisiz ({msg})")
                    if not ok:
                        out[a].update(durum="hatali", neden=f"yeniden başlatma: {msg}")
            else:
                zk, msg = pencereye_zamanla(motor, yeniden_gerek, is_k, "yama")
                for a in yeniden_gerek:
                    out[a]["stdout"] = out[a]["stdout"].replace(
                        "yeniden_baslatma=gerekmiyor", f"yeniden_baslatma=bakım penceresine zamanlandı ({zk}, {msg})" if zk
                        else f"yeniden_baslatma=zamanlanamadı ({msg})")
                    if not zk:
                        out[a].update(durum="hatali", neden=f"yeniden başlatma bakım penceresine zamanlanamadı: {msg}")
        return out

    return asamali(motor, sunucular, p.get("test_grubu"), asama)


def isleyici_geri_al(sunucular, p, kuru=False, durdurma=None, motor=None, plan=None, gozlemci=None):
    """Son yama uygulamasını (ya da `is_kimligi` verilen işi) geri alır: paketler önceki sürümlerine iner."""
    is_k = (plan or {}).get("is_kimligi") or "yama-geri"
    plan_e, kayit = {}, {}
    out = {}
    for s in sunucular:
        k = (next((v for v in reversed(duzelt.kayitlar(s.ad, "yama_uygula", p.get("is_kimligi"))) if not v.get("geri_alindi")), None)
             if p.get("is_kimligi") else duzelt.son_kayit(s.ad, ["yama_uygula"]))
        if not k or not k.get("geri"):
            out[s.ad] = sonuc(s.ad, "basarili", {"geri_alinan": 0, "paketler": "-", "not": "geri alınacak yama kaydı yok"})
            continue
        kayit[s.ad] = k
        plan_e[s.ad] = k["geri"]
    if kuru:
        for a, ee in plan_e.items():
            out[a] = sonuc(a, "basarili", {"geri_alinan": 0, "paketler": "; ".join(duzelt.aciklama(e) for e in ee)})
        return [out[s.ad] for s in sunucular]
    uyg = duzelt.uygula(motor, plan_e, is_k, gozlemci, zaman_asimi=600)
    for a, u in uyg.items():
        ok = u["sonuc"]["durum"] == "basarili"
        eksik = [e for e in u["eylemler"] if e["durum"] != "basarili"]
        if ok:
            duzelt.geri_alindi_isaretle(kayit[a]["is"], a, is_k)
        neden = "" if ok else ("geri alınamadı: " + "; ".join(
            f"{duzelt.aciklama(e)}: {e['hata'] or e['durum']}" + (" (eski sürüm depoda yok; geri alma bu yoldan mümkün değil)"
                                                                 if "depoda yok" in (e["hata"] or "") else "") for e in eksik))
        out[a] = sonuc(a, "basarili" if ok else "hatali",
                       {"geri_alinan": sum(1 for e in u["eylemler"] if e["durum"] == "basarili"),
                        "paketler": "; ".join(duzelt.aciklama(e) for e in u["eylemler"])}, neden, u["sonuc"])
    return [out[s.ad] for s in sunucular]


def isleyici_yeniden_baslat(sunucular, p, kuru=False, durdurma=None, motor=None, plan=None, gozlemci=None):
    is_k = (plan or {}).get("is_kimligi") or "yeniden"
    adlar = [s.ad for s in sunucular]
    if kuru:
        return [sonuc(a, "basarili", {"yeniden_baslatildi": "hayir", "not": "kuru çalıştırma: yeniden başlatılacak"}) for a in adlar]
    rb = yeniden_baslat_ve_bekle(motor, adlar, is_k, gozlemci=gozlemci)
    return [sonuc(a, "basarili" if rb[a][0] else "hatali", {"yeniden_baslatildi": "evet" if rb[a][0] else "hayir",
                                                            "not": rb[a][1]}, "" if rb[a][0] else rb[a][1]) for a in adlar]


ISLEYICILER = {"yama_durumu": isleyici_durum, "yama_uyumu": isleyici_uyum, "yama_uygula": isleyici_uygula,
               "yama_geri_al": isleyici_geri_al, "sunucu_yeniden_baslat": isleyici_yeniden_baslat}
