"""Zamanlanmış işin ajanlarla bağlantısı: talepten zamanlama planı, önceden onay, tanımın risk hesabı ve tanımın
yürütülmesi (konsol ve bench aynı yolu kullanır).

Tanım türleri (zamanlayici.py):
    beceri  Kalfa'nın planı: beceri + şemadan geçmiş parametreler + hedef seçici (+ dondurulmuş liste) + biçim/alıcı +
            çalıştırma kimliği. Koşuda model ÇAĞRILMAZ.
    akis    Kaptan'ın planladığı (yapılı) akış + hedef + inisiyatif düzeyi. Koşuda model yalnız hata teşhisi için
            çağrılır (bağlantı yoksa hata insana devredilir).
    talep   Operatörün serbest metni: koşu anında Kalfa ya da Kaptan yeniden planlar.
"""
import re

from .ajan_ortak import normal
from .zamanlayici import ZamanlamaHatasi, okunakli, zamanlama_sor


def zamanlama_plani(model, motor, talep, iz, hedefler):
    """Talepte zamanlama varsa {"zamanlama", "okunakli", "sonraki", "hedef_cozumu", "kacirilan", "yasak_politikasi"}."""
    pen = motor._pencereler()
    zm = zamanlama_sor(model, talep, iz, pen.saat(), pen, motor.envanter, hedefler)
    if not zm:
        return None
    n = normal(talep)
    zm["hedef_cozumu"] = ("calisma_aninda" if re.search(r"calisma aninda|calistigi anda|her seferinde|o anki", n)
                          else "simdi")
    zm["kacirilan"] = "hemen" if re.search(r"kacirilirsa (hemen|yine)|kacirilan.{0,20}hemen", n) else "atla"
    zm["yasak_politikasi"] = pen.varsayilan_politika()
    return zm


def on_onay_al(motor, plan, veren=None):
    """Zamanlanırken önceden onay. Arayüzde operatör işaretler (veren); komut satırında --onayla, bench'te senaryo
    politikası verir. Etkileşimli kipte açık işaret yoksa onay koşu anında istenir."""
    if not plan.get("onay_gerekli"):
        return None
    if veren:
        return veren
    pol = motor.politika
    if pol.kip in ("bench", "komut_satiri"):
        durum, kim, _ = pol.onay({**plan, "on_onay": None, "onay_kimligi": None})
        return kim if durum == "onaylandi" else None
    return None


def zamanlama_raporu(z, plan=None):
    hedef = z.get("dondurulmus_liste")
    s = [f"İş şimdi çalıştırılmadı; zamanlandı: {z['okunakli']} (zamanlanmış iş {z['kimlik']}).",
         "Sonraki 3 çalışma: " + (", ".join(x.replace("T", " ") for x in z.get("sonraki_uc") or []) or "yok"),
         ("Hedef: tanım anında donduruldu: " + ", ".join(hedef)) if z["hedef_cozumu"] == "simdi" and hedef
         else "Hedef: seçici her koşuda yeniden çözülür",
         f"Kaçırılan koşu: {'atlanır' if z['kacirilan'] == 'atla' else 'konsol açılınca hemen çalışır'}; "
         f"yasak pencerede: {dict(bekle='pencere kapanınca çalışır', sor='operatöre sorulur', atla='atlanır')[z['yasak_politikasi']]}."]
    if z.get("onay_gerekli"):
        o = z.get("onay")
        s.append(f"Önceden onay: {o['veren']} ({o['zaman']}, tanım v{o['tanim_surumu']})" if o
                 else "Önceden onay yok: her koşu insan onayı isteyecek.")
    return "\n".join(s)


def risk_fn(motor):
    """Zamanlayıcı için: tanım -> (en yüksek risk, onay gerekir mi, çalışma anındaki hedef adları)."""
    def fn(tanim):
        k, env = motor.katalog, motor.envanter
        hedefler = []
        if tanim.get("hedef_secici"):
            try:
                hedefler = [s.ad for s in env.sec(tanim["hedef_secici"])]
            except ValueError:
                hedefler = []
        if tanim["tur"] == "beceri":
            r = k.etkin_risk(k[tanim["beceri"]], tanim.get("parametreler") or {})[0] if tanim["beceri"] in k else 3
        elif tanim["tur"] == "akis":
            from .akis_motoru import beceri_dugumleri
            r = max([k.etkin_risk(k[d["beceri"]], d.get("parametreler") or {})[0]
                     for d in beceri_dugumleri(tanim["akis"]) if d["beceri"] in k] or [0])
        else:
            r = 3                       # serbest talep: risk koşu anında planlanınca belli olur; temkinli varsayılır
        return r, r >= 3, hedefler
    return fn


def tanim_yurut(z, motor, model_fabrikasi=None, on_onay=None, not_="", istisna=None, kayit=None, zamanlayici=None,
                onay_bekle_sn=None):
    """Zamanlanmış işin bir koşusunu EŞZAMANLI yürütür; iş kaydını döndürür."""
    from .isler import IsKaydi
    from .kalfa import Kalfa
    from .kaptan import Kaptan
    t = z["tanim"]
    hedef = None
    if t.get("hedef_secici") or z.get("hedefler"):
        if z.get("hedef_cozumu") == "simdi" and z.get("hedefler"):
            var = [h for h in z["hedefler"] if h in motor.envanter]
            eksik = [h for h in z["hedefler"] if h not in motor.envanter]
            if eksik:
                not_ = (not_ + "; " if not_ else "") + f"dondurulmuş listedeki şu sunucular artık envanterde yok: {eksik}"
            hedef = {"secici": t.get("hedef_secici"), "sunucular": var, "sayi": len(var),
                     "zaman": z.get("olusturma"), "ozet": "dondurulmus"}
            if not var:
                raise ZamanlamaHatasi("dondurulmuş listedeki sunucuların hiçbiri envanterde yok")
        else:
            hedef = motor.envanter.dondur(t["hedef_secici"])
    talep = f"[zamanlanmış {z['kimlik']}: {okunakli(z['zamanlama'])}] " + (t.get("talep") or t.get("metin") or z["ad"])
    if t["tur"] == "beceri":
        k = kayit or IsKaydi(talep, "kalfa", "zamanlayıcı (model yok)")
        plan = motor.plan(t["beceri"], t.get("parametreler") or {}, hedef if motor.katalog[t["beceri"]]["tur"] != "yerel"
                          else None, k.talep, "zamanlayici", k.kimlik, kimlik=t.get("kimlik"))
        k.plan = {"ana": plan, "bicim": t.get("bicim"), "alici": t.get("alici"), "gerekce": "zamanlanmış iş",
                  "adimlar": [t["beceri"]] + (["sonucu_donustur"] if t.get("bicim") else [])
                  + (["eposta_gonder"] if t.get("alici") else [])}
        k.ek.update(zamanlama=z["kimlik"], zamanlama_notu=not_)
        k.durum_yap("plan_hazir", "zamanlanmış koşu" + (f" ({not_})" if not_ else ""))
        return Kalfa(None, motor, k, on_onay=on_onay, yasak_istisnasi=istisna, zamanlayici=zamanlayici,
                     onay_bekle_sn=onay_bekle_sn).yurut()
    model = model_fabrikasi(t.get("baglanti")) if model_fabrikasi else None
    if t["tur"] == "akis":
        k = kayit or IsKaydi(talep, "kaptan", t.get("baglanti"))
        kap = Kaptan(model, motor, k, inisiyatif=t.get("inisiyatif", 2), on_onay=on_onay, yasak_istisnasi=istisna,
                     onay_bekle_sn=onay_bekle_sn)
        kap.akis_otomatik_kaydet = False
        kap._kayit(talep)
        k.plan = {"akis": t["akis"], "hedef": hedef, "risk": z.get("risk"), "gerekce": "zamanlanmış akış",
                  "adimlar": [d.get("beceri") or d.get("tur") for d in t["akis"].get("adimlar", [])]}
        k.ek.update(zamanlama=z["kimlik"], zamanlama_notu=not_)
        k.durum_yap("plan_hazir", "zamanlanmış koşu")
        return kap.yurut()
    sinif = Kalfa if t.get("ajan", "kalfa") == "kalfa" else Kaptan
    k = kayit or IsKaydi(t["metin"], sinif.ad, t.get("baglanti"))
    a = sinif(model, motor, k, on_onay=on_onay, yasak_istisnasi=istisna, onay_bekle_sn=onay_bekle_sn)
    k.ek.update(zamanlama=z["kimlik"], zamanlama_notu=not_)
    a.planla(t["metin"])
    if k.durum != "plan_hazir":
        return k
    k.plan["simdi_calistir"] = True
    return a.yurut()
