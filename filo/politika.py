"""Politika: onay kapısı, kuru çalıştırma kararı.

    risk 0-1   doğrudan çalışır
    risk 2     önce kuru çalıştırma (sonucu plana yazılır), sonra çalışır
    risk 3-4   kuru çalıştırma + insan onayı. Onay yoksa iş `onay_bekliyor` durumunda kalır.

Onay kaynakları:
    etkilesimli    onay kaydı (results/onaylar.json) açılır; web arayüzündeki Onaylar sekmesi ya da
                   `python -m filo onay ver <kimlik>` ile verilir
    komut_satiri   operatör `--onayla` bayrağıyla aynı anda onay verdi; onaylayan olarak hesap adı yazılır
    bench          onayı senaryo tanımı verir: {"varsayilan": "onayla"|"reddet", "beceriler": {"ad": "reddet"}}
Her onay ve ret denetim izine yazılır.
"""
import datetime
import getpass
import json
import threading
import uuid

from . import SONUC
from .denetim import DENETIM

_KILIT = threading.Lock()


class Onaylar:
    def __init__(self, yol=None, denetim=DENETIM):
        self.yol = yol or (SONUC / "onaylar.json")
        self.denetim = denetim

    def _oku(self):
        if not self.yol.exists():
            return []
        try:
            return json.loads(self.yol.read_text(encoding="utf-8"))
        except ValueError:
            return []

    def _yaz(self, kayitlar):
        self.yol.parent.mkdir(parents=True, exist_ok=True)
        self.yol.write_text(json.dumps(kayitlar, ensure_ascii=False, indent=1, default=str), encoding="utf-8")

    def talep_et(self, plan, kuru=None):
        with _KILIT:
            kayitlar = self._oku()
            k = {"kimlik": uuid.uuid4().hex[:8], "durum": "bekliyor",
                 "zaman": datetime.datetime.now().isoformat(timespec="seconds"),
                 "is_kimligi": plan.get("is_kimligi"), "beceri": plan["beceri"], "surum": plan["surum"],
                 "risk": plan["risk"], "risk_neden": plan.get("risk_neden"), "parametreler": plan["parametreler"],
                 "hedefler": (plan.get("hedef") or {}).get("sunucular", []), "kuru": kuru or [],
                 "talep": plan.get("talep", ""), "ajan": plan.get("ajan", "")}
            kayitlar.append(k)
            self._yaz(kayitlar)
        self.denetim.yaz("onay_istendi", is_kimligi=k["is_kimligi"], onay=k["kimlik"], beceri=k["beceri"],
                         surum=k["surum"], risk=k["risk"], hedefler=k["hedefler"])
        return k

    def karar(self, kimlik, onayla, kim, not_=""):
        with _KILIT:
            kayitlar = self._oku()
            for k in kayitlar:
                if k["kimlik"] == kimlik:
                    if k["durum"] != "bekliyor":
                        return k
                    k.update(durum="onaylandi" if onayla else "reddedildi", karar_veren=kim, not_=not_,
                             karar_zamani=datetime.datetime.now().isoformat(timespec="seconds"))
                    self._yaz(kayitlar)
                    break
            else:
                return None
        self.denetim.yaz("onay_verildi" if onayla else "onay_reddedildi", is_kimligi=k["is_kimligi"], onay=kimlik,
                         beceri=k["beceri"], onaylayan=kim, not_=not_)
        return k

    def getir(self, kimlik):
        return next((k for k in self._oku() if k["kimlik"] == kimlik), None)

    def liste(self, durum=None):
        return [k for k in self._oku() if durum is None or k["durum"] == durum][::-1]


class Politika:
    def __init__(self, kip="etkilesimli", bench_kurali=None, onaylar=None, denetim=DENETIM, kim=None):
        if kip not in ("etkilesimli", "komut_satiri", "bench"):
            raise ValueError("kip etkilesimli / komut_satiri / bench olmalı")
        self.kip, self.bench_kurali, self.denetim = kip, bench_kurali or {}, denetim
        self.onaylar = onaylar or Onaylar(denetim=denetim)
        self.kim = kim or (f"komut_satiri:{getpass.getuser()}" if kip == "komut_satiri" else None)

    @staticmethod
    def degerlendir(risk, tanim=None):
        return {"kuru_once": risk >= 2 and bool((tanim or {}).get("kuru")), "onay_gerekli": risk >= 3}

    def onay(self, plan, kuru=None):
        """('onaylandi' | 'reddedildi' | 'bekliyor', onaylayan, onay_kimligi)"""
        if not plan.get("onay_gerekli"):
            return "onaylandi", "gerekmedi", None
        oo = plan.get("on_onay")
        if oo and oo.get("veren") and oo.get("tanim_surumu"):
            # Zamanlanmış işin önceden onayı: zamanlayıcı onayı yalnız aynı tanım sürümü ve özeti için geçirir (tanım
            # değişince düşer). Kim, ne zaman, hangi sürüm için verdiği denetim izine yazılır.
            kim = f"zamanlama:{oo['veren']}"
            self.denetim.yaz("onay_verildi", is_kimligi=plan.get("is_kimligi"), beceri=plan["beceri"], surum=plan["surum"],
                             onaylayan=kim, on_onay=True, onay_zamani=oo.get("zaman"), tanim_surumu=oo["tanim_surumu"],
                             zamanlama=oo.get("zamanlama"), hedefler=(plan.get("hedef") or {}).get("sunucular", []))
            return "onaylandi", kim, None
        if plan.get("onay_kimligi"):
            k = self.onaylar.getir(plan["onay_kimligi"])
            if k and k["durum"] != "bekliyor":
                gecerli = k["beceri"] == plan["beceri"] and k["surum"] == plan["surum"] and \
                    k["hedefler"] == (plan.get("hedef") or {}).get("sunucular", [])
                if k["durum"] == "onaylandi" and not gecerli:
                    return "reddedildi", "onay başka bir plana ait (beceri, sürüm ya da hedef değişmiş)", k["kimlik"]
                return k["durum"], k.get("karar_veren"), k["kimlik"]
            if k:
                return "bekliyor", None, k["kimlik"]
        if self.kip == "bench":
            kural = self.bench_kurali.get("beceriler", {}).get(plan["beceri"], self.bench_kurali.get("varsayilan", "reddet"))
            durum = "onaylandi" if kural == "onayla" else "reddedildi"
            self.denetim.yaz("onay_verildi" if durum == "onaylandi" else "onay_reddedildi",
                             is_kimligi=plan.get("is_kimligi"), beceri=plan["beceri"], onaylayan="senaryo",
                             hedefler=(plan.get("hedef") or {}).get("sunucular", []))
            return durum, "senaryo", None
        if self.kip == "komut_satiri":
            self.denetim.yaz("onay_verildi", is_kimligi=plan.get("is_kimligi"), beceri=plan["beceri"],
                             surum=plan["surum"], onaylayan=self.kim,
                             hedefler=(plan.get("hedef") or {}).get("sunucular", []))
            return "onaylandi", self.kim, None
        k = self.onaylar.talep_et(plan, kuru)
        return "bekliyor", None, k["kimlik"]
