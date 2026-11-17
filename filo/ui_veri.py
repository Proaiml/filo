"""Konsolun Yama, Politikalar ve Uyum sayfalarının veri uçları (D4). Yürütme bu modülde yoktur: sayfalar işleri
Kalfa'nın "beceriden başla" yolundan (`/api/kalfa/dogrudan` + `/api/is/yurut`) başlatır; plan, onay, kuru çalıştırma,
denetim izi aynı motordan geçer. Burada yalnız okuma ve ayar kaydı vardır."""
import json

from . import durum, duzelt, uyum as uyum_m, yama as yama_m, yazilim_politikasi as yp


def _oku(yol, bos):
    try:
        return json.loads(yol.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return bos


def _linux(env):
    return [s.ad for s in env.sunucular.values() if s.os == "linux"]


def _gecmis(beceriler, n=40):
    out = []
    for v in reversed(duzelt.kayitlar(beceri=beceriler)):
        out.append({"zaman": v.get("zaman"), "is": v.get("is"), "beceri": v.get("beceri"), "sunucu": v.get("sunucu"),
                    "eylemler": [{"aciklama": duzelt.aciklama(e), "durum": e.get("durum")} for e in v.get("eylemler", [])],
                    "paketler": v.get("paketler"), "politika": v.get("politika"), "kural_seti": v.get("kural_seti"),
                    "geri_alindi": v.get("geri_alindi"), "geri_alinabilir": bool(v.get("geri"))})
        if len(out) >= n:
            break
    return out


def _kapsam(env, secici):
    try:
        return env.dondur(secici)["sunucular"] if secici else []
    except Exception:  # noqa: BLE001
        return []


def yama(env):
    pol = yama_m.politikalar()
    return {"politikalar": [{"ad": a, **p, "sunucular": _kapsam(env, p.get("hedef"))} for a, p in sorted(pol.items())],
            "durum": _oku(yama_m.yama_sonuc() / "durum.json", {}), "uyum": _oku(yama_m.yama_sonuc() / "uyum.json", {}),
            "gecmis": _gecmis(["yama_uygula", "yama_geri_al"]), "sunucular": _linux(env)}


def politikalar(env):
    from .teslim import POLITIKA
    teslim = _oku(POLITIKA, {}).get("profiller", {})
    pol = yp.politikalar()
    return {"politikalar": [{"ad": a, **p, "sunucular": sorted({x for s in p.get("atamalar", []) for x in _kapsam(env, s)}),
                             "teslim_profilleri": [k for k, v in teslim.items() if v.get("politika") == a]}
                            for a, p in sorted(pol.items())],
            "sapma": _oku(durum.sonuc_yolu("politika", "sapma.json"), {}), "gecmis": _gecmis(["yazilim_politikasi_uygula"]),
            "sunucular": _linux(env)}


def uyum(env):
    k = uyum_m.kayit()
    kosular = []
    if uyum_m.uyum_sonuc().exists():
        for p in sorted(uyum_m.uyum_sonuc().glob("2*.json"), reverse=True)[:20]:
            v = _oku(p, {})
            s = v.get("sunucular", {})
            kosular.append({"dosya": p.name, "kural_seti": v.get("kural_seti"), "zaman": v.get("zaman"),
                            "sunucu": len(s), "ortalama": round(sum(x["puan"] for x in s.values()) / len(s)) if s else None,
                            "ihlal": sum(x["ihlal"] for x in s.values())})
    return {"kural_setleri": [{"ad": a, **x} for a, x in sorted((k.get("kural_setleri") or {}).items())],
            "istisnalar": k.get("istisnalar", []), "son": _oku(uyum_m.uyum_sonuc() / "son.json", {}), "kosular": kosular,
            "goruntuler": durum.goruntu_listesi(), "gecmis": _gecmis(["uyum_duzelt"]), "sunucular": _linux(env)}


def goruntu_fark(a, b):
    ga, gb = durum.goruntu_oku(a), durum.goruntu_oku(b)
    f = durum.karsilastir(ga, gb)
    return {"a": {"kimlik": a, "sunucu": ga["sunucu"], "zaman": ga["zaman"]},
            "b": {"kimlik": b, "sunucu": gb["sunucu"], "zaman": gb["zaman"]}, "fark": f, "metin": durum.fark_metni(f, 200)}


def kaydet(yol, g, env):
    kim = "web:operatör"
    if yol == "/api/yama/politika":
        ad = str(g.get("ad") or "").strip()
        if not ad or not all(c.isalnum() or c == "-" for c in ad):
            raise ValueError("politika adı harf, rakam ve tire olmalı")
        kayit, degisti = yama_m.politika_kaydet(ad, g.get("politika") or {}, kim, env)
        return {"ad": ad, "surum": kayit["surum"], "degisti": degisti}
    if yol == "/api/yazilim-politikasi":
        ad = str(g.get("ad") or "").strip()
        if not ad or not all(c.isalnum() or c == "-" for c in ad):
            raise ValueError("politika adı harf, rakam ve tire olmalı")
        kayit, degisti = yp.politika_kaydet(ad, g.get("politika") or {}, kim, env, "konsoldan düzenlendi")
        return {"ad": ad, "surum": kayit["surum"], "degisti": degisti}
    if yol == "/api/uyum/istisna":
        if g.get("kural_seti") not in uyum_m.kural_setleri():
            raise ValueError("kural seti yok")
        _kapsam_dogrula(env, g.get("sunucu"))
        return uyum_m.istisna_ekle(g["kural_seti"], g["kural"], g["sunucu"], g.get("gerekce", ""), g.get("bitis") or None, kim)
    if yol == "/api/uyum/kural-seti":
        kayit, degisti = uyum_m.kural_seti_kaydet(g["ad"], g.get("kurallar") or [], g.get("aciklama", ""), kim)
        return {"ad": g["ad"], "surum": kayit["surum"], "degisti": degisti}
    raise KeyError(yol)


def _kapsam_dogrula(env, secici):
    if not secici or not env.dondur(secici)["sunucular"]:
        raise ValueError("istisna seçicisi hiçbir sunucuyu kapsamıyor")
