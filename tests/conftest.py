import json
import pathlib
import shutil
import sys

import pytest

KOK = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK))

from filo.denetim import Denetim  # noqa: E402
from filo.envanter import Envanter  # noqa: E402
from filo.erisim import Durdurma, Erisilemedi, ZamanAsimi  # noqa: E402


def pytest_configure(config):
    config.addinivalue_line("markers", "lab: Docker laboratuvarı ister; laboratuvar yoksa atlanır")


def pytest_collection_modifyitems(config, items):
    from filo import lab
    if not any("lab" in i.keywords for i in items):
        return
    neden = None
    if not lab.lab_var():
        neden = "laboratuvar ayakta değil (python -m filo lab kur)"
    else:
        # D0-b: bench koşusu laboratuvarı kullanırken laboratuvar sınamaları konteynerleri durdurup yeniden yaratır ve
        # koşunun hakemini yanıltır. Kilit başka bir canlı süreçteyse laboratuvar sınamaları atlanır.
        sahibi = lab.lab_kilidi_kimde()
        if sahibi:
            neden = f"laboratuvar başka bir süreçte kullanılıyor: {sahibi.get('amac')} (pid {sahibi.get('pid')})"
        else:
            lab.lab_kilidi_al("pytest laboratuvar sınamaları")
            config._filo_lab_kilidi = True
    if neden:
        atla = pytest.mark.skip(reason=neden)
        for i in items:
            if "lab" in i.keywords:
                i.add_marker(atla)


def pytest_unconfigure(config):
    if getattr(config, "_filo_lab_kilidi", False):
        from filo import lab
        lab.lab_kilidi_birak()


def _canli_ajanlar():
    """Çalışan ajan kapısındaki canlı ajanların sunucu adları (kapı kapalıysa boş küme)."""
    from filo.ajan_istemci import AjanYok, onbellegi_bosalt, yerel_istek
    onbellegi_bosalt()
    try:
        a = yerel_istek("/yerel/v1/ajanlar", zaman_asimi=3).get("ajanlar", {})
    except AjanYok:
        return set()
    return {ad for ad, x in a.items() if x.get("durum") == "canli"}


@pytest.fixture(scope="session", autouse=True)
def ajan_durumunu_koru(request):
    """Laboratuvar testleri konteynerleri imajdan yeniden yaratır (lab.sifirla) ve kapıdaki ajan kayıtlarını düşürür.
    İkinci turda ana oturum testleri koşunca 8 ajan "kayıtsız" kaldı (C0). Oturum başında canlı olan ajanlar oturum
    sonunda eksikse aynı kapıya yeniden kurulur; böylece testler laboratuvarın ajan durumunu bozmaz."""
    if not getattr(request.config, "_filo_lab_kilidi", False):
        yield                     # laboratuvar sınamaları bu oturumda çalışmıyor: ajanlara dokunulmaz
        return
    onceki = _canli_ajanlar()
    yield
    if not onceki:
        return
    eksik = sorted(onceki - _canli_ajanlar())
    if not eksik:
        return
    from filo import lab
    if not lab.lab_var():
        return
    import concurrent.futures
    from filo.ajan_yonetimi import kur
    env = Envanter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        sonuc = list(ex.map(lambda ad: (ad, kur(env[ad], {})), [a for a in eksik if a in env]))
    # Başarısız kalan kurulum bir kez sırayla yeniden denenir (neden aşağıda yazılır; kök neden D0-c'de düzeltildi)
    sonuc = [(a, r if r["durum"] == "basarili" else kur(env[a], {})) for a, r in sonuc]
    kalan = sorted(onceki - _canli_ajanlar())
    print(f"\n[filo] testlerin düşürdüğü ajanlar yeniden kuruldu: {[a for a, r in sonuc if r['durum'] == 'basarili']}"
          + (f"; hâlâ canlı değil: {kalan}" if kalan else ""))
    for a, r in sonuc:
        if r["durum"] != "basarili":
            print(f"[filo] {a}: {r['durum']} {r.get('neden')} | {(r.get('stdout') or '')[-300:]!r}")


class FakeTasiyici:
    """Betik metnine göre cevap veren sahte taşıyıcı. davranis(sunucu, betik) -> (rc, out, err) ya da istisna."""
    ad = "fake"

    def __init__(self, davranis):
        self.davranis, self.cagrilar = davranis, []

    def calistir(self, sunucu, betik, zaman_asimi=60):
        self.cagrilar.append((sunucu.ad, betik))
        return self.davranis(sunucu, betik)


@pytest.fixture
def envanter():
    return Envanter(KOK / "ayarlar" / "envanter.json")


@pytest.fixture
def denetim(tmp_path):
    return Denetim(tmp_path / "denetim.jsonl")


@pytest.fixture
def durdurma(tmp_path):
    return Durdurma(tmp_path / "DURDUR")


@pytest.fixture
def katalog_dizini(tmp_path):
    hedef = tmp_path / "skills"
    shutil.copytree(KOK / "skills", hedef, ignore=shutil.ignore_patterns("gecmis"))
    return hedef


@pytest.fixture
def onaylar(tmp_path, denetim):
    from filo.politika import Onaylar
    return Onaylar(tmp_path / "onaylar.json", denetim)


def basit_davranis(sunucu, betik):
    if "filo-erisim-ok" in betik:
        return 0, "filo-erisim-ok\n", ""
    return 0, f"{sunucu.ad}\n", ""


@pytest.fixture
def motor_kur(envanter, denetim, durdurma, katalog_dizini, onaylar):
    """motor_kur(davranis, kip='bench', kural=None) -> (motor, fake_tasiyici)"""
    from filo.beceri import Katalog
    from filo.motor import BeceriMotoru
    from filo.politika import Politika
    from filo.yurutme import Yurutucu

    def kur(davranis=basit_davranis, kip="bench", kural=None, yeniden=0):
        t = FakeTasiyici(davranis)
        y = Yurutucu(envanter, denetim=denetim, durdurma=durdurma, tasiyici_fn=lambda s: t)
        k = Katalog(katalog_dizini, denetim=denetim)
        p = Politika(kip, bench_kurali=kural or {"varsayilan": "onayla"}, onaylar=onaylar, denetim=denetim)
        return BeceriMotoru(k, envanter, y, p, denetim=denetim, yeniden_deneme=yeniden), t
    return kur


__all__ = ["FakeTasiyici", "Erisilemedi", "ZamanAsimi", "json"]
