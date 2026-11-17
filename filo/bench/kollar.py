"""Bench kolları. Her kol bir senaryoyu yürütür ve {"beyan": basarili|kismi|basarisiz, "rapor", "adim", "cagri"} döndürür.

    bos        hiçbir şey yapmaz (hakemin "yapılmamış iş" ile kaldığını sınamak için)
    referans   senaryonun elle yazılmış çözümü (docker exec + SMTP; harness'i kullanmaz)
    yardimsiz  aynı model, yalnız ham araçlar: herhangi bir lab sunucusunda kabuk komutu (SSH, sudo var) ve ham e-posta;
               aynı adım bütçesi. Beceri, şema, onay, hedef dondurma yok.
    kalfa      Kalfa ajanı (beceri kataloğu, bench onay politikası senaryodan)
    kaptan       Kaptan ajanı (aynı; katalog her senaryoda temiz bir kopyadan başlar, değişiklikleri kalıcı olmaz)
"""
import csv
import io
import json
import pathlib
import shutil
import tempfile

from .. import lab, rapor
from ..ajan_ortak import kisa
from ..beceri import SKILLS, Katalog
from ..denetim import Denetim
from ..erisim import Erisilemedi, Iptal, SSHTasiyici, ZamanAsimi
from ..gateway import BaglantiHatasi, sor_json
from ..isler import IsKaydi
from ..motor import BeceriMotoru
from ..politika import Onaylar, Politika
from ..yurutme import Yurutucu


def bos(senaryo, env, model=None, dizin=None):
    return {"beyan": "basarisiz", "rapor": "hiçbir şey yapılmadı", "adim": 0, "cagri": 0}


# ---------------------------------------------------------------- referans
def _komut(r, s):
    k = r["komut"]
    return k.get(s.aile) or k.get("linux") if isinstance(k, dict) else k


def referans(senaryo, env, model=None, dizin=None):
    """Referans çözüm. {"islem": "zaman"} işaretinden sonraki işlemler zaman ilerletilince (zamanlanmış koşu anında)
    yapılır."""
    adimlar = senaryo["referans"]
    i = next((j for j, r in enumerate(adimlar) if r["islem"] == "zaman"), None)
    if i is None:
        return _referans(adimlar, env, len(adimlar))
    once = _referans(adimlar[:i], env, len(adimlar))
    once["_ilerlet"] = lambda: _referans(adimlar[i + 1:], env, 0)
    return once


def _referans(adimlar, env, n):
    ctx = {}
    beyan = "basarili"
    for r in adimlar:
        if r["islem"] in ("kabuk", "topla"):
            ciktilar = {}
            for ad in r["sunucular"]:
                s = env[ad]
                rc, out, err = lab.dexec(s.konteyner, _komut(r, s), zaman_asimi=300)
                ciktilar[ad] = out.strip() if rc == 0 else f"HATA (erişilemedi ya da başarısız): {err.strip()[:200]}"
            if r["islem"] == "topla":
                ctx[r["ad"]] = ciktilar
        elif r["islem"] == "posta":
            veri = ctx.get(r.get("kaynak"), {})
            govde = r.get("govde", "") + "\n" + "\n".join(f"{a}: {v}" for a, v in veri.items())
            ekler = []
            if r.get("ek") == "csv":
                f = io.StringIO()
                w = csv.writer(f, lineterminator="\n")
                w.writerow(["sunucu", "sonuc"])
                for a, v in veri.items():
                    w.writerow([a, v])
                ekler.append(("rapor.csv", f.getvalue(), "text/csv"))
            elif r.get("ek") in ("xml", "html"):
                if r["ek"] == "xml":
                    icerik = "<rapor>" + "".join(f"<sunucu ad='{a}'>{v}</sunucu>" for a, v in veri.items()) + "</rapor>"
                    ekler.append(("rapor.xml", icerik, "application/xml"))
                else:
                    icerik = "<table>" + "".join(f"<tr><td>{a}</td><td>{v}</td></tr>" for a, v in veri.items()) + "</table>"
                    ekler.append(("rapor.html", icerik, "text/html"))
            rapor.eposta_gonder(r["alici"], r.get("konu", "referans"), govde, ekler)
        elif r["islem"] == "lab":
            # Referans çözümün harness dışı yapamadığı laboratuvar işi (ör. Filo ajanını kurmak kapıdan belirteç ister)
            ok, msg = lab.bozukluk(r["sunucu"], r["bozukluk"], None, **{k: v for k, v in r.items()
                                                                       if k not in ("islem", "sunucu", "bozukluk")})
            if not ok:
                beyan = "basarisiz"
        elif r["islem"] == "beyan":
            beyan = r["durum"]
    return {"beyan": beyan, "rapor": "referans çözüm", "adim": n, "cagri": 0}


# ---------------------------------------------------------------- yardımsız (ham araçlar)
YARDIMSIZ_SISTEM = ("Sen bir Linux sunucu yöneticisisin. Görevi araçlarla yaparsın. Her cevabın TEK bir JSON nesnesidir, "
                    "başka metin yazma. Araçlar:\n"
                    '{"arac": "kabuk", "sunucu": "<ad>", "komut": "<sh komutu>"}  sunucuda filo kullanıcısıyla çalışır, '
                    "parolasız sudo vardır\n"
                    '{"arac": "posta", "alici": "<adres>", "konu": "...", "govde": "..."}  e-posta gönderir\n'
                    '{"arac": "bitir", "durum": "basarili" | "kismi" | "basarisiz", "rapor": "<kısa özet>"}  işi bitirir\n')


def yardimsiz(senaryo, env, model, dizin=None, butce=None):
    butce = butce or senaryo.get("adim_butcesi", 14)
    sunucular = ", ".join(f"{s.ad} ({s.aile})" for s in lab.lab_sunuculari(env))
    gecmis = []
    t = SSHTasiyici()
    cagri0 = getattr(model, "cagri", 0)
    for adim in range(1, butce + 1):
        son = "\n".join(gecmis[-8:])
        metin = (f"Görev: {senaryo['talep']}\nSunucular: {sunucular}\nKalan adım: {butce - adim + 1}\n"
                 f"Önceki adımlar ve sonuçları:\n{son or '(yok)'}\nSıradaki eylemin JSON'u:")

        def dogrula(v):
            a = v.get("arac")
            if a == "kabuk" and v.get("sunucu") in env and isinstance(v.get("komut"), str) and v["komut"].strip():
                return v, None
            if a == "posta" and v.get("alici") and isinstance(v.get("govde"), str):
                return v, None
            if a == "bitir" and v.get("durum") in ("basarili", "kismi", "basarisiz"):
                return v, None
            return None, "geçerli bir araç çağrısı değil (kabuk / posta / bitir ve alanları)"
        try:
            v = sor_json(model, YARDIMSIZ_SISTEM, metin, dogrula, onarim=1, etiket="yardimsiz")[0]
        except BaglantiHatasi as e:
            return {"beyan": "basarisiz", "rapor": f"model hatası: {e}", "adim": adim, "cagri": model.cagri - cagri0}
        if v is None:
            gecmis.append(f"{adim}. (geçersiz cevap)")
            continue
        if v["arac"] == "bitir":
            return {"beyan": v["durum"], "rapor": str(v.get("rapor", ""))[:2000], "adim": adim,
                    "cagri": model.cagri - cagri0}
        if v["arac"] == "kabuk":
            try:
                rc, out, err = t.calistir(env[v["sunucu"]], v["komut"], 120)
                sonuc = f"çıkış {rc}; {kisa(out.strip(), 600)}{' | stderr: ' + kisa(err.strip(), 200) if err.strip() else ''}"
            except (Erisilemedi, ZamanAsimi, Iptal) as e:
                sonuc = f"bağlantı/çalıştırma hatası: {e}"
            gecmis.append(f"{adim}. kabuk {v['sunucu']}: {kisa(v['komut'], 200)} -> {sonuc}")
        else:
            try:
                rapor.eposta_gonder(v["alici"], str(v.get("konu", ""))[:200], v["govde"][:20000])
                gecmis.append(f"{adim}. posta {v['alici']}: gönderildi")
            except (rapor.PostaReddi, OSError) as e:
                gecmis.append(f"{adim}. posta {v['alici']}: gönderilemedi ({e})")
    return {"beyan": "basarisiz", "rapor": "adım bütçesi bitti", "adim": butce, "cagri": model.cagri - cagri0}


# ---------------------------------------------------------------- harness'li kollar
BEYAN = {"bitti": "basarili", "kismi": "kismi", "zamanlandi": "basarili", "ertelendi": "kismi"}
SON = ("bitti", "kismi", "basarisiz", "iptal", "devredildi", "beceri_yok", "reddedildi", "hata", "oneri", "zamanlandi",
       "ertelendi")


def _saat(senaryo):
    import datetime
    if not senaryo.get("saat"):
        return datetime.datetime.now
    sabit = {"an": datetime.datetime.fromisoformat(senaryo["saat"])}
    f = lambda: sabit["an"]  # noqa: E731
    f.ayarla = lambda an: sabit.update(an=an)
    return f


def _lab_islemleri(islemler, env):
    for x in islemler or []:
        if x.get("sifirla"):
            lab.sifirla(x["sifirla"])
        elif x.get("komut"):
            lab.dexec(env[x["sunucu"]].konteyner, x["komut"])


def _operator(senaryo, k, sonuc):
    """Bench'te operatörün yaptığı: işi duraklatıp sürdürmek ya da insana devredilen işte düzeltip kararla sürdürmek."""
    import threading
    import time
    from .. import kontrol
    op = senaryo.get("operator")
    if not op:
        return None

    def calis():
        son = time.time() + 600
        kt = kontrol.kontrol(k.kimlik, k)
        if "duraklat_adimda" in op:
            while time.time() < son and k.durum not in SON and not (
                    k.durum == "calisiyor" and len(k.adimlar) >= op["duraklat_adimda"]):
                time.sleep(0.1)
            if k.durum in SON:
                return
            kt.duraklat("bench-operatör", "senaryo: adım sınırında duraklat")
            while time.time() < son and k.durum not in ("duraklatildi",) + SON:
                time.sleep(0.2)
            n = len(k.adimlar)
            time.sleep(op.get("surdur_sn", 2))
            sonuc["duraklatma"] = {"durdu": k.durum == "duraklatildi", "bekleme_sirasinda_yeni_adim": len(k.adimlar) - n}
            kt.surdur("bench-operatör", "senaryo: sürdür")
        if op.get("devir"):
            while time.time() < son and k.durum not in ("devredildi",) + SON:
                time.sleep(0.3)
            if k.durum != "devredildi":
                return
            _lab_islemleri(op["devir"].get("lab"), senaryo["_env"])
            kt.surdur("bench-operatör", op["devir"].get("not", ""), op["devir"].get("karar"))
    th = threading.Thread(target=calis, daemon=True)
    th.start()
    return th


def _ajan_kolu(sinif, senaryo, env, model, dizin):
    from ..zamanli import risk_fn, tanim_yurut
    from ..zamanlayici import Pencereler, Zamanlayici
    gecici = tempfile.mkdtemp(prefix="filo-bench-")
    kat_dizin = shutil.copytree(SKILLS, f"{gecici}/skills", ignore=shutil.ignore_patterns("gecmis"))
    den = Denetim((dizin / f"{senaryo['kimlik']}__{sinif.ad}.denetim.jsonl") if dizin else None)
    katalog = Katalog(pathlib.Path(kat_dizin), denetim=den)
    pol = Politika("bench", bench_kurali=senaryo["onay_politikasi"], denetim=den,
                   onaylar=Onaylar(pathlib.Path(gecici) / "onaylar.json", den))
    saat = _saat(senaryo)
    # Bench'te pencereler senaryodan gelir (yoksa hiç pencere yok): konsolun ayarları ölçümü etkilemez.
    pen = Pencereler(saat=saat, veri={"pencereler": senaryo.get("pencereler", []),
                                      "yasak_politikasi": senaryo.get("yasak_politikasi", "bekle")})
    motor = BeceriMotoru(katalog, env, Yurutucu(env, denetim=den), pol, denetim=den, pencereler=pen)
    akis_dizini = pathlib.Path(gecici) / "akislar"
    akis_dizini.mkdir(parents=True, exist_ok=True)
    for ad, a in (senaryo.get("akislar") or {}).items():
        (akis_dizini / f"{ad}.json").write_text(json.dumps({**a, "ad": ad}, ensure_ascii=False), encoding="utf-8")
    kosular = []
    zm = Zamanlayici(pathlib.Path(gecici) / "zamanlama.json", saat=saat, pencereler=pen, envanter_fn=lambda: env,
                     risk_fn=risk_fn(motor), denetim=den,
                     calistirici=lambda z, an, oo, n, ist=None: kosular.append(tanim_yurut(
                         z, motor, lambda b: model, oo, n, ist, kayit=IsKaydi(f"[zamanlanmış] {z['ad']}", "zamanlayici",
                                                                            None, dizin=dizin or None))) or
                     {"is": kosular[-1].kimlik, "durum": kosular[-1].durum})
    k = IsKaydi(senaryo["talep"], sinif.ad, getattr(model, "spec", None), dizin=dizin or None)
    cagri0 = getattr(model, "cagri", 0)
    # Kaptan'ın inisiyatif düzeyi operatör ayarıdır: senaryo verirse o, yoksa 3 (risk 4 her zaman senaryonun onayına
    # kalır). Kalfa'da düzey yoktur (yalnız hazır beceri; düzey 3+ adımlar onay ister).
    ek = {"zamanlayici": zm}
    if sinif.ad == "kaptan":
        ek.update(akis_dizini=akis_dizini, inisiyatif=senaryo.get("kaptan_inisiyatif", 3),
                  devir_bekle_sn=120 if (senaryo.get("operator") or {}).get("devir") else None)
    ajan = sinif(model, motor, k, **ek)
    sonuc = {}
    senaryo["_env"] = env
    op = _operator(senaryo, k, sonuc)
    try:
        ajan.calistir(senaryo["talep"])
    except Exception as e:  # noqa: BLE001 - kolun çökmesi başarısızlık olarak kaydedilir
        k.hata = f"{type(e).__name__}: {e}"
        k.durum = "hata"
    if op:
        op.join(5)
    son_is = k
    devam_isi = None
    if senaryo.get("devam") and k.devam and k.durum not in ("hata", "beceri_yok"):
        # Kol bitti; operatör ortamı düzeltir ve başarısız adımdan devam ettirir (önceki adımlar yeniden çalışmaz).
        from ..devam import devam_hazirla
        dv = senaryo["devam"]
        try:
            _lab_islemleri(dv.get("lab"), env)
            bas, sun, onceki = devam_hazirla(k.sozluk(), dv.get("adim", 0), dv.get("kapsam", "basarisiz"))
            k2 = IsKaydi(senaryo["talep"], sinif.ad, getattr(model, "spec", None), dizin=dizin or None)
            k2.plan, k2.inisiyatif = json.loads(json.dumps(k.plan)), json.loads(json.dumps(k.inisiyatif))
            k2.ek = {"kaynak_is": k.kimlik, "devam_noktasi": {"adim": dv.get("adim", 0), "kapsam": dv.get("kapsam"),
                                                             "sunucular": sun}}
            if k2.inisiyatif:
                k2.inisiyatif["kararlar"] = []
            sinif(model, motor, k2, **ek).yurut(bas, sun, onceki)
            son_is, devam_isi = k2, {"kimlik": k2.kimlik, "sunucular": sun, "durum": k2.durum}
        except (ValueError, KeyError) as e:
            k.olay("hata", f"adımdan devam kurulamadı: {e}")
    if dizin:
        k.kaydet()

    def ilerlet():
        import datetime
        for an in senaryo.get("zaman_ilerlet") or []:
            t = datetime.datetime.fromisoformat(an)
            if hasattr(saat, "ayarla"):
                saat.ayarla(t)
            zm.tik(t)

    def temizle():
        shutil.rmtree(gecici, ignore_errors=True)
    return {"beyan": BEYAN.get(son_is.durum, "basarisiz"), "rapor": (son_is.rapor or son_is.hata)[:3000],
            "durum": son_is.durum, "adim": len(k.adimlar), "cagri": getattr(model, "cagri", 0) - cagri0, "is": k.kimlik,
            "degisiklik": len(k.degisiklikler), "_ilerlet": ilerlet, "_temizle": temizle,
            "_zamanlamalar": lambda: zm.liste(), "_is_kaydi": k.sozluk(), "_devam": devam_isi,
            "_kosular": lambda: [x.sozluk() for x in kosular], **sonuc}


def kalfa(senaryo, env, model, dizin=None):
    from ..kalfa import Kalfa
    return _ajan_kolu(Kalfa, senaryo, env, model, dizin)


def kaptan(senaryo, env, model, dizin=None):
    from ..kaptan import Kaptan
    return _ajan_kolu(Kaptan, senaryo, env, model, dizin)


KOLLAR = {"bos": bos, "referans": referans, "yardimsiz": yardimsiz, "kalfa": kalfa, "kaptan": kaptan}
MODEL_KOLLARI = ("yardimsiz", "kalfa", "kaptan")
__all__ = ["KOLLAR", "MODEL_KOLLARI", "json"]
