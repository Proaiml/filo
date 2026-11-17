"""Yeni sunucu teslimi: kayıt politikası → teslim profili → beceri zinciri → rapor (B3).

Yeni bir Filo ajanı kapıya kaydolduğunda (`AjanKapisi` kayıt dinleyicisi) sunucusu `ayarlar/teslim_politikalari.json`
içindeki ilk uyan kurala göre (ad kalıbı ya da grup) bir profile düşer ve profilin beceri zinciri kendiliğinden başlar.
Zincir motor üzerinden yürür (hedef dondurulur, şema denetlenir, denetim izine yazılır); işler artık ajan yolundan gider.

Onay: düzey 3+ adım, profilde `"on_onayli": true` değilse insan onayı bekler (Onaylar sekmesi / `filo onay ver`).
Ön onaylı adım denetim izine "onaylayan: teslim_politikasi:<profil>" diye yazılır.

Yarıda kalırsa: profil `"yarida_kalirsa": "kaptan"` diyorsa Kaptan, profildeki inisiyatif düzeyiyle devralır (kalan
adımları ve hatayı talep olarak alır); değilse insana devredilir. Her durumda teslim raporu e-postası gider.
"""
import datetime
import fnmatch
import html
import json
import threading
import time

from . import AYARLAR, rapor
from .denetim import DENETIM
from .erisim import DURDURMA
from .isler import IsKaydi, onay_bekle

POLITIKA = AYARLAR / "teslim_politikalari.json"


def politikalar(yol=None):
    return json.loads((yol or POLITIKA).read_text(encoding="utf-8"))


def profil_bul(sunucu, pol=None):
    """(profil adı, kural) ya da (None, None)."""
    pol = pol or politikalar()
    for kural in pol.get("kurallar", []):
        if kural.get("ad_kalibi") and not fnmatch.fnmatchcase(sunucu.ad.upper(), kural["ad_kalibi"].upper()):
            continue
        if kural.get("grup") and kural["grup"] not in sunucu.gruplar:
            continue
        if kural.get("ad_kalibi") or kural.get("grup"):
            return kural["profil"], kural
    return None, None


def politika_denetle(pol, katalog):
    """Politika dosyasının hataları (boş: geçerli). Profil adımlarının parametreleri şemadan geçmeli."""
    from .beceri import SemaHatasi, parametre_dogrula
    h = []
    for k in pol.get("kurallar", []):
        if k.get("profil") not in pol.get("profiller", {}):
            h.append(f"kural tanımsız profile işaret ediyor: {k}")
    for ad, p in pol.get("profiller", {}).items():
        for a in p.get("adimlar", []):
            if a["beceri"] not in katalog:
                h.append(f"{ad}: katalogda olmayan beceri {a['beceri']}")
                continue
            try:
                parametre_dogrula(katalog[a["beceri"]].get("girdi") or {}, a.get("parametre") or {})
            except SemaHatasi as e:
                h.append(f"{ad}/{a['beceri']}: {e}")
        if p.get("yarida_kalirsa", "insan") not in ("insan", "kaptan"):
            h.append(f"{ad}: yarida_kalirsa insan/kaptan olmalı")
    return h


class Teslim:
    """Bir sunucunun teslimi. motor: o anki envanterle kurulmuş BeceriMotoru (etkileşimli ya da bench politikası)."""

    def __init__(self, motor, sunucu_adi, profil_adi=None, pol=None, kayit=None, model_fabrikasi=None,
                 onay_bekle_sn=None, durdurma=DURDURMA, denetim=None, neden="yeni ajan kaydı"):
        self.motor, self.durdurma = motor, durdurma
        self.denetim = denetim or motor.denetim
        self.pol = pol or politikalar()
        self.sunucu = motor.envanter[sunucu_adi]
        if profil_adi is None:
            profil_adi, _ = profil_bul(self.sunucu, self.pol)
        if profil_adi is None:
            raise ValueError(f"{sunucu_adi}: hiçbir teslim kuralına uymuyor")
        self.profil_adi, self.profil = profil_adi, self.pol["profiller"][profil_adi]
        self.model_fabrikasi = model_fabrikasi
        self.onay_bekle_sn = onay_bekle_sn if onay_bekle_sn is not None else 60 * self.pol.get("onay_bekleme_dk", 30)
        talep = f"{self.sunucu.ad} için '{profil_adi}' teslim profili ({self.profil.get('baslik', '')}); neden: {neden}"
        self.kayit = kayit or IsKaydi(talep, "teslim")
        self.kayit.ek.update({"teslim": {"sunucu": self.sunucu.ad, "profil": profil_adi, "baslik": self.profil.get("baslik"),
                                         "neden": neden, "adimlar": [a["beceri"] for a in self.profil["adimlar"]]}})

    # ------------------------------------------------------------ yürütme
    def _adim(self, i, a, baglam):
        k = self.kayit
        hedef = self.motor.envanter.dondur({"ad": self.sunucu.ad})
        plan = self.motor.plan(a["beceri"], a.get("parametre") or {}, hedef if self.motor.katalog[a["beceri"]]["tur"] != "yerel"
                               else None, k.talep, "teslim", k.kimlik)
        on_onay = bool(a.get("on_onayli")) and plan["onay_gerekli"]
        if on_onay:
            self.denetim.yaz("onay_verildi", is_kimligi=plan["is_kimligi"], beceri=plan["beceri"], surum=plan["surum"],
                             onaylayan=f"teslim_politikasi:{self.profil_adi}", hedefler=hedef["sunucular"], on_onay=True)
            k.olay("onay", f"{a['beceri']}: risk {plan['risk']}, politika ön onaylı")
        adim = self.motor.yurut(plan, baglam, k.gozlemci(a["beceri"]), onay_atla=on_onay)
        if adim["durum"] == "onay_bekliyor":
            k.onay = adim.get("onay")
            k.durum_yap("onay_bekliyor", f"{a['beceri']}: risk {plan['risk']}, politika ön onaylı değil — insan onayı "
                                         f"bekleniyor (onay {k.onay['kimlik']})")
            k.kaydet()
            karar = onay_bekle(self.motor.politika.onaylar, k.onay["kimlik"], self.durdurma, self.onay_bekle_sn)
            if karar != "onaylandi":
                adim["durum"], adim["aciklama"] = "reddedildi", f"onay sonucu: {karar}"
            else:
                k.durum_yap("calisiyor", "onay verildi")
                adim = self.motor.yurut({**plan, "onay_kimligi": k.onay["kimlik"], "kuru_yapildi": True}, baglam,
                                        k.gozlemci(a["beceri"]))
        adim["teslim_adimi"] = i
        k.adim_ekle(adim)
        baglam["adimlar"].append(adim)
        return adim

    def yurut(self):
        k = self.kayit
        self.denetim.yaz("teslim_basladi", is_kimligi=k.kimlik, sunucu=self.sunucu.ad, profil=self.profil_adi)
        k.plan = {"teslim_profili": self.profil_adi, "hedef": {"sunucular": [self.sunucu.ad], "sayi": 1},
                  "adimlar": [a["beceri"] for a in self.profil["adimlar"]],
                  "on_onayli": [a["beceri"] for a in self.profil["adimlar"] if a.get("on_onayli")]}
        k.durum_yap("calisiyor", f"teslim başladı: {self.profil_adi}")
        baglam = {"adimlar": []}
        kalan = []
        durdugu = None
        for i, a in enumerate(self.profil["adimlar"], 1):
            if self.durdurma.basili():
                durdugu = (a, {"durum": "iptal", "aciklama": "durdurma düğmesi"})
                kalan = self.profil["adimlar"][i - 1:]
                break
            adim = self._adim(i, a, baglam)
            if adim["durum"] != "basarili":
                durdugu = (a, adim)
                kalan = self.profil["adimlar"][i - 1:]
                break
        devralan = None
        if durdugu and self.profil.get("yarida_kalirsa") == "kaptan" and durdugu[1]["durum"] not in ("iptal", "reddedildi"):
            devralan = self._kaptan_devralsin(durdugu, kalan)
        durum = "bitti" if not durdugu else ("bitti" if devralan and devralan.durum == "bitti" else
                                             "devredildi" if not devralan else devralan.durum)
        k.rapor = self._rapor_metni(baglam, durdugu, devralan)
        self._rapor_gonder(baglam, durdugu, devralan, durum)
        k.durum_yap(durum, f"teslim {durum}")
        self.denetim.yaz("teslim_bitti", is_kimligi=k.kimlik, sunucu=self.sunucu.ad, profil=self.profil_adi, durum=durum,
                         devralan=devralan.kimlik if devralan else None)
        k.kaydet()
        return k

    def _kaptan_devralsin(self, durdugu, kalan):
        from .kaptan import Kaptan
        k = self.kayit
        a, adim = durdugu
        if not self.model_fabrikasi:
            k.olay("devret", "Kaptan devralamadı: model bağlantısı yok")
            return None
        try:
            model = self.model_fabrikasi()
        except Exception as e:  # noqa: BLE001 - bağlantı hatası teslimi düşürmesin, insana devredilsin
            k.olay("devret", f"Kaptan devralamadı: model bağlantısı kurulamadı ({e})")
            return None
        hata = "; ".join(f"{r['sunucu']}: {(r.get('sema_hatasi') or r.get('neden') or r.get('stderr') or '').strip()[:200]}"
                         for r in adim.get("sonuclar", []) if r["durum"] != "basarili") or adim.get("aciklama", "")
        adimlar = ", ".join(f"{x['beceri']} {json.dumps(x.get('parametre') or {}, ensure_ascii=False)}" for x in kalan)
        alici = (self.profil.get("rapor") or {}).get("alici")
        talep = (f"{self.sunucu.ad} sunucusunun '{self.profil_adi}' teslimi {a['beceri']} adımında yarıda kaldı. Hata: {hata}. "
                 f"Teslimi tamamla; kalan adımlar sırasıyla: {adimlar}."
                 + (f" Sonucu {alici} adresine gönder." if alici else ""))
        duzey = int(self.profil.get("kaptan_inisiyatif", 2))
        kk = IsKaydi(talep, "kaptan", getattr(model, "spec", None), dizin=self.kayit.dizin)
        kk.ek["devralinan_teslim"] = {"teslim_isi": k.kimlik, "sunucu": self.sunucu.ad, "profil": self.profil_adi,
                                      "durdugu_adim": a["beceri"]}
        k.olay("devralma", f"Kaptan devraldı (inisiyatif {duzey}), iş {kk.kimlik}", is_=kk.kimlik)
        k.ek["devralan_is"] = kk.kimlik
        kap = Kaptan(model, self.motor, kk, durdurma=self.durdurma, onay_bekle_sn=self.onay_bekle_sn, inisiyatif=duzey,
                     ek_adaylar=[x["beceri"] for x in kalan] + ["eposta_gonder"],
                     en_cok_adim=max(6, len(kalan) + 1))
        try:
            kap.calistir(talep)
        except Exception as e:  # noqa: BLE001
            kk.hata = f"{type(e).__name__}: {e}"
            kk.durum_yap("hata", kk.hata)
            kk.kaydet()
        return kk

    # ------------------------------------------------------------ rapor
    def _rapor_metni(self, baglam, durdugu, devralan):
        satir = [f"Teslim: {self.sunucu.ad} — profil '{self.profil_adi}' ({self.profil.get('baslik', '')})",
                 rapor.ozet_metni(baglam["adimlar"])]
        if durdugu:
            satir.append(f"\nZincir {durdugu[0]['beceri']} adımında durdu ({durdugu[1]['durum']}).")
        if devralan:
            satir.append(f"Kaptan devraldı (iş {devralan.kimlik}): sonuç {devralan.durum}.\n{devralan.rapor}")
        elif durdugu:
            satir.append("İnsana devredildi: kalan adımlar yapılmadı.")
        return "\n".join(satir)

    def _rapor_gonder(self, baglam, durdugu, devralan, durum):
        r = self.profil.get("rapor") or {}
        if not r.get("alici"):
            return
        satirlar = "".join(
            f"<tr><td>{a.get('teslim_adimi', '')}</td><td>{html.escape(a['beceri'])} v{a.get('surum')}</td>"
            f"<td>{html.escape(a['durum'])}</td><td>{html.escape(str(a.get('aciklama') or ''))[:300]}</td></tr>"
            for a in baglam["adimlar"])
        ek = ""
        if devralan:
            ek = f"<h2>Kaptan devraldı</h2><p>İş {devralan.kimlik}: {html.escape(devralan.durum)}</p><pre>{html.escape(devralan.rapor or '')}</pre>"
        belge = (f"<html><body><h1>Teslim raporu: {html.escape(self.sunucu.ad)}</h1><p>Profil: {html.escape(self.profil_adi)}"
                 f" — sonuç: <b>{html.escape(durum)}</b></p><table border='1'><tr><th>#</th><th>Adım</th><th>Durum</th>"
                 f"<th>Açıklama</th></tr>{satirlar}</table>{ek}</body></html>")
        ad = f"teslim-{self.sunucu.ad}-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}.html"
        b = {"adimlar": baglam["adimlar"], "belge": {"ad": ad, "icerik": belge, "mime": "text/html"}}
        if baglam["adimlar"]:
            b["son_uzak_adim"] = next((a for a in reversed(baglam["adimlar"]) if a.get("sonuclar")), None)
        try:
            p = self.motor.plan("eposta_gonder", {"alici": r["alici"], "konu": f"Filo teslim raporu: {self.sunucu.ad} ({durum})"},
                                None, self.kayit.talep, "teslim", self.kayit.kimlik)
            e = self.motor.yurut(p, b)
            self.kayit.adim_ekle(e)
        except Exception as ex:  # noqa: BLE001 - rapor gönderilemese de teslim kaydı yazılsın
            self.kayit.olay("hata", f"teslim raporu gönderilemedi: {ex}")


# ---------------------------------------------------------------- kapı dinleyicisi
_CALISAN = set()
_KILIT = threading.Lock()


def motor_olustur(kip="etkilesimli", bench_kurali=None, denetim=None, katalog=None):
    from .beceri import Katalog
    from .envanter import Envanter
    from .motor import BeceriMotoru
    from .politika import Onaylar, Politika
    from .yurutme import Yurutucu
    d = denetim or DENETIM
    env = Envanter()
    return BeceriMotoru(katalog or Katalog(denetim=d), env, Yurutucu(env, denetim=d),
                        Politika(kip, bench_kurali=bench_kurali, onaylar=Onaylar(denetim=d), denetim=d), denetim=d)


def _model_fabrikasi():
    from .gateway import baglan
    return baglan(None)


def kapi_dinleyicisi(ofis=None, motor_fabrikasi=None, model_fabrikasi=_model_fabrikasi):
    """Ajan kapısının kayıt dinleyicisi: politikaya uyan yeni sunucunun teslimini arka planda başlatır. Aynı sunucu
    için aynı anda tek teslim; daha önce 'bitti' ile teslim edilmiş sunucu yeniden teslim edilmez."""
    def dinle(ajan):
        from .envanter import Envanter
        ad = ajan["sunucu"]
        env = Envanter()
        if ad not in env:
            DENETIM.yaz("teslim_atlandi", sunucu=ad, neden="sunucu envanterde yok")
            return
        if env[ad].oznitelikler.get("teslim") != "bekliyor":
            # Çalışan bir sunucuya sonradan ajan kurmak onu "yeniden teslim" etmez: yalnız envanterde teslim bekleyen
            # (teslim=bekliyor) diye işaretli yeni sunucular profile düşer.
            DENETIM.yaz("teslim_atlandi", sunucu=ad, neden="sunucu teslim bekleyen olarak işaretli değil")
            return
        profil, _ = profil_bul(env[ad])
        if not profil:
            DENETIM.yaz("teslim_atlandi", sunucu=ad, neden="hiçbir teslim kuralına uymuyor")
            return
        if teslim_edildi_mi(ad):
            DENETIM.yaz("teslim_atlandi", sunucu=ad, neden="daha önce teslim edildi (ajan yeniden kaydoldu)")
            return
        with _KILIT:
            if ad in _CALISAN:
                return
            _CALISAN.add(ad)
        try:
            time.sleep(1.0)                       # ajanın ilk yoklaması başlasın
            motor = (motor_fabrikasi or motor_olustur)()
            t = Teslim(motor, ad, profil, model_fabrikasi=model_fabrikasi)
            if ofis is not None:
                ofis.isler[t.kayit.kimlik] = {"kayit": t.kayit, "ajan": None, "thread": threading.current_thread()}
            t.yurut()
            teslim_kaydet(ad, profil, t.kayit)
        finally:
            with _KILIT:
                _CALISAN.discard(ad)
    return dinle


TESLIMLER = AYARLAR.parent / "results" / "teslimler.json"


def teslim_edildi_mi(ad):
    try:
        return json.loads(TESLIMLER.read_text(encoding="utf-8")).get(ad.upper(), {}).get("durum") == "bitti"
    except (OSError, ValueError):
        return False


def teslim_kaydet(ad, profil, kayit):
    try:
        v = json.loads(TESLIMLER.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        v = {}
    v[ad.upper()] = {"profil": profil, "durum": kayit.durum, "is": kayit.kimlik,
                     "zaman": datetime.datetime.now().isoformat(timespec="seconds")}
    TESLIMLER.parent.mkdir(parents=True, exist_ok=True)
    TESLIMLER.write_text(json.dumps(v, ensure_ascii=False, indent=1), encoding="utf-8")
    if kayit.durum == "bitti":               # envanterdeki işaret kalkar: sunucu artık teslim edilmiş
        from .envanter import EK_ENVANTER
        try:
            ek = json.loads(EK_ENVANTER.read_text(encoding="utf-8"))
            for s in ek.get("sunucular", []):
                if s["ad"].upper() == ad.upper():
                    s.setdefault("oznitelikler", {})["teslim"] = "tamam"
            EK_ENVANTER.write_text(json.dumps(ek, ensure_ascii=False, indent=1), encoding="utf-8")
        except (OSError, ValueError):
            pass


def teslim_kaydini_sil(ad):
    try:
        v = json.loads(TESLIMLER.read_text(encoding="utf-8"))
        v.pop(ad.upper(), None)
        TESLIMLER.write_text(json.dumps(v, ensure_ascii=False, indent=1), encoding="utf-8")
    except (OSError, ValueError):
        pass
