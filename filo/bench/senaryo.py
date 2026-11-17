"""Senaryo biçimi ve yükleyici.

`bench/<seviye>/<kimlik>.json`:
    {
      "kimlik": "O01-ulasilamayan-sunucuya-kurulum", "seviye": "orta", "baslik": "...",
      "kaynak": "https://community.opentext.com/..."  ya da  "türetildi: docs/arastirma/03-vaka-taslaklari.md O-006",
      "kaynak_turu": "forum" | "taslak" | "turetilmis",
      "talep": "doğal dilde talep",
      "kurulum": [{"sunucu": "PA-DB-01", "bozukluk": "sshd_kapali", ...parametreler}],
      "onay_politikasi": {"varsayilan": "onayla" | "reddet", "beceriler": {"<beceri>": "reddet"}},
      "degisebilir": ["PA-APP-01", ...],     bu sunucular dışında bir değişiklik zararlı sayılır
      "hakem": [ölçütler, bkz. hakem.py],
      "yasak": [ölçütler; biri tutarsa zararlı: onaysız yıkıcı değişiklik],
      "referans": [işlemler, bkz. kollar.py Referans],
      "adim_butcesi": 14
    }
"""
import json

from .. import ROOT
from ..lab import BOZUKLUKLAR

BENCH = ROOT / "bench"
SEVIYELER = ("temel", "orta", "ileri")
HAKEM_TURLERI = ("paket", "servis", "dosya", "dosya_yok", "kullanici", "posta", "posta_csv", "beyan", "pid_degisti", "komut",
                 "zamanlama", "is_kaydi", "posta_yok")
REFERANS_TURLERI = ("kabuk", "topla", "posta", "beyan", "lab", "zaman")
# Üçüncü tur alanları (hepsi isteğe bağlı):
#   "saat": "2026-11-17T15:00"       zamanlayıcı ve pencereler için sahte saat (gerçek bekleme yok)
#   "pencereler": [...]               senaryonun bakım/yasak pencereleri (zamanlayici.Pencereler biçimi)
#   "zaman_ilerlet": ["2026-11-18T02:00"]  kol bittikten sonra zamanlayıcı bu anlarda tetiklenir
#   "akislar": {"ad": {...}}          Kaptan'ın akış dizinine konan kayıtlı sabit akışlar (alt akış senaryoları)
#   "operator": {"duraklat_adimda": 1, "surdur_sn": 2} | {"devir": {"lab": [...], "karar": "...", "not": "..."}}
#   "devam": {"lab": [...], "adim": 0, "kapsam": "basarisiz"}   kol bitince düzeltme + adımdan devam
#   ölçütte "asama": "kol_sonrasi"   ölçüt zaman ilerletilmeden ÖNCE değerlendirilir


def yukle(kimlikler=None, seviye=None):
    out = []
    for p in sorted(BENCH.glob("*/*.json")):
        s = json.loads(p.read_text(encoding="utf-8"))
        s["_dosya"] = str(p.relative_to(ROOT))
        if kimlikler and s["kimlik"] not in kimlikler:
            continue
        if seviye and s["seviye"] != seviye:
            continue
        out.append(s)
    return out


def bicim_denetle(s, envanter):
    """Senaryo dosyasının biçim hataları (boş liste: geçerli)."""
    h = []
    for alan in ("kimlik", "seviye", "baslik", "kaynak", "kaynak_turu", "talep", "kurulum", "onay_politikasi",
                 "degisebilir", "hakem", "referans"):
        if alan not in s:
            h.append(f"eksik alan: {alan}")
    if s.get("seviye") not in SEVIYELER:
        h.append("seviye temel/orta/ileri olmalı")
    if s.get("_dosya") and f"/{s.get('seviye')}/" not in s["_dosya"].replace("\\", "/"):
        h.append("dosya seviyesinin dizininde değil")
    from ..lab import YENI_SUNUCULAR
    for k in s.get("kurulum", []):
        if k.get("bozukluk") not in BOZUKLUKLAR:
            h.append(f"bilinmeyen bozukluk: {k.get('bozukluk')}")
        if k.get("sunucu") not in envanter and k.get("sunucu") not in YENI_SUNUCULAR:
            h.append(f"envanterde olmayan sunucu: {k.get('sunucu')}")
    for x in s.get("degisebilir", []):
        if x not in envanter and x not in YENI_SUNUCULAR:
            h.append(f"degisebilir: envanterde yok: {x}")
    if s.get("kaptan_inisiyatif") is not None and s["kaptan_inisiyatif"] not in (0, 1, 2, 3):
        h.append("kaptan_inisiyatif 0-3 olmalı")
    for o in s.get("hakem", []) + s.get("yasak", []):
        if o.get("tur") not in HAKEM_TURLERI:
            h.append(f"bilinmeyen hakem ölçütü: {o.get('tur')}")
    for r in s.get("referans", []):
        if r.get("islem") not in REFERANS_TURLERI:
            h.append(f"bilinmeyen referans işlemi: {r.get('islem')}")
    if not s.get("hakem"):
        h.append("hakem ölçütü yok")
    if s.get("onay_politikasi", {}).get("varsayilan") not in ("onayla", "reddet"):
        h.append("onay_politikasi.varsayilan onayla/reddet olmalı")
    return h
