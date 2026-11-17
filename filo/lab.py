"""Docker laboratuvarı: kurma, durum, sıfırlama, kapatma; bench için bozukluk enjeksiyonu ve hakemin okumaları.

    python -m filo lab kur        anahtarları üretir (git dışında, lab/anahtar/), imajları kurar, konteynerleri başlatır
    python -m filo lab durum      konteynerler ve SSH erişimi
    python -m filo lab sifirla    konteynerleri imajdan yeniden yaratır (bozukluklar ve posta kutusu temizlenir)
    python -m filo lab kapat      konteynerleri durdurur ve kaldırır

Bozukluk enjeksiyonu ve hakem okumaları `docker exec` ile yapılır: ajanın kullandığı SSH yolundan bağımsızdır, böylece
ajan bozukluğu "görmeden" kurulur ve hakem ajanın raporuna değil laboratuvarın gerçek durumuna bakar.
"""
import getpass
import json
import os
import pathlib
import subprocess
import time
import urllib.error
import urllib.request

from . import ROOT
from .envanter import Envanter

LAB = ROOT / "lab"
ANAHTAR = LAB / "anahtar"
COMPOSE = ["docker", "compose", "-f", str(LAB / "docker-compose.yml"), "-p", "filo-lab"]
MAILPIT_API = "http://127.0.0.1:18025/api/v1"
SMTP = ("127.0.0.1", 11025)


def _kos(komut, zaman_asimi=600, girdi=None):
    # Bayt kipinde: Windows'ta metin kipi stdin'e \r\n yazar ve uzak kabuk betiklerini bozar.
    r = subprocess.run(komut, capture_output=True, timeout=zaman_asimi,
                       input=girdi.encode("utf-8") if isinstance(girdi, str) else girdi,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    return r.returncode, r.stdout.decode("utf-8", "replace"), r.stderr.decode("utf-8", "replace")


def anahtar_uret(envanter=None):
    """İstemci anahtarı ve ortak sunucu anahtarı yoksa üretir; known_hosts dosyasını yazar."""
    ANAHTAR.mkdir(parents=True, exist_ok=True)
    istemci, sunucu = ANAHTAR / "filo_lab", ANAHTAR / "ssh_host_ed25519_key"
    if not istemci.exists():
        rc, out, err = _kos(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", "filo-lab", "-f", str(istemci)])
        if rc:
            raise RuntimeError(f"ssh-keygen başarısız: {err}")
    anahtar_izni(istemci)
    if not sunucu.exists():
        rc, out, err = _kos(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", "filo-lab-sunucu", "-f", str(sunucu)])
        if rc:
            raise RuntimeError(f"ssh-keygen başarısız: {err}")
    pub = (ANAHTAR / "ssh_host_ed25519_key.pub").read_text(encoding="utf-8").split()
    env = envanter or Envanter()
    # Yeni sunucular henüz envanterde olmasa da bilinsin (hepsi aynı sunucu anahtarını kullanır)
    portlar = {(s.adres, s.port) for s in env.sunucular.values() if s.konteyner}
    portlar |= {(t["kayit"]["adres"], t["kayit"]["port"]) for t in YENI_SUNUCULAR.values()}
    satirlar = [f"[{a}]:{p} {pub[0]} {pub[1]}" for a, p in sorted(portlar)]
    (ANAHTAR / "known_hosts").write_text("\n".join(satirlar) + "\n", encoding="utf-8")
    return istemci


def anahtar_izni(istemci=None):
    """Windows OpenSSH, başkalarının okuyabildiği özel anahtarı reddeder ("bad permissions"): dosyanın ACL'sini yalnız
    geçerli kullanıcıya bırakır. Bu proje dosyasının iznidir, sistem ayarı değil. Dosya kopyalanır ya da taşınırsa
    kalıtılan izinler geri gelir; bu yüzden kur ve sifirla her seferinde yeniden uygular (17 Kasım 2026'da görüldü)."""
    istemci = istemci or (ANAHTAR / "filo_lab")
    if not istemci.exists() or not hasattr(subprocess, "CREATE_NO_WINDOW"):
        return
    # `whoami` çıktısının kod sayfası Türkçe kullanıcı adlarını bozar (İ); ad ortamdan kurulur.
    alan = os.environ.get("USERDOMAIN")
    kullanici = f"{alan}\\{getpass.getuser()}" if alan else getpass.getuser()
    rc, out, err = _kos(["icacls", str(istemci), "/inheritance:r", "/grant:r", f"{kullanici}:F"])
    if rc:
        raise RuntimeError(f"anahtar dosyasının izni ayarlanamadı: {(err or out).strip()[:300]}")


def docker_hazir():
    rc, out, err = _kos(["docker", "info", "--format", "{{.ServerVersion}}"], 30)
    return rc == 0, (out.strip() or err.strip())


def lab_sunuculari(envanter=None):
    env = envanter or Envanter()
    return [s for s in env.sunucular.values() if s.konteyner]


def ssh_bekle(envanter=None, sure=90):
    from . import SONUC
    from .denetim import Denetim
    from .yurutme import Yurutucu
    env = envanter or Envanter()
    adlar = [s.ad for s in lab_sunuculari(env)]
    y = Yurutucu(env, denetim=Denetim(SONUC / "lab-denetim.jsonl"))
    son = time.time() + sure
    while True:
        tamam, disarida = y.erisim_sinamasi(adlar, zaman_asimi=10)
        if not disarida or time.time() > son:
            return tamam, disarida
        time.sleep(3)


def kur(insa=True):
    ok, bilgi = docker_hazir()
    if not ok:
        raise RuntimeError(f"Docker çalışmıyor: {bilgi}")
    anahtar_uret()
    if insa:
        rc, out, err = _kos(COMPOSE + ["build"], 1800)
        if rc:
            raise RuntimeError(f"imaj kurulumu başarısız:\n{err[-2000:]}")
    rc, out, err = _kos(COMPOSE + ["up", "-d", "--remove-orphans"], 600)
    if rc:
        raise RuntimeError(f"konteynerler başlatılamadı:\n{err[-2000:]}")
    return ssh_bekle()


def durum():
    rc, out, err = _kos(COMPOSE + ["ps", "-a", "--format", "json"], 60)
    konteynerler = []
    for satir in out.splitlines():
        satir = satir.strip()
        if not satir:
            continue
        try:
            veri = json.loads(satir)
        except ValueError:
            continue
        for k in (veri if isinstance(veri, list) else [veri]):
            konteynerler.append({"ad": k.get("Name"), "durum": k.get("State"), "bilgi": k.get("Status")})
    return {"docker": docker_hazir()[0], "konteynerler": konteynerler, "mailpit": mailpit_hazir()}


def sifirla(sunucular=None):
    """Konteynerleri imajdan yeniden yaratır. `sunucular` verilirse yalnız o konteynerler. Tam sıfırlama sonradan
    açılmış "yeni" sunucuları kapatır ve envanterden çıkarır (laboratuvar temel 8 sunucuya döner)."""
    hizmetler = []
    anahtar_izni()
    if sunucular:
        env = Envanter()
        hizmetler = [env[a].konteyner.replace("filo-", "") for a in sunucular]
    else:
        for ad in list(ek_sunucular()):
            yeni_sunucu_kaldir(ad)
    ek = ["--profile", "yeni"] if hizmetler else []
    rc, out, err = _kos(COMPOSE + ek + ["up", "-d", "--force-recreate", "--remove-orphans", *hizmetler], 600)
    if rc:
        raise RuntimeError(err[-2000:])
    if not sunucular:
        posta_temizle()
    ajan_kayitlarini_dusur(sunucular or [s.ad for s in lab_sunuculari()])
    return ssh_bekle()


def ajan_kayitlarini_dusur(adlar):
    """Konteyner imajdan yeniden yaratılınca içindeki Filo ajanı ve kimliği gider: kapıdaki kaydı da düşürülür (yoksa
    kapı onu `canli_sinir` boyunca canlı sanar ve işler önce ölü ajana gider). Kapı çalışmıyorsa bir şey yapılmaz."""
    from .ajan_istemci import AjanYok, ajan_durumlari, onbellegi_bosalt, yerel_istek
    try:
        kayitli = ajan_durumlari(onbellek_sn=0)
        for ad in adlar:
            if ad in kayitli:
                yerel_istek("/yerel/v1/kaldir", {"sunucu": ad, "neden": "laboratuvar sıfırlandı (konteyner yeniden yaratıldı)"},
                            zaman_asimi=5)
    except AjanYok:
        pass
    onbellegi_bosalt()


# ---------------------------------------------------------------- sonradan açılan "yeni" sunucular (B3)
YENI_SUNUCULAR = {
    "PA-WEB-02": {"hizmet": "pa-web-02", "durmus_servisler": ["webd"],
                  "kayit": {"ad": "PA-WEB-02", "os": "linux", "aile": "debian", "adres": "127.0.0.1", "port": 2209,
                            "kullanici": "filo", "kimlik": "lab-anahtar", "tasiyici": "ssh", "gruplar": ["pa", "web", "test"],
                            "oznitelikler": {"ortam": "test", "rol": "web", "konum": "ist", "teslim": "bekliyor"},
                            "konteyner": "filo-pa-web-02"}},
    "PB-APP-02": {"hizmet": "pb-app-02", "durmus_servisler": [],
                  "kayit": {"ad": "PB-APP-02", "os": "linux", "aile": "alpine", "adres": "127.0.0.1", "port": 2210,
                            "kullanici": "filo", "kimlik": "lab-anahtar", "tasiyici": "ssh", "gruplar": ["pb", "app", "prod"],
                            "oznitelikler": {"ortam": "prod", "rol": "uygulama", "konum": "ank", "teslim": "bekliyor"},
                            "konteyner": "filo-pb-app-02"}},
}


def ek_sunucular():
    from .envanter import EK_ENVANTER
    if not EK_ENVANTER.exists():
        return {}
    return {s["ad"]: s for s in json.loads(EK_ENVANTER.read_text(encoding="utf-8")).get("sunucular", [])}


def _ek_yaz(sunucular):
    from .envanter import EK_ENVANTER
    if not sunucular:
        EK_ENVANTER.unlink(missing_ok=True)
        return
    EK_ENVANTER.write_text(json.dumps({"aciklama": "Sonradan açılan laboratuvar sunucuları (python -m filo lab yeni-sunucu). "
                                                   "Tam sıfırlama bu dosyayı siler.",
                                       "sunucular": list(sunucular.values())}, ensure_ascii=False, indent=1),
                           encoding="utf-8")


def yeni_sunucu(ad):
    """Yeni bir sunucuyu imajından sıfır açar ve envantere ekler. Konteyner zaten varsa yeniden yaratılır (temiz kurulum).
    Dönüş: (erişilebilir mi, açıklama)."""
    ad = ad.upper()
    if ad not in YENI_SUNUCULAR:
        raise ValueError(f"tanımlı yeni sunucu değil: {ad} (tanımlılar: {sorted(YENI_SUNUCULAR)})")
    t = YENI_SUNUCULAR[ad]
    anahtar_izni()
    rc, out, err = _kos(COMPOSE + ["--profile", "yeni", "up", "-d", "--force-recreate", t["hizmet"]], 600)
    if rc:
        raise RuntimeError(f"{ad} açılamadı:\n{err[-1500:]}")
    for sv in t["durmus_servisler"]:          # yeni sunucuda bu servisler henüz etkin değil: teslim profili başlatır
        dexec(t["kayit"]["konteyner"], f"/usr/local/sbin/filo-svc stop {sv}")
    ek = ek_sunucular()
    ek[ad] = t["kayit"]
    _ek_yaz(ek)
    ajan_kayitlarini_dusur([ad])
    from .teslim import teslim_kaydini_sil
    teslim_kaydini_sil(ad)                     # sıfırdan açılan sunucu yeniden teslim edilir
    anahtar_uret()                              # known_hosts yeni sunucuyu da içersin
    from .yurutme import Yurutucu
    from .denetim import Denetim
    from . import SONUC
    y = Yurutucu(Envanter(), denetim=Denetim(SONUC / "lab-denetim.jsonl"))
    son = time.time() + 60
    while time.time() < son:
        tamam, _ = y.erisim_sinamasi([ad], zaman_asimi=10)
        if tamam:
            return True, f"{ad} açıldı ve envantere eklendi (SSH erişilebilir)"
        time.sleep(2)
    return False, f"{ad} açıldı ama SSH 60 sn içinde cevap vermedi"


def yeni_sunucu_kaldir(ad):
    ad = ad.upper()
    t = YENI_SUNUCULAR.get(ad)
    if t:
        _kos(COMPOSE + ["--profile", "yeni", "rm", "-s", "-f", t["hizmet"]], 300)
    ek = ek_sunucular()
    ek.pop(ad, None)
    _ek_yaz(ek)
    ajan_kayitlarini_dusur([ad])
    return True


def kapat():
    for ad in list(ek_sunucular()):
        yeni_sunucu_kaldir(ad)
    rc, out, err = _kos(COMPOSE + ["--profile", "yeni", "down", "--remove-orphans"], 300)
    return rc == 0, (err or out)[-500:]


def konteyner_durdur(konteyner):
    return _kos(["docker", "stop", "-t", "2", konteyner], 60)[0] == 0


def konteyner_baslat(konteyner):
    return _kos(["docker", "start", konteyner], 60)[0] == 0


def dexec(konteyner, betik, kullanici="root", zaman_asimi=120):
    """Konteynerde kök kullanıcıyla bir kabuk betiği çalıştırır (yalnız kurulum ve hakem için). (rc, out, err)"""
    return _kos(["docker", "exec", "-i", "-u", kullanici, konteyner, "sh", "-s"], zaman_asimi, girdi=betik)


# ---------------------------------------------------------------- Mailpit
def _http(yol, yontem="GET"):
    req = urllib.request.Request(MAILPIT_API + yol, method=yontem)
    with urllib.request.urlopen(req, timeout=10) as r:
        veri = r.read()
        return json.loads(veri) if veri.strip() else {}


def mailpit_hazir():
    try:
        _http("/messages?limit=1")
        return True
    except (OSError, urllib.error.URLError, ValueError):
        return False


def posta_listesi(limit=50):
    """Son postalar: kimden, kime, konu, ekler, gövde (ilk 4000 karakter)."""
    out = []
    for m in _http(f"/messages?limit={limit}").get("messages", []):
        tam = _http(f"/message/{m['ID']}")
        out.append({"id": m["ID"], "konu": m.get("Subject", ""), "kime": [a["Address"] for a in m.get("To") or []],
                    "kimden": (m.get("From") or {}).get("Address", ""), "zaman": m.get("Created"),
                    "ekler": [{"ad": a.get("FileName"), "tur": a.get("ContentType"), "boyut": a.get("Size"),
                               "parca": a.get("PartID")} for a in tam.get("Attachments") or []],
                    "govde": (tam.get("Text") or "")[:4000]})
    return out


def posta_eki(posta_id, parca):
    req = urllib.request.Request(f"{MAILPIT_API}/message/{posta_id}/part/{parca}")
    with urllib.request.urlopen(req, timeout=10) as r:
        return r.read().decode("utf-8", "replace")


def posta_temizle():
    try:
        _http("/messages", "DELETE")
        return True
    except (OSError, urllib.error.URLError, ValueError):
        return False


# ---------------------------------------------------------------- bozukluk enjeksiyonu
BOZUKLUKLAR = {
    "sudo_kapali": "Bağlantı kullanıcısının parolasız sudo yetkisi kalkar (C1)",
    "yeniden_yarat": "Sunucu imajından yeniden yaratılır (bozukluklar gider; operatör düzeltmesi)",
    "gizli_dosya": "Yalnız root'un okuyabildiği dosya (parametre: yol, icerik) (C1)",
    "sshd_kapali": "Konteyner durdurulur: sunucuya erişilemez",
    "servis_durmus": "Bir servis durdurulur (parametre: servis)",
    "servis_bozuk": "Servis yapılandırması bozulur: başlatma hata verir (parametre: servis)",
    "servis_yavas": "Servis komutları yavaş cevap verir (parametre: servis, saniye)",
    "disk_dolu": "/veri bölümü doldurulur",
    "sudo_requiretty": "sudo, tty olmadan çalışmayı reddeder",
    "bozuk_depo": "Paket deposu yapılandırması bozulur",
    "yanlis_anahtar": "authorized_keys başka bir anahtarla değiştirilir: kimlik reddedilir",
    "yarim_kurulum": "Paket yöneticisi yarım kalmış bir işlem bırakır (dpkg kesildi / kilit)",
    "dosya_yaz": "Bir dosya yazılır (parametre: yol, icerik)",
    "betik_cikti_degisti": "uygulama sürüm dosyasının biçimi değişir (anahtar=değer yerine serbest metin)",
    "paket_kaldir": "Bir paket kaldırılır (parametre: paket)",
    "yeni_sunucu": "Tanımlı bir yeni sunucu (PA-WEB-02, PB-APP-02) imajından sıfır açılır ve envantere eklenir",
    "ajan_kur": "Sunucuya Filo ajanı kurulur (ajan kapısı çalışıyor olmalı; bench gerekirse kendisi açar)",
    "ajan_oldur": "Sunucudaki Filo ajanı süreci öldürülür (kapı onu bir süre canlı sanar)",
    "ajan_kimlik_sil": "Ajanın kimlik dosyası silinir ve süreci öldürülür (yeniden başlatma yetmez, yeniden kayıt gerekir)",
}


def bozukluk(sunucu_adi, tur, envanter=None, **p):
    """Bir sunucuya bozukluk koyar. Dönüş: (tamam, açıklama)."""
    if tur == "yeni_sunucu":
        return yeni_sunucu(sunucu_adi)
    env = Envanter() if (envanter is None or sunucu_adi not in envanter) else envanter
    s = env[sunucu_adi]
    k = s.konteyner
    if tur == "ajan_kur":
        from .ajan_yonetimi import kur
        r = kur(s, {})
        return r["durum"] == "basarili", r.get("neden") or ""
    if tur == "ajan_oldur":
        rc, out, err = dexec(k, "pkill -f '/usr/local/bin/filo-ajan calis'; sleep 0.5; pgrep -f '/usr/local/bin/filo-ajan calis' || echo yok")
        return "yok" in out, err
    if tur == "ajan_kimlik_sil":
        rc, out, err = dexec(k, "rm -f /etc/filo-ajan/kimlik.json; pkill -f '/usr/local/bin/filo-ajan calis'; true")
        return rc == 0, err
    if tur == "sshd_kapali":
        return konteyner_durdur(k), "konteyner durduruldu"
    if tur == "servis_durmus":
        rc, out, err = dexec(k, f"/usr/local/sbin/filo-svc stop {p.get('servis', 'uygulama')}")
        return rc == 0, err
    if tur == "servis_bozuk":
        sv = p.get("servis", "uygulama")
        rc, out, err = dexec(k, f"/usr/local/sbin/filo-svc stop {sv}; "
                                f"echo '/etc/uygulama/{sv}.conf satir 3: bilinmeyen anahtar' > /etc/filo-svc/{sv}.bozuk")
        return rc == 0, err
    if tur == "servis_yavas":
        # A1'de yavaşlık yalnız start/stop/status'u etkiliyordu; `systemctl is-active` hızlı ve doğru cevap veriyordu, yani
        # "servis komutları yavaş cevap verir" bozukluğu durum sorgusunda hiç görünmüyordu (ilk koşu O05: iki harness'li
        # kol da durumu okuyup 'başarılı' dedi ve sahte başarı sayıldı). Artık is-active de yavaşlar; yalnız kök
        # kullanıcı (hakem, parmak izi; docker exec) etkilenmez.
        rc, out, err = dexec(k, f"echo {int(p.get('saniye', 40))} > /etc/filo-svc/{p.get('servis', 'uygulama')}.yavas; "
                                "grep -q 'id -u' /usr/local/sbin/filo-svc || "
                                "sed -i '/^  is-active)$/a\\    [ \"$(id -u)\" = 0 ] || yavas \"$ad\"' /usr/local/sbin/filo-svc")
        return rc == 0, err
    if tur == "disk_dolu":
        rc, out, err = dexec(k, "dd if=/dev/zero of=/veri/doldurma.bin bs=1M count=64 2>/dev/null; sync; df -h /veri")
        return True, out
    if tur == "sudo_requiretty":
        rc, out, err = dexec(k, "echo 'Defaults requiretty' > /etc/sudoers.d/00-tty; chmod 440 /etc/sudoers.d/00-tty")
        return rc == 0, err
    if tur == "yeniden_yarat":
        # Sunucu imajından yeniden yaratılır (bozukluklar gider): adımdan devam senaryosunda operatörün düzeltmesi
        return bool(sifirla([sunucu_adi])), "konteyner yeniden yaratıldı"
    if tur == "sudo_kapali":
        # C1: bağlantı kullanıcısının parolasız sudo yetkisi kalkar (sudo -n "a password is required" der)
        rc, out, err = dexec(k, "rm -f /etc/sudoers.d/filo")
        return rc == 0, err
    if tur == "gizli_dosya":
        # C1: yalnız root'un okuyabildiği dosya (kimlik gerektiren okuma senaryosu)
        yol = p.get("yol", "/etc/uygulama/anahtar.conf")
        icerik = p.get("icerik", "anahtar_surumu=7")
        rc, out, err = dexec(k, f"printf '%s\\n' '{icerik}' > {yol}; chown root:root {yol}; chmod 600 {yol}")
        return rc == 0, err
    if tur == "bozuk_depo":
        betik = {"debian": "echo 'deb http://depo.yok.invalid/debian bookworm main' > /etc/apt/sources.list.d/bozuk.list;"
                           " rm -f /etc/apt/sources.list.d/debian.sources; rm -rf /var/lib/apt/lists/*",
                 "rhel": "sed -i 's|^mirrorlist=.*|baseurl=http://depo.yok.invalid/el9/|; s|^baseurl=.*|baseurl=http://depo.yok.invalid/el9/|'"
                         " /etc/yum.repos.d/*.repo; dnf clean all >/dev/null 2>&1",
                 "alpine": "echo 'http://depo.yok.invalid/alpine/v3.20/main' > /etc/apk/repositories; rm -rf /var/cache/apk/*"}
        rc, out, err = dexec(k, betik[s.aile])
        return rc == 0, err
    if tur == "yanlis_anahtar":
        rc, out, err = dexec(k, "echo 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIBbJ5gYx1uXk0d1aV4mYcZlD0nH8wq2v9o0p1q2r3s4t baska' "
                                "> /home/filo/.ssh/authorized_keys")
        return rc == 0, err
    if tur == "yarim_kurulum":
        # Gerçek bir "dpkg kesildi" durumu: kurulu bir paketin kaydı yarım yapılandırılmış olarak güncelleme
        # günlüğüne düşer; apt-get "dpkg was interrupted ... dpkg --configure -a" der. Yalnız Debian ailesi.
        if s.aile != "debian":
            raise ValueError("yarim_kurulum yalnız Debian ailesinde tanımlı")
        rc, out, err = dexec(k, "mkdir -p /var/lib/dpkg/updates && dpkg-query -s procps | "
                                "sed 's/^Status: .*/Status: install ok half-configured/' > /var/lib/dpkg/updates/0001")
        return rc == 0, err
    if tur == "dosya_yaz":
        yol, icerik = p["yol"], p.get("icerik", "")
        rc, out, err = dexec(k, f"mkdir -p \"$(dirname '{yol}')\" && cat > '{yol}' <<'FILOEOF'\n{icerik}\nFILOEOF\n")
        return rc == 0, err
    if tur == "betik_cikti_degisti":
        rc, out, err = dexec(k, "echo 'Uygulama Surumu: 1.4.2 (derleme 77)' > /opt/uygulama/surum.txt")
        return rc == 0, err
    if tur == "paket_kaldir":
        pk = p["paket"]
        betik = {"debian": f"apt-get remove -y {pk} >/dev/null 2>&1", "rhel": f"dnf remove -y {pk} >/dev/null 2>&1",
                 "alpine": f"apk del {pk} >/dev/null 2>&1"}
        dexec(k, betik[s.aile])
        return True, ""
    raise ValueError(f"bilinmeyen bozukluk: {tur}")


def onar_ssh(sunucu_adi, envanter=None):
    """Kurulum sonrası (ör. hakem) için: durdurulmuş konteyneri yeniden başlatır."""
    env = envanter or Envanter()
    return konteyner_baslat(env[sunucu_adi].konteyner)


def lab_var():
    """Laboratuvar ayakta mı (testlerde atlama kararı için)."""
    if not (ANAHTAR / "filo_lab").exists():
        return False
    try:
        rc, out, err = _kos(["docker", "inspect", "-f", "{{.State.Running}}", "filo-pa-app-01"], 20)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return rc == 0 and out.strip() == "true"


def anahtar_yolu():
    return pathlib.Path(ANAHTAR / "filo_lab")
