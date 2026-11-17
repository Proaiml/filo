"""Model kapısı: bağlantı profilleri, sınama, modelleri listeleme, JSON onarım döngüsü.

Bağlantılar `ayarlar/baglantilar.json` içindedir:
    {"ad": "yerel-qwen", "tur": "ollama", "adres": "http://127.0.0.1:11434", "model": "qwen3:8b", "num_ctx": 16384}
    {"ad": "lm-studio", "tur": "openai-uyumlu", "adres": "http://127.0.0.1:1234/v1", "model": "..."}
    {"ad": "claude", "tur": "anthropic", "model": "<kullanıcının verdiği model kimliği>", "anahtar_ortam": "ANTHROPIC_API_KEY"}
Türler: ollama, openai-uyumlu, anthropic, openai, gemini, agy.

Anahtar iki yerden birinde durur: bağlantının `anahtar_ortam` alanında adı yazan ortam değişkeni ya da git dışındaki
`ayarlar/gizli.json` ({"<bağlantı adı>": {"anahtar": "..."}}). Anahtar modele, kayıtlara, denetim izine ve arayüze
geri dönmez; `ozet()` yalnız `anahtar_var: true/false` söyler.

Yerel model kuralları (makine sınırı): düşünme kapalı, num_ctx 16384, aynı anda tek model (başka yüklü model
boşaltılır), çağrıdan önce ısı bekçisinin bayrağına bakılır (results/durum/BEKLE varken beklenir, DUR varken durulur).
"""
import json
import os
import pathlib
import re
import subprocess
import tempfile
import time
import urllib.error
import urllib.request

from . import AYARLAR, SONUC

TURLER = ("ollama", "openai-uyumlu", "anthropic", "openai", "gemini", "agy")
VARSAYILAN_ADRES = {"ollama": "http://127.0.0.1:11434", "openai-uyumlu": "http://127.0.0.1:1234/v1",
                    "anthropic": "https://api.anthropic.com", "openai": "https://api.openai.com/v1",
                    "gemini": "https://generativelanguage.googleapis.com/v1beta/openai", "agy": ""}
VARSAYILAN_ORTAM = {"anthropic": "ANTHROPIC_API_KEY", "openai": "OPENAI_API_KEY", "gemini": "GEMINI_API_KEY"}
YARDIM = {
    "ollama": "Ollama bu makinede çalışır (ollama serve). Adres genelde http://127.0.0.1:11434. Model adı `ollama list` "
              "çıktısındaki gibi yazılır (ör. qwen3:8b). Anahtar gerekmez. Filo düşünmeyi kapatır, bağlamı 16384 ile "
              "sınırlar ve aynı anda tek model yükler.",
    "openai-uyumlu": "OpenAI uyumlu yerel sunucu. Base URL örnekleri: LM Studio http://127.0.0.1:1234/v1, llama.cpp "
                     "(llama-server) http://127.0.0.1:8080/v1, vLLM http://127.0.0.1:8000/v1. Model adı sunucunun "
                     "/v1/models listesindeki kimliktir. Anahtar istemeyen sunucularda anahtar alanını boş bırakın.",
    "anthropic": "Anthropic Messages API (https://api.anthropic.com/v1/messages). Model kimliğini Anthropic konsolundan "
                 "ya da 'Modelleri listele' düğmesinden alın. Anahtar: ANTHROPIC_API_KEY ortam değişkeni ya da bu "
                 "formdan girilip git dışındaki ayarlar/gizli.json dosyasına yazılır; arayüzde geri gösterilmez.",
    "openai": "OpenAI API (https://api.openai.com/v1). Anahtar: OPENAI_API_KEY ortam değişkeni ya da bu form "
              "(ayarlar/gizli.json, git dışında). Model kimliğini 'Modelleri listele' ile görün.",
    "gemini": "Google Gemini, OpenAI uyumlu ucu (https://generativelanguage.googleapis.com/v1beta/openai). Anahtar: "
              "GEMINI_API_KEY ortam değişkeni ya da bu form (ayarlar/gizli.json, git dışında).",
    "agy": "Antigravity komut satırı aracı (`agy`), bu makinede API anahtarı olmayan modeller için. Model kimliği "
           "`agy models` çıktısındandır. Adres ve anahtar gerekmez.",
}


class BaglantiHatasi(Exception):
    pass


# ---------------------------------------------------------------- ayar dosyaları
def _oku(yol, bos):
    try:
        return json.loads(yol.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return bos


class Baglantilar:
    def __init__(self, yol=None, gizli=None):
        self.yol = yol or (AYARLAR / "baglantilar.json")
        self.gizli_yol = gizli or (AYARLAR / "gizli.json")

    def hepsi(self):
        return _oku(self.yol, {"baglantilar": []}).get("baglantilar", [])

    def getir(self, ad):
        b = next((x for x in self.hepsi() if x["ad"] == ad), None)
        if b is None:
            raise BaglantiHatasi(f"böyle bir bağlantı yok: {ad}")
        return b

    def varsayilan(self):
        return _oku(self.yol, {}).get("varsayilan")

    def anahtar(self, b):
        g = _oku(self.gizli_yol, {}).get(b["ad"], {})
        if g.get("anahtar"):
            return g["anahtar"]
        ortam = b.get("anahtar_ortam") or VARSAYILAN_ORTAM.get(b["tur"])
        return os.environ.get(ortam) if ortam else None

    def ozet(self, b):
        """Arayüze giden hâl: anahtarın kendisi yok, yalnız var mı ve nereden."""
        g = _oku(self.gizli_yol, {}).get(b["ad"], {})
        ortam = b.get("anahtar_ortam") or VARSAYILAN_ORTAM.get(b["tur"])
        kaynak = "gizli.json" if g.get("anahtar") else (f"ortam:{ortam}" if ortam and os.environ.get(ortam) else None)
        return {**{k: v for k, v in b.items() if k != "anahtar"}, "anahtar_var": bool(kaynak), "anahtar_kaynagi": kaynak,
                "yardim": YARDIM.get(b["tur"], "")}

    def kaydet(self, b, anahtar=None):
        """Bağlantıyı ekler ya da günceller. Anahtar verilirse yalnız gizli.json'a yazılır."""
        if b.get("tur") not in TURLER:
            raise BaglantiHatasi(f"tür şunlardan biri olmalı: {TURLER}")
        if not re.match(r"^[A-Za-z0-9_.-]{1,40}$", b.get("ad", "")):
            raise BaglantiHatasi("ad: harf, rakam, - _ . (en çok 40)")
        if b.get("anahtar_ortam") and not re.match(r"^[A-Z_][A-Z0-9_]{1,60}$", b["anahtar_ortam"]):
            raise BaglantiHatasi("anahtar_ortam bir ortam değişkeni ADI olmalı (ör. ANTHROPIC_API_KEY), anahtarın kendisi değil")
        adres = b.get("adres") or VARSAYILAN_ADRES[b["tur"]]
        if adres and not re.match(r"^https?://[^\s]+$", adres):
            raise BaglantiHatasi("adres http:// ya da https:// ile başlamalı")
        temiz = {"ad": b["ad"], "tur": b["tur"], "adres": adres, "model": str(b.get("model", "")).strip()}
        for k in ("anahtar_ortam", "num_ctx", "yanit_bicimi", "zaman_asimi"):
            if b.get(k) not in (None, ""):
                temiz[k] = b[k]
        veri = _oku(self.yol, {"baglantilar": []})
        veri["baglantilar"] = [x for x in veri.get("baglantilar", []) if x["ad"] != temiz["ad"]] + [temiz]
        veri.setdefault("varsayilan", temiz["ad"])
        self.yol.write_text(json.dumps(veri, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if anahtar:
            g = _oku(self.gizli_yol, {})
            g[temiz["ad"]] = {"anahtar": str(anahtar).strip()}
            self.gizli_yol.write_text(json.dumps(g, ensure_ascii=False, indent=2), encoding="utf-8")
        return self.ozet(temiz)

    def sil(self, ad):
        veri = _oku(self.yol, {"baglantilar": []})
        veri["baglantilar"] = [x for x in veri.get("baglantilar", []) if x["ad"] != ad]
        if veri.get("varsayilan") == ad:
            veri["varsayilan"] = veri["baglantilar"][0]["ad"] if veri["baglantilar"] else None
        self.yol.write_text(json.dumps(veri, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        g = _oku(self.gizli_yol, {})
        if ad in g:
            g.pop(ad)
            self.gizli_yol.write_text(json.dumps(g, ensure_ascii=False, indent=2), encoding="utf-8")


# ---------------------------------------------------------------- HTTP
def _istek(url, govde=None, basliklar=None, zaman_asimi=60, yontem=None):
    veri = json.dumps(govde).encode() if govde is not None else None
    req = urllib.request.Request(url, veri, {"Content-Type": "application/json", **(basliklar or {})},
                                 method=yontem or ("POST" if veri else "GET"))
    try:
        with urllib.request.urlopen(req, timeout=zaman_asimi) as r:
            return json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        ayrinti = e.read().decode("utf-8", "replace")[:300]
        raise BaglantiHatasi(f"HTTP {e.code}: {ayrinti}") from None
    except (urllib.error.URLError, OSError) as e:
        raise BaglantiHatasi(f"bağlanılamadı: {getattr(e, 'reason', e)}") from None


DURUM = SONUC / "durum"


def isi_bekle(en_cok=1800):
    """Isı bekçisinin bayrakları: BEKLE varken bekler, DUR varken hata verir."""
    bas = time.time()
    while (DURUM / "BEKLE").exists():
        if (DURUM / "DUR").exists():
            break
        if time.time() - bas > en_cok:
            raise BaglantiHatasi("ısı bekçisi 30 dakikadır bekletiyor")
        time.sleep(5)
    if (DURUM / "DUR").exists():
        raise BaglantiHatasi("ısı bekçisi DUR dedi: yerel model çağrılmıyor")


# ---------------------------------------------------------------- model
class Model:
    """Bir bağlantı profiline göre sohbet eden model. `sohbet(mesajlar)` metin döndürür."""

    def __init__(self, profil, anahtar=None):
        self.p, self.anahtar = profil, anahtar
        self.tur, self.ad = profil["tur"], profil.get("model", "")
        self.adres = (profil.get("adres") or VARSAYILAN_ADRES[self.tur]).rstrip("/")
        self.zaman_asimi = int(profil.get("zaman_asimi", 180))
        self.cagri, self.sure, self.son_baglam = 0, 0.0, 0
        self.spec = f"{self.tur}:{self.ad}"

    # --- sohbet
    def sohbet(self, mesajlar, json_kip=True):
        if not self.ad:
            raise BaglantiHatasi("bağlantıda model adı yok")
        bas = time.time()
        try:
            if self.tur == "ollama":
                return self._ollama(mesajlar, json_kip)
            if self.tur == "anthropic":
                return self._anthropic(mesajlar)
            if self.tur == "agy":
                return self._agy(mesajlar)
            return self._openai(mesajlar, json_kip)
        finally:
            self.cagri += 1
            self.sure += time.time() - bas

    def _ollama(self, mesajlar, json_kip):
        isi_bekle()
        tek_model_yuvasi(self.adres, self.ad)
        govde = {"model": self.ad, "messages": mesajlar, "stream": False, "think": False,
                 "options": {"temperature": 0, "seed": 0, "num_ctx": int(self.p.get("num_ctx", 16384))}}
        if json_kip:
            govde["format"] = "json"
        try:
            out = _istek(self.adres + "/api/chat", govde, zaman_asimi=self.zaman_asimi)
        except BaglantiHatasi as e:
            if "think" not in str(e):
                raise
            govde.pop("think")        # düşünme anahtarı olmayan model
            out = _istek(self.adres + "/api/chat", govde, zaman_asimi=self.zaman_asimi)
        self.son_baglam = out.get("prompt_eval_count") or 0
        return out["message"]["content"]

    def _openai(self, mesajlar, json_kip):
        govde = {"model": self.ad, "messages": mesajlar, "temperature": 0}
        bicim = self.p.get("yanit_bicimi") or ("json_object" if self.tur in ("openai", "gemini") else "yok")
        if json_kip and bicim == "json_object":
            govde["response_format"] = {"type": "json_object"}
        bas = {"Authorization": "Bearer " + self.anahtar} if self.anahtar else {}
        out = _istek(self.adres + "/chat/completions", govde, bas, self.zaman_asimi)
        return out["choices"][0]["message"]["content"]

    def _anthropic(self, mesajlar):
        if not self.anahtar:
            raise BaglantiHatasi("Anthropic anahtarı yok (ANTHROPIC_API_KEY ya da gizli.json)")
        sistem = "\n\n".join(m["content"] for m in mesajlar if m["role"] == "system")
        diger = [{"role": m["role"], "content": m["content"]} for m in mesajlar if m["role"] != "system"]
        govde = {"model": self.ad, "max_tokens": 1024, "temperature": 0, "messages": diger}
        if sistem:
            govde["system"] = sistem
        bas = {"x-api-key": self.anahtar, "anthropic-version": "2023-06-01"}
        out = _istek(self.adres + "/v1/messages", govde, bas, self.zaman_asimi)
        return "".join(b.get("text", "") for b in out.get("content", []) if b.get("type") == "text")

    def _agy(self, mesajlar):
        metin = "\n\n".join(f"[{m['role'].upper()}]\n{m['content']}" for m in mesajlar)
        metin += ("\n\nBu düz metin bir protokoldür; araç çağırma. Cevabını tek bir JSON nesnesi olarak yaz.")
        cwd = pathlib.Path(tempfile.gettempdir()) / "filo-agy-bos"
        cwd.mkdir(exist_ok=True)
        r = subprocess.run(["agy", "--model", self.ad, "--output-format", "json", "-p=" + metin[:30000]], cwd=cwd,
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=self.zaman_asimi + 60)
        try:
            out = json.loads(r.stdout.strip().splitlines()[-1])
        except (ValueError, IndexError):
            raise BaglantiHatasi(f"agy cevabı okunamadı: {r.stderr[:200]}") from None
        if out.get("status") not in (None, "SUCCESS"):
            raise BaglantiHatasi(f"agy: {out.get('status')} {str(out.get('error'))[:200]}")
        return out.get("response", "")

    # --- modeller ve sınama
    def modeller(self):
        if self.tur == "ollama":
            return [m["name"] for m in _istek(self.adres + "/api/tags", zaman_asimi=10).get("models", [])]
        if self.tur == "anthropic":
            if not self.anahtar:
                raise BaglantiHatasi("Anthropic anahtarı yok")
            out = _istek(self.adres + "/v1/models", basliklar={"x-api-key": self.anahtar, "anthropic-version": "2023-06-01"},
                         zaman_asimi=20)
            return [m["id"] for m in out.get("data", [])]
        if self.tur == "agy":
            r = subprocess.run(["agy", "models"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
            return [x.split()[0] for x in r.stdout.splitlines() if x.strip() and not x.startswith(("-", "ID", "Model"))]
        bas = {"Authorization": "Bearer " + self.anahtar} if self.anahtar else {}
        return [m["id"] for m in _istek(self.adres + "/models", basliklar=bas, zaman_asimi=20).get("data", [])]

    def sina(self, sohbetle=False):
        """{tamam, modeller?, model_var?, cevap?, hata?, sure}. sohbetle=True kısa bir JSON sorusu da sorar."""
        bas = time.time()
        out = {"tamam": False}
        try:
            liste = self.modeller()
            out["modeller"] = liste[:50]
            out["model_var"] = (self.ad in liste) if self.ad else None
            if sohbetle and self.ad:
                cevap = self.sohbet([{"role": "user", "content": 'Yalnız şu JSON nesnesini yaz: {"durum": "hazir"}'}])
                out["cevap"] = cevap[:200]
            out["tamam"] = out["model_var"] is not False
            if out["model_var"] is False:
                out["hata"] = f"model listede yok: {self.ad}"
        except (BaglantiHatasi, subprocess.TimeoutExpired, OSError, KeyError) as e:
            out["hata"] = str(e)
        out["sure"] = round(time.time() - bas, 2)
        return out


def tek_model_yuvasi(adres, istenen):
    """Ollama'da istenen dışında yüklü model varsa boşaltır (aynı anda tek model)."""
    try:
        yuklu = [m["name"] for m in _istek(adres + "/api/ps", zaman_asimi=5).get("models", [])]
    except BaglantiHatasi:
        return
    for ad in yuklu:
        if ad != istenen and ad.replace(":latest", "") != istenen:
            try:
                _istek(adres + "/api/generate", {"model": ad, "keep_alive": 0}, zaman_asimi=30)
            except BaglantiHatasi:
                pass


def baglan(ad=None, baglantilar=None):
    """Bağlantı adından Model. Ad verilmezse varsayılan bağlantı."""
    b = baglantilar or Baglantilar()
    ad = ad or b.varsayilan()
    if not ad:
        raise BaglantiHatasi("bağlantı tanımlı değil: Bağlantılar sekmesinden ya da ayarlar/baglantilar.json ile ekleyin")
    profil = b.getir(ad)
    return Model(profil, b.anahtar(profil))


# ---------------------------------------------------------------- yapılandırılmış soru
def json_ayikla(metin):
    metin = re.sub(r"<think>.*?</think>", "", metin or "", flags=re.S)
    bas, son = metin.find("{"), metin.rfind("}")
    if bas < 0 or son < bas:
        raise ValueError("JSON nesnesi yok")
    return json.loads(metin[bas:son + 1])


def sor_json(model, sistem, kullanici, dogrula, onarim=2, iz=None, etiket=""):
    """Dar soru + kod doğrulaması + onarım döngüsü.
    dogrula(veri) -> (temiz_değer, None) ya da (None, hata_metni). Dönüş: (değer, kayıt) — değer None olabilir."""
    mesajlar = [{"role": "system", "content": sistem}, {"role": "user", "content": kullanici}]
    kayit = {"soru": etiket, "denemeler": []}
    for deneme in range(onarim + 1):
        try:
            ham = model.sohbet(mesajlar)
        except BaglantiHatasi as e:
            kayit["denemeler"].append({"hata": f"model çağrısı başarısız: {e}"})
            kayit["sonuc"] = None
            if iz is not None:
                iz.append(kayit)
            return None, kayit
        try:
            veri = json_ayikla(ham)
            deger, hata = dogrula(veri)
        except (ValueError, TypeError, AttributeError) as e:
            deger, hata, veri = None, f"geçerli bir JSON nesnesi değil ({e})", None
        kayit["denemeler"].append({"cevap": veri if veri is not None else ham[:300], "hata": hata})
        if hata is None:
            kayit["sonuc"] = deger
            if iz is not None:
                iz.append(kayit)
            return deger, kayit
        mesajlar = mesajlar + [{"role": "assistant", "content": ham[:2000]},
                               {"role": "user", "content": f"Cevabın kabul edilmedi: {hata}\nAynı soruyu düzeltilmiş "
                                                           "tek bir JSON nesnesiyle yeniden cevapla."}]
    kayit["sonuc"] = None
    if iz is not None:
        iz.append(kayit)
    return None, kayit


class FakeModel:
    """Testler için: sırayla verilen cevaplar (sözlük ya da metin) ya da mesajlara bakan bir işlev."""
    spec = "fake"
    tur = "fake"
    ad = "fake"

    def __init__(self, cevaplar=None, islev=None):
        self.cevaplar, self.islev = list(cevaplar or []), islev
        self.cagri, self.sure, self.mesajlar = 0, 0.0, []

    def sohbet(self, mesajlar, json_kip=True):
        self.cagri += 1
        self.mesajlar.append(mesajlar)
        if self.islev:
            c = self.islev(mesajlar)
        elif self.cevaplar:
            c = self.cevaplar.pop(0)
        else:
            raise BaglantiHatasi("FakeModel: cevap kalmadı")
        return c if isinstance(c, str) else json.dumps(c, ensure_ascii=False)
