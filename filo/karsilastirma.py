"""sunucu/akış yolu ile Filo yolu karşılaştırması (konsolun Karşılaştırma sayfası).

sunucu/akış tarafı yalnız `docs/arastirma/07-talep-karsilastirmasi.md` dosyasından okunur (kaynakta olmayan iddia eklenmez).
Filo tarafının sayıları yalnız gerçekten koşulmuş bench sonuçlarından (`results/bench/<koşu>/sonuclar.jsonl`) gelir; o
talebe karşılık gelen senaryo hiç koşulmamışsa "ölçülmedi" yazılır.
"""
import json
import re

from . import ROOT, SONUC

KAYNAK = ROOT / "docs" / "arastirma" / "07-talep-karsilastirmasi.md"
# 07'deki talep → bu talebi laboratuvarda ölçen bench senaryoları (senaryo dosyası adı öneki)
ESLESME = {
    "T1": ["T01", "T03"], "T2": ["T03", "T04", "T09"], "T3": ["O03", "O07", "I06"], "T4": ["O08", "O09", "I09"],
    "T5": ["O01", "I01", "I02", "T06"], "T6": ["I04"], "T7": ["I05", "O04", "O05", "O11", "O12", "I07", "I08"],
    "T8": ["O06", "T08"], "T9": ["T05"], "T10": ["T07"], "T11": ["O01"], "T12": ["I03"], "T13": ["O10"],
}
ESKI_KOL = {"reis": "kaptan"}


def _bolumler(metin):
    out = {}
    for m in re.finditer(r"^## (T\d+)\. (.+?)$(.*?)(?=^## |\Z)", metin, re.M | re.S):
        kod, baslik, govde = m.group(1), m.group(2).strip(), m.group(3)
        alan = {}
        for a in ("talep", "adim_sayisi", "on_hazirlik", "kirildigi_yer", "ajanla_yapilisi", "olculebilir_fark", "forum_kaniti"):
            mm = re.search(rf"^- \*\*{a}:\*\*(.*?)(?=^- \*\*\w+:\*\*|^---|\Z)", govde, re.M | re.S)
            if mm:
                alan[a] = mm.group(1).strip()
        out[kod] = {"kod": kod, "baslik": baslik, **alan}
    return out


def _ozet_tablosu(metin):
    satirlar = []
    blok = re.search(r"## Özet tablosu\s*\n(.*?)(?:\n\n|\n##)", metin, re.S)
    if not blok:
        return satirlar
    for s in blok.group(1).splitlines():
        h = [x.strip() for x in s.strip().strip("|").split("|")]
        if len(h) >= 6 and re.fullmatch(r"T\d+", h[0]):
            satirlar.append({"kod": h[0], "talep": h[1], "sa_adim": h[2], "oo_adim": h[3], "on_hazirlik": h[4], "kirilma": h[5]})
    return satirlar


def olcumler():
    """{senaryo: [{kosu, kol, gecti, zararli, cagri, model}]} bütün koşulardan."""
    out = {}
    d = SONUC / "bench"
    if not d.exists():
        return out
    for p in sorted(d.glob("*/sonuclar.jsonl")):
        for s in p.read_text(encoding="utf-8").splitlines():
            if not s.strip():
                continue
            r = json.loads(s)
            out.setdefault(r["senaryo"], []).append({"kosu": p.parent.name, "kol": ESKI_KOL.get(r["kol"], r["kol"]),
                                                     "gecti": r["gecti"], "zararli": r["zararli_mi"], "cagri": r.get("cagri"),
                                                     "model": r.get("model"), "beyan": r.get("beyan")})
    return out


def karsilastirma():
    if not KAYNAK.exists():
        return {"kaynak": None, "talepler": [], "not": "docs/arastirma/07-talep-karsilastirmasi.md yok"}
    metin = KAYNAK.read_text(encoding="utf-8")
    bol = _bolumler(metin)
    olc = olcumler()
    senaryo_adlari = sorted(olc)
    talepler = []
    for o in _ozet_tablosu(metin):
        b = bol.get(o["kod"], {})
        eslesen = [s for s in senaryo_adlari if any(s.startswith(p + "-") for p in ESLESME.get(o["kod"], []))]
        olcum = {s: olc[s] for s in eslesen}
        talepler.append({**o, "baslik": b.get("baslik"), "ornek_talep": b.get("talep"), "kirildigi_yer_ayrinti": b.get("kirildigi_yer"),
                         "on_hazirlik_ayrinti": b.get("on_hazirlik"), "olculebilir_fark": b.get("olculebilir_fark"),
                         "senaryolar": ESLESME.get(o["kod"], []), "olcum": olcum, "olculdu": bool(olcum)})
    return {"kaynak": str(KAYNAK.relative_to(ROOT)).replace("\\", "/"), "talepler": talepler}
