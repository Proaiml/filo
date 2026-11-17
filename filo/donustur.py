"""Beceriye dönüştürme (B5).

(a) Biten bir işten tek adımda beceri: başarılı bir Kaptan akışı ya da tek seferlik bir betik/komut işi katalogda yeni
    bir beceri olur. Kod parametreleri çıkarır (adımların değerleri üst düzey girdiye taşınır, varsayılan olarak eski değer
    kalır; sunucu adları hedefe döner, beceriye gömülmez), şemayı ve riski kodla üretir (`tanim_dogrula`, `etkin_risk`),
    beceriyi sürüm 1 olarak yazar ve kaynağını (iş kimliği, talep) kaydeder. Etiketler talepten çıkarılır: Kalfa bir
    sonraki benzer talepte beceriyi aday olarak görür.
(b) Düz dil tarifinden taslak: model taslağı yazar; kod tanımı, yer tutucu/girdi tutarlılığını, salt-okur denetimini ve
    riski denetler; risk 2+ ise kuru çalıştırma ve geri alma tanımı zorunludur. Taslak bir sınama sunucusunda kuru
    çalıştırılır (risk 0-1: komutun kendisi + çıktı şeması; risk 2+: kuru komutu). Geçmeyen taslak kataloğa girmez,
    `results/taslaklar/` altında hatasıyla kalır.
"""
import datetime
import json
import re

from . import SONUC
from .ajan_ortak import SISTEM, normal
from .beceri import CIKTI_BICIMLERI, TIPLER, SemaHatasi, cikti_dogrula, parametre_dogrula, risk_sinifla, tanim_dogrula
from .gateway import sor_json

TASLAKLAR = SONUC / "taslaklar"
DURAK = {"sunucu", "sunucular", "sunucularda", "sunucusunda", "adresine", "olarak", "icin", "gonder", "sonucu", "yap",
         "baslayan", "olan", "lerde", "larda", "talep", "filo", "bunu", "sonra", "once", "ile", "veya"}
YER_TUTUCU = re.compile(r"\{([a-z_][a-z0-9_]*)\}")


class DonusturmeHatasi(ValueError):
    pass


def _simdi():
    return datetime.datetime.now().isoformat(timespec="seconds")


def ad_uret(metin, katalog):
    kok = re.sub(r"[^a-z0-9]+", "_", normal(metin)).strip("_")[:40].strip("_") or "yeni_beceri"
    ad, n = kok, 2
    while ad in katalog or (katalog.dizin / ad).exists():
        ad, n = f"{kok}_{n}", n + 1
    return ad


def etiket_cikar(talep, envanter=None, en_cok=8):
    adlar = {normal(a) for a in (envanter.sunucular if envanter else {})}
    sozler = []
    for w in re.findall(r"[a-z0-9_@.-]+", normal(talep)):
        w = w.strip(".-")
        if len(w) < 4 or w in DURAK or "@" in w or w in adlar or re.fullmatch(r"[a-z]{1,3}\d*\*?", w) \
                or w.startswith(("sunucu", "adres")):
            continue
        if w not in sozler:
            sozler.append(w)
    return sozler[:en_cok]


def _alan_kopyala(sema_alani, varsayilan):
    a = {k: v for k, v in sema_alani.items() if k not in ("varsayilan", "zorunlu")}
    a["varsayilan"] = varsayilan
    return a


# ---------------------------------------------------------------- (a) biten işten
def isten_beceri(katalog, envanter, is_, ad=None, baslik=None, degistiren="operatör"):
    """is_: IsKaydi.sozluk() (bitti durumunda). Kaptan akışı → zincir; tek beceri işi → zincir (tek adım + dönüştür +
    e-posta) ya da betik/komut işi → uzak beceri. Dönüş: yazılan tanım."""
    if is_.get("durum") != "bitti":
        raise DonusturmeHatasi("yalnız başarıyla bitmiş bir iş beceriye dönüştürülür (durum: bitti)")
    adimlar = (is_.get("ek") or {}).get("yapilan")
    if not adimlar:                      # Kalfa / operatör işi: çalışmış adımlar iş kaydından
        adimlar = [{"beceri": a["beceri"], "parametreler": a.get("parametreler") or {}}
                   for a in is_.get("adimlar", []) if a.get("durum") == "basarili"
                   and not str(a.get("aciklama") or "").startswith(("teşhis", "gerileme"))]
    if not adimlar:
        raise DonusturmeHatasi("işte beceriye dönüştürülecek başarılı adım yok")
    talep = is_.get("talep", "")
    onarimlar = [a["beceri"] for a in adimlar if a.get("onarim")]
    # Kaptan'ın duruma özgü onarımı (ör. o sunucuda dpkg kesikti → paket_onar) kalıcı adım olmaz: aynı onarım başka bir
    # sunucuda gereksiz ya da zararlı olabilir (17 Kasım'da qwen3:8b koşusunda rhel'de rpm --rebuilddb düştü).
    adimlar = [a for a in adimlar if not a.get("onarim")]
    if not adimlar:
        raise DonusturmeHatasi("işte onarım dışında beceriye dönüştürülecek adım yok")
    tek_betik =len([a for a in adimlar if katalog[a["beceri"]]["tur"] != "yerel"]) == 1 and \
        adimlar[0]["beceri"] in ("betik_calistir", "komut_calistir") and len(adimlar) == 1
    if tek_betik:
        t = _betikten(katalog, envanter, adimlar[0], talep)
    else:
        t = _akistan(katalog, envanter, adimlar, talep)
    if onarimlar:
        t["aciklama"] += (f" Kaynak işte Kaptan duruma özgü onarım yaptı ({', '.join(onarimlar)}); onarım kalıcı adım "
                          "olarak alınmadı: aynı arıza yeniden çıkarsa Kalfa adımı başarısız raporlar, Kaptan onarır.")
    t["ad"] = ad or ad_uret(baslik or talep, katalog)
    t["baslik"] = baslik or f"{talep[:70]}"
    t["kaynak"] = {"tur": "is", "is": is_.get("kimlik"), "ajan": is_.get("ajan"), "talep": talep[:500], "zaman": _simdi()}
    return beceri_yaz(katalog, t, degistiren)


def _akistan(katalog, envanter, adimlar, talep):
    girdi, zincir = {}, []
    for a in adimlar:
        sema = katalog[a["beceri"]].get("girdi") or {}
        p_alt = {}
        for k, v in (a.get("parametreler") or {}).items():
            if k not in sema or k.startswith("_"):
                continue
            if isinstance(v, str) and v.upper() in envanter:
                continue                                  # sunucu adı beceriye gömülmez: hedef çalışma anında verilir
            ad = k if k not in girdi or girdi[k]["varsayilan"] == v else f"{a['beceri']}_{k}"
            if ad not in girdi:
                girdi[ad] = _alan_kopyala(sema[k], v)
            p_alt[k] = "{" + ad + "}"
        zincir.append({"beceri": a["beceri"], **({"parametre": p_alt} if p_alt else {})})
    risk = max(katalog.etkin_risk(katalog[a["beceri"]], a.get("parametreler"))[0] for a in adimlar)
    etiketler = etiket_cikar(talep, envanter)
    for ad, alan in girdi.items():                        # paket/servis adları da etiket: "jq kur" talebi bulsun
        if alan.get("desen") in ("paket", "servis"):
            for v in (alan["varsayilan"] if isinstance(alan["varsayilan"], list) else [alan["varsayilan"]]):
                if str(v) not in etiketler:
                    etiketler.append(str(v))
    return {"surum": 1, "aciklama": f"Kaptan'ın başarıyla bitirdiği akıştan üretildi: {' → '.join(a['beceri'] for a in adimlar)}. "
                                    f"Kaynak talep: {talep[:200]}",
            "etiketler": etiketler, "risk": risk, "tur": "zincir",
            "zaman_asimi": min(1800, sum(int(katalog[a["beceri"]].get("zaman_asimi", 60)) for a in adimlar)),
            "girdi": girdi, "adimlar": zincir, "cikti": {"bicim": "ham"}}


def _betikten(katalog, envanter, a, talep):
    """Tek seferlik betik/komut işi → kendi komutunu taşıyan uzak beceri. Komuttaki mutlak yollar parametre olur."""
    p = a.get("parametreler") or {}
    if a["beceri"] == "betik_calistir":
        metin = katalog.betik_oku(p["betik"])
        cikti = katalog.betik_meta(p["betik"]).get("cikti") or {"bicim": "ham"}
        girdi = {}
        if p.get("argumanlar"):
            girdi["argumanlar"] = {"tip": "liste", "varsayilan": p["argumanlar"], "aciklama": "betik argümanları"}
            metin = "set -- {argumanlar}\n" + metin
    else:
        metin, cikti, girdi = p["komut"], {"bicim": "ham"}, {}
    yollar = []
    for m in re.finditer(r"(?<![\w$])(/[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)+)", metin):
        if m.group(1) not in yollar and not m.group(1).startswith(("/dev/", "/proc/", "/usr/", "/bin/", "/sbin/")):
            yollar.append(m.group(1))
    for i, y in enumerate(yollar[:4], 1):
        alan = "yol" if len(yollar) == 1 else f"yol{i}"
        girdi[alan] = {"tip": "yol", "varsayilan": y, "izinli_onekler": ["/" + y.strip("/").split("/")[0]],
                       "aciklama": f"okunacak yol (ilk değer: {y})"}
        metin = metin.replace(y, "{" + alan + "}")
    risk, _ = risk_sinifla([metin])
    return {"surum": 1, "aciklama": f"Tek seferlik {a['beceri']} işinden üretildi. Kaynak talep: {talep[:200]}",
            "etiketler": etiket_cikar(talep, envanter), "risk": risk, "tur": "uzak", "zaman_asimi": 120,
            "girdi": girdi, "cikti": cikti, "komut": {"linux": metin.rstrip("\n")}}


def beceri_yaz(katalog, t, degistiren="operatör"):
    """Kod denetimi + sürüm 1 olarak yazma. Risk = max(beyan, kod sınıflaması)."""
    h = tanim_dogrula(t)
    if h:
        raise DonusturmeHatasi(f"beceri tanımı geçersiz: {h}")
    t["risk"] = max(int(t.get("risk", 0)), katalog.etkin_risk(t)[0])
    h = tanim_dogrula(t)
    if h:
        raise DonusturmeHatasi(f"risk düzeyi {t['risk']} oldu ama: {h}")
    _yer_tutucu_denetle(t)
    parametre_dogrula(t.get("girdi") or {}, {})        # varsayılanlar şemadan geçmeli
    d = katalog.dizin / t["ad"]
    if d.exists():
        raise DonusturmeHatasi(f"bu adla bir beceri zaten var: {t['ad']}")
    d.mkdir(parents=True)
    t["surum"] = 1
    t["olusturma"] = {"zaman": _simdi(), "olusturan": degistiren}
    (d / "beceri.json").write_text(json.dumps(t, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    katalog.denetim.yaz("beceri_olusturuldu", beceri=t["ad"], surum=1, risk=t["risk"], tur=t["tur"], olusturan=degistiren,
                        kaynak=t.get("kaynak"))
    katalog.yukle()
    return t


def _yer_tutucu_denetle(t):
    girdi = set(t.get("girdi") or {})
    metinler = []
    for kip in ("komut", "kuru", "geri_al"):
        metinler += [v for v in (t.get(kip) or {}).values() if isinstance(v, str)]
    kullanilan = {m for x in metinler for m in YER_TUTUCU.findall(x)} - {"_icerik", "_ozet"}
    for a in t.get("adimlar") or []:
        for v in (a.get("parametre") or {}).values():
            if isinstance(v, str):
                kullanilan |= set(YER_TUTUCU.findall(v))
    tanimsiz = kullanilan - girdi
    if tanimsiz:
        raise DonusturmeHatasi(f"komutta tanımsız yer tutucu: {sorted(tanimsiz)}")
    if t["tur"] in ("uzak", "zincir"):
        bos = girdi - kullanilan
        if bos:
            raise DonusturmeHatasi(f"hiçbir komutta kullanılmayan girdi: {sorted(bos)}")


# ---------------------------------------------------------------- (b) düz dil tarifinden taslak
TASLAK_SORUSU = """Bir sunucu otomasyon becerisi taslağı yaz. Tarif: "{tarif}"
Kurallar:
- Komutlar POSIX sh; ailelere göre "debian", "rhel", "alpine" ya da hepsi için "linux" anahtarı.
- Değişken değerler komutta {{ad}} yer tutucusuyla geçer ve "girdi" içinde tanımlanır (tip: {tipler}).
- Çıktı tercihen anahtar=değer satırları: "cikti": {{"bicim": "anahtar_deger", "alanlar": {{"alan": "metin"}}}}.
- Sunucuda değişiklik yapan komut (yazma, paket, servis) varsa "kuru" (ne değişeceğini gösteren salt-okur komut) ve
  "geri_al" de yaz. Yönetici yetkisi gerekiyorsa "sudo -n" kullan.
- risk: 0 salt-okur, 1 raporlama, 2 geri alınabilir değişiklik, 3 servis/paket, 4 yıkıcı.
JSON: {{"ad": "kucuk_harf_alt_cizgi", "baslik": "...", "aciklama": "...", "etiketler": [...], "risk": 0,
"girdi": {{}}, "cikti": {{...}}, "komut": {{"linux": "..."}}, "kuru": {{}}, "geri_al": {{}}}}"""


def taslak_denetle(katalog, t):
    """Taslak için kod denetimi; (temiz tanım, hatalar)."""
    h = []
    if not isinstance(t, dict):
        return None, ["JSON nesnesi değil"]
    t = {k: t[k] for k in ("ad", "baslik", "aciklama", "etiketler", "risk", "girdi", "cikti", "komut", "kuru", "geri_al",
                           "zaman_asimi") if k in t and t[k] not in (None, {}, [])}
    t["tur"], t["surum"] = "uzak", 1
    t.setdefault("risk", 0)
    t.setdefault("girdi", {})
    t.setdefault("cikti", {"bicim": "ham"})
    if not re.fullmatch(r"[a-z][a-z0-9_]{2,40}", str(t.get("ad", ""))):
        h.append("ad küçük harf, rakam ve alt çizgi olmalı (3-41 karakter)")
    for k, v in (t.get("girdi") or {}).items():
        if not isinstance(v, dict) or v.get("tip", "metin") not in TIPLER:
            h.append(f"girdi {k}: tip {TIPLER} içinden olmalı")
    if (t.get("cikti") or {}).get("bicim") not in CIKTI_BICIMLERI:
        h.append(f"çıktı biçimi {CIKTI_BICIMLERI} içinden olmalı")
    if not isinstance(t.get("komut"), dict) or not t["komut"]:
        h.append("komut tablosu yok")
    else:
        bilinmeyen = set(t["komut"]) - {"debian", "rhel", "alpine", "linux", "windows"}
        if bilinmeyen:
            h.append(f"komut anahtarları debian/rhel/alpine/linux/windows olmalı: {sorted(bilinmeyen)}")
    try:
        t["risk"] = max(int(t.get("risk", 0)), katalog.etkin_risk(t)[0]) if not h else int(t.get("risk", 0))
    except (TypeError, ValueError, KeyError):
        h.append("risk tamsayı olmalı")
    h += tanim_dogrula(t) if not h else []
    if not h:
        try:
            _yer_tutucu_denetle(t)
            parametre_dogrula(t["girdi"], {})
        except (DonusturmeHatasi, SemaHatasi) as e:
            h.append(str(e))
    return t, h


def tariften_taslak(model, katalog, tarif, iz=None):
    """Model taslağı yazar; kod denetler ve hatayla geri sorar (onarım döngüsü). (tanım, kayıt)."""
    def dogrula(v):
        t, h = taslak_denetle(katalog, v)
        if h:
            return None, "; ".join(h)[:600]
        if t["ad"] in katalog:
            return None, f"bu adla beceri var: {t['ad']}; başka ad seç"
        return t, None
    return sor_json(model, SISTEM, TASLAK_SORUSU.format(tarif=tarif, tipler=", ".join(TIPLER)), dogrula, iz=iz,
                    etiket="beceri taslağı", onarim=2)


def kuru_sina(motor, t, sunucu, parametreler=None):
    """Taslağı kataloğa yazmadan bir sınama sunucusunda dener. (geçti mi, sonuç, açıklama)."""
    from .beceri import doldur, komut_sec
    s = motor.envanter[sunucu]
    p = parametre_dogrula(t.get("girdi") or {}, parametreler or {})
    kip = "kuru" if t["risk"] >= 2 else "komut"
    sablon = komut_sec(t.get(kip), s)
    if sablon is None:
        return False, None, f"{s.aile} için {kip} komutu yok"
    betik = doldur(sablon, p, s.os)
    r = motor.yurutucu.yelpaze([s.ad], betik, int(t.get("zaman_asimi", 60)), yeniden_deneme=0, denetle=False)[0]
    if r["durum"] != "basarili":
        return False, r, f"{kip} çalıştırması başarısız: {r['durum']} {(r.get('stderr') or r.get('neden') or '')[:200]}"
    if kip == "komut":
        veri, hata = cikti_dogrula(t.get("cikti"), r["stdout"], p)
        r["veri"] = veri
        if hata:
            return False, r, f"çıktı şemaya uymuyor: {hata}"
    return True, r, f"{kip} çalıştırması {s.ad} üzerinde geçti"


def taslak_kaydet(t, durum, notlar):
    TASLAKLAR.mkdir(parents=True, exist_ok=True)
    yol = TASLAKLAR / f"{t.get('ad', 'taslak')}-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    yol.write_text(json.dumps({"durum": durum, "notlar": notlar, "tanim": t}, ensure_ascii=False, indent=1), encoding="utf-8")
    return yol


def tariften_beceri(model, motor, tarif, sinama_sunucusu, degistiren="operatör", iz=None):
    """Taslak → kod denetimi → kuru çalıştırma → katalog. Dönüş: {"durum": katalogda|taslak, ...}."""
    iz = iz if iz is not None else []
    t, kayit = tariften_taslak(model, motor.katalog, tarif, iz)
    if t is None:
        son = kayit["denemeler"][-1].get("hata") if kayit and kayit.get("denemeler") else "model cevap vermedi"
        yol = taslak_kaydet({"tarif": tarif}, "denetimden_gecmedi", [son])
        return {"durum": "taslak", "neden": f"kod denetiminden geçmedi: {son}", "taslak": str(yol), "iz": iz}
    gecti, r, aciklama = kuru_sina(motor, t, sinama_sunucusu)
    if not gecti:
        yol = taslak_kaydet(t, "kuru_calistirma_gecmedi", [aciklama])
        return {"durum": "taslak", "neden": aciklama, "taslak": str(yol), "tanim": t, "sonuc": r, "iz": iz}
    t["kaynak"] = {"tur": "tarif", "tarif": tarif[:500], "sinama": {"sunucu": sinama_sunucusu, "aciklama": aciklama},
                   "zaman": _simdi()}
    yaz = beceri_yaz(motor.katalog, t, degistiren)
    return {"durum": "katalogda", "tanim": yaz, "sinama": aciklama, "sonuc": r, "iz": iz}
