"""Çalıştırma kimliği (sunucu otomasyonu'daki Runtime User'ın sade hâli): iş bağlantı kullanıcısıyla mı, root olarak mı (sudo), adı
verilen bir kullanıcı olarak mı (sudo -u) çalışacak.

    izinli kimlikler   ayarlar/calistirma_kimlikleri.json: varsayilan + grup + sunucu girişlerinin birleşimi
    sarma              kimlik bağlantı kullanıcısı değilse betik `sudo -n -u <kimlik> sh -s` içine sarılır. Bu sarma
                       taşıyıcıdan bağımsızdır: SSH ve Go ajanı yollarında aynı betik gider (ajan işi bağlantı
                       kullanıcısıyla çalıştırır, kimlik değişimini sudo yapar). `-n`: sudo parola isterse beklemez,
                       hemen hata verir.
    yetki yok          sudo izin vermezse betik 126 ve 'filo-kimlik-reddi' işaretiyle çıkar; yürütücü bunu
                       `yetki_yok` diye sınıflar ve yeniden denemez (yeniden denemek düzeltmez).
"""
import json
import re
import uuid

from . import AYARLAR

KIMLIK_DOSYASI = AYARLAR / "calistirma_kimlikleri.json"
ISARET = "filo-kimlik-reddi"
CIKIS = 126
_AD = re.compile(r"[a-z_][a-z0-9_-]{0,31}")


class KimlikHatasi(ValueError):
    pass


def gecerli_ad(ad):
    return bool(_AD.fullmatch(str(ad or "")))


def _ayar(yol=None):
    try:
        return json.loads((yol or KIMLIK_DOSYASI).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"varsayilan": ["baglanti"]}


def izinli_kimlikler(sunucu, yol=None):
    if sunucu.os == "windows":
        return ["baglanti"]
    a = _ayar(yol)
    out = list(a.get("varsayilan") or ["baglanti"])
    for g in sunucu.gruplar:
        out += a.get("gruplar", {}).get(g, [])
    out += a.get("sunucular", {}).get(sunucu.ad, [])
    return list(dict.fromkeys(out))


def sar(betik, kimlik, sunucu):
    """Betiği çalıştırma kimliğine sarar (Linux). Kimlik yoksa ya da bağlantı kullanıcısıysa betik olduğu gibi döner."""
    if not kimlik or kimlik in ("baglanti", sunucu.kullanici):
        return betik
    if not gecerli_ad(kimlik):
        raise KimlikHatasi(f"geçersiz çalıştırma kimliği: {kimlik!r}")
    sinir = "FILO_KIMLIK_" + uuid.uuid4().hex[:10].upper()
    while sinir in betik:
        sinir = "FILO_KIMLIK_" + uuid.uuid4().hex[:10].upper()
    return (f"_filo_r=$(sudo -n -u {kimlik} -- true 2>&1) || "
            f"{{ printf '%s\\n' \"{ISARET}: {kimlik}: $_filo_r\" >&2; exit {CIKIS}; }}\n"
            f"exec sudo -n -u {kimlik} -- sh -s <<'{sinir}'\n{betik.rstrip(chr(10))}\n{sinir}\n")


def yetki_yok_mu(rc, stderr):
    return rc == CIKIS and ISARET in (stderr or "")


def yetki_nedeni(stderr):
    satir = next((x for x in (stderr or "").splitlines() if ISARET in x), "").split(":", 2)
    kim = satir[1].strip() if len(satir) > 1 else "?"
    neden = satir[2].strip() if len(satir) > 2 else ""
    return f"yetki yok: '{kim}' kimliğiyle çalıştırılamadı (sudo: {neden or 'izin verilmedi'})"


# ---------------------------------------------------------------- talepten kimlik (kod önce, model dar soruyla)
_KALIPLAR = (
    (re.compile(r"\b(root|kok)\s*(olarak|yetkisiyle|yetkisi ile|haklariyla|kullanicisiyla|kullanicisi ile|ile)\b"), "root"),
    (re.compile(r"\bsudo\s*(ile|yla|kullanarak)\b"), "root"),
    (re.compile(r"\b([a-z_][a-z0-9_-]{1,31})\s+kullanici(?:si)?\s*(?:yla|ile|olarak|adina|hesabiyla)\b"), None),
    (re.compile(r"\b([a-z_][a-z0-9_-]{1,31})\s+(?:kullanicisiyla|kullaniciyla|kimligiyle|hesabiyla|olarak calistir)"), None),
)
GENEL = {"bir", "yeni", "bu", "su", "her", "ayni", "baglanti", "kendi", "standart", "sistem", "yerel", "uzak", "farkli",
         "onun", "bunun", "sunun", "benim", "senin", "bizim", "hangi", "baska", "diger"}


def metinden_kimlik(talep):
    """Talepteki çalıştırma kimliği ifadesi ('root olarak', 'webops kullanıcısıyla'): ad | None."""
    from .ajan_ortak import normal
    n = normal(talep)
    for kalip, sabit in _KALIPLAR:
        m = kalip.search(n)
        if not m:
            continue
        if sabit:
            return sabit
        ad = m.group(1)
        if ad in GENEL:
            continue
        return "root" if ad in ("root", "kok") else ad
    return None


IPUCU = re.compile(r"\b(olarak|kullanicisiyla|kullaniciyla|kullanicisi ile|yetkisiyle|kimligiyle|sudo)\b")


def kimlik_sor(model, talep, iz):
    """Talepteki çalıştırma kimliği. Kod çözer; ipucu var ama çözülemezse model dar bir soruya cevap verir.
    Dönüş: None (bağlantı kullanıcısı) ya da kimlik adı. Uydurulmuş ad (talepte geçmeyen) reddedilir."""
    from .ajan_ortak import SISTEM, normal
    from .gateway import sor_json
    k = metinden_kimlik(talep)
    if k:
        if iz is not None:
            iz.append({"soru": "çalıştırma kimliği (kod)", "denemeler": [], "sonuc": {"kimlik": k},
                       "kod_notu": "talepteki kimlik ifadesini kod çözdü; model sorulmadı"})
        return k
    n = normal(talep)
    if model is None or not re.search(r"\b(kullanicisiyla|kullaniciyla|kullanicisi ile|kimligiyle|yetkisiyle)\b", n):
        return None
    metin = (f"Talep: \"{talep}\"\nTalep işin hangi kullanıcı kimliğiyle çalışacağını söylüyor mu? 'root' (kök, sudo), "
             "adı verilen bir kullanıcı ya da 'baglanti' (söylemiyorsa).\nJSON: {\"kimlik\": \"baglanti\" | \"root\" | \"<kullanıcı adı>\"}")

    def dogrula(v):
        x = str(v.get("kimlik", "")).strip().lower()
        if x in ("", "baglanti", "yok"):
            return "baglanti", None
        if not gecerli_ad(x):
            return None, "geçerli bir kullanıcı adı yaz (küçük harf, rakam, - ve _)"
        if x != "root" and x not in n:
            return None, f"'{x}' talepte geçmiyor; talepteki kullanıcı adını ya da 'baglanti' yaz"
        return x, None
    out = sor_json(model, SISTEM, metin, dogrula, iz=iz, etiket="çalıştırma kimliği")[0]
    return None if out in (None, "baglanti") else out
