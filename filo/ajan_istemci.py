"""Ajan taşıyıcısı: işi sunucudaki `filo-ajan` üzerinden yürütür (erisim.py'deki üçüncü taşıyıcı).

Seçim kuralı (`erisim.tasiyici_sec`): envanterde SSH taşıyıcılı bir sunucunun ajan kapısında canlı bir ajanı varsa iş
ajandan gider; ajan yoksa, kapı çalışmıyorsa ya da ajan işi `alim_suresi` içinde almazsa SSH'a düşülür. Hangi yoldan
gidildiği sonucun `tasiyici` alanına ve denetim izine yazılır; SSH'a düşüş `tasiyici_notu` ile açıklanır.

Bu modül kapıya yerel API'den bağlanır (results/ajanlar/yerel.anahtar); kapı aynı süreçte de ayrı süreçte de olabilir.
"""
import json
import threading
import time
import urllib.error
import urllib.request

from . import SONUC
from .erisim import DURDURMA, Erisilemedi, Iptal, SSHTasiyici, ZamanAsimi

YEREL_ANAHTAR = SONUC / "ajanlar" / "yerel.anahtar"
_ONBELLEK = {"zaman": 0.0, "veri": None, "kilit": threading.Lock()}


class AjanYok(Exception):
    pass


def _kapi_adresi():
    from .ajan_kapisi import ayar
    return f"http://127.0.0.1:{ayar()['kapi_port']}"


def yerel_istek(yol, govde=None, zaman_asimi=15, adres=None, anahtar=None):
    """Kapının yerel API'sine istek. Kapı çalışmıyorsa AjanYok."""
    try:
        anahtar = anahtar or YEREL_ANAHTAR.read_text(encoding="utf-8").strip()
    except OSError:
        raise AjanYok("ajan kapısı hiç başlatılmamış (yerel anahtar yok)") from None
    veri = json.dumps(govde).encode() if govde is not None else None
    req = urllib.request.Request((adres or _kapi_adresi()) + yol, data=veri, method="POST" if veri is not None else "GET",
                                 headers={"X-Filo-Yerel": anahtar, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=zaman_asimi) as r:
            return json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        try:
            metin = json.loads(e.read()).get("hata", "")
        except ValueError:
            metin = ""
        raise AjanYok(f"kapı {e.code}: {metin}") from None
    except (urllib.error.URLError, OSError, ValueError) as e:
        raise AjanYok(f"ajan kapısına ulaşılamadı: {e}") from None


def ajan_durumlari(onbellek_sn=3.0, adres=None):
    """{sunucu: {"durum": "canli"|"ajan yok", ...}}; kapı kapalıysa {}."""
    with _ONBELLEK["kilit"]:
        # Kapı kapalıyken (Windows'ta kapalı yerel porta bağlanmak ~2 sn sürer) sonuç daha uzun saklanır.
        sure = onbellek_sn if (_ONBELLEK.get("ulasildi") or onbellek_sn == 0) else 15.0
        if adres is None and _ONBELLEK["veri"] is not None and time.time() - _ONBELLEK["zaman"] < sure:
            return _ONBELLEK["veri"]
    ulasildi = True
    try:
        veri = yerel_istek("/yerel/v1/ajanlar", zaman_asimi=3, adres=adres).get("ajanlar", {})
    except AjanYok:
        veri, ulasildi = {}, False
    if adres is None:
        with _ONBELLEK["kilit"]:
            _ONBELLEK.update(zaman=time.time(), veri=veri, ulasildi=ulasildi)
    return veri


def onbellegi_bosalt():
    with _ONBELLEK["kilit"]:
        _ONBELLEK["veri"] = None


_SUPHELI = {}          # sunucu -> zaman: ajanı işi almadı; kapı "ajan yok" diyene kadar bu süreçte SSH kullanılır


def canli_ajan(sunucu_adi):
    if time.time() - _SUPHELI.get(str(sunucu_adi).upper(), 0) < 40:
        return False
    d = ajan_durumlari().get(sunucu_adi) or next((v for k, v in ajan_durumlari().items()
                                                 if k.upper() == str(sunucu_adi).upper()), None)
    return bool(d and d.get("durum") == "canli")


def supheli_isaretle(sunucu_adi):
    _SUPHELI[str(sunucu_adi).upper()] = time.time()


def supheyi_kaldir(sunucu_adi):
    _SUPHELI.pop(str(sunucu_adi).upper(), None)


class AjanTasiyici:
    ad = "ajan"

    def __init__(self, durdurma=DURDURMA, adres=None, anahtar=None):
        self.durdurma, self.adres, self.anahtar = durdurma, adres, anahtar
        self.kesildi = False

    def _istek(self, yol, govde=None, zaman_asimi=15):
        return yerel_istek(yol, govde, zaman_asimi, self.adres, self.anahtar)

    def gonder_ve_bekle(self, sunucu, govde, zaman_asimi):
        if self.durdurma.basili():
            raise Iptal("durdurma düğmesi basılı")
        kimlik = self._istek("/yerel/v1/is", {"sunucu": sunucu.ad, **govde})["kimlik"]
        son = time.time() + zaman_asimi + 30
        while True:
            if self.durdurma.basili():
                self._istek("/yerel/v1/iptal", {"is": kimlik})
                raise Iptal("durdurma düğmesi basıldı")
            d = self._istek(f"/yerel/v1/sonuc?is={kimlik}&bekle=2", zaman_asimi=20)
            if d["durum"] == "alinmadi":
                raise AjanYok("ajan işi zamanında almadı")
            if d["durum"] == "kayip":
                raise Erisilemedi("ajan işi aldı ama sonra sustu (ajan durmuş olabilir)")
            if d["durum"] == "iptal":
                raise Iptal("iş iptal edildi")
            if d["durum"] == "bitti":
                return d["sonuc"]
            if time.time() > son:
                self._istek("/yerel/v1/iptal", {"is": kimlik})
                raise ZamanAsimi(f"{zaman_asimi} sn içinde ajandan sonuç gelmedi")

    def calistir(self, sunucu, betik, zaman_asimi=60, cikti_siniri=65536):
        r = self.gonder_ve_bekle(sunucu, {"tur": "calistir", "betik": betik, "zaman_asimi": zaman_asimi,
                                          "cikti_siniri": cikti_siniri}, zaman_asimi)
        self.kesildi = bool(r.get("kesildi"))
        if r["durum"] == "zaman_asimi":
            raise ZamanAsimi(f"{zaman_asimi} sn içinde bitmedi (ajan süreci kesti)")
        if r["durum"] == "iptal":
            raise Iptal("ajan işi iptal etti")
        if r["durum"] == "reddedildi":
            return 126, r.get("stdout") or "", f"ajan işi reddetti: {r.get('neden')}"
        rc = r.get("cikis_kodu")
        err = r.get("stderr") or ""
        if rc is None:
            rc, err = -1, (err + "\n" + (r.get("neden") or "")).strip()
        return rc, r.get("stdout") or "", err

    def dosya_gonder(self, sunucu, ad, uzak_yol, kip="0644", kullanici=None, zaman_asimi=60):
        r = self.gonder_ve_bekle(sunucu, {"tur": "dosya_al", "zaman_asimi": zaman_asimi, "kullanici": kullanici,
                                          "dosya": {"ad": ad, "yol": uzak_yol, "kip": kip}}, zaman_asimi)
        return r

    def sistem_bilgisi(self, sunucu):
        r = self.gonder_ve_bekle(sunucu, {"tur": "sistem_bilgisi", "zaman_asimi": 10}, 10)
        return json.loads(r["stdout"]) if r.get("durum") == "basarili" else None


class YedekliTasiyici:
    """Önce ajan; ajan işi almazsa ya da kapıya ulaşılamazsa SSH. `ad` gerçekten kullanılan yolu gösterir."""

    def __init__(self, durdurma=DURDURMA):
        self.ajan = AjanTasiyici(durdurma)
        self.ssh = SSHTasiyici(durdurma)
        self.ad = "ajan"
        self.not_ = ""
        self.kesildi = False

    def calistir(self, sunucu, betik, zaman_asimi=60):
        try:
            sonuc = self.ajan.calistir(sunucu, betik, zaman_asimi)
            self.kesildi = self.ajan.kesildi
            return sonuc
        except AjanYok as e:
            onbellegi_bosalt()
            supheli_isaretle(sunucu.ad)
            self.ad, self.not_ = "ssh", f"ajan yolu kullanılamadı ({e}); SSH'a düşüldü"
            return self.ssh.calistir(sunucu, betik, zaman_asimi)
