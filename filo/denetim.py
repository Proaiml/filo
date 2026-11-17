"""Eklemeli denetim izi.

Her karar ve eylem (talep, seçilen beceri ve sürümü, dondurulmuş hedef listesi, onaylayan, sonuç) bir JSON satırı
olarak `results/denetim.jsonl` dosyasına eklenir. Satırlar bir özet zinciriyle bağlıdır: her satır bir öncekinin
özetini `_onceki`, kendi özetini `_ozet` alanında taşır (alt çizgili alan adları zincire ayrılmıştır); araya satır sokmak, satır silmek ya da değiştirmek `dogrula()` ile görülür.

Kimlik bilgisi buraya girmez: adı parola, anahtar, token, secret gibi olan alanlar yazılmadan önce maskelenir.
"""
import datetime
import hashlib
import json
import re
import threading

from . import SONUC

GIZLI_ALAN = re.compile(r"(parola|sifre|şifre|password|passwd|secret|token|api[_-]?key|anahtar_degeri|authorization)",
                        re.I)
_KILIT = threading.Lock()


def temizle(deger):
    """Gizli adlı alanları maskeler (iç içe sözlük ve listelerde de)."""
    if isinstance(deger, dict):
        return {k: ("***" if GIZLI_ALAN.search(str(k)) else temizle(v)) for k, v in deger.items()}
    if isinstance(deger, list):
        return [temizle(x) for x in deger]
    return deger


class Denetim:
    def __init__(self, yol=None):
        self.yol = yol or (SONUC / "denetim.jsonl")

    def _son_ozet(self):
        if not self.yol.exists():
            return "0" * 16
        son = None
        with self.yol.open("rb") as f:
            for satir in f:
                if satir.strip():
                    son = satir
        if not son:
            return "0" * 16
        try:
            return json.loads(son)["_ozet"]
        except (ValueError, KeyError):
            return "bozuk"

    def yaz(self, tur, /, **alanlar):
        """Bir satır ekler ve satırı döndürür."""
        with _KILIT:
            self.yol.parent.mkdir(parents=True, exist_ok=True)
            onceki = self._son_ozet()
            alanlar = {(k if not k.startswith("_") else "alan" + k): v for k, v in alanlar.items()}
            govde = {"zaman": datetime.datetime.now().isoformat(timespec="seconds"), **temizle(alanlar), "tur": tur}
            metin = json.dumps(govde, ensure_ascii=False, sort_keys=True, default=str)
            ozet = hashlib.sha256((onceki + metin).encode("utf-8")).hexdigest()[:16]
            satir = {**govde, "_onceki": onceki, "_ozet": ozet}
            with self.yol.open("a", encoding="utf-8") as f:
                f.write(json.dumps(satir, ensure_ascii=False, default=str) + "\n")
            return satir

    def oku(self, limit=200, tur=None, is_kimligi=None):
        if not self.yol.exists():
            return []
        satirlar = []
        for s in self.yol.read_text(encoding="utf-8").splitlines():
            if not s.strip():
                continue
            try:
                r = json.loads(s)
            except ValueError:
                continue
            if tur and r.get("tur") != tur:
                continue
            if is_kimligi and r.get("is_kimligi") != is_kimligi:
                continue
            satirlar.append(r)
        return satirlar[-limit:][::-1]

    def dogrula(self):
        """(zincir_saglam, satir_sayisi, ilk_bozuk_satir)"""
        if not self.yol.exists():
            return True, 0, None
        onceki = "0" * 16
        n = 0
        for i, s in enumerate(self.yol.read_text(encoding="utf-8").splitlines(), 1):
            if not s.strip():
                continue
            n += 1
            try:
                r = json.loads(s)
            except ValueError:
                return False, n, i
            ozet = r.pop("_ozet", None)
            if r.pop("_onceki", None) != onceki:
                return False, n, i
            metin = json.dumps(r, ensure_ascii=False, sort_keys=True, default=str)
            if hashlib.sha256((onceki + metin).encode("utf-8")).hexdigest()[:16] != ozet:
                return False, n, i
            onceki = ozet
        return True, n, None


DENETIM = Denetim()
