"""Düzeltme eylemleri: istenen duruma götüren küçük, idempotent, geri alınabilir adımlar (D1-D3'ün ortak yürütücüsü).

Yama uygulama, yazılım politikası remediation'ı ve uyum düzeltmesi aynı eylem türlerini kullanır; komutu aileye göre
kod üretir (apt-get/dnf/apk, systemctl/rc-service, useradd/adduser). Her eylemin riski ve geri alma eylemi koddadır;
uygulanan her eylem `results/duzeltmeler/kayit.jsonl` dosyasına geri alma eylemleriyle yazılır, böylece "geri al" aynı
işin tersini, aynı yoldan yapar. Geri alınamayan eylem (ör. kullanıcı silme) bunu açıkça söyler.

Eylem: {"tur": ..., alanlar...}
    paket_kur {ad, surum?}        paket_kaldir {ad}         paket_yukselt {paketler: [..]}   paket_surum {ad, surum}
    servis_baslat {ad}            servis_durdur {ad}        kullanici_ac {ad}                kullanici_sil {ad}
    dosya_yaz {yol, kaynak|icerik, mod?}                    izin {yol, mod}
    satir_ayarla {yol, anahtar, deger, ayirici?}            dosya_geri {yol, vardi}
"""
import base64
import datetime
import hashlib
import json
import re
import shlex

from .beceri import DOSYALAR

def _kayit():
    from . import durum
    return durum.sonuc_yolu("duzeltmeler", "kayit.jsonl")
RISK = {"paket_kur": 3, "paket_kaldir": 3, "paket_yukselt": 3, "paket_surum": 3, "servis_baslat": 3,
        "servis_durdur": 3, "kullanici_ac": 3, "kullanici_sil": 4, "dosya_yaz": 2, "izin": 2, "satir_ayarla": 2,
        "dosya_geri": 2, "yeniden_baslat": 4}
GERI_ALINAMAZ = {"kullanici_sil": "silinen kullanıcının ev dizini ve dosyaları geri getirilemez",
                 "yeniden_baslat": "yeniden başlatma geri alınmaz"}
_AD = re.compile(r"^[A-Za-z0-9][A-Za-z0-9+._@-]{0,63}$")
_YOL = re.compile(r"^/[A-Za-z0-9_./-]{1,250}$")
_SURUM = re.compile(r"^[A-Za-z0-9.+~:_-]{1,64}$")


def _q(x):
    return shlex.quote(str(x))


class EylemHatasi(ValueError):
    pass


def dogrula(e):
    t = e.get("tur")
    if t not in RISK:
        raise EylemHatasi(f"bilinmeyen eylem: {t}")
    for alan in ("ad",):
        if alan in e and not _AD.match(str(e[alan])):
            raise EylemHatasi(f"{t}: geçersiz ad {e[alan]!r}")
    if "yol" in e and (not _YOL.match(str(e["yol"])) or ".." in str(e["yol"])):
        raise EylemHatasi(f"{t}: geçersiz yol {e['yol']!r}")
    if e.get("surum") and not _SURUM.match(str(e["surum"])):
        raise EylemHatasi(f"{t}: geçersiz sürüm {e['surum']!r}")
    if e.get("mod") and not re.match(r"^0?[0-7]{3,4}$", str(e["mod"])):
        raise EylemHatasi(f"{t}: geçersiz kip {e['mod']!r}")
    for p in e.get("paketler", []):
        if not _AD.match(str(p)):
            raise EylemHatasi(f"{t}: geçersiz paket {p!r}")
    return e


def aciklama(e):
    t = e["tur"]
    return {"paket_kur": lambda: f"{e['ad']} paketini kur" + (f" (sürüm {e['surum']})" if e.get("surum") else ""),
            "paket_kaldir": lambda: f"{e['ad']} paketini kaldır",
            "paket_yukselt": lambda: "güncelle: " + ", ".join(e["paketler"]),
            "paket_surum": lambda: f"{e['ad']} paketini {e['surum']} sürümüne getir",
            "servis_baslat": lambda: f"{e['ad']} servisini başlat", "servis_durdur": lambda: f"{e['ad']} servisini durdur",
            "kullanici_ac": lambda: f"{e['ad']} kullanıcısını aç", "kullanici_sil": lambda: f"{e['ad']} kullanıcısını sil",
            "dosya_yaz": lambda: f"{e['yol']} dosyasını yaz" + (f" ({e.get('kaynak')})" if e.get("kaynak") else ""),
            "izin": lambda: f"{e['yol']} izni {e['mod']}",
            "satir_ayarla": lambda: f"{e['yol']}: {e['anahtar']}{e.get('ayirici', ' ')}{e['deger']}",
            "dosya_geri": lambda: f"{e['yol']} önceki hâline", "yeniden_baslat": lambda: "sunucuyu yeniden başlat"}[t]()


def _icerik(e):
    if e.get("kaynak"):
        yol = DOSYALAR / e["kaynak"]
        if not yol.is_file() or yol.parent != DOSYALAR:
            raise EylemHatasi(f"dosya kütüphanesinde yok: {e['kaynak']}")
        return yol.read_bytes()
    return str(e.get("icerik", "")).encode("utf-8")


def icerik_ozeti(e):
    return hashlib.sha256(_icerik(e)).hexdigest()


def komut(aile, e, is_kimligi):
    """Tek eylemin kabuk komutu (aileye göre). Sudo -n: parola isterse beklemez."""
    t = e["tur"]
    yedek = f"$y.filo-yedek-{is_kimligi}"
    if t in ("paket_kur", "paket_surum"):
        ad, v = e["ad"], e.get("surum")
        if aile == "debian":
            if not v:
                return f"sudo -n env DEBIAN_FRONTEND=noninteractive apt-get install -y -q {_q(ad)}"
            return (f"v=$(apt-cache madison {_q(ad)} 2>/dev/null | awk '{{print $3}}' | grep -E '^{re.escape(v)}([-+~]|$)' | head -1); "
                    f"[ -n \"$v\" ] || {{ echo 'sürüm depoda yok: {ad} {v}' >&2; exit 3; }}; "
                    f"sudo -n env DEBIAN_FRONTEND=noninteractive apt-get install -y -q --allow-downgrades {_q(ad)}=\"$v\"")
        if aile == "rhel":
            if not v:
                return f"sudo -n dnf -y -q install {_q(ad)}"
            return (f"sudo -n dnf -q list --showduplicates {_q(ad + '-' + v)} >/dev/null 2>&1 || {{ echo 'sürüm depoda yok: {ad} {v}' >&2; exit 3; }}; "
                    f"if rpm -q {_q(ad)} >/dev/null 2>&1; then sudo -n dnf -y -q downgrade {_q(ad + '-' + v)} 2>/dev/null || "
                    f"sudo -n dnf -y -q upgrade {_q(ad + '-' + v)} 2>/dev/null || rpm -q {_q(ad + '-' + v)}; "
                    f"else sudo -n dnf -y -q install {_q(ad + '-' + v)}; fi")
        if aile == "alpine":
            if not v:
                return f"sudo -n apk add -q {_q(ad)}"
            return (f"apk search -x -a {_q(ad)} 2>/dev/null | grep -q -- {_q(ad + '-' + v)} || {{ echo 'sürüm depoda yok: {ad} {v}' >&2; exit 3; }}; "
                    f"sudo -n apk add -q {_q(ad + '~' + v)}")
    if t == "paket_kaldir":
        return {"debian": f"sudo -n env DEBIAN_FRONTEND=noninteractive apt-get remove -y -q {_q(e['ad'])}",
                "rhel": f"sudo -n dnf -y -q remove {_q(e['ad'])}", "alpine": f"sudo -n apk del -q {_q(e['ad'])}"}.get(aile)
    if t == "paket_yukselt":
        p = " ".join(_q(x) for x in e["paketler"])
        return {"debian": f"sudo -n env DEBIAN_FRONTEND=noninteractive apt-get install -y -q --only-upgrade {p}",
                "rhel": f"sudo -n dnf -y -q upgrade {p}", "alpine": f"sudo -n apk add -q -u {p}"}.get(aile)
    if t in ("servis_baslat", "servis_durdur"):
        ey = "start" if t == "servis_baslat" else "stop"
        return f"sudo -n rc-service {_q(e['ad'])} {ey}" if aile == "alpine" else f"sudo -n systemctl {ey} {_q(e['ad'])}"
    if t == "kullanici_ac":
        return (f"id {_q(e['ad'])} >/dev/null 2>&1 || "
                + (f"sudo -n adduser -D -s /bin/sh {_q(e['ad'])}" if aile == "alpine" else f"sudo -n useradd -m -s /bin/bash {_q(e['ad'])}"))
    if t == "kullanici_sil":
        return (f"! id {_q(e['ad'])} >/dev/null 2>&1 || "
                + (f"sudo -n deluser --remove-home {_q(e['ad'])}" if aile == "alpine" else f"sudo -n userdel -r {_q(e['ad'])}"))
    if t == "dosya_yaz":
        b64 = base64.b64encode(_icerik(e)).decode()
        y = e["yol"]
        return (f"y={_q(y)}; [ -e \"$y\" ] && sudo -n cp -p \"$y\" \"{yedek}\"; "
                f"printf '%s' {_q(b64)} | base64 -d | sudo -n tee \"$y.filo-yeni\" >/dev/null && sudo -n mv \"$y.filo-yeni\" \"$y\""
                + (f" && sudo -n chmod {_q(e['mod'])} \"$y\"" if e.get("mod") else ""))
    if t == "izin":
        return f"sudo -n chmod {_q(e['mod'])} {_q(e['yol'])}"
    if t == "satir_ayarla":
        y, k, d, a = e["yol"], e["anahtar"], e["deger"], e.get("ayirici", " ")
        if not re.match(r"^[A-Za-z0-9_.-]{1,64}$", str(k)) or not re.match(r"^[A-Za-z0-9_.,:/ -]{0,128}$", str(d)):
            raise EylemHatasi("satir_ayarla: anahtar/değer biçimi geçersiz")
        satir = f"{k}{a}{d}"
        return (f"y={_q(y)}; sudo -n cp -p \"$y\" \"{yedek}\" && "
                f"if sudo -n grep -Eq '^[#[:space:]]*{k}([[:space:]=]|$)' \"$y\"; then "
                f"sudo -n sed -i -E 's|^[#[:space:]]*{k}([[:space:]=].*)?$|{satir}|' \"$y\"; "
                f"else printf '%s\\n' {_q(satir)} | sudo -n tee -a \"$y\" >/dev/null; fi")
    if t == "dosya_geri":
        y = e["yol"]
        yedek_ = e.get("yedek") or f"{y}.filo-yedek-{is_kimligi}"
        if e.get("vardi", True):
            return f"[ -e {_q(yedek_)} ] || {{ echo 'yedek yok: {yedek_}' >&2; exit 3; }}; sudo -n mv {_q(yedek_)} {_q(y)}"
        return f"sudo -n rm -f {_q(y)}"
    if t == "yeniden_baslat":
        return "sudo -n reboot" if aile == "alpine" else "sudo -n systemctl reboot"
    return None


def betik(aile, eylemler, is_kimligi, dur_hatada=False):
    """Eylemleri sırayla çalıştıran betik; her eylem için `eylem|sıra|rc|son satırlar` yazar. Bir eylem düşerse
    `dur_hatada` ise kalanlar çalışmaz (`eylem|i|atlandi`)."""
    s = ["dusen=0"]
    for i, e in enumerate(eylemler):
        k = komut(aile, e, is_kimligi)
        if k is None:
            s.append(f"echo 'eylem|{i}|127|bu dağıtımda tanımlı değil'")
            continue
        on = "if [ $dusen = 1 ]; then echo 'eylem|%d|atlandi|'; else " % i if dur_hatada else "{ "
        son = "fi" if dur_hatada else "}"
        s.append(f"{on}( {k} ) >/tmp/filo-eylem.log 2>&1; rc=$?; [ $rc = 0 ] || dusen=1; "
                 f"echo \"eylem|{i}|$rc|$(tail -3 /tmp/filo-eylem.log | tr '\\n|' '  ' | cut -c1-300)\"; {son}")
    s.append("rm -f /tmp/filo-eylem.log; exit 0")
    return "\n".join(s) + "\n"


def sonuclari_ayristir(metin, eylemler):
    out = [dict(e, rc=None, durum="calismadi", hata="") for e in eylemler]
    for satir in (metin or "").splitlines():
        if not satir.startswith("eylem|"):
            continue
        p = satir.split("|", 3)
        if len(p) < 3 or not p[1].isdigit() or int(p[1]) >= len(out):
            continue
        x = out[int(p[1])]
        if p[2] == "atlandi":
            x.update(durum="atlandi", hata="önceki eylem düştü")
            continue
        x["rc"] = int(p[2]) if p[2].lstrip("-").isdigit() else None
        x["durum"] = "basarili" if x["rc"] == 0 else "hatali"
        x["hata"] = "" if x["rc"] == 0 else (p[3] if len(p) > 3 else "").strip()
    return out


def geri_eylem(e, once=None, is_kimligi=None):
    """Bir eylemin geri alma eylemi; geri alınamıyorsa (None, neden). `once`: eylemden önceki görüntü."""
    once = once or {}
    paketler = once.get("paketler", {})
    t = e["tur"]
    if t == "paket_kur":
        if e["ad"] in paketler:
            return {"tur": "paket_surum", "ad": e["ad"], "surum": paketler[e["ad"]]}, ""
        return {"tur": "paket_kaldir", "ad": e["ad"]}, ""
    if t == "paket_surum":
        if e["ad"] in paketler:
            return {"tur": "paket_surum", "ad": e["ad"], "surum": paketler[e["ad"]]}, ""
        return {"tur": "paket_kaldir", "ad": e["ad"]}, ""
    if t == "paket_kaldir":
        v = paketler.get(e["ad"])
        return ({"tur": "paket_surum", "ad": e["ad"], "surum": v}, "") if v else ({"tur": "paket_kur", "ad": e["ad"]}, "")
    if t == "servis_baslat":
        return {"tur": "servis_durdur", "ad": e["ad"]}, ""
    if t == "servis_durdur":
        return {"tur": "servis_baslat", "ad": e["ad"]}, ""
    if t == "kullanici_ac":
        return {"tur": "kullanici_sil", "ad": e["ad"]}, ""
    if t in ("dosya_yaz", "satir_ayarla"):
        vardi = (once.get("dosyalar", {}).get(e["yol"]) or {}).get("var", True)
        return {"tur": "dosya_geri", "yol": e["yol"], "vardi": vardi,
                "yedek": f"{e['yol']}.filo-yedek-{is_kimligi}" if is_kimligi else None}, ""
    if t == "izin":
        eski = (once.get("dosyalar", {}).get(e["yol"]) or {}).get("mod")
        return ({"tur": "izin", "yol": e["yol"], "mod": eski}, "") if eski else (None, "önceki izin bilinmiyor")
    return None, GERI_ALINAMAZ.get(t, "geri alma tanımı yok")


def yukseltme_geri(e, once):
    """paket_yukselt: her paket önceki sürümüne (paket_surum) indirilir. Eski sürüm depoda yoksa eylem çalışırken
    'sürüm depoda yok' der (geri alınamaz olduğu açıkça yazılır)."""
    p = (once or {}).get("paketler", {})
    return [{"tur": "paket_surum", "ad": x, "surum": p[x]} for x in e["paketler"] if x in p]


def risk(eylemler):
    return max([RISK[e["tur"]] for e in eylemler] or [0])


def uygula(motor, eylem_plani, is_kimligi, gozlemci=None, zaman_asimi=300, dur_hatada=False):
    """eylem_plani: {sunucu: [eylem]} → {sunucu: {"sonuc": tek şemalı sonuç, "eylemler": [...rc/durum...]}}."""
    env = motor.envanter
    for ad, ee in eylem_plani.items():
        for e in ee:
            dogrula(e)
    adlar = [a for a, ee in eylem_plani.items() if ee]
    if not adlar:
        return {}
    sonuclar = motor.yurutucu.yelpaze(adlar, lambda s: betik(s.aile, eylem_plani[s.ad], is_kimligi, dur_hatada)
                                      if s.os == "linux" else None, zaman_asimi, yeniden_deneme=0, gozlemci=gozlemci,
                                      is_kimligi=is_kimligi)
    out = {}
    for r in sonuclar:
        ee = sonuclari_ayristir(r.get("stdout"), eylem_plani[r["sunucu"]])
        if r["durum"] == "basarili" and any(e["durum"] != "basarili" for e in ee):
            r = {**r, "durum": "hatali", "neden": "; ".join(f"{aciklama(e)}: {e['hata'] or e['durum']}"
                                                            for e in ee if e["durum"] != "basarili")[:500]}
        out[r["sunucu"]] = {"sonuc": r, "eylemler": ee}
        _ = env
    return out


def kaydet(is_kimligi, beceri, sunucu, eylemler, geri, ek=None):
    KAYIT = _kayit()
    KAYIT.parent.mkdir(parents=True, exist_ok=True)
    with KAYIT.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"zaman": datetime.datetime.now().isoformat(timespec="seconds"), "is": is_kimligi,
                            "beceri": beceri, "sunucu": sunucu, "eylemler": eylemler, "geri": geri, **(ek or {})},
                           ensure_ascii=False) + "\n")


def kayitlar(sunucu=None, beceri=None, is_kimligi=None):
    KAYIT = _kayit()
    if not KAYIT.exists():
        return []
    out = []
    for s in KAYIT.read_text(encoding="utf-8").splitlines():
        try:
            v = json.loads(s)
        except ValueError:
            continue
        if (sunucu and v.get("sunucu") != sunucu) or (beceri and v.get("beceri") not in (beceri if isinstance(beceri, (list, tuple, set)) else [beceri])) \
                or (is_kimligi and v.get("is") != is_kimligi):
            continue
        out.append(v)
    return out


def son_kayit(sunucu, beceriler, geri_alinmamis=True):
    for v in reversed(kayitlar(sunucu, beceriler)):
        if geri_alinmamis and v.get("geri_alindi"):
            continue
        return v
    return None


def geri_alindi_isaretle(is_kimligi, sunucu, geri_is):
    KAYIT = _kayit()
    if not KAYIT.exists():
        return
    satirlar = []
    for s in KAYIT.read_text(encoding="utf-8").splitlines():
        try:
            v = json.loads(s)
        except ValueError:
            satirlar.append(s)
            continue
        if v.get("is") == is_kimligi and v.get("sunucu") == sunucu:
            v["geri_alindi"] = geri_is
        satirlar.append(json.dumps(v, ensure_ascii=False))
    KAYIT.write_text("\n".join(satirlar) + "\n", encoding="utf-8")
