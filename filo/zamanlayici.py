"""Zamanlayıcı: tek seferlik ve tekrarlı işler, bakım ve yasak (blackout) pencereleri.

sunucu otomasyonu'daki iş zamanlama / akış otomasyonu'daki Schedules karşılığının sadeleşmiş hâli. Durum dosyadadır:
    results/zamanlama/isler.json   zamanlanmış işler, onayları ve çalışma geçmişi
    ayarlar/pencereler.json        bakım ve yasak pencereleri (sunucu/grup başına, seçici metniyle)
Konsol süreci içinde bir iş parçacığı her `aralik` saniyede `tik()` çağırır. Saat dışarıdan verilir (`saat` işlevi):
testlerde sahte saat kullanılır, gerçek bekleme yoktur.

Zamanlama tanımı (okunaklı; cron isteğe bağlı):
    {"tur": "tek",      "zaman": "2026-11-20T02:00"}
    {"tur": "gunluk",   "saat": "02:00"}
    {"tur": "haftalik", "gunler": ["cumartesi"], "saat": "03:00"}
    {"tur": "aylik",    "gun": 1, "saat": "02:00"}
    {"tur": "cron",     "ifade": "0 2 * * 1-5"}          (dakika saat ayın-günü ay haftanın-günü; 0/7 = pazar)
    {"tur": "pencere",  "pencere": "web-cumartesi"}      (o bakım penceresinin her açılışında)

Pencere:
    {"ad": "web-cumartesi", "tur": "bakim" | "yasak", "kapsam": "grup:web",
     "tekrar": {"tur": "haftalik", "gunler": ["cumartesi"], "baslangic": "02:00", "sure_dk": 240}
             | {"tur": "gunluk", "baslangic": "01:00", "sure_dk": 60}
             | {"tur": "tek", "baslangic": "2026-12-28T00:00", "bitis": "2027-01-02T00:00"}}
Yasak pencerede sunucuyu DEĞİŞTİREN iş (risk ≥ 2) başlamaz. Politika (iş başına): `bekle` (pencere kapanınca başlar),
`sor` (operatöre sorulur; karar verilene kadar bekler), `atla` (bu koşu atlanır). Salt-okur işler yasaktan etkilenmez.

Zamanlanmış iş tanımında açık seçenekler:
    hedef_cozumu   "simdi" (sunucu otomasyonu "Now": liste tanım anında dondurulur) | "calisma_aninda" (seçici her koşuda çözülür)
    kacirilan      "atla" | "hemen"   (konsol kapalıyken geçen koşu)
    yasak_politikasi "bekle" | "sor" | "atla"
Onay gerektiren iş önceden onaylanabilir: onay kimin, ne zaman, hangi tanım SÜRÜMÜ (ve özeti) için verildiği yazılır.
Tanım değişirse sürüm artar ve onay düşer.
"""
import calendar
import copy
import datetime
import hashlib
import json
import re
import threading
import uuid

from . import AYARLAR, SONUC
from .denetim import DENETIM

ZAMANLAMA = SONUC / "zamanlama"
PENCERE_DOSYASI = AYARLAR / "pencereler.json"
GUNLER = ["pazartesi", "sali", "carsamba", "persembe", "cuma", "cumartesi", "pazar"]
GUN_ADI = {"pazartesi": "Pazartesi", "sali": "Salı", "carsamba": "Çarşamba", "persembe": "Perşembe", "cuma": "Cuma",
           "cumartesi": "Cumartesi", "pazar": "Pazar"}
KACIRMA_TOLERANSI = datetime.timedelta(minutes=2)
TR = str.maketrans("çğıöşüÇĞİÖŞÜâîû", "cgiosuCGIOSUaiu")


class ZamanlamaHatasi(ValueError):
    pass


def _n(metin):
    return str(metin).replace("İ", "i").replace("I", "ı").lower().translate(TR)


def _iso(t):
    return t.isoformat(timespec="minutes") if t else None


def _coz_zaman(s):
    if isinstance(s, datetime.datetime):
        return s
    try:
        return datetime.datetime.fromisoformat(str(s).strip().replace(" ", "T"))
    except ValueError:
        raise ZamanlamaHatasi(f"geçersiz tarih-saat: {s!r} (ör. 2026-11-20T02:00)") from None


def _saat(s):
    m = re.fullmatch(r"([01]?\d|2[0-3])[:.]([0-5]\d)", str(s or "").strip())
    if not m:
        raise ZamanlamaHatasi(f"geçersiz saat: {s!r} (ör. 02:00)")
    return int(m.group(1)), int(m.group(2))


def _gun(g):
    g = _n(g).strip()
    if g in GUNLER:               # tam eşleşme önce: "pazar" "pazartesi"nin başı sayılmasın
        return g
    for ad in GUNLER:
        if g == ad or (len(g) >= 3 and ad.startswith(g)):
            return ad
    raise ZamanlamaHatasi(f"geçersiz gün: {g!r} (şunlardan biri: {', '.join(GUNLER)})")


# ---------------------------------------------------------------- cron (isteğe bağlı)
_CRON_SINIR = [(0, 59), (0, 23), (1, 31), (1, 12), (0, 7)]


def _cron_alan(ifade, alt, ust):
    degerler = set()
    for parca in ifade.split(","):
        adim = 1
        if "/" in parca:
            parca, a = parca.split("/", 1)
            if not a.isdigit() or int(a) < 1:
                raise ZamanlamaHatasi(f"cron: geçersiz adım {a!r}")
            adim = int(a)
        if parca == "*":
            b, s = alt, ust
        elif "-" in parca:
            b, s = parca.split("-", 1)
            if not (b.isdigit() and s.isdigit()):
                raise ZamanlamaHatasi(f"cron: geçersiz aralık {parca!r}")
            b, s = int(b), int(s)
        elif parca.isdigit():
            b = s = int(parca)
        else:
            raise ZamanlamaHatasi(f"cron: geçersiz alan {parca!r}")
        if b < alt or s > ust or b > s:
            raise ZamanlamaHatasi(f"cron: {parca!r} {alt}-{ust} aralığında değil")
        degerler |= set(range(b, s + 1, adim))
    return degerler


def cron_coz(ifade):
    alanlar = str(ifade or "").split()
    if len(alanlar) != 5:
        raise ZamanlamaHatasi("cron ifadesi 5 alan olmalı: dakika saat ayın-günü ay haftanın-günü")
    d, s, ag, ay, hg = (_cron_alan(a, *_CRON_SINIR[i]) for i, a in enumerate(alanlar))
    hg = {0 if x == 7 else x for x in hg}
    return {"dakika": d, "saat": s, "ayin_gunu": ag, "ay": ay, "hafta_gunu": hg,
            "ag_yildiz": alanlar[2] == "*", "hg_yildiz": alanlar[4] == "*"}


def _cron_gun_uyar(c, gun):
    if gun.month not in c["ay"]:
        return False
    ag = gun.day in c["ayin_gunu"]
    hg = ((gun.weekday() + 1) % 7) in c["hafta_gunu"]        # cron: 0 = pazar
    if c["ag_yildiz"] or c["hg_yildiz"]:
        return ag and hg
    return ag or hg                                         # klasik cron: ikisi de kısıtlıysa VEYA


# ---------------------------------------------------------------- zamanlama tanımı
def zamanlama_dogrula(z, pencereler=None):
    """Zamanlamayı denetler ve sade biçimine getirir. Hata: ZamanlamaHatasi (Türkçe, ne beklendiğini söyler)."""
    if not isinstance(z, dict):
        raise ZamanlamaHatasi("zamanlama bir nesne olmalı")
    tur = str(z.get("tur", "")).strip()
    if tur == "tek":
        return {"tur": "tek", "zaman": _iso(_coz_zaman(z.get("zaman")))}
    if tur == "gunluk":
        h, m = _saat(z.get("saat"))
        return {"tur": "gunluk", "saat": f"{h:02d}:{m:02d}"}
    if tur == "haftalik":
        g = z.get("gunler") or ([z["gun"]] if z.get("gun") else [])
        if isinstance(g, str):
            g = [x for x in re.split(r"[,\s]+", g) if x]
        if not g:
            raise ZamanlamaHatasi("haftalık zamanlamada en az bir gün gerekli")
        h, m = _saat(z.get("saat"))
        gunler = sorted({_gun(x) for x in g}, key=GUNLER.index)
        return {"tur": "haftalik", "gunler": gunler, "saat": f"{h:02d}:{m:02d}"}
    if tur == "aylik":
        try:
            gun = int(z.get("gun"))
        except (TypeError, ValueError):
            raise ZamanlamaHatasi("aylık zamanlamada gün 1-31 arası bir sayı olmalı") from None
        if not 1 <= gun <= 31:
            raise ZamanlamaHatasi("aylık zamanlamada gün 1-31 arası olmalı")
        h, m = _saat(z.get("saat"))
        return {"tur": "aylik", "gun": gun, "saat": f"{h:02d}:{m:02d}"}
    if tur == "cron":
        cron_coz(z.get("ifade"))
        return {"tur": "cron", "ifade": " ".join(str(z["ifade"]).split())}
    if tur == "pencere":
        ad = str(z.get("pencere", "")).strip()
        if pencereler is not None:
            p = pencereler.getir(ad)
            if not p:
                raise ZamanlamaHatasi(f"böyle bir pencere yok: {ad!r} (var olanlar: {pencereler.adlar('bakim')})")
            if p["tur"] != "bakim":
                raise ZamanlamaHatasi(f"{ad} bir yasak pencere; iş yalnız bakım penceresine zamanlanır")
        return {"tur": "pencere", "pencere": ad}
    raise ZamanlamaHatasi("zamanlama türü tek / gunluk / haftalik / aylik / cron / pencere olmalı")


def okunakli(z):
    """Zamanlamanın Türkçe okunaklı metni."""
    t = z.get("tur")
    if t == "tek":
        return f"bir kez: {_coz_zaman(z['zaman']).strftime('%d.%m.%Y %H:%M')}"
    if t == "gunluk":
        return f"her gün {z['saat']}"
    if t == "haftalik":
        return f"her {', '.join(GUN_ADI[g] for g in z['gunler'])} {z['saat']}"
    if t == "aylik":
        return f"her ayın {z['gun']}. günü {z['saat']}"
    if t == "cron":
        return f"cron: {z['ifade']}"
    if t == "pencere":
        return f"'{z['pencere']}' bakım penceresinin her açılışında"
    return str(z)


def sonraki_zamanlar(z, simdi, pencereler=None, n=3, sonra_dahil=False):
    """`simdi`den SONRAKİ (sonra_dahil: simdi dahil) n çalışma zamanı."""
    z = zamanlama_dogrula(z, pencereler)
    simdi = simdi.replace(second=0, microsecond=0) + (datetime.timedelta(0) if sonra_dahil else datetime.timedelta(minutes=1))
    out = []
    t = z["tur"]
    if t == "tek":
        an = _coz_zaman(z["zaman"])
        return [an] if an >= simdi else []
    if t == "pencere":
        if pencereler is None:
            return []
        p = pencereler.getir(z["pencere"])
        return [b for b, _ in pencereler.araliklar(p, simdi, simdi + datetime.timedelta(days=400)) if b >= simdi][:n]
    if t == "cron":
        c = cron_coz(z["ifade"])
        gun = simdi.date()
        for _ in range(4 * 366):
            if _cron_gun_uyar(c, gun):
                for h in sorted(c["saat"]):
                    for m in sorted(c["dakika"]):
                        an = datetime.datetime.combine(gun, datetime.time(h, m))
                        if an >= simdi:
                            out.append(an)
                            if len(out) >= n:
                                return out
            gun += datetime.timedelta(days=1)
        return out
    h, m = _saat(z["saat"])
    gun = simdi.date()
    for _ in range(4 * 366):
        uyar = (t == "gunluk" or (t == "haftalik" and GUNLER[gun.weekday()] in z["gunler"])
                or (t == "aylik" and gun.day == min(z["gun"], calendar.monthrange(gun.year, gun.month)[1])))
        if uyar:
            an = datetime.datetime.combine(gun, datetime.time(h, m))
            if an >= simdi:
                out.append(an)
                if len(out) >= n:
                    break
        gun += datetime.timedelta(days=1)
    return out


# ---------------------------------------------------------------- pencereler
class Pencereler:
    """Bakım ve yasak pencereleri (ayarlar/pencereler.json). `saat`: şimdiki zamanı veren işlev (testte sahte)."""

    def __init__(self, yol=None, saat=None, veri=None):
        self.yol = yol or PENCERE_DOSYASI
        self.saat = saat or datetime.datetime.now
        self._veri = veri

    def _oku(self):
        if self._veri is not None:
            return self._veri
        try:
            return json.loads(self.yol.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {"pencereler": [], "yasak_politikasi": "bekle"}

    def _yaz(self, veri):
        if self._veri is not None:
            self._veri = veri
            return
        self.yol.parent.mkdir(parents=True, exist_ok=True)
        self.yol.write_text(json.dumps(veri, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    def hepsi(self):
        return list(self._oku().get("pencereler", []))

    def adlar(self, tur=None):
        return [p["ad"] for p in self.hepsi() if tur is None or p["tur"] == tur]

    def getir(self, ad):
        return next((p for p in self.hepsi() if p["ad"] == ad), None)

    def varsayilan_politika(self):
        return self._oku().get("yasak_politikasi", "bekle")

    @staticmethod
    def dogrula(p, envanter=None):
        if not isinstance(p, dict):
            raise ZamanlamaHatasi("pencere bir nesne olmalı")
        ad = str(p.get("ad", "")).strip()
        if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{1,48}", ad):
            raise ZamanlamaHatasi("pencere adı küçük harf, rakam, - ve _ ile 2-49 karakter olmalı")
        tur = p.get("tur")
        if tur not in ("bakim", "yasak"):
            raise ZamanlamaHatasi("pencere türü bakim ya da yasak olmalı")
        kapsam = str(p.get("kapsam", "")).strip()
        if not kapsam:
            raise ZamanlamaHatasi("kapsam gerekli (ör. grup:web ya da PA-APP-01)")
        if envanter is not None:
            from .envanter import SeciciHatasi
            try:
                if not envanter.sec(kapsam):
                    raise ZamanlamaHatasi(f"kapsam hiçbir sunucuya uymuyor: {kapsam}")
            except SeciciHatasi as e:
                raise ZamanlamaHatasi(f"kapsam: {e}") from None
        t = p.get("tekrar") or {}
        tt = t.get("tur")
        if tt in ("haftalik", "gunluk"):
            h, m = _saat(t.get("baslangic"))
            try:
                sure = int(t.get("sure_dk"))
            except (TypeError, ValueError):
                raise ZamanlamaHatasi("sure_dk bir sayı olmalı (dakika)") from None
            if not 1 <= sure <= 7 * 24 * 60:
                raise ZamanlamaHatasi("sure_dk 1 dakika ile 7 gün arasında olmalı")
            tekrar = {"tur": tt, "baslangic": f"{h:02d}:{m:02d}", "sure_dk": sure}
            if tt == "haftalik":
                g = t.get("gunler") or []
                if isinstance(g, str):
                    g = [x for x in re.split(r"[,\s]+", g) if x]
                if not g:
                    raise ZamanlamaHatasi("haftalık pencerede en az bir gün gerekli")
                tekrar["gunler"] = sorted({_gun(x) for x in g}, key=GUNLER.index)
        elif tt == "tek":
            b, s = _coz_zaman(t.get("baslangic")), _coz_zaman(t.get("bitis"))
            if s <= b:
                raise ZamanlamaHatasi("bitiş başlangıçtan sonra olmalı")
            tekrar = {"tur": "tek", "baslangic": _iso(b), "bitis": _iso(s)}
        else:
            raise ZamanlamaHatasi("tekrar türü haftalik / gunluk / tek olmalı")
        return {"ad": ad, "tur": tur, "kapsam": kapsam, "tekrar": tekrar, "aciklama": str(p.get("aciklama", ""))[:300]}

    def kaydet(self, p, envanter=None, kim="operatör", denetim=DENETIM):
        p = self.dogrula(p, envanter)
        veri = self._oku()
        liste = [x for x in veri.get("pencereler", []) if x["ad"] != p["ad"]]
        liste.append(p)
        veri["pencereler"] = sorted(liste, key=lambda x: (x["tur"], x["ad"]))
        self._yaz(veri)
        denetim.yaz("pencere_kaydedildi", pencere=p["ad"], tur=p["tur"], kapsam=p["kapsam"], tekrar=p["tekrar"], kim=kim)
        return p

    def sil(self, ad, kim="operatör", denetim=DENETIM):
        veri = self._oku()
        once = len(veri.get("pencereler", []))
        veri["pencereler"] = [x for x in veri.get("pencereler", []) if x["ad"] != ad]
        if len(veri["pencereler"]) == once:
            raise ZamanlamaHatasi(f"böyle bir pencere yok: {ad}")
        self._yaz(veri)
        denetim.yaz("pencere_silindi", pencere=ad, kim=kim)

    def politika_yaz(self, politika):
        if politika not in ("bekle", "sor", "atla"):
            raise ZamanlamaHatasi("yasak politikası bekle / sor / atla olmalı")
        veri = self._oku()
        veri["yasak_politikasi"] = politika
        self._yaz(veri)

    # -------------------------------------------------------- zaman aralıkları
    def araliklar(self, p, bas, son):
        """Pencerenin [bas, son] ile kesişen açık aralıkları [(başlangıç, bitiş)], sıralı."""
        t = p["tekrar"]
        if t["tur"] == "tek":
            b, s = _coz_zaman(t["baslangic"]), _coz_zaman(t["bitis"])
            return [(b, s)] if s > bas and b < son else []
        h, m = _saat(t["baslangic"])
        sure = datetime.timedelta(minutes=int(t["sure_dk"]))
        out = []
        gun = (bas - sure).date() - datetime.timedelta(days=1)
        while datetime.datetime.combine(gun, datetime.time(0, 0)) <= son:
            if t["tur"] == "gunluk" or GUNLER[gun.weekday()] in t.get("gunler", []):
                b = datetime.datetime.combine(gun, datetime.time(h, m))
                if b + sure > bas and b < son:
                    out.append((b, b + sure))
            gun += datetime.timedelta(days=1)
        return out

    def acik_mi(self, p, an):
        """(açık mı, kapanış zamanı)."""
        for b, s in self.araliklar(p, an, an + datetime.timedelta(minutes=1)):
            if b <= an < s:
                return True, s
        return False, None

    def kapsadigi(self, p, envanter):
        from .envanter import SeciciHatasi
        try:
            return {s.ad for s in envanter.sec(p["kapsam"])}
        except SeciciHatasi:
            return set()

    def yasakta(self, envanter, sunucular, an=None):
        """Şu an yasak pencerede olan hedef sunucular: {sunucu: {"pencere", "bitis"}}."""
        an = an or self.saat()
        out = {}
        for p in self.hepsi():
            if p["tur"] != "yasak":
                continue
            acik, bitis = self.acik_mi(p, an)
            if not acik:
                continue
            for s in self.kapsadigi(p, envanter) & {str(x).upper() for x in sunucular}:
                if s not in out or bitis > _coz_zaman(out[s]["bitis"]):
                    out[s] = {"pencere": p["ad"], "bitis": _iso(bitis)}
        return out

    def yasak_sonu(self, envanter, sunucular, an=None):
        """Hedeflerin hiçbirinin yasakta olmadığı ilk an (zincirleme pencereler dahil)."""
        an = an or self.saat()
        for _ in range(50):
            y = self.yasakta(envanter, sunucular, an)
            if not y:
                return an
            an = max(_coz_zaman(v["bitis"]) for v in y.values())
        return an

    def bakim_penceresi_bul(self, envanter, sunucular, gun=None):
        """Hedefleri kapsayan bakım penceresi (adı); `gun` verilirse o gün açılan. Tek aday yoksa ZamanlamaHatasi."""
        hedef = {str(x).upper() for x in sunucular}
        adaylar = []
        for p in self.hepsi():
            if p["tur"] != "bakim" or not hedef <= self.kapsadigi(p, envanter):
                continue
            if gun and p["tekrar"]["tur"] == "haftalik" and _gun(gun) not in p["tekrar"]["gunler"]:
                continue
            adaylar.append(p["ad"])
        if len(adaylar) == 1:
            return adaylar[0]
        if not adaylar:
            raise ZamanlamaHatasi(f"hedeflerin hepsini kapsayan bakım penceresi yok ({', '.join(sorted(hedef))})"
                                  + (f", gün: {gun}" if gun else "") + f"; tanımlı bakım pencereleri: {self.adlar('bakim')}")
        raise ZamanlamaHatasi(f"birden çok bakım penceresi uyuyor: {adaylar}; adını belirtin")

    def durum(self, envanter, an=None):
        """Arayüz için: her pencere, şu an açık mı, sonraki açılış, kapsadığı sunucular."""
        an = an or self.saat()
        out = []
        for p in self.hepsi():
            acik, bitis = self.acik_mi(p, an)
            sonraki = next((b for b, _ in self.araliklar(p, an, an + datetime.timedelta(days=400)) if b > an), None)
            out.append({**p, "acik": acik, "kapanis": _iso(bitis), "sonraki_acilis": _iso(sonraki),
                        "sunucular": sorted(self.kapsadigi(p, envanter)), "okunakli": self.okunakli(p)})
        return out

    @staticmethod
    def okunakli(p):
        t = p["tekrar"]
        if t["tur"] == "tek":
            return f"{_coz_zaman(t['baslangic']).strftime('%d.%m.%Y %H:%M')} – {_coz_zaman(t['bitis']).strftime('%d.%m.%Y %H:%M')}"
        sure = f"{t['sure_dk'] // 60} sa {t['sure_dk'] % 60} dk" if t["sure_dk"] % 60 else f"{t['sure_dk'] // 60} sa"
        gun = "her gün" if t["tur"] == "gunluk" else "her " + ", ".join(GUN_ADI[g] for g in t["gunler"])
        return f"{gun} {t['baslangic']}, {sure}"


# ---------------------------------------------------------------- talepten zamanlama (kod önce, model dar soruyla)
_SAAT_RE = r"(?:saat\s*)?([01]?\d|2[0-3])[:.]([0-5]\d)"
IPUCU = re.compile(r"\bher (gece|gun|sabah|aksam|hafta|ay|pazartesi|sali|carsamba|persembe|cuma|cumartesi|pazar)"
                   r"|\byarin\b|\bbu (gece|aksam|sabah)\b|\bbakim pencere|\bcron\b|\bzamanla|"
                   r"\b\d{1,2}[./]\d{1,2}[./]\d{4}\b|\b\d{4}-\d{2}-\d{2}\b|\bsaat\s*\d|\b\d{1,2}[:.]\d{2}\s*'?\s*(d[ae]|t[ae])\b")


def _gun_re(g):
    """Gün adı + ek; "cuma" "cumartesi"nin başını yakalamasın."""
    return r"\b" + g + ("(?!rtesi)" if g == "cuma" else "") + r"\w*"


def zamanlama_ipucu(talep):
    return bool(IPUCU.search(_n(talep)))


def _saat_bul(n):
    m = re.search(_SAAT_RE, n)
    if m:
        return f"{int(m.group(1)):02d}:{m.group(2)}"
    m = re.search(r"\b(?:saat|gece|sabah)\s*([01]?\d|2[0-3])\s*'?\s*(?:de|da|te|ta)?\b", n)
    if m:
        h = int(m.group(1))
        if "aksam" in n and h < 12:
            h += 12
        return f"{h:02d}:00"
    return None


def metinden_zamanlama(talep, simdi, pencereler=None, envanter=None, hedefler=None):
    """Talepteki zamanlama ifadesini kodla çözer: (zamanlama | None, açıklama). Çözemezse None (model sorulur)."""
    n = _n(talep)
    m = re.search(r"\bcron\s*[:=]?\s*\"?([0-9*/,\- ]{9,})\"?", n)
    if m:
        return {"tur": "cron", "ifade": " ".join(m.group(1).split()[:5])}, "cron ifadesi"
    if "bakim pencere" in n:
        if pencereler is None or envanter is None or not hedefler:
            return None, "bakım penceresi istendi ama hedef/pencere bilgisi yok"
        gun = next((g for g in GUNLER if re.search(_gun_re(g), n)), None)
        try:
            ad = pencereler.bakim_penceresi_bul(envanter, hedefler, gun)
        except ZamanlamaHatasi as e:
            return None, str(e)
        return {"tur": "pencere", "pencere": ad}, f"hedefleri kapsayan bakım penceresi: {ad}"
    saat = _saat_bul(n)
    gunler = [g for g in GUNLER if re.search(r"\bher (hafta )?" + _gun_re(g)[2:] + "|" + _gun_re(g) + r" ?(ve|,)", n)]
    if re.search(r"\bher (gece|gun|sabah|aksam)\b", n) and saat:
        return {"tur": "gunluk", "saat": saat}, "her gün"
    if gunler and saat and re.search(r"\bher\b", n):
        return {"tur": "haftalik", "gunler": gunler, "saat": saat}, "her hafta"
    m = re.search(r"\bher ay(?:in)? (\d{1,2})\s*'?\s*\w*", n)
    if m and saat:
        return {"tur": "aylik", "gun": int(m.group(1)), "saat": saat}, "her ay"
    if re.search(r"\bher ay(?:in)? son gun", n) and saat:
        # Ayın son günü: gün 31 verilir, kısa aylarda zamanlayıcı ayın son gününe çeker (forum F-SV-018'in çözümü)
        return {"tur": "aylik", "gun": 31, "saat": saat}, "her ayın son günü"
    m = re.search(r"\b(\d{4})-(\d{2})-(\d{2})\b", n) or None
    tarih = None
    if m:
        tarih = datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    else:
        m = re.search(r"\b(\d{1,2})[./](\d{1,2})[./](\d{4})\b", n)
        if m:
            tarih = datetime.date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    if tarih is None and re.search(r"\byarin\b", n):
        tarih = simdi.date() + datetime.timedelta(days=1)
    if tarih is None and re.search(r"\bbu (gece|aksam|sabah)\b|\bbugun\b", n):
        tarih = simdi.date()
    if tarih and saat:
        h, mi = _saat(saat)
        an = datetime.datetime.combine(tarih, datetime.time(h, mi))
        if an < simdi and re.search(r"\bbu gece\b", n):
            an += datetime.timedelta(days=1)      # "bu gece 02:00" öğleden sonra söylenirse ertesi günün 02:00'si
        return {"tur": "tek", "zaman": _iso(an)}, "tek seferlik"
    return None, "kod zamanlamayı çözemedi"


def zamanlama_sor(model, talep, iz, simdi, pencereler=None, envanter=None, hedefler=None):
    """Talepte zamanlama ipucu varsa: önce kod çözer; çözemezse model dar bir soruya cevap verir, kod doğrular.
    Dönüş: {"zamanlama", "okunakli", "sonraki"} ya da None (zamanlama yok). Doğrulanamazsa ZamanlamaHatasi."""
    if not zamanlama_ipucu(talep):
        return None
    z, neden = metinden_zamanlama(talep, simdi, pencereler, envanter, hedefler)
    kaynak = "kod"
    if z is None:
        if model is None:
            raise ZamanlamaHatasi(f"talepteki zamanlama çözülemedi: {neden}")
        from .ajan_ortak import SISTEM
        from .gateway import sor_json
        bak = (f"Bakım pencereleri: {', '.join(pencereler.adlar('bakim'))}\n" if pencereler else "")
        metin = (f"Talep: \"{talep}\"\nŞu an: {simdi.strftime('%Y-%m-%d %H:%M')} ({GUN_ADI[GUNLER[simdi.weekday()]]})\n{bak}"
                 "Talep işin NE ZAMAN çalışacağını söylüyor. Bunu yapılandırılmış zamanlamaya çevir. Türler: tek (bir kez; "
                 "zaman YYYY-MM-DDTHH:MM), gunluk (saat), haftalik (gunler + saat), aylik (gun + saat), pencere (bakım "
                 "penceresinin adı). Gün adları: " + ", ".join(GUNLER) + ".\n"
                 'JSON: {"tur": "...", "zaman": "", "saat": "", "gunler": [], "gun": 0, "pencere": ""}')

        def dogrula(v):
            try:
                zz = zamanlama_dogrula({k: x for k, x in v.items() if x not in (None, "", [], 0)}, pencereler)
            except ZamanlamaHatasi as e:
                return None, str(e)
            nn = _n(talep)
            if zz.get("saat"):            # saat talepte geçmeli (uydurma saat reddedilir)
                h, mi = _saat(zz["saat"])
                if not re.search(rf"\b0?{h}\b|\b{h - 12 if h > 12 else h}\b", nn):
                    return None, f"saat {zz['saat']} talepte geçmiyor; talepteki saati yaz"
            for g in zz.get("gunler", []):
                if not re.search(_gun_re(g), nn):
                    return None, f"{g} talepte geçmiyor"
            if zz["tur"] == "tek" and _coz_zaman(zz["zaman"]) < simdi:
                return None, "tek seferlik zaman geçmişte kalıyor"
            return zz, None
        z = sor_json(model, SISTEM, metin, dogrula, iz=iz, etiket="zamanlama")[0]
        kaynak = "model"
        if z is None:
            raise ZamanlamaHatasi(f"talepteki zamanlama çözülemedi ({neden}); model geçerli bir zamanlama vermedi")
    elif iz is not None:
        iz.append({"soru": "zamanlama (kod)", "denemeler": [], "sonuc": z,
                   "kod_notu": f"zamanlamayı kod çözdü ({neden}); model sorulmadı"})
    z = zamanlama_dogrula(z, pencereler)
    sonraki = sonraki_zamanlar(z, simdi, pencereler, 3)
    if not sonraki:
        raise ZamanlamaHatasi(f"{okunakli(z)}: bundan sonra çalışma zamanı yok (geçmişte kalıyor)")
    return {"zamanlama": z, "okunakli": okunakli(z), "sonraki": [_iso(x) for x in sonraki], "kaynak": kaynak}


# ---------------------------------------------------------------- zamanlanmış işler
def tanim_ozeti(z):
    """Onayın bağlı olduğu tanımın özeti: ne, nerede, ne zaman (onaya, geçmişe, durum alanlarına bakılmaz)."""
    oz = {k: z.get(k) for k in ("tanim", "zamanlama", "hedef_cozumu", "dondurulmus_liste")}
    return hashlib.sha256(json.dumps(oz, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()[:16]


class Zamanlayici:
    """Zamanlanmış işlerin deposu ve tetikleyicisi.

    calistirici(zis, an, on_onay, not_) -> {"is": kimlik, "durum": ...}: işi başlatan geri çağrı (konsolda Ofis, bench'te
    kol). envanter_fn: güncel envanteri veren işlev. risk_fn(tanim) -> (risk, onay_gerekli, hedef adları).
    """

    def __init__(self, yol=None, saat=None, pencereler=None, envanter_fn=None, calistirici=None, risk_fn=None,
                 denetim=DENETIM):
        self.yol = yol or (ZAMANLAMA / "isler.json")
        self.saat = saat or datetime.datetime.now
        self.pencereler = pencereler or Pencereler(saat=self.saat)
        self.envanter_fn, self.calistirici, self.risk_fn = envanter_fn, calistirici, risk_fn
        self.denetim = denetim
        self.kilit = threading.RLock()
        self._dur = threading.Event()
        self._is_parcacigi = None

    # -------------------------------------------------------- depo
    def _oku(self):
        try:
            return json.loads(self.yol.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {"isler": []}

    def _yaz(self, veri):
        self.yol.parent.mkdir(parents=True, exist_ok=True)
        gecici = self.yol.with_suffix(".tmp")
        gecici.write_text(json.dumps(veri, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
        gecici.replace(self.yol)

    def liste(self):
        with self.kilit:
            out = []
            for z in self._oku()["isler"]:
                z = dict(z)
                z["okunakli"] = okunakli(z["zamanlama"])
                try:
                    z["sonraki_uc"] = [_iso(x) for x in sonraki_zamanlar(z["zamanlama"], self.saat(), self.pencereler, 3,
                                                                          sonra_dahil=True)] if z.get("etkin") else []
                except ZamanlamaHatasi as e:
                    z["sonraki_uc"], z["hata"] = [], str(e)
                z["onay_gecerli"] = self._onay_gecerli(z)
                out.append(z)
            return out

    def getir(self, kimlik):
        return next((z for z in self.liste() if z["kimlik"] == kimlik), None)

    def _guncelle(self, kimlik, fn):
        with self.kilit:
            veri = self._oku()
            for z in veri["isler"]:
                if z["kimlik"] == kimlik:
                    fn(z)
                    self._yaz(veri)
                    return z
        raise ZamanlamaHatasi(f"zamanlanmış iş yok: {kimlik}")

    @staticmethod
    def _gecmis(z, olay, **alan):
        z.setdefault("gecmis", []).append({"olay": olay, **alan})
        z["gecmis"] = z["gecmis"][-60:]

    # -------------------------------------------------------- oluşturma ve değiştirme
    def ekle(self, ad, tanim, zamanlama, hedef_cozumu="simdi", kacirilan="atla", yasak_politikasi=None,
             olusturan="operatör", on_onay=None, dondurulmus=None):
        if hedef_cozumu not in ("simdi", "calisma_aninda"):
            raise ZamanlamaHatasi("hedef_cozumu simdi ya da calisma_aninda olmalı")
        if kacirilan not in ("atla", "hemen"):
            raise ZamanlamaHatasi("kaçırılan koşu politikası atla ya da hemen olmalı")
        yasak_politikasi = yasak_politikasi or self.pencereler.varsayilan_politika()
        if yasak_politikasi not in ("bekle", "sor", "atla"):
            raise ZamanlamaHatasi("yasak politikası bekle / sor / atla olmalı")
        if not isinstance(tanim, dict) or tanim.get("tur") not in ("beceri", "talep", "akis"):
            raise ZamanlamaHatasi("tanım türü beceri / talep / akis olmalı")
        z_ = zamanlama_dogrula(zamanlama, self.pencereler)
        simdi = self.saat()
        sonraki = sonraki_zamanlar(z_, simdi, self.pencereler, 1, sonra_dahil=True)
        if not sonraki:
            raise ZamanlamaHatasi(f"{okunakli(z_)}: çalışma zamanı geçmişte kalıyor")
        risk, onay_gerekli, hedefler = self.risk_fn(tanim) if self.risk_fn else (0, False, [])
        z = {"kimlik": uuid.uuid4().hex[:8], "ad": str(ad or tanim.get("metin") or tanim.get("beceri") or "iş")[:120],
             "olusturan": olusturan, "olusturma": _iso(simdi), "etkin": True, "tanim": tanim, "zamanlama": z_,
             "hedef_cozumu": hedef_cozumu, "kacirilan": kacirilan, "yasak_politikasi": yasak_politikasi,
             "risk": risk, "onay_gerekli": onay_gerekli, "tanim_surumu": 1, "onay": None,
             "dondurulmus_liste": (dondurulmus or {}).get("sunucular") if hedef_cozumu == "simdi" else None,
             "dondurulmus": dondurulmus if hedef_cozumu == "simdi" else None,
             "sonraki": _iso(sonraki[0]), "son_calisma": None, "bekleyen_soru": None, "gecmis": []}
        if hedef_cozumu == "simdi" and not z["dondurulmus_liste"] and hedefler:
            z["dondurulmus_liste"] = list(hedefler)
        z["tanim_ozeti"] = tanim_ozeti(z)
        self._gecmis(z, "olusturuldu", zaman=_iso(simdi), kim=olusturan)
        with self.kilit:
            veri = self._oku()
            veri["isler"].append(z)
            self._yaz(veri)
        self.denetim.yaz("zamanlama_eklendi", zamanlama=z["kimlik"], ad=z["ad"], tanim=tanim, zaman=z_,
                         hedef_cozumu=hedef_cozumu, hedefler=z["dondurulmus_liste"], kacirilan=kacirilan,
                         yasak_politikasi=yasak_politikasi, kim=olusturan)
        if on_onay:
            self.onayla(z["kimlik"], on_onay)
        return self.getir(z["kimlik"])

    def degistir(self, kimlik, kim="operatör", **alanlar):
        """Tanımı değiştirir. Ne/nerede/ne zaman değişirse tanım sürümü artar ve önceden verilmiş onay düşer."""
        izinli = {"ad", "tanim", "zamanlama", "hedef_cozumu", "kacirilan", "yasak_politikasi", "etkin"}
        bilinmeyen = set(alanlar) - izinli
        if bilinmeyen:
            raise ZamanlamaHatasi(f"değiştirilemeyen alan: {sorted(bilinmeyen)}")
        if "zamanlama" in alanlar:
            alanlar["zamanlama"] = zamanlama_dogrula(alanlar["zamanlama"], self.pencereler)
        simdi = self.saat()

        def fn(z):
            z.update(alanlar)
            yeni = tanim_ozeti(z)
            if yeni != z["tanim_ozeti"]:
                z["tanim_surumu"] += 1
                z["tanim_ozeti"] = yeni
                if self.risk_fn and "tanim" in alanlar:
                    z["risk"], z["onay_gerekli"], _ = self.risk_fn(z["tanim"])
                if z.get("onay"):
                    self._gecmis(z, "onay_dustu", zaman=_iso(simdi), neden=f"tanım değişti (v{z['tanim_surumu']})",
                                 onay=z["onay"])
                    self.denetim.yaz("zamanlama_onayi_dustu", zamanlama=kimlik, tanim_surumu=z["tanim_surumu"],
                                     onceki_onay=z["onay"])
                    z["onay"] = None
            if "zamanlama" in alanlar or alanlar.get("etkin"):
                s = sonraki_zamanlar(z["zamanlama"], simdi, self.pencereler, 1, sonra_dahil=True)
                z["sonraki"] = _iso(s[0]) if s else None
            self._gecmis(z, "degistirildi", zaman=_iso(simdi), kim=kim, alanlar=sorted(alanlar))
        self._guncelle(kimlik, fn)
        self.denetim.yaz("zamanlama_degisti", zamanlama=kimlik, alanlar=sorted(alanlar), kim=kim)
        return self.getir(kimlik)

    def sil(self, kimlik, kim="operatör"):
        with self.kilit:
            veri = self._oku()
            once = len(veri["isler"])
            veri["isler"] = [z for z in veri["isler"] if z["kimlik"] != kimlik]
            if len(veri["isler"]) == once:
                raise ZamanlamaHatasi(f"zamanlanmış iş yok: {kimlik}")
            self._yaz(veri)
        self.denetim.yaz("zamanlama_silindi", zamanlama=kimlik, kim=kim)

    def onayla(self, kimlik, veren):
        """Önceden onay: kim, ne zaman, hangi tanım sürümü ve özeti için."""
        simdi = self.saat()

        def fn(z):
            z["onay"] = {"veren": veren, "zaman": _iso(simdi), "tanim_surumu": z["tanim_surumu"],
                         "tanim_ozeti": z["tanim_ozeti"]}
            self._gecmis(z, "onaylandi", zaman=_iso(simdi), kim=veren, tanim_surumu=z["tanim_surumu"])
        z = self._guncelle(kimlik, fn)
        self.denetim.yaz("zamanlama_onaylandi", zamanlama=kimlik, onaylayan=veren, tanim_surumu=z["tanim_surumu"],
                         tanim_ozeti=z["tanim_ozeti"])
        return z

    @staticmethod
    def _onay_gecerli(z):
        o = z.get("onay")
        return bool(o and o.get("tanim_surumu") == z["tanim_surumu"] and o.get("tanim_ozeti") == z["tanim_ozeti"])

    # -------------------------------------------------------- tetikleme
    def _hedefler(self, z):
        if z["hedef_cozumu"] == "simdi":
            return list(z.get("dondurulmus_liste") or [])
        if self.risk_fn:
            return list(self.risk_fn(z["tanim"])[2])
        return []

    def _calistir(self, z, an, plan_zamani, not_="", istisna=None):
        on_onay = None
        if z.get("onay_gerekli"):
            if self._onay_gecerli(z):
                on_onay = {**z["onay"], "zamanlama": z["kimlik"]}
            elif z.get("onay"):
                not_ = (not_ + "; " if not_ else "") + "önceden verilen onay bu tanım sürümüne ait değil: koşu onay isteyecek"
        z = {**z, "hedefler": self._hedefler(z)}
        try:
            sonuc = (self.calistirici(z, an, on_onay, not_, istisna) if self.calistirici
                     else {"durum": "calistirici_yok"})
        except Exception as e:  # noqa: BLE001 - zamanlayıcı iş parçacığı düşmesin; hata geçmişe yazılır
            sonuc = {"durum": "hata", "hata": f"{type(e).__name__}: {e}"}
        self.denetim.yaz("zamanlama_calisti", zamanlama=z["kimlik"], plan_zamani=_iso(plan_zamani), an=_iso(an),
                         is_kimligi=sonuc.get("is"), durum=sonuc.get("durum"), on_onay=bool(on_onay), not_=not_)
        return sonuc

    def tik(self, simdi=None):
        """Vadesi gelen işleri yürütür. Dönüş: bu tikte olan olayların listesi (sınama ve günlük için)."""
        simdi = (simdi or self.saat()).replace(second=0, microsecond=0)
        olaylar = []
        with self.kilit:
            veri = self._oku()
            vadeli = [z["kimlik"] for z in veri["isler"]
                      if z.get("etkin") and z.get("sonraki") and not z.get("bekleyen_soru")
                      and _coz_zaman(z["sonraki"]) <= simdi]
        for kimlik in vadeli:
            olaylar.append(self._tetikle(kimlik, simdi))
        return olaylar

    def _sonrakini_kur(self, z, plan_zamani, simdi):
        if z["zamanlama"]["tur"] == "tek":
            z["sonraki"], z["etkin"] = None, False
            return
        s = sonraki_zamanlar(z["zamanlama"], max(plan_zamani, simdi), self.pencereler, 1)
        z["sonraki"] = _iso(s[0]) if s else None

    def _tetikle(self, kimlik, simdi):
        z = next(x for x in self._oku()["isler"] if x["kimlik"] == kimlik)
        plan_zamani = _coz_zaman(z["sonraki"])
        ertelenmis = bool(z.get("erteleme"))
        # 1) kaçırılan koşu (konsol kapalıydı)
        if not ertelenmis and simdi - plan_zamani > KACIRMA_TOLERANSI and z["kacirilan"] == "atla":
            def fn(x):
                self._gecmis(x, "kacirildi", zaman=_iso(simdi), plan_zamani=_iso(plan_zamani),
                             not_="konsol bu saatte çalışmıyordu; politika: atla")
                self._sonrakini_kur(x, plan_zamani, simdi)
            self._guncelle(kimlik, fn)
            self.denetim.yaz("zamanlama_kacirildi", zamanlama=kimlik, plan_zamani=_iso(plan_zamani), politika="atla")
            return {"zamanlama": kimlik, "olay": "kacirildi"}
        not_ = ("kaçırılan koşu hemen çalıştırıldı (plan: " + _iso(plan_zamani) + ")"
                if not ertelenmis and simdi - plan_zamani > KACIRMA_TOLERANSI else "")
        # 2) yasak pencere (yalnız değiştiren işler)
        env = self.envanter_fn() if self.envanter_fn else None
        hedefler = self._hedefler(z)
        yasak = self.pencereler.yasakta(env, hedefler, simdi) if (env is not None and z.get("risk", 0) >= 2) else {}
        if yasak:
            bitis = max(_coz_zaman(v["bitis"]) for v in yasak.values())
            pol = z["yasak_politikasi"]
            ozet = ", ".join(f"{s} ({v['pencere']}, {v['bitis']} kapanır)" for s, v in sorted(yasak.items()))

            def fn(x):
                if pol == "bekle":
                    son = self.pencereler.yasak_sonu(env, hedefler, simdi)
                    x["erteleme"] = {"plan_zamani": x.get("erteleme", {}).get("plan_zamani") or _iso(plan_zamani),
                                     "neden": f"yasak pencere: {ozet}"}
                    x["sonraki"] = _iso(son)
                    self._gecmis(x, "ertelendi", zaman=_iso(simdi), plan_zamani=_iso(plan_zamani), yeni=_iso(son),
                                 not_=f"yasak pencere: {ozet}")
                elif pol == "sor":
                    x["bekleyen_soru"] = {"zaman": _iso(simdi), "plan_zamani": _iso(plan_zamani), "yasak": yasak,
                                          "soru": f"Hedefler yasak pencerede ({ozet}). Şimdi mi çalışsın, pencere "
                                                  f"kapanınca ({_iso(bitis)}) mı, yoksa bu koşu atlansın mı?"}
                    self._gecmis(x, "soruldu", zaman=_iso(simdi), plan_zamani=_iso(plan_zamani), not_=f"yasak pencere: {ozet}")
                else:
                    self._gecmis(x, "atlandi", zaman=_iso(simdi), plan_zamani=_iso(plan_zamani), not_=f"yasak pencere: {ozet}")
                    self._sonrakini_kur(x, plan_zamani, simdi)
            self._guncelle(kimlik, fn)
            self.denetim.yaz("zamanlama_yasak", zamanlama=kimlik, politika=pol, yasak=yasak, plan_zamani=_iso(plan_zamani))
            return {"zamanlama": kimlik, "olay": {"bekle": "ertelendi", "sor": "soruldu", "atla": "atlandi"}[pol],
                    "yasak": yasak}
        # 3) çalıştır
        sonuc = self._calistir(z, simdi, plan_zamani, not_)

        def fn(x):
            asil = _coz_zaman((x.get("erteleme") or {}).get("plan_zamani") or _iso(plan_zamani))
            x.pop("erteleme", None)
            x["son_calisma"] = {"zaman": _iso(simdi), "plan_zamani": _iso(asil), "is": sonuc.get("is"),
                                "durum": sonuc.get("durum")}
            self._gecmis(x, "calisti", zaman=_iso(simdi), plan_zamani=_iso(asil), is_=sonuc.get("is"),
                         durum=sonuc.get("durum"), not_=not_ or sonuc.get("hata", ""))
            self._sonrakini_kur(x, asil, simdi)
        self._guncelle(kimlik, fn)
        return {"zamanlama": kimlik, "olay": "calisti", **sonuc}

    def soru_cevapla(self, kimlik, karar, kim="operatör"):
        """Yasak pencere sorusu: 'simdi' (operatör yasağı bu koşu için kaldırır), 'bekle', 'atla'."""
        if karar not in ("simdi", "bekle", "atla"):
            raise ZamanlamaHatasi("karar simdi / bekle / atla olmalı")
        simdi = self.saat()
        z = next((x for x in self._oku()["isler"] if x["kimlik"] == kimlik), None)
        if not z or not z.get("bekleyen_soru"):
            raise ZamanlamaHatasi("bu işin bekleyen sorusu yok")
        soru = z["bekleyen_soru"]
        self.denetim.yaz("zamanlama_soru_cevabi", zamanlama=kimlik, karar=karar, kim=kim)
        if karar == "simdi":
            sonuc = self._calistir(z, simdi, _coz_zaman(soru["plan_zamani"]),
                                   f"yasak pencerede operatör kararıyla çalıştı ({kim})",
                                   istisna={"kim": kim, "zaman": _iso(simdi), "yasak": soru.get("yasak")})

            def fn(x):
                x["bekleyen_soru"] = None
                x["son_calisma"] = {"zaman": _iso(simdi), "plan_zamani": soru["plan_zamani"], "is": sonuc.get("is"),
                                    "durum": sonuc.get("durum")}
                self._gecmis(x, "calisti", zaman=_iso(simdi), plan_zamani=soru["plan_zamani"], is_=sonuc.get("is"),
                             durum=sonuc.get("durum"), not_=f"yasak pencerede operatör kararı ({kim})")
                self._sonrakini_kur(x, _coz_zaman(soru["plan_zamani"]), simdi)
            self._guncelle(kimlik, fn)
            return sonuc
        env = self.envanter_fn() if self.envanter_fn else None

        def fn(x):
            x["bekleyen_soru"] = None
            if karar == "bekle":
                son = self.pencereler.yasak_sonu(env, self._hedefler(x), simdi) if env is not None else simdi
                x["erteleme"] = {"plan_zamani": soru["plan_zamani"], "neden": "operatör: pencere kapanınca"}
                x["sonraki"] = _iso(son)
                self._gecmis(x, "ertelendi", zaman=_iso(simdi), yeni=_iso(son), not_=f"operatör kararı ({kim})")
            else:
                self._gecmis(x, "atlandi", zaman=_iso(simdi), not_=f"operatör kararı ({kim})")
                self._sonrakini_kur(x, _coz_zaman(soru["plan_zamani"]), simdi)
        self._guncelle(kimlik, fn)
        return {"durum": karar}

    def simdi_calistir(self, kimlik, kim="operatör"):
        """Operatör zamanlanmış işi beklemeden bir kez çalıştırır (yasak pencere denetimi yine uygulanır)."""
        z = next((x for x in self._oku()["isler"] if x["kimlik"] == kimlik), None)
        if not z:
            raise ZamanlamaHatasi(f"zamanlanmış iş yok: {kimlik}")
        simdi = self.saat()
        env = self.envanter_fn() if self.envanter_fn else None
        yasak = self.pencereler.yasakta(env, self._hedefler(z), simdi) if (env is not None and z.get("risk", 0) >= 2) else {}
        if yasak:
            raise ZamanlamaHatasi("hedefler yasak pencerede: " + ", ".join(f"{s} ({v['pencere']})" for s, v in yasak.items()))
        sonuc = self._calistir(z, simdi, simdi, f"operatör şimdi çalıştırdı ({kim})")
        def fn(x):
            x["son_calisma"] = {"zaman": _iso(simdi), "plan_zamani": None, "is": sonuc.get("is"), "durum": sonuc.get("durum")}
            self._gecmis(x, "calisti", zaman=_iso(simdi), is_=sonuc.get("is"), durum=sonuc.get("durum"),
                         not_=f"elle ({kim})")
        self._guncelle(kimlik, fn)
        return sonuc

    # -------------------------------------------------------- iş parçacığı (konsol)
    def baslat(self, aralik=20):
        if self._is_parcacigi and self._is_parcacigi.is_alive():
            return self

        def dongu():
            while not self._dur.is_set():
                try:
                    self.tik()
                except Exception as e:  # noqa: BLE001 - zamanlayıcı düşmesin
                    self.denetim.yaz("zamanlama_hatasi", hata=f"{type(e).__name__}: {e}")
                self._dur.wait(aralik)
        self._is_parcacigi = threading.Thread(target=dongu, name="filo-zamanlayici", daemon=True)
        self._is_parcacigi.start()
        return self

    def durdur(self):
        self._dur.set()


def kopya(x):
    return copy.deepcopy(x)
