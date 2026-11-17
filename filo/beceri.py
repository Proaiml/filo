"""Beceri kataloğu: tipli girdi/çıktı şeması, risk düzeyi, geri alma, kuru çalıştırma, sürümleme.

Bir beceri `skills/<ad>/beceri.json` dosyasıdır. Betik kütüphanesi `skills/_betikler/<ad>/` (betik.sh + meta.json),
dağıtılacak dosyalar `skills/_dosyalar/` altındadır. Alt çizgiyle başlayan dizinler beceri değildir.

    {
      "ad": "disk_durumu", "surum": 1, "baslik": "...", "aciklama": "...", "etiketler": [...],
      "risk": 0,                      0 salt-okur, 1 raporlama/dosya üretme, 2 geri alınabilir değişiklik,
                                      3 servis ve paket değişikliği, 4 yıkıcı
      "tur": "uzak" | "yerel" | "zincir",
      "zaman_asimi": 60,
      "girdi": {"esik": {"tip": "tamsayi", "varsayilan": 90, "en_az": 1, "en_cok": 100, "aciklama": "..."}},
      "cikti": {"bicim": "satirlar", "ayirici": "|", "alanlar": {"bolum": "metin", "yuzde": "tamsayi"}},
      "komut":   {"debian": "...", "rhel": "...", "alpine": "...", "linux": "...", "windows": "..."},
      "kuru":    {...aynı biçim, salt-okur: ne değişeceğini gösterir...},
      "geri_al": {...aynı biçim...} ya da {"geri_alinamaz": "neden"},
      "adimlar": [...]                yalnız zincir becerilerde
    }

Komutlardaki {ad} yer tutucuları şemadan geçmiş değerlerle, işletim sistemine göre tırnaklanarak doldurulur.
Risk düzeyi kodla da hesaplanır (`risk_sinifla`): etkin düzey = max(beyan, hesaplanan). Bir değişiklik düzeyi
yükseltirse etkin düzey yükselir ve politika onay ister.
"""
import copy
import datetime
import difflib
import json
import re
import shlex
import shutil

from . import ROOT
from .denetim import DENETIM
from .erisim import salt_okur_denetle

SKILLS = ROOT / "skills"
BETIKLER = SKILLS / "_betikler"
DOSYALAR = SKILLS / "_dosyalar"

TIPLER = ("metin", "tamsayi", "mantik", "secim", "liste", "eposta", "yol", "komut")
# yonetim: işi komut şablonu değil, koddaki bir işleyici yapar (ör. ajan kurulumu: SSH + kapı + kalp bekleme)
TURLER = ("uzak", "yerel", "zincir", "yonetim")
CIKTI_BICIMLERI = ("satirlar", "anahtar_deger", "json", "ham", "belge", "betik")
DESENLER = {
    "paket": r"^[a-z0-9][a-z0-9+._-]{0,63}$",
    "servis": r"^[a-z0-9][a-z0-9_.@-]{0,63}$",
    "kullanici": r"^[a-z_][a-z0-9_-]{0,31}$",
    "konu": r"^[^\r\n]{1,200}$",
}
EPOSTA = re.compile(r"^[A-Za-z0-9._%+-]{1,64}@[A-Za-z0-9.-]{1,190}\.[A-Za-z]{2,24}$")
YOL = re.compile(r"^/[A-Za-z0-9_./-]{1,250}$")

# ---------------------------------------------------------------- risk sınıflama (kod)
RISK_DESENLERI = [
    (4, r"\brm\s+-[a-zA-Z]*[rR][a-zA-Z]*\b|\bmkfs|\bdd\s+if=|\breboot\b(?![-.])|\bshutdown\b|\bpoweroff\b|\bhalt\b|\buserdel\b|\bdeluser\b|"
        r"\bwipefs\b|\btruncate\b|\bfind\b[^|;]*-delete|Remove-Item[^|;]*-Recurse|Format-Volume|Stop-Computer|"
        r"Restart-Computer|Remove-LocalUser|:\s*>\s*/"),
    (3, r"\b(apt-get|apt|dnf|yum|microdnf)\s+(-[-\w=]+\s+)*(install|remove|purge|upgrade|reinstall|autoremove)\b|"
        r"\bapk\s+(-[-\w]+\s+)*(add|del|upgrade|fix)\b|\bdpkg\s+(-i|--configure|--remove|-r|-P|--purge)\b|"
        r"\bsystemctl\s+(-[-\w]+\s+)*(start|stop|restart|reload|enable|disable|mask)\b|"
        r"\brc-service\s+\S+\s+(start|stop|restart)\b|\bservice\s+\S+\s+(start|stop|restart)\b|"
        r"\buseradd\b|\badduser\b|\busermod\b|(?<![/\w.-])passwd\b(?![./-])|\bchpasswd\b|\bvisudo\b|\bkill\b|\bpkill\b|\bkillall\b|"
        r"Restart-Service|Stop-Service|Start-Service|Install-Package|Install-WindowsFeature|New-LocalUser|"
        r"Set-Service|Stop-Process"),
    (2, r"(?<![=!<>-])>{1,2}(?![=&])\s*[A-Za-z_/$\"'{.~-]|\btee\b|\bcp\b|\bmv\b|\bmkdir\b|\btouch\b|\bchmod\b|\bchown\b|\bsed\s+-i|\binstall\s+-[a-zA-Z]|"
        r"\bln\s+-s|\brm\b|\bbase64\s+-d|Set-Content|Out-File|New-Item|Copy-Item|Move-Item|Set-ItemProperty|"
        r"Remove-Item|Add-Content"),
]
_ZARARSIZ_YONLENDIRME = re.compile(r"[0-9]?>>?\s*/dev/null|[0-9]>&[0-9]|>\s*&2")


def risk_sinifla(metinler):
    """Komut metinlerinden kodla risk düzeyi (0, 2, 3, 4) ve gerekçe."""
    en, neden = 0, ""
    for metin in metinler:
        if not metin:
            continue
        temiz = _ZARARSIZ_YONLENDIRME.sub(" ", str(metin))
        temiz = re.sub(r"(?m)^\s*#.*$", "", temiz)   # yorum satırları
        for duzey, desen in RISK_DESENLERI:
            m = re.search(desen, temiz)
            if m and duzey > en:
                en, neden = duzey, f"'{m.group(0).strip()}' (düzey {duzey})"
                break
    return en, neden


class SemaHatasi(ValueError):
    pass


# ---------------------------------------------------------------- girdi şeması
def betik_listesi():
    return sorted(p.name for p in BETIKLER.iterdir() if (p / "betik.sh").exists()) if BETIKLER.exists() else []


def dosya_listesi():
    return sorted(p.name for p in DOSYALAR.iterdir() if p.is_file()) if DOSYALAR.exists() else []


def secenekler(alan):
    if alan.get("kaynak") == "betikler":
        return betik_listesi()
    if alan.get("kaynak") == "dosyalar":
        return dosya_listesi()
    if alan.get("kaynak") in ("yama_politikalari", "yazilim_politikalari", "kural_setleri"):
        # D1-D3: politika ve kural seti adları ayar dosyalarından (seçenekleri kod daraltır, model yalnız seçer)
        from . import durum
        return durum.kayit_adlari(alan["kaynak"])
    return list(alan.get("secenekler") or [])


def parametre_dogrula(sema, degerler):
    """Şemaya göre doğrulanmış ve varsayılanları doldurulmuş parametreler; uymayan çağrı SemaHatasi verir."""
    degerler = dict(degerler or {})
    bilinmeyen = set(degerler) - set(sema)
    if bilinmeyen:
        raise SemaHatasi(f"şemada olmayan parametre: {sorted(bilinmeyen)}")
    out = {}
    for ad, alan in sema.items():
        tip = alan.get("tip", "metin")
        if ad not in degerler or degerler[ad] in (None, ""):
            if "varsayilan" in alan:
                out[ad] = copy.deepcopy(alan["varsayilan"])
                continue
            if alan.get("zorunlu", True):
                raise SemaHatasi(f"zorunlu parametre eksik: {ad}")
            continue
        v = degerler[ad]
        if tip == "tamsayi":
            try:
                v = int(v)
            except (TypeError, ValueError):
                raise SemaHatasi(f"{ad}: tamsayı olmalı") from None
            if "en_az" in alan and v < alan["en_az"] or "en_cok" in alan and v > alan["en_cok"]:
                raise SemaHatasi(f"{ad}: {alan.get('en_az')}..{alan.get('en_cok')} aralığında olmalı")
        elif tip == "mantik":
            if isinstance(v, str):
                if v.lower() not in ("evet", "hayir", "hayır", "true", "false", "1", "0"):
                    raise SemaHatasi(f"{ad}: evet/hayır olmalı")
                v = v.lower() in ("evet", "true", "1")
            v = bool(v)
        elif tip == "secim":
            se = secenekler(alan)
            if str(v) not in se:
                raise SemaHatasi(f"{ad}: şunlardan biri olmalı: {se}")
            v = str(v)
        elif tip == "liste":
            if isinstance(v, str):
                v = [x.strip() for x in re.split(r"[,\s]+", v) if x.strip()]
            if not isinstance(v, list) or not v:
                raise SemaHatasi(f"{ad}: boş olmayan liste olmalı")
            desen = DESENLER.get(alan.get("desen"), alan.get("desen")) or r"^[A-Za-z0-9_.+-]{1,64}$"
            for x in v:
                if not re.match(desen, str(x)):
                    raise SemaHatasi(f"{ad}: geçersiz öğe {x!r}")
            if len(v) > alan.get("en_cok", 20):
                raise SemaHatasi(f"{ad}: en çok {alan.get('en_cok', 20)} öğe")
            v = [str(x) for x in v]
        elif tip == "eposta":
            v = str(v).strip()
            if not EPOSTA.match(v):
                raise SemaHatasi(f"{ad}: geçerli bir e-posta adresi değil")
        elif tip == "yol":
            v = str(v).strip()
            if not YOL.match(v) or ".." in v or "//" in v:
                raise SemaHatasi(f"{ad}: mutlak ve sade bir yol olmalı")
            onekler = alan.get("izinli_onekler")
            if onekler and not any(v == o.rstrip("/") or v.startswith(o.rstrip("/") + "/") for o in onekler):
                raise SemaHatasi(f"{ad}: yalnız şu dizinlerin altı: {onekler}")
        elif tip == "komut":
            v = str(v).strip()
            neden = salt_okur_denetle(v)
            if neden:
                raise SemaHatasi(f"{ad}: salt-okur izin listesine uymuyor: {neden}")
        else:  # metin
            v = str(v)
            desen = DESENLER.get(alan.get("desen"), alan.get("desen"))
            if desen and not re.match(desen, v):
                # Değer ve beklenen biçim modele geri söylenir (ikinci koşu I07: "servis: biçime uymuyor" iletisiyle
                # model üç denemede de aynı hatayı yaptı)
                ipucu = {"servis": "yalnız servis adı, küçük harf, boşluksuz (ör. uygulama, webd)",
                         "paket": "yalnız paket adı, küçük harf, boşluksuz", "kullanici": "küçük harf kullanıcı adı, boşluksuz"}
                raise SemaHatasi(f"{ad}: {v[:60]!r} biçime uymuyor; beklenen: {ipucu.get(alan.get('desen'), desen)}")
            if len(v) > alan.get("en_uzun", 500):
                raise SemaHatasi(f"{ad}: çok uzun")
        out[ad] = v
    return out


def alintila(deger, os_):
    if isinstance(deger, list):
        return " ".join(alintila(x, os_) for x in deger)
    if isinstance(deger, bool):
        deger = "1" if deger else "0"
    s = str(deger)
    if os_ == "windows":
        return "'" + s.replace("'", "''") + "'"
    return shlex.quote(s)


def komut_sec(tablo, sunucu):
    """Bir komut tablosundan sunucuya uyanı: önce aile (debian/rhel/alpine), sonra os (linux/windows)."""
    if not tablo:
        return None
    return tablo.get(sunucu.aile) or tablo.get(sunucu.os)


def doldur(sablon, parametreler, os_):
    def degistir(m):
        ad = m.group(1)
        if ad not in parametreler:
            raise SemaHatasi(f"komut şablonunda bilinmeyen yer tutucu: {ad}")
        return alintila(parametreler[ad], os_)
    return re.sub(r"\{([a-z_][a-z0-9_]*)\}", degistir, sablon)


# ---------------------------------------------------------------- çıktı şeması
def _cevir(deger, tip):
    deger = deger.strip()
    if tip == "tamsayi":
        return int(deger.rstrip("%"))
    if tip == "ondalik":
        return float(deger.replace(",", "."))
    return deger


def cikti_dogrula(sema, metin, parametreler=None):
    """(veri, hata). hata None ise çıktı şemaya uyuyor. `beklenen` ({alan: değer}) ve `yasak` ({alan: değer})
    son koşullardır: komut sıfırla bitse de beklenen durum yoksa adım başarısızdır."""
    veri, hata = _cikti_ayristir(sema or {"bicim": "ham"}, metin)
    if hata or not sema:
        return veri, hata
    p = parametreler or {}
    doldur_ = lambda v: re.sub(r"\{([a-z_][a-z0-9_]*)\}", lambda m: str(p.get(m.group(1), m.group(0))), str(v))  # noqa: E731
    kayitlar = veri if isinstance(veri, list) else [veri] if isinstance(veri, dict) else []
    for k, v in (sema.get("beklenen") or {}).items():
        for r in kayitlar:
            if str(r.get(k)) != doldur_(v):
                return veri, f"son koşul tutmadı: {k} beklenen {doldur_(v)!r}, gelen {r.get(k)!r}"
    for k, v in (sema.get("yasak") or {}).items():
        kotu = [r for r in kayitlar if str(r.get(k)) == str(v)]
        if kotu:
            return veri, f"son koşul tutmadı: {len(kotu)} kayıtta {k}={v!r} ({kotu[0]})"
    return veri, None


def _cikti_ayristir(sema, metin):
    bicim = sema.get("bicim", "ham")
    metin = metin or ""
    if bicim == "ham":
        if sema.get("bos_olamaz") and not metin.strip():
            # İkinci koşu T02: arama komutu hiçbir şey bulmadı ama adım "başarılı" sayıldı ve kol başarı bildirdi
            return metin, "çıktı boş: komut hiçbir şey bulmadı ya da yazdırmadı"
        return metin, None
    if bicim == "json":
        try:
            return json.loads(metin), None
        except ValueError as e:
            return None, f"JSON değil: {e}"
    alanlar = sema.get("alanlar") or {}
    if bicim == "anahtar_deger":
        veri, yabanci = {}, []
        for satir in metin.splitlines():
            if not satir.strip():
                continue
            if "=" not in satir:
                yabanci.append(satir.strip())
                continue
            k, v = satir.split("=", 1)
            k = k.strip()
            try:
                veri[k] = _cevir(v, alanlar.get(k, "metin"))
            except ValueError:
                return veri, f"'{k}' alanı {alanlar.get(k)} olmalı, gelen: {v.strip()[:40]!r}"
        eksik = [k for k in sema.get("zorunlu", list(alanlar)) if k not in veri]
        if eksik:
            ek = f"; anahtar=değer olmayan satırlar: {yabanci[:3]}" if yabanci else ""
            return veri, f"beklenen alanlar yok: {eksik}{ek}"
        return veri, None
    if bicim == "satirlar":
        ayr = sema.get("ayirici", "|")
        adlar = list(alanlar)
        satirlar = []
        for satir in metin.splitlines():
            if not satir.strip():
                continue
            parca = satir.split(ayr)
            if len(parca) != len(adlar):
                return satirlar, f"satır {len(parca)} alan taşıyor, beklenen {len(adlar)} ({ayr!r} ile): {satir[:80]!r}"
            try:
                satirlar.append({a: _cevir(p, alanlar[a]) for a, p in zip(adlar, parca)})
            except ValueError:
                return satirlar, f"satırda tip uyuşmazlığı: {satir[:80]!r}"
        if sema.get("en_az_satir", 0) > len(satirlar):
            return satirlar, f"en az {sema['en_az_satir']} satır bekleniyordu"
        return satirlar, None
    return metin, None


# ---------------------------------------------------------------- katalog ve sürümleme
def _simdi():
    return datetime.datetime.now().isoformat(timespec="seconds")


def tanim_dogrula(t):
    """Beceri tanımının kendisini denetler; hatalar listesi (boşsa geçerli)."""
    h = []
    for alan in ("ad", "surum", "baslik", "aciklama", "risk", "tur"):
        if alan not in t:
            h.append(f"eksik alan: {alan}")
    if t.get("tur") not in TURLER:
        h.append("tur uzak/yerel/zincir/yonetim olmalı")
    if t.get("tur") == "yonetim" and not t.get("islem"):
        h.append("yönetim becerisinde islem (kod işleyicisinin adı) yok")
    if not isinstance(t.get("risk"), int) or not 0 <= t.get("risk", -1) <= 4:
        h.append("risk 0-4 olmalı")
    for ad, alan in (t.get("girdi") or {}).items():
        if alan.get("tip", "metin") not in TIPLER:
            h.append(f"girdi {ad}: bilinmeyen tip")
    if (t.get("cikti") or {}).get("bicim", "ham") not in CIKTI_BICIMLERI:
        h.append("çıktı biçimi geçersiz")
    if t.get("tur") == "uzak" and not t.get("komut"):
        h.append("uzak beceride komut yok")
    if t.get("tur") == "zincir" and not t.get("adimlar"):
        h.append("zincir beceride adım yok")
    if t.get("risk", 0) >= 2 and t.get("tur") == "uzak":
        if not t.get("kuru"):
            h.append("değiştiren beceride kuru çalıştırma tanımı yok")
        if not t.get("geri_al"):
            h.append("değiştiren beceride geri alma tanımı yok")
    if "zaman_asimi" in t and (not isinstance(t["zaman_asimi"], int) or t["zaman_asimi"] <= 0):
        h.append("zaman_asimi pozitif tamsayı olmalı")
    return h


def _komut_metinleri(t):
    """Risk sınıflaması becerinin asıl komutlarına bakar. Geri alma ayrı bir eylemdir ve becerinin onay düzeyiyle
    çalışır; kuru çalıştırma sunucuyu değiştirmez (ör. `apt-get install -s`)."""
    return [v for v in (t.get("komut") or {}).values() if isinstance(v, str)]


class Katalog:
    def __init__(self, dizin=None, denetim=DENETIM):
        self.dizin = dizin or SKILLS
        self.betik_dizini = self.dizin / "_betikler"
        self.denetim = denetim
        self.beceriler = {}
        self.hatalar = {}
        self.yukle()

    def yukle(self):
        self.beceriler, self.hatalar = {}, {}
        for p in sorted(self.dizin.glob("*/beceri.json")):
            if p.parent.name.startswith("_"):
                continue
            try:
                t = json.loads(p.read_text(encoding="utf-8"))
            except ValueError as e:
                self.hatalar[p.parent.name] = [f"JSON okunamadı: {e}"]
                continue
            h = tanim_dogrula(t)
            if h:
                self.hatalar[t.get("ad", p.parent.name)] = h
                continue
            self.beceriler[t["ad"]] = t
        return self

    def __getitem__(self, ad):
        return self.beceriler[ad]

    def __contains__(self, ad):
        return ad in self.beceriler

    # --- risk
    def etkin_risk(self, t, parametreler=None):
        """(düzey, gerekçe): beyan ile koddan hesaplananın büyüğü. betik_calistir için betiğin kendisi de sınıflanır."""
        hesap, neden = risk_sinifla(_komut_metinleri(t))
        if t["tur"] == "zincir":
            for a in t.get("adimlar", []):
                if a.get("beceri") in self.beceriler:
                    r, n = self.etkin_risk(self.beceriler[a["beceri"]])
                    if r > hesap:
                        hesap, neden = r, f"adım {a['beceri']}: {n}"
        if parametreler and parametreler.get("betik"):
            r, n = risk_sinifla([self.betik_oku(parametreler["betik"])])
            if r > hesap:
                hesap, neden = r, f"betik {parametreler['betik']}: {n}"
        # Parametreye bağlı risk (D1): ör. yama_uygula'da yeniden_baslatma=gerekirse → düzey 4 (hemen yeniden başlatma)
        for alan, tablo in (t.get("risk_kurali") or {}).items():
            v = str((parametreler or {}).get(alan, (t.get("girdi") or {}).get(alan, {}).get("varsayilan", "")))
            if v in tablo and tablo[v] > hesap:
                hesap, neden = tablo[v], f"{alan}={v} (düzey {tablo[v]})"
        if hesap > t["risk"]:
            return hesap, f"kod sınıflaması düzeyi yükseltti: {neden}"
        return t["risk"], "beyan"

    def ozet(self, ad):
        t = self.beceriler[ad]
        r, n = self.etkin_risk(t)
        return {"ad": ad, "baslik": t["baslik"], "aciklama": t["aciklama"], "risk": r, "risk_beyan": t["risk"],
                "risk_neden": n, "tur": t["tur"], "surum": t["surum"], "etiketler": t.get("etiketler", []),
                "girdi": {k: {kk: vv for kk, vv in v.items()} | ({"secenekler": secenekler(v)} if v.get("kaynak") else {})
                          for k, v in (t.get("girdi") or {}).items()},
                "cikti": t.get("cikti"), "geri_al": bool(t.get("geri_al")), "kuru": bool(t.get("kuru")),
                "isletim": sorted((t.get("komut") or {}).keys())}

    def liste(self):
        return [self.ozet(a) for a in sorted(self.beceriler)]

    # --- betik kütüphanesi
    def betik_oku(self, ad):
        return (self.betik_dizini / ad / "betik.sh").read_text(encoding="utf-8")

    def betik_meta(self, ad):
        return json.loads((self.betik_dizini / ad / "meta.json").read_text(encoding="utf-8"))

    # --- sürümleme: her kayıt bir dizindir; eski sürüm dizinin gecmis/v<N>/ altına kopyalanır
    def _kayit_dizini(self, tur, ad):
        if tur == "betik":
            d = self.betik_dizini / ad
        else:
            d = self.dizin / ad
        if not d.is_dir() or not re.match(r"^[a-z0-9_]+$", ad):
            raise KeyError(f"böyle bir {tur} yok: {ad}")
        return d

    def _meta_yolu(self, tur, d):
        return d / ("meta.json" if tur == "betik" else "beceri.json")

    def _dosyalar(self, d):
        return {p.name: p.read_text(encoding="utf-8") for p in sorted(d.iterdir()) if p.is_file()}

    def yeni_surum(self, tur, ad, dosyalar, degistiren, neden):
        """Kayda yeni sürüm yazar. dosyalar: {dosya_adi: yeni_icerik} (verilmeyen dosyalar aynen kalır).
        Dönüş: {eski_surum, yeni_surum, risk_onceki, risk_yeni, risk_neden, fark}."""
        d = self._kayit_dizini(tur, ad)
        meta_yolu = self._meta_yolu(tur, d)
        eski_meta = json.loads(meta_yolu.read_text(encoding="utf-8"))
        eski_dosyalar = self._dosyalar(d)
        eski_n = int(eski_meta.get("surum", 1))
        yeni_dosyalar = {**eski_dosyalar, **dosyalar}
        yeni_meta = json.loads(yeni_dosyalar[meta_yolu.name])
        yeni_meta["surum"] = eski_n + 1
        yeni_meta["degisiklik"] = {"zaman": _simdi(), "degistiren": degistiren, "neden": neden, "onceki_surum": eski_n}
        if tur == "beceri":
            h = tanim_dogrula(yeni_meta)
            if h:
                raise SemaHatasi(f"yeni sürüm geçersiz: {h}")
            risk_onceki = self.etkin_risk(eski_meta)[0]
            risk_yeni, risk_neden = self.etkin_risk(yeni_meta)
            yeni_meta["risk"] = max(yeni_meta["risk"], risk_yeni)
            h = tanim_dogrula(yeni_meta)   # yükselen düzey kuru çalıştırma ve geri alma ister (koruma 7)
            if h:
                raise SemaHatasi(f"yeni sürüm düzey {yeni_meta['risk']} oldu ({risk_neden}) ama: {h}")
        else:
            risk_onceki = risk_sinifla([eski_dosyalar.get("betik.sh", "")])[0]
            risk_yeni, risk_neden = risk_sinifla([yeni_dosyalar.get("betik.sh", "")])
            yeni_meta["risk"] = max(int(yeni_meta.get("risk", 0)), risk_yeni)
        yeni_dosyalar[meta_yolu.name] = json.dumps(yeni_meta, ensure_ascii=False, indent=2) + "\n"
        # eski sürümü sakla
        arsiv = d / "gecmis" / f"v{eski_n}"
        arsiv.mkdir(parents=True, exist_ok=True)
        for n, icerik in eski_dosyalar.items():
            (arsiv / n).write_text(icerik, encoding="utf-8")
        for n, icerik in yeni_dosyalar.items():
            if "/" in n or "\\" in n or n.startswith("."):
                raise SemaHatasi(f"geçersiz dosya adı: {n}")
            (d / n).write_text(icerik, encoding="utf-8")
        fark = self._fark_metni(eski_dosyalar, yeni_dosyalar, f"v{eski_n}", f"v{eski_n + 1}")
        sonuc = {"kayit": tur, "ad": ad, "eski_surum": eski_n, "yeni_surum": eski_n + 1, "risk_onceki": risk_onceki,
                 "risk_yeni": yeni_meta["risk"], "risk_neden": risk_neden, "risk_yukseldi": yeni_meta["risk"] > risk_onceki,
                 "fark": fark, "degistiren": degistiren, "neden": neden}
        self.denetim.yaz("beceri_degisti", **{k: v for k, v in sonuc.items() if k != "fark"}, fark_ozet=fark[:2000])
        self.yukle()
        return sonuc

    def _fark_metni(self, a, b, ea, eb):
        out = []
        for n in sorted(set(a) | set(b)):
            if a.get(n) != b.get(n):
                out.extend(difflib.unified_diff((a.get(n) or "").splitlines(), (b.get(n) or "").splitlines(),
                                                f"{ea}/{n}", f"{eb}/{n}", lineterm=""))
        return "\n".join(out)

    def surum_dosyalari(self, tur, ad, surum):
        d = self._kayit_dizini(tur, ad)
        meta = json.loads(self._meta_yolu(tur, d).read_text(encoding="utf-8"))
        if int(meta.get("surum", 1)) == int(surum):
            return {k: v for k, v in self._dosyalar(d).items()}
        arsiv = d / "gecmis" / f"v{int(surum)}"
        if not arsiv.is_dir():
            raise KeyError(f"{ad}: v{surum} yok")
        return self._dosyalar(arsiv)

    def gecmis(self, tur, ad):
        d = self._kayit_dizini(tur, ad)
        out = []
        surumler = sorted(int(p.name[1:]) for p in (d / "gecmis").glob("v*") if p.name[1:].isdigit()) \
            if (d / "gecmis").exists() else []
        meta = json.loads(self._meta_yolu(tur, d).read_text(encoding="utf-8"))
        for n in surumler + [int(meta.get("surum", 1))]:
            m = json.loads(self.surum_dosyalari(tur, ad, n)[self._meta_yolu(tur, d).name])
            out.append({"surum": n, "risk": m.get("risk"), "degisiklik": m.get("degisiklik"),
                        "guncel": n == int(meta.get("surum", 1))})
        return out

    def fark(self, tur, ad, s1, s2):
        return self._fark_metni(self.surum_dosyalari(tur, ad, s1), self.surum_dosyalari(tur, ad, s2), f"v{s1}", f"v{s2}")

    def geri_don(self, tur, ad, surum, degistiren="operatör"):
        """Eski bir sürümün içeriğini YENİ sürüm olarak yazar (geçmiş doğrusal kalır)."""
        eski = self.surum_dosyalari(tur, ad, surum)
        return self.yeni_surum(tur, ad, eski, degistiren, f"v{surum} sürümüne geri dönüş")

    def fabrika_ayari(self, kaynak):
        """Bench ve testler için: katalog dizinini bir kopyadan yeniler."""
        shutil.rmtree(self.dizin, ignore_errors=True)
        shutil.copytree(kaynak, self.dizin)
        return self.yukle()
