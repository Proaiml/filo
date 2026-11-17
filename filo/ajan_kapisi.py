"""Ajan kapısı: yönetilen sunuculardaki `filo-ajan` (Go) ajanlarının bağlandığı uç (yalnız standart kitaplık).

Ajan sunucuda port açmaz; bu kapıya dışarı doğru bağlanır. Kapı yalnız 127.0.0.1'e bağlanır: aynı makinedeki istemciler
ve Docker Desktop'un `host.docker.internal` vekili üzerinden laboratuvar konteynerleri ulaşır (güvenlik duvarı ayarı
gerekmez). Gerçek bir ağda kapının önüne TLS sonlandıran bir vekil konmalıdır; laboratuvarda trafik düz HTTP'dir ve
gizliliği değil, imza ile bütünlüğü ve kimliği korur.

Ajan protokolü (/ajan/v1/...):
    POST kayit    {belirtec, sunucu, surum, sistem}  tek kullanımlık belirteç -> {ajan_kimligi, gizli}
    POST kalp     {surum, calisan}                   -> {iptal: [...]}
    POST yokla    {bekle}                            uzun yoklama -> {isler: [zarf], iptal: [...]}
    POST sonuc    {kimlik, durum, cikis_kodu, stdout, stderr, sure, kesildi, ...}
    GET  dosya?is=<kimlik>                           dosya alma işinin içeriği
Kayıt dışındaki her istek imzalıdır (X-Filo-Ajan, X-Filo-Zaman, X-Filo-Nonce, X-Filo-Imza); zaman damgası 60 sn'den
eski ya da nonce tekrarlıysa reddedilir. Cevaplar isteğin nonce'una bağlı imzayla döner. İş paketi {govde, imza}
biçimindedir; imza iş anahtarıyla gövdenin tam metnine atılır (bkz. ajan/imza.go).

Yerel API (/yerel/v1/...; yalnız `results/ajanlar/yerel.anahtar` dosyasını okuyabilen yerel süreçler için):
    POST is {sunucu, tur, betik, zaman_asimi, cikti_siniri, kullanici, dosya}  -> {kimlik}
    GET  sonuc?is=<kimlik>&bekle=2                   -> {durum: bekliyor|alindi|bitti|iptal|alinmadi, sonuc}
    POST iptal {is}
    GET  ajanlar                                     ajan durumları (gizli bilgi yok)
    POST belirtec {sunucu}                           -> {belirtec}   (yalnız bir kez gösterilir)
    POST kaldir {sunucu}

Gizli anahtarlar `ayarlar/ajan_gizli.json` (git dışında) içinde durur; hiçbir uçtan, kayda ya da modele dönmez.
Kayıt belirteçlerinin yalnız özeti saklanır.
"""
import collections
import datetime
import hashlib
import hmac
import http.server
import json
import secrets
import select
import socket
import threading
import time
import urllib.parse
import uuid

from . import AYARLAR, ROOT, SONUC
from .denetim import DENETIM
from .erisim import DURDURMA

AJAN_SURUM = "0.2.0"
AJAN_DIZINI = SONUC / "ajanlar"
GIZLI_DOSYA = AYARLAR / "ajan_gizli.json"
AYAR_DOSYASI = AYARLAR / "ajan.json"
DOSYA_KOKLERI = (ROOT / "skills" / "_dosyalar", ROOT / "ajan" / "cikti")
VARSAYILAN_AYAR = {
    "kapi_port": 8795,
    "sunucular_icin_adres": "http://host.docker.internal:8795",
    "canli_sinir_sn": 35,
    "alim_suresi_sn": 8,
    "belirtec_suresi_dk": 15,
    "kullanici": "filo",
}
ZAMAN_PENCERESI = 60


def ayar():
    a = dict(VARSAYILAN_AYAR)
    if AYAR_DOSYASI.exists():
        a.update(json.loads(AYAR_DOSYASI.read_text(encoding="utf-8")))
    return a


def _simdi():
    return datetime.datetime.now().isoformat(timespec="seconds")


# ---------------------------------------------------------------- imza (ajan/imza.go ile aynı)
def _hmac(anahtar, mesaj):
    return hmac.new(anahtar, mesaj.encode("utf-8") if isinstance(mesaj, str) else mesaj, hashlib.sha256)


def anahtar_turet(gizli_hex):
    g = bytes.fromhex(gizli_hex)
    return _hmac(g, "filo-istek-v1").digest(), _hmac(g, "filo-is-v1").digest()


def _ozet(govde):
    return hashlib.sha256(govde or b"").hexdigest()


def istek_imzasi(anahtar, yontem, yol, zaman, nonce, govde):
    return _hmac(anahtar, f"{yontem}\n{yol}\n{zaman}\n{nonce}\n{_ozet(govde)}").hexdigest()


def yanit_imzasi(anahtar, nonce, govde):
    return _hmac(anahtar, f"yanit\n{nonce}\n{_ozet(govde)}").hexdigest()


def is_zarfi(is_anahtari, is_):
    govde = json.dumps(is_, ensure_ascii=False, separators=(",", ":"))
    return {"govde": govde, "imza": _hmac(is_anahtari, "is\n" + govde).hexdigest()}


class KapiHatasi(Exception):
    def __init__(self, kod, metin):
        super().__init__(metin)
        self.kod = kod


# ---------------------------------------------------------------- kayıt defteri
class Defter:
    """Ajan kayıtları (results/ajanlar/kayit.json), belirteç özetleri ve gizli anahtarlar (ayarlar/ajan_gizli.json)."""

    def __init__(self, dizin=None, gizli_dosya=None):
        self.dizin = dizin or AJAN_DIZINI
        self.gizli_dosya = gizli_dosya or GIZLI_DOSYA
        self.kilit = threading.RLock()
        self.dizin.mkdir(parents=True, exist_ok=True)

    def _oku(self, yol, bos):
        """Dosya yoksa `bos`. D0-c: Windows'ta yeni yazılıp yerine konan dosya bir an başka bir süreçte (virüs tarayıcı,
        dizinleyici, kapının dosyasını okuyan komut satırı) açık kalabilir; okuma PermissionError verir. Eskiden bu da
        `bos` sayılıyordu: belirteç deposu boş okununca paralel kurulumda geçerli belirteç "geçersiz" diye reddediliyor,
        sonraki yazma da öteki belirteçleri siliyordu (testlerden sonra rastgele bir ajanın kayıtsız kalması). Artık
        geçici hata birkaç kez yeniden denenir; sürerse hata yükselir (sessizce boş sayılmaz)."""
        for deneme in range(20):
            try:
                return json.loads(yol.read_text(encoding="utf-8"))
            except FileNotFoundError:
                return bos
            except (OSError, ValueError):
                if deneme == 19:
                    raise
                time.sleep(0.05 * (deneme + 1))

    def _yaz(self, yol, veri):
        yol.parent.mkdir(parents=True, exist_ok=True)
        gecici = yol.with_suffix(".yeni")
        gecici.write_text(json.dumps(veri, ensure_ascii=False, indent=1), encoding="utf-8")
        for deneme in range(20):
            try:
                gecici.replace(yol)
                return
            except PermissionError:
                if deneme == 19:
                    raise
                time.sleep(0.05 * (deneme + 1))

    @property
    def kayit_yolu(self):
        return self.dizin / "kayit.json"

    @property
    def belirtec_yolu(self):
        return self.dizin / "belirtecler.json"

    def ajanlar(self):
        return self._oku(self.kayit_yolu, {})

    def ajanlar_yaz(self, v):
        self._yaz(self.kayit_yolu, v)

    def gizliler(self):
        return self._oku(self.gizli_dosya, {})

    def gizliler_yaz(self, v):
        self._yaz(self.gizli_dosya, v)

    def belirtecler(self):
        return self._oku(self.belirtec_yolu, {})

    def belirtecler_yaz(self, v):
        self._yaz(self.belirtec_yolu, v)


# ---------------------------------------------------------------- kapı
class AjanKapisi:
    def __init__(self, port=None, defter=None, denetim=DENETIM, durdurma=DURDURMA, kayit_dinleyici=None,
                 yerel_anahtar_yolu=None):
        a = ayar()
        self.port = port if port is not None else a["kapi_port"]
        self.canli_sinir = a["canli_sinir_sn"]
        self.alim_suresi = a["alim_suresi_sn"]
        self.belirtec_suresi = a["belirtec_suresi_dk"]
        self.defter = defter or Defter()
        self.denetim, self.durdurma = denetim, durdurma
        self.kayit_dinleyiciler = [kayit_dinleyici] if kayit_dinleyici else []
        self.kosul = threading.Condition()
        self.kuyruk = collections.defaultdict(collections.deque)   # ajan -> iş kimlikleri
        self.isler = {}
        self.iptal_bekleyen = collections.defaultdict(set)          # ajan -> iptal edilecek iş kimlikleri
        self.nonce = {}
        self.son_temas = {}                                          # ajan -> time.time()
        self.yoklayan = collections.Counter()                        # ajan -> açık uzun yoklama sayısı
        self.httpd = None
        yol = yerel_anahtar_yolu or (self.defter.dizin / "yerel.anahtar")
        if not yol.exists():
            yol.write_text(secrets.token_hex(32), encoding="utf-8")
        self.yerel_anahtar = yol.read_text(encoding="utf-8").strip()
        self.yerel_anahtar_yolu = yol

    # ------------------------------------------------------------ belirteç ve kayıt
    def belirtec_uret(self, sunucu, sure_dk=None):
        b = secrets.token_urlsafe(24)
        with self.defter.kilit:
            v = self.defter.belirtecler()
            simdi = time.time()
            v = {k: x for k, x in v.items() if x["son"] > simdi and not x.get("kullanildi")}
            v[hashlib.sha256(b.encode()).hexdigest()] = {"sunucu": sunucu, "son": simdi + 60 * (sure_dk or self.belirtec_suresi),
                                                         "olusturma": _simdi()}
            self.defter.belirtecler_yaz(v)
        self.denetim.yaz("ajan_belirteci", sunucu=sunucu, sure_dk=sure_dk or self.belirtec_suresi)
        return b

    def kayit(self, govde, istemci=""):
        b = str(govde.get("belirtec") or "")
        sunucu = str(govde.get("sunucu") or "")
        ozet = hashlib.sha256(b.encode()).hexdigest()
        with self.defter.kilit:
            v = self.defter.belirtecler()
            k = v.get(ozet)
            if not k or k.get("kullanildi") or k["son"] < time.time():
                self.denetim.yaz("ajan_kayit_reddi", sunucu=sunucu, neden="belirteç geçersiz, kullanılmış ya da süresi dolmuş",
                                 istemci=istemci)
                raise KapiHatasi(401, "kayıt belirteci geçersiz")
            if k["sunucu"].upper() != sunucu.upper():
                self.denetim.yaz("ajan_kayit_reddi", sunucu=sunucu, neden=f"belirteç {k['sunucu']} için verilmiş",
                                 istemci=istemci)
                raise KapiHatasi(403, "belirteç bu sunucu için değil")
            k["kullanildi"] = _simdi()
            self.defter.belirtecler_yaz(v)
            kimlik = "ajan-" + uuid.uuid4().hex[:12]
            gizli = secrets.token_hex(32)
            ajanlar = self.defter.ajanlar()
            gizliler = self.defter.gizliler()
            for eski_kimlik, eski in list(ajanlar.items()):        # aynı sunucunun eski ajanı geçersiz olur
                if eski["sunucu"].upper() == k["sunucu"].upper() and eski.get("durum") != "kaldirildi":
                    eski["durum"] = "kaldirildi"
                    eski["kaldirilma"] = _simdi()
                    eski["kaldirma_nedeni"] = "aynı sunucuya yeni ajan kaydoldu"
                    gizliler.pop(eski_kimlik, None)
            ajanlar[kimlik] = {"kimlik": kimlik, "sunucu": k["sunucu"], "surum": str(govde.get("surum", ""))[:32],
                               "sistem": govde.get("sistem") if isinstance(govde.get("sistem"), dict) else {},
                               "kayit": _simdi(), "durum": "kayitli"}
            gizliler[kimlik] = gizli
            self.defter.gizliler_yaz(gizliler)
            self.defter.ajanlar_yaz(ajanlar)
        self.son_temas[kimlik] = time.time()
        self.denetim.yaz("ajan_kayit", sunucu=k["sunucu"], ajan=kimlik, surum=ajanlar[kimlik]["surum"],
                         sistem=ajanlar[kimlik]["sistem"])
        for d in self.kayit_dinleyiciler:
            threading.Thread(target=self._dinleyici, args=(d, dict(ajanlar[kimlik])), daemon=True).start()
        return {"ajan_kimligi": kimlik, "gizli": gizli}

    def _dinleyici(self, d, ajan):
        try:
            d(ajan)
        except Exception as e:  # noqa: BLE001 - dinleyici hatası kapıyı düşürmesin
            self.denetim.yaz("ajan_dinleyici_hatasi", sunucu=ajan.get("sunucu"), hata=f"{type(e).__name__}: {e}")

    def kaldir(self, sunucu, neden="operatör"):
        n = 0
        with self.defter.kilit:
            ajanlar, gizliler = self.defter.ajanlar(), self.defter.gizliler()
            for kimlik, a in ajanlar.items():
                if a["sunucu"].upper() == sunucu.upper() and a.get("durum") != "kaldirildi":
                    a.update(durum="kaldirildi", kaldirilma=_simdi(), kaldirma_nedeni=neden)
                    gizliler.pop(kimlik, None)
                    n += 1
            self.defter.gizliler_yaz(gizliler)
            self.defter.ajanlar_yaz(ajanlar)
        self.denetim.yaz("ajan_kaldirildi", sunucu=sunucu, neden=neden, sayi=n)
        return n

    # ------------------------------------------------------------ istek doğrulama
    def dogrula(self, yontem, yol, basliklar, govde):
        """İmzalı ajan isteğini doğrular; (ajan kaydı, istek nonce'u, iş anahtarı)."""
        kimlik = basliklar.get("X-Filo-Ajan") or ""
        zaman = basliklar.get("X-Filo-Zaman") or ""
        nonce = basliklar.get("X-Filo-Nonce") or ""
        imza = (basliklar.get("X-Filo-Imza") or "").lower()
        if not (kimlik and zaman and nonce and imza):
            raise KapiHatasi(401, "imzasız istek")
        ajanlar = self.defter.ajanlar()
        a = ajanlar.get(kimlik)
        if a and a.get("durum") == "kaldirildi":
            raise KapiHatasi(410, "ajan kaldırıldı")
        gizli = self.defter.gizliler().get(kimlik)
        if not a or not gizli:
            raise KapiHatasi(401, "bilinmeyen ajan")
        try:
            fark = abs(time.time() - int(zaman))
        except ValueError:
            raise KapiHatasi(401, "zaman damgası geçersiz") from None
        if fark > ZAMAN_PENCERESI:
            self.denetim.yaz("ajan_imza_reddi", sunucu=a["sunucu"], ajan=kimlik, neden=f"zaman farkı {int(fark)} sn")
            raise KapiHatasi(401, "zaman damgası pencere dışında")
        istek_a, is_a = anahtar_turet(gizli)
        if not hmac.compare_digest(istek_imzasi(istek_a, yontem, yol, zaman, nonce, govde), imza):
            self.denetim.yaz("ajan_imza_reddi", sunucu=a["sunucu"], ajan=kimlik, neden="imza tutmuyor", yol=yol)
            raise KapiHatasi(401, "imza tutmuyor")
        with self.kosul:
            simdi = time.time()
            for n_, t in list(self.nonce.items()):
                if t < simdi - 2 * ZAMAN_PENCERESI:
                    del self.nonce[n_]
            if nonce in self.nonce:
                raise KapiHatasi(401, "nonce tekrarı")
            self.nonce[nonce] = simdi
        self.son_temas[kimlik] = time.time()
        return a, nonce, is_a

    # ------------------------------------------------------------ ajan uçları
    def kalp(self, a, govde):
        kimlik = a["kimlik"]
        with self.defter.kilit:
            ajanlar = self.defter.ajanlar()
            if kimlik in ajanlar:
                ajanlar[kimlik]["son_kalp"] = _simdi()
                ajanlar[kimlik]["surum"] = str(govde.get("surum", ajanlar[kimlik].get("surum", "")))[:32]
                self.defter.ajanlar_yaz(ajanlar)
        return {"iptal": self._iptaller(kimlik)}

    def _iptaller(self, kimlik):
        with self.kosul:
            return self._iptaller_kilitli(kimlik)

    def yokla(self, a, govde, kapali_mi=lambda: False):
        """Uzun yoklama. `kapali_mi`: istemci bağlantıyı kapattı mı (ölen ajanın bekleyen yoklaması iş almasın)."""
        kimlik = a["kimlik"]
        bekle = max(0, min(int(govde.get("bekle", 25) or 0), 25))
        son = time.time() + bekle
        with self.kosul:
            self.yoklayan[kimlik] += 1
            try:
                while True:
                    if kapali_mi():
                        return None
                    iptal = self._iptaller_kilitli(kimlik)
                    if not self.durdurma.basili() and self.kuyruk[kimlik]:
                        verilen = []
                        while self.kuyruk[kimlik] and len(verilen) < 4:
                            k = self.kuyruk[kimlik].popleft()
                            j = self.isler.get(k)
                            if not j or j["durum"] != "bekliyor":
                                continue
                            j["durum"], j["alinma"] = "alindi", time.time()
                            verilen.append(j["zarf"])
                        self.kosul.notify_all()
                        if verilen or iptal:
                            return {"isler": verilen, "iptal": iptal}
                    if iptal:
                        return {"isler": [], "iptal": iptal}
                    kalan = son - time.time()
                    if kalan <= 0:
                        return {"isler": [], "iptal": []}
                    self.kosul.wait(min(kalan, 1.0))
            finally:
                self.yoklayan[kimlik] -= 1

    def geri_koy(self, zarflar):
        """Cevabı yazılamayan yoklamanın işleri kuyruğa geri döner."""
        with self.kosul:
            for z in zarflar:
                k = json.loads(z["govde"])["kimlik"]
                j = self.isler.get(k)
                if j and j["durum"] == "alindi":
                    j["durum"] = "bekliyor"
                    self.kuyruk[j["ajan"]].appendleft(k)
            self.kosul.notify_all()

    def _iptaller_kilitli(self, kimlik):
        if self.durdurma.basili():
            for k, j in self.isler.items():
                if j["ajan"] == kimlik and j["durum"] == "alindi":
                    self.iptal_bekleyen[kimlik].add(k)
        return sorted(self.iptal_bekleyen.pop(kimlik, set()))

    def sonuc(self, a, govde):
        k = str(govde.get("kimlik") or "")
        with self.kosul:
            j = self.isler.get(k)
            if not j or j["ajan"] != a["kimlik"]:
                raise KapiHatasi(404, "böyle bir iş yok")
            if j["durum"] in ("bitti",):
                return {"tamam": True}
            alanlar = ("durum", "cikis_kodu", "stdout", "stderr", "sure", "kesildi", "kullanici", "neden")
            j["sonuc"] = {x: govde.get(x) for x in alanlar}
            j["durum"] = "bitti"
            self.kosul.notify_all()
        return {"tamam": True}

    def dosya(self, a, sorgu):
        k = sorgu.get("is", "")
        with self.kosul:
            j = self.isler.get(k)
            if not j or j["ajan"] != a["kimlik"] or j["durum"] != "alindi" or not j.get("dosya_yolu"):
                raise KapiHatasi(404, "bu iş için dosya yok")
            yol = j["dosya_yolu"]
        return yol.read_bytes()

    # ------------------------------------------------------------ yerel API
    def ajan_bul(self, sunucu):
        """Sunucunun etkin (kaldırılmamış) ajan kaydı ya da None."""
        for a in self.defter.ajanlar().values():
            if a["sunucu"].upper() == str(sunucu).upper() and a.get("durum") != "kaldirildi":
                return a
        return None

    def canli_mi(self, kimlik):
        """Canlı: son imzalı istek `canli_sinir` saniyeden yeni (kalp 10 sn'de bir gelir). Açık bir yoklama tek başına
        canlılık sayılmaz: ölen ajanın bağlantısı vekilde bir süre açık görünebilir."""
        return time.time() - self.son_temas.get(kimlik, 0) < self.canli_sinir

    def durumlar(self):
        out = {}
        for a in self.defter.ajanlar().values():
            if a.get("durum") == "kaldirildi":
                continue
            canli = self.canli_mi(a["kimlik"])
            out[a["sunucu"]] = {"ajan": a["kimlik"], "surum": a.get("surum"), "kayit": a.get("kayit"),
                                "son_kalp": a.get("son_kalp"), "durum": "canli" if canli else "ajan yok",
                                "sistem": a.get("sistem", {}),
                                "son_temas_sn": round(time.time() - self.son_temas[a["kimlik"]], 1)
                                if a["kimlik"] in self.son_temas else None}
        return out

    def is_gonder(self, sunucu, tur="calistir", betik="", zaman_asimi=60, cikti_siniri=65536, kullanici=None,
                  dosya=None):
        a = self.ajan_bul(sunucu)
        if not a:
            raise KapiHatasi(404, f"{sunucu}: kayıtlı ajan yok")
        if not self.canli_mi(a["kimlik"]):
            raise KapiHatasi(409, f"{sunucu}: ajan yok (son temas {self.canli_sinir} sn'den eski)")
        if self.durdurma.basili():
            raise KapiHatasi(409, "durdurma düğmesi basılı")
        gizli = self.defter.gizliler().get(a["kimlik"])
        if not gizli:
            raise KapiHatasi(409, f"{sunucu}: ajan anahtarı yok")
        if not zaman_asimi or int(zaman_asimi) <= 0:
            raise KapiHatasi(400, "zaman_asimi zorunlu ve pozitif olmalı")
        kimlik = uuid.uuid4().hex
        simdi = int(time.time())
        is_ = {"kimlik": kimlik, "ajan": a["kimlik"], "tur": tur, "betik": betik or "", "zaman_asimi": int(zaman_asimi),
               "cikti_siniri": int(cikti_siniri), "kullanici": ayar()["kullanici"] if kullanici is None else kullanici,
               "olusturma": simdi, "gecerlilik": simdi + self.alim_suresi + 30}
        dosya_yolu = None
        if tur == "dosya_al":
            dosya_yolu = self._dosya_coz(dosya or {})
            veri = dosya_yolu.read_bytes()
            is_["dosya"] = {"ad": dosya["ad"], "yol": dosya["yol"], "kip": str(dosya.get("kip") or "0644"),
                            "ozet": hashlib.sha256(veri).hexdigest()}
        zarf = is_zarfi(anahtar_turet(gizli)[1], is_)
        with self.kosul:
            self.isler[kimlik] = {"ajan": a["kimlik"], "sunucu": a["sunucu"], "zarf": zarf, "durum": "bekliyor",
                                  "olusturma": time.time(), "sonuc": None, "dosya_yolu": dosya_yolu, "tur": tur}
            self.kuyruk[a["kimlik"]].append(kimlik)
            self._eskileri_temizle()
            self.kosul.notify_all()
        return {"kimlik": kimlik, "ajan": a["kimlik"]}

    def _dosya_coz(self, dosya):
        ad = str(dosya.get("ad") or "")
        if not ad or "/" in ad or "\\" in ad or ad.startswith(".") or not str(dosya.get("yol", "")).startswith("/"):
            raise KapiHatasi(400, "dosya adı ya da hedef yol geçersiz")
        for kok in DOSYA_KOKLERI:
            p = kok / ad
            if p.is_file():
                return p
        raise KapiHatasi(404, f"izinli dizinlerde böyle bir dosya yok: {ad}")

    def _eskileri_temizle(self):
        sinir = time.time() - 3600
        for k in [k for k, j in self.isler.items() if j["olusturma"] < sinir]:
            del self.isler[k]

    def sonuc_bekle(self, kimlik, bekle=2.0):
        son = time.time() + max(0.0, min(float(bekle), 10.0))
        with self.kosul:
            while True:
                j = self.isler.get(kimlik)
                if not j:
                    raise KapiHatasi(404, "böyle bir iş yok")
                if j["durum"] == "bekliyor" and time.time() - j["olusturma"] > self.alim_suresi:
                    j["durum"] = "alinmadi"
                    self.kuyruk[j["ajan"]] = collections.deque(x for x in self.kuyruk[j["ajan"]] if x != kimlik)
                if j["durum"] == "alindi" and not self.canli_mi(j["ajan"]):
                    j["durum"] = "kayip"          # ajan işi aldı, sonra sustu (öldü ya da bağlantı koptu)
                if j["durum"] in ("bitti", "alinmadi", "iptal", "kayip") or time.time() >= son:
                    return {"durum": j["durum"], "sonuc": j.get("sonuc"), "alindi": j["durum"] in ("alindi", "bitti")}
                self.kosul.wait(min(0.5, max(0.01, son - time.time())))

    def iptal(self, kimlik):
        with self.kosul:
            j = self.isler.get(kimlik)
            if not j:
                return False
            if j["durum"] == "bekliyor":
                j["durum"] = "iptal"
            elif j["durum"] == "alindi":
                self.iptal_bekleyen[j["ajan"]].add(kimlik)
            self.kosul.notify_all()
        return True

    # ------------------------------------------------------------ sunucu
    def baslat(self):
        self.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", self.port), _isleyici(self))
        self.httpd.daemon_threads = True
        self.port = self.httpd.server_address[1]
        threading.Thread(target=self.httpd.serve_forever, daemon=True, name="ajan-kapisi").start()
        return self

    def durdur(self):
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()


def _isleyici(kapi):
    class H(http.server.BaseHTTPRequestHandler):
        server_version = "filo-ajan-kapisi"
        protocol_version = "HTTP/1.1"

        def log_message(self, fmt, *args):
            pass

        def _gonder(self, kod, veri, nonce=None, is_a=None, tur="application/json; charset=utf-8"):
            ham = veri if isinstance(veri, bytes) else json.dumps(veri, ensure_ascii=False).encode("utf-8")
            self.send_response(kod)
            self.send_header("Content-Type", tur)
            self.send_header("Content-Length", str(len(ham)))
            self.send_header("Cache-Control", "no-store")
            if nonce and is_a:
                self.send_header("X-Filo-Imza", yanit_imzasi(is_a, nonce, ham))
            self.end_headers()
            self.wfile.write(ham)

        def _kapali_mi(self):
            try:
                r, _, _ = select.select([self.connection], [], [], 0)
                return bool(r) and self.connection.recv(1, socket.MSG_PEEK) == b""
            except (OSError, ValueError):
                return True

        def _govde(self):
            n = int(self.headers.get("Content-Length") or 0)
            if n > 8 * 1024 * 1024:
                raise KapiHatasi(413, "istek çok büyük")
            return self.rfile.read(n) if n else b""

        def _yonlendir(self, yontem):
            u = urllib.parse.urlparse(self.path)
            sorgu = {k: v[0] for k, v in urllib.parse.parse_qs(u.query).items()}
            try:
                ham = self._govde()
                if u.path.startswith("/ajan/v1/"):
                    return self._ajan(yontem, u.path, sorgu, ham)
                if u.path.startswith("/yerel/v1/"):
                    if not hmac.compare_digest(self.headers.get("X-Filo-Yerel", ""), kapi.yerel_anahtar):
                        raise KapiHatasi(403, "yerel anahtar gerekli")
                    return self._yerel(yontem, u.path, sorgu, ham)
                raise KapiHatasi(404, "yok")
            except KapiHatasi as e:
                return self._gonder(e.kod, {"hata": str(e)})
            except (ValueError, KeyError, TypeError) as e:
                return self._gonder(400, {"hata": f"geçersiz istek: {e}"})

        def do_GET(self):
            return self._yonlendir("GET")

        def do_POST(self):
            return self._yonlendir("POST")

        def _ajan(self, yontem, yol, sorgu, ham):
            if yol == "/ajan/v1/kayit" and yontem == "POST":
                return self._gonder(200, kapi.kayit(json.loads(ham or b"{}"), self.client_address[0]))
            # Ajan imzayı sorgusuz URL yoluna atar (Go tarafında req.URL.Path).
            a, nonce, is_a = kapi.dogrula(yontem, yol, self.headers, ham)
            govde = json.loads(ham) if ham else {}
            if yol == "/ajan/v1/kalp":
                return self._gonder(200, kapi.kalp(a, govde), nonce, is_a)
            if yol == "/ajan/v1/yokla":
                cevap = kapi.yokla(a, govde, self._kapali_mi)
                if cevap is None:
                    self.close_connection = True
                    return None
                try:
                    return self._gonder(200, cevap, nonce, is_a)
                except OSError:
                    kapi.geri_koy(cevap["isler"])
                    raise
            if yol == "/ajan/v1/sonuc":
                return self._gonder(200, kapi.sonuc(a, govde), nonce, is_a)
            if yol == "/ajan/v1/dosya" and yontem == "GET":
                return self._gonder(200, kapi.dosya(a, sorgu), nonce, is_a, "application/octet-stream")
            raise KapiHatasi(404, "yok")

        def _yerel(self, yontem, yol, sorgu, ham):
            g = json.loads(ham) if ham else {}
            if yol == "/yerel/v1/is":
                return self._gonder(200, kapi.is_gonder(g["sunucu"], g.get("tur", "calistir"), g.get("betik", ""),
                                                        g.get("zaman_asimi"), g.get("cikti_siniri", 65536),
                                                        g.get("kullanici"), g.get("dosya")))
            if yol == "/yerel/v1/sonuc":
                return self._gonder(200, kapi.sonuc_bekle(sorgu["is"], float(sorgu.get("bekle", 2))))
            if yol == "/yerel/v1/iptal":
                return self._gonder(200, {"iptal": kapi.iptal(g["is"])})
            if yol == "/yerel/v1/ajanlar":
                return self._gonder(200, {"ajanlar": kapi.durumlar(), "surum": AJAN_SURUM})
            if yol == "/yerel/v1/belirtec":
                return self._gonder(200, {"belirtec": kapi.belirtec_uret(g["sunucu"], g.get("sure_dk"))})
            if yol == "/yerel/v1/kaldir":
                return self._gonder(200, {"kaldirilan": kapi.kaldir(g["sunucu"], g.get("neden", "operatör"))})
            raise KapiHatasi(404, "yok")
    return H


def calistir(port=None, kayit_dinleyici=None):
    """`python -m filo ajan kapi`: kapıyı ön planda çalıştırır."""
    k = AjanKapisi(port, kayit_dinleyici=kayit_dinleyici).baslat()
    print(f"Filo ajan kapısı: http://127.0.0.1:{k.port}  (sunucular için: {ayar()['sunucular_icin_adres']})", flush=True)
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        pass
    finally:
        k.durdur()
