"""Yelpaze yürütücü: aynı işi dondurulmuş bir sunucu listesinde paralel yürütür.

Kurallar (docs/00-devir-notu.md, zorunlu korumalar 2, 3, 4, 11, 12):
  - zaman aşımı zorunlu parametredir; zaman aşımı ayrı durumdur
  - sunucu başına sonuç tek şemadadır (SONUC_ALANLARI); durum yalnız DURUMLAR içinden
  - kısmi başarısızlık sessiz geçilmez; yalnız başarısızlar yeniden denenir, deneme sayısı sınırlı (varsayılan 2)
  - çıktı boyutu sınırlıdır, kesilen çıktı `kesildi: true` taşır
  - durdurma düğmesi basılınca başlamamış sunucular `iptal` olur, çalışan süreçler öldürülür
  - yürütmeden önce erişim sınaması: erişilemeyen sunucu hedef kümeden ayrılır ve ayrıca raporlanır
"""
import concurrent.futures
import time
import uuid

from . import kontrol
from .denetim import DENETIM
from .erisim import DURDURMA, Erisilemedi, Iptal, ZamanAsimi, tasiyici_sec
from .kimlik import yetki_nedeni, yetki_yok_mu

DURUMLAR = ("basarili", "hatali", "zaman_asimi", "erisilemedi", "iptal")
SONUC_ALANLARI = ("sunucu", "durum", "cikis_kodu", "stdout", "stderr", "sure", "kesildi", "deneme", "oykunme",
                  "tasiyici", "neden")
YENIDEN_DENENIR = ("hatali", "zaman_asimi", "erisilemedi")
ERISIM_BETIGI = "echo filo-erisim-ok"


def _kes(metin, sinir):
    b = metin.encode("utf-8")
    if len(b) <= sinir:
        return metin, False
    return b[:sinir].decode("utf-8", "ignore"), True


def bos_sonuc(ad, durum, neden=""):
    return {"sunucu": ad, "durum": durum, "cikis_kodu": None, "stdout": "", "stderr": "", "sure": 0.0,
            "kesildi": False, "deneme": 0, "oykunme": False, "tasiyici": None, "neden": neden}


def ozetle(sonuclar):
    sayi = {d: 0 for d in DURUMLAR}
    for r in sonuclar:
        sayi[r["durum"]] += 1
    sayi["toplam"] = len(sonuclar)
    sayi["oykunme"] = sum(1 for r in sonuclar if r.get("oykunme"))
    sayi["kismi"] = 0 < sayi["basarili"] < len(sonuclar)
    return sayi


class Yurutucu:
    def __init__(self, envanter, eszamanli=8, cikti_siniri=65536, denetim=DENETIM, durdurma=DURDURMA,
                 tasiyici_fn=None):
        self.envanter, self.eszamanli, self.cikti_siniri = envanter, eszamanli, cikti_siniri
        self.denetim, self.durdurma = denetim, durdurma
        self.tasiyici_fn = tasiyici_fn or (lambda s: tasiyici_sec(s, self.durdurma))

    # ------------------------------------------------------------ tek sunucu
    def _bir(self, ad, betik_fn, zaman_asimi, is_kimligi=None):
        s = self.envanter[ad]
        kt = kontrol.varsa(is_kimligi)
        if kt is not None:
            # Duraklatılmış işte sıradaki sunucu başlamaz, sürdürülene kadar bekler (çalışanlar biter); iptalde başlamaz.
            try:
                kt.nokta(f"{ad} başlamadan", self.durdurma)
            except kontrol.IsIptal as e:
                return bos_sonuc(ad, "iptal", str(e))
        r = bos_sonuc(ad, "hatali")
        bas = time.monotonic()
        try:
            t = self.tasiyici_fn(s)
            r["tasiyici"], r["oykunme"] = t.ad, t.ad == "oykunucu"
            betik = betik_fn(s)
            if betik is None:
                r.update(durum="hatali", neden="bu işletim sistemi/dağıtım için komut tanımlı değil", tekrar_yok=True)
                return r
            try:
                rc, out, err = t.calistir(s, betik, zaman_asimi)
            finally:
                r["tasiyici"] = t.ad          # yedekli taşıyıcıda gerçekten kullanılan yol (ajan | ssh)
                if getattr(t, "not_", ""):
                    r["tasiyici_notu"] = t.not_
            r["stdout"], k1 = _kes(out, self.cikti_siniri)
            r["stderr"], k2 = _kes(err, self.cikti_siniri // 4)
            r["kesildi"] = k1 or k2 or bool(getattr(t, "kesildi", False))
            r["cikis_kodu"] = rc
            r["durum"] = "basarili" if rc == 0 else "hatali"
            if rc and yetki_yok_mu(rc, err):
                # Çalıştırma kimliğine geçilemedi (sudo izin vermedi ya da parola istedi): yeniden denemek düzeltmez.
                r.update(neden=yetki_nedeni(err), yetki_yok=True, tekrar_yok=True)
        except ZamanAsimi as e:
            r.update(durum="zaman_asimi", neden=str(e))
        except Erisilemedi as e:
            r.update(durum="erisilemedi", neden=str(e))
        except Iptal as e:
            r.update(durum="iptal", neden=str(e))
        except OSError as e:
            r.update(durum="erisilemedi", neden=f"istemci çalıştırılamadı: {e}")
        finally:
            r["sure"] = round(time.monotonic() - bas, 2)
        return r

    # ------------------------------------------------------------ yelpaze
    def yelpaze(self, adlar, betik_fn, zaman_asimi, yeniden_deneme=2, gozlemci=None, is_kimligi=None,
                denetle=True):
        """Betiği (ya da sunucuya göre betik üreten işlevi) her sunucuda çalıştırır; sonuç listesi ad sırasıyla."""
        if not zaman_asimi or zaman_asimi <= 0:
            raise ValueError("zaman_asimi zorunlu ve pozitif olmalı")
        if isinstance(betik_fn, str):
            sabit = betik_fn
            betik_fn = lambda s: sabit  # noqa: E731
        is_kimligi = is_kimligi or uuid.uuid4().hex[:10]
        sonuc = {}
        bekleyen = list(adlar)
        for deneme in range(1, yeniden_deneme + 2):
            if not bekleyen:
                break
            if deneme > 1:
                time.sleep(min(2.0, 0.5 * deneme))
            with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, min(self.eszamanli, len(bekleyen)))) as ex:
                isler = {}
                for ad in bekleyen:
                    if self.durdurma.basili():
                        r = bos_sonuc(ad, "iptal", "durdurma düğmesi basılı")
                        sonuc[ad] = {**r, "deneme": deneme}
                        if gozlemci:
                            gozlemci({"olay": "sunucu", "sonuc": sonuc[ad]})
                        continue
                    if gozlemci:
                        gozlemci({"olay": "basladi", "sunucu": ad, "deneme": deneme})
                    isler[ex.submit(self._bir, ad, betik_fn, zaman_asimi, is_kimligi)] = ad
                for f in concurrent.futures.as_completed(isler):
                    r = f.result()
                    r["deneme"] = deneme
                    sonuc[isler[f]] = r
                    if gozlemci:
                        gozlemci({"olay": "sunucu", "sonuc": r})
            bekleyen = [a for a in bekleyen if sonuc[a]["durum"] in YENIDEN_DENENIR and not sonuc[a].get("tekrar_yok")
                        and not self.durdurma.basili()]
        liste = [sonuc[a] for a in adlar if a in sonuc]
        if denetle:
            self.denetim.yaz("yurutme", is_kimligi=is_kimligi, zaman_asimi=zaman_asimi, ozet=ozetle(liste),
                             sunucular={r["sunucu"]: {"durum": r["durum"], "cikis_kodu": r["cikis_kodu"],
                                                      "deneme": r["deneme"], "oykunme": r["oykunme"],
                                                      "tasiyici": r.get("tasiyici"),
                                                      **({"tasiyici_notu": r["tasiyici_notu"]} if r.get("tasiyici_notu") else {})}
                                        for r in liste})
        return liste

    def erisim_sinamasi(self, adlar, zaman_asimi=15, gozlemci=None, is_kimligi=None):
        """(erişilen adlar, erişilemeyen sonuçlar). Erişilemeyenler hedef kümeden ayrılır."""
        sonuclar = self.yelpaze(adlar, ERISIM_BETIGI, zaman_asimi, yeniden_deneme=1, is_kimligi=is_kimligi,
                                denetle=False)
        tamam = [r["sunucu"] for r in sonuclar if r["durum"] == "basarili" and "filo-erisim-ok" in r["stdout"]]
        disarida = [r if r["durum"] != "basarili" else {**r, "durum": "erisilemedi", "neden": "erişim cevabı bozuk"}
                    for r in sonuclar if r["sunucu"] not in tamam]
        for r in disarida:
            r["on_sinama"] = True
            if gozlemci:
                gozlemci({"olay": "sunucu", "sonuc": r})
        self.denetim.yaz("erisim_sinamasi", is_kimligi=is_kimligi, erisilen=tamam,
                         erisilemeyen={r["sunucu"]: r.get("neden") or r["durum"] for r in disarida})
        return tamam, disarida

    def is_yurut(self, adlar, betik_fn, zaman_asimi, yeniden_deneme=2, gozlemci=None, is_kimligi=None,
                 on_sinama=True):
        """Erişim sınaması + yelpaze. Dönüş: sunucu sırasıyla tam sonuç listesi (ayrılanlar dahil)."""
        is_kimligi = is_kimligi or uuid.uuid4().hex[:10]
        disarida = []
        hedef = list(adlar)
        if on_sinama:
            hedef, disarida = self.erisim_sinamasi(adlar, gozlemci=gozlemci, is_kimligi=is_kimligi)
        sonuclar = self.yelpaze(hedef, betik_fn, zaman_asimi, yeniden_deneme, gozlemci, is_kimligi) if hedef else []
        harita = {r["sunucu"]: r for r in sonuclar + disarida}
        return [harita[a] for a in adlar if a in harita]
