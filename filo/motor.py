"""Beceri motoru: plan -> (kuru çalıştırma) -> onay -> yürütme -> şema denetimi -> sonuç. Ajanlar ve komut satırı
aynı motoru kullanır; hiçbir yol motoru atlayıp sunucuya komut gönderemez.

Plan iş başlamadan dondurulur: beceri adı ve sürümü, şemadan geçmiş parametreler, dondurulmuş hedef listesi, etkin risk,
onay gereği. Yürütme anında becerinin sürümü değişmişse plan geçersizdir (yeniden planlanmalı).

Adım sonucu:
    {"beceri", "surum", "is_kimligi", "durum": basarili|kismi|basarisiz|onay_bekliyor|reddedildi|iptal,
     "sonuclar": [sunucu başına tek şemalı sonuç + "veri" + varsa "sema_hatasi"], "ozet", "belge"?, "aciklama"}
"""
import base64
import datetime
import hashlib
import json
import re
import uuid

from . import rapor
from .beceri import (DOSYALAR, SemaHatasi, alintila, cikti_dogrula, doldur, komut_sec, parametre_dogrula)
from .denetim import DENETIM
from .yurutme import ozetle


def _simdi():
    return datetime.datetime.now().isoformat(timespec="seconds")


def adim_durumu(sonuclar):
    if not sonuclar:
        return "basarisiz"
    oz = ozetle(sonuclar)
    if oz["iptal"] and not oz["basarili"]:
        return "iptal"
    if oz["basarili"] == oz["toplam"]:
        return "basarili"
    return "kismi" if oz["basarili"] else "basarisiz"


class PlanHatasi(ValueError):
    pass


class BeceriMotoru:
    def __init__(self, katalog, envanter, yurutucu, politika, denetim=DENETIM, posta_ayari=None, yeniden_deneme=2,
                 pencereler=None):
        self.katalog, self.envanter, self.yurutucu, self.politika = katalog, envanter, yurutucu, politika
        self.denetim, self.posta_ayari, self.yeniden_deneme = denetim, posta_ayari, yeniden_deneme
        self.pencereler = pencereler          # None: ayarlar/pencereler.json, gerçek saat (ilk kullanımda yüklenir)

    def _pencereler(self):
        if self.pencereler is None:
            from .zamanlayici import Pencereler
            self.pencereler = Pencereler()
        return self.pencereler

    def _yasak_ayir(self, plan):
        """Yasak (blackout) pencere: sunucuyu değiştiren adım (risk ≥ 2) yasaktaki sunucuda başlamaz. Dönüş:
        (yasaktakiler çıkarılmış plan, {sunucu: {"pencere", "bitis"}}). Operatör istisnası plana kodla yazılır."""
        t = self.katalog[plan["beceri"]]
        if t["tur"] == "yerel" or plan["risk"] < 2 or not plan.get("hedef") or plan.get("yasak_istisnasi"):
            if plan.get("yasak_istisnasi"):
                self.denetim.yaz("yasak_istisnasi", is_kimligi=plan["is_kimligi"], beceri=plan["beceri"],
                                 istisna=plan["yasak_istisnasi"])
            return plan, {}
        yasak = self._pencereler().yasakta(self.envanter, plan["hedef"]["sunucular"])
        if not yasak:
            return plan, {}
        self.denetim.yaz("yasak_pencere", is_kimligi=plan["is_kimligi"], beceri=plan["beceri"], risk=plan["risk"],
                         yasak=yasak)
        kalan = [h for h in plan["hedef"]["sunucular"] if h.upper() not in yasak]
        return {**plan, "hedef": {**plan["hedef"], "sunucular": kalan}}, yasak

    # ------------------------------------------------------------ plan
    def plan(self, ad, parametreler=None, hedef=None, talep="", ajan="", is_kimligi=None, kimlik=None):
        """`kimlik`: çalıştırma kimliği (None: becerinin varsayılanı, o da yoksa bağlantı kullanıcısı)."""
        if ad not in self.katalog:
            raise PlanHatasi(f"katalogda böyle bir beceri yok: {ad}")
        t = self.katalog[ad]
        p = parametre_dogrula(t.get("girdi") or {}, parametreler)
        dondurulmus = None
        if t["tur"] != "yerel":
            if hedef is None:
                raise PlanHatasi("uzak beceri için hedef gerekli")
            dondurulmus = hedef if isinstance(hedef, dict) and "sunucular" in hedef else self.envanter.dondur(hedef)
            bilinmeyen = [a for a in dondurulmus["sunucular"] if a not in self.envanter]
            if bilinmeyen:
                raise PlanHatasi(f"envanterde olmayan sunucu: {bilinmeyen}")
        risk, neden = self.katalog.etkin_risk(t, p)
        karar = self.politika.degerlendir(risk, t)
        kimlik = kimlik if kimlik not in (None, "") else t.get("calistirma_kimligi")
        kimlik = self.kimlik_denetle(kimlik, (dondurulmus or {}).get("sunucular", []), t)
        plan = {"is_kimligi": is_kimligi or uuid.uuid4().hex[:10], "beceri": ad, "surum": t["surum"],
                "baslik": t["baslik"], "tur": t["tur"], "parametreler": p, "hedef": dondurulmus, "risk": risk,
                "risk_neden": neden, "onay_gerekli": karar["onay_gerekli"], "kuru_once": karar["kuru_once"],
                "zaman_asimi": int(t.get("zaman_asimi", 60)), "talep": talep, "ajan": ajan,
                "geri_al": t.get("geri_al"), "zaman": _simdi()}
        if kimlik:
            plan["kimlik_calistirma"] = kimlik
        self.denetim.yaz("plan", is_kimligi=plan["is_kimligi"], beceri=ad, surum=t["surum"], parametreler=p,
                         hedef=dondurulmus, risk=risk, risk_neden=neden, onay_gerekli=plan["onay_gerekli"],
                         ajan=ajan, talep=talep[:500], calistirma_kimligi=kimlik or "baglanti")
        return plan

    # ------------------------------------------------------------ çalıştırma kimliği (C1)
    def kimlik_denetle(self, kimlik, sunucular, tanim=None):
        """Çalıştırma kimliğini denetler: None/"baglanti" → None (bağlantı kullanıcısı). Başka kimlik her hedef sunucuda
        izinli olmalı (ayarlar/calistirma_kimlikleri.json); izinli değilse PlanHatasi (hiçbir şey çalışmaz)."""
        from .kimlik import KimlikHatasi, gecerli_ad, izinli_kimlikler
        if kimlik in (None, "", "baglanti"):
            return None
        kimlik = str(kimlik).strip()
        if not gecerli_ad(kimlik):
            raise PlanHatasi(f"geçersiz çalıştırma kimliği: {kimlik!r} (kullanıcı adı, 'root' ya da 'baglanti')")
        if tanim is not None and tanim["tur"] not in ("uzak", "zincir"):
            return None        # yerel ve yönetim becerileri (ajan kurulumu, e-posta) sunucuda betik çalıştırmaz
        red = {}
        for ad in sunucular:
            s = self.envanter[ad]
            try:
                izinli = izinli_kimlikler(s)
            except KimlikHatasi as e:
                raise PlanHatasi(str(e)) from None
            if all(kimlik != s.kullanici and kimlik != x for x in izinli):
                red[ad] = izinli
        if red:
            raise PlanHatasi(f"çalıştırma kimliği '{kimlik}' şu sunucularda izinli değil: "
                             + "; ".join(f"{a} (izinli: {', '.join(v)})" for a, v in red.items()))
        return kimlik

    # ------------------------------------------------------------ betik üretimi
    def _turet(self, t, p):
        """Şemadan geçmiş parametrelere türetilmiş değerler ekler (yalnız kod üretir; model veremez)."""
        p = dict(p)
        dosya_alani = next((k for k, v in (t.get("girdi") or {}).items() if v.get("kaynak") == "dosyalar"), None)
        if dosya_alani and p.get(dosya_alani):
            veri = (DOSYALAR / p[dosya_alani]).read_bytes()
            p["_icerik"] = base64.b64encode(veri).decode()
            p["_ozet"] = hashlib.sha256(veri).hexdigest()
        return p

    def betik_fn(self, t, p, kip="komut", kimlik=None):
        from .kimlik import sar
        tablo = t.get(kip) or {}
        tam = self._turet(t, p)

        def ham(sunucu):
            sablon = komut_sec(tablo, sunucu)
            if sablon is None:
                return None
            if sablon == "@betik":
                if sunucu.os != "linux":
                    return None
                arg = alintila(tam.get("argumanlar") or [], "linux")
                return f"set -- {arg}\n" + self.katalog.betik_oku(tam["betik"])
            return doldur(sablon, tam, sunucu.os)

        def fn(sunucu):
            b = ham(sunucu)
            return b if b is None or not kimlik else sar(b, kimlik, sunucu)
        return fn

    def cikti_semasi(self, t, p):
        sema = t.get("cikti") or {"bicim": "ham"}
        if sema.get("bicim") == "betik":
            return self.katalog.betik_meta(p["betik"]).get("cikti") or {"bicim": "ham"}
        return sema

    # ------------------------------------------------------------ kuru çalıştırma
    def kuru_calistir(self, plan, gozlemci=None):
        t = self.katalog[plan["beceri"]]
        if t["tur"] == "yonetim" and t.get("kuru"):
            sonuc = self._yonetim_yelpaze(t, plan, gozlemci, kuru=True)
            self.denetim.yaz("kuru_calistirma", is_kimligi=plan["is_kimligi"], beceri=plan["beceri"],
                             sunucular={r["sunucu"]: r["durum"] for r in sonuc})
            return sonuc
        if t["tur"] != "uzak" or not t.get("kuru"):
            return []
        sonuc = self.yurutucu.yelpaze(plan["hedef"]["sunucular"], self.betik_fn(t, plan["parametreler"], "kuru", plan.get("kimlik_calistirma")),
                                      min(plan["zaman_asimi"], 120), yeniden_deneme=0, gozlemci=gozlemci,
                                      is_kimligi=plan["is_kimligi"], denetle=False)
        self.denetim.yaz("kuru_calistirma", is_kimligi=plan["is_kimligi"], beceri=plan["beceri"],
                         sunucular={r["sunucu"]: r["durum"] for r in sonuc})
        return sonuc

    # ------------------------------------------------------------ yürütme
    def yurut(self, plan, baglam=None, gozlemci=None, onay_atla=False):
        """Planı yürütür. Onay gerekiyorsa politikaya sorar; onay yoksa `onay_bekliyor` döner ve hiçbir şey çalışmaz."""
        t = self.katalog[plan["beceri"]] if plan["beceri"] in self.katalog else None
        if t is None or t["surum"] != plan["surum"]:
            raise PlanHatasi(f"{plan['beceri']}: plan v{plan['surum']} için yapıldı, katalogdaki sürüm "
                             f"{t['surum'] if t else 'yok'}; yeniden planlayın")
        baglam = baglam if baglam is not None else {}
        adim = {"beceri": plan["beceri"], "surum": plan["surum"], "is_kimligi": plan["is_kimligi"],
                "parametreler": plan["parametreler"], "hedef": (plan.get("hedef") or {}).get("sunucular"),
                "risk": plan["risk"], "baslangic": _simdi(), "sonuclar": [], "kuru": []}
        if plan.get("kimlik_calistirma"):
            adim["kimlik_calistirma"] = plan["kimlik_calistirma"]
        plan, yasak = self._yasak_ayir(plan)
        engellenen = []
        if yasak:
            from .yurutme import bos_sonuc
            adim["yasak"] = yasak
            engellenen = [{**bos_sonuc(h, "iptal", f"yasak pencere '{v['pencere']}' ({v['bitis']} kapanır): sunucuyu "
                                                   "değiştiren iş başlamadı"), "yasak": v} for h, v in yasak.items()]
            if not plan["hedef"]["sunucular"]:
                adim["sonuclar"], adim["durum"] = engellenen, "iptal"
                adim["aciklama"] = "bütün hedefler yasak pencerede; hiçbir şey çalışmadı"
                return self._bitir(adim)
        sonuc = self._yurut_ic(t, plan, adim, baglam, gozlemci, onay_atla)
        if engellenen and sonuc.get("durum") not in ("onay_bekliyor", "reddedildi"):
            sira = {h: i for i, h in enumerate(adim["hedef"] or [])}
            sonuc["sonuclar"] = sorted(sonuc.get("sonuclar", []) + engellenen, key=lambda r: sira.get(r["sunucu"], 999))
            sonuc["ozet"] = ozetle(sonuc["sonuclar"])
            sonuc["durum"] = adim_durumu(sonuc["sonuclar"])
        return sonuc

    def _yurut_ic(self, t, plan, adim, baglam, gozlemci, onay_atla):
        if plan["kuru_once"] and not plan.get("kuru_yapildi"):
            adim["kuru"] = self.kuru_calistir(plan, gozlemci)
        if plan["onay_gerekli"] and not onay_atla:
            durum, kim, onay_kimligi = self.politika.onay(plan, adim["kuru"])
            adim["onay"] = {"durum": durum, "onaylayan": kim, "kimlik": onay_kimligi}
            if durum != "onaylandi":
                adim["durum"] = "onay_bekliyor" if durum == "bekliyor" else "reddedildi"
                adim["aciklama"] = "insan onayı bekleniyor" if durum == "bekliyor" else f"onay verilmedi ({kim})"
                return self._bitir(adim)
        try:
            if t["tur"] == "uzak":
                self._uzak(t, plan, adim, gozlemci)
            elif t["tur"] == "yonetim":
                self._yonetim(t, plan, adim, gozlemci)
            elif t["tur"] == "yerel":
                self._yerel(t, plan, adim, baglam)
            else:
                self._zincir(t, plan, adim, baglam, gozlemci)
        except (SemaHatasi, PlanHatasi, rapor.PostaReddi, OSError) as e:
            adim["durum"], adim["aciklama"] = "basarisiz", str(e)
            return self._bitir(adim)
        baglam["son_adim"] = adim
        if adim.get("belge"):
            baglam["belge"] = adim["belge"]
        if t["tur"] != "yerel":
            baglam["son_uzak_adim"] = adim
        return self._bitir(adim)

    def _bitir(self, adim):
        adim["bitis"] = _simdi()
        if adim.get("sonuclar") and "ozet" not in adim:
            adim["ozet"] = ozetle(adim["sonuclar"])
        self.denetim.yaz("adim", is_kimligi=adim["is_kimligi"], beceri=adim["beceri"], surum=adim["surum"],
                         durum=adim["durum"], ozet=adim.get("ozet"), aciklama=adim.get("aciklama"),
                         onay=adim.get("onay"),
                         sema_hatalari={r["sunucu"]: r["sema_hatasi"] for r in adim.get("sonuclar", []) if r.get("sema_hatasi")})
        return adim

    def _uzak(self, t, plan, adim, gozlemci):
        p = plan["parametreler"]
        sema = self.cikti_semasi(t, p)
        tam = self._turet(t, p)
        sonuclar = self.yurutucu.is_yurut(plan["hedef"]["sunucular"], self.betik_fn(t, p, kimlik=plan.get("kimlik_calistirma")), plan["zaman_asimi"],
                                          self.yeniden_deneme, gozlemci, plan["is_kimligi"])
        for r in sonuclar:
            if r["durum"] == "basarili":
                veri, hata = cikti_dogrula(sema, r["stdout"], tam)
                r["veri"] = veri
                if hata:
                    r["sema_hatasi"] = hata
                    r["durum"] = "hatali"
                    r["neden"] = f"çıktı şemaya uymuyor: {hata}"
            elif r["durum"] == "hatali" and r.get("stdout"):
                r["veri"] = cikti_dogrula(sema, r["stdout"], tam)[0]
        adim["sonuclar"] = sonuclar
        adim["ozet"] = ozetle(sonuclar)
        adim["durum"] = adim_durumu(sonuclar)

    def _yonetim_yelpaze(self, t, plan, gozlemci, kuru=False):
        """Yönetim becerisi: koddaki işleyici her sunucuda (paralel, en çok yürütücünün eşzamanlılığı kadar) çalışır."""
        import concurrent.futures
        from .ajan_yonetimi import ISLEYICILER
        fn = ISLEYICILER[t["islem"]]
        adlar = plan["hedef"]["sunucular"]
        durdurma = self.yurutucu.durdurma

        def bir(ad):
            if durdurma.basili():
                from .yurutme import bos_sonuc
                return bos_sonuc(ad, "iptal", "durdurma düğmesi basılı")
            if gozlemci:
                gozlemci({"olay": "basladi", "sunucu": ad, "deneme": 1})
            r = fn(self.envanter[ad], plan["parametreler"], kuru, durdurma, motor=self)
            if gozlemci:
                gozlemci({"olay": "sunucu", "sonuc": r})
            return r
        with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, min(self.yurutucu.eszamanli, len(adlar)))) as ex:
            return list(ex.map(bir, adlar))

    def _yonetim(self, t, plan, adim, gozlemci):
        sema = t.get("cikti") or {"bicim": "ham"}
        sonuclar = self._yonetim_yelpaze(t, plan, gozlemci)
        for r in sonuclar:
            veri, hata = cikti_dogrula(sema, r.get("stdout") or "", plan["parametreler"])
            r["veri"] = veri
            if r["durum"] == "basarili" and hata:
                r.update(durum="hatali", sema_hatasi=hata, neden=f"çıktı şemaya uymuyor: {hata}")
        self.denetim.yaz("yurutme", is_kimligi=plan["is_kimligi"], zaman_asimi=plan["zaman_asimi"],
                         ozet=ozetle(sonuclar), sunucular={r["sunucu"]: {"durum": r["durum"], "tasiyici": r.get("tasiyici"),
                                                                         "neden": (r.get("neden") or "")[:200]}
                                                           for r in sonuclar})
        adim["sonuclar"] = sonuclar
        adim["ozet"] = ozetle(sonuclar)
        adim["durum"] = adim_durumu(sonuclar)

    def _yerel(self, t, plan, adim, baglam):
        p = plan["parametreler"]
        if t["ad"] == "sonucu_donustur":
            kaynak = baglam.get("son_uzak_adim")
            if not kaynak:
                raise PlanHatasi("dönüştürülecek bir önceki sunucu adımı yok")
            ad, icerik, mime = rapor.donustur(kaynak, p["bicim"])
            adim["belge"] = {"ad": ad, "icerik": icerik, "mime": mime, "bicim": p["bicim"], "kaynak": kaynak["beceri"],
                             "sunucu_sayisi": len(kaynak.get("sonuclar", []))}
            adim["durum"], adim["aciklama"] = "basarili", f"{ad} ({len(icerik)} bayt)"
            return
        if t["ad"] == "eposta_gonder":
            belge = baglam.get("belge")
            adimlar = baglam.get("adimlar") or ([baglam["son_adim"]] if baglam.get("son_adim") else [])
            govde = (f"Filo iş raporu\nİş: {plan['is_kimligi']}\nTalep: {plan.get('talep') or '-'}\n\n"
                     + (rapor.ozet_metni(adimlar) or "(önceki adım yok)") + "\n")
            ekler = [(belge["ad"], belge["icerik"], belge["mime"])] if belge else []
            kaynak = baglam.get("son_uzak_adim")
            # Ek yoksa sunucu başına sonuç gövdeye girer (rapor yalnız sayılardan ibaret kalmasın). Çok adımlı akışta
            # (paralel kollar, alt akış) her sunucu adımının sonucu yazılır; eskiden yalnız sonuncusu giriyordu.
            uzaklar = [a for a in adimlar if a.get("sonuclar") and a.get("beceri") not in ("sonucu_donustur", "eposta_gonder")]
            if kaynak and kaynak.get("sonuclar") and not any(a is kaynak for a in uzaklar):
                uzaklar.append(kaynak)
            if not belge and uzaklar:
                satir = []
                for a in uzaklar[-6:]:
                    if len(uzaklar) > 1:
                        satir.append(f"# {a.get('beceri')}")
                    for r in a["sonuclar"]:
                        v = r.get("veri")
                        icerik = (json.dumps(v, ensure_ascii=False) if v not in (None, "") else
                                  (r.get("stdout") or r.get("neden") or r.get("stderr") or "").strip())
                        satir.append(f"{r['sunucu']} [{r['durum']}]: {icerik[:1500]}")
                govde += "\nSonuçlar:\n" + "\n".join(satir)[:12000] + "\n"
            mid = rapor.eposta_gonder(p["alici"], p["konu"], govde, ekler, self.posta_ayari)
            adim["durum"] = "basarili"
            adim["aciklama"] = f"{p['alici']} adresine gönderildi" + (f", ek: {belge['ad']}" if belge else "")
            adim["veri"] = {"alici": p["alici"], "ileti": mid, "ek": belge["ad"] if belge else None}
            return
        raise PlanHatasi(f"yerel beceri tanımsız: {t['ad']}")

    def _zincir(self, t, plan, adim, baglam, gozlemci):
        """Zincirin adımları sırayla yürür; bir adımda başarısız olan sunucu sonraki adımlara girmez ve raporlanır."""
        hedefler = list(plan["hedef"]["sunucular"])
        dusenler = {}
        alt = []
        for i, a in enumerate(t["adimlar"], 1):
            if not hedefler:
                break
            dondurulmus = {**plan["hedef"], "sunucular": hedefler}
            # "{ad}" biçimindeki adım parametresi zincirin kendi girdisinden doldurulur (beceriye dönüştürülmüş akışlar)
            ap = {k: (plan["parametreler"][v[1:-1]] if isinstance(v, str) and re.fullmatch(r"\{[a-z_][a-z0-9_]*\}", v)
                      and v[1:-1] in plan["parametreler"] else v) for k, v in (a.get("parametre") or {}).items()}
            p_alt = self.plan(a["beceri"], ap, dondurulmus, plan.get("talep", ""),
                              plan.get("ajan", ""), plan["is_kimligi"], kimlik=plan.get("kimlik_calistirma"))
            if gozlemci:
                gozlemci({"olay": "alt_adim", "sira": i, "beceri": a["beceri"]})
            # Zincirin onayı alt adımları kapsar (zincirin etkin riski alt adımların en büyüğüdür).
            sonuc = self.yurut(p_alt, baglam, gozlemci, onay_atla=True)
            alt.append(sonuc)
            for r in sonuc.get("sonuclar", []):
                if r["durum"] != "basarili":
                    dusenler.setdefault(r["sunucu"], {**r, "dustugu_adim": a["beceri"]})
            hedefler = [h for h in hedefler if h not in dusenler]
        adim["alt_adimlar"] = alt
        son = {h: {"sunucu": h, "durum": "basarili", "cikis_kodu": 0, "stdout": "", "stderr": "", "sure": 0,
                   "kesildi": False, "deneme": 1, "oykunme": False, "tasiyici": "ssh", "neden": ""} for h in hedefler}
        son.update({h: {**r, "neden": f"{r['dustugu_adim']}: {r.get('neden') or r.get('stderr', '')[:200]}"}
                    for h, r in dusenler.items()})
        for h, r in son.items():   # sunucu başına her alt adımın durumu: rapor zincirin tamamını gösterir
            r["veri"] = {a["beceri"]: next((x["durum"] for x in a.get("sonuclar", []) if x["sunucu"] == h), "girmedi")
                         for a in alt}
        adim["sonuclar"] = [son[h] for h in plan["hedef"]["sunucular"] if h in son]
        adim["ozet"] = ozetle(adim["sonuclar"])
        adim["durum"] = adim_durumu(adim["sonuclar"])

    # ------------------------------------------------------------ geri alma
    def geri_al(self, plan, gozlemci=None, sunucular=None):
        t = self.katalog[plan["beceri"]]
        ga = t.get("geri_al") or {}
        if not ga or "geri_alinamaz" in ga:
            return {"durum": "geri_alinamaz", "aciklama": ga.get("geri_alinamaz", "geri alma tanımı yok")}
        hedef = sunucular or plan["hedef"]["sunucular"]
        if ga.get("beceri"):          # geri alma başka bir becerinin işidir (ör. ajan_kur -> ajan_kaldir)
            p = self.plan(ga["beceri"], ga.get("parametre") or {}, {**plan["hedef"], "sunucular": hedef},
                          plan.get("talep", ""), plan.get("ajan", ""), plan["is_kimligi"])
            a = self.yurut(p, {}, gozlemci, onay_atla=True)
            self.denetim.yaz("geri_alma", is_kimligi=plan["is_kimligi"], beceri=plan["beceri"], yontem=ga["beceri"],
                             sunucular={r["sunucu"]: r["durum"] for r in a.get("sonuclar", [])})
            return {"durum": a["durum"], "sonuclar": a.get("sonuclar", []), "ozet": a.get("ozet")}
        sonuc = self.yurutucu.is_yurut(hedef, self.betik_fn(t, plan["parametreler"], "geri_al", plan.get("kimlik_calistirma")),
                                       plan["zaman_asimi"], 1, gozlemci, plan["is_kimligi"])
        self.denetim.yaz("geri_alma", is_kimligi=plan["is_kimligi"], beceri=plan["beceri"],
                         sunucular={r["sunucu"]: r["durum"] for r in sonuc})
        return {"durum": adim_durumu(sonuc), "sonuclar": sonuc, "ozet": ozetle(sonuc)}
