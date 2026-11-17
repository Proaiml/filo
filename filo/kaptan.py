"""Kaptan: dinamik akış ajanı (akış otomasyonu sınıfı).

talep → akış (katalogdan beceri adımları; kod adayları daraltır, model sıralar) → hedef → her adımın parametresi →
adım adım yürütme. Bir adım hata verir ya da çıktısı şemaya uymazsa:
    1. teşhis: model salt-okur bir beceri seçer (en çok 2), kod onu yalnız başarısız sunucularda çalıştırır
    2. karar (seçenekleri kod daraltır): yeniden_dene | onarim:<beceri> | beceriyi_degistir | devret
    3. beceriyi_degistir: model yeni komut/betik metni yazar; kod onu YENİ SÜRÜM olarak kaydeder, riski kodla yeniden
       sınıflar (yükselirse onay ister), adımı yeni sürümle yeniden planlar
    4. adım başına en çok `deneme_siniri` (varsayılan 2) onarım; sonra insana devreder
Başarısız sunucular sonraki adımlara girmez; kalan sunucularla akış sürer ve sonuç dürüstçe raporlanır.
Bütün sunucularda başarıyla biten akış `akislar/<ad>.json` olarak sabit akış diye kaydedilir; `akis_yurut` onu
modele sormadan aynı sırayla yeniden yürütür.
"""
import datetime
import json
import re
import time

from . import ROOT, rapor
from .ajan_ortak import (SISTEM, aday_beceriler, beceri_sec, bicim_ve_alici, dayanak_var, hata_yorumu, hedef_sor, kisa,
                         talep_eylemleri,
                         normal, parametre_sor, secenek_satiri)
from .akis_motoru import (BICIM, AkisDurdu, AkisYurutucu, akis_ozeti, baglam_coz, baglam_sikistir, beceri_dugumleri,
                          duz_akis, duz_mu, eski_akistan)
from .beceri import SemaHatasi, komut_sec, parametre_dogrula
from .erisim import DURDURMA
from .gateway import sor_json
from .isler import IsKaydi, onay_bekle
from .kimlik import kimlik_sor
from .kontrol import IsIptal
from .kontrol import kontrol as kontrol_al
from .motor import PlanHatasi
from .zamanlayici import ZamanlamaHatasi
from .zamanli import on_onay_al, zamanlama_plani, zamanlama_raporu

AKISLAR = ROOT / "akislar"
TESHIS = ("komut_calistir", "servis_durumu", "disk_durumu", "paket_dogrula", "erisim_sinamasi", "sistem_envanteri",
          "ajan_durumu")
ONARIM = ("servis_baslat", "servis_yeniden_baslat", "paket_onar", "paket_kur", "gecici_dosya_temizle", "dosya_dagit",
          "ajan_onar", "depo_onar")


AYAR = ROOT / "ayarlar" / "kaptan.json"

# İnisiyatif düzeyi: operatörün Kaptan'a verdiği serbestlik. Kodla uygulanır; model ne derse desin aşılamaz.
DUZEYLER = {
    0: {"ad": "Yalnız öner", "izin": "Hiçbir şey çalıştırmaz. Akışı, gerekçesini ve her adımın hangi onayı isteyeceğini "
                                     "önerir."},
    1: {"ad": "Teşhis serbest", "izin": "Salt-okur beceriler ve raporlama (risk 0-1) onaysız çalışır. Sunucuda değişiklik "
                                        "yapan her adım insan onayı ister."},
    2: {"ad": "Geri alınabilir onarım serbest", "izin": "Risk 2'ye kadar (kuru çalıştırması ve geri alması olan değişiklik) "
                                                        "onaysız. Servis/paket değişikliği ve beceri değiştirme onay ister."},
    3: {"ad": "Beceri ve servis/paket değişikliği serbest", "izin": "Risk 3'e kadar onaysız; beceriyi yeni sürümle "
                                                                    "değiştirebilir (risk kodla yeniden sınıflanır)."},
}
YIKICI_NOTU = "Tam yetki yok: yıkıcı (risk 4) işler her düzeyde insan onayı ister."


def varsayilan_inisiyatif():
    try:
        return int(json.loads(AYAR.read_text(encoding="utf-8")).get("varsayilan_inisiyatif", 2))
    except (OSError, ValueError):
        return 2


def inisiyatif_karari(duzey, risk):
    """(karar, açıklama). karar: onerildi | izinli | onay_gerekli"""
    if duzey == 0:
        return "onerildi", "düzey 0: yalnız öneri, çalıştırılmaz"
    if risk >= 4:
        return "onay_gerekli", f"risk {risk} (yıkıcı): her düzeyde insan onayı"
    if risk <= duzey:
        return "izinli", f"risk {risk} ≤ düzey {duzey}: bu düzeyde izinli"
    return "onay_gerekli", f"risk {risk} > düzey {duzey}: onay gerekti"


class Kaptan:
    ad = "kaptan"

    def __init__(self, model, motor, kayit=None, durdurma=DURDURMA, deneme_siniri=2, onay_bekle_sn=None,
                 akis_dizini=None, en_cok_adim=6, inisiyatif=None, ek_adaylar=(), on_onay=None, yasak_istisnasi=None,
                 devir_bekle_sn=None, zamanlayici=None, on_onay_veren=None, saat=time.monotonic, uyu=time.sleep,
                 yapi_kur=True):
        self.ek_adaylar = list(ek_adaylar)
        self.akis_otomatik_kaydet = True
        self.on_onay, self.yasak_istisnasi, self.on_onay_veren = on_onay, yasak_istisnasi, on_onay_veren
        self.devir_bekle_sn = devir_bekle_sn      # None: insana devirde beklemez (bench, komut satırı)
        self.zamanlayici = zamanlayici
        self.saat, self.uyu = saat, uyu           # bekleme adımı için (sınamada sahte saat)
        self.yapi_kur = yapi_kur                  # talepte yapı ipucu varsa dar sorularla yapılı akış kur (C4)
        self._hedef, self._kontrol, self._yurutucu = None, None, None
        self.model, self.motor, self.kayit, self.durdurma = model, motor, kayit, durdurma
        self.deneme_siniri, self.onay_bekle_sn, self.en_cok_adim = deneme_siniri, onay_bekle_sn, en_cok_adim
        self.akis_dizini = akis_dizini or AKISLAR
        n = varsayilan_inisiyatif() if inisiyatif is None else int(inisiyatif)
        if n not in DUZEYLER:
            raise ValueError("inisiyatif düzeyi 0-3 olmalı (4 yok: yıkıcı işler her zaman insan onayı ister)")
        self.inisiyatif = n

    # ------------------------------------------------------------ yardımcılar
    def _kayit(self, talep):
        if self.kayit is None:
            self.kayit = IsKaydi(talep, self.ad, getattr(self.model, "spec", None))
        if not self.kayit.inisiyatif:
            self.kayit.inisiyatif = {"duzey": self.inisiyatif, "ad": DUZEYLER[self.inisiyatif]["ad"],
                                     "izin": DUZEYLER[self.inisiyatif]["izin"], "not": YIKICI_NOTU, "kararlar": []}
        return self.kayit

    def _iz(self, beceri, risk, karar, aciklama, amac, sonuc=None):
        """Her yürütme kararının yanına hangi düzeyle geçtiği yazılır (arayüzün inisiyatif izi)."""
        k = self.kayit
        satir = {"zaman": datetime.datetime.now().isoformat(timespec="seconds"), "beceri": beceri, "risk": risk,
                 "duzey": self.inisiyatif, "karar": karar, "aciklama": aciklama, "amac": amac, "sonuc": sonuc}
        k.inisiyatif["kararlar"].append(satir)
        k.olay("inisiyatif", f"{beceri} (risk {risk}, {amac}): {aciklama}" + (f" → {sonuc}" if sonuc else ""),
               karar=karar)
        return satir

    def _calistir(self, plan, baglam, amac="adım", onay_bekle=True):
        """Kaptan'ın bütün yürütmeleri buradan geçer: inisiyatif düzeyi kodla uygulanır.
        izinli → motor onay kapısını atlar (onay veren: operatörün düzey ayarı, denetim izine yazılır);
        onay_gerekli → plan onay ister (bench'te senaryo, arayüzde insan karar verir)."""
        k = self.kayit
        if self.on_onay:
            plan = {**plan, "on_onay": self.on_onay}
        if self.yasak_istisnasi:
            plan = {**plan, "yasak_istisnasi": self.yasak_istisnasi}
        karar, aciklama = inisiyatif_karari(self.inisiyatif, plan["risk"])
        satir = self._iz(plan["beceri"], plan["risk"], karar, aciklama, amac)
        if karar == "onerildi":
            satir["sonuc"] = "çalıştırılmadı"
            return {"beceri": plan["beceri"], "surum": plan["surum"], "durum": "onerildi", "sonuclar": [],
                    "aciklama": aciklama, "risk": plan["risk"], "is_kimligi": plan["is_kimligi"]}
        if karar == "izinli":
            if plan["onay_gerekli"]:
                self.motor.denetim.yaz("onay_verildi", is_kimligi=plan["is_kimligi"], beceri=plan["beceri"],
                                       surum=plan["surum"], onaylayan=f"inisiyatif:{self.inisiyatif}",
                                       hedefler=(plan.get("hedef") or {}).get("sunucular", []))
            adim = self.motor.yurut(plan, baglam, k.gozlemci(plan["beceri"]), onay_atla=True)
            satir["sonuc"] = f"çalıştı ({adim['durum']})"
            adim["inisiyatif"] = "izinli"
            return adim
        plan = {**plan, "onay_gerekli": True}
        adim = self.motor.yurut(plan, baglam, k.gozlemci(plan["beceri"]))
        if adim["durum"] == "onay_bekliyor" and onay_bekle:
            k.onay = adim.get("onay")
            k.durum_yap("onay_bekliyor", f"{plan['beceri']}: risk {plan['risk']}, düzey {self.inisiyatif} — onay bekliyor "
                                         f"(onay {k.onay['kimlik']})")
            k.kaydet()
            if self.onay_bekle_sn is None:
                satir["sonuc"] = "onay bekliyor"
                return adim
            karar2 = onay_bekle(self.motor.politika.onaylar, k.onay["kimlik"], self.durdurma, self.onay_bekle_sn)
            if karar2 != "onaylandi":
                adim["durum"], adim["aciklama"] = "reddedildi", f"onay sonucu: {karar2}"
                satir["sonuc"] = "reddedildi"
                return adim
            k.durum_yap("calisiyor", "onay verildi")
            adim = self.motor.yurut({**plan, "onay_kimligi": k.onay["kimlik"], "kuru_yapildi": True}, baglam,
                                    k.gozlemci(plan["beceri"]))
        satir["sonuc"] = {"reddedildi": "reddedildi", "onay_bekliyor": "onay bekliyor"}.get(
            adim["durum"], f"onaylandı, çalıştı ({adim['durum']})")
        adim["inisiyatif"] = "onay_gerekti"
        return adim

    def _bitir(self, durum, metin=""):
        k = self.kayit
        k.model_cagri = getattr(self.model, "cagri", 0)
        if metin:
            k.rapor = (k.rapor + "\n" + metin).strip()
        k.durum_yap(durum, metin or durum)
        k.kaydet()
        return k

    def _yurut_plan(self, plan, baglam, amac="adım"):
        """Motoru inisiyatif kapısından çalıştırır; onay gerekiyorsa bekler (ya da bekleme yoksa durumu döndürür)."""
        return self._calistir(plan, baglam, amac)

    # ------------------------------------------------------------ akış kurma
    def akis_kur(self, talep):
        k = self._kayit(talep)
        katalog, iz = self.motor.katalog, k.gerekce
        adaylar = aday_beceriler(katalog, talep, k=8, turler=("uzak", "zincir", "yerel", "yonetim"))
        for x in self.ek_adaylar:          # devralmada bilinen kalan adımlar her zaman aday olur
            if x in katalog and x not in adaylar:
                adaylar.append(x)
        for yerel in ("sonucu_donustur", "eposta_gonder"):
            if yerel not in adaylar and any(w in normal(talep) for w in ("xml", "csv", "json", "html", "@", "posta", "mail")):
                adaylar.append(yerel)
        k.olay("daraltma", f"akış için aday beceriler: {', '.join(adaylar)}")
        metin = (f"Talep: \"{talep}\"\nBu talebi yürütecek akışı kur: sırayla çalışacak beceri adımları "
                 f"(en çok {self.en_cok_adim}). Yalnız şu becerileri kullan:\n"
                 + "\n".join(secenek_satiri(katalog, a) for a in adaylar)
                 + "\nKurallar: talepte istenmeyen adım ekleme. sonucu_donustur bir sunucu adımından sonra gelir; "
                   "eposta_gonder en sonda olur. Talebi hiçbir beceri karşılamıyorsa boş liste yaz.\n"
                   'JSON: {"adimlar": ["<beceri>", ...], "gerekce": "<tek cümle>"}')

        def dogrula(v):
            a = v.get("adimlar")
            if not isinstance(a, list):
                return None, "adimlar bir liste olmalı"
            a = [str(x).strip() for x in a]
            yabanci = [x for x in a if x not in adaylar]
            if yabanci:
                return None, f"listede olmayan beceri: {yabanci}; yalnız {adaylar}"
            if len(a) > self.en_cok_adim:
                return None, f"en çok {self.en_cok_adim} adım"
            uzak_goruldu = False
            for i, x in enumerate(a):
                if katalog[x]["tur"] != "yerel":
                    uzak_goruldu = True
                elif x == "sonucu_donustur" and not uzak_goruldu:
                    return None, "sonucu_donustur'dan önce bir sunucu adımı olmalı"
                elif x == "eposta_gonder" and i != len(a) - 1:
                    return None, "eposta_gonder son adım olmalı"
            for i, x in enumerate(a):        # doğrulama, doğruladığı işten önce gelmez (ilk koşu O01: önce doğrula, sonra kur)
                if x.endswith("_dogrula") and x.replace("_dogrula", "_kur") in a[i + 1:]:
                    return None, f"{x}, {x.replace('_dogrula', '_kur')} adımından SONRA gelmeli"
            dayanaksiz = [x for x in a if x not in self.ek_adaylar and not dayanak_var(katalog, x, talep)]
            if dayanaksiz:
                return None, (f"talepte dayanağı olmayan adım: {dayanaksiz}; yalnız talebin istediği işleri yap "
                              "(istenmeyen kurulum, teslim, dönüştürme ekleme)")
            return {"adimlar": a, "gerekce": str(v.get("gerekce", ""))[:300]}, None
        akis = sor_json(self.model, SISTEM, metin, dogrula, iz=iz, etiket="akış")[0]
        if akis is None:
            return None
        if akis["adimlar"] and not self.ek_adaylar and "eposta_gonder" not in akis["adimlar"] and "eposta_gonder" in katalog \
                and len(set(re.findall(r"[\w.%+-]+@[\w.-]+\.\w+", talep))) == 1 \
                and dayanak_var(katalog, "eposta_gonder", talep):
            # Talep tek bir adrese bildirim istiyor ama model e-posta adımını koymadı (tam koşu O08: iş "başarılı"
            # bitti, rapor gitmedi → sahte başarı). Kod adımı sona ekler.
            akis["adimlar"].append("eposta_gonder")
            iz.append({"soru": "akış (kod)", "denemeler": [], "sonuc": akis["adimlar"],
                       "kod_notu": "talep e-posta bildirimi istiyor; eposta_gonder adımı kodla sona eklendi"})
        if not akis["adimlar"]:
            return {"adimlar": [], "gerekce": akis["gerekce"]}
        k.olay("karar", f"akış: {' → '.join(akis['adimlar'])} ({akis['gerekce']})")
        secici = None
        if any(katalog[a]["tur"] != "yerel" for a in akis["adimlar"]):
            secici = hedef_sor(self.model, self.motor.envanter, talep, iz)
            if secici is None:
                return None
        adimlar = []
        for a in akis["adimlar"]:
            p = parametre_sor(self.model, katalog, a, talep, iz,
                              ek=f"Akış: {' → '.join(akis['adimlar'])}. Bu adım: {a}.\n",
                              sunucu_adlari=list(self.motor.envanter.sunucular))
            if p is None:
                k.rapor = f"{a} adımının parametreleri talepten doldurulamadı."
                return None
            adimlar.append({"beceri": a, "parametreler": p, "gecis": {"basari": "sonraki", "hata": "teshis"}})
        kc = kimlik_sor(self.model, talep, iz)        # "root olarak", "webops kullanıcısıyla"
        if kc:
            for a in adimlar:
                if katalog[a["beceri"]]["tur"] in ("uzak", "zincir"):
                    a["kimlik_calistirma"] = kc
        return {"adimlar": adimlar, "hedef": secici, "gerekce": akis["gerekce"], "kimlik": kc}

    def planla(self, talep):
        k = self._kayit(talep)
        akis = self.akis_kur(talep)
        if akis is None:
            return self._bitir("hata", k.rapor or "Akış kurulamadı (model geçerli cevap vermedi); iş başlatılmadı.")
        if not akis["adimlar"] and self.yapi_kur:
            akis = self._kayitli_akis_talebi(talep, akis) or akis
        if not akis["adimlar"] and not akis.get("alt_akis"):
            return self._bitir("beceri_yok", "Katalogdaki beceriler bu talebi karşılamıyor; iş başlatılmadı.")
        hedef = self.motor.envanter.dondur(akis["hedef"]) if akis.get("hedef") else None
        if akis.get("kimlik"):
            try:                      # izinli olmayan çalıştırma kimliği planda reddedilir (hiçbir şey çalışmaz)
                for a in akis["adimlar"]:
                    if a.get("kimlik_calistirma"):
                        self.motor.kimlik_denetle(a["kimlik_calistirma"], (hedef or {}).get("sunucular", []),
                                                  self.motor.katalog[a["beceri"]])
            except PlanHatasi as e:
                return self._bitir("hata", f"Plan reddedildi: {e}. Hiçbir sunucuda işlem yapılmadı.")
        akis_kaydi = akis
        if self.yapi_kur:
            from .akis_kurucu import yapi_kur
            yapili = yapi_kur(self, talep, akis, hedef)
            if yapili is not None:
                akis_kaydi = yapili
        if akis_kaydi is akis and not akis["adimlar"]:
            return self._bitir("beceri_yok", "Kayıtlı akış çağrılamadı ve katalogdaki beceriler talebi karşılamıyor; "
                                             "iş başlatılmadı.")
        k.plan = {"akis": akis_kaydi, "hedef": hedef, "risk": max([self.motor.katalog.etkin_risk(
                  self.motor.katalog[a["beceri"]], a.get("parametreler") or {})[0] for a in beceri_dugumleri(
                      akis_kaydi if akis_kaydi is not akis else duz_akis(akis["adimlar"]))] or [0]),
                  "adimlar": [a["beceri"] for a in akis["adimlar"]], "gerekce": akis["gerekce"]}
        try:
            zm = zamanlama_plani(self.model, self.motor, talep, k.gerekce, (hedef or {}).get("sunucular"))
        except ZamanlamaHatasi as e:
            return self._bitir("hata", f"Talepteki zamanlama çözülemedi: {e}. İş başlatılmadı.")
        if zm:
            k.plan["zamanlama"] = zm
        k.model_cagri = getattr(self.model, "cagri", 0)
        k.durum_yap("plan_hazir", f"akış: {' → '.join(k.plan['adimlar'])}"
                                  + (" (yapılı)" if akis_kaydi is not akis else "")
                                  + (f", {hedef['sayi']} sunucu" if hedef else "") + f", en yüksek risk {k.plan['risk']}"
                                  + (f", zamanlama: {zm['okunakli']}" if zm else ""))
        k.kaydet()
        return k

    # ------------------------------------------------------------ yürütme
    def _kayitli_akis_talebi(self, talep, akis):
        """Talep kayıtlı bir sabit akışı adıyla istiyor ama model katalogdan adım kuramadıysa: hedef ve bildirim kodla
        sorulur, akış yapı kurucusunda alt akış düğümü olarak eklenir."""
        from .akis_kurucu import yapi_ipuclari
        try:
            adlar = [a["ad"] for a in akis_listesi(self.akis_dizini)]
        except OSError:
            return None
        _, alt = yapi_ipuclari(talep, adlar)
        if not alt:
            return None
        k = self.kayit
        secici = hedef_sor(self.model, self.motor.envanter, talep, k.gerekce)
        if secici is None:
            return None
        _, alici = bicim_ve_alici(self.model, talep, k.gerekce)
        adimlar = ([{"beceri": "eposta_gonder", "parametreler": {"alici": alici, "konu": f"Filo: {alt[0]} akışı"}}]
                   if alici else [])
        k.olay("karar", f"talep kayıtlı akışı istiyor: {alt[0]}")
        return {"adimlar": adimlar, "hedef": secici, "gerekce": f"kayıtlı akış {alt[0]} çağrılıyor", "alt_akis": alt[0]}

    def akis_v2(self):
        """Planın akışı sürüm 2 biçiminde (Kaptan'ın düz akışı da yapılı akış da aynı motordan yürür)."""
        akis = self.kayit.plan["akis"]
        if isinstance(akis, dict) and akis.get("bicim") == BICIM:
            return akis
        return duz_akis(akis.get("adimlar", []), talep=self.kayit.talep,
                        hedef_secici=(self.kayit.plan.get("hedef") or {}).get("secici"))

    def yurut(self, baslangic=0, sunucular=None, onceki=None):
        """Akışı yürütür. `baslangic`/`sunucular`/`onceki`: adımdan devam (önceki koşunun kayıtlı durumu)."""
        k = self.kayit
        if not k or not k.plan:
            raise PlanHatasi("önce planla")
        self._kayit(k.talep)                     # inisiyatif kaydı (devam koşusunda yeni iş nesnesi olabilir)
        if self.durdurma.basili():
            return self._bitir("iptal", "Durdurma düğmesi basılı; iş başlatılmadı.")
        if k.plan.get("zamanlama") and not k.plan.get("simdi_calistir") and not onceki:
            return self._zamanla()
        if self.inisiyatif == 0:
            return self._oneri()
        k.durum_yap("calisiyor")
        akis, hedef = self.akis_v2(), k.plan.get("hedef")
        self._hedef = hedef
        baglam = baglam_coz((onceki or {}).get("baglam")) or {"adimlar": []}
        yapilan = list((onceki or {}).get("yapilan") or [])
        kt = kontrol_al(k.kimlik, k)
        self._kontrol = kt

        uzunluk = dict((onceki or {}).get("baglam_uzunlugu") or {})

        def kaydet(durum):
            uzunluk.setdefault(str(durum["ust"]), len(baglam["adimlar"]))
            k.devam = {"tur": "kaptan", "akis_durumu": durum, "baglam": baglam_sikistir(baglam), "yapilan": yapilan,
                       "hedef": hedef, "baglam_uzunlugu": uzunluk}
            k.ek["akis_izleri"] = durum["izler"]
            k.kaydet()
        y = AkisYurutucu(akis, self.motor.envanter, lambda d, hd: self._beceri_dugumu(d, hd, baglam, yapilan),
                         onay_iste=self._onay_dugumu, bildir=lambda d, durum: self._bildirim_dugumu(d, baglam),
                         yokla=self._yoklama, kontrol=kt, durdurma=self.durdurma, kaydet_fn=kaydet, olay_fn=k.olay,
                         saat=self.saat, uyu=self.uyu, akis_dizini=self.akis_dizini)
        if onceki and onceki.get("akis_durumu"):
            y.geri_yukle(onceki["akis_durumu"])
            for s in (sunucular or []):          # devam edilen sunucular yeniden işlenir
                y.devredilen.pop(s, None)
        self._yurutucu = y
        bas_kume = list(sunucular) if sunucular is not None else (list(hedef["sunucular"]) if hedef else [])
        durma = None
        try:
            kalan = y.yurut(bas_kume, baslangic)
        except AkisDurdu as e:
            durma, kalan = e, []
        devredilen = {s: v["neden"] for s, v in y.devredilen.items()}
        if durma is not None:
            if durma.durum == "iptal":
                return self._son(baglam, devredilen, "iptal", yapilan, f"İş iptal edildi: {durma.metin}")
            son = baglam["adimlar"][-1] if baglam["adimlar"] else {}
            if son.get("kuru"):
                baglam["son_uzak_adim"] = {**son, "sonuclar": son["kuru"]}
            if durma.durum == "onay_bekliyor" or (durma.durum == "onay" and k.durum == "onay_bekliyor"):
                return self._son(baglam, devredilen, "onay_bekliyor", yapilan)
            return self._son(baglam, devredilen, "reddedildi", yapilan,
                             durma.metin if durma.durum == "reddedildi" else "")
        if y.bitis:
            sonuc = y.bitis["sonuc"]
            durum = {"basarisiz": "basarisiz", "devret": "devredildi"}.get(sonuc) or (
                "bitti" if not devredilen else ("kismi" if kalan else "devredildi"))
            return self._son(baglam, devredilen, durum, yapilan, f"Akış bitir adımıyla sonlandı ({sonuc}): "
                                                                 f"{y.bitis.get('mesaj') or '-'}")
        durum = "bitti" if not devredilen else ("kismi" if kalan else "devredildi")
        ek_not = ""
        if y.uyarilar:          # "hata olsa da devam" adımlarındaki hatalar: iş başarılı sayılmaz
            durum = "kismi" if durum == "bitti" else durum
            ek_not = "Devam edilen hatalar (sunucu sonraki adımlara girdi ama bu kısımlar yapılamadı):\n" + "\n".join(
                f"- {s}: {'; '.join(v)}" for s, v in y.uyarilar.items())
        return self._son(baglam, devredilen, durum, yapilan, ek_not)

    # ------------------------------------------------------------ akış düğümleri (motorun geri çağrıları)
    def _beceri_dugumu(self, d, sunucular, baglam, yapilan):
        t = self.motor.katalog[d["beceri"]]
        if t["tur"] != "yerel" and not sunucular:
            self.kayit.olay("atlandi", f"{d['beceri']}: çalışacak sunucu kalmadı")
            return {"atlandi": True}
        hd = {**(self._hedef or {}), "sunucular": list(sunucular)} if t["tur"] != "yerel" else None
        a = {"beceri": d["beceri"], "parametreler": d.get("parametreler") or {}, "kimlik": d.get("kimlik"),
             "kimlik_calistirma": d.get("kimlik_calistirma")}
        sonuc = self._adim(a, hd, baglam, yapilan)
        if sonuc is not None and t["tur"] == "yerel":
            sonuc = {**sonuc, "yerel": True}
        return sonuc

    def _onay_dugumu(self, d, sunucular):
        """Akıştaki insan onayı adımı (gated): inisiyatif düzeyinden bağımsız, her zaman insan karar verir."""
        k = self.kayit
        plan = {"is_kimligi": k.kimlik, "beceri": "insan_onayi", "surum": 1, "risk": 3, "onay_gerekli": True,
                "risk_neden": "akıştaki onay adımı", "parametreler": {"mesaj": d.get("mesaj", "")},
                "hedef": {"sunucular": list(sunucular)}, "talep": k.talep, "ajan": self.ad}
        satir = self._iz("insan_onayi", 3, "onay_gerekli", "akıştaki onay adımı: her düzeyde insan karar verir",
                         "onay adımı")
        durum, kim, onay_k = self.motor.politika.onay(plan, [])
        if durum == "bekliyor":
            k.onay = {"durum": "bekliyor", "kimlik": onay_k, "mesaj": d.get("mesaj")}
            k.durum_yap("onay_bekliyor", f"akış onay adımı {d.get('kimlik')}: {d.get('mesaj')} (onay {onay_k})")
            k.kaydet()
            if self.onay_bekle_sn is None:
                satir["sonuc"] = "onay bekliyor"
                return "bekliyor"
            durum = onay_bekle(self.motor.politika.onaylar, onay_k, self.durdurma, self.onay_bekle_sn)
            k.durum_yap("calisiyor", f"onay adımı: {durum}")
        satir["sonuc"] = durum
        return "onaylandi" if durum == "onaylandi" else "reddedildi"

    def _bildirim_dugumu(self, d, baglam):
        k = self.kayit
        try:
            p = self.motor.plan("eposta_gonder", {"alici": d["alici"], "konu": d.get("konu") or f"Filo: {k.talep[:60]}"},
                                None, k.talep, self.ad, k.kimlik)
        except (PlanHatasi, ValueError) as e:
            k.olay("hata", f"bildirim gönderilemedi: {e}")
            return {"durum": "basarisiz"}
        a = self._calistir(p, {**baglam, "adimlar": list(baglam["adimlar"])}, "bildirim", onay_bekle=False)
        k.adim_ekle({**a, "aciklama": f"bildirim: {a.get('aciklama') or ''}".strip()})
        return a

    def _yoklama(self, c, sunucular):
        k = self.kayit
        p = self.motor.plan(c["beceri"], c.get("parametreler") or {}, {**(self._hedef or {}), "sunucular": list(sunucular)},
                            k.talep, self.ad, k.kimlik)
        a = self._calistir(p, {}, "yoklama", onay_bekle=False)
        k.adim_ekle({**a, "aciklama": "bekleme adımının yoklaması"})
        return a

    def _devir_bekle(self, a, basarisiz, sonuclar):
        """İnsana devir: iş 'devredildi' durumunda bekler. Operatörün kararı: yeniden_dene | kaptan (notla Kaptan yeniden
        karar verir) | atla (bu sunucular bırakılır). Bekleme yoksa None."""
        k = self.kayit
        if self.devir_bekle_sn is None:
            return None
        kt = self._kontrol or kontrol_al(k.kimlik, k)
        ozet = "; ".join(f"{h}: {sonuclar[h]['durum']} "
                         f"{(sonuclar[h].get('sema_hatasi') or sonuclar[h].get('neden') or sonuclar[h].get('stderr') or '').strip()[:120]}"
                         for h in basarisiz)
        k.ek["devir"] = {"adim": a["beceri"], "dugum": a.get("kimlik"), "sunucular": basarisiz, "neden": ozet,
                         "secenekler": {"yeniden_dene": "adımı başarısız sunucularda yeniden çalıştır",
                                        "kaptan": "notumu dikkate alarak Kaptan yeniden karar versin",
                                        "atla": "bu sunucuları bırak, akış kalanlarla sürsün"}}
        try:
            kar = kt.devir_bekle("operatör", f"{a['beceri']}: {len(basarisiz)} sunucu başarısız — {ozet[:300]}",
                                 self.durdurma, self.devir_bekle_sn)
        except IsIptal as e:
            raise AkisDurdu("iptal", str(e)) from None
        finally:
            k.ek.pop("devir", None)
        if kar:
            k.gerekce.append({"soru": "operatör kararı (insana devir)", "denemeler": [], "sonuc": kar,
                              "kod_notu": "Kaptan insana devretti; operatörün notu ve kararı Kaptan'a girdi oldu"})
        return kar

    def _zamanla(self):
        """Talep zamanlama içeriyorsa akış şimdi çalışmaz; zamanlayıcıya 'akis' tanımı olarak yazılır."""
        k = self.kayit
        zm = k.plan["zamanlama"]
        if self.zamanlayici is None:
            return self._bitir("hata", "Talep zamanlama içeriyor ama zamanlayıcı yok; iş başlatılmadı.")
        akis = self.akis_v2()
        tanim = {"tur": "akis", "akis": akis, "hedef_secici": (k.plan.get("hedef") or {}).get("secici"),
                 "inisiyatif": self.inisiyatif, "baglanti": k.baglanti, "talep": k.talep}
        plan_benzeri = {"onay_gerekli": any(inisiyatif_karari(self.inisiyatif, self.motor.katalog.etkin_risk(
            self.motor.katalog[d["beceri"]], d.get("parametreler") or {})[0])[0] == "onay_gerekli"
            for d in beceri_dugumleri(akis)), "beceri": "akis", "surum": 1, "risk": k.plan.get("risk"),
            "is_kimligi": k.kimlik, "hedef": k.plan.get("hedef"), "parametreler": {}}
        veren = on_onay_al(self.motor, plan_benzeri, self.on_onay_veren)
        z = self.zamanlayici.ekle(k.talep[:120], tanim, zm["zamanlama"], zm.get("hedef_cozumu", "simdi"),
                                  zm.get("kacirilan", "atla"), zm.get("yasak_politikasi"), f"kaptan:{k.kimlik}",
                                  on_onay=veren, dondurulmus=k.plan.get("hedef"))
        k.ek["zamanlama"] = z["kimlik"]
        k.rapor = zamanlama_raporu(z)
        return self._bitir("zamanlandi")

    def _oneri(self):
        """Düzey 0: hiçbir şey çalışmaz; akış, gerekçe ve her adımın hangi düzeyde onaysız geçeceği raporlanır."""
        k = self.kayit
        satirlar = [f"Öneri (inisiyatif düzeyi 0 — hiçbir sunucuda hiçbir şey çalıştırılmadı).",
                    f"Gerekçe: {k.plan.get('gerekce') or '-'}"]
        if k.plan.get("hedef"):
            satirlar.append(f"Hedef ({k.plan['hedef']['sayi']} sunucu, donduruldu): {', '.join(k.plan['hedef']['sunucular'])}")
        akis = self.akis_v2()
        if not duz_mu(akis):
            satirlar.append("Yapılı akış: " + akis_ozeti(akis))
        for i, a in enumerate(beceri_dugumleri(akis), 1):
            risk = self.motor.katalog.etkin_risk(self.motor.katalog[a["beceri"]], a["parametreler"])[0]
            en_az = "her düzeyde insan onayı" if risk >= 4 else f"düzey {max(1, risk)} ve üstünde onaysız"
            self._iz(a["beceri"], risk, "onerildi", "düzey 0: yalnız öneri, çalıştırılmaz", "adım", "çalıştırılmadı")
            satirlar.append(f"{i}. {a['beceri']} {kisa(a['parametreler'], 160)} — risk {risk}; {en_az}")
        k.rapor = "\n".join(satirlar)
        return self._bitir("oneri")

    def _yasak_ertele(self, baglam):
        """Yasak penceredeki sunucularda değiştiren adım başlamadı: politika 'bekle'/'sor' ise akış o sunucular için
        pencere kapanınca bir kez çalışacak şekilde zamanlanır (Kalfa'daki gibi). Dönüş: (not, ertelenen sunucular)."""
        yasak = {}
        for a in baglam["adimlar"]:
            for r in a.get("sonuclar", []):
                if r.get("yasak"):
                    yasak[r["sunucu"]] = r["yasak"]
        if not yasak:
            return "", []
        pen = self.motor._pencereler()
        pol = pen.varsayilan_politika()
        sunucular = sorted(yasak)
        ozet = ", ".join(f"{s} ('{v['pencere']}', {v['bitis']} kapanır)" for s, v in sorted(yasak.items()))
        if pol == "atla" or self.zamanlayici is None:
            return f"Yasak pencere: {ozet}. Bu sunucularda değiştiren adım başlamadı.", []
        k = self.kayit
        an = pen.yasak_sonu(self.motor.envanter, sunucular) if pol == "bekle" else pen.saat()
        tanim = {"tur": "akis", "akis": self.akis_v2(), "hedef_secici": {"ad": ",".join(sunucular)},
                 "inisiyatif": self.inisiyatif, "baglanti": k.baglanti, "talep": k.talep}
        z = self.zamanlayici.ekle(f"{k.talep[:90]} (yasak pencere sonrası)", tanim,
                                  {"tur": "tek", "zaman": an.isoformat(timespec="minutes")}, "simdi", "hemen", pol,
                                  f"kaptan:{k.kimlik}", dondurulmus={"secici": {"ad": ",".join(sunucular)},
                                                                     "sunucular": sunucular})
        k.ek.setdefault("ertelenen", []).append({"zamanlama": z["kimlik"], "sunucular": sunucular, "zaman": z["sonraki"]})
        return (f"Yasak pencere: {ozet}. Akış bu sunucular için pencere kapanınca ({z['sonraki']}) bir kez çalışmak üzere "
                f"ertelendi (zamanlanmış iş {z['kimlik']})."), sunucular

    def _son(self, baglam, devredilen, durum, yapilan, ek_not=""):
        k = self.kayit
        yasak_notu, ertelenen = self._yasak_ertele(baglam) if durum not in ("iptal",) else ("", [])
        if yasak_notu:
            ek_not = (ek_not + "\n\n" if ek_not else "") + yasak_notu
            gercek = {s: n for s, n in devredilen.items() if s not in ertelenen}
            if ertelenen and not gercek and durum in ("devredildi", "kismi", "bitti"):
                durum = "ertelendi" if durum == "devredildi" else "kismi"
            devredilen = gercek
        if ek_not:
            k.olay("akis", ek_not)
        eposta = next((a for a in (beceri_dugumleri(self.akis_v2()) if (k.plan or {}).get("akis") else [])
                       if a.get("beceri") == "eposta_gonder"), None)
        gonderildi = any(a.get("beceri") == "eposta_gonder" and a.get("durum") == "basarili" for a in baglam["adimlar"])
        if eposta and not gonderildi and durum not in ("bitti", "iptal") and baglam["adimlar"]:
            # İstenen bildirim yine gider: akış yarıda kaldıysa ne yapıldığı ve ne yapılamadığı raporlanır.
            ek = " / İnsana devredilen: " + "; ".join(f"{h}: {n}" for h, n in devredilen.items()) if devredilen else ""
            try:
                p = self.motor.plan("eposta_gonder", {**eposta["parametreler"], "konu": f"Filo: akış yarıda kaldı ({durum})"},
                                    None, k.talep + ek, self.ad, k.kimlik)
                a = self._calistir(p, baglam, "rapor", onay_bekle=False)
                k.adim_ekle(a)
            except (PlanHatasi, ValueError) as e:
                k.olay("hata", f"rapor e-postası gönderilemedi: {e}")
        k.rapor = rapor.ozet_metni(baglam["adimlar"])
        if ek_not:
            k.rapor += "\n\n" + ek_not
        if devredilen:
            k.rapor += "\n\nİnsana devredilen:\n" + "\n".join(f"- {h}: {n}" for h, n in devredilen.items())
            if self.model is not None:
                k.yorum = hata_yorumu(self.model, k.talep, baglam["adimlar"], k.gerekce)
        k.ek["yapilan"] = yapilan          # beceriye dönüştürme için gerçekten çalışan adımlar (onarımlar dahil)
        akis = self.akis_v2() if k.plan and k.plan.get("akis") else None
        if akis is not None and not duz_mu(akis):
            k.ek["yapili_akis"] = akis      # sabit akış olarak kaydedilecek olan yapının kendisidir
        if durum == "bitti" and yapilan and self.akis_otomatik_kaydet:
            yol = self.akis_kaydet(yapilan)
            k.olay("akis_kaydedildi", f"sabit akış kaydedildi: {yol.name}")
            k.rapor += f"\n\nBaşarılı akış sabit akış olarak kaydedildi: akislar/{yol.name}"
        return self._bitir(durum)

    def _adim(self, a, hd, baglam, yapilan):
        """Bir akış adımını yürütür; hata varsa teşhis/onarım döngüsü. Dönüş: son adım sonucu ya da None (onay)."""
        k = self.kayit
        kc = a.get("kimlik_calistirma")
        plan = self.motor.plan(a["beceri"], a["parametreler"], hd, k.talep, self.ad, k.kimlik, kimlik=kc)
        adim = self._yurut_plan(plan, baglam)
        if adim.get("dugum") is None and a.get("kimlik"):
            adim["dugum"] = a["kimlik"]
        if adim["durum"] in ("onay_bekliyor", "reddedildi"):
            k.adim_ekle(adim)
            baglam["adimlar"].append(adim)
            return None
        k.adim_ekle(adim)
        if adim["durum"] == "basarili" or self.motor.katalog[a["beceri"]]["tur"] == "yerel":
            baglam["adimlar"].append(adim)
            yapilan.append({"beceri": a["beceri"], "parametreler": a["parametreler"], "surum": plan["surum"]})
            return adim
        sonuclar = {r["sunucu"]: r for r in adim["sonuclar"]}
        deneme, sinir, operator_notu = 0, self.deneme_siniri, ""
        while not self.durdurma.basili():
            basarisiz = [h for h, r in sonuclar.items() if r["durum"] != "basarili" and not r.get("yasak")]
            if not basarisiz:
                break
            if deneme >= sinir:
                # Deneme sınırı doldu ya da model devretti: insana devir. Konsolda iş "devredildi" durumunda bekler;
                # operatörün notu/kararı Kaptan'a girdi olur. Bekleme yoksa (bench, komut satırı) sunucular bırakılır.
                kar = self._devir_bekle(a, basarisiz, sonuclar)
                if not kar or kar.get("karar") == "atla":
                    break
                if kar.get("karar") == "yeniden_dene":
                    karar = "yeniden_dene"
                    kanit = ""
                    deneme += 1
                else:
                    operator_notu = f"\nOperatörün notu ({kar.get('kim')}): {kar.get('not') or '-'}"
                    sinir = deneme + 1
                    continue
            else:
                deneme += 1
                k.olay("teshis", f"{a['beceri']}: {len(basarisiz)} sunucu başarısız, deneme {deneme}/{sinir}")
                kanit = self._kanit(a, [sonuclar[h] for h in basarisiz]) + operator_notu
                kanit += self._teshis(a, basarisiz, kanit, hd)
                karar = self._karar(a, basarisiz, kanit, sonuclar)
                if karar is None or karar == "devret":
                    k.olay("devret", f"{a['beceri']}: insana devredildi")
                    sinir = deneme
                    continue
            if karar.startswith("onarim:"):
                onarim = karar.split(":", 1)[1]
                ok = self._onarim(onarim, a, basarisiz, kanit, hd, baglam, yapilan)
                if ok is None:
                    return None
            degisim = None
            if karar == "beceriyi_degistir":
                degisim = self._degistir(a, basarisiz, kanit, hd)
                if not degisim:
                    continue
            # adımı yalnız başarısız sunucularda yeniden dene (sürüm değiştiyse yeni sürümle yeniden planlanır)
            p2 = self.motor.plan(a["beceri"], a["parametreler"], {**hd, "sunucular": basarisiz}, k.talep, self.ad, k.kimlik,
                                 kimlik=a.get("kimlik_calistirma"))
            tekrar = self._yurut_plan(p2, baglam)
            if tekrar["durum"] in ("onay_bekliyor", "reddedildi"):
                k.adim_ekle(tekrar)
                if degisim:
                    self._degisimi_geri_al(degisim, "değişiklik onaylanmadı")
                return None
            k.adim_ekle(tekrar)
            if degisim:
                hala = [r["sunucu"] for r in tekrar.get("sonuclar", []) if r["durum"] != "basarili"]
                neden = f"yeni sürüm {len(hala)} sunucuda yine başarısız" if hala else self._gerileme(a, p2, hd, sonuclar, basarisiz)
                if neden:
                    self._degisimi_geri_al(degisim, neden)
                    continue            # sonuçlar eski hâlinde kalır: başarısızlar başarısız sayılır
            for r in tekrar.get("sonuclar", []):
                sonuclar[r["sunucu"]] = r
        birlesik = {**adim, "sonuclar": [sonuclar[h] for h in hd["sunucular"] if h in sonuclar],
                    "surum": self.motor.katalog[a["beceri"]]["surum"]}
        from .motor import adim_durumu
        from .yurutme import ozetle
        birlesik["ozet"], birlesik["durum"] = ozetle(birlesik["sonuclar"]), adim_durumu(birlesik["sonuclar"])
        baglam["adimlar"].append(birlesik)
        baglam["son_uzak_adim"] = birlesik
        if birlesik["durum"] == "basarili":
            yapilan.append({"beceri": a["beceri"], "parametreler": a["parametreler"], "surum": birlesik["surum"]})
        return birlesik

    # ------------------------------------------------------------ teşhis ve karar
    def _kanit(self, a, sonuclar):
        satir = [f"Başarısız adım: {a['beceri']} (parametreler: {kisa(a['parametreler'], 200)})"]
        for r in sonuclar[:8]:
            aile = self.motor.envanter[r["sunucu"]].aile
            satir.append(f"- {r['sunucu']} ({aile}): {r['durum']}, çıkış {r.get('cikis_kodu')}; "
                         f"{kisa((r.get('sema_hatasi') or '') + ' ' + (r.get('stderr') or r.get('neden') or ''), 300)}"
                         + (f"; stdout: {kisa(r.get('stdout') or '', 200)}" if r.get("stdout") else ""))
        return "\n".join(satir)

    def _teshis(self, a, basarisiz, kanit, hd):
        k = self.kayit
        if all(self.kayit.izgara.get(h, {}).get("durum") == "erisilemedi" for h in basarisiz):
            return "\nTeşhis: sunuculara erişilemiyor; salt-okur teşhis çalıştırılamaz."
        ek = ""
        secenek = [t for t in TESHIS if t in self.motor.katalog]
        for _ in range(2):
            metin = (f"{kanit}{ek}\nTeşhis için salt-okur bir beceri seç (yalnız başarısız sunucularda çalışır). "
                     "Yeterli kanıt varsa \"yok\" yaz.\nSeçenekler:\n" + "\n".join(secenek_satiri(self.motor.katalog, t) for t in secenek)
                     + '\n- yok: teşhis gerekmiyor\nJSON: {"beceri": "<seçenek>", "parametreler": {...}, "gerekce": "<tek cümle>"}')

            def dogrula(v):
                b = str(v.get("beceri", "")).strip()
                if b == "yok":
                    return {"beceri": "yok"}, None
                if b not in secenek:
                    return None, f"şunlardan biri: {secenek + ['yok']}"
                try:
                    p = parametre_dogrula(self.motor.katalog[b].get("girdi") or {}, v.get("parametreler") or {})
                except SemaHatasi as e:
                    return None, str(e)
                return {"beceri": b, "parametreler": p, "gerekce": str(v.get("gerekce", ""))[:200]}, None
            s = sor_json(self.model, SISTEM, metin, dogrula, iz=k.gerekce, etiket=f"teşhis: {a['beceri']}")[0]
            if not s or s["beceri"] == "yok":
                break
            plan = self.motor.plan(s["beceri"], s["parametreler"], {**hd, "sunucular": basarisiz}, k.talep, self.ad, k.kimlik,
                                   kimlik=a.get("kimlik_calistirma"))
            t_adim = self._calistir(plan, {}, "teşhis", onay_bekle=False)
            k.adim_ekle({**t_adim, "aciklama": f"teşhis: {s['gerekce']}"})
            ek += f"\nTeşhis {s['beceri']} {kisa(s['parametreler'], 120)} sonucu:\n" + "\n".join(
                f"  {r['sunucu']}: {kisa((r.get('stdout') or r.get('neden') or r.get('stderr') or '').strip(), 400)}"
                for r in t_adim.get("sonuclar", []))
        return ek

    def _karar(self, a, basarisiz, kanit, sonuclar):
        k = self.kayit
        erisilemez = all(sonuclar[h]["durum"] == "erisilemedi" for h in basarisiz)
        se = ["yeniden_dene", "devret"]
        aciklama = {"yeniden_dene": "aynı adımı başarısız sunucularda yeniden çalıştır (geçici hata ise)",
                    "devret": "insana devret (erişim, yetki, belirsizlik ya da riskli müdahale)"}
        sema_sorunu = all(sonuclar[h].get("sema_hatasi") and sonuclar[h].get("cikis_kodu") == 0 for h in basarisiz)
        degistirebilir = self.inisiyatif >= 3
        if not degistirebilir and self.motor.katalog[a["beceri"]]["tur"] == "uzak":
            self._iz(a["beceri"], None, "kapali", f"beceri değiştirme düzey 3 ister (düzey {self.inisiyatif}); seçenek "
                                                  "modele sunulmadı", "karar")
        if sema_sorunu and self.motor.katalog[a["beceri"]]["tur"] == "uzak":
            # Komut başarıyla bitti ama çıktı şemaya uymuyor: yeniden denemek ya da servis/paket onarımı bunu
            # düzeltmez. Kod seçenekleri daraltır: beceriyi (ya da betiği) değiştir ya da devret.
            se = ["beceriyi_degistir", "devret"] if degistirebilir else ["devret"]
            aciklama["beceriyi_degistir"] = ("komut başarıyla bitti ama çıktı biçimi beklenen şemaya uymuyor; becerinin "
                                             "ya da betiğin yeni sürümünü yaz")
        elif not erisilemez:
            metin_n = normal(kanit)
            onarimlar = [o for o in ONARIM if o in self.motor.katalog and o != a["beceri"]]
            if not talep_eylemleri(self.motor.katalog, k.talep) and not self.ek_adaylar:
                # Talep yalnız okuma/raporlama istiyorsa sunucuyu değiştiren onarım seçenek olarak sunulmaz (üçüncü tur
                # O05: "durumunu kontrol et" talebinde Kaptan yavaş servise servis_baslat uyguladı).
                onarimlar = []
                k.olay("karar", f"{a['beceri']}: talepte değiştirici eylem yok; onarım seçenekleri sunulmadı")
            # kod daraltması: kanıtla ilgisi olan onarımlar önce, en çok 4
            onarimlar.sort(key=lambda o: -len({w for w in re.findall(r"[a-z]{4,}", normal(
                " ".join(self.motor.katalog[o].get("etiketler", []))))} & set(re.findall(r"[a-z]{4,}", metin_n))))
            for o in onarimlar[:4]:
                se.insert(-1, f"onarim:{o}")
                aciklama[f"onarim:{o}"] = f"önce {o} çalıştır ({self.motor.katalog[o]['baslik']}), sonra adımı yeniden dene"
            if self.motor.katalog[a["beceri"]]["tur"] == "uzak" and degistirebilir:
                se.insert(-1, "beceriyi_degistir")
                aciklama["beceriyi_degistir"] = ("adımın komutu ya da betiği bu sunucularda yanlış çalışıyor ya da çıktısı "
                                                 "şemaya uymuyor; becerinin yeni sürümünü yaz")
        if se == ["devret"]:
            k.olay("karar", f"{a['beceri']}: bu düzeyde tek seçenek devretmek (model çağrılmadı)")
            return "devret"
        metin = (f"{kanit}\nNe yapılmalı? Seçenekler:\n" + "\n".join(f"- {s}: {aciklama[s]}" for s in se)
                 + '\nJSON: {"karar": "<seçenek>", "gerekce": "<tek cümle>"}')
        out = sor_json(self.model, SISTEM, metin,
                       lambda v: ((str(v.get("karar")).strip(), None) if str(v.get("karar", "")).strip() in se
                                  else (None, f"şunlardan biri: {se}")),
                       iz=k.gerekce, etiket=f"karar: {a['beceri']}")[0]
        k.olay("karar", f"{a['beceri']}: {out or 'cevap yok → devret'}")
        return out

    def _onarim(self, onarim, a, basarisiz, kanit, hd, baglam, yapilan):
        k = self.kayit
        p = parametre_sor(self.model, self.motor.katalog, onarim, k.talep, k.gerekce,
                          kaynak_metin=kanit + " " + json.dumps(a["parametreler"], ensure_ascii=False),
                          ek=f"Bu bir onarım adımıdır. Kanıt:\n{kanit}\n")
        if p is None:
            k.olay("onarim", f"{onarim}: parametre doldurulamadı")
            return False
        plan = self.motor.plan(onarim, p, {**hd, "sunucular": basarisiz}, k.talep, self.ad, k.kimlik,
                               kimlik=a.get("kimlik_calistirma"))
        o = self._yurut_plan(plan, baglam, "onarım")
        k.adim_ekle({**o, "aciklama": f"onarım: {o.get('aciklama') or ''}".strip()})
        if o["durum"] in ("onay_bekliyor",):
            return None
        if o["durum"] == "basarili":
            yapilan.append({"beceri": onarim, "parametreler": p, "surum": plan["surum"], "onarim": True})
        return o["durum"] == "basarili"

    def _gerileme(self, a, plan, hd, sonuclar, basarisiz):
        """Değişen salt-okur beceriyi, eski sürümle başarılı olmuş bir sunucuda da dener. Bozarsa neden döner."""
        if plan["risk"] > 1:
            return None          # değiştiren beceri sağlam sunucuda yeniden çalıştırılmaz
        saglam = [h for h, r in sonuclar.items() if r["durum"] == "basarili" and h not in basarisiz]
        if not saglam:
            return None
        k = self.kayit
        p3 = self.motor.plan(a["beceri"], a["parametreler"], {**hd, "sunucular": saglam[:1]}, k.talep, self.ad, k.kimlik,
                             kimlik=a.get("kimlik_calistirma"))
        g = self._calistir(p3, {}, "gerileme sınaması", onay_bekle=False)
        k.adim_ekle({**g, "aciklama": "gerileme sınaması: yeni sürüm, eskisiyle başarılı olan sunucuda"})
        if g["durum"] != "basarili":
            return f"gerileme: yeni sürüm {saglam[0]} üzerinde bozuldu"
        return None

    def _degisimi_geri_al(self, d, neden):
        k = self.kayit
        g = self.motor.katalog.geri_don(d["kayit"], d["ad"], d["eski_surum"], f"kaptan:{k.kimlik}")
        d["geri_alindi"] = {"neden": neden, "yeni_surum": g["yeni_surum"]}
        k.olay("degisiklik_geri_alindi", f"{d['kayit']} {d['ad']}: {neden}; v{d['eski_surum']} içeriği "
                                         f"v{g['yeni_surum']} olarak geri yüklendi")

    def _degistir(self, a, basarisiz, kanit, hd):
        """Model yeni komut ya da betik yazar; kod yeni sürüm olarak kaydeder (risk yeniden sınıflanır)."""
        k = self.kayit
        katalog = self.motor.katalog
        if self.inisiyatif < 3:            # seçenek sunulmasa da: kod sınırı ikinci kez denetler
            self._iz(a["beceri"], None, "reddedildi", f"beceri değiştirme düzey 3 ister (düzey {self.inisiyatif})",
                     "değişiklik", "reddedildi")
            return None
        t = katalog[a["beceri"]]
        aile = self.motor.envanter[basarisiz[0]].aile
        if (t.get("komut") or {}).get("linux") == "@betik":
            tur, ad, dosya = "betik", a["parametreler"]["betik"], "betik.sh"
            eski = katalog.betik_oku(ad)
            sema = katalog.betik_meta(ad).get("cikti")
            nesne = f"betik kütüphanesindeki '{ad}' betiği"
        else:
            tur, ad, dosya = "beceri", a["beceri"], f"komut.{aile}"
            sunucu = self.motor.envanter[basarisiz[0]]
            eski = komut_sec(t.get("komut"), sunucu) or ""
            sema = t.get("cikti")
            nesne = f"'{ad}' becerisinin {aile} komutu"
        metin = (f"{kanit}\nŞu anki {nesne}:\n---\n{eski}\n---\nBeklenen çıktı şeması: {json.dumps(sema, ensure_ascii=False)}\n"
                 "Bu metnin düzeltilmiş tam hâlini yaz. Yalnız gerekeni değiştir; gereksiz yazan komut ekleme "
                 "(eklenirse risk düzeyi yükselir ve insan onayı gerekir). {ad} biçimindeki yer tutucuları koru.\n"
                 'JSON: {"yeni_icerik": "<tam metin>", "gerekce": "<tek cümle>"}')

        def dogrula(v):
            y = v.get("yeni_icerik")
            if not isinstance(y, str) or not y.strip():
                return None, "yeni_icerik boş"
            if len(y) > 4000:
                return None, "en çok 4000 karakter"
            if y.strip() == eski.strip():
                return None, "yeni içerik eskisiyle aynı"
            return {"yeni_icerik": y.strip() + "\n", "gerekce": str(v.get("gerekce", ""))[:300]}, None
        out = sor_json(self.model, SISTEM, metin, dogrula, iz=k.gerekce, etiket=f"değişiklik: {ad}")[0]
        if not out:
            return None
        try:
            if tur == "betik":
                d = katalog.yeni_surum("betik", ad, {"betik.sh": out["yeni_icerik"]}, f"kaptan:{k.kimlik}", out["gerekce"])
            else:
                yeni = json.loads(json.dumps(t))
                yeni["komut"][aile if aile in yeni["komut"] else "linux"] = out["yeni_icerik"].rstrip("\n")
                d = katalog.yeni_surum("beceri", ad, {"beceri.json": json.dumps(yeni, ensure_ascii=False, indent=2)},
                                       f"kaptan:{k.kimlik}", out["gerekce"])
        except SemaHatasi as e:
            k.olay("degisiklik_reddi", f"{ad}: {e}")
            return None
        k.degisiklikler.append({**d, "adim": a["beceri"]})
        k.olay("degisiklik", f"{tur} {ad}: v{d['eski_surum']} → v{d['yeni_surum']}, risk {d['risk_onceki']} → {d['risk_yeni']}"
                             + (" (yükseldi, onay gerekecek)" if d["risk_yukseldi"] else ""))
        return k.degisiklikler[-1]

    # ------------------------------------------------------------ sabit akışlar
    def akis_kaydet(self, yapilan):
        k = self.kayit
        self.akis_dizini.mkdir(parents=True, exist_ok=True)
        tarih = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        kok = re.sub(r"[^a-z0-9]+", "-", normal(k.talep))[:40].strip("-") or "akis"
        yol = self.akis_dizini / f"{kok}-{tarih}.json"
        veri = _sabit_akis_verisi(yol.stem, k.talep, tarih, k.kimlik, (k.plan.get("hedef") or {}).get("secici"),
                                  yapilan, k.ek.get("yapili_akis"))
        yol.write_text(json.dumps(veri, ensure_ascii=False, indent=2), encoding="utf-8")
        return yol

    def calistir(self, talep):
        self.planla(talep)
        if self.kayit.durum != "plan_hazir":
            return self.kayit
        return self.yurut()


def akis_kaydet_kayittan(is_, dizin=None):
    """Bitmiş bir Kaptan işinin kaydından sabit akış yazar (arayüzdeki 'Sabit akış olarak kaydet')."""
    if is_.get("durum") != "bitti" or not (is_.get("ek") or {}).get("yapilan"):
        raise ValueError("yalnız başarıyla bitmiş bir Kaptan akışı sabit akış olarak kaydedilir")
    d = dizin or AKISLAR
    d.mkdir(parents=True, exist_ok=True)
    tarih = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    kok = re.sub(r"[^a-z0-9]+", "-", normal(is_["talep"]))[:40].strip("-") or "akis"
    yol = d / f"{kok}-{tarih}.json"
    veri = _sabit_akis_verisi(yol.stem, is_["talep"], tarih, is_["kimlik"],
                              ((is_.get("plan") or {}).get("hedef") or {}).get("secici"), is_["ek"]["yapilan"],
                              is_["ek"].get("yapili_akis"))
    yol.write_text(json.dumps(veri, ensure_ascii=False, indent=2), encoding="utf-8")
    return yol


def _sabit_akis_verisi(ad, talep, tarih, kaynak_is, secici, yapilan, yapili=None):
    """Düz akış eski biçimde (sürüm 1, onarımlar dahil gerçekten çalışan adımlar) kalır; yapılı akış sürüm 2 olarak
    yapısıyla kaydedilir (Kaptan'ın duruma özgü onarımları kalıcı adım olmaz)."""
    if yapili:
        return {**yapili, "ad": ad, "talep": talep, "olusturma": tarih, "kaynak_is": kaynak_is, "hedef_secici": secici}
    return {"ad": ad, "talep": talep, "olusturma": tarih, "kaynak_is": kaynak_is, "hedef_secici": secici,
            "adimlar": yapilan}


def akis_listesi(dizin=None):
    """Kayıtlı sabit akışlar (sürüm 1 dosyaları olduğu gibi okunur; `ozet` ve `surum` alanları eklenir)."""
    from .akis_motoru import akis_ozeti
    d = dizin or AKISLAR
    out = []
    for p in sorted(d.glob("*.json")) if d.exists() else []:
        try:
            x = json.loads(p.read_text(encoding="utf-8"))
        except ValueError:
            continue
        v2 = eski_akistan(x)
        out.append({**x, "ad": x.get("ad") or p.stem, "surum": x.get("surum", 1) if x.get("bicim") else 1,
                    "ozet": akis_ozeti(v2), "yapili": not duz_mu(v2)})
    return out


def akis_yurut(motor, ad, hedef=None, kayit=None, dizin=None, girdi=None, inisiyatif=2, onay_bekle_sn=None):
    """Kayıtlı sabit akışı (sürüm 1 düz ya da sürüm 2 yapılı) modele sormadan yürütür. Değiştiren adımlar inisiyatif
    düzeyi 2 kuralıyla geçer (risk 3+ onay ister). Başarısız sunucu sonraki adımlara girmez ve raporlanır; teşhis ve
    onarım yoktur (model yok)."""
    from .akis_motoru import akis_yukle, dogrula
    akis = akis_yukle(ad, dizin or AKISLAR)
    if girdi:
        akis = {**akis, "girdi": {a: {**x, "varsayilan": girdi.get(a, x.get("varsayilan"))}
                                  for a, x in (akis.get("girdi") or {}).items()}}
    hatalar = dogrula(akis, motor.katalog, dizin or AKISLAR)
    if hatalar:
        raise PlanHatasi("sabit akış geçersiz: " + "; ".join(hatalar[:5]))
    k = kayit or IsKaydi(akis.get("talep") or ad, "sabit-akis")
    secici = hedef or akis.get("hedef_secici")
    dondurulmus = motor.envanter.dondur(secici) if secici else None
    kap = Kaptan(None, motor, k, inisiyatif=inisiyatif, deneme_siniri=0, akis_dizini=dizin or AKISLAR,
                 onay_bekle_sn=onay_bekle_sn, yapi_kur=False)
    kap.akis_otomatik_kaydet = False
    kap._kayit(k.talep)
    k.plan = {"sabit_akis": ad, "akis": akis, "hedef": dondurulmus,
              "adimlar": [d.get("beceri") or d.get("tur") for d in akis["adimlar"]]}
    return kap.yurut()
