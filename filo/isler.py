"""İş kaydı: bir talebin baştan sona izi (plan, dondurulmuş hedef, adımlar, canlı sunucu ızgarası, zaman çizgisi,
ajanın gerekçe izi, Kaptan'ın beceri değişiklikleri, rapor). Arayüz bu kaydı yoklayarak gösterir; iş bitince
`results/isler/<kimlik>.json` dosyasına yazılır.
"""
import datetime
import json
import threading
import time
import uuid

from . import SONUC

ISLER = SONUC / "isler"
SON_DURUMLAR = ("bitti", "kismi", "basarisiz", "iptal", "devredildi", "beceri_yok", "reddedildi", "hata", "oneri",
                "zamanlandi", "ertelendi")


def _simdi():
    return datetime.datetime.now().isoformat(timespec="seconds")


class IsKaydi:
    def __init__(self, talep, ajan, baglanti=None, kimlik=None, dizin=None):
        self.kimlik = kimlik or (datetime.datetime.now().strftime("%m%d-%H%M%S-") + uuid.uuid4().hex[:4])
        self.talep, self.ajan, self.baglanti = talep, ajan, baglanti
        self.durum = "planlaniyor"
        self.olusturma = _simdi()
        self.plan = None
        self.adimlar, self.olaylar, self.gerekce, self.degisiklikler = [], [], [], []
        self.izgara = {}
        self.rapor, self.yorum, self.hata = "", "", ""
        self.onay = None
        self.model_cagri = 0
        self.inisiyatif = None          # Kaptan: {"duzey", "ad", "izin", "kararlar": [...]}
        self.ek = {}                    # ajana özgü ek bilgi (teslim profili, devralma, beceriye dönüştürme)
        self.sahip = None               # devredilen operatör/rol
        self.kontrol_gecmisi = []       # duraklat / sürdür / iptal / devret kayıtları (iş geçmişi)
        self.devam = None               # kaldığı yerden sürdürme durumu (adım girişleri, bağlam, devredilenler)
        self.dizin = dizin or ISLER
        self._kilit = threading.Lock()

    @classmethod
    def yukle(cls, d, dizin=None):
        """Kayıttan iş nesnesi (konsol yeniden başlayınca duraklatılmış/devredilmiş işi sürdürmek için)."""
        k = cls(d["talep"], d["ajan"], d.get("baglanti"), kimlik=d["kimlik"], dizin=dizin)
        for a in ("durum", "olusturma", "plan", "adimlar", "olaylar", "gerekce", "degisiklikler", "izgara", "rapor", "yorum",
                  "hata", "onay", "model_cagri", "inisiyatif", "ek", "sahip", "kontrol_gecmisi", "devam"):
            if a in d and d[a] is not None:
                setattr(k, a, d[a])
        return k

    def kontrol_kaydi(self, olay, metin, **ek):
        with self._kilit:
            self.kontrol_gecmisi.append({"zaman": _simdi(), "olay": olay, "metin": metin, **ek})
            if olay == "devret":
                self.sahip = ek.get("kime")
        self.olay("kontrol", metin, eylem=olay)
        try:
            from .denetim import DENETIM
            DENETIM.yaz("is_kontrolu", is_kimligi=self.kimlik, eylem=olay, metin=metin[:300],
                        **{k: v for k, v in ek.items() if k in ("kim", "kime", "karar")})
        except OSError:
            pass
        self.kaydet()

    def olay(self, tur, metin, **ek):
        with self._kilit:
            self.olaylar.append({"zaman": _simdi(), "tur": tur, "metin": metin, **ek})

    def durum_yap(self, durum, metin=None):
        self.durum = durum
        self.olay("durum", metin or durum, durum=durum)

    def gozlemci(self, adim_adi):
        """Yürütücünün olaylarını canlı ızgaraya işler."""
        def f(e):
            with self._kilit:
                if e.get("olay") == "basladi":
                    self.izgara[e["sunucu"]] = {"durum": "calisiyor", "adim": adim_adi, "deneme": e.get("deneme")}
                elif e.get("olay") == "sunucu":
                    r = e["sonuc"]
                    self.izgara[r["sunucu"]] = {"durum": r["durum"], "adim": adim_adi, "deneme": r.get("deneme"),
                                                "oykunme": r.get("oykunme"), "neden": (r.get("neden") or "")[:160]}
        return f

    def adim_ekle(self, adim):
        ozet = {k: adim.get(k) for k in ("beceri", "surum", "durum", "ozet", "aciklama", "baslangic", "bitis", "onay",
                                         "parametreler", "hedef", "risk", "kimlik_calistirma", "yasak", "dugum",
                                         "inisiyatif")}
        ozet["sonuclar"] = [{k: r.get(k) for k in ("sunucu", "durum", "cikis_kodu", "sure", "deneme", "kesildi",
                                                   "oykunme", "neden", "sema_hatasi", "veri", "yetki_yok", "yasak",
                                                   "tasiyici")}
                            | {"stdout": (r.get("stdout") or "")[:1500], "stderr": (r.get("stderr") or "")[:600]}
                            for r in adim.get("sonuclar", [])]
        if adim.get("belge"):
            ozet["belge"] = {k: adim["belge"][k] for k in ("ad", "bicim", "mime")} | {"onizleme": adim["belge"]["icerik"][:3000]}
        if adim.get("kuru"):
            ozet["kuru"] = [{"sunucu": r["sunucu"], "durum": r["durum"], "stdout": (r.get("stdout") or "")[:800]}
                            for r in adim["kuru"]]
        with self._kilit:
            self.adimlar.append(ozet)
        self.olay("adim", f"{adim['beceri']} v{adim.get('surum')}: {adim.get('durum')}", beceri=adim["beceri"])

    def sozluk(self):
        with self._kilit:
            return {"kimlik": self.kimlik, "talep": self.talep, "ajan": self.ajan, "baglanti": self.baglanti,
                    "durum": self.durum, "olusturma": self.olusturma, "plan": self.plan, "adimlar": list(self.adimlar),
                    "olaylar": list(self.olaylar), "gerekce": list(self.gerekce), "degisiklikler": list(self.degisiklikler),
                    "izgara": dict(self.izgara), "rapor": self.rapor, "yorum": self.yorum, "hata": self.hata,
                    "onay": self.onay, "model_cagri": self.model_cagri, "inisiyatif": self.inisiyatif,
                    "ek": dict(self.ek), "sahip": self.sahip, "kontrol_gecmisi": list(self.kontrol_gecmisi),
                    "devam": self.devam}

    def ozet(self):
        return {k: getattr(self, k) for k in ("kimlik", "talep", "ajan", "baglanti", "durum", "olusturma", "sahip")}

    def kaydet(self):
        self.dizin.mkdir(parents=True, exist_ok=True)
        yol = self.dizin / f"{self.kimlik}.json"
        metin = json.dumps(self.sozluk(), ensure_ascii=False, indent=1, default=str)
        gecici = yol.with_suffix(f".{threading.get_ident()}.tmp")
        gecici.write_text(metin, encoding="utf-8")
        for _ in range(5):              # Windows: okuyan biri varken replace kısa süre reddedilebilir
            try:
                gecici.replace(yol)
                return
            except PermissionError:
                time.sleep(0.05)
        gecici.unlink(missing_ok=True)
        yol.write_text(metin, encoding="utf-8")


def onay_bekle(onaylar, kimlik, durdurma, en_cok=1800, aralik=1.0):
    """Onay kaydı karara bağlanana kadar bekler: 'onaylandi' | 'reddedildi' | 'iptal' | 'zaman_asimi'."""
    bas = time.time()
    while time.time() - bas < en_cok:
        if durdurma.basili():
            return "iptal"
        k = onaylar.getir(kimlik)
        if k and k["durum"] != "bekliyor":
            return k["durum"]
        time.sleep(aralik)
    return "zaman_asimi"
