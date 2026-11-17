"""Gerçek Go ajanı + gerçek laboratuvar konteyneri + sınama için ayrı bir ajan kapısı.

Ajan ikilisi derlenmiş olmalı (python -m filo ajan derle). Konteynerde ayrı bir dizinle ikinci bir ajan süreci başlatılır;
sınamanın kapısı rastgele bir portta çalışır, böylece arka planda çalışan asıl kapıya ve kurulu ajanlara dokunulmaz.
"""
import json
import subprocess
import time

import pytest

from filo import lab
from filo.ajan_istemci import AjanTasiyici
from filo.ajan_kapisi import AjanKapisi, Defter, anahtar_turet, is_zarfi
from filo.ajan_yonetimi import ikili_yolu
from filo.denetim import Denetim
from filo.envanter import Envanter
from filo.erisim import Durdurma

pytestmark = pytest.mark.lab
KONTEYNER = "filo-pb-app-01"
DIZIN = "/tmp/filo-ajan-sinama"


@pytest.fixture
def gercek_ajan(tmp_path):
    if not ikili_yolu("linux", "amd64").exists():
        pytest.skip("ajan derlenmemiş: python -m filo ajan derle")
    d = Denetim(tmp_path / "denetim.jsonl")
    k = AjanKapisi(port=0, defter=Defter(tmp_path / "ajanlar", tmp_path / "gizli.json"), denetim=d,
                   durdurma=Durdurma(tmp_path / "DURDUR")).baslat()
    b = k.belirtec_uret("PB-APP-01")
    subprocess.run(["docker", "cp", str(ikili_yolu("linux", "amd64")), f"{KONTEYNER}:/tmp/filo-ajan-sinama-ikili"],
                   check=True, capture_output=True)
    ayar = json.dumps({"cekirdek": f"http://host.docker.internal:{k.port}", "sunucu": "PB-APP-01", "kullanici": "filo",
                       "belirtec": b})
    lab.dexec(KONTEYNER, f"rm -rf {DIZIN}; mkdir -p {DIZIN}; chmod 700 {DIZIN}; cat > {DIZIN}/ajan.json <<'EOF'\n{ayar}\nEOF\n"
                         f"chmod 755 /tmp/filo-ajan-sinama-ikili\n")
    subprocess.run(["docker", "exec", "-d", KONTEYNER, "sh", "-c",
                    f"exec /tmp/filo-ajan-sinama-ikili calis -dizin {DIZIN} >{DIZIN}/log 2>&1"], check=True)
    son = time.time() + 40           # tam koşuda bir kez 20 sn yetmedi (önceki sınamanın laboratuvar sıfırlamasının hemen ardı)
    while time.time() < son and not k.durumlar().get("PB-APP-01", {}).get("durum") == "canli":
        time.sleep(0.5)
    assert k.durumlar().get("PB-APP-01", {}).get("durum") == "canli", lab.dexec(KONTEYNER, f"cat {DIZIN}/log")[1]
    yield k, d
    lab.dexec(KONTEYNER, f"pkill -f '{DIZIN}'; rm -rf {DIZIN} /tmp/filo-ajan-sinama-ikili")
    k.durdur()


def _tasiyici(k):
    return AjanTasiyici(Durdurma(k.defter.dizin / "DURDUR"), f"http://127.0.0.1:{k.port}", k.yerel_anahtar)


def test_kayit_dosyalari_ve_izinler(gercek_ajan):
    k, d = gercek_ajan
    rc, out, _ = lab.dexec(KONTEYNER, f"stat -c '%a %n' {DIZIN}/kimlik.json {DIZIN}/ajan.json; grep -c belirtec {DIZIN}/ajan.json; "
                                      f"cat {DIZIN}/log")
    assert "600 " + DIZIN + "/kimlik.json" in out and "600 " + DIZIN + "/ajan.json" in out
    assert "\n0\n" in out                                            # belirteç ayardan silindi
    gizli = k.defter.gizliler()[k.ajan_bul("PB-APP-01")["kimlik"]]
    assert gizli not in out                                          # ajanın günlüğünde gizli anahtar yok
    assert gizli not in (d.yol.read_text(encoding="utf-8"))          # denetim izinde de yok


def test_gercek_ajanda_calistirma_zaman_asimi_kesilme(gercek_ajan):
    k, _ = gercek_ajan
    t = _tasiyici(k)
    s = Envanter()["PB-APP-01"]
    rc, out, err = t.calistir(s, "hostname; id -un; echo uyari >&2; exit 4", 10)
    assert (rc, out, err) == (4, "PB-APP-01\nfilo\n", "uyari\n")
    from filo.erisim import ZamanAsimi
    with pytest.raises(ZamanAsimi):
        t.calistir(s, "sleep 20", 1)
    rc, out, err = t.calistir(s, "head -c 200000 /dev/zero | tr '\\0' x", 10, cikti_siniri=1000)
    assert rc == 0 and len(out) == 1000 and t.kesildi
    bilgi = t.sistem_bilgisi(s)
    assert bilgi["aile"] == "alpine" and bilgi["paket_yoneticisi"] == "apk"


def test_dosya_alma_ozet_dogrulamali(gercek_ajan):
    k, _ = gercek_ajan
    t = _tasiyici(k)
    r = t.dosya_gonder(Envanter()["PB-APP-01"], "motd.txt", "/tmp/filo-sinama-motd", "0640", "filo")
    assert r["durum"] == "basarili", r
    out = lab.dexec(KONTEYNER, "stat -c '%a %U' /tmp/filo-sinama-motd; rm -f /tmp/filo-sinama-motd")[1]
    assert out.strip() == "640 filo"


def test_sahte_imzali_is_reddedilir(gercek_ajan):
    """Kapı kuyruğuna yanlış anahtarla imzalanmış ve gövdesi değiştirilmiş iş konur; ajan çalıştırmaz."""
    k, _ = gercek_ajan
    a = k.ajan_bul("PB-APP-01")
    gercek_is_a = anahtar_turet(k.defter.gizliler()[a["kimlik"]])[1]
    sahte_is_a = anahtar_turet("33" * 32)[1]
    simdi = int(time.time())
    iz = "/tmp/filo-sahte-is-izi"

    def koy(zarf, kimlik):
        with k.kosul:
            k.isler[kimlik] = {"ajan": a["kimlik"], "sunucu": "PB-APP-01", "zarf": zarf, "durum": "bekliyor",
                               "olusturma": time.time(), "sonuc": None, "dosya_yolu": None, "tur": "calistir"}
            k.kuyruk[a["kimlik"]].append(kimlik)
            k.kosul.notify_all()
    is1 = {"kimlik": "sahte-1", "ajan": a["kimlik"], "tur": "calistir", "betik": f"touch {iz}", "zaman_asimi": 5,
           "cikti_siniri": 1000, "kullanici": "filo", "olusturma": simdi, "gecerlilik": simdi + 60}
    koy(is_zarfi(sahte_is_a, is1), "sahte-1")
    is2 = {**is1, "kimlik": "sahte-2", "betik": "echo zararsiz"}
    z2 = is_zarfi(gercek_is_a, is2)
    z2["govde"] = z2["govde"].replace("echo zararsiz", f"touch {iz}")   # imza sonrası gövde değişti
    koy(z2, "sahte-2")
    for kimlik in ("sahte-1", "sahte-2"):
        son = time.time() + 15
        while time.time() < son and k.isler[kimlik]["durum"] != "bitti":
            time.sleep(0.3)
        assert k.isler[kimlik]["sonuc"]["durum"] == "reddedildi", k.isler[kimlik]
    assert lab.dexec(KONTEYNER, f"test -e {iz} && echo var || echo yok")[1].strip() == "yok"
