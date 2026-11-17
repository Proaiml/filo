"""Kalfa: yalnız hazır becerilerle çalışan ajan (sunucu otomasyonu sınıfı).

talep → katalogdan beceri seçimi (kod adayları daraltır, model seçer) → parametre (model doldurur, kod doğrular)
→ hedef (model seçici yazar, kod çözer ve dondurur) → plan → onay → yürütme → (dönüştürme, e-posta) → rapor.

Kalfa beceri değiştirmez ve yeni komut yazmaz. Uygun beceri yoksa bunu açıkça söyler. Raporu kod yazar (sayılar,
başarısız sunucular, öykünme); model yalnız başarısızlık için ayrı etiketli kısa bir yorum ekler.
"""
from . import rapor
from .ajan_ortak import aday_beceriler, beceri_sec, bicim_ve_alici, hata_yorumu, hedef_sor, parametre_sor
from .erisim import DURDURMA
from .isler import IsKaydi, onay_bekle
from .akis_motoru import baglam_coz, baglam_sikistir
from .kimlik import kimlik_sor
from .kontrol import IsIptal
from .kontrol import kontrol as kontrol_al
from .motor import PlanHatasi
from .zamanlayici import ZamanlamaHatasi
from .zamanli import on_onay_al, zamanlama_plani, zamanlama_raporu


class Kalfa:
    ad = "kalfa"

    def __init__(self, model, motor, kayit=None, durdurma=DURDURMA, onay_bekle_sn=None, zamanlayici=None,
                 on_onay=None, yasak_istisnasi=None, on_onay_veren=None):
        self.model, self.motor, self.durdurma = model, motor, durdurma
        self.kayit = kayit
        self.onay_bekle_sn = onay_bekle_sn       # None: onay gerekiyorsa beklemeden durur (komut satırı)
        self.zamanlayici = zamanlayici           # talep zamanlama içeriyorsa iş buraya kaydedilir
        self.on_onay = on_onay                   # zamanlanmış koşunun önceden onayı (zamanlayıcı verir)
        self.yasak_istisnasi = yasak_istisnasi   # operatörün yasak pencere istisnası (zamanlayıcıdaki soru cevabı)
        self.on_onay_veren = on_onay_veren       # zamanlarken önceden onay veren operatör (arayüz)
        if zamanlayici is not None and getattr(motor, "zamanlayici", None) is None:
            motor.zamanlayici = zamanlayici      # D1: yama sonrası yeniden başlatma bakım penceresine bu zamanlayıcıya yazılır

    def _kayit(self, talep):
        if self.kayit is None:
            self.kayit = IsKaydi(talep, self.ad, getattr(self.model, "spec", None))
        return self.kayit

    def _bitir(self, durum, metin=""):
        k = self.kayit
        k.model_cagri = getattr(self.model, "cagri", 0)
        if metin:
            k.rapor = (k.rapor + "\n" + metin).strip()
        k.durum_yap(durum, metin or durum)
        k.kaydet()
        return k

    # ------------------------------------------------------------ plan
    def planla(self, talep):
        k = self._kayit(talep)
        katalog, iz = self.motor.katalog, k.gerekce
        import re
        from .ajan_ortak import normal
        if re.search(r"\b[a-z0-9]+(-[a-z0-9]+)+ akis(i|ini|ina)\b|\bsabit akis", normal(talep)):
            # Tam koşu A04: talep kayıtlı bir akışı adıyla istiyordu; Kalfa "hiçbiri" sınamasında adı benzeyen bir
            # betiği çalıştırıp başarı bildirdi (sahte başarı). Kalfa akış yürütmez: kod bunu baştan söyler.
            return self._bitir("beceri_yok", "Talep kayıtlı bir akışı (adıyla) çalıştırmak istiyor; Kalfa yalnız tek hazır "
                                             "beceri yürütür, akış yürütmez. Kaptan ile ya da `python -m filo akis calistir "
                                             "<ad>` ile çalıştırın. Hiçbir sunucuda işlem yapılmadı.")
        adaylar = aday_beceriler(katalog, talep)
        k.olay("daraltma", f"aday beceriler: {', '.join(adaylar)}")
        secim = beceri_sec(self.model, katalog, talep, adaylar, iz)
        if secim is None:
            return self._bitir("hata", "Model beceri seçimine geçerli bir cevap vermedi; iş başlatılmadı.")
        if secim["secim"] == "hicbiri":
            return self._bitir("beceri_yok", "Katalogda bu talebi karşılayan bir beceri yok. Kalfa yeni beceri yazmaz; "
                                             "Kaptan ile deneyin ya da kataloğa beceri ekleyin. Hiçbir sunucuda işlem yapılmadı.")
        ad = secim["secim"]
        k.olay("karar", f"beceri: {ad} ({secim['gerekce']})")
        secici = hedef_sor(self.model, self.motor.envanter, talep, iz)
        if secici is None:
            return self._bitir("hata", "Hedef sunucular talepten çözülemedi; iş başlatılmadı.")
        param = parametre_sor(self.model, katalog, ad, talep, iz, sunucu_adlari=list(self.motor.envanter.sunucular))
        if param is None:
            son = (iz[-1]["denemeler"][-1].get("hata") if iz and iz[-1]["denemeler"] else "") or ""
            return self._bitir("hata", f"{ad} için parametreler talepten doldurulamadı ({son}); iş başlatılmadı.")
        bicim, alici = bicim_ve_alici(self.model, talep, iz)
        icerir = {a["beceri"] for a in katalog[ad].get("adimlar", [])}
        if "sonucu_donustur" in icerir:           # beceri (ör. dönüştürülmüş bir akış) biçimi kendisi üretiyor
            bicim = None
        if "eposta_gonder" in icerir:
            alici = None
        kc = kimlik_sor(self.model, talep, iz)     # "root olarak", "webops kullanıcısıyla" → çalıştırma kimliği
        try:
            plan = self.motor.plan(ad, param, secici, talep, self.ad, is_kimligi=k.kimlik, kimlik=kc)
        except (PlanHatasi, ValueError) as e:
            return self._bitir("hata", f"plan kurulamadı: {e}")
        yapi = self._kosullu_degisiklik(talep, plan)
        if yapi:
            return self._bitir("beceri_yok", yapi)
        eksik = self._kapsam(talep, ad, bicim, alici, iz, plan.get("parametreler"))
        k.plan = {"ana": plan, "bicim": bicim, "alici": alici, "gerekce": secim["gerekce"], "eksik": eksik,
                  "adimlar": [ad] + (["sonucu_donustur"] if bicim else []) + (["eposta_gonder"] if alici else [])}
        try:
            zm = zamanlama_plani(self.model, self.motor, talep, iz, (plan.get("hedef") or {}).get("sunucular"))
        except ZamanlamaHatasi as e:
            return self._bitir("hata", f"Talepteki zamanlama çözülemedi: {e}. İş başlatılmadı.")
        if zm:
            k.plan["zamanlama"] = zm
        k.model_cagri = getattr(self.model, "cagri", 0)
        k.durum_yap("plan_hazir", f"plan: {ad}, {len(plan['hedef']['sunucular'])} sunucu, risk {plan['risk']}"
                                  + (", onay gerekli" if plan["onay_gerekli"] else "")
                                  + (f", zamanlama: {zm['okunakli']}" if zm else ""))
        k.kaydet()
        return k

    # ------------------------------------------------------------ zamanlama
    def _zamanla(self):
        """Plan zamanlama içeriyorsa iş şimdi çalışmaz; zamanlayıcıya model çağırmadan yürütülecek bir tanım olarak yazılır."""
        k = self.kayit
        plan, zm = k.plan["ana"], k.plan["zamanlama"]
        if self.zamanlayici is None:
            return self._bitir("hata", "Talep zamanlama içeriyor ama zamanlayıcı yok (konsol ya da bench dışında); "
                                       "iş başlatılmadı.")
        tanim = {"tur": "beceri", "beceri": plan["beceri"], "parametreler": plan["parametreler"],
                 "hedef_secici": (plan.get("hedef") or {}).get("secici"), "bicim": k.plan.get("bicim"),
                 "alici": k.plan.get("alici"), "kimlik": plan.get("kimlik_calistirma"), "talep": k.talep}
        veren = on_onay_al(self.motor, plan, self.on_onay_veren)
        z = self.zamanlayici.ekle(k.talep[:120], tanim, zm["zamanlama"], zm.get("hedef_cozumu", "simdi"),
                                  zm.get("kacirilan", "atla"), zm.get("yasak_politikasi"), f"kalfa:{k.kimlik}",
                                  on_onay=veren, dondurulmus=plan.get("hedef"))
        k.ek["zamanlama"] = z["kimlik"]
        k.rapor = zamanlama_raporu(z, plan)
        return self._bitir("zamanlandi")

    def _kosullu_degisiklik(self, talep, plan):
        """Talep sunucu bazında koşullu ya da öğe öğe (döngü) bir DEĞİŞİKLİK istiyorsa Kalfa bunu tek beceriyle bütün
        hedefe uygulamaz (duman koşusu A01: "çalışmayanlarda yeniden başlat" talebinde çalışan servis de yeniden
        başlatıldı). Kod ipucunu bulur; iş başlatılmaz, Kaptan önerilir."""
        from .akis_kurucu import yapi_ipuclari
        if plan["risk"] < 2:
            return None
        ipucu, _ = yapi_ipuclari(talep)
        tur = [x for x in ipucu if x in ("sunucu_dal", "dongu")]
        if not tur:
            return None
        ad = {"sunucu_dal": "yalnız bir koşulu sağlayan sunucularda", "dongu": "öğe öğe (her biri için ayrı)"}
        self.kayit.olay("kapsam", f"kod: talep {', '.join(ad[x] for x in tur)} değişiklik istiyor; Kalfa tek beceriyi "
                                  "bütün hedefe uygular")
        return (f"Talep {', '.join(ad[x] for x in tur)} bir değişiklik istiyor; Kalfa tek hazır beceriyi bütün hedefe "
                f"uygular ve bunu koşullu yapamaz. Yanlış sunucuda değişiklik yapmamak için iş başlatılmadı; Kaptan ile "
                f"deneyin (yapılı akış kurar). Hiçbir sunucuda işlem yapılmadı.")

    def _kapsam(self, talep, ad, bicim, alici, iz, parametreler=None):
        """Kalfa tek beceri yürütür. Talep bunun dışında bir iş de istiyorsa (ör. "durumuna bak VE yeniden başlat")
        iş sonunda 'bitti' değil 'kismi' denir ve yapılmayan kısım raporda yazılır (ikinci koşu I07/O11: Kalfa işin
        yarısını yapıp 'başarılı' dedi, hakem sahte başarı saydı)."""
        from .ajan_ortak import SISTEM, kapsam_eksigi
        from .gateway import sor_json
        # Önce kod: talepteki değiştirici eylemlerden seçilen becerinin (ve zincir adımlarının) yapmadığı var mı?
        # Kodun bulduğu eksik modelin "yok" cevabıyla silinemez (ikinci koşu O11: model "yok" dedi, sahte başarı).
        kod_eksik = kapsam_eksigi(self.motor.katalog, talep, [ad], {ad: parametreler})
        if kod_eksik:
            metin = "; ".join(kod_eksik)
            self.kayit.olay("kapsam", f"kod denetimi: talepteki şu iş(ler)i {ad} yapmaz: {metin}")
            iz.append({"soru": "kapsam (kod)", "denemeler": [], "sonuc": {"eksik": metin},
                       "kod_notu": "talepteki değiştirici eylemler ve salt-okur işler beceri kapsamıyla karşılaştırıldı; "
                                   "model sorulmadı"})
            return metin
        if self.motor.katalog[ad]["tur"] == "zincir":
            return None          # zincir beceri çok adımlı işi zaten kapsar (dönüştürülmüş akışlar); soru sorulmaz
        yapilacak =f"{ad} ({self.motor.katalog[ad]['baslik']})" + (f", sonucu {bicim} yapmak" if bicim else "") + \
            (f", {alici} adresine e-posta" if alici else "")
        metin = (f"Talep: \"{talep}\"\nYapılacak işler yalnız şunlar: {yapilacak}.\nTalep bunların DIŞINDA sunucuda yapılacak "
                 "başka bir iş istiyor mu (ör. ikinci bir değişiklik, başlatma, dağıtma)? Yoksa \"yok\" yaz.\n"
                 'JSON: {"eksik": "yok" | "<yapılmayacak işin kısa adı>"}')
        out = sor_json(self.model, SISTEM, metin, lambda v: ((str(v.get("eksik", "")).strip()[:200], None)
                                                              if str(v.get("eksik", "")).strip() else (None, "eksik alanı boş")),
                       iz=iz, etiket="kapsam")[0]
        return None if not out or out.lower() in ("yok", "hayir", "hayır", "none") else out

    # ------------------------------------------------------------ yürütme
    def _devam_kaydet(self, baglam, sonraki, girenler=None):
        """Kaldığı yerden sürdürme durumu: bir sonraki adım (0 ana, 1 dönüştürme, 2 e-posta) ve bağlam."""
        k = self.kayit
        d = dict(k.devam or {"tur": "kalfa", "adim_girisi": {}})
        d.update(tur="kalfa", sonraki=sonraki, baglam=baglam_sikistir(baglam))
        d.setdefault("baglam_uzunlugu", {})[str(sonraki)] = len(baglam["adimlar"])
        if girenler is not None:
            d.setdefault("adim_girisi", {})["0"] = list(girenler)
        k.devam = d
        k.kaydet()

    def yurut(self, baslangic=0, sunucular=None, onceki=None):
        """`baslangic`: 0 ana adım, 1 dönüştürme, 2 e-posta (adımdan devam); `sunucular`: ana adımın hedefi (yalnız
        başarısızlar ya da hepsi); `onceki`: önceki koşunun kayıtlı durumu (bağlam)."""
        k = self.kayit
        if not k or not k.plan:
            raise PlanHatasi("önce planla")
        if self.durdurma.basili():
            return self._bitir("iptal", "Durdurma düğmesi basılı; iş başlatılmadı.")
        if k.plan.get("zamanlama") and not k.plan.get("simdi_calistir") and not onceki:
            return self._zamanla()
        kt = kontrol_al(k.kimlik, k)
        try:
            return self._yurut(kt, baslangic, sunucular, onceki)
        except IsIptal as e:
            return self._bitir("iptal", f"İş iptal edildi: {e}. Tamamlanan adımlar raporda; kalan adımlar çalışmadı.")

    def _yurut(self, kt, baslangic, sunucular, onceki):
        k = self.kayit
        plan = {**k.plan["ana"]}
        if self.on_onay:
            plan["on_onay"] = self.on_onay
        if self.yasak_istisnasi:
            plan["yasak_istisnasi"] = self.yasak_istisnasi
        if sunucular is not None and plan.get("hedef"):
            plan["hedef"] = {**plan["hedef"], "sunucular": list(sunucular), "sayi": len(sunucular)}
        baglam = baglam_coz((onceki or {}).get("baglam")) or {"adimlar": []}
        k.durum_yap("calisiyor")
        if baslangic > 0:
            adim = baglam.get("son_uzak_adim") or {}
            yasak_notu = ""
            return self._ek_adimlar(kt, plan, adim, baglam, baslangic, yasak_notu)
        kt.nokta("ana adım öncesi", self.durdurma)
        self._devam_kaydet(baglam, 0, (plan.get("hedef") or {}).get("sunucular"))
        adim = self.motor.yurut(plan, baglam, k.gozlemci(plan["beceri"]))
        if adim["durum"] == "onay_bekliyor":
            k.onay = adim.get("onay")
            k.durum_yap("onay_bekliyor", f"düzey {plan['risk']} işlem insan onayı bekliyor (onay {k.onay['kimlik']})")
            k.kaydet()
            if self.onay_bekle_sn is None:
                return k
            karar = onay_bekle(self.motor.politika.onaylar, k.onay["kimlik"], self.durdurma, self.onay_bekle_sn)
            if karar != "onaylandi":
                return self._bitir("reddedildi" if karar == "reddedildi" else "iptal",
                                   f"Onay sonucu: {karar}. Hiçbir sunucuda değişiklik yapılmadı.")
            k.durum_yap("calisiyor", "onay verildi")
            adim = self.motor.yurut({**plan, "onay_kimligi": k.onay["kimlik"], "kuru_yapildi": True}, baglam,
                                    k.gozlemci(plan["beceri"]))
        k.adim_ekle(adim)
        baglam["adimlar"].append(adim)
        yasak_notu = self._yasak_ertele(adim) if adim.get("yasak") else ""
        if yasak_notu and all(r.get("yasak") for r in adim.get("sonuclar", [])):    # bütün hedefler yasakta
            k.rapor = rapor.ozet_metni(baglam["adimlar"]) + "\n\n" + yasak_notu
            return self._bitir("ertelendi" if "ertelendi" in yasak_notu else "iptal")
        if adim["durum"] in ("reddedildi", "onay_bekliyor"):
            metin = f"{plan['beceri']}: {adim.get('aciklama')}. Hiçbir sunucuda değişiklik yapılmadı."
            if k.plan["alici"] and adim.get("kuru"):
                # İstenen bildirim yine gider: ne yapılacaktı (kuru çalıştırma) ve neden yapılmadı.
                baglam["son_uzak_adim"] = {**adim, "sonuclar": adim["kuru"]}
                a = self.motor.yurut(self.motor.plan("eposta_gonder", {"alici": k.plan["alici"], "konu":
                                     f"Filo: {plan['baslik']} (yapılmadı: {adim['durum']})"}, None,
                                     k.talep + " / " + metin, self.ad, k.kimlik), baglam)
                k.adim_ekle(a)
            return self._bitir("reddedildi", metin)
        self._devam_kaydet(baglam, 1)
        return self._ek_adimlar(kt, plan, adim, baglam, 1, yasak_notu)

    def _ek_adimlar(self, kt, plan, adim, baglam, baslangic, yasak_notu):
        k = self.kayit
        for i, (ad, p) in enumerate(((("sonucu_donustur", {"bicim": k.plan["bicim"]}) if k.plan.get("bicim") else (None, None)),
                                      (("eposta_gonder", {"alici": k.plan["alici"], "konu": f"Filo: {plan['baslik']}"})
                                       if k.plan.get("alici") else (None, None))), 1):
            if i < baslangic or not ad or self.durdurma.basili() or not adim.get("sonuclar"):
                continue
            kt.nokta(f"{ad} öncesi", self.durdurma)
            a = self.motor.yurut(self.motor.plan(ad, p, None, k.talep, self.ad, k.kimlik), baglam)
            k.adim_ekle(a)
            baglam["adimlar"].append(a)
            self._devam_kaydet(baglam, i + 1)
        if not adim:
            adim = {"durum": "basarili"}
        k.rapor = rapor.ozet_metni(baglam["adimlar"])
        k.yorum = hata_yorumu(self.model, k.talep, baglam["adimlar"], k.gerekce) if self.model else ""
        durumlar = [a["durum"] for a in baglam["adimlar"]]
        son = "bitti" if all(d == "basarili" for d in durumlar) else (
            "iptal" if "iptal" in durumlar else "basarisiz" if adim["durum"] == "basarisiz" else "kismi")
        if son == "bitti" and k.plan.get("eksik"):
            son = "kismi"
            k.rapor += (f"\n\nTalebin bu kısmı yapılmadı (Kalfa yalnız tek hazır beceri yürütür): {k.plan['eksik']}. "
                        "Kaptan ile deneyin ya da bu iş için beceri ekleyin.")
        if yasak_notu:
            k.rapor += "\n\n" + yasak_notu
        return self._bitir(son)

    def _yasak_ertele(self, adim):
        """Yasak penceredeki sunucular: politika 'bekle' ise iş o sunucular için pencere kapanınca bir kez çalışacak
        şekilde zamanlanır; 'sor' ise operatöre sorulacak bir zamanlanmış iş açılır; 'atla' ise yalnız raporlanır."""
        k = self.kayit
        k_plan = k.plan["ana"]
        yasak = adim["yasak"]
        sunucular = sorted(yasak)
        pen = self.motor._pencereler()
        pol = pen.varsayilan_politika()
        ozet = ", ".join(f"{s} ('{v['pencere']}', {v['bitis']} kapanır)" for s, v in sorted(yasak.items()))
        if pol == "atla" or self.zamanlayici is None:
            return (f"Yasak pencere: {ozet}. Bu sunucularda değiştiren iş başlamadı"
                    + (" (politika: atla)." if pol == "atla" else "; zamanlayıcı olmadığı için ertelenemedi."))
        an = pen.yasak_sonu(self.motor.envanter, sunucular) if pol == "bekle" else pen.saat()
        tanim = {"tur": "beceri", "beceri": k_plan["beceri"], "parametreler": k_plan["parametreler"],
                 "hedef_secici": {"ad": ",".join(sunucular)}, "bicim": k.plan.get("bicim"), "alici": k.plan.get("alici"),
                 "kimlik": k_plan.get("kimlik_calistirma"), "talep": k.talep}
        veren = on_onay_al(self.motor, k_plan, self.on_onay_veren)
        z = self.zamanlayici.ekle(f"{k.talep[:90]} (yasak pencere sonrası)", tanim,
                                  {"tur": "tek", "zaman": an.isoformat(timespec="minutes")}, "simdi", "hemen", pol,
                                  f"kalfa:{k.kimlik}", on_onay=veren,
                                  dondurulmus={"secici": {"ad": ",".join(sunucular)}, "sunucular": sunucular})
        k.ek.setdefault("ertelenen", []).append({"zamanlama": z["kimlik"], "sunucular": sunucular, "zaman": z["sonraki"]})
        k.olay("ertelendi", f"yasak pencere: {ozet} → zamanlanmış iş {z['kimlik']} ({z['sonraki']})")
        if pol == "sor":
            return (f"Yasak pencere: {ozet}. Bu sunucularda iş başlamadı; operatör kararı için zamanlanmış iş "
                    f"{z['kimlik']} açıldı (Zamanlanmış işler sayfasında sorulur).")
        return (f"Yasak pencere: {ozet}. Bu sunucularda iş başlamadı; pencere kapanınca ({z['sonraki']}) bir kez "
                f"çalışmak üzere ertelendi (zamanlanmış iş {z['kimlik']}).")

    def calistir(self, talep):
        self.planla(talep)
        if self.kayit.durum != "plan_hazir":
            return self.kayit
        return self.yurut()
