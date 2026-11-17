"""Konsol sunucusu ve JSON API (yalnız standart kitaplık).

    python -m filo web [--port 8790]        http://127.0.0.1:8790

Sayfalar: / (genel bakış), /kalfa, /kaptan, /onaylar, /envanter, /ajanlar, /teslim, /beceriler, /bench,
/karsilastirma, /baglantilar, /denetim. Hepsi aynı kabuğu (static/konsol.html) yükler; içerik JSON API'den gelir.

Yalnız 127.0.0.1'e bağlanır ve başka adresten gelen isteği reddeder. Giriş yoktur; dışarı açmayın. Değiştiren her
istek (POST) `X-Filo: 1` başlığı ister: başka bir sitenin sayfası tarayıcı üzerinden bu sunucuya istek atamaz
(özel başlık CORS ön denetimi gerektirir ve sunucu CORS izni vermez). Varsayılan olarak aynı süreçte ajan kapısını
(8795) da başlatır; yeni kaydolan ajanların teslim profili bu süreçte yürür.

Uzun işler arka plan iş parçacığında çalışır; sayfa yoklayarak günceller. Aynı anda tek iş yürür (makine sınırı: tek
koşu). Anahtarlar hiçbir uçtan geri dönmez.
"""
import copy
import http.server
import json
import threading
import traceback
import urllib.parse
import uuid

from . import ROOT, __version__
from .beceri import Katalog
from .denetim import DENETIM
from .envanter import Envanter, SeciciHatasi
from .erisim import DURDURMA, _WINRM
from .gateway import TURLER, YARDIM, Baglantilar, BaglantiHatasi, Model, baglan
from .isler import ISLER, IsKaydi
from .motor import BeceriMotoru, PlanHatasi
from .politika import Onaylar, Politika
from .yurutme import Yurutucu

STATIC = ROOT / "filo" / "static"
SAYFALAR = {"", "kalfa", "kaptan", "onaylar", "envanter", "ajanlar", "teslim", "beceriler", "bench", "karsilastirma",
            "baglantilar", "denetim", "zamanlama", "pencereler", "yama", "politikalar", "uyum"}
STATIK = {"konsol.css": "text/css", "konsol.js": "text/javascript", "sayfalar.js": "text/javascript",
          "kalfa.js": "text/javascript", "kaptan.js": "text/javascript", "zamanlama.js": "text/javascript",
          "uyum.js": "text/javascript"}
ESKI_AJAN_ADLARI = {"reis": "kaptan"}       # eski iş kayıtları (ad değişikliğinden önce) yeni adla görünür


class Ofis:
    """Konsolun arkasındaki tek durum: katalog, envanter, motor, işler, arka plan görevleri."""

    DEVIR_BEKLE_SN = 7 * 24 * 3600                 # Kaptan insana devrettiğinde iş bu kadar bekler (kalıcıdır)

    def __init__(self, zamanlama_yolu=None, pencereler=None, saat=None):
        from .zamanli import risk_fn
        from .zamanlayici import Pencereler, Zamanlayici
        self.kilit = threading.Lock()
        self.yurutme_kilidi = threading.Lock()        # aynı anda tek iş yürür
        self.isler = {}                                # kimlik -> {"kayit", "ajan", "thread"}
        self.gorevler = {}                             # arka plan görevleri (beceri taslağı, ajan eylemi, teslim)
        self.bench_durumu = {"calisiyor": False, "son": None, "ilerleme": []}
        self.onaylar = Onaylar()
        self.kapi = None
        self.pencereler = pencereler or Pencereler(saat=saat)
        self.yenile()
        self.zamanlayici = Zamanlayici(zamanlama_yolu, saat=self.pencereler.saat, pencereler=self.pencereler,
                                       envanter_fn=lambda: self._taze_motor().envanter,
                                       calistirici=self._zamanli_calistir, risk_fn=lambda t: risk_fn(self.motor)(t))
        self._kayitli_isleri_yukle()

    def yenile(self):
        self.envanter = Envanter()
        self.katalog = Katalog()
        self.yurutucu = Yurutucu(self.envanter)
        self.motor = BeceriMotoru(self.katalog, self.envanter, self.yurutucu, Politika("etkilesimli", onaylar=self.onaylar),
                                  pencereler=self.pencereler)

    def _kayitli_isleri_yukle(self):
        """Konsol yeniden başladığında duraklatılmış, devredilmiş, onay bekleyen ya da yarıda kalmış işler kayıttan
        yüklenir; operatör 'Sürdür' ile kaldıkları adımdan devam ettirir."""
        if not ISLER.exists():
            return
        for p in sorted(ISLER.glob("*.json"))[-400:]:
            try:
                d = json.loads(p.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if d.get("durum") not in ("duraklatildi", "devredildi", "calisiyor", "onay_bekliyor", "planlaniyor",
                                      "yarida_kaldi") or not d.get("devam"):
                continue
            k = IsKaydi.yukle(d)
            if k.durum in ("calisiyor", "planlaniyor"):
                k.durum_yap("yarida_kaldi", "konsol yeniden başladı; iş kaldığı adımdan sürdürülebilir")
                k.kaydet()
            self.isler[k.kimlik] = {"kayit": k, "ajan": None, "thread": None, "uyuyan": True}

    def _taze_motor(self):
        """Envanter değişmiş olabilir (yeni sunucu): planlamadan önce envanter yeniden okunur."""
        env = Envanter()
        if set(env.sunucular) != set(self.envanter.sunucular):
            self.envanter = env
            self.yurutucu.envanter = env
            self.motor.envanter = env
        return self.motor

    # ------------------------------------------------------------ okumalar
    def durum(self):
        from .ajan_istemci import AjanYok, yerel_istek
        calisan = [k for k, v in self.isler.items() if v["kayit"].durum in ("planlaniyor", "calisiyor", "onay_bekliyor")]
        try:
            a = yerel_istek("/yerel/v1/ajanlar", zaman_asimi=2)["ajanlar"]
            ajan = {"kapi": True, "canli": sum(x["durum"] == "canli" for x in a.values()),
                    "yok": sum(x["durum"] != "canli" for x in a.values())}
        except AjanYok:
            ajan = {"kapi": False}
        return {"surum": __version__, "durdurma": {"basili": DURDURMA.basili(), "neden": DURDURMA.neden()},
                "bekleyen_onay": len(self.onaylar.liste("bekliyor")), "calisan_is": calisan,
                "varsayilan_baglanti": Baglantilar().varsayilan(), "winrm": _WINRM.get("hazir"),
                "bench_calisiyor": self.bench_durumu["calisiyor"], "ajanlar": ajan}

    def is_listesi(self, ajan=None, limit=100):
        out = {k: v["kayit"].ozet() for k, v in self.isler.items()}
        if ISLER.exists():
            for p in sorted(ISLER.glob("*.json"), reverse=True)[:300]:
                if p.stem not in out:
                    try:
                        d = json.loads(p.read_text(encoding="utf-8"))
                        out[p.stem] = {k: d.get(k) for k in ("kimlik", "talep", "ajan", "baglanti", "durum", "olusturma")}
                        out[p.stem]["model_cagri"] = d.get("model_cagri")
                    except ValueError:
                        pass
        liste = []
        for x in out.values():
            x["ajan"] = ESKI_AJAN_ADLARI.get(x.get("ajan"), x.get("ajan"))
            if ajan and x["ajan"] not in ajan:
                continue
            liste.append(x)
        return sorted(liste, key=lambda x: x.get("olusturma") or "", reverse=True)[:limit]

    def is_getir(self, kimlik):
        if kimlik in self.isler:
            return self.isler[kimlik]["kayit"].sozluk()
        p = ISLER / f"{kimlik}.json"
        if p.parent == ISLER and p.exists() and all(c.isalnum() or c == "-" for c in kimlik):
            d = json.loads(p.read_text(encoding="utf-8"))
            d["ajan"] = ESKI_AJAN_ADLARI.get(d.get("ajan"), d.get("ajan"))
            return d
        return None

    def beceri(self, ad, tur="beceri"):
        if tur == "betik":
            return {**self.katalog.betik_meta(ad), "betik": self.katalog.betik_oku(ad),
                    "gecmis": self.katalog.gecmis("betik", ad)}
        t = self.katalog[ad]
        return {**self.katalog.ozet(ad), "tanim": {k: t.get(k) for k in ("komut", "kuru", "geri_al", "adimlar", "zaman_asimi",
                                                                            "islem", "kaynak")},
                "gecmis": self.katalog.gecmis("beceri", ad)}

    def genel(self):
        from .ajan_istemci import ajan_durumlari
        from .bench import kos
        from .teslim import TESLIMLER
        d = ajan_durumlari(onbellek_sn=2)
        sunucular = list(self.envanter.sunucular.values())
        isler = self.is_listesi(limit=12)
        try:
            teslimler = json.loads(TESLIMLER.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            teslimler = {}
        ok, n, _ = DENETIM.dogrula()
        sayac = {}
        for x in self.is_listesi(limit=300):
            sayac[x["durum"]] = sayac.get(x["durum"], 0) + 1
        return {"sunucu": len(sunucular), "linux": sum(s.os == "linux" for s in sunucular),
                "windows": sum(s.os == "windows" for s in sunucular),
                "ajan": {"canli": sum(1 for s in sunucular if (d.get(s.ad) or {}).get("durum") == "canli"),
                         "yok": sum(1 for s in sunucular if (d.get(s.ad) or {}).get("durum") == "ajan yok"),
                         "kayitsiz": sum(1 for s in sunucular if s.ad not in d)},
                "son_isler": isler, "is_sayaci": sayac, "bekleyen_onaylar": self.onaylar.liste("bekliyor")[:10],
                "teslimler": teslimler, "denetim": {"saglam": ok, "satir": n},
                "bench": kos.rapor()[-12:], "beceri_sayisi": len(self.katalog.beceriler)}

    def ajanlar(self):
        from .ajan_istemci import AjanYok, ajan_durumlari, yerel_istek
        from .ajan_yonetimi import CIKTI
        try:
            yerel_istek("/yerel/v1/ajanlar", zaman_asimi=2)
            kapi = True
        except AjanYok as e:
            kapi = str(e)
        d = ajan_durumlari(onbellek_sn=0) if kapi is True else {}
        satirlar = []
        for s in sorted(self._taze_motor().envanter.sunucular.values(), key=lambda x: x.ad):
            a = d.get(s.ad) or {}
            satirlar.append({"sunucu": s.ad, "os": s.os, "aile": s.aile, "gruplar": s.gruplar, "tasiyici_tanim": s.tasiyici,
                             "durum": a.get("durum") or ("kayitsiz" if s.tasiyici == "ssh" else "-"),
                             "ajan": a.get("ajan"), "surum": a.get("surum"), "son_kalp": a.get("son_kalp"),
                             "son_temas_sn": a.get("son_temas_sn"), "sistem": a.get("sistem") or {},
                             "fiili_yol": "ajan" if a.get("durum") == "canli" else s.tasiyici,
                             "teslim": s.oznitelikler.get("teslim")})
        derleme = {}
        try:
            derleme = json.loads((CIKTI / "surum.json").read_text(encoding="utf-8"))
            derleme["ikililer"] = [x.split() for x in (CIKTI / "SHA256SUMS").read_text(encoding="utf-8").splitlines() if x.strip()]
        except (OSError, ValueError):
            pass
        from .ajan_kapisi import ayar
        return {"kapi": kapi, "sunucular": satirlar, "derleme": derleme, "ayar": ayar()}

    def teslim_bilgisi(self):
        from .teslim import TESLIMLER, politika_denetle, politikalar, profil_bul
        pol = politikalar()
        try:
            teslimler = json.loads(TESLIMLER.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            teslimler = {}
        env = self._taze_motor().envanter
        return {"politika": pol, "hatalar": politika_denetle(pol, self.katalog), "teslimler": teslimler,
                "sunucular": [{"sunucu": s.ad, "profil": profil_bul(s, pol)[0], "teslim": s.oznitelikler.get("teslim"),
                               "gruplar": s.gruplar} for s in sorted(env.sunucular.values(), key=lambda x: x.ad)]}

    # ------------------------------------------------------------ talep ve iş
    def _ajan(self, ajan, baglanti, kayit, model=..., **ek):
        from .kalfa import Kalfa
        from .kaptan import Kaptan
        if model is ...:
            model = baglan(baglanti)
        if ajan == "kalfa":
            return Kalfa(model, self.motor, kayit, onay_bekle_sn=1800, zamanlayici=self.zamanlayici, **ek)
        a = Kaptan(model, self.motor, kayit, onay_bekle_sn=1800, zamanlayici=self.zamanlayici,
                   devir_bekle_sn=self.DEVIR_BEKLE_SN, **ek)
        if model is None:
            a.deneme_siniri = 0            # model yoksa teşhis/onarım yok: başarısız sunucu doğrudan insana kalır
        return a

    @staticmethod
    def _model_dene(baglanti):
        try:
            return baglan(baglanti)
        except (BaglantiHatasi, KeyError, ValueError):
            return None

    def _arka_plan(self, k, is_):
        def calis():
            if not self.yurutme_kilidi.acquire(blocking=False):
                k.olay("bekleme", "başka bir iş çalışıyor; sıra bekleniyor")
                self.yurutme_kilidi.acquire()
            try:
                is_()
            except Exception as e:  # noqa: BLE001 - arayüz hatayı göstersin, sunucu düşmesin
                k.hata = f"{type(e).__name__}: {e}"
                k.durum_yap("hata", k.hata)
                k.olay("iz", traceback.format_exc()[-1500:])
                k.kaydet()
            finally:
                self.yurutme_kilidi.release()
        th = threading.Thread(target=calis, daemon=True)
        th.start()
        return th

    def talep(self, metin, ajan, baglanti, inisiyatif=None):
        metin = str(metin or "").strip()
        if not metin:
            raise ValueError("talep metni boş")
        if ajan not in ("kalfa", "kaptan"):
            raise ValueError("ajan kalfa ya da kaptan olmalı")
        if DURDURMA.basili():
            raise ValueError("durdurma düğmesi basılı; önce kaldırın")
        self._taze_motor()
        baglanti = baglanti or Baglantilar().varsayilan()
        k = IsKaydi(metin[:2000], ajan, baglanti)
        nesne = self._ajan(ajan, baglanti, k)
        if ajan == "kaptan":
            from .kaptan import DUZEYLER, varsayilan_inisiyatif
            n = varsayilan_inisiyatif() if inisiyatif in (None, "") else int(inisiyatif)
            if n not in DUZEYLER:
                raise ValueError("inisiyatif düzeyi 0-3 olmalı")
            nesne.inisiyatif = n
            nesne.akis_otomatik_kaydet = False        # arayüzde "Sabit akış olarak kaydet" düğmesi
            nesne._kayit(metin)
        DENETIM.yaz("talep", is_kimligi=k.kimlik, ajan=ajan, baglanti=baglanti, metin=metin[:2000], kaynak="web",
                    inisiyatif=getattr(nesne, "inisiyatif", None))
        th = self._arka_plan(k, lambda: nesne.planla(metin))
        self.isler[k.kimlik] = {"kayit": k, "ajan": nesne, "thread": th}
        return k.ozet()

    def dogrudan(self, beceri, parametreler, hedef, bicim=None, alici=None, yurut=False, talep=None):
        """Kalfa'nın 'beceriden başla' yolu: model yok; operatör beceriyi, parametreleri ve hedefi verir (sunucu otomasyonu'daki Run
        Server Script'in karşılığı). Plan aynı motordan geçer: şema, dondurulmuş hedef, risk, onay."""
        from .kalfa import Kalfa
        if DURDURMA.basili():
            raise ValueError("durdurma düğmesi basılı; önce kaldırın")
        motor = self._taze_motor()
        t = motor.katalog[beceri]
        k = IsKaydi(talep or f"operatör: {beceri}", "kalfa", "operatör (model yok)")
        plan = motor.plan(beceri, parametreler or {}, hedef if t["tur"] != "yerel" else None, k.talep, "operatör", k.kimlik)
        if bicim and bicim not in ("csv", "xml", "json", "html"):
            raise ValueError("biçim csv/xml/json/html olmalı")
        if alici:
            from .beceri import EPOSTA
            if not EPOSTA.match(alici):
                raise ValueError("geçerli bir e-posta adresi değil")
        k.plan = {"ana": plan, "bicim": bicim or None, "alici": alici or None, "gerekce": "operatör seçti",
                  "adimlar": [beceri] + (["sonucu_donustur"] if bicim else []) + (["eposta_gonder"] if alici else [])}
        k.ek["kaynak"] = "dogrudan"
        k.durum_yap("plan_hazir", f"plan: {beceri}, {len((plan.get('hedef') or {}).get('sunucular', []))} sunucu, risk {plan['risk']}"
                                  + (", onay gerekli" if plan["onay_gerekli"] else ""))
        DENETIM.yaz("talep", is_kimligi=k.kimlik, ajan="kalfa", baglanti="operatör", metin=k.talep, kaynak="web-dogrudan")
        nesne = Kalfa(None, motor, k, onay_bekle_sn=1800, zamanlayici=self.zamanlayici)
        self.isler[k.kimlik] = {"kayit": k, "ajan": nesne, "thread": None}
        if yurut:
            return self.yurut(k.kimlik)
        return k.ozet()

    def kalfa_parametre(self, kimlik, parametreler, hedef=None):
        v = self.isler.get(kimlik)
        if not v or v["kayit"].durum != "plan_hazir" or v["kayit"].ajan != "kalfa":
            raise ValueError("yalnız yürütülmemiş bir Kalfa planının parametreleri değiştirilebilir")
        k = v["kayit"]
        eski = k.plan["ana"]
        yeni = self.motor.plan(eski["beceri"], parametreler, hedef or eski["hedef"]["secici"] if eski.get("hedef") else None,
                               k.talep, "kalfa", k.kimlik)
        k.plan["ana"] = yeni
        k.olay("operator", f"operatör parametreleri/hedefi değiştirdi: {json.dumps(yeni['parametreler'], ensure_ascii=False)[:300]}")
        DENETIM.yaz("plan_degisti", is_kimligi=kimlik, kaynak="web", parametreler=yeni["parametreler"],
                    hedef=(yeni.get("hedef") or {}).get("sunucular"))
        k.durum_yap("plan_hazir", f"plan güncellendi: risk {yeni['risk']}")
        return k.sozluk()

    def yurut(self, kimlik, kip=None, zamanlama=None, hedef_cozumu=None, kacirilan=None, yasak_politikasi=None,
              on_onay=False):
        """Planı yürütür. kip: 'simdi' (talepte zamanlama olsa da şimdi çalıştır) | 'zamanla' (verilen ya da talepten
        çözülmüş zamanlamayla zamanlanmış işe dönüştür). Önceden onay işareti zamanlanmış işe yazılır."""
        from .zamanlayici import okunakli, sonraki_zamanlar, zamanlama_dogrula
        v = self.isler.get(kimlik)
        if not v:
            raise ValueError("iş bulunamadı (sunucu yeniden başladıysa talebi yeniden verin)")
        k = v["kayit"]
        if k.durum != "plan_hazir":
            raise ValueError(f"iş yürütmeye hazır değil: {k.durum}")
        if DURDURMA.basili():
            raise ValueError("durdurma düğmesi basılı")
        if kip == "simdi":
            k.plan["simdi_calistir"] = True
        elif kip == "zamanla":
            zm = dict(k.plan.get("zamanlama") or {})
            if zamanlama:
                z = zamanlama_dogrula(zamanlama, self.pencereler)
                zm.update(zamanlama=z, okunakli=okunakli(z),
                          sonraki=[x.isoformat(timespec="minutes") for x in
                                   sonraki_zamanlar(z, self.pencereler.saat(), self.pencereler, 3)])
            if not zm.get("zamanlama"):
                raise ValueError("zamanlama gerekli")
            zm["hedef_cozumu"] = hedef_cozumu or zm.get("hedef_cozumu") or "simdi"
            zm["kacirilan"] = kacirilan or zm.get("kacirilan") or "atla"
            zm["yasak_politikasi"] = yasak_politikasi or zm.get("yasak_politikasi") or self.pencereler.varsayilan_politika()
            k.plan["zamanlama"] = zm
            k.plan.pop("simdi_calistir", None)
            if on_onay and v["ajan"] is not None:
                v["ajan"].on_onay_veren = "web:operatör"
        DENETIM.yaz("yurutme_istendi", is_kimligi=kimlik, kaynak="web", kip=kip or "varsayilan")
        k.durum_yap("calisiyor", "yürütme başladı" if not (k.plan.get("zamanlama") and not k.plan.get("simdi_calistir"))
                    else "zamanlanıyor")
        v["thread"] = self._arka_plan(k, v["ajan"].yurut)
        return k.ozet()

    # ------------------------------------------------------------ duraklat / sürdür / iptal / devret / adımdan devam
    def kontrol_eylem(self, kimlik, eylem, not_="", kime=None, karar=None, kim="web:operatör"):
        from . import kontrol
        v = self.isler.get(kimlik)
        if not v:
            raise ValueError("iş bulunamadı")
        k = v["kayit"]
        canli = v.get("thread") is not None and v["thread"].is_alive()
        if eylem == "surdur" and not canli:
            return self.surdur_uyuyan(kimlik, not_, karar)
        kt = kontrol.kontrol(kimlik, k)
        if eylem == "duraklat":
            if not canli:
                raise ValueError("yalnız çalışan iş duraklatılır")
            kt.duraklat(kim, not_)
        elif eylem == "surdur":
            kt.surdur(kim, not_, karar)
        elif eylem == "iptal":
            kt.iptal(kim, not_)
            if not canli:
                k.durum_yap("iptal", f"{kim} iptal etti")
                k.kaydet()
                v["uyuyan"] = False
        elif eylem == "devret":
            kt.devret(kime, kim, not_)
            if not canli:
                k.durum_yap("devredildi", f"{kime} sahibine devredildi")
                k.kaydet()
        else:
            raise ValueError("eylem duraklat / surdur / iptal / devret olmalı")
        return k.ozet()

    def surdur_uyuyan(self, kimlik, not_="", karar=None):
        """Konsol yeniden başlamış: kayıttan yüklenen işi kaldığı adımdan yeni bir yürütücüyle sürdürür."""
        from . import kontrol
        from .devam import surdurme_hazirla
        v = self.isler.get(kimlik)
        k = v["kayit"]
        if k.durum not in ("duraklatildi", "devredildi", "yarida_kaldi", "onay_bekliyor"):
            raise ValueError(f"bu iş sürdürülecek durumda değil: {k.durum}")
        baslangic, sunucular, onceki = surdurme_hazirla(k.sozluk())
        ajan = self._ajan(k.ajan if k.ajan in ("kalfa", "kaptan") else "kaptan", k.baglanti, k,
                          model=self._model_dene(k.baglanti))
        if k.ajan == "kaptan" and k.inisiyatif:
            ajan.inisiyatif = int(k.inisiyatif["duzey"])
            ajan.akis_otomatik_kaydet = False
        kt = kontrol.kontrol(kimlik, k)
        kt.durum = "calisiyor"
        k.kontrol_kaydi("surdur", f"web:operatör kayıttan sürdürdü (adım {baslangic})"
                        + (f": {not_}" if not_ else ""), kim="web:operatör", karar=karar, not_=not_)
        v.update(ajan=ajan, uyuyan=False)
        v["thread"] = self._arka_plan(k, lambda: ajan.yurut(baslangic, sunucular, onceki))
        return k.ozet()

    def devam_noktalari(self, kimlik):
        from .devam import devam_noktalari
        d = self.is_getir(kimlik)
        if not d:
            raise ValueError("iş bulunamadı")
        return {"kimlik": kimlik, "noktalar": devam_noktalari(d), "durum": d.get("durum")}

    def adimdan_devam(self, kimlik, adim, kapsam="basarisiz"):
        """Seçilen adımdan yeni koşu (önceki adımlar yeniden çalışmaz); yeni iş eskisine bağlıdır."""
        from .devam import devam_hazirla
        d = self.is_getir(kimlik)
        if not d:
            raise ValueError("iş bulunamadı")
        if d.get("durum") in ("calisiyor", "planlaniyor", "onay_bekliyor", "duraklatildi"):
            raise ValueError("iş hâlâ çalışıyor; önce bitmesini bekleyin ya da iptal edin")
        if DURDURMA.basili():
            raise ValueError("durdurma düğmesi basılı")
        baslangic, sunucular, onceki = devam_hazirla(d, adim, kapsam)
        self._taze_motor()
        ajan_adi = d.get("ajan") if d.get("ajan") in ("kalfa", "kaptan") else "kaptan"
        k = IsKaydi(d["talep"], ajan_adi, d.get("baglanti"))
        k.plan = copy.deepcopy(d.get("plan"))
        k.plan["simdi_calistir"] = True
        k.inisiyatif = copy.deepcopy(d.get("inisiyatif"))
        if k.inisiyatif:
            k.inisiyatif["kararlar"] = []
        k.ek = {"kaynak_is": kimlik, "devam_noktasi": {"adim": int(adim), "kapsam": kapsam, "sunucular": sunucular}}
        k.olay("devam", f"{kimlik} işinin {int(adim) + 1}. adımından devam ({'yalnız başarısızlar' if kapsam == 'basarisiz' else 'hepsi'}"
                        + (f": {', '.join(sunucular)}" if sunucular else "") + "); önceki adımlar yeniden çalışmaz")
        ajan = self._ajan(ajan_adi, d.get("baglanti"), k, model=self._model_dene(d.get("baglanti")))
        if ajan_adi == "kaptan" and k.inisiyatif:
            ajan.inisiyatif = int(k.inisiyatif["duzey"])
            ajan.akis_otomatik_kaydet = False
        DENETIM.yaz("adimdan_devam", is_kimligi=k.kimlik, kaynak_is=kimlik, adim=int(adim), kapsam=kapsam,
                    sunucular=sunucular, kaynak="web")
        k.durum_yap("calisiyor", "adımdan devam başladı")
        self.isler[k.kimlik] = {"kayit": k, "ajan": ajan, "thread": None}
        self.isler[k.kimlik]["thread"] = self._arka_plan(k, lambda: ajan.yurut(baslangic, sunucular, onceki))
        return k.ozet()

    # ------------------------------------------------------------ zamanlama ve pencereler
    def _zamanli_calistir(self, z, an, on_onay, not_, istisna=None):
        from .zamanli import tanim_yurut
        if DURDURMA.basili():
            return {"durum": "iptal", "hata": "durdurma düğmesi basılı"}
        t = z["tanim"]
        k = IsKaydi(f"[zamanlanmış {z['kimlik']}] " + (t.get("talep") or t.get("metin") or z["ad"]),
                    "kaptan" if t["tur"] == "akis" or t.get("ajan") == "kaptan" else "kalfa",
                    t.get("baglanti") or ("zamanlayıcı (model yok)" if t["tur"] == "beceri" else None))
        self.isler[k.kimlik] = {"kayit": k, "ajan": None, "thread": None}
        self.isler[k.kimlik]["thread"] = self._arka_plan(k, lambda: tanim_yurut(
            z, self._taze_motor(), baglan, on_onay, not_, istisna, kayit=k, zamanlayici=self.zamanlayici,
            onay_bekle_sn=1800))
        return {"is": k.kimlik, "durum": "basladi"}

    def zamanlama_coz(self, zamanlama=None, metin=None, hedef=None):
        """Arayüz önizlemesi: yapılandırılmış zamanlama ya da düz metin → doğrulanmış zamanlama + sonraki 3 çalışma."""
        from .zamanlayici import ZamanlamaHatasi, metinden_zamanlama, okunakli, sonraki_zamanlar, zamanlama_dogrula
        simdi = self.pencereler.saat()
        if not zamanlama and metin:
            hedefler = [s.ad for s in self._taze_motor().envanter.sec(hedef)] if hedef else None
            zamanlama, neden = metinden_zamanlama(metin, simdi, self.pencereler, self.envanter, hedefler)
            if zamanlama is None:
                raise ZamanlamaHatasi(f"metinden zamanlama çözülemedi: {neden}. Ör. 'her gün 02:00', 'her cumartesi 03:00', "
                                      "'yarın 23:30', '2026-11-20 02:00', 'bakım penceresinde'")
        z = zamanlama_dogrula(zamanlama or {}, self.pencereler)
        return {"zamanlama": z, "okunakli": okunakli(z),
                "sonraki": [x.isoformat(timespec="minutes") for x in sonraki_zamanlar(z, simdi, self.pencereler, 3)]}

    def zamanlama_yeni(self, g):
        """Konsoldan doğrudan zamanlanmış iş (model yok: beceri; ya da kayıtlı sabit akış; ya da serbest talep)."""
        from .akis_motoru import akis_yukle, dogrula
        from .beceri import EPOSTA, parametre_dogrula
        t = dict(g.get("tanim") or {})
        motor = self._taze_motor()
        dondurulmus = None
        if t.get("tur") == "beceri":
            if t.get("beceri") not in motor.katalog:
                raise ValueError("katalogda olmayan beceri")
            tb = motor.katalog[t["beceri"]]
            t["parametreler"] = parametre_dogrula(tb.get("girdi") or {}, t.get("parametreler") or {})
            if tb["tur"] != "yerel":
                dondurulmus = motor.envanter.dondur(t.get("hedef_secici"))
            if t.get("alici") and not EPOSTA.match(t["alici"]):
                raise ValueError("geçerli bir e-posta adresi değil")
            if t.get("bicim") and t["bicim"] not in ("csv", "xml", "json", "html"):
                raise ValueError("biçim csv/xml/json/html olmalı")
            if t.get("kimlik"):
                motor.kimlik_denetle(t["kimlik"], dondurulmus["sunucular"] if dondurulmus else [], tb)
        elif t.get("tur") == "akis":
            akis = akis_yukle(t.get("akis_adi") or t.get("akis"))
            h = dogrula(akis, motor.katalog)
            if h:
                raise ValueError("akış geçersiz: " + "; ".join(h[:4]))
            t["akis"] = akis
            t["hedef_secici"] = t.get("hedef_secici") or akis.get("hedef_secici")
            dondurulmus = motor.envanter.dondur(t["hedef_secici"]) if t["hedef_secici"] else None
            t.setdefault("inisiyatif", 2)
        elif t.get("tur") == "talep":
            if not str(t.get("metin", "")).strip():
                raise ValueError("talep metni boş")
            t.setdefault("ajan", "kalfa")
            t.setdefault("baglanti", Baglantilar().varsayilan())
        else:
            raise ValueError("tanım türü beceri / akis / talep olmalı")
        z = self.zamanlama_coz(g.get("zamanlama"), g.get("zamanlama_metni"), t.get("hedef_secici"))["zamanlama"]
        return self.zamanlayici.ekle(g.get("ad") or t.get("metin") or t.get("beceri") or "iş", t, z,
                                     g.get("hedef_cozumu") or "simdi", g.get("kacirilan") or "atla",
                                     g.get("yasak_politikasi"), "web:operatör",
                                     on_onay="web:operatör" if g.get("on_onay") else None, dondurulmus=dondurulmus)

    def vazgec(self, kimlik):
        v = self.isler.get(kimlik)
        if not v or v["kayit"].durum != "plan_hazir":
            raise ValueError("yalnız yürütülmemiş bir plandan vazgeçilebilir")
        v["kayit"].durum_yap("iptal", "operatör plandan vazgeçti; hiçbir şey çalışmadı")
        v["kayit"].kaydet()
        DENETIM.yaz("plan_vazgecildi", is_kimligi=kimlik, kaynak="web")
        return v["kayit"].ozet()

    # ------------------------------------------------------------ beceriye dönüştürme, sabit akış
    def beceriye_donustur(self, kimlik, ad=None, baslik=None):
        from .donustur import isten_beceri
        d = self.is_getir(kimlik)
        if not d:
            raise ValueError("iş bulunamadı")
        t = isten_beceri(self.katalog, self.envanter, d, ad=ad or None, baslik=baslik or None, degistiren="web:operatör")
        self.katalog.yukle()
        return {"beceri": t["ad"], "surum": t["surum"], "risk": t["risk"], "tur": t["tur"], "girdi": t.get("girdi"),
                "adimlar": t.get("adimlar"), "etiketler": t.get("etiketler")}

    def akis_kaydet(self, kimlik):
        from .kaptan import akis_kaydet_kayittan
        d = self.is_getir(kimlik)
        if not d:
            raise ValueError("iş bulunamadı")
        yol = akis_kaydet_kayittan(d)
        DENETIM.yaz("akis_kaydedildi", is_kimligi=kimlik, akis=yol.stem, kaynak="web")
        return {"akis": yol.stem}

    # ------------------------------------------------------------ arka plan görevleri
    def _gorev(self, tur, is_, **bilgi):
        kimlik = uuid.uuid4().hex[:10]
        g = {"kimlik": kimlik, "tur": tur, "durum": "calisiyor", "sonuc": None, **bilgi}
        self.gorevler[kimlik] = g

        def calis():
            try:
                g["sonuc"] = is_()
                g["durum"] = "bitti"
            except Exception as e:  # noqa: BLE001
                g["durum"], g["hata"] = "hata", f"{type(e).__name__}: {e}"
        threading.Thread(target=calis, daemon=True).start()
        return g

    def tariften_beceri(self, tarif, sunucu, baglanti=None):
        from .donustur import tariften_beceri
        if not str(tarif or "").strip():
            raise ValueError("tarif boş")
        if sunucu not in self.envanter:
            raise ValueError("sınama sunucusu envanterde yok")

        def is_():
            r = tariften_beceri(baglan(baglanti), self.motor, tarif, sunucu, "web:operatör")
            self.katalog.yukle()
            return {k: v for k, v in r.items() if k != "sonuc"} | {"stdout": ((r.get("sonuc") or {}).get("stdout") or "")[:2000]}
        return self._gorev("beceri_taslagi", is_, tarif=tarif[:300])

    def ajan_eylem(self, eylem, hedef):
        beceri = {"kur": "ajan_kur", "onar": "ajan_onar", "kaldir": "ajan_kaldir", "durum": "ajan_durumu"}.get(eylem)
        if not beceri:
            raise ValueError("eylem kur/onar/kaldir/durum olmalı")
        return self.dogrudan(beceri, {}, hedef, yurut=True, talep=f"operatör: ajan {eylem} ({hedef})")

    def teslim_baslat(self, sunucu):
        from .teslim import Teslim, teslim_kaydet
        motor = self._taze_motor()
        t = Teslim(motor, sunucu, model_fabrikasi=lambda: baglan(None), neden="operatör başlattı (konsol)")
        self.isler[t.kayit.kimlik] = {"kayit": t.kayit, "ajan": None, "thread": None}

        def is_():
            t.yurut()
            teslim_kaydet(sunucu, t.profil_adi, t.kayit)
        self.isler[t.kayit.kimlik]["thread"] = self._arka_plan(t.kayit, is_)
        return t.kayit.ozet()

    # ------------------------------------------------------------ karşılaştırma
    def karsilastirma(self):
        from .karsilastirma import karsilastirma
        return karsilastirma()

    # ------------------------------------------------------------ bench
    def bench_baslat(self, eylem, govde):
        from .bench import kos
        if self.bench_durumu["calisiyor"]:
            raise ValueError("bench zaten çalışıyor")
        self.bench_durumu.update(calisiyor=True, ilerleme=[], son=None, eylem=eylem)

        def ilerle(metin):
            self.bench_durumu["ilerleme"].append(metin)

        def calis():
            with self.yurutme_kilidi:
                try:
                    if eylem == "dogrula":
                        self.bench_durumu["son"] = kos.dogrula(govde.get("senaryolar"), ilerle=ilerle)
                    else:
                        self.bench_durumu["son"] = kos.kos(govde.get("senaryolar"), govde.get("kollar") or ["kalfa"],
                                                           govde.get("baglanti"), ilerle=ilerle)
                except Exception as e:  # noqa: BLE001
                    self.bench_durumu["son"] = {"hata": f"{type(e).__name__}: {e}"}
                    ilerle(traceback.format_exc()[-800:])
                finally:
                    self.bench_durumu["calisiyor"] = False
                    self.yenile()
        threading.Thread(target=calis, daemon=True).start()
        return {"basladi": True}


def make_handler(ofis):
    class Handler(http.server.BaseHTTPRequestHandler):
        server_version = f"filo/{__version__}"

        def log_message(self, fmt, *args):
            pass

        def _gonder(self, kod, govde, tur="application/json; charset=utf-8"):
            veri = govde if isinstance(govde, bytes) else json.dumps(govde, ensure_ascii=False, default=str).encode()
            self.send_response(kod)
            self.send_header("Content-Type", tur)
            self.send_header("Content-Length", str(len(veri)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("X-Frame-Options", "DENY")
            self.end_headers()
            self.wfile.write(veri)

        def _yerel_mi(self):
            return self.client_address[0] in ("127.0.0.1", "::1")

        def do_GET(self):
            if not self._yerel_mi():
                return self._gonder(403, {"hata": "yalnız yerel"})
            u = urllib.parse.urlparse(self.path)
            q = {k: v[0] for k, v in urllib.parse.parse_qs(u.query).items()}
            try:
                return self._get(u.path, q)
            except (KeyError, ValueError, SeciciHatasi, PlanHatasi) as e:
                return self._gonder(400, {"hata": str(e)})

        def _get(self, yol, q):
            if yol.strip("/") in SAYFALAR or yol == "/index.html":
                return self._gonder(200, (STATIC / "konsol.html").read_bytes(), "text/html; charset=utf-8")
            if yol.startswith("/static/"):
                ad = yol[len("/static/"):]
                if ad in STATIK:
                    return self._gonder(200, (STATIC / ad).read_bytes(), STATIK[ad] + "; charset=utf-8")
                return self._gonder(404, {"hata": "yok"})
            if yol == "/api/durum":
                return self._gonder(200, ofis.durum())
            if yol == "/api/genel":
                return self._gonder(200, ofis.genel())
            if yol == "/api/envanter":
                ofis._taze_motor()
                return self._gonder(200, {"sunucular": ofis.envanter.liste(), "gruplar": ofis.envanter.gruplar(),
                                          "oznitelikler": ofis.envanter.oznitelik_degerleri()})
            if yol == "/api/envanter/sec":
                return self._gonder(200, {"sunucular": [s.ad for s in ofis._taze_motor().envanter.sec(q.get("hedef", ""))]})
            if yol == "/api/ajanlar":
                return self._gonder(200, ofis.ajanlar())
            if yol == "/api/teslim":
                return self._gonder(200, ofis.teslim_bilgisi())
            if yol == "/api/beceriler":
                betikler = [{**ofis.katalog.betik_meta(b)} for b in sorted(p.name for p in ofis.katalog.betik_dizini.iterdir()
                                                                             if (p / "betik.sh").exists())]
                from .beceri import dosya_listesi
                return self._gonder(200, {"beceriler": ofis.katalog.liste(), "hatalar": ofis.katalog.hatalar,
                                          "betikler": betikler, "dosyalar": dosya_listesi()})
            if yol == "/api/beceri":
                return self._gonder(200, ofis.beceri(q["ad"], q.get("tur", "beceri")))
            if yol == "/api/beceri/fark":
                return self._gonder(200, {"fark": ofis.katalog.fark(q.get("tur", "beceri"), q["ad"], int(q["s1"]), int(q["s2"]))})
            if yol == "/api/isler":
                return self._gonder(200, ofis.is_listesi(q.get("ajan", "").split(",") if q.get("ajan") else None))
            if yol == "/api/is":
                d = ofis.is_getir(q.get("kimlik", ""))
                return self._gonder(200 if d else 404, d or {"hata": "iş yok"})
            if yol == "/api/onaylar":
                return self._gonder(200, ofis.onaylar.liste(None if q.get("hepsi") else "bekliyor"))
            if yol == "/api/kaptan/duzeyler":
                from .kaptan import DUZEYLER, YIKICI_NOTU, varsayilan_inisiyatif
                return self._gonder(200, {"duzeyler": DUZEYLER, "varsayilan": varsayilan_inisiyatif(), "not": YIKICI_NOTU})
            if yol == "/api/gorev":
                g = ofis.gorevler.get(q.get("kimlik", ""))
                return self._gonder(200 if g else 404, g or {"hata": "görev yok"})
            if yol == "/api/baglantilar":
                b = Baglantilar()
                return self._gonder(200, {"baglantilar": [b.ozet(x) for x in b.hepsi()], "varsayilan": b.varsayilan(),
                                          "turler": list(TURLER), "yardim": YARDIM})
            if yol == "/api/denetim":
                ok, n, bozuk = DENETIM.dogrula()
                return self._gonder(200, {"zincir": {"saglam": ok, "satir": n, "bozuk_satir": bozuk},
                                          "satirlar": DENETIM.oku(int(q.get("limit", 300)), q.get("tur") or None,
                                                                  q.get("is") or None)})
            if yol == "/api/akislar":
                from .kaptan import akis_listesi
                return self._gonder(200, akis_listesi())
            if yol == "/api/zamanlama":
                return self._gonder(200, {"isler": ofis.zamanlayici.liste(), "simdi": ofis.pencereler.saat().isoformat(
                    timespec="minutes"), "politika": ofis.pencereler.varsayilan_politika()})
            if yol == "/api/pencereler":
                return self._gonder(200, {"pencereler": ofis.pencereler.durum(ofis._taze_motor().envanter),
                                          "politika": ofis.pencereler.varsayilan_politika(),
                                          "simdi": ofis.pencereler.saat().isoformat(timespec="minutes")})
            if yol == "/api/is/devam-noktalari":
                return self._gonder(200, ofis.devam_noktalari(q.get("kimlik", "")))
            if yol == "/api/bench":
                from .bench import kos
                return self._gonder(200, {**kos.ozet(), "durum": ofis.bench_durumu})
            if yol == "/api/karsilastirma":
                return self._gonder(200, ofis.karsilastirma())
            if yol in ("/api/yama", "/api/politikalar", "/api/uyum"):
                from . import ui_veri
                return self._gonder(200, {"/api/yama": ui_veri.yama, "/api/politikalar": ui_veri.politikalar,
                                          "/api/uyum": ui_veri.uyum}[yol](ofis._taze_motor().envanter))
            if yol == "/api/uyum/karsilastir":
                from . import ui_veri
                return self._gonder(200, ui_veri.goruntu_fark(q["a"], q["b"]))
            return self._gonder(404, {"hata": "yok"})

        def do_POST(self):
            if not self._yerel_mi():
                return self._gonder(403, {"hata": "yalnız yerel"})
            n = int(self.headers.get("Content-Length") or 0)
            if n > 256_000:
                return self._gonder(413, {"hata": "istek çok büyük"})
            ham = self.rfile.read(n) if n else b""   # gövde okunmadan cevap verilirse Windows istemcisi bağlantıyı koparıyor
            if self.headers.get("X-Filo") != "1":
                return self._gonder(403, {"hata": "X-Filo başlığı gerekli"})
            try:
                govde = json.loads(ham or b"{}")
            except ValueError:
                return self._gonder(400, {"hata": "geçersiz JSON"})
            yol = urllib.parse.urlparse(self.path).path
            try:
                return self._post(yol, govde)
            except (KeyError, ValueError, SeciciHatasi, BaglantiHatasi, PlanHatasi) as e:
                return self._gonder(400, {"hata": str(e)})

        def _post(self, yol, g):
            if yol == "/api/talep":
                return self._gonder(200, ofis.talep(g.get("metin"), g.get("ajan", "kalfa"), g.get("baglanti"),
                                                    g.get("inisiyatif")))
            if yol == "/api/kalfa/dogrudan":
                return self._gonder(200, ofis.dogrudan(g["beceri"], g.get("parametreler") or {}, g.get("hedef"),
                                                       g.get("bicim"), g.get("alici")))
            if yol in ("/api/yama/politika", "/api/yazilim-politikasi", "/api/uyum/istisna", "/api/uyum/kural-seti"):
                from . import ui_veri
                return self._gonder(200, ui_veri.kaydet(yol, g, ofis._taze_motor().envanter))
            if yol == "/api/kalfa/parametre":
                return self._gonder(200, ofis.kalfa_parametre(g["kimlik"], g.get("parametreler") or {}, g.get("hedef")))
            if yol == "/api/is/yurut":
                return self._gonder(200, ofis.yurut(g["kimlik"], g.get("kip"), g.get("zamanlama"), g.get("hedef_cozumu"),
                                                    g.get("kacirilan"), g.get("yasak_politikasi"), bool(g.get("on_onay"))))
            if yol == "/api/is/kontrol":
                return self._gonder(200, ofis.kontrol_eylem(g["kimlik"], g.get("eylem"), str(g.get("not", ""))[:500],
                                                            g.get("kime"), g.get("karar")))
            if yol == "/api/is/devam":
                return self._gonder(200, ofis.adimdan_devam(g["kimlik"], int(g["adim"]), g.get("kapsam", "basarisiz")))
            if yol == "/api/zamanlama/onizle":
                return self._gonder(200, ofis.zamanlama_coz(g.get("zamanlama"), g.get("metin"), g.get("hedef")))
            if yol == "/api/zamanlama/yeni":
                return self._gonder(200, ofis.zamanlama_yeni(g))
            if yol == "/api/zamanlama/degistir":
                alan = {a: g[a] for a in ("ad", "zamanlama", "hedef_cozumu", "kacirilan", "yasak_politikasi", "etkin")
                        if a in g}
                if g.get("zamanlama_metni"):
                    alan["zamanlama"] = ofis.zamanlama_coz(None, g["zamanlama_metni"])["zamanlama"]
                return self._gonder(200, ofis.zamanlayici.degistir(g["kimlik"], "web:operatör", **alan))
            if yol == "/api/zamanlama/sil":
                ofis.zamanlayici.sil(g["kimlik"], "web:operatör")
                return self._gonder(200, {"silindi": g["kimlik"]})
            if yol == "/api/zamanlama/onayla":
                return self._gonder(200, ofis.zamanlayici.onayla(g["kimlik"], "web:operatör"))
            if yol == "/api/zamanlama/soru":
                return self._gonder(200, ofis.zamanlayici.soru_cevapla(g["kimlik"], g.get("karar"), "web:operatör"))
            if yol == "/api/zamanlama/calistir":
                return self._gonder(200, ofis.zamanlayici.simdi_calistir(g["kimlik"], "web:operatör"))
            if yol == "/api/pencere/kaydet":
                return self._gonder(200, ofis.pencereler.kaydet(g, ofis._taze_motor().envanter, "web:operatör"))
            if yol == "/api/pencere/sil":
                ofis.pencereler.sil(g["ad"], "web:operatör")
                return self._gonder(200, {"silindi": g["ad"]})
            if yol == "/api/pencere/politika":
                ofis.pencereler.politika_yaz(g.get("politika"))
                return self._gonder(200, {"politika": g.get("politika")})
            if yol == "/api/is/vazgec":
                return self._gonder(200, ofis.vazgec(g["kimlik"]))
            if yol == "/api/beceriye-donustur":
                return self._gonder(200, ofis.beceriye_donustur(g["kimlik"], g.get("ad"), g.get("baslik")))
            if yol == "/api/akis/kaydet":
                return self._gonder(200, ofis.akis_kaydet(g["kimlik"]))
            if yol == "/api/beceri/tarif":
                return self._gonder(200, ofis.tariften_beceri(g.get("tarif"), g.get("sunucu"), g.get("baglanti")))
            if yol == "/api/ajan/eylem":
                return self._gonder(200, ofis.ajan_eylem(g.get("eylem"), g.get("hedef")))
            if yol == "/api/ajan/belirtec":
                from .ajan_istemci import AjanYok, yerel_istek
                if g.get("sunucu") not in ofis._taze_motor().envanter:
                    raise ValueError("sunucu envanterde yok")
                try:
                    return self._gonder(200, yerel_istek("/yerel/v1/belirtec", {"sunucu": g["sunucu"]}))
                except AjanYok as e:
                    raise ValueError(f"ajan kapısı çalışmıyor: {e}") from None
            if yol == "/api/teslim/baslat":
                return self._gonder(200, ofis.teslim_baslat(g["sunucu"]))
            if yol == "/api/onay":
                k = ofis.onaylar.karar(g["kimlik"], g.get("karar") == "ver", "web:operatör", str(g.get("not", ""))[:300])
                return self._gonder(200 if k else 404, k or {"hata": "onay kaydı yok"})
            if yol == "/api/durdur":
                n = DURDURMA.bas("arayüz")
                DENETIM.yaz("durdurma", kaynak="web", oldurulen=n)
                return self._gonder(200, {"basili": True, "oldurulen": n})
            if yol == "/api/durdur/kaldir":
                DURDURMA.kaldir()
                DENETIM.yaz("durdurma_kaldirildi", kaynak="web")
                return self._gonder(200, {"basili": False})
            if yol == "/api/envanter/sina":
                adlar = [s.ad for s in ofis._taze_motor().envanter.sec(g.get("hedef") or "*")]
                tamam, disarida = ofis.yurutucu.erisim_sinamasi(adlar, zaman_asimi=10)
                return self._gonder(200, {"erisilen": tamam, "erisilemeyen": [{"sunucu": r["sunucu"], "neden": r.get("neden"),
                                                                               "oykunme": r.get("oykunme")} for r in disarida],
                                          "oykunme": [a for a in tamam if ofis.envanter[a].tasiyici == "winrm" and not _WINRM.get("hazir")]})
            if yol == "/api/baglanti/kaydet":
                b = Baglantilar()
                anahtar = g.pop("anahtar", None)
                return self._gonder(200, b.kaydet(g, anahtar=anahtar or None))
            if yol == "/api/baglanti/sil":
                Baglantilar().sil(g["ad"])
                return self._gonder(200, {"silindi": g["ad"]})
            if yol == "/api/baglanti/varsayilan":
                b = Baglantilar()
                b.getir(g["ad"])
                veri = json.loads(b.yol.read_text(encoding="utf-8"))
                veri["varsayilan"] = g["ad"]
                b.yol.write_text(json.dumps(veri, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                return self._gonder(200, {"varsayilan": g["ad"]})
            if yol in ("/api/baglanti/sina", "/api/baglanti/modeller"):
                b = Baglantilar()
                p = b.getir(g["ad"])
                m = Model(p, b.anahtar(p))
                if yol.endswith("modeller"):
                    return self._gonder(200, {"modeller": m.modeller()})
                return self._gonder(200, m.sina(sohbetle=bool(g.get("sohbet"))))
            if yol == "/api/beceri/geri-don":
                r = ofis.katalog.geri_don(g.get("tur", "beceri"), g["ad"], int(g["surum"]), "web:operatör")
                return self._gonder(200, {k: v for k, v in r.items()})
            if yol == "/api/winrm":
                from .erisim import winrm_kontrol
                return self._gonder(200, winrm_kontrol())
            if yol in ("/api/bench/dogrula", "/api/bench/kos"):
                return self._gonder(200, ofis.bench_baslat(yol.rsplit("/", 1)[1], g))
            return self._gonder(404, {"hata": "yok"})

    return Handler


def serve(host="127.0.0.1", port=8790, ofis=None, ajan_kapisi=True):
    if host not in ("127.0.0.1", "localhost", "::1"):
        raise SystemExit("Filo arayüzü yalnız 127.0.0.1'e bağlanır")
    ofis = ofis or Ofis()
    ofis.zamanlayici.baslat(aralik=20)
    print("Zamanlayıcı çalışıyor (20 sn'de bir; durum: results/zamanlama/isler.json)", flush=True)
    if ajan_kapisi:
        from .ajan_kapisi import AjanKapisi
        from .teslim import kapi_dinleyicisi
        try:
            ofis.kapi = AjanKapisi(kayit_dinleyici=kapi_dinleyicisi(ofis)).baslat()
            print(f"Ajan kapısı: http://127.0.0.1:{ofis.kapi.port}", flush=True)
        except OSError as e:
            print(f"Ajan kapısı bu süreçte başlatılmadı ({e}); ayrı çalışan bir kapı varsa o kullanılır.", flush=True)
    httpd = http.server.ThreadingHTTPServer((host, port), make_handler(ofis))
    httpd.daemon_threads = True
    print(f"Filo konsolu: http://{host}:{port}   (durdurmak için Ctrl+C)", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
    return httpd
