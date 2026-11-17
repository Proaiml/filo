"""Kaptan'ın yapılı akış kurucusu (C4). Küçük model için: model akışı tek seferde dev bir JSON olarak yazmaz.

1. Model önce düz adım listesini kurar (kaptan.akis_kur; değişmedi).
2. Kod talepte yapı ipuçlarını arar (onay, bekleme, döngü, sunucu bazında dal, koşul, paralel, alt akış). İpucu yoksa
   hiçbir şey sorulmaz ve akış düz kalır (ek model çağrısı yok).
3. Her ipucu için kod seçenekleri hazırlar, model yalnız dar bir karar verir ("onay hangi adımdan önce?", "hangi
   adımın sonucuna göre, hangi alan, hangi değer?", "hangi adımlar yalnız o sunucularda?"). Tek seçenek varsa model
   çağrılmaz.
4. Kod parçaları birleştirir ve akis_motoru.dogrula ile denetler; geçmezse gerekçe izine yazar ve düz akışa döner.
İnisiyatif düzeyi ve risk kuralları yapılı akışta da aynen geçerlidir (yürütme yine Kaptan._calistir'dan geçer).
"""
import copy
import re

from .ajan_ortak import SISTEM, normal
from .akis_motoru import BICIM, ISLEMLER, SURUM, akis_ozeti, dogrula
from .gateway import sor_json

IPUCLARI = {
    "onay": r"\bonay(imi|ini|ini al|imi al)?\s*(al|iste|alarak|isteyerek)\b|\bbenden onay|\bonaylarsam\b|\bonayimla\b|\bonay(ina|ima) sun",
    "bekle": r"\b\d+\s*(saniye|sn|dakika|dk)\b.{0,20}\bbekle|\bbekle\w*.{0,20}\b\d+\s*(saniye|sn|dakika|dk)\b",
    "dongu": r"\btek tek\b|\bsirayla\b|\bteker teker\b|\bbirer birer\b|\bher bir\w* (icin|ayri)|\bayri ayri\b",
    "sunucu_dal": r"\b(calismayan|durmus|basarisiz|hata veren|erisilemeyen|kurulu olmayan|olmayan|bulunmayan|dolu)\w*\s*(olan)?\w*\s*(sunucu\w*|lar\w*)\b|\b\w+(mayan|meyen)larda\b|\bolanlarda\b|\bolmayanlarda\b",
    "kosul": r"\beger\b|\bolursa\b|\bdegilse\b|\bise\b",
    "paralel": r"\bayni anda\b|\bparalel\b|\bes ?zamanli\b",
}


# Değerleri bilinen çıktı alanları: kod bunlardan hazır koşul seçenekleri üretir (anlamıyla birlikte)
BILINEN_DEGERLER = {"durum": [("active", "çalışıyor"), ("inactive", "çalışmıyor")]}


class Vazgec(Exception):
    pass


def yapi_ipuclari(talep, akis_adlari=()):
    n = normal(talep)
    out = [ad for ad, k in IPUCLARI.items() if re.search(k, n)]
    if "sunucu_dal" in out and "kosul" in out:
        out.remove("kosul")                       # "başarısız olanlarda" sunucu bazında dal; ayrı akış koşulu sorulmaz
    alt = [a for a in akis_adlari if a and (a in n or a.replace("-", " ") in n)]
    if alt:
        out.insert(0, "alt_akis")
    return out, alt


def _secenek(dugumler, filtre=lambda d: True):
    return [d for d in dugumler if d.get("tur", "beceri") == "beceri" and filtre(d)]


def _satir(d):
    return f"{d['kimlik']}: {d['beceri']} {d.get('parametreler') or ''}"


def _sec(model, talep, iz, soru, secenekler, etiket, coklu=False, yok=True):
    """Model seçeneklerden birini (ya da birkaçını) seçer. Seçenek kimlikleri dışında cevap reddedilir."""
    kimlikler = [x[0] for x in secenekler]
    if not coklu and len(kimlikler) == 1 and not yok:
        iz.append({"soru": f"{etiket} (kod)", "denemeler": [], "sonuc": kimlikler[0], "kod_notu": "tek seçenek: model sorulmadı"})
        return kimlikler[0]
    se = kimlikler + (["hicbiri"] if yok else [])
    metin = (f"Talep: \"{talep}\"\n{soru}\nSeçenekler:\n" + "\n".join(f"- {k}: {a}" for k, a in secenekler)
             + ("\n- hicbiri: gerekmiyor" if yok else "") + "\n"
             + ('JSON: {"secim": ["<seçenek>", ...]}' if coklu else 'JSON: {"secim": "<seçenek>"}'))

    def dogrula_(v):
        s = v.get("secim")
        if coklu:
            s = s if isinstance(s, list) else [s]
            s = [str(x).strip() for x in s if str(x).strip()]
            if "hicbiri" in s:
                return [], None
            yabanci = [x for x in s if x not in kimlikler]
            if yabanci or not s:
                return None, f"yalnız şunlardan seç: {se}"
            return s, None
        s = str(s or "").strip()
        return (s, None) if s in se else (None, f"şunlardan biri: {se}")
    out = sor_json(model, SISTEM, metin, dogrula_, iz=iz, etiket=etiket)[0]
    if out is None or out == "hicbiri" or out == []:
        raise Vazgec(etiket)
    return out


def _bul(blok, kimlik):
    for i, d in enumerate(blok):
        if d.get("kimlik") == kimlik:
            return i
    return None


def yapi_kur(kaptan, talep, akis, hedef):
    """Düz akıştan (ve talepten) yapılı akış. İpucu yoksa ya da yapı doğrulanamazsa None (düz akış kalır)."""
    from .kaptan import akis_listesi
    katalog, k = kaptan.motor.katalog, kaptan.kayit
    iz, model = k.gerekce, kaptan.model
    try:
        adlar = [a["ad"] for a in akis_listesi(kaptan.akis_dizini)]
    except OSError:
        adlar = []
    ipucu, alt_adlar = yapi_ipuclari(talep, adlar)
    if not ipucu or model is None:
        return None
    n = normal(talep)
    blok = [{"kimlik": f"a{i}", "tur": "beceri", "beceri": a["beceri"], "parametreler": copy.deepcopy(a["parametreler"]),
             **({"kimlik_calistirma": a["kimlik_calistirma"]} if a.get("kimlik_calistirma") else {})}
            for i, a in enumerate(akis["adimlar"], 1)]
    notlar = []
    sayac = [0]

    def yeni_kimlik(on):
        sayac[0] += 1
        return f"{on}{sayac[0]}"

    def uzak(d):
        return katalog[d["beceri"]]["tur"] != "yerel"

    def degistiren(d):
        return katalog.etkin_risk(katalog[d["beceri"]], d.get("parametreler") or {})[0] >= 2

    for tur in ipucu:
        try:
            if tur == "alt_akis":
                ad = alt_adlar[0]
                cevap = _sec(model, talep, iz, f"Talep kayıtlı '{ad}' akışını çalıştırmak istiyor mu?",
                             [("evet", f"'{ad}' akışı bir adım olarak çalışsın"), ("hayir", "hayır")], "alt akış", yok=False)
                if cevap != "evet":
                    raise Vazgec("alt akış")
                from .akis_motoru import akis_yukle
                alt = akis_yukle(ad, kaptan.akis_dizini)
                alt_beceriler = {d.get("beceri") for d in alt.get("adimlar", [])}
                kalan = [d for d in blok if not uzak(d) or d["beceri"] not in alt_beceriler]
                ilk_yerel = next((i for i, d in enumerate(kalan) if not uzak(d)), len(kalan))
                kalan.insert(ilk_yerel, {"kimlik": yeni_kimlik("alt"), "tur": "alt_akis", "akis": ad, "girdi": {}})
                blok = kalan
                notlar.append(f"alt akış: {ad}")
            elif tur == "onay":
                aday = _secenek(blok, degistiren) or _secenek(blok, uzak)
                if not aday:
                    raise Vazgec("onay")
                hedef_k = _sec(model, talep, iz, "Talep insan onayını hangi adımdan ÖNCE istiyor?",
                               [(d["kimlik"], _satir(d)) for d in aday], "onay adımı", yok=False)
                i = _bul(blok, hedef_k)
                mesaj = f"{blok[i]['beceri']} adımı çalışsın mı? (talep: {talep[:150]})"
                dugum = {"kimlik": yeni_kimlik("onay"), "tur": "onay", "mesaj": mesaj}
                eposta = next((d for d in blok if d.get("beceri") == "eposta_gonder"), None)
                if eposta and eposta["parametreler"].get("alici"):
                    # Reddedilirse istenen bildirim yine gider: ne yapılacaktı, neden yapılmadı (kod ekler, model değil)
                    dugum["reddedilirse"] = [{"kimlik": yeni_kimlik("bil"), "tur": "bildirim", "alici": eposta["parametreler"]["alici"],
                                              "konu": f"Filo: onay verilmedi, {blok[i]['beceri']} çalışmadı"}]
                blok.insert(i, dugum)
                notlar.append(f"onay: {hedef_k} öncesi")
            elif tur == "bekle":
                m = re.search(r"\b(\d+)\s*(saniye|sn|dakika|dk)\b", n)
                sure = int(m.group(1)) * (60 if m.group(2) in ("dakika", "dk") else 1)
                aday = [d for d in blok[:-1] if d.get("tur", "beceri") == "beceri"]
                if not aday:
                    raise Vazgec("bekle")
                sonra = _sec(model, talep, iz, f"Talep {sure} sn beklemeyi hangi adımdan SONRA istiyor?",
                             [(d["kimlik"], _satir(d)) for d in aday], "bekleme adımı", yok=False)
                blok.insert(_bul(blok, sonra) + 1, {"kimlik": yeni_kimlik("bekle"), "tur": "bekle", "sure_sn": sure})
                notlar.append(f"bekle: {sure} sn ({sonra} sonrası)")
            elif tur == "dongu":
                aday = [(d, a, v) for d in _secenek(blok, uzak) for a, v in (d.get("parametreler") or {}).items()
                        if isinstance(v, list) and len(v) >= 2]
                if not aday:
                    raise Vazgec("döngü")
                secim = _sec(model, talep, iz, "Talep hangi adımın listedeki HER öğe için ayrı ayrı (sırayla) çalışmasını istiyor?",
                             [(f"{d['kimlik']}.{a}", f"{d['beceri']}, {a} = {v}") for d, a, v in aday], "döngü")
                d, a, v = next(x for x in aday if f"{x[0]['kimlik']}.{x[1]}" == secim)
                devam = bool(re.search(r"devam et|digerlerine (gec|devam)|durma\b|atla", n))
                govde = {**d, "parametreler": {**d["parametreler"], a: ["{oge}"]},
                         **({"hata_durumunda": "devam"} if devam else {})}
                i = _bul(blok, d["kimlik"])
                blok[i] = {"kimlik": yeni_kimlik("dongu"), "tur": "dongu", "degisken": "oge", "liste": list(v),
                           "en_cok": len(v), "govde": [govde]}
                notlar.append(f"döngü: {d['beceri']} her {a} öğesi için" + (" (hata olsa da sonrakine geçer)" if devam else ""))
            elif tur in ("sunucu_dal", "kosul"):
                if not any(degistiren(d) for d in _secenek(blok, uzak)[1:]):
                    # Yalnız okuyup raporlayan akışta (ör. "başarısız olanları bildir") dal gerekmez: rapor zaten
                    # sunucu başına sonucu gösterir. Model sorulmaz.
                    raise Vazgec(tur)
                aday = _secenek(blok, uzak)[:-1] or _secenek(blok, uzak)
                ref = _sec(model, talep, iz, "Talepteki ayrım hangi adımın sonucuna göre yapılıyor?",
                           [(d["kimlik"], _satir(d)) for d in aday], "koşul: adım")
                rd = blok[_bul(blok, ref)]
                sema = (katalog[rd["beceri"]].get("cikti") or {}).get("alanlar") or {}
                alanlar = [("sonuc", "adımın o sunucudaki sonucu (basarili / basarisiz)")] + \
                          [(x, f"çıktı alanı '{x}'") for x in sema]
                # Değerleri bilinen alanlar için kod hazır koşul seçenekleri sunar; küçük model serbest yazınca
                # anlamı ters çevirebiliyor (duman koşusu A01: "çalışmayanlarda" için "durum ≠ inactive" yazdı).
                hazir = [("sonuc_basarisiz", "adım bu sunucuda BAŞARISIZ oldu", {"alan": "sonuc", "islem": "esit", "deger": "basarisiz"}),
                         ("sonuc_basarili", "adım bu sunucuda başarılı oldu", {"alan": "sonuc", "islem": "esit", "deger": "basarili"})]
                for alan, degerler in BILINEN_DEGERLER.items():
                    if alan in sema:
                        for dg, anlam in degerler:
                            hazir.append((f"{alan}_{dg}", f"{alan} = {dg} ({anlam})", {"alan": alan, "islem": "esit", "deger": dg}))
                            hazir.append((f"{alan}_degil_{dg}", f"{alan} {dg} DEĞİL (yani {anlam} değil)",
                                          {"alan": alan, "islem": "esit_degil", "deger": dg}))
                secim = _sec(model, talep, iz, f"Adım {ref} ({rd['beceri']}) sonrasında talepteki ayrım hangi sunucuları seçiyor? "
                                               "Talepteki işi (ör. yeniden başlatma) GÖRECEK sunucuların koşulunu seç.",
                             [(x[0], x[1]) for x in hazir] + [("diger", "başka bir koşul (alan ve değeri ayrıca yazılacak)")],
                             "koşul: seçenek", yok=False)
                c = next((x[2] for x in hazir if x[0] == secim), None)
                metin = (f"Talep: \"{talep}\"\nAdım {ref} ({rd['beceri']}) sonrasında sunucular bir koşula göre ayrılıyor. "
                         f"Koşulu yaz. Alan seçenekleri: {[x[0] for x in alanlar]}. İşlem: {list(ISLEMLER)}. Değer: talepteki "
                         "anlamın karşılığı (servis durumu için active / inactive; sonuç için basarili / basarisiz).\n"
                         'JSON: {"alan": "...", "islem": "...", "deger": "..."}')

                def dk(v):
                    al, isl, dg = str(v.get("alan", "")).strip(), str(v.get("islem", "")).strip(), v.get("deger")
                    if al not in [x[0] for x in alanlar]:
                        return None, f"alan şunlardan biri: {[x[0] for x in alanlar]}"
                    if isl not in ISLEMLER:
                        return None, f"işlem şunlardan biri: {list(ISLEMLER)}"
                    if dg in (None, ""):
                        return None, "değer boş"
                    if al == "sonuc" and str(dg) not in ("basarili", "basarisiz"):
                        return None, "sonuç değeri basarili ya da basarisiz"
                    if isl in ("buyuk", "kucuk"):
                        try:
                            dg = float(dg) if "." in str(dg) else int(dg)
                        except ValueError:
                            return None, "büyük/küçük için sayı yaz"
                    return {"alan": al, "islem": isl, "deger": dg}, None
                if c is None:
                    c = sor_json(model, SISTEM, metin, dk, iz=iz, etiket="koşul: alan ve değer")[0]
                if not c:
                    raise Vazgec("koşul")
                # Yalnız sunucu adımları kola girebilir: dönüştürme ve e-posta herkes için çalışır (duman koşusu A01:
                # e-posta dalın içine alınmıştı, koşul sağlanmasa rapor gitmeyecekti).
                sonrakiler = [d for d in blok[_bul(blok, ref) + 1:] if d.get("tur", "beceri") == "beceri" and uzak(d)]
                if not sonrakiler:
                    raise Vazgec("koşul")
                kollar = _sec(model, talep, iz, "Hangi adımlar YALNIZ koşulu sağlayan sunucularda (ya da koşul doğruysa) "
                                                "çalışmalı? Diğer adımlar herkes için çalışır.",
                              [(d["kimlik"], _satir(d)) for d in sonrakiler], "koşul: kol", coklu=True)
                kol = [d for d in blok if d.get("kimlik") in kollar]
                blok = [d for d in blok if d.get("kimlik") not in kollar]
                i = _bul(blok, ref) + 1
                if c["alan"] == "sonuc" and tur == "sunucu_dal":
                    basarisiz = (c["deger"] == "basarisiz") == (c["islem"] == "esit")
                    dugum = {"kimlik": yeni_kimlik("sdal"), "tur": "sunucu_dal", "adim": ref,
                             "basarili": [] if basarisiz else kol, "basarisiz": kol if basarisiz else []}
                elif c["alan"] == "sonuc":
                    dugum = {"kimlik": yeni_kimlik("dal"), "tur": "dal", "kosul": {"adim": ref, "olcu": "durum",
                             c["islem"] if c["islem"] in ("esit", "esit_degil") else "esit": c["deger"]}, "evet": kol, "hayir": []}
                else:
                    kosul = {"adim": ref, "alan": c["alan"], c["islem"]: c["deger"]}
                    if tur == "kosul":                  # akış düzeyi: alanın değeri bütün sunucularda değil, adım düzeyinde
                        kosul = {"adim": ref, "alan": c["alan"], c["islem"]: c["deger"]}
                    dugum = {"kimlik": yeni_kimlik("dal"), "tur": "dal", "kosul": kosul, "evet": kol, "hayir": []}
                blok.insert(i, dugum)
                notlar.append(f"{'sunucu bazında dal' if tur == 'sunucu_dal' else 'koşul'}: {ref} → {kollar}")
            elif tur == "paralel":
                aday = _secenek(blok, uzak)
                if len(aday) < 2:
                    raise Vazgec("paralel")
                sec = _sec(model, talep, iz, "Hangi adımlar birbirinden bağımsız ve AYNI ANDA çalışmalı? (en az iki)",
                           [(d["kimlik"], _satir(d)) for d in aday], "paralel kollar", coklu=True)
                if len(sec) < 2:
                    raise Vazgec("paralel")
                idx = sorted(_bul(blok, x) for x in sec)
                if idx != list(range(idx[0], idx[0] + len(idx))):
                    iz.append({"soru": "paralel (kod)", "denemeler": [], "sonuc": sec,
                               "kod_notu": "paralel adımlar ardışık değil; aradaki adımın sırası bozulmasın diye paralel kurulmadı"})
                    raise Vazgec("paralel")
                kollar = [[blok[i]] for i in idx]
                blok = blok[:idx[0]] + [{"kimlik": yeni_kimlik("par"), "tur": "paralel", "kollar": kollar}] + blok[idx[-1] + 1:]
                notlar.append(f"paralel: {sec}")
        except Vazgec:
            notlar.append(f"{tur}: model yapı gerekmediğini söyledi ya da seçemedi; atlandı")
    yapili = {"bicim": BICIM, "surum": SURUM, "talep": talep, "girdi": {},
              "hedef_secici": (hedef or {}).get("secici"), "adimlar": blok}
    if all(d.get("tur", "beceri") == "beceri" for d in blok):
        iz.append({"soru": "akış yapısı (kod)", "denemeler": [], "sonuc": None,
                   "kod_notu": "ipuçları: " + ", ".join(ipucu) + "; " + "; ".join(notlar) + " → düz akış"})
        return None
    hatalar = dogrula(yapili, katalog, kaptan.akis_dizini)
    if hatalar:
        iz.append({"soru": "akış yapısı (kod)", "denemeler": [], "sonuc": None,
                   "kod_notu": "yapı doğrulanamadı, düz akış kullanılıyor: " + "; ".join(hatalar[:4])})
        return None
    iz.append({"soru": "akış yapısı (kod)", "denemeler": [], "sonuc": akis_ozeti(yapili),
               "kod_notu": "kod birleştirdi ve doğruladı: " + "; ".join(notlar)})
    k.olay("yapi", f"yapılı akış: {akis_ozeti(yapili)}")
    return yapili
