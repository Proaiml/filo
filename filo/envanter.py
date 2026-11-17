"""Envanter ve hedef seçici.

Sunucu kaydı: ad, os (linux | windows), aile (debian | rhel | alpine | windows), adres, port, kullanıcı, kimlik (bir
kimlik profilinin ADI; anahtarın kendisi değil), taşıyıcı (ssh | winrm | oykunucu), gruplar, öznitelikler.

Hedef seçici bir sözlüktür:
    {"ad": "PA*", "grup": "web", "os": "linux", "aile": "alpine", "oznitelik": {"ortam": "test"}, "haric": ["PA-DB-01"]}
Metinden de kurulabilir: `PA* grup:web os:linux ortam=test !PA-DB-01` (boşlukla ayrılmış koşullar VE ile birleşir;
virgülle ayrılmış ad kalıpları VEYA ile).

Seçim iş başlamadan dondurulur (`dondur`): sonradan envanter değişse de iş aynı listeyle yürür, liste denetim izine
yazılır.
"""
import dataclasses
import datetime
import fnmatch
import hashlib
import json
import re

from . import AYARLAR

OS_DEGERLERI = ("linux", "windows")
AILELER = ("debian", "rhel", "alpine", "windows")


@dataclasses.dataclass
class Sunucu:
    ad: str
    os: str
    aile: str
    adres: str
    port: int = 22
    kullanici: str = "filo"
    kimlik: str = ""
    tasiyici: str = "ssh"
    gruplar: list = dataclasses.field(default_factory=list)
    oznitelikler: dict = dataclasses.field(default_factory=dict)
    konteyner: str = ""

    def ozet(self):
        return {"ad": self.ad, "os": self.os, "aile": self.aile, "adres": self.adres, "port": self.port,
                "tasiyici": self.tasiyici, "gruplar": self.gruplar, "oznitelikler": self.oznitelikler,
                "kimlik": self.kimlik}


class SeciciHatasi(ValueError):
    pass


def secici_coz(metin):
    """`PA* grup:web os:linux ortam=test !PA-DB-01` -> seçici sözlüğü."""
    secici = {}
    for parca in str(metin or "").split():
        if parca.startswith("!"):
            secici.setdefault("haric", []).append(parca[1:])
        elif ":" in parca:
            k, v = parca.split(":", 1)
            k = k.lower()
            if k not in ("grup", "os", "aile", "ad"):
                raise SeciciHatasi(f"bilinmeyen seçici anahtarı: {k}")
            secici[k] = v
        elif "=" in parca:
            k, v = parca.split("=", 1)
            secici.setdefault("oznitelik", {})[k] = v
        else:
            secici["ad"] = (secici["ad"] + "," + parca) if secici.get("ad") else parca
    return secici


EK_ENVANTER = AYARLAR / "envanter.ek.json"   # sonradan eklenen (yeni teslim edilen) sunucular; git dışında


class Envanter:
    def __init__(self, yol=None, sunucular=None):
        varsayilan = yol is None
        self.yol = yol or (AYARLAR / "envanter.json")
        if sunucular is None:
            veri = json.loads(self.yol.read_text(encoding="utf-8"))
            sunucular = list(veri["sunucular"])
            if varsayilan and EK_ENVANTER.exists():
                sunucular += json.loads(EK_ENVANTER.read_text(encoding="utf-8")).get("sunucular", [])
        self.sunucular = {}
        for s in sunucular:
            s = Sunucu(**s) if isinstance(s, dict) else s
            if s.os not in OS_DEGERLERI or s.aile not in AILELER:
                raise ValueError(f"{s.ad}: geçersiz os/aile")
            self.sunucular[s.ad.upper()] = s

    def __getitem__(self, ad):
        return self.sunucular[ad.upper()]

    def __contains__(self, ad):
        return str(ad).upper() in self.sunucular

    def gruplar(self):
        g = {}
        for s in self.sunucular.values():
            for x in s.gruplar:
                g.setdefault(x, []).append(s.ad)
        return g

    def oznitelik_degerleri(self):
        o = {}
        for s in self.sunucular.values():
            for k, v in s.oznitelikler.items():
                o.setdefault(k, set()).add(str(v))
        return {k: sorted(v) for k, v in o.items()}

    def sec(self, secici):
        """Seçiciye uyan sunucular (ada göre sıralı). Bilinmeyen grup ya da işletim sistemi hata verir: yanlış yazılmış
        bir grup adı sessizce boş liste dönmesin."""
        if isinstance(secici, str):
            secici = secici_coz(secici)
        secici = {k: v for k, v in (secici or {}).items() if v not in (None, "", [], {})}
        if not secici:
            raise SeciciHatasi("hedef seçici boş: en az bir koşul gerekli")
        bilinmeyen = set(secici) - {"ad", "grup", "os", "aile", "oznitelik", "haric"}
        if bilinmeyen:
            raise SeciciHatasi(f"bilinmeyen seçici alanı: {sorted(bilinmeyen)}")
        if secici.get("grup") and secici["grup"] not in self.gruplar():
            raise SeciciHatasi(f"böyle bir grup yok: {secici['grup']} (var olanlar: {sorted(self.gruplar())})")
        if secici.get("os") and secici["os"] not in OS_DEGERLERI:
            raise SeciciHatasi(f"geçersiz işletim sistemi: {secici['os']}")
        if secici.get("aile") and secici["aile"] not in AILELER:
            raise SeciciHatasi(f"geçersiz dağıtım ailesi: {secici['aile']}")
        kaliplar = [k.strip().upper() for k in re.split(r"[,\s]+", str(secici.get("ad", ""))) if k.strip()]
        haric = {h.upper() for h in secici.get("haric", [])}
        out = []
        for ad, s in sorted(self.sunucular.items()):
            if kaliplar and not any(fnmatch.fnmatchcase(ad, k) for k in kaliplar):
                continue
            if secici.get("grup") and secici["grup"] not in s.gruplar:
                continue
            if secici.get("os") and s.os != secici["os"]:
                continue
            if secici.get("aile") and s.aile != secici["aile"]:
                continue
            if any(str(s.oznitelikler.get(k)) != str(v) for k, v in (secici.get("oznitelik") or {}).items()):
                continue
            if any(fnmatch.fnmatchcase(ad, h) for h in haric):
                continue
            out.append(s)
        return out

    def dondur(self, secici):
        """Seçimi dondurur: iş bu listeyle yürür. Liste boşsa hata."""
        if isinstance(secici, str):
            secici = secici_coz(secici)
        secilen = self.sec(secici)
        if not secilen:
            raise SeciciHatasi(f"seçiciye uyan sunucu yok: {secici}")
        adlar = [s.ad for s in secilen]
        return {"secici": secici, "sunucular": adlar, "sayi": len(adlar),
                "zaman": datetime.datetime.now().isoformat(timespec="seconds"),
                "ozet": hashlib.sha256(",".join(adlar).encode()).hexdigest()[:12]}

    def liste(self):
        return [s.ozet() for _, s in sorted(self.sunucular.items())]
