"""Sunucu durumu: toplayıcı, anlık görüntü ve karşılaştırma (D1-D3'ün ortak çekirdeği).

Yama durumu, yazılım politikası sapması, uyum denetimi ve anlık görüntü aynı soruyu sorar: "sunucu şu an ne durumda?"
Bu modül tek bir salt-okur toplayıcı betik üretir (aile farkını kod çözer: apt/dnf/apk, systemd/filo-svc/OpenRC), betiği
motorun yürütücüsüyle (ajan → SSH yedeği, denetim izi, durdurma düğmesi) çalıştırır ve çıktıyı tek biçimli bir sözlüğe
çevirir. Karşılaştırma ve değerlendirme saf Python'dur: model yoktur, aynı girdi aynı sonucu verir.

Görüntü:
    {"sunucu", "zaman", "aile", "acilis", "cekirdek",
     "paketler": {ad: surum}, "servisler": {ad: active|inactive}, "kullanicilar": {ad: {"uid", "kabuk"}},
     "gruplar": {ad: [uyeler]}, "dosyalar": {yol: {"var", "mod", "sahip", "grup", "ozet"}},
     "icerik": {anahtar: "1"|"0"|"yok"}, "sysctl": {anahtar: deger}, "portlar": ["tcp:22", ...],
     "guncellemeler": [{"paket", "kurulu", "aday", "guvenlik", "kaynak"}], "yeniden_baslatma": bool,
     "komutlar": {anahtar: {"rc", "cikti"}}, "uyarilar": [...]}
"""
import base64
import datetime
import json
import re
import shlex

from . import ROOT, SONUC

AYARLAR = ROOT / "ayarlar"
DOSYA_ADLARI = {"yama_politikalari": "yama_politikalari.json", "yazilim_politikalari": "yazilim_politikalari.json",
                "kural_setleri": "uyum_kurallari.json"}
# Ayar ve sonuç kökleri: konsol ve komut satırı depodakileri kullanır; bench her kolu geçici bir kopyada yalıtır
# (bench'te talepten kurulan politika, düzeltme kaydı, görüntü konsolun verisine karışmaz).
KOK = {"ayar": AYARLAR, "sonuc": SONUC}


def sonuc_yolu(*parcalar):
    return KOK["sonuc"].joinpath(*parcalar)


def kayit_dosyasi(kaynak):
    return KOK["ayar"] / DOSYA_ADLARI[kaynak]


def yalit(dizin, ayarlar=None):
    """Bench yalıtımı: ayar dosyaları `dizin/ayarlar`a kopyalanır (senaryo kendi içeriğini verebilir), sonuçlar
    `dizin/sonuc` altına yazılır. `yalitimi_kaldir` ile depo köklerine dönülür."""
    import shutil
    a, s = dizin / "ayarlar", dizin / "sonuc"
    a.mkdir(parents=True, exist_ok=True)
    s.mkdir(parents=True, exist_ok=True)
    for kaynak, ad in DOSYA_ADLARI.items():
        if ayarlar and kaynak in ayarlar:
            (a / ad).write_text(json.dumps(ayarlar[kaynak], ensure_ascii=False), encoding="utf-8")
        elif (AYARLAR / ad).exists():
            shutil.copy(AYARLAR / ad, a / ad)
    KOK.update(ayar=a, sonuc=s)


def yalitimi_kaldir():
    KOK.update(ayar=AYARLAR, sonuc=SONUC)


def _simdi():
    return datetime.datetime.now().isoformat(timespec="seconds")


# ---------------------------------------------------------------- ayar kayıtları (politikalar, kural setleri)
def kayit_oku(kaynak):
    yol = kayit_dosyasi(kaynak)
    if not yol.exists():
        return {}
    return json.loads(yol.read_text(encoding="utf-8"))


def kayit_yaz(kaynak, veri):
    yol = kayit_dosyasi(kaynak)
    gecici = yol.with_suffix(".yeni")
    gecici.write_text(json.dumps(veri, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    gecici.replace(yol)


def kayit_adlari(kaynak):
    v = kayit_oku(kaynak)
    alan = {"kural_setleri": "kural_setleri"}.get(kaynak, "politikalar")
    return sorted((v.get(alan) or {}).keys())


def surumlu_kaydet(kaynak, alan, ad, yeni, kim, neden=""):
    """Politika / kural seti kaydı: aynı içerik yeniden yazılmaz; değişirse sürüm artar, eski sürüm `gecmis`e girer."""
    v = kayit_oku(kaynak) or {}
    tablo = v.setdefault(alan, {})
    eski = tablo.get(ad)
    karsilastir = lambda x: {k: y for k, y in (x or {}).items() if k not in ("surum", "gecmis", "degisiklik")}  # noqa: E731
    if eski and karsilastir(eski) == karsilastir(yeni):
        return eski, False
    kayit = {**yeni, "surum": (eski or {}).get("surum", 0) + 1,
             "degisiklik": {"zaman": _simdi(), "kim": kim, "neden": neden}}
    gecmis = list((eski or {}).get("gecmis", []))
    if eski:
        gecmis.append({k: y for k, y in eski.items() if k != "gecmis"})
    kayit["gecmis"] = gecmis[-20:]
    tablo[ad] = kayit
    kayit_yaz(kaynak, v)
    return kayit, True


# ---------------------------------------------------------------- toplayıcı betik
def _q(x):
    return shlex.quote(str(x))


def toplayici(aile, istek=None):
    """Salt-okur toplayıcı betik. istek: {"paketler", "servisler", "kullanicilar", "portlar", "guncellemeler",
    "yenile": bool, "dosyalar": [yol], "icerik": {anahtar: (yol, desen)}, "sysctl": [anahtar],
    "komutlar": {anahtar: komut}}. Verilmeyen bölüm toplanmaz (paketler/servisler/kullanıcılar varsayılan açık)."""
    i = {"paketler": True, "servisler": True, "kullanicilar": True, **(istek or {})}
    b = ["echo \"bilgi|aile|" + aile + "\"",
         "echo \"bilgi|acilis|$(cat /run/filo-acilis-kimligi 2>/dev/null || cat /proc/sys/kernel/random/boot_id 2>/dev/null)\"",
         "echo \"bilgi|cekirdek|$(uname -r)\""]
    if i.get("paketler") or i.get("guncellemeler"):
        b.append({"debian": "dpkg-query -W -f='paket|${Package}|${Version}|${db:Status-Status}\\n' 2>/dev/null | grep '|installed$'",
                  "rhel": "rpm -qa --qf 'paket|%{NAME}|%{VERSION}-%{RELEASE}\\n' 2>/dev/null",
                  "alpine": "apk info -v 2>/dev/null | sed 's/^/apkv|/'"}.get(aile, "true"))
    if i.get("servisler"):
        b.append("if [ -d /run/systemd/system ]; then systemctl list-units --type=service --all --no-legend --plain 2>/dev/null"
                 " | awk '{sub(/\\.service$/,\"\",$1); print \"servis|\"$1\"|\"$3}';"
                 " elif [ -x /usr/local/sbin/filo-svc ]; then /usr/local/sbin/filo-svc list x 2>/dev/null | awk '{print \"servis|\"$1\"|\"$2}';"
                 " elif command -v rc-status >/dev/null 2>&1; then rc-status -a 2>/dev/null | awk '$2==\"[\"{print \"servis|\"$1\"|\"($3==\"started\"?\"active\":\"inactive\")}'; fi")
    if i.get("kullanicilar"):
        b.append("awk -F: '{print \"kullanici|\"$1\"|\"$3\"|\"$7}' /etc/passwd; awk -F: '{print \"grup|\"$1\"|\"$4}' /etc/group")
    for y in i.get("dosyalar") or []:
        b.append(f"y={_q(y)}; if [ -e \"$y\" ] || sudo -n test -e \"$y\" 2>/dev/null; then s=$(stat -c '%a|%U|%G' \"$y\" 2>/dev/null || sudo -n stat -c '%a|%U|%G' \"$y\" 2>/dev/null); "
                 "h=$(sha256sum \"$y\" 2>/dev/null || sudo -n sha256sum \"$y\" 2>/dev/null); "
                 "echo \"dosya|$y|var|$s|${h%% *}\"; else echo \"dosya|$y|yok||||\"; fi")
    for k, (y, desen) in (i.get("icerik") or {}).items():
        b.append(f"y={_q(y)}; if [ ! -e \"$y\" ] && ! sudo -n test -e \"$y\" 2>/dev/null; then echo 'icerik|{k}|yok'; elif grep -Eq -- {_q(desen)} \"$y\" 2>/dev/null"
                 f" || sudo -n grep -Eq -- {_q(desen)} \"$y\" 2>/dev/null; then echo 'icerik|{k}|1'; else echo 'icerik|{k}|0'; fi")
    for k in i.get("sysctl") or []:
        yol = "/proc/sys/" + str(k).replace(".", "/")
        b.append(f"echo \"sysctl|{k}|$(cat {_q(yol)} 2>/dev/null)\"")
    if i.get("portlar"):
        b.append("ss -Hltn 2>/dev/null | awk '{print \"port|tcp|\"$4}'; ss -Hlun 2>/dev/null | awk '{print \"port|udp|\"$4}'")
    if i.get("guncellemeler"):
        if i.get("yenile", True):
            b.append({"debian": "sudo -n apt-get update -qq >/dev/null 2>&1 || echo 'uyari|depo üst verisi yenilenemedi (apt-get update)'",
                      "rhel": "sudo -n dnf -q makecache >/dev/null 2>&1 || echo 'uyari|depo üst verisi yenilenemedi (dnf makecache)'",
                      "alpine": "sudo -n apk update -q >/dev/null 2>&1 || echo 'uyari|depo üst verisi yenilenemedi (apk update)'"}.get(aile, "true"))
        b.append({"debian": "apt-get -s -o Debug::NoLocking=1 dist-upgrade 2>/dev/null | grep '^Inst ' | sed 's/^/apt|/'",
                  "rhel": "sudo -n dnf -q -C check-update 2>/dev/null | sed 's/^/dnf|/'; "
                          "sudo -n dnf -q -C updateinfo list --security --available 2>/dev/null | sed 's/^/dnfsec|/'",
                  "alpine": "apk version -l '<' 2>/dev/null | sed 's/^/apk|/'; "
                            "wget -qO- \"$(grep -v '^#' /etc/apk/repositories | head -1)/secdb.json\" 2>/dev/null | tr -d '\\n' | sed 's/^/secdb|/'; echo"}
                 .get(aile, "true"))
        b.append("if [ -f /var/run/reboot-required ]; then echo \"yeniden|1|$(tr '\\n' ' ' < /var/run/reboot-required.pkgs 2>/dev/null)\";"
                 " elif command -v needs-restarting >/dev/null 2>&1 && ! sudo -n needs-restarting -r >/dev/null 2>&1; then echo 'yeniden|1|needs-restarting';"
                 " else echo 'yeniden|0|'; fi")
    for k, komut in (i.get("komutlar") or {}).items():
        b.append(f"o=$(sh -c {_q(komut)} 2>&1); rc=$?; printf 'komut|{k}|%s|%s\\n' \"$rc\" \"$(printf '%s' \"$o\" | head -c 4000 | base64 | tr -d '\\n')\"")
    b.append("exit 0")
    return "\n".join(b) + "\n"


APK_SURUM = re.compile(r"^(.+)-([^-]+-r\d+)$")
APK_GUNCEL = re.compile(r"^(\S+)-([^-\s]+-r\d+)\s+<\s+(\S+)")
APT_INST = re.compile(r"^Inst (\S+) \[([^\]]+)\] \((\S+) ([^ )\[]+)")
NEVRA_AD = re.compile(r"^(.+)-[^-]+-[^-]+\.[A-Za-z0-9_]+$")


def ayristir(metin, sunucu=None):
    g = {"sunucu": sunucu, "zaman": _simdi(), "aile": None, "acilis": None, "cekirdek": None, "paketler": {},
         "servisler": {}, "kullanicilar": {}, "gruplar": {}, "dosyalar": {}, "icerik": {}, "sysctl": {}, "portlar": [],
         "guncellemeler": [], "yeniden_baslatma": False, "yeniden_paketler": "", "komutlar": {}, "uyarilar": []}
    dnf, dnfsec, apk, apt, secdb = [], set(), [], [], None
    for s in (metin or "").splitlines():
        tur, _, kalan = s.partition("|")
        p = kalan.split("|")
        if tur == "bilgi" and len(p) >= 2:
            g[p[0]] = p[1].strip() or None
        elif tur == "paket" and len(p) >= 2:
            g["paketler"][p[0]] = p[1]
        elif tur == "apkv":
            m = APK_SURUM.match(kalan.strip())
            if m:
                g["paketler"][m.group(1)] = m.group(2)
        elif tur == "servis" and len(p) >= 2 and p[0]:
            g["servisler"][p[0]] = "active" if p[1].strip() == "active" else "inactive"
        elif tur == "kullanici" and len(p) >= 3:
            g["kullanicilar"][p[0]] = {"uid": p[1], "kabuk": p[2]}
        elif tur == "grup" and len(p) >= 2:
            g["gruplar"][p[0]] = [x for x in p[1].split(",") if x]
        elif tur == "dosya" and len(p) >= 2:
            g["dosyalar"][p[0]] = {"var": p[1] == "var", "mod": (p[2] if len(p) > 2 else "") or None,
                                   "sahip": (p[3] if len(p) > 3 else "") or None, "grup": (p[4] if len(p) > 4 else "") or None,
                                   "ozet": (p[5] if len(p) > 5 else "") or None}
        elif tur == "icerik" and len(p) >= 2:
            g["icerik"][p[0]] = p[1].strip()
        elif tur == "sysctl" and len(p) >= 2:
            g["sysctl"][p[0]] = p[1].strip()
        elif tur == "port" and len(p) >= 2:
            port = p[1].rsplit(":", 1)[-1].strip()
            if p[1].startswith("127.0.0.11:"):
                continue                # Docker'ın konteyner içi DNS dinleyicisi (rastgele port): yapılandırma değil
            if port.isdigit() and f"{p[0]}:{port}" not in g["portlar"]:
                g["portlar"].append(f"{p[0]}:{port}")
        elif tur == "apt":
            apt.append(kalan)
        elif tur == "dnf":
            dnf.append(kalan)
        elif tur == "dnfsec":
            nevra = kalan.split()[-1] if kalan.split() else ""
            m = NEVRA_AD.match(nevra)
            if m:
                dnfsec.add(m.group(1))
        elif tur == "apk":
            apk.append(kalan)
        elif tur == "secdb" and kalan.strip():
            try:
                secdb = json.loads(kalan)
            except ValueError:
                g["uyarilar"].append("güvenlik veritabanı (secdb.json) okunamadı")
        elif tur == "yeniden" and p:
            g["yeniden_baslatma"] = p[0] == "1"
            g["yeniden_paketler"] = (p[1] if len(p) > 1 else "").strip()
        elif tur == "komut" and len(p) >= 3:
            try:
                cikti = base64.b64decode(p[2]).decode("utf-8", "replace")
            except ValueError:
                cikti = ""
            g["komutlar"][p[0]] = {"rc": int(p[1]) if p[1].strip().lstrip("-").isdigit() else None, "cikti": cikti}
        elif tur == "uyari":
            g["uyarilar"].append(kalan)
    for s in apt:
        m = APT_INST.match(s)
        if m:
            g["guncellemeler"].append({"paket": m.group(1), "kurulu": m.group(2), "aday": m.group(3),
                                       "kaynak": m.group(4), "guvenlik": "security" in m.group(4).lower()})
    for s in dnf:
        a = s.split()
        if len(a) != 3 or "." not in a[0] or a[0].lower().startswith(("obsoleting", "security")):
            continue
        ad = a[0].rsplit(".", 1)[0]
        g["guncellemeler"].append({"paket": ad, "kurulu": g["paketler"].get(ad, "?"), "aday": a[1], "kaynak": a[2],
                                   "guvenlik": ad in dnfsec})
    sec = {}
    for x in (secdb or {}).get("packages", []):
        pk = x.get("pkg") or {}
        sec[pk.get("name")] = set((pk.get("secfixes") or {}).keys())
    for s in apk:
        m = APK_GUNCEL.match(s.strip())
        if m:
            g["guncellemeler"].append({"paket": m.group(1), "kurulu": m.group(2), "aday": m.group(3), "kaynak": "apk",
                                       "guvenlik": m.group(3) in sec.get(m.group(1), set())})
    return g


def topla(motor, sunucular, istek=None, is_kimligi=None, gozlemci=None, zaman_asimi=120):
    """Toplayıcıyı hedeflerde çalıştırır. Dönüş: {sunucu: {"sonuc": tek şemalı sonuç, "goruntu": görüntü|None}}."""
    env = motor.envanter

    def fn(s):
        if s.os != "linux":
            return None
        return toplayici(s.aile, istek)
    sonuclar = motor.yurutucu.yelpaze(list(sunucular), fn, zaman_asimi, yeniden_deneme=1, gozlemci=gozlemci,
                                      is_kimligi=is_kimligi)
    out = {}
    for r in sonuclar:
        g = ayristir(r.get("stdout"), r["sunucu"]) if r["durum"] == "basarili" else None
        if g is not None:
            g["aile"] = g.get("aile") or env[r["sunucu"]].aile
        out[r["sunucu"]] = {"sonuc": r, "goruntu": g}
    return out


# ---------------------------------------------------------------- anlık görüntü kayıtları
def goruntu_kaydet(g, etiket=""):
    d = sonuc_yolu("goruntuler", g["sunucu"])
    d.mkdir(parents=True, exist_ok=True)
    ad = g["zaman"].replace(":", "").replace("-", "")
    g = {**g, "etiket": etiket}
    (d / f"{ad}.json").write_text(json.dumps(g, ensure_ascii=False, indent=1), encoding="utf-8")
    return f"{g['sunucu']}/{ad}"


def goruntu_listesi(sunucu=None):
    out = []
    GORUNTULER = sonuc_yolu("goruntuler")
    if not GORUNTULER.exists():
        return out
    for d in sorted(GORUNTULER.iterdir()):
        if not d.is_dir() or (sunucu and d.name != sunucu):
            continue
        for p in sorted(d.glob("*.json")):
            try:
                v = json.loads(p.read_text(encoding="utf-8"))
            except ValueError:
                continue
            out.append({"kimlik": f"{d.name}/{p.stem}", "sunucu": d.name, "zaman": v.get("zaman"),
                        "etiket": v.get("etiket", ""), "paket": len(v.get("paketler", {})),
                        "servis": len(v.get("servisler", {})), "kullanici": len(v.get("kullanicilar", {}))})
    return out


def goruntu_oku(kimlik):
    sunucu, ad = kimlik.split("/", 1)
    if not re.match(r"^[A-Za-z0-9_-]+$", sunucu) or not re.match(r"^[0-9T]+$", ad):
        raise ValueError(f"geçersiz görüntü kimliği: {kimlik}")
    return json.loads((sonuc_yolu("goruntuler") / sunucu / f"{ad}.json").read_text(encoding="utf-8"))


def son_goruntu(sunucu, once=None):
    """Sunucunun en son (ya da `once` kimliğinden önceki) kayıtlı görüntüsü."""
    liste = [x["kimlik"] for x in goruntu_listesi(sunucu)]
    if once in liste:
        liste = liste[:liste.index(once)]
    return goruntu_oku(liste[-1]) if liste else None


# Karşılaştırmada gürültü: açılış kimliği, zaman ve ajan/hizmet pid'leri farkı yapılandırma farkı değildir.
def karsilastir(a, b):
    """İki görüntünün yapılandırma farkı (a: referans/eski, b: hedef/yeni)."""
    f = {}
    pa, pb = a.get("paketler", {}), b.get("paketler", {})
    f["paketler"] = {"yalniz_referansta": sorted(set(pa) - set(pb)), "yalniz_hedefte": sorted(set(pb) - set(pa)),
                     "surum_farki": sorted([k, pa[k], pb[k]] for k in set(pa) & set(pb) if pa[k] != pb[k])}
    sa, sb = a.get("servisler", {}), b.get("servisler", {})
    f["servisler"] = {"yalniz_referansta": sorted(set(sa) - set(sb)), "yalniz_hedefte": sorted(set(sb) - set(sa)),
                      "durum_farki": sorted([k, sa[k], sb[k]] for k in set(sa) & set(sb) if sa[k] != sb[k])}
    ka, kb = a.get("kullanicilar", {}), b.get("kullanicilar", {})
    f["kullanicilar"] = {"yalniz_referansta": sorted(set(ka) - set(kb)), "yalniz_hedefte": sorted(set(kb) - set(ka))}
    da, db = a.get("dosyalar", {}), b.get("dosyalar", {})
    f["dosyalar"] = sorted([y, {k: da.get(y, {}).get(k) for k in ("var", "mod", "sahip", "ozet")},
                            {k: db.get(y, {}).get(k) for k in ("var", "mod", "sahip", "ozet")}]
                           for y in set(da) | set(db)
                           if any(da.get(y, {}).get(k) != db.get(y, {}).get(k) for k in ("var", "mod", "sahip", "ozet")))
    f["portlar"] = {"yalniz_referansta": sorted(set(a.get("portlar", [])) - set(b.get("portlar", []))),
                    "yalniz_hedefte": sorted(set(b.get("portlar", [])) - set(a.get("portlar", [])))}
    ya, yb = a.get("sysctl", {}), b.get("sysctl", {})
    f["sysctl"] = sorted([k, ya.get(k), yb.get(k)] for k in set(ya) | set(yb) if ya.get(k) != yb.get(k))
    f["toplam"] = (sum(len(v) for v in f["paketler"].values()) + sum(len(v) for v in f["servisler"].values())
                   + sum(len(v) for v in f["kullanicilar"].values()) + len(f["dosyalar"])
                   + sum(len(v) for v in f["portlar"].values()) + len(f["sysctl"]))
    return f


def fark_metni(f, en_cok=40):
    """Karşılaştırma sonucunu okunur satırlara çevirir (rapor ve e-posta için)."""
    s = []
    # Önce yapılandırma farkları (servis, kullanıcı, dosya, port, sürüm); paket listesi en sona ve kalabalıksa özetlenir
    # (farklı dağıtımlar karşılaştırılınca yüzlerce paket farkı asıl farkları gömüyordu).
    for alan, ad in (("servisler", "servis"), ("kullanicilar", "kullanıcı"), ("portlar", "port")):
        for x in f[alan].get("yalniz_referansta", []):
            s.append(f"{ad} yalnız referansta: {x}")
        for x in f[alan].get("yalniz_hedefte", []):
            s.append(f"{ad} yalnız hedefte: {x}")
    for k, va, vb in f["servisler"]["durum_farki"]:
        s.append(f"servis durumu farklı: {k} {va} → {vb}")
    for y, va, vb in f["dosyalar"]:
        s.append(f"dosya farklı: {y} ({'var' if va.get('var') else 'yok'} {va.get('mod') or ''} {str(va.get('ozet') or '')[:12]}"
                 f" → {'var' if vb.get('var') else 'yok'} {vb.get('mod') or ''} {str(vb.get('ozet') or '')[:12]})")
    for k, va, vb in f["sysctl"]:
        s.append(f"sysctl farklı: {k} {va} → {vb}")
    for k, va, vb in f["paketler"]["surum_farki"][:15]:
        s.append(f"paket sürümü farklı: {k} {va} → {vb}")
    if len(f["paketler"]["surum_farki"]) > 15:
        s.append(f"paket sürümü farklı: {len(f['paketler']['surum_farki']) - 15} paket daha")
    for alan, ad in (("yalniz_referansta", "yalnız referansta"), ("yalniz_hedefte", "yalnız hedefte")):
        liste = f["paketler"][alan]
        if len(liste) > 8:
            s.append(f"paket {ad}: {len(liste)} paket (ör. {', '.join(liste[:5])})")
        else:
            s.extend(f"paket {ad}: {x}" for x in liste)
    return s[:en_cok] + ([f"... ve {len(s) - en_cok} fark daha"] if len(s) > en_cok else [])

