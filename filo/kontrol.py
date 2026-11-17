"""Çalışan işin denetimi: duraklat, sürdür, iptal, devret (akış otomasyonu'daki pause/resume/cancel/reassign'ın sade hâli).

Her işin bir `IsKontrolu` nesnesi vardır (süreç içinde `kontrol(kimlik)` ile bulunur). Ajanlar ve yürütücü belirli
noktalarda `nokta()` çağırır:
    - adım sınırında (Kalfa'nın ana adımı → dönüştürme → e-posta; Kaptan'ın her akış düğümü)
    - yelpaze yürütmede her sunucu başlamadan önce (çalışan sunucular biter, sıradakiler bekler)
Duraklatılmış ya da devredilmiş iş `nokta()` içinde bekler; sürdürülünce kaldığı yerden devam eder, iptal edilince
`IsIptal` fırlar. Durum iş kaydına (results/isler/<kimlik>.json) yazılır; konsol yeniden başlarsa iş kayıttan
"adımdan devam" ile sürdürülür (bkz. web.Ofis.surdur).

Devir: iş bir operatöre ya da role bırakılır (not ile). Kaptan insana devrettiğinde de iş "devredildi" durumunda
bekler; operatörün notu ve kararı Kaptan'a girdi olur.
"""
import datetime
import threading
import time

KONTROLLER = {}
_KILIT = threading.Lock()


class IsIptal(Exception):
    pass


def _simdi():
    return datetime.datetime.now().isoformat(timespec="seconds")


class IsKontrolu:
    def __init__(self, kimlik, kayit=None):
        self.kimlik = kimlik
        self.kayit = kayit
        self.durum = "calisiyor"          # calisiyor | duraklatildi | devredildi | iptal
        self.kosul = threading.Condition()
        self.karar = None                 # sürdürürken operatörün kararı/notu (Kaptan'a girdi)
        self.sahip = None
        self.bekleyen = 0                 # noktada bekleyen iş parçacığı sayısı

    # -------------------------------------------------------- operatör eylemleri
    def _yaz(self, olay, metin, **ek):
        k = self.kayit
        if k is not None:
            k.kontrol_kaydi(olay, metin, **ek)

    def duraklat(self, kim="operatör", not_=""):
        with self.kosul:
            if self.durum in ("iptal",):
                raise ValueError("iptal edilmiş iş duraklatılamaz")
            self.durum = "duraklatildi"
            self.kosul.notify_all()
        self._yaz("duraklat", f"{kim} duraklattı" + (f": {not_}" if not_ else ""), kim=kim, not_=not_)

    def surdur(self, kim="operatör", not_="", karar=None):
        with self.kosul:
            if self.durum == "iptal":
                raise ValueError("iptal edilmiş iş sürdürülemez")
            self.durum = "calisiyor"
            self.karar = {"kim": kim, "not": not_, "karar": karar, "zaman": _simdi()} if (not_ or karar) else None
            self.kosul.notify_all()
        self._yaz("surdur", f"{kim} sürdürdü" + (f" (karar: {karar})" if karar else "") + (f": {not_}" if not_ else ""),
                  kim=kim, not_=not_, karar=karar)

    def iptal(self, kim="operatör", not_=""):
        with self.kosul:
            self.durum = "iptal"
            self.kosul.notify_all()
        self._yaz("iptal", f"{kim} iptal etti" + (f": {not_}" if not_ else ""), kim=kim, not_=not_)

    def devret(self, kime, kim="operatör", not_=""):
        if not str(kime or "").strip():
            raise ValueError("devredilecek operatör ya da rol gerekli")
        with self.kosul:
            if self.durum == "iptal":
                raise ValueError("iptal edilmiş iş devredilemez")
            self.durum, self.sahip = "devredildi", str(kime).strip()[:80]
            self.kosul.notify_all()
        self._yaz("devret", f"{kim} işi {self.sahip} sahibine devretti" + (f": {not_}" if not_ else ""),
                  kim=kim, kime=self.sahip, not_=not_)

    # -------------------------------------------------------- iş tarafı
    def iptal_mi(self):
        return self.durum == "iptal"

    def nokta(self, yer="", durdurma=None, en_cok=None):
        """Bekleme noktası. Duraklatılmış/devredilmiş işte sürdürülene kadar bekler. İptalde IsIptal."""
        bas = time.time()
        bildirildi = False
        with self.kosul:
            while self.durum in ("duraklatildi", "devredildi"):
                if not bildirildi:
                    self.bekleyen += 1
                    bildirildi = True
                    k = self.kayit
                    if k is not None and k.durum not in ("duraklatildi", "devredildi"):
                        k.durum_yap(self.durum, f"{'duraklatıldı' if self.durum == 'duraklatildi' else 'devredildi'}"
                                                f" ({yer or 'bekleme noktası'})")
                        k.kaydet()
                if durdurma is not None and durdurma.basili():
                    self.durum = "iptal"
                    break
                if en_cok is not None and time.time() - bas > en_cok:
                    break
                self.kosul.wait(1.0)
            if bildirildi:
                self.bekleyen -= 1
            if self.durum == "iptal":
                raise IsIptal(f"iş iptal edildi ({yer})")
        if bildirildi and self.kayit is not None and self.kayit.durum in ("duraklatildi", "devredildi"):
            self.kayit.durum_yap("calisiyor", f"sürdürüldü ({yer})")
        if durdurma is not None and durdurma.basili():
            raise IsIptal("durdurma düğmesi basılı")

    def devir_bekle(self, kime, neden, durdurma=None, en_cok=None):
        """Ajan (Kaptan) işi insana bırakır ve operatörün kararını bekler. Dönüş: karar sözlüğü ya da None (süre doldu).
        İptalde IsIptal."""
        with self.kosul:
            self.durum, self.sahip, self.karar = "devredildi", kime, None
        self._yaz("devret", f"Kaptan işi insana devretti: {neden}", kim="kaptan", kime=kime, not_=neden)
        self.nokta("insana devir", durdurma, en_cok)
        if self.durum == "devredildi":          # süre doldu, karar gelmedi
            return None
        k, self.karar = self.karar, None
        return k or {"kim": "operatör", "not": "", "karar": None}


def kontrol(kimlik, kayit=None):
    with _KILIT:
        x = KONTROLLER.get(kimlik)
        if x is None:
            x = KONTROLLER[kimlik] = IsKontrolu(kimlik, kayit)
        elif kayit is not None and x.kayit is None:
            x.kayit = kayit
        return x


def varsa(kimlik):
    return KONTROLLER.get(kimlik) if kimlik else None


def birak(kimlik):
    with _KILIT:
        KONTROLLER.pop(kimlik, None)
