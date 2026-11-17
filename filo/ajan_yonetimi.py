"""Ajan yönetimi: derleme (Docker içindeki resmi golang imajı), kurulum, durum, onarım ve kaldırma.

Kurulum ve onarım SSH yolundan yapılır (SSH artık ağırlıkla ilk kurulum ve onarım yoludur). Bu işler katalogda
`tur: "yonetim"` becerileridir (ajan_kur, ajan_durumu, ajan_onar, ajan_kaldir); motor her sunucu için buradaki işleyiciyi
çağırır, sonuç sunucu başına tek şemadadır (yurutme.py).

Ajanın sunucuda yaşatılması (hizmet yöneticisine göre):
    systemd   /etc/systemd/system/filo-ajan.service (Restart=always), systemctl enable --now
    filo-svc  laboratuvar konteynerlerinde systemd yok; ajan, konteynerin servis yöneticisine (filo-svc, systemctl ve
              rc-service ince katmanlarının altındaki) `filo-ajan` servisi olarak tanımlanır. filo-svc ölen servisi
              kendiliğinden yeniden başlatmaz: durmuş ajanı `ajan_onar` başlatır. Konteyner imajdan yeniden yaratılınca
              (lab sifirla) ajan da gider.
    yok       nohup + /run/filo-ajan.pid (son çare; yeniden başlatma yok)
"""
import json
import secrets
import subprocess
import time

from . import ROOT
from .ajan_istemci import AjanYok, ajan_durumlari, onbellegi_bosalt, yerel_istek
from .erisim import Erisilemedi, Iptal, SSHTasiyici, ZamanAsimi
from .yurutme import bos_sonuc

AJAN_KAYNAK = ROOT / "ajan"
CIKTI = AJAN_KAYNAK / "cikti"
GO_IMAJI = "golang:1.23-alpine"
HEDEFLER = (("linux", "amd64"), ("linux", "arm64"), ("windows", "amd64"))
MIMARI = {"x86_64": "amd64", "amd64": "amd64", "aarch64": "arm64", "arm64": "arm64"}


# ---------------------------------------------------------------- derleme
def derle(testler=True, zaman_asimi=1200):
    """Go testlerini ve çapraz derlemeyi konteynerde koşar. (rc, çıktı)"""
    from .ajan_kapisi import AJAN_SURUM
    adimlar = ["set -e", "go version", "go vet ./..."]
    if testler:
        adimlar.append("go test -count=1 ./...")
    for gos, arch in HEDEFLER:
        ad = f"filo-ajan-{gos}-{arch}" + (".exe" if gos == "windows" else "")
        adimlar.append(f"GOOS={gos} GOARCH={arch} go build -trimpath -ldflags '-s -w -X main.surum={AJAN_SURUM}' "
                       f"-o cikti/{ad} .")
    adimlar.append("cd cikti && sha256sum filo-ajan-* > SHA256SUMS && cat SHA256SUMS")
    komut = ["docker", "run", "--rm", "-v", f"{AJAN_KAYNAK}:/src", "-v", "filo-go-onbellek:/root/.cache",
             "-v", "filo-go-modul:/go/pkg", "-w", "/src", "-e", "CGO_ENABLED=0", "-e", "GOFLAGS=-buildvcs=false",
             GO_IMAJI, "sh", "-c", " && ".join(adimlar)]
    CIKTI.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(komut, capture_output=True, timeout=zaman_asimi,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    cikti = (r.stdout + r.stderr).decode("utf-8", "replace")
    if r.returncode == 0:
        (CIKTI / "surum.json").write_text(json.dumps({"surum": AJAN_SURUM, "imaj": GO_IMAJI,
                                                      "zaman": time.strftime("%Y-%m-%dT%H:%M:%S")}), encoding="utf-8")
    return r.returncode, cikti


def ikili_yolu(gos, arch):
    return CIKTI / (f"filo-ajan-{gos}-{arch}" + (".exe" if gos == "windows" else ""))


# ---------------------------------------------------------------- yardımcılar
def _sonuc(ad, durum, stdout="", neden="", rc=None, sure=0.0):
    r = bos_sonuc(ad, durum, neden)
    r.update(stdout=stdout, cikis_kodu=rc if rc is not None else (0 if durum == "basarili" else None), sure=round(sure, 2),
             tasiyici="ssh", deneme=1)
    return r


def _ssh(sunucu, betik, zaman_asimi=60, durdurma=None):
    t = SSHTasiyici(durdurma) if durdurma else SSHTasiyici()
    return t.calistir(sunucu, betik, zaman_asimi)


KESIF = r"""
echo "mimari=$(uname -m)"
if [ -d /run/systemd/system ]; then echo hizmet=systemd; elif [ -x /usr/local/sbin/filo-svc ]; then echo hizmet=filo-svc; else echo hizmet=yok; fi
if [ -x /usr/local/bin/filo-ajan ]; then echo "ikili=var"; echo "ikili_surum=$(/usr/local/bin/filo-ajan surum 2>/dev/null)"; else echo ikili=yok; fi
if sudo -n test -f /etc/filo-ajan/kimlik.json 2>/dev/null; then echo kimlik=var; else echo kimlik=yok; fi
if pgrep -f '/usr/local/bin/filo-ajan calis' >/dev/null 2>&1; then echo surec=calisiyor; else echo surec=yok; fi
"""


def _kv(metin):
    out = {}
    for s in metin.splitlines():
        if "=" in s:
            k, v = s.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def kesif(sunucu, durdurma=None):
    rc, out, err = _ssh(sunucu, KESIF, 30, durdurma)
    if rc != 0:
        raise Erisilemedi(f"keşif başarısız: {err.strip()[:200]}")
    return _kv(out)


def _hizmet_betigi(hizmet, eylem):
    """eylem: kur | baslat | durdur | kaldir"""
    if hizmet == "systemd":
        return {"kur": "sudo sh -c 'cat > /etc/systemd/system/filo-ajan.service' <<'FILOEOF'\n"
                       "[Unit]\nDescription=Filo ajani\nAfter=network-online.target\n\n[Service]\n"
                       "ExecStart=/usr/local/bin/filo-ajan calis -dizin /etc/filo-ajan\nRestart=always\nRestartSec=5\n\n"
                       "[Install]\nWantedBy=multi-user.target\nFILOEOF\nsudo systemctl daemon-reload\n"
                       "sudo systemctl enable filo-ajan >/dev/null 2>&1\nsudo systemctl restart filo-ajan\n",
                "baslat": "sudo systemctl restart filo-ajan\n",
                "durdur": "sudo systemctl stop filo-ajan 2>/dev/null || true\n",
                "kaldir": "sudo systemctl disable --now filo-ajan 2>/dev/null || true\n"
                          "sudo rm -f /etc/systemd/system/filo-ajan.service\nsudo systemctl daemon-reload\n"}[eylem]
    if hizmet == "filo-svc":
        return {"kur": "echo 'exec /usr/local/bin/filo-ajan calis -dizin /etc/filo-ajan >>/var/log/filo-ajan.log 2>&1' "
                       "| sudo tee /etc/filo-svc/filo-ajan.cmd >/dev/null\nsudo /usr/local/sbin/filo-svc restart filo-ajan\n",
                "baslat": "sudo /usr/local/sbin/filo-svc restart filo-ajan\n",
                "durdur": "sudo /usr/local/sbin/filo-svc stop filo-ajan 2>/dev/null || true\n",
                "kaldir": "sudo /usr/local/sbin/filo-svc stop filo-ajan 2>/dev/null || true\n"
                          "sudo rm -f /etc/filo-svc/filo-ajan.cmd /run/filo-svc/filo-ajan.pid\n"}[eylem]
    baslat = ("sudo sh -c 'nohup /usr/local/bin/filo-ajan calis -dizin /etc/filo-ajan >>/var/log/filo-ajan.log 2>&1 & "
              "echo $! > /run/filo-ajan.pid'\n")
    durdur = "sudo pkill -f '/usr/local/bin/filo-ajan calis' 2>/dev/null || true\nsudo rm -f /run/filo-ajan.pid\n"
    return {"kur": durdur + baslat, "baslat": durdur + baslat, "durdur": durdur, "kaldir": durdur}[eylem]


def _ayar_betigi(sunucu, belirtec):
    from .ajan_kapisi import ayar
    a = ayar()
    veri = json.dumps({"cekirdek": a["sunucular_icin_adres"], "sunucu": sunucu.ad, "kullanici": a["kullanici"],
                       "belirtec": belirtec}, ensure_ascii=False)
    # Belirteç betiğe standart girdiden gider (komut satırına ve süreç listesine girmez); dosya 0600.
    return ("sudo install -d -m 0700 /etc/filo-ajan\nsudo rm -f /etc/filo-ajan/kimlik.json\n"
            "sudo sh -c 'umask 077; cat > /etc/filo-ajan/ajan.json' <<'FILOEOF'\n" + veri + "\nFILOEOF\n")


def canli_bekle(sunucu_adi, sure=30, eski_ajan=None, sonra=None):
    """Ajanın canlı olmasını bekler; `sonra` verilirse o andan SONRA gelmiş bir temas ister (eski kayıt sayılmaz)."""
    from .ajan_istemci import supheyi_kaldir
    son = time.time() + sure
    while time.time() < son:
        onbellegi_bosalt()
        d = ajan_durumlari(onbellek_sn=0).get(sunucu_adi)
        taze = sonra is None or (d and d.get("son_temas_sn") is not None and d["son_temas_sn"] < time.time() - sonra)
        if d and d["durum"] == "canli" and d["ajan"] != eski_ajan and taze:
            supheyi_kaldir(sunucu_adi)
            return d
        time.sleep(1.0)
    return None


# ---------------------------------------------------------------- işleyiciler (motor çağırır)
def kur(sunucu, parametreler, kuru=False, durdurma=None, motor=None):
    bas = time.time()
    try:
        k = kesif(sunucu, durdurma)
        arch = MIMARI.get(k.get("mimari", ""))
        ikili = ikili_yolu("linux", arch) if arch else None
        plan = (f"mimari={k.get('mimari')}\nhizmet={k.get('hizmet')}\nmevcut_ikili={k.get('ikili')}\n"
                f"mevcut_surum={k.get('ikili_surum', '')}\nkurulacak={ikili.name if ikili else 'yok'}\n")
        if kuru:
            return _sonuc(sunucu.ad, "basarili", plan + "eylem=ikili kopyalanacak, ayar yazılacak, "
                                                         f"{k.get('hizmet')} servisi tanımlanıp başlatılacak\n",
                          sure=time.time() - bas)
        if not arch:
            return _sonuc(sunucu.ad, "hatali", plan, f"desteklenmeyen mimari: {k.get('mimari')}", rc=1)
        if not ikili.exists():
            return _sonuc(sunucu.ad, "hatali", plan, "ajan ikilisi derlenmemiş: python -m filo ajan derle", rc=1)
        eski = (ajan_durumlari(onbellek_sn=0).get(sunucu.ad) or {}).get("ajan")
        belirtec = yerel_istek("/yerel/v1/belirtec", {"sunucu": sunucu.ad})["belirtec"]
        uzak_tmp = f"/tmp/filo-ajan.{secrets.token_hex(4)}"
        (SSHTasiyici(durdurma) if durdurma else SSHTasiyici()).scp_gonder(sunucu, ikili, uzak_tmp, 180)
        betik = ("set -e\n" + _hizmet_betigi(k.get("hizmet"), "durdur")
                 + f"sudo install -m 0755 {uzak_tmp} /usr/local/bin/filo-ajan\nrm -f {uzak_tmp}\n"
                 + _ayar_betigi(sunucu, belirtec) + _hizmet_betigi(k.get("hizmet"), "kur") + "echo kuruldu\n")
        rc, out, err = _ssh(sunucu, betik, 120, durdurma)
        if rc != 0:
            return _sonuc(sunucu.ad, "hatali", plan + out, f"kurulum betiği başarısız: {err.strip()[:300]}", rc=rc)
        d = canli_bekle(sunucu.ad, 30, eski)
        if not d:
            return _sonuc(sunucu.ad, "hatali", plan + out, "ajan kuruldu ama 30 sn içinde kalp atışı gelmedi "
                                                           "(çekirdek adresine ulaşamıyor olabilir: /var/log/filo-ajan.log)",
                          rc=1, sure=time.time() - bas)
        return _sonuc(sunucu.ad, "basarili", plan + f"ajan={d['ajan']}\nsurum={d.get('surum')}\ndurum={d['durum']}\n",
                      sure=time.time() - bas)
    except AjanYok as e:
        return _sonuc(sunucu.ad, "hatali", "", f"ajan kapısı çalışmıyor ya da cevap vermedi: {e}", rc=1)
    except Erisilemedi as e:
        return _sonuc(sunucu.ad, "erisilemedi", "", str(e))
    except ZamanAsimi as e:
        return _sonuc(sunucu.ad, "zaman_asimi", "", str(e))
    except Iptal as e:
        return _sonuc(sunucu.ad, "iptal", "", str(e))


def durum(sunucu, parametreler, kuru=False, durdurma=None, motor=None):
    d = ajan_durumlari(onbellek_sn=0).get(sunucu.ad)
    if not d:
        return _sonuc(sunucu.ad, "basarili", "durum=kayitsiz\n")
    s = d.get("sistem") or {}
    metin = (f"durum={d['durum']}\najan={d['ajan']}\nsurum={d.get('surum')}\nson_kalp={d.get('son_kalp') or ''}\n"
             f"son_temas_sn={d.get('son_temas_sn') if d.get('son_temas_sn') is not None else ''}\n"
             f"dagitim={s.get('dagitim_ad') or s.get('dagitim', '')}\nmimari={s.get('mimari', '')}\n"
             f"paket_yoneticisi={s.get('paket_yoneticisi', '')}\nhizmet={s.get('hizmet_yoneticisi', '')}\n")
    r = _sonuc(sunucu.ad, "basarili", metin)
    r["tasiyici"] = "kapi"
    return r


def onar(sunucu, parametreler, kuru=False, durdurma=None, motor=None):
    bas = time.time()
    try:
        d = ajan_durumlari(onbellek_sn=0).get(sunucu.ad)
        k = kesif(sunucu, durdurma)
        if d and d["durum"] == "canli" and k.get("surec") == "calisiyor" and not kuru:
            return _sonuc(sunucu.ad, "basarili", f"durum=canli\najan={d['ajan']}\neylem=yok (ajan zaten çalışıyor)\n")
        yeniden_kayit = k.get("kimlik") != "var" or not d
        plan = (f"ikili={k.get('ikili')}\nkimlik={k.get('kimlik')}\nsurec={k.get('surec')}\nhizmet={k.get('hizmet')}\n"
                f"eylem={'yeniden kur' if k.get('ikili') != 'var' else 'yeniden kayıt + yeniden başlat' if yeniden_kayit else 'yeniden başlat'}\n")
        if kuru:
            return _sonuc(sunucu.ad, "basarili", plan)
        if k.get("ikili") != "var":
            return kur(sunucu, parametreler, False, durdurma)
        betik = "set -e\n"
        if yeniden_kayit:
            belirtec = yerel_istek("/yerel/v1/belirtec", {"sunucu": sunucu.ad})["belirtec"]
            betik += _ayar_betigi(sunucu, belirtec)
        betik += _hizmet_betigi(k.get("hizmet"), "baslat") + "echo yeniden_baslatildi\n"
        an = time.time()
        rc, out, err = _ssh(sunucu, betik, 60, durdurma)
        if rc != 0:
            return _sonuc(sunucu.ad, "hatali", plan + out, f"onarım betiği başarısız: {err.strip()[:300]}", rc=rc)
        d2 = canli_bekle(sunucu.ad, 30, sonra=an)
        if not d2:
            return _sonuc(sunucu.ad, "hatali", plan, "ajan yeniden başlatıldı ama kalp atışı gelmedi", rc=1,
                          sure=time.time() - bas)
        return _sonuc(sunucu.ad, "basarili", plan + f"ajan={d2['ajan']}\ndurum=canli\n", sure=time.time() - bas)
    except AjanYok as e:
        return _sonuc(sunucu.ad, "hatali", "", f"ajan kapısı çalışmıyor: {e}", rc=1)
    except Erisilemedi as e:
        return _sonuc(sunucu.ad, "erisilemedi", "", str(e))
    except ZamanAsimi as e:
        return _sonuc(sunucu.ad, "zaman_asimi", "", str(e))
    except Iptal as e:
        return _sonuc(sunucu.ad, "iptal", "", str(e))


def kaldir(sunucu, parametreler, kuru=False, durdurma=None, motor=None):
    try:
        k = kesif(sunucu, durdurma)
        plan = f"ikili={k.get('ikili')}\nhizmet={k.get('hizmet')}\neylem=servis durdurulup dosyalar silinecek, kayıt iptal\n"
        if kuru:
            return _sonuc(sunucu.ad, "basarili", plan)
        betik = (_hizmet_betigi(k.get("hizmet"), "kaldir")
                 + "sudo rm -rf /etc/filo-ajan /usr/local/bin/filo-ajan /var/log/filo-ajan.log\necho kaldirildi\n")
        rc, out, err = _ssh(sunucu, betik, 60, durdurma)
        try:
            yerel_istek("/yerel/v1/kaldir", {"sunucu": sunucu.ad, "neden": "ajan_kaldir becerisi"})
        except AjanYok:
            pass
        onbellegi_bosalt()
        return _sonuc(sunucu.ad, "basarili" if rc == 0 else "hatali", plan + out, err.strip()[:300], rc=rc)
    except Erisilemedi as e:
        return _sonuc(sunucu.ad, "erisilemedi", "", str(e))
    except (ZamanAsimi, Iptal) as e:
        return _sonuc(sunucu.ad, "zaman_asimi" if isinstance(e, ZamanAsimi) else "iptal", "", str(e))


def teslim_uygula(sunucu, parametreler, kuru=False, durdurma=None, motor=None):
    """Sunucunun teslim profilini (ayarlar/teslim_politikalari.json) aynı motorla yürütür; normalde yeni ajan kaydı
    başlatır, bu beceri onu talep üzerine (Kalfa/Kaptan) başlatır. Yarıda kalırsa burada Kaptan devralmaz: beceriyi
    çağıran ajan (Kaptan ise) kendi teşhis/onarım döngüsüyle ele alır."""
    from .teslim import Teslim, politikalar, profil_bul
    bas = time.time()
    pol = politikalar()
    profil = parametreler.get("profil") or profil_bul(sunucu, pol)[0]
    if not profil or profil not in pol["profiller"]:
        return _sonuc(sunucu.ad, "hatali", "", "bu sunucuya uyan teslim profili yok", rc=1)
    p = pol["profiller"][profil]
    if kuru:
        return _sonuc(sunucu.ad, "basarili", f"profil={profil}\nadimlar={' > '.join(a['beceri'] for a in p['adimlar'])}\n"
                                             f"on_onayli={','.join(a['beceri'] for a in p['adimlar'] if a.get('on_onayli'))}\n")
    if motor is None:
        return _sonuc(sunucu.ad, "hatali", "", "teslim için motor verilmedi", rc=1)
    t = Teslim(motor, sunucu.ad, profil, pol={**pol, "profiller": {**pol["profiller"], profil: {**p, "yarida_kalirsa": "insan"}}},
               durdurma=durdurma or motor.yurutucu.durdurma, neden="teslim_uygula becerisi")
    k = t.yurut()
    from .teslim import teslim_kaydet
    teslim_kaydet(sunucu.ad, profil, k)
    metin = f"profil={profil}\ndurum={k.durum}\nis={k.kimlik}\n"
    if k.durum == "bitti":
        return _sonuc(sunucu.ad, "basarili", metin, sure=time.time() - bas)
    dur = next((a for a in k.adimlar if a.get("durum") != "basarili" and a.get("beceri") != "eposta_gonder"), None)
    neden = (f"{dur['beceri']}: " + "; ".join((r.get("sema_hatasi") or r.get("neden") or r.get("stderr") or "")[:200]
                                              for r in dur.get("sonuclar", []) if r.get("durum") != "basarili")) if dur else k.rapor[:300]
    return _sonuc(sunucu.ad, "hatali", metin, f"teslim yarıda kaldı: {neden}", rc=1, sure=time.time() - bas)


ISLEYICILER = {"ajan_kur": kur, "ajan_durumu": durum, "ajan_onar": onar, "ajan_kaldir": kaldir,
               "teslim_uygula": teslim_uygula}


def isleyici_bul(ad):
    """Yönetim becerisinin kod işleyicisi: ajan yönetimi burada; yama, yazılım politikası, uyum ve anlık görüntü
    işleyicileri kendi modüllerinde (D1-D3)."""
    if ad in ISLEYICILER:
        return ISLEYICILER[ad]
    from . import uyum, yama, yazilim_politikasi
    for m in (yama, yazilim_politikasi, uyum):
        if ad in m.ISLEYICILER:
            return m.ISLEYICILER[ad]
    raise KeyError(f"yönetim işleyicisi yok: {ad}")
