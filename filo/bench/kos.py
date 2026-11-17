"""Bench koşucusu.

    python -m filo bench liste
    python -m filo bench dogrula [--senaryo ...]            her senaryo: referans çözümle GEÇMELİ, boş çözümle KALMALI
    python -m filo bench kos --kol kalfa kaptan yardimsiz --baglanti <ad> [--senaryo ...] [--seviye ...]
    python -m filo bench rapor [--kosu <ad>]

Her senaryo koşusundan önce laboratuvar sıfırlanır (konteynerler imajdan yeniden yaratılır, posta kutusu boşalır),
kurulum bozuklukları konur, parmak izleri alınır, kol çalışır, hakem laboratuvarın gerçek durumuna bakar.
Model kollarını koşmadan önce ısı bekçisinin çalışıyor olması şarttır (results/durum/isi.log son 3 dakikada yazılmış).
Aynı anda tek koşu: koşucu `results/bench/KILIT` dosyasını tutar.
"""
import datetime
import json
import os
import time

from .. import SONUC, lab
from ..envanter import Envanter
from . import hakem
from .kollar import KOLLAR, MODEL_KOLLARI
from .senaryo import bicim_denetle, yukle

BENCH_SONUC = SONUC / "bench"
# Eski sonuç dosyaları yeniden yazılmaz; rapor eski kol adlarını yeni adla okur (Reis → Kaptan, 17 Kasım 2026).
ESKI_KOL_ADLARI = {"reis": "kaptan"}
DOGRULAMA = BENCH_SONUC / "dogrulama.json"


def _kilit():
    BENCH_SONUC.mkdir(parents=True, exist_ok=True)
    k = BENCH_SONUC / "KILIT"
    if k.exists() and time.time() - k.stat().st_mtime < 6 * 3600:
        try:
            sahibi = int(k.read_text(encoding="utf-8").strip() or 0)
        except (OSError, ValueError):
            sahibi = 0
        if lab._surec_canli(sahibi):
            raise RuntimeError(f"başka bir bench koşusu sürüyor (pid {sahibi}, {k})")
    lab.lab_kilidi_al("bench koşusu")          # laboratuvar sınamaları (pytest) aynı anda çalışmasın (D0-b)
    k.write_text(str(os.getpid()), encoding="utf-8")
    return k


AJAN_KURULUMLARI = ("ajan_kur", "ajan_oldur", "ajan_kimlik_sil")


def ajan_kapisi_hazirla(senaryolar):
    """Ajan kuran senaryolar için ajan kapısı: çalışan bir kapı (ör. konsol) varsa o kullanılır, yoksa bench kendi
    kapısını açar. Dönüş: açılan kapı ya da None."""
    if not any(k.get("bozukluk") in AJAN_KURULUMLARI for s in senaryolar for k in s.get("kurulum", [])) and \
            not any(s.get("ajan_kapisi") for s in senaryolar):
        return None
    from ..ajan_istemci import AjanYok, yerel_istek
    try:
        yerel_istek("/yerel/v1/ajanlar", zaman_asimi=3)
        return None
    except AjanYok:
        from ..ajan_kapisi import AjanKapisi
        return AjanKapisi().baslat()


def hazirla(senaryo, env):
    """Sıfırla + kurulum + önce-durum (parmak izi, pid). Dönüş: (parmak izleri, bağlam, envanter) — yeni sunucu açan
    kurulumdan sonra envanter yeniden okunur."""
    lab.sifirla()
    lab.posta_temizle()
    for k in senaryo.get("kurulum", []):
        p = {a: b for a, b in k.items() if a not in ("sunucu", "bozukluk")}
        ok, msg = lab.bozukluk(k["sunucu"], k["bozukluk"], env, **p)
        if not ok:
            raise RuntimeError(f"kurulum başarısız: {k} ({msg})")
        if k["bozukluk"] == "yeni_sunucu":
            env = Envanter()
    ctx = {"pid": {}}
    for o in senaryo["hakem"] + senaryo.get("yasak", []):
        if o["tur"] == "pid_degisti":
            onceki = ctx["pid"].setdefault(o["servis"], {})
            onceki.update(hakem.pidler(env, o["sunucular"], o["servis"]))
    return hakem.parmak_izleri(env), ctx, env


def bir_kosu(senaryo, kol, env, model=None, dizin=None):
    if kol == "yardimsiz" and senaryo.get("yardimsiz") is False:
        return {"senaryo": senaryo["kimlik"], "seviye": senaryo["seviye"], "kol": kol, "uygulanamaz": True,
                "neden": senaryo.get("yardimsiz_neden", "kol için uygulanamaz"), "gecti": False, "zararli_mi": False,
                "zararli": {"yanlis_sunucu": [], "sahte_basari": False, "onaysiz_degisiklik": []}, "olcutler": [],
                "beyan": "-", "adim": 0, "cagri": 0, "sure": 0,
                "zaman": datetime.datetime.now().isoformat(timespec="seconds")}
    once, ctx, env = hazirla(senaryo, env)
    bas = time.time()
    try:
        sonuc = KOLLAR[kol](senaryo, env, model, dizin)
    except Exception as e:  # noqa: BLE001 - kolun çökmesi kayıt altına alınır
        sonuc = {"beyan": "basarisiz", "rapor": f"kol çöktü: {type(e).__name__}: {e}", "adim": 0, "cagri": 0}
    ctx["kol"] = kol
    try:
        time.sleep(1.0)                   # posta Mailpit'e düşsün
        # Zaman ilerletilmeden önceki ölçütler (ör. "bakım penceresinden önce kurulmamış olmalı")
        ara = {}
        for liste, on in ((senaryo["hakem"], "h"), (senaryo.get("yasak", []), "y")):
            for i, o in enumerate(liste):
                if o.get("asama") == "kol_sonrasi":
                    try:
                        ara[f"{on}{i}"] = hakem.olcut(o, env, dict(ctx))
                    except Exception as e:  # noqa: BLE001
                        ara[f"{on}{i}"] = (False, f"hakem hatası: {e}")
        ctx["ara"] = ara
        if senaryo.get("zaman_ilerlet") and sonuc.get("_ilerlet"):
            try:
                sonuc["_ilerlet"]()
            except Exception as e:  # noqa: BLE001 - zamanlanmış koşunun çökmesi kayda geçer
                sonuc["ilerletme_hatasi"] = f"{type(e).__name__}: {e}"
            time.sleep(1.0)
        if sonuc.get("_zamanlamalar"):
            ctx["zamanlamalar"] = sonuc["_zamanlamalar"]()
        ctx["is_kaydi"] = sonuc.get("_is_kaydi")
        ctx["devam"] = sonuc.get("_devam")
        ctx["duraklatma"] = sonuc.get("duraklatma")
        sure = round(time.time() - bas, 1)
        h = hakem.degerlendir(senaryo, env, once, sonuc["beyan"], ctx)
    finally:
        if sonuc.get("_temizle"):
            sonuc["_temizle"]()
    if sonuc.get("_kosular"):
        sonuc["zamanli_kosular"] = [{"kimlik": x["kimlik"], "durum": x["durum"]} for x in sonuc["_kosular"]()]
    temiz = {a: v for a, v in sonuc.items() if not a.startswith("_")}
    return {"senaryo": senaryo["kimlik"], "seviye": senaryo["seviye"], "kol": kol, "sure": sure, **temiz, **h,
            "zaman": datetime.datetime.now().isoformat(timespec="seconds")}


def dogrula(kimlikler=None, ilerle=print):
    env = Envanter()
    senaryolar = yukle(kimlikler)
    if not senaryolar:
        raise RuntimeError("senaryo yok")
    if not lab.lab_var():
        raise RuntimeError("laboratuvar ayakta değil: python -m filo lab kur")
    kilit = _kilit()
    kapi = ajan_kapisi_hazirla(senaryolar)
    sonuc = json.loads(DOGRULAMA.read_text(encoding="utf-8")) if DOGRULAMA.exists() else {}
    try:
        for s in senaryolar:
            bicim = bicim_denetle(s, env)
            if bicim:
                sonuc[s["kimlik"]] = {"gecti": False, "bicim": bicim}
                ilerle(f"{s['kimlik']}: BİÇİM HATASI {bicim}")
                continue
            r = bir_kosu(s, "referans", env)
            b = bir_kosu(s, "bos", env)
            gecti = r["gecti"] and not r["zararli_mi"] and not b["gecti"]
            sonuc[s["kimlik"]] = {"gecti": gecti, "referans": {"gecti": r["gecti"], "zararli": r["zararli"],
                                                               "olcutler": r["olcutler"]},
                                  "bos": {"gecti": b["gecti"], "olcutler": b["olcutler"]},
                                  "zaman": datetime.datetime.now().isoformat(timespec="seconds")}
            ilerle(f"{s['kimlik']:<40} referans {'GEÇTİ' if r['gecti'] else 'KALDI'}"
                   f"{' (ZARARLI)' if r['zararli_mi'] else ''}  boş {'GEÇTİ (hakem zayıf!)' if b['gecti'] else 'kaldı'}"
                   f"  => {'tamam' if gecti else 'SORUN'}")
            if not r["gecti"]:
                ilerle("    referansın tutmayan ölçütleri: " + "; ".join(o["aciklama"] for o in r["olcutler"] if not o["tuttu"]))
            DOGRULAMA.write_text(json.dumps(sonuc, ensure_ascii=False, indent=1), encoding="utf-8")
    finally:
        kilit.unlink(missing_ok=True)
        lab.sifirla()
        lab.lab_kilidi_birak()
        if kapi:
            kapi.durdur()
    return sonuc


def isi_bekcisi_calisiyor():
    log = SONUC / "durum" / "isi.log"
    return log.exists() and time.time() - log.stat().st_mtime < 180


def kos(kimlikler, kollar, baglanti=None, ilerle=print, kosu_adi=None, seviye=None):
    from ..gateway import baglan, isi_bekle
    env = Envanter()
    senaryolar = yukle(kimlikler, seviye)
    if not senaryolar:
        raise RuntimeError("senaryo yok")
    model = None
    if any(k in MODEL_KOLLARI for k in kollar):
        if not isi_bekcisi_calisiyor():
            raise RuntimeError("ısı bekçisi çalışmıyor: önce `python -u tools/isi_bekcisi.py 60` arka planda başlatın")
        model = baglan(baglanti)
    kilit = _kilit()
    kapi = ajan_kapisi_hazirla(senaryolar)
    ad = kosu_adi or datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    dizin = BENCH_SONUC / ad
    dizin.mkdir(parents=True, exist_ok=True)
    (dizin / "kosu.json").write_text(json.dumps({"kollar": kollar, "model": getattr(model, "spec", None),
                                                 "senaryolar": [s["kimlik"] for s in senaryolar]}, ensure_ascii=False),
                                     encoding="utf-8")
    try:
        for s in senaryolar:
            for kol in kollar:
                if model is not None:
                    isi_bekle()
                r = bir_kosu(s, kol, env, model, dizin)
                r["model"] = getattr(model, "spec", None) if kol in MODEL_KOLLARI else None
                with (dizin / "sonuclar.jsonl").open("a", encoding="utf-8") as f:
                    f.write(json.dumps(r, ensure_ascii=False, default=str) + "\n")
                ilerle(f"{s['kimlik']:<40} {kol:<10} {'GEÇTİ' if r['gecti'] else 'kaldı'}"
                       f"{' ZARARLI' if r['zararli_mi'] else ''}  beyan={r['beyan']} adım={r.get('adim')} çağrı={r.get('cagri')}")
    finally:
        kilit.unlink(missing_ok=True)
        lab.sifirla()
        lab.lab_kilidi_birak()
        if kapi:
            kapi.durdur()
    return rapor(ad)


def rapor(kosu=None):
    kosular = sorted(p.parent.name for p in BENCH_SONUC.glob("*/sonuclar.jsonl")) if BENCH_SONUC.exists() else []
    if kosu:
        kosular = [kosu]
    tablo = {}
    for k in kosular:
        yol = BENCH_SONUC / k / "sonuclar.jsonl"
        if not yol.exists():
            continue
        for satir in yol.read_text(encoding="utf-8").splitlines():
            if not satir.strip():
                continue
            r = json.loads(satir)
            if r.get("uygulanamaz"):
                continue                       # kol bu senaryoda uygulanamaz (ör. yardımsız kol Filo ajanı kuramaz)
            r["kol"] = ESKI_KOL_ADLARI.get(r["kol"], r["kol"])
            g = tablo.setdefault((k, r["kol"], r.get("model") or "-", r["seviye"]),
                                 {"n": 0, "gecen": 0, "zararli": 0, "sahte_basari": 0, "yanlis_sunucu": 0, "cagri": 0})
            g["n"] += 1
            g["gecen"] += bool(r["gecti"])
            g["zararli"] += bool(r["zararli_mi"])
            g["sahte_basari"] += bool(r["zararli"]["sahte_basari"])
            g["yanlis_sunucu"] += bool(r["zararli"]["yanlis_sunucu"])
            g["cagri"] += r.get("cagri") or 0
    return [{"kosu": k, "kol": kol, "model": m, "seviye": sv, **g, "cagri": round(g["cagri"] / g["n"], 1)}
            for (k, kol, m, sv), g in sorted(tablo.items())]


def ozet():
    dog = json.loads(DOGRULAMA.read_text(encoding="utf-8")) if DOGRULAMA.exists() else {}
    senaryolar = [{"kimlik": s["kimlik"], "seviye": s["seviye"], "baslik": s["baslik"], "talep": s["talep"],
                   "kurulum": s.get("kurulum"), "kaynak": s.get("kaynak"), "kaynak_turu": s.get("kaynak_turu"),
                   "dogrulama": dog.get(s["kimlik"])} for s in yukle()]
    return {"senaryolar": senaryolar, "sonuclar": rapor()}


def cli(a):
    if a.eylem == "liste":
        env = Envanter()
        for s in yukle(a.senaryo, a.seviye):
            h = bicim_denetle(s, env)
            print(f"{s['kimlik']:<40} {s['seviye']:<6} {s['kaynak_turu']:<11} {'BİÇİM: ' + str(h) if h else ''}")
            print(f"    {s['talep']}")
        return 0
    if a.eylem == "dogrula":
        sonuc = dogrula(a.senaryo)
        sorun = [k for k, v in sonuc.items() if (not a.senaryo or k in a.senaryo) and not v["gecti"]]
        print(f"\n{len(sonuc) - len(sorun)}/{len(sonuc)} senaryo doğrulandı" + (f"; sorunlu: {sorun}" if sorun else ""))
        return 0 if not sorun else 1
    if a.eylem == "kos":
        if not a.kol:
            raise SystemExit("--kol gerekli (ör. --kol kalfa kaptan yardimsiz)")
        satirlar = kos(a.senaryo, a.kol, a.baglanti, kosu_adi=a.kosu, seviye=a.seviye)
    else:
        satirlar = rapor(a.kosu)
    print(f"{'KOŞU':<16} {'KOL':<10} {'MODEL':<22} {'SEVİYE':<7} {'GEÇEN':>6} {'ZARARLI':>8} {'SAHTE':>6} {'ÇAĞRI':>6}")
    for r in satirlar:
        print(f"{r['kosu']:<16} {r['kol']:<10} {r['model']:<22} {r['seviye']:<7} {r['gecen']:>3}/{r['n']:<2} "
              f"{r['zararli']:>8} {r['sahte_basari']:>6} {r['cagri']:>6}")
    return 0
