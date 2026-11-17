"""Uzak erişim: taşıyıcılar, durdurma düğmesi, salt-okur komut izin listesi.

    Linux sunucular     sistemdeki OpenSSH istemcisi (ssh, scp), yalnız anahtarla; betik stdin'den `sh -s` ile gider,
                        komut satırında tırnak sorunu ve kimlik bilgisi olmaz
    Windows sunucular   PowerShell Invoke-Command (WinRM); WinRM hazır değilse öykünücü cevaplar ve sonuç
                        `oykunme: true` etiketi taşır (başarı diye sayılmaz, ayrı raporlanır)

Kimlik bilgisi envanterde bir profil ADIDIR (ayarlar/kimlikler.json); anahtar dosyasının yolu yalnız çalıştırma
anında çözülür ve denetim izine, modele, sonuçlara girmez.

Durdurma düğmesi: `DURDURMA.bas()` çalışan bütün ssh/powershell süreçlerini öldürür ve bayrak dosyası
(results/durum/DURDUR) kaldırılana kadar yeni uzak işlem başlatılmaz. Web arayüzü ve komut satırı aynı bayrağı görür.
"""
import base64
import json
import os
import re
import subprocess
import threading
import time

from . import AYARLAR, ROOT, SONUC

DURUM_DIZINI = SONUC / "durum"


class Erisilemedi(Exception):
    pass


class ZamanAsimi(Exception):
    pass


class Iptal(Exception):
    pass


# ---------------------------------------------------------------- durdurma düğmesi
class Durdurma:
    def __init__(self, bayrak=None):
        self.bayrak = bayrak or (DURUM_DIZINI / "DURDUR")
        self._surecler = set()
        self._kilit = threading.Lock()

    def basili(self):
        return self.bayrak.exists()

    def bas(self, neden="operatör"):
        self.bayrak.parent.mkdir(parents=True, exist_ok=True)
        self.bayrak.write_text(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {neden}\n", encoding="utf-8")
        with self._kilit:
            surecler = list(self._surecler)
        for p in surecler:
            try:
                p.kill()
            except OSError:
                pass
        return len(surecler)

    def kaldir(self):
        self.bayrak.unlink(missing_ok=True)

    def kaydet(self, p):
        with self._kilit:
            self._surecler.add(p)

    def birak(self, p):
        with self._kilit:
            self._surecler.discard(p)

    def neden(self):
        try:
            return self.bayrak.read_text(encoding="utf-8").strip()
        except OSError:
            return ""


DURDURMA = Durdurma()


def _kos(komut, girdi=None, zaman_asimi=60, durdurma=DURDURMA):
    """Bir süreci çalıştırır; (rc, stdout_bytes, stderr_bytes). ZamanAsimi / Iptal fırlatır."""
    if durdurma.basili():
        raise Iptal("durdurma düğmesi basılı")
    p = subprocess.Popen(komut, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    durdurma.kaydet(p)
    try:
        out, err = p.communicate(input=girdi, timeout=zaman_asimi)
    except subprocess.TimeoutExpired:
        p.kill()
        p.communicate()
        raise ZamanAsimi(f"{zaman_asimi} sn içinde bitmedi") from None
    finally:
        durdurma.birak(p)
    if durdurma.basili():
        raise Iptal("durdurma düğmesi basıldı")
    return p.returncode, out, err


# ---------------------------------------------------------------- kimlik profilleri
def kimlik_profili(ad, yol=None):
    veri = json.loads((yol or (AYARLAR / "kimlikler.json")).read_text(encoding="utf-8"))
    p = veri.get("profiller", {}).get(ad)
    if p is None:
        raise Erisilemedi(f"kimlik profili tanımlı değil: {ad}")
    return p


def _yol(p):
    p = str(p)
    return p if os.path.isabs(p) else str(ROOT / p)


# ---------------------------------------------------------------- taşıyıcılar
SSH_HATALARI = re.compile(r"(Connection refused|timed out|No route to host|Could not resolve|Permission denied|"
                          r"Host key verification failed|Connection closed|Connection reset|kex_exchange|"
                          r"banner exchange|Network is unreachable|UNPROTECTED PRIVATE KEY|bad permissions)", re.I)


class SSHTasiyici:
    ad = "ssh"

    def __init__(self, durdurma=DURDURMA, kimlik_yolu=None):
        self.durdurma, self.kimlik_yolu = durdurma, kimlik_yolu

    def _ssh_secenekleri(self, sunucu):
        p = kimlik_profili(sunucu.kimlik, self.kimlik_yolu)
        if p.get("tur") != "ssh-anahtar":
            raise Erisilemedi(f"{sunucu.ad}: kimlik profili ssh anahtarı değil")
        return ["-F", "none", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5", "-o", "StrictHostKeyChecking=yes",
                "-o", f"UserKnownHostsFile={_yol(p['bilinen_sunucular'])}", "-o", "IdentitiesOnly=yes",
                "-o", f"IdentityFile={_yol(p['anahtar_dosyasi'])}", "-o", "LogLevel=ERROR",
                "-o", "ServerAliveInterval=10", "-o", "ServerAliveCountMax=2"]

    def calistir(self, sunucu, betik, zaman_asimi=60):
        """Betiği sunucuda `sh -s` ile çalıştırır. (rc, stdout, stderr)"""
        komut = ["ssh", *self._ssh_secenekleri(sunucu), "-p", str(sunucu.port),
                 f"{sunucu.kullanici}@{sunucu.adres}", "sh -s"]
        rc, out, err = _kos(komut, betik.encode("utf-8"), zaman_asimi, self.durdurma)
        out, err = out.decode("utf-8", "replace"), err.decode("utf-8", "replace")
        if rc == 255 and SSH_HATALARI.search(err):
            raise Erisilemedi(err.strip().splitlines()[-1] if err.strip() else "ssh bağlantısı kurulamadı")
        if rc == 255 and not out.strip() and not err.strip():
            # Docker Desktop'un port vekili, konteyner durmuşken bağlantıyı kabul edip iletisiz kapatır: ssh 255 ile
            # ve hiçbir şey yazmadan çıkar (17 Kasım 2026'da görüldü; A1'de "Connection refused" yazıyordu).
            raise Erisilemedi("ssh bağlantısı kurulamadı (çıkış 255, sunucu cevap vermeden kapattı)")
        return rc, out, err

    def scp_gonder(self, sunucu, yerel, uzak, zaman_asimi=120):
        """Büyük dosyalar için scp; hedef kullanıcının yazabildiği bir yere gönderir."""
        komut = ["scp", *self._ssh_secenekleri(sunucu), "-P", str(sunucu.port), "-q", str(yerel),
                 f"{sunucu.kullanici}@{sunucu.adres}:{uzak}"]
        rc, out, err = _kos(komut, None, zaman_asimi, self.durdurma)
        err = err.decode("utf-8", "replace")
        if rc != 0:
            raise Erisilemedi(err.strip() or "scp başarısız")
        return rc


_WINRM = {"zaman": 0, "hazir": None}


def _ps(komut, zaman_asimi=40, durdurma=DURDURMA):
    komut = "[Console]::OutputEncoding=[Text.Encoding]::UTF8; $OutputEncoding=[Text.Encoding]::UTF8; " + komut
    kod = base64.b64encode(komut.encode("utf-16-le")).decode()
    rc, out, err = _kos(["powershell", "-NoProfile", "-NonInteractive", "-EncodedCommand", kod], None,
                        zaman_asimi, durdurma)
    return rc, out.decode("utf-8", "replace"), err.decode("utf-8", "replace")


class WinRMTasiyici:
    ad = "winrm"

    def __init__(self, durdurma=DURDURMA):
        self.durdurma = durdurma

    def calistir(self, sunucu, betik, zaman_asimi=60):
        dis = ("$ErrorActionPreference='Stop'; [Console]::OutputEncoding=[Text.Encoding]::UTF8; "
               f"$sb=[scriptblock]::Create(@'\n{betik}\n'@); "
               f"try {{ Invoke-Command -ComputerName '{sunucu.adres}' -ScriptBlock $sb }} "
               "catch [System.Management.Automation.Remoting.PSRemotingTransportException] "
               "{ [Console]::Error.WriteLine('WINRM-ERISIM: ' + $_.Exception.Message); exit 255 }")
        rc, out, err = _ps(dis, zaman_asimi, self.durdurma)
        if rc == 255 and "WINRM-ERISIM" in err:
            raise Erisilemedi(err.strip()[:300])
        return rc, out, err


class Oykunucu:
    """WinRM hazır olmayan Windows hedefleri için kayıtlı cevaplar. Her sonuç `oykunme: true` taşır."""
    ad = "oykunucu"
    # Beceri komutlarındaki `#filo:<işaret>` satırı hangi kayıtlı cevabın verileceğini seçer.
    CEVAPLAR = [
        (r"filo-erisim-ok", "filo-erisim-ok\n"),
        (r"#filo:erisim", "sunucu={ad}\nkullanici=filo\ncalisma_suresi=86400\nsudo=yok\n"),
        (r"#filo:envanter", "sunucu={ad}\nisletim=Microsoft Windows Server 2022 Standard\ncekirdek=10.0.20348\n"
                            "islemci=4\nbellek_mb=8192\nkok_doluluk=61\ncalisma_suresi=86400\n"),
        (r"#filo:disk", "C:|67108864|40960000|61|normal\n"),
        (r"#filo:servis", "servis={servis}\ndurum=active\n"),
        (r"#filo:yama", "bekleyen=2\nkaynak=windows-update\n"),
        (r"^\s*hostname\s*$", "{ad}\n"),
    ]

    def calistir(self, sunucu, betik, zaman_asimi=60):
        servis = (re.search(r"-Name\s+'?([\w.-]+)", betik) or [None, "uygulama"])[1]
        for kalip, cevap in self.CEVAPLAR:
            if re.search(kalip, betik, re.M):
                return 0, cevap.format(ad=sunucu.ad, servis=servis), ""
        return 1, "", "öykünücü: bu komut için kayıtlı cevap yok (WinRM açılınca gerçek sunucu cevaplar)"


def winrm_kontrol(zaman_asimi=40):
    """Bu makinedeki WinRM'in kullanılabilir olup olmadığını salt-okur sınamalarla bulur. Hiçbir ayarı değiştirmez."""
    adimlar, eksik = [], []
    try:
        rc, out, err = _ps("(Get-Service -Name WinRM).Status", zaman_asimi)
        servis = out.strip() or err.strip()
    except (ZamanAsimi, Iptal, OSError) as e:
        servis = f"okunamadı: {e}"
    adimlar.append({"sinama": "WinRM servisi", "sonuc": servis, "tamam": servis == "Running"})
    if servis != "Running":
        eksik.append("WinRM servisi çalışmıyor")
    try:
        rc, out, err = _ps("try { Test-WSMan -ComputerName localhost -ErrorAction Stop | Out-Null; 'ok' } "
                           "catch { 'hata: ' + $_.Exception.Message }", zaman_asimi)
        wsman = out.strip()
    except (ZamanAsimi, Iptal, OSError) as e:
        wsman = f"hata: {e}"
    adimlar.append({"sinama": "WS-Management dinleyicisi (Test-WSMan localhost)", "sonuc": wsman[:300],
                    "tamam": wsman == "ok"})
    if wsman != "ok":
        eksik.append("WS-Management dinleyicisi yok ya da cevap vermiyor")
    uzak = "atlandı (önceki sınama geçmedi)"
    if wsman == "ok":
        try:
            rc, out, err = _ps("try { Invoke-Command -ComputerName localhost -ScriptBlock { hostname } -ErrorAction Stop } "
                               "catch { 'hata: ' + $_.Exception.Message }", zaman_asimi)
            uzak = out.strip()
        except (ZamanAsimi, Iptal, OSError) as e:
            uzak = f"hata: {e}"
        if uzak.startswith("hata"):
            eksik.append("Invoke-Command reddedildi (kullanıcı yönetici ya da Remote Management Users üyesi değil)")
    adimlar.append({"sinama": "Invoke-Command localhost", "sonuc": uzak[:300],
                    "tamam": bool(uzak) and not uzak.startswith(("hata", "atlandı"))})
    hazir = not eksik
    komutlar = [] if hazir else [
        "# Yönetici olarak açılmış bir PowerShell penceresinde (Filo bu ayarları kendisi değiştirmez):",
        "Enable-PSRemoting -Force",
        "# Filo'yu yönetici olmayan bir hesapla çalıştıracaksanız o hesabı uzak yönetim grubuna ekleyin:",
        "Add-LocalGroupMember -Group 'Remote Management Users' -Member $env:USERNAME",
        "# Sonra yeniden sınayın:",
        "python -m filo winrm-kontrol",
    ]
    _WINRM.update(zaman=time.time(), hazir=hazir)
    return {"hazir": hazir, "adimlar": adimlar, "eksik": eksik, "komutlar": komutlar}


def winrm_hazir(onbellek_sn=300):
    if _WINRM["hazir"] is None or time.time() - _WINRM["zaman"] > onbellek_sn:
        try:
            winrm_kontrol(20)
        except Exception:  # noqa: BLE001 - sınama hiçbir koşulda yürütmeyi düşürmesin
            _WINRM.update(zaman=time.time(), hazir=False)
    return bool(_WINRM["hazir"])


def tasiyici_sec(sunucu, durdurma=DURDURMA, winrm_sor=winrm_hazir, ajan_sor=None):
    """Sunucunun taşıyıcısı. SSH sunucusunda canlı Filo ajanı varsa iş ajandan gider (ajan almazsa SSH'a düşülür);
    SSH artık ağırlıkla ilk kurulum ve onarım yoludur. `ajan_sor`: sunucu adı -> canlı mı (testlerde verilir)."""
    if sunucu.tasiyici in ("ssh", "ajan"):
        from . import ajan_istemci
        if (ajan_sor or ajan_istemci.canli_ajan)(sunucu.ad):
            return ajan_istemci.YedekliTasiyici(durdurma)
        return SSHTasiyici(durdurma)
    if sunucu.tasiyici == "winrm":
        return WinRMTasiyici(durdurma) if winrm_sor() else Oykunucu()
    if sunucu.tasiyici == "oykunucu":
        return Oykunucu()
    raise Erisilemedi(f"{sunucu.ad}: bilinmeyen taşıyıcı {sunucu.tasiyici}")


# ---------------------------------------------------------------- salt-okur komut izin listesi
SALT_OKUR = {"hostname", "uname", "uptime", "df", "free", "cat", "head", "tail", "grep", "egrep", "wc", "ls", "ps",
             "id", "whoami", "date", "who", "w", "ip", "ss", "netstat", "printenv", "lsblk", "sort", "uniq", "cut",
             "tr", "du", "stat", "getent", "nproc", "lscpu", "arch", "echo", "find", "dpkg", "dpkg-query", "rpm",
             "apk", "systemctl", "rc-service", "journalctl", "test", "true", "basename", "dirname", "which",
             "command", "md5sum", "sha256sum", "column", "lsof", "pgrep", "vmstat", "iostat", "timedatectl"}
ALT_KOMUT = {"systemctl": {"status", "is-active", "is-enabled", "list-units", "show"},
             "rc-service": None,   # ikinci sözcük servis adı; üçüncü sözcük denetlenir
             "apk": {"info", "version", "list", "policy"},
             "dpkg": {"-l", "-s", "-L", "--list", "--status"},
             "rpm": {"-q", "-qa", "-qi", "-ql", "-qf"}}
YASAK_PARCA = re.compile(r"(>|<|`|\$\(|\bsudo\b|\bsu\b|-delete\b|-exec\b|-ok\b|-fprint|\n)")


def salt_okur_denetle(komut):
    """Komut salt-okur izin listesine uyuyorsa None, uymuyorsa nedenini döndürür."""
    komut = str(komut).strip()
    if not komut:
        return "komut boş"
    if len(komut) > 1000:
        return "komut çok uzun"
    m = YASAK_PARCA.search(komut.replace("2>/dev/null", "").replace("2>&1", ""))
    if m:
        return f"izin verilmeyen parça: {m.group(0)!r}"
    if re.search(r"(?<!&)&(?!&)", komut):
        return "arka plan işareti (&) yasak"
    for parca in re.split(r"\|\||&&|;|\|", komut.replace("2>/dev/null", "").replace("2>&1", "")):
        sozler = parca.split()
        if not sozler:
            continue
        ilk = sozler[0]
        if ilk not in SALT_OKUR:
            return f"izin listesinde olmayan komut: {ilk}"
        if ilk == "rc-service":
            if len(sozler) < 3 or sozler[2] != "status":
                return "rc-service yalnız 'status' ile"
        elif ilk in ALT_KOMUT:
            alt = next((s for s in sozler[1:] if not s.startswith("--no-")), None)
            if alt not in ALT_KOMUT[ilk]:
                return f"{ilk} yalnız {sorted(ALT_KOMUT[ilk])} ile"
    return None
