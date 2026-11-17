"""Yapılı akış: dosya biçimi (sürüm 2), kodla doğrulama ve kalıcı durumla yürütme.

Eski düz akışlar (`akislar/*.json`, sürüm 1: {"adimlar": [{"beceri", "parametreler"}]}) `eski_akistan` ile okunur ve
çalışmaya devam eder. Sürüm 2 iç içe bloklardan oluşur (okunaklı; görsel çizim gerektirmez):

    {"bicim": "filo-akis", "surum": 2, "ad": "...", "aciklama": "...",
     "girdi": {"paketler": {"tip": "liste", "varsayilan": ["jq"]}},
     "hedef_secici": "PA*",
     "adimlar": [ <düğüm>, ... ]}

Düğümler (her birinin benzersiz "kimlik" alanı vardır):
    beceri     {"tur": "beceri", "beceri": "paket_kur", "parametreler": {"paketler": ["{paket}"]},
                "hata_durumunda": "dusur" | "devam"}            dusur: başarısız sunucu sonraki adımlara girmez
    dal        {"tur": "dal", "kosul": <koşul>, "evet": [...], "hayir": [...]}
               akış düzeyi koşul (bir adımın sonucu, değişken) tüm akışı dallar; sunucu düzeyi koşul (sunucu özelliği ya da
               bir adımın o sunucudaki çıktısı) sunucuları iki kola ayırır
    sunucu_dal {"tur": "sunucu_dal", "adim": "<kimlik>", "basarili": [...], "basarisiz": [...]}
               o adımda başarılı olan sunucular bir kola, başarısız olanlar öbür kola (başarısız kolu başarıyla bitiren
               sunucu akışa geri döner)
    dongu      {"tur": "dongu", "degisken": "paket", "liste": ["jq", "tree"] | "{paketler}", "en_cok": 5, "govde": [...]}
               {"tur": "dongu", "kadar": <koşul>, "en_cok": 3, "govde": [...]}       üst sınır ZORUNLU
    paralel    {"tur": "paralel", "kollar": [[...], [...]]}     kollar aynı anda; hepsi bitince birleşir
    alt_akis   {"tur": "alt_akis", "akis": "<kayıtlı akış adı>", "girdi": {"paket": "{paket}"}, "cikti": {"x": "y"}}
    bekle      {"tur": "bekle", "sure_sn": 30}  |  {"tur": "bekle", "kosul": <yoklama>, "zaman_asimi_sn": 120, "aralik_sn": 10}
               yoklama: {"beceri": "servis_durumu", "parametreler": {...}, "alan": "durum", "esit": "active"} (salt-okur)
    onay       {"tur": "onay", "mesaj": "...", "reddedilirse": [...]}   insan onayı (gated); reddedilirse akış durur
    bildirim   {"tur": "bildirim", "alici": "ops@lab.yerel", "konu": "..."}
    bitir      {"tur": "bitir", "sonuc": "basarili" | "basarisiz" | "devret", "mesaj": "..."}

Koşul: {"adim": "a1", "olcu": "durum" | "basarili_sayisi" | "basarisiz_sayisi", <işlem>: değer}
       {"degisken": "x", <işlem>: değer}
       {"sunucu": "aile" | "os" | "ad" | "grup" | "oznitelik.<ad>", <işlem>: değer}      (sunucu düzeyi)
       {"adim": "a1", "alan": "durum" | "<çıktı alanı>", <işlem>: değer}                (sunucu düzeyi)
       işlem: esit, esit_degil, icerir, buyuk, kucuk (buyuk/kucuk sayı ister)

Devam noktaları: üst düzeydeki her tamamlanan düğüm (bileşik düğüm bütünüyle) bir devam noktasıdır.
"""
import copy
import json
import re
import threading
import time

from . import ROOT

BICIM = "filo-akis"
SURUM = 2
TURLER = ("beceri", "dal", "sunucu_dal", "dongu", "paralel", "alt_akis", "bekle", "onay", "bildirim", "bitir")
ISLEMLER = ("esit", "esit_degil", "icerir", "buyuk", "kucuk")
EN_COK_DONGU = 50
EN_COK_BEKLE_SN = 6 * 3600
EN_COK_DERINLIK = 5
EN_COK_DUGUM = 80
AKISLAR = ROOT / "akislar"
YER_TUTUCU = re.compile(r"\{([a-z_][a-z0-9_]*)\}")


class AkisHatasi(ValueError):
    pass


class AkisDurdu(Exception):
    """Akış bir düğümde durdu: onay bekliyor, reddedildi, iptal."""

    def __init__(self, durum, metin=""):
        super().__init__(metin or durum)
        self.durum, self.metin = durum, metin


class AkisBitti(Exception):
    def __init__(self, sonuc, mesaj=""):
        super().__init__(mesaj)
        self.sonuc, self.mesaj = sonuc, mesaj


# ---------------------------------------------------------------- biçim
def duz_akis(adimlar, ad=None, talep=None, hedef_secici=None):
    """Düz beceri listesinden sürüm 2 akış."""
    return {"bicim": BICIM, "surum": SURUM, "ad": ad, "talep": talep, "hedef_secici": hedef_secici, "girdi": {},
            "adimlar": [{"kimlik": f"a{i}", "tur": "beceri", "beceri": a["beceri"],
                         "parametreler": dict(a.get("parametreler") or {}),
                         **({"kimlik_calistirma": a["kimlik_calistirma"]} if a.get("kimlik_calistirma") else {})}
                        for i, a in enumerate(adimlar, 1)]}


def eski_akistan(veri):
    """Sürüm 1 (düz) ya da sürüm 2 akış -> sürüm 2. Eski dosyalar yeniden yazılmaz."""
    if isinstance(veri, dict) and veri.get("bicim") == BICIM:
        return veri
    return duz_akis(veri.get("adimlar", []), veri.get("ad"), veri.get("talep"), veri.get("hedef_secici"))


def akis_yukle(ad, dizin=None):
    yol = (dizin or AKISLAR) / f"{ad}.json"
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", str(ad)) or not yol.exists():
        raise AkisHatasi(f"kayıtlı akış yok: {ad}")
    return eski_akistan(json.loads(yol.read_text(encoding="utf-8")))


def alt_bloklar(d):
    """Düğümün alt blokları: [(ad, blok)]."""
    t = d.get("tur")
    if t == "dal":
        return [("evet", d.get("evet") or []), ("hayir", d.get("hayir") or [])]
    if t == "sunucu_dal":
        return [("basarili", d.get("basarili") or []), ("basarisiz", d.get("basarisiz") or [])]
    if t == "dongu":
        return [("govde", d.get("govde") or [])]
    if t == "paralel":
        return [(f"kol{i}", k) for i, k in enumerate(d.get("kollar") or [], 1)]
    if t == "onay":
        return [("reddedilirse", d.get("reddedilirse") or [])]
    return []


def dugumler(akis_ya_da_blok):
    """Bütün düğümler, önce-sıra (pre-order)."""
    blok = akis_ya_da_blok.get("adimlar", []) if isinstance(akis_ya_da_blok, dict) else akis_ya_da_blok
    for d in blok:
        yield d
        for _, b in alt_bloklar(d):
            yield from dugumler(b)


def beceri_dugumleri(akis):
    return [d for d in dugumler(akis) if d.get("tur", "beceri") == "beceri" and d.get("beceri")]


def duz_mu(akis):
    return all(d.get("tur", "beceri") == "beceri" for d in akis.get("adimlar", []))


def _dugum_metni(d):
    t = d.get("tur", "beceri")
    if t == "beceri":
        return d["beceri"]
    if t == "dal":
        return f"dal[{kosul_metni(d.get('kosul') or {})}]"
    if t == "sunucu_dal":
        return f"sunucu_dal[{d.get('adim')} sonucuna göre]"
    if t == "dongu":
        return (f"döngü[{d.get('degisken')} ∈ {d.get('liste')}, en çok {d.get('en_cok')}]" if "liste" in d
                else f"döngü[{kosul_metni(d.get('kadar') or {})} olana kadar, en çok {d.get('en_cok')}]")
    if t == "paralel":
        return f"paralel[{len(d.get('kollar') or [])} kol]"
    if t == "alt_akis":
        return f"alt_akış[{d.get('akis')}]"
    if t == "bekle":
        return f"bekle[{d['sure_sn']} sn]" if "sure_sn" in d else f"bekle[koşul, en çok {d.get('zaman_asimi_sn')} sn]"
    if t == "onay":
        return "insan_onayı"
    if t == "bildirim":
        return f"bildirim[{d.get('alici')}]"
    return f"bitir[{d.get('sonuc', 'basarili')}]"


def kosul_metni(c):
    islem = next((x for x in ISLEMLER if x in c), "esit")
    isaret = {"esit": "=", "esit_degil": "≠", "icerir": "∋", "buyuk": ">", "kucuk": "<"}[islem]
    sol = (f"{c['adim']}.{c.get('olcu') or c.get('alan')}" if "adim" in c else
           c.get("degisken") or f"sunucu.{c.get('sunucu')}")
    return f"{sol} {isaret} {c.get(islem)}"


def akis_ozeti(akis):
    """Akışın tek satırlık okunaklı özeti (iç içe bloklar köşeli parantezle)."""
    def blok(b):
        parca = []
        for d in b:
            s = _dugum_metni(d)
            alt = [(ad, x) for ad, x in alt_bloklar(d) if x]
            if alt:
                s += " {" + " | ".join(f"{ad}: {blok(x)}" for ad, x in alt) + "}"
            parca.append(s)
        return " → ".join(parca)
    return blok(akis.get("adimlar", []))


def baglam_sikistir(baglam, stdout_siniri=4000):
    """Adımdan devam için yürütme bağlamının kalıcı kopyası (dönüştürme ve e-posta önceki adımın sonucunu kullanır)."""
    def adim(a):
        a = {k: v for k, v in a.items() if k not in ("alt_adimlar",)}
        a["sonuclar"] = [{**r, "stdout": (r.get("stdout") or "")[:stdout_siniri], "stderr": (r.get("stderr") or "")[:1000]}
                         for r in a.get("sonuclar", [])]
        a["kuru"] = [{"sunucu": r.get("sunucu"), "durum": r.get("durum"), "stdout": (r.get("stdout") or "")[:1500]}
                     for r in a.get("kuru", [])]
        return a
    out = {"adimlar": [adim(a) for a in baglam.get("adimlar", [])]}
    for x in ("son_uzak_adim", "son_adim"):
        if baglam.get(x):
            out[x] = adim(baglam[x])
    if baglam.get("belge"):
        out["belge"] = baglam["belge"]
    return json.loads(json.dumps(out, default=str))


def baglam_coz(d):
    return copy.deepcopy(d) if d else None


# ---------------------------------------------------------------- doğrulama
def _tip_uyar(deger_tipi, sema_tipi):
    if deger_tipi is None or sema_tipi is None:
        return True
    if sema_tipi == "liste":
        return deger_tipi == "liste"
    if sema_tipi == "tamsayi":
        return deger_tipi in ("tamsayi",)
    return deger_tipi != "liste"


def _deger_tipi(v):
    if isinstance(v, bool):
        return "mantik"
    if isinstance(v, int):
        return "tamsayi"
    if isinstance(v, list):
        return "liste"
    return "metin"


def dogrula(akis, katalog, akis_dizini=None, _yigin=()):
    """Akışı denetler. Dönüş: hata listesi (boşsa geçerli). Sonsuz döngü (üst sınırsız döngü), erişilemeyen adım,
    tanımsız değişken/adım, tip uyuşmazlığı, bilinmeyen beceri, alt akış döngüsü reddedilir."""
    h = []
    if not isinstance(akis, dict) or akis.get("bicim") != BICIM or akis.get("surum") != SURUM:
        return [f"akış biçimi '{BICIM}' sürüm {SURUM} olmalı"]
    if not isinstance(akis.get("adimlar"), list) or not akis["adimlar"]:
        return ["akışta en az bir adım olmalı"]
    girdi = akis.get("girdi") or {}
    degiskenler = {ad: (x.get("tip") or "metin") for ad, x in girdi.items()}
    kimlikler = {}
    tum = list(dugumler(akis))
    if len(tum) > EN_COK_DUGUM:
        h.append(f"en çok {EN_COK_DUGUM} düğüm")
    for d in tum:
        k = d.get("kimlik")
        if not k or not re.fullmatch(r"[a-z0-9_]{1,40}", str(k)):
            h.append(f"düğüm kimliği eksik ya da geçersiz: {k!r}")
        elif k in kimlikler:
            h.append(f"aynı kimlik iki kez: {k}")
        kimlikler[k] = d
        if d.get("tur", "beceri") not in TURLER:
            h.append(f"{k}: bilinmeyen düğüm türü {d.get('tur')!r} (türler: {', '.join(TURLER)})")

    def kosul_denetle(c, onceki, yer, sunucu_izinli=True):
        if not isinstance(c, dict):
            h.append(f"{yer}: koşul bir nesne olmalı")
            return
        islem = [x for x in ISLEMLER if x in c]
        if len(islem) != 1:
            h.append(f"{yer}: koşulda tek bir işlem olmalı ({', '.join(ISLEMLER)})")
            return
        deger = c[islem[0]]
        if islem[0] in ("buyuk", "kucuk") and not isinstance(deger, (int, float)):
            h.append(f"{yer}: '{islem[0]}' sayı ister, {deger!r} verildi (tip uyuşmazlığı)")
        if "adim" in c:
            if c["adim"] not in onceki:
                h.append(f"{yer}: koşul tanımsız ya da sonra gelen bir adıma bakıyor: {c['adim']!r}")
            elif onceki[c["adim"]].get("tur", "beceri") != "beceri":
                h.append(f"{yer}: koşul yalnız beceri adımının sonucuna bakabilir ({c['adim']})")
            if "olcu" in c:
                if c["olcu"] not in ("durum", "basarili_sayisi", "basarisiz_sayisi"):
                    h.append(f"{yer}: bilinmeyen ölçü {c['olcu']!r}")
                elif c["olcu"] == "durum" and deger not in ("basarili", "kismi", "basarisiz", "iptal"):
                    h.append(f"{yer}: adım durumu basarili/kismi/basarisiz/iptal olur, {deger!r} değil")
                elif c["olcu"].endswith("_sayisi") and islem[0] in ("esit", "buyuk", "kucuk", "esit_degil") \
                        and not isinstance(deger, int):
                    h.append(f"{yer}: sayı ölçüsü tamsayıyla karşılaştırılır (tip uyuşmazlığı)")
            elif "alan" not in c:
                h.append(f"{yer}: adım koşulunda 'olcu' ya da 'alan' gerekli")
            elif not sunucu_izinli:
                h.append(f"{yer}: burada sunucu düzeyi koşul kullanılamaz")
        elif "degisken" in c:
            if c["degisken"] not in kapsam_degiskenleri[-1]:
                h.append(f"{yer}: tanımsız değişken {c['degisken']!r}")
        elif "sunucu" in c:
            if not sunucu_izinli:
                h.append(f"{yer}: burada sunucu düzeyi koşul kullanılamaz")
            alan = str(c["sunucu"])
            if alan not in ("aile", "os", "ad", "grup") and not alan.startswith("oznitelik."):
                h.append(f"{yer}: sunucu özelliği aile/os/ad/grup/oznitelik.<ad> olmalı, {alan!r} değil")
        else:
            h.append(f"{yer}: koşul 'adim', 'degisken' ya da 'sunucu' alanından birini içermeli")

    kapsam_degiskenleri = [dict(degiskenler)]

    def param_denetle(d, sema):
        for ad, v in (d.get("parametreler") or {}).items():
            if ad not in sema:
                h.append(f"{d['kimlik']}: {d['beceri']} becerisinde '{ad}' parametresi yok")
                continue
            metinler = v if isinstance(v, list) else [v]
            for x in metinler:
                for ref in YER_TUTUCU.findall(x) if isinstance(x, str) else []:
                    if ref not in kapsam_degiskenleri[-1]:
                        h.append(f"{d['kimlik']}: tanımsız değişken {{{ref}}}")
            if isinstance(v, str) and YER_TUTUCU.fullmatch(v):
                vt = kapsam_degiskenleri[-1].get(v[1:-1])
                if not _tip_uyar(vt, sema[ad].get("tip")):
                    h.append(f"{d['kimlik']}: '{ad}' {sema[ad].get('tip')} ister, {v} değişkeni {vt} (tip uyuşmazlığı)")
            elif not (isinstance(v, str) and YER_TUTUCU.search(v)) and not (isinstance(v, list) and any(
                    isinstance(x, str) and YER_TUTUCU.search(x) for x in v)):
                from .beceri import SemaHatasi, parametre_dogrula
                try:
                    parametre_dogrula({ad: {**sema[ad], "zorunlu": False}}, {ad: v})
                except SemaHatasi as e:
                    h.append(f"{d['kimlik']}: {e}")

    def blok_denetle(blok, onceki, derinlik, yer):
        if derinlik > EN_COK_DERINLIK:
            h.append(f"{yer}: iç içe derinlik en çok {EN_COK_DERINLIK}")
            return onceki, False
        if not isinstance(blok, list):
            h.append(f"{yer}: blok bir liste olmalı")
            return onceki, False
        bitti = False
        for d in blok:
            k = d.get("kimlik", "?")
            if bitti:
                h.append(f"{k}: erişilemeyen adım (öncesinde akış her yolda bitiyor)")
                continue
            t = d.get("tur", "beceri")
            if t == "beceri":
                if d.get("beceri") not in katalog:
                    h.append(f"{k}: katalogda olmayan beceri {d.get('beceri')!r}")
                else:
                    param_denetle(d, katalog[d["beceri"]].get("girdi") or {})
                if d.get("hata_durumunda", "dusur") not in ("dusur", "devam"):
                    h.append(f"{k}: hata_durumunda dusur ya da devam olmalı")
            elif t == "dal":
                kosul_denetle(d.get("kosul"), onceki, k)
                if not d.get("evet") and not d.get("hayir"):
                    h.append(f"{k}: dalın iki kolu da boş")
                o1, b1 = blok_denetle(d.get("evet") or [], dict(onceki), derinlik + 1, f"{k}.evet")
                o2, b2 = blok_denetle(d.get("hayir") or [], dict(onceki), derinlik + 1, f"{k}.hayir")
                onceki = {**onceki, **o1, **o2}
                bitti = b1 and b2 and bool(d.get("evet")) and bool(d.get("hayir"))
            elif t == "sunucu_dal":
                ref = d.get("adim")
                if ref not in onceki:
                    h.append(f"{k}: sunucu dalı tanımsız ya da sonra gelen bir adıma bakıyor: {ref!r}")
                elif onceki[ref].get("tur", "beceri") != "beceri":
                    h.append(f"{k}: sunucu dalı yalnız beceri adımının sonucuna göre ayrılır")
                elif onceki[ref].get("hata_durumunda", "dusur") == "dusur" and d.get("basarisiz") is not None:
                    pass
                if not d.get("basarili") and not d.get("basarisiz"):
                    h.append(f"{k}: sunucu dalının iki kolu da boş")
                o1, _ = blok_denetle(d.get("basarili") or [], dict(onceki), derinlik + 1, f"{k}.basarili")
                o2, _ = blok_denetle(d.get("basarisiz") or [], dict(onceki), derinlik + 1, f"{k}.basarisiz")
                onceki = {**onceki, **o1, **o2}
            elif t == "dongu":
                en_cok = d.get("en_cok")
                if not isinstance(en_cok, int) or isinstance(en_cok, bool) or not 1 <= en_cok <= EN_COK_DONGU:
                    h.append(f"{k}: döngünün üst sınırı (en_cok, 1-{EN_COK_DONGU}) zorunlu; sınırsız döngü sonsuz "
                             "döngü sayılır")
                if not d.get("govde"):
                    h.append(f"{k}: döngü gövdesi boş")
                yeni = dict(kapsam_degiskenleri[-1])
                if "liste" in d:
                    lst = d["liste"]
                    if isinstance(lst, str):
                        m = YER_TUTUCU.fullmatch(lst)
                        if not m or m.group(1) not in kapsam_degiskenleri[-1]:
                            h.append(f"{k}: döngü listesi tanımsız: {lst!r}")
                        elif kapsam_degiskenleri[-1][m.group(1)] != "liste":
                            h.append(f"{k}: döngü listesi {lst} liste değil (tip uyuşmazlığı)")
                    elif not isinstance(lst, list) or not lst:
                        h.append(f"{k}: döngü listesi boş olmayan bir liste olmalı")
                    elif isinstance(en_cok, int) and len(lst) > en_cok:
                        h.append(f"{k}: listede {len(lst)} öğe var, üst sınır {en_cok}")
                    if not re.fullmatch(r"[a-z_][a-z0-9_]*", str(d.get("degisken", ""))):
                        h.append(f"{k}: döngü değişkeni adı gerekli (ör. paket)")
                    else:
                        yeni[d["degisken"]] = "metin"
                elif "kadar" in d:
                    kosul_denetle(d["kadar"], {**onceki, **{x["kimlik"]: x for x in dugumler(d.get("govde") or [])
                                                           if x.get("kimlik")}}, f"{k}.kadar")
                else:
                    h.append(f"{k}: döngü 'liste' ya da 'kadar' (koşul) ister")
                kapsam_degiskenleri.append(yeni)
                o1, _ = blok_denetle(d.get("govde") or [], dict(onceki), derinlik + 1, f"{k}.govde")
                kapsam_degiskenleri.pop()
                onceki = {**onceki, **o1}
            elif t == "paralel":
                kollar = d.get("kollar")
                if not isinstance(kollar, list) or len(kollar) < 2:
                    h.append(f"{k}: paralel düğüm en az iki kol ister")
                    kollar = kollar if isinstance(kollar, list) else []
                birlesik = dict(onceki)
                for i, kol in enumerate(kollar, 1):
                    if not kol:
                        h.append(f"{k}: kol {i} boş")
                    o1, _ = blok_denetle(kol, dict(onceki), derinlik + 1, f"{k}.kol{i}")   # kollar birbirini göremez
                    birlesik.update(o1)
                onceki = birlesik
            elif t == "alt_akis":
                ad = d.get("akis")
                if ad in _yigin:
                    h.append(f"{k}: alt akış döngüsü: {' → '.join(_yigin + (ad,))}")
                else:
                    try:
                        alt = akis_yukle(ad, akis_dizini)
                    except AkisHatasi as e:
                        h.append(f"{k}: {e}")
                        alt = None
                    if alt is not None:
                        for x in dogrula(alt, katalog, akis_dizini, _yigin + (ad,)):
                            h.append(f"{k} (alt akış {ad}): {x}")
                        for g, tanim in (alt.get("girdi") or {}).items():
                            if g not in (d.get("girdi") or {}) and "varsayilan" not in tanim:
                                h.append(f"{k}: alt akışın zorunlu girdisi eşlenmemiş: {g}")
                        for g, v in (d.get("girdi") or {}).items():
                            if g not in (alt.get("girdi") or {}):
                                h.append(f"{k}: alt akışta '{g}' girdisi yok")
                            for ref in YER_TUTUCU.findall(json.dumps(v)):
                                if ref not in kapsam_degiskenleri[-1]:
                                    h.append(f"{k}: tanımsız değişken {{{ref}}}")
                        for ust, alt_ad in (d.get("cikti") or {}).items():
                            if alt_ad not in (alt.get("girdi") or {}) and alt_ad not in (alt.get("cikti") or []):
                                h.append(f"{k}: alt akışta '{alt_ad}' çıktısı yok")
                            kapsam_degiskenleri[-1][ust] = "metin"
            elif t == "bekle":
                if "sure_sn" in d:
                    s = d["sure_sn"]
                    if not isinstance(s, (int, float)) or not 0 < s <= EN_COK_BEKLE_SN:
                        h.append(f"{k}: bekleme süresi 1-{EN_COK_BEKLE_SN} sn olmalı")
                elif "kosul" in d:
                    zs = d.get("zaman_asimi_sn")
                    if not isinstance(zs, (int, float)) or not 0 < zs <= EN_COK_BEKLE_SN:
                        h.append(f"{k}: koşullu beklemede zaman aşımı (zaman_asimi_sn) zorunlu")
                    c = d["kosul"]
                    if not isinstance(c, dict) or c.get("beceri") not in katalog:
                        h.append(f"{k}: yoklama becerisi katalogda yok")
                    elif katalog.etkin_risk(katalog[c["beceri"]])[0] > 1:
                        h.append(f"{k}: yoklama becerisi salt-okur olmalı (risk 0-1)")
                    elif not c.get("alan") or not any(x in c for x in ISLEMLER):
                        h.append(f"{k}: yoklama koşulunda alan ve işlem gerekli")
                else:
                    h.append(f"{k}: bekleme süre (sure_sn) ya da koşul ister")
            elif t == "onay":
                if not str(d.get("mesaj", "")).strip():
                    h.append(f"{k}: onay mesajı gerekli")
                o1, _ = blok_denetle(d.get("reddedilirse") or [], dict(onceki), derinlik + 1, f"{k}.reddedilirse")
                onceki = {**onceki, **o1}
            elif t == "bildirim":
                from .beceri import EPOSTA
                if not EPOSTA.match(str(d.get("alici", ""))):
                    h.append(f"{k}: bildirim alıcısı geçerli bir e-posta adresi değil")
            elif t == "bitir":
                if d.get("sonuc", "basarili") not in ("basarili", "basarisiz", "devret"):
                    h.append(f"{k}: bitir sonucu basarili/basarisiz/devret olmalı")
                bitti = True
            if d.get("kimlik"):
                onceki[d["kimlik"]] = d
        return onceki, bitti

    blok_denetle(akis["adimlar"], {}, 0, "akış")
    return h


# ---------------------------------------------------------------- koşul değerlendirme
def _karsilastir(deger, c):
    for islem in ISLEMLER:
        if islem in c:
            b = c[islem]
            if islem == "esit":
                return str(deger) == str(b)
            if islem == "esit_degil":
                return str(deger) != str(b)
            if islem == "icerir":
                return str(b) in str(deger)
            try:
                return float(deger) > float(b) if islem == "buyuk" else float(deger) < float(b)
            except (TypeError, ValueError):
                return False
    return False


def sunucu_kosulu_mu(c):
    return "sunucu" in c or ("adim" in c and "alan" in c)


def _veri_alani(veri, alan):
    if isinstance(veri, list):
        veri = veri[0] if veri and isinstance(veri[0], dict) else {}
    if isinstance(veri, dict):
        return veri.get(alan)
    return veri if alan in ("ham", "cikti") else None


# ---------------------------------------------------------------- yürütme
class AkisYurutucu:
    """Bir sürüm 2 akışı yürütür. Beceri düğümünü ajan çalıştırır (`calistir_beceri`; Kaptan'da teşhis/onarım döngüsü
    oradadır). Onay, bildirim ve yoklama da ajanın geri çağrılarıyla yapılır (inisiyatif ve onay kuralları aynen geçerli).

    Durum (`durum()`): sonuçlar, devredilenler, değişkenler, üst düzey adım girişleri; her üst düzey düğümden sonra
    `kaydet_fn(durum)` çağrılır. `yurut(baslangic=i, sunucular=...)` i. üst düzey düğümden devam eder.
    """

    def __init__(self, akis, envanter, calistir_beceri, onay_iste=None, bildir=None, yokla=None, kontrol=None,
                 durdurma=None, kaydet_fn=None, olay_fn=None, saat=time.monotonic, uyu=time.sleep, akis_dizini=None,
                 girdi=None):
        self.akis = akis
        self.envanter = envanter
        self.calistir_beceri, self.onay_iste, self.bildir, self.yokla = calistir_beceri, onay_iste, bildir, yokla
        self.kontrol, self.durdurma = kontrol, durdurma
        self.kaydet_fn, self.olay_fn = kaydet_fn, olay_fn
        self.saat, self.uyu = saat, uyu
        self.akis_dizini = akis_dizini
        self.kilit = threading.RLock()
        self.sonuclar = {}               # düğüm kimliği -> {"durum", "sunucular": {ad: durum}, "veri": {ad: veri}}
        self.devredilen = {}             # sunucu -> {"neden", "dugum", "ust": üst düzey indeks}
        self.uyarilar = {}               # sunucu -> ["hata_durumunda: devam" adımlarında görülen hatalar]
        self.izler = {}                  # düğüm kimliği -> {"durum", "yineleme", "kol", "sunucular"} (tuval)
        self.degiskenler = {a: copy.deepcopy(x.get("varsayilan")) for a, x in (akis.get("girdi") or {}).items()}
        self.degiskenler.update(girdi or {})
        self.adim_girisi = {}            # üst düzey indeks -> o adıma giren sunucular
        self.ust = 0
        self.bitis = None
        self.durma = None

    # -------------------------------------------------------- yardımcılar
    def _olay(self, tur, metin, **ek):
        if self.olay_fn:
            self.olay_fn(tur, metin, **ek)

    def _iz(self, dugum, **alan):
        with self.kilit:
            self.izler.setdefault(dugum["kimlik"], {"tur": dugum.get("tur", "beceri")}).update(alan)

    def _nokta(self, dugum):
        if self.durdurma is not None and self.durdurma.basili():
            raise AkisDurdu("iptal", "durdurma düğmesi basılı")
        if self.kontrol is not None:
            from .kontrol import IsIptal
            try:
                self.kontrol.nokta(f"{dugum.get('kimlik')} öncesi", self.durdurma)
            except IsIptal as e:
                raise AkisDurdu("iptal", str(e)) from None

    def yerlestir(self, v, degiskenler=None):
        d = self.degiskenler if degiskenler is None else degiskenler
        if isinstance(v, str):
            m = YER_TUTUCU.fullmatch(v)
            if m and m.group(1) in d:
                return copy.deepcopy(d[m.group(1)])
            return YER_TUTUCU.sub(lambda x: str(d.get(x.group(1), x.group(0))), v)
        if isinstance(v, list):
            out = []
            for x in v:
                y = self.yerlestir(x, d)
                out.extend(y if isinstance(y, list) and isinstance(x, str) and YER_TUTUCU.fullmatch(x) else [y])
            return out
        if isinstance(v, dict):
            return {k: self.yerlestir(x, d) for k, x in v.items()}
        return v

    def _sunucu_ozelligi(self, ad, alan):
        s = self.envanter[ad]
        if alan == "grup":
            return ",".join(s.gruplar)
        if alan.startswith("oznitelik."):
            return s.oznitelikler.get(alan.split(".", 1)[1])
        return getattr(s, alan, None)

    def kosul_akis(self, c):
        if "degisken" in c:
            return _karsilastir(self.degiskenler.get(c["degisken"]), c)
        r = self.sonuclar.get(c["adim"])
        if r is None:
            return False
        olcu = c.get("olcu", "durum")
        if olcu == "durum":
            return _karsilastir(r["durum"], c)
        n = sum(1 for d in r["sunucular"].values() if (d == "basarili") == (olcu == "basarili_sayisi"))
        return _karsilastir(n, c)

    def kosul_sunucu(self, c, ad):
        if "sunucu" in c:
            deger = self._sunucu_ozelligi(ad, c["sunucu"])
            if c["sunucu"] == "grup" and "esit" in c:
                return c["esit"] in str(deger).split(",")
            return _karsilastir(deger, c)
        r = self.sonuclar.get(c["adim"]) or {"sunucular": {}, "veri": {}}
        v = _veri_alani(r["veri"].get(ad), c["alan"])
        if v is None and c["alan"] == "durum":          # çıktıda 'durum' alanı yoksa adımın o sunucudaki sonucu
            v = r["sunucular"].get(ad)
        return _karsilastir(v, c)

    def _canli(self, sunucular):
        with self.kilit:
            return [s for s in sunucular if s not in self.devredilen]

    def _dusur(self, ad, neden, dugum):
        with self.kilit:
            self.devredilen.setdefault(ad, {"neden": neden, "dugum": dugum, "ust": self.ust})

    # -------------------------------------------------------- dışa açık
    def durum(self):
        with self.kilit:
            return {"sonuclar": copy.deepcopy(self.sonuclar), "devredilen": dict(self.devredilen),
                    "uyarilar": copy.deepcopy(self.uyarilar),
                    "degiskenler": copy.deepcopy(self.degiskenler), "adim_girisi": dict(self.adim_girisi),
                    "izler": copy.deepcopy(self.izler), "ust": self.ust, "bitis": self.bitis,
                    "durma": self.durma}

    def geri_yukle(self, d):
        self.sonuclar = copy.deepcopy(d.get("sonuclar") or {})
        self.devredilen = dict(d.get("devredilen") or {})
        self.uyarilar = copy.deepcopy(d.get("uyarilar") or {})
        self.degiskenler.update(copy.deepcopy(d.get("degiskenler") or {}))
        self.adim_girisi = {int(k): v for k, v in (d.get("adim_girisi") or {}).items()}
        self.izler = copy.deepcopy(d.get("izler") or {})

    def yurut(self, sunucular, baslangic=0):
        """Üst düzey `baslangic` düğümünden itibaren yürütür. Dönüş: sağ kalan sunucular."""
        kume = list(sunucular)
        bloklar = self.akis["adimlar"]
        try:
            for i in range(baslangic, len(bloklar)):
                self.ust = i
                self.adim_girisi[i] = self._canli(kume)
                if self.kaydet_fn:                 # adım başı da kaydedilir: konsol düşerse bu adımdan sürdürülür
                    self.kaydet_fn(self.durum())
                kume = self._blok([bloklar[i]], kume)
                if self.kaydet_fn:
                    self.kaydet_fn(self.durum())
        except AkisBitti as b:
            self.bitis = {"sonuc": b.sonuc, "mesaj": b.mesaj, "ust": self.ust}
            if self.kaydet_fn:
                self.kaydet_fn(self.durum())
        except AkisDurdu as d:
            self.durma = {"durum": d.durum, "metin": d.metin, "ust": self.ust}
            if self.kaydet_fn:
                self.kaydet_fn(self.durum())
            raise
        return self._canli(kume)

    # -------------------------------------------------------- bloklar
    def _blok(self, blok, kume):
        for d in blok:
            self._nokta(d)
            kume = getattr(self, "_d_" + d.get("tur", "beceri"))(d, kume)
        return kume

    def _d_beceri(self, d, kume):
        hd = self._canli(kume)
        parametreler = self.yerlestir(d.get("parametreler") or {})
        dugum = {**d, "parametreler": parametreler}
        self._iz(d, durum="calisiyor", sunucular=hd)
        adim = self.calistir_beceri(dugum, hd)
        if adim is None:
            self._iz(d, durum="durdu")
            raise AkisDurdu("onay", "onay bekleniyor ya da reddedildi")
        if adim.get("atlandi"):
            self._iz(d, durum="atlandi")
            return kume
        sun = {r["sunucu"]: r["durum"] for r in adim.get("sonuclar", [])}
        veri = {r["sunucu"]: r.get("veri") for r in adim.get("sonuclar", [])}
        with self.kilit:
            onceki = self.sonuclar.get(d["kimlik"])
            if onceki and d.get("_dongu"):            # döngüde: yinelemelerin sonuçları birikir
                sun, veri = {**onceki["sunucular"], **sun}, {**onceki["veri"], **veri}
            self.sonuclar[d["kimlik"]] = {"durum": adim.get("durum"), "sunucular": sun, "veri": veri,
                                          "beceri": d["beceri"], "ozet": adim.get("ozet")}
        dusen = [r for r in adim.get("sonuclar", []) if r["durum"] != "basarili"]
        if d.get("hata_durumunda") == "devam":
            # Sunucu sonraki adımlara girer ama hata kaybolmaz: iş sonunda 'kismi' sayılır ve raporlanır.
            with self.kilit:
                for r in dusen:
                    self.uyarilar.setdefault(r["sunucu"], []).append(
                        f"{d['beceri']} {json.dumps(parametreler, ensure_ascii=False)[:80]}: {r['durum']} - "
                        f"{(r.get('neden') or r.get('stderr') or '').strip()[:160]}")
        if d.get("hata_durumunda", "dusur") == "dusur":
            for r in dusen:
                self._dusur(r["sunucu"], f"{d['beceri']}: {r['durum']} - "
                                         f"{(r.get('sema_hatasi') or r.get('neden') or r.get('stderr') or '').strip()[:200]}",
                            d["kimlik"])
        if adim.get("yerel") and adim.get("durum") != "basarili":
            with self.kilit:
                self.devredilen.setdefault("(yerel)", {"neden": f"{d['beceri']}: {adim.get('aciklama')}",
                                                       "dugum": d["kimlik"], "ust": self.ust})
        self._iz(d, durum=adim.get("durum"), sunucular=hd, yineleme=self.izler.get(d["kimlik"], {}).get("yineleme"))
        return [s for s in kume if s not in {r["sunucu"] for r in dusen} or d.get("hata_durumunda") == "devam"]

    def _d_dal(self, d, kume):
        c = d["kosul"]
        if sunucu_kosulu_mu(c):
            canli = self._canli(kume)
            evet = [s for s in canli if self.kosul_sunucu(c, s)]
            hayir = [s for s in canli if s not in evet]
            self._iz(d, durum="tamam", evet=evet, hayir=hayir)
            self._olay("dal", f"{d['kimlik']}: sunucu koşulu → evet {evet or '-'}, hayır {hayir or '-'}")
            s1 = self._blok(d.get("evet") or [], evet) if evet else []
            s2 = self._blok(d.get("hayir") or [], hayir) if hayir else []
            return [s for s in kume if s in set(s1) | set(s2)]
        sonuc = self.kosul_akis(c)
        self._iz(d, durum="tamam", kol="evet" if sonuc else "hayir")
        self._olay("dal", f"{d['kimlik']}: koşul {'sağlandı → evet' if sonuc else 'sağlanmadı → hayır'} kolu")
        return self._blok(d.get("evet" if sonuc else "hayir") or [], kume)

    def _d_sunucu_dal(self, d, kume):
        r = self.sonuclar.get(d["adim"]) or {"sunucular": {}}
        basarili = [s for s in self._canli(kume) if r["sunucular"].get(s) == "basarili"]
        basarisiz = [s for s, x in r["sunucular"].items() if x != "basarili"]
        self._iz(d, durum="tamam", basarili=basarili, basarisiz=basarisiz)
        self._olay("dal", f"{d['kimlik']}: {d['adim']} sonucuna göre başarılı {basarili or '-'}, başarısız {basarisiz or '-'}")
        s1 = self._blok(d.get("basarili") or [], basarili) if basarili and d.get("basarili") else basarili
        s2 = []
        if basarisiz and d.get("basarisiz"):
            with self.kilit:                      # başarısız kolda bu sunucular yeniden işlenir
                eski = {s: self.devredilen.pop(s) for s in basarisiz if s in self.devredilen}
            s2 = self._blok(d["basarisiz"], basarisiz)
            with self.kilit:
                for s in basarisiz:
                    if s not in s2 and s not in self.devredilen and s in eski:
                        self.devredilen[s] = eski[s]
            if s2:
                self._olay("dal", f"{d['kimlik']}: başarısız kolu bitiren sunucular akışa döndü: {s2}")
        hayatta = set(s1) | set(s2)
        return [s for s in kume if s in hayatta] + [s for s in s2 if s not in kume]

    def _d_dongu(self, d, kume):
        en_cok = int(d["en_cok"])
        govde = [{**x, "_dongu": True} if x.get("tur", "beceri") == "beceri" else x for x in d["govde"]]
        if "liste" in d:
            lst = self.yerlestir(d["liste"])
            lst = lst if isinstance(lst, list) else [lst]
            for i, oge in enumerate(lst[:en_cok], 1):
                self.degiskenler[d["degisken"]] = oge
                self._iz(d, durum="calisiyor", yineleme=i, toplam=len(lst), oge=oge)
                self._olay("dongu", f"{d['kimlik']}: {i}/{len(lst)} {d['degisken']}={oge}")
                kume = self._blok(govde, kume)
                if not self._canli(kume):
                    break
            self._iz(d, durum="tamam")
            return kume
        c = d["kadar"]
        calisan, tamam_toplam, bekleyen = self._canli(kume), [], []
        for i in range(1, en_cok + 1):
            self._iz(d, durum="calisiyor", yineleme=i, toplam=en_cok)
            canli = self._canli(self._blok(govde, calisan))
            if sunucu_kosulu_mu(c):
                bekleyen = [s for s in canli if not self.kosul_sunucu(c, s)]
            else:
                bekleyen = [] if self.kosul_akis(c) else canli
            tamam_toplam += [s for s in canli if s not in bekleyen]
            self._olay("dongu", f"{d['kimlik']}: yineleme {i}/{en_cok}, koşulu bekleyen {bekleyen or 'yok'}")
            if not bekleyen:
                break
            calisan = bekleyen                     # sonraki yinelemede yalnız koşulu sağlamayanlar
        for s in bekleyen:
            self._dusur(s, f"döngü {d['kimlik']}: koşul {en_cok} yinelemede sağlanmadı (üst sınır)", d["kimlik"])
        self._iz(d, durum="sinira_ulasti" if bekleyen else "tamam")
        return [s for s in kume if s in tamam_toplam]

    def _d_paralel(self, d, kume):
        self._iz(d, durum="calisiyor", kol_sayisi=len(d["kollar"]))
        sonuc, hatalar = {}, []

        def kol(i, blok):
            try:
                sonuc[i] = self._blok(blok, list(kume))
            except BaseException as e:  # noqa: BLE001 - kolun hatası birleşmede yeniden fırlatılır
                hatalar.append(e)
        isler = [threading.Thread(target=kol, args=(i, b), daemon=True) for i, b in enumerate(d["kollar"])]
        self._olay("paralel", f"{d['kimlik']}: {len(isler)} kol aynı anda başladı")
        for t in isler:
            t.start()
        for t in isler:
            t.join()
        if hatalar:
            raise hatalar[0]
        self._iz(d, durum="tamam")
        self._olay("paralel", f"{d['kimlik']}: kollar bitti, birleşildi")
        return [s for s in kume if s not in self.devredilen]

    def _d_alt_akis(self, d, kume):
        alt = akis_yukle(d["akis"], self.akis_dizini)
        girdi = {a: copy.deepcopy(x.get("varsayilan")) for a, x in (alt.get("girdi") or {}).items()}
        girdi.update(self.yerlestir(d.get("girdi") or {}))
        self._iz(d, durum="calisiyor", akis=d["akis"])
        self._olay("alt_akis", f"{d['kimlik']}: alt akış {d['akis']} (girdi {json.dumps(girdi, ensure_ascii=False)[:160]})")
        ust_degisken = self.degiskenler
        self.degiskenler = girdi
        onek = d["kimlik"] + "__"
        try:
            blok = json.loads(json.dumps(alt["adimlar"]))
            for x in dugumler(blok):                     # alt akış düğümleri üst akışınkilerle çakışmasın
                x["kimlik"] = onek + x["kimlik"]
                if x.get("tur") == "sunucu_dal" or "adim" in (x.get("kosul") or {}):
                    if x.get("adim"):
                        x["adim"] = onek + x["adim"]
                    if (x.get("kosul") or {}).get("adim"):
                        x["kosul"]["adim"] = onek + x["kosul"]["adim"]
            kume = self._blok(blok, kume)
            cikti = {ust: self.degiskenler.get(a) for ust, a in (d.get("cikti") or {}).items()}
        finally:
            self.degiskenler = ust_degisken
        self.degiskenler.update(cikti)
        self._iz(d, durum="tamam")
        return kume

    def _d_bekle(self, d, kume):
        if "sure_sn" in d:
            self._iz(d, durum="calisiyor", sure_sn=d["sure_sn"])
            self._olay("bekle", f"{d['kimlik']}: {d['sure_sn']} sn bekleniyor")
            bas = self.saat()
            while self.saat() - bas < d["sure_sn"]:
                self._nokta(d)
                self.uyu(min(1.0, d["sure_sn"] - (self.saat() - bas)))
            self._iz(d, durum="tamam")
            return kume
        c = d["kosul"]
        bekleyen = self._canli(kume)
        bas = self.saat()
        aralik = max(1, int(d.get("aralik_sn") or 10))
        tur = 0
        while bekleyen:
            tur += 1
            self._nokta(d)
            r = self.yokla({**c, "parametreler": self.yerlestir(c.get("parametreler") or {})}, bekleyen)
            tamam = [x["sunucu"] for x in (r or {}).get("sonuclar", [])
                     if x["durum"] == "basarili" and _karsilastir(_veri_alani(x.get("veri"), c["alan"]), c)]
            bekleyen = [s for s in bekleyen if s not in tamam]
            self._iz(d, durum="calisiyor", yoklama=tur, bekleyen=bekleyen)
            if not bekleyen or self.saat() - bas >= d["zaman_asimi_sn"]:
                break
            self.uyu(min(aralik, max(0.1, d["zaman_asimi_sn"] - (self.saat() - bas))))
        for s in bekleyen:
            self._dusur(s, f"bekleme {d['kimlik']}: koşul {d['zaman_asimi_sn']} sn içinde sağlanmadı (zaman aşımı)",
                        d["kimlik"])
        self._iz(d, durum="zaman_asimi" if bekleyen else "tamam")
        return [s for s in kume if s not in bekleyen]

    def _d_onay(self, d, kume):
        self._iz(d, durum="bekliyor")
        karar = self.onay_iste(d, self._canli(kume)) if self.onay_iste else "reddedildi"
        self._iz(d, durum=karar)
        self._olay("onay", f"{d['kimlik']}: insan onayı → {karar}")
        if karar == "onaylandi":
            return kume
        if karar == "bekliyor":
            raise AkisDurdu("onay_bekliyor", f"{d['kimlik']}: insan onayı bekleniyor")
        if d.get("reddedilirse"):
            self._blok(d["reddedilirse"], kume)
        raise AkisDurdu("reddedildi", f"{d['kimlik']}: insan onayı vermedi; akış bu noktada durdu")

    def _d_bildirim(self, d, kume):
        self._iz(d, durum="calisiyor")
        r = self.bildir(d, self.durum()) if self.bildir else None
        self._iz(d, durum=(r or {}).get("durum", "atlandi"))
        return kume

    def _d_bitir(self, d, kume):
        self._iz(d, durum="tamam")
        raise AkisBitti(d.get("sonuc", "basarili"), d.get("mesaj", ""))
