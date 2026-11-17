"""Filo komut satırı.

    python -m filo lab kur|durum|sifirla|kapat|depo-derle [--sunucu debian el9 alpine]
    python -m filo envanter [--hedef "PA*"]
    python -m filo calistir --hedef "PA*" --komut "hostname; uname -r" [--zaman-asimi 60]
    python -m filo winrm-kontrol
    python -m filo beceri liste|goster|gecmis|fark|geri-al|sinifla
    python -m filo is --hedef ... --beceri ... [--param k=v] [--kuru] [--onayla]
    python -m filo talep "metin" --ajan kalfa|kaptan --baglanti <ad> [--onayla]
    python -m filo baglanti liste|sina|modeller
    python -m filo web [--port 8790]
    python -m filo bench dogrula|kos|rapor
    python -m filo denetim [--dogrula]
    python -m filo durdur [--kaldir]
"""
import argparse
import json
import sys

from . import __version__


def _yaz(veri):
    print(json.dumps(veri, ensure_ascii=False, indent=2, default=str))


def _tablo(sonuclar):
    print(f"{'SUNUCU':<13} {'DURUM':<12} {'KOD':>4} {'SÜRE':>6} {'DNM':>3} {'YOL':<6} ÇIKTI")
    for r in sonuclar:
        cikti = (r.get("stdout") or r.get("neden") or r.get("stderr") or "").strip().replace("\n", " | ")
        etiket = " [öykünme]" if r.get("oykunme") else ""
        etiket += " [kesildi]" if r.get("kesildi") else ""
        etiket += f" [{r['tasiyici_notu']}]" if r.get("tasiyici_notu") else ""
        kod = "" if r.get("cikis_kodu") is None else r["cikis_kodu"]
        print(f"{r['sunucu']:<13} {r['durum']:<12} {kod!s:>4} {r.get('sure', 0):>6} {r.get('deneme', 0):>3} "
              f"{r.get('tasiyici') or '-':<6} {cikti[:84]}{etiket}")


def komut_lab(a):
    from . import lab
    if a.eylem == "kur":
        tamam, disarida = lab.kur(insa=not a.insa_etme)
        print(f"laboratuvar hazır: {len(tamam)} sunucu erişilebilir" + (f", erişilemeyen: {[r['sunucu'] for r in disarida]}" if disarida else ""))
        return 0 if not disarida else 1
    if a.eylem == "durum":
        d = lab.durum()
        print(f"docker: {'çalışıyor' if d['docker'] else 'ÇALIŞMIYOR'}   mailpit: {'hazır' if d['mailpit'] else 'yok'}")
        for k in d["konteynerler"]:
            print(f"  {k['ad']:<20} {k['durum']:<10} {k['bilgi']}")
        if d["konteynerler"] and a.erisim:
            from .envanter import Envanter
            from .yurutme import Yurutucu
            adlar = [s.ad for s in lab.lab_sunuculari()]
            tamam, disarida = Yurutucu(Envanter()).erisim_sinamasi(adlar, zaman_asimi=10)
            print(f"ssh erişimi: {len(tamam)}/{len(adlar)}" + (f"  erişilemeyen: {[r['sunucu'] for r in disarida]}" if disarida else ""))
        return 0
    if a.eylem == "sifirla":
        tamam, disarida = lab.sifirla(a.sunucu or None)
        print(f"sıfırlandı: {len(tamam)} sunucu erişilebilir")
        return 0
    if a.eylem == "yeni-sunucu":
        if not a.ad:
            print("tanımlı yeni sunucular: " + ", ".join(sorted(lab.YENI_SUNUCULAR))
                  + "\nAçık olanlar: " + (", ".join(lab.ek_sunucular()) or "yok"))
            return 0
        if a.kaldir:
            lab.yeni_sunucu_kaldir(a.ad)
            print(f"{a.ad.upper()} kapatıldı ve envanterden çıkarıldı")
            return 0
        ok, msg = lab.yeni_sunucu(a.ad)
        print(msg)
        return 0 if ok else 1
    if a.eylem == "depo-derle":
        # D1: yerel paket deposunu üretir (bir kez internet ister); ardından imajlar yeniden kurulur (lab kur)
        lab.depo_derle(a.sunucu or None)
        print("depo üretildi: lab/depo/srv (imajları yeniden kurmak için: python -m filo lab kur)")
        return 0
    if a.eylem == "kapat":
        ok, msg = lab.kapat()
        print("laboratuvar kapatıldı" if ok else f"kapatılamadı: {msg}")
        return 0 if ok else 1


def komut_envanter(a):
    from .envanter import Envanter
    env = Envanter()
    sunucular = env.sec(a.hedef) if a.hedef else list(env.sunucular.values())
    for s in sunucular:
        print(f"{s.ad:<13} {s.os:<8} {s.aile:<8} {s.tasiyici:<7} {','.join(s.gruplar):<18} "
              f"{' '.join(f'{k}={v}' for k, v in s.oznitelikler.items())}")
    return 0


def komut_calistir(a):
    from .denetim import DENETIM
    from .envanter import Envanter
    from .erisim import salt_okur_denetle
    from .yurutme import Yurutucu, ozetle
    neden = salt_okur_denetle(a.komut)
    if neden:
        DENETIM.yaz("ret", kaynak="calistir", komut=a.komut, neden=neden)
        print(f"reddedildi: {neden}\n(komut çalıştır yalnız salt-okur komutları kabul eder; değişiklik becerilerle yapılır)")
        return 2
    env = Envanter()
    liste = env.dondur(a.hedef)
    print(f"hedef (donduruldu {liste['zaman']}): {', '.join(liste['sunucular'])}")
    is_kimligi = DENETIM.yaz("is_basladi", kaynak="calistir", komut=a.komut, hedef=liste,
                             zaman_asimi=a.zaman_asimi)["_ozet"]
    y = Yurutucu(env, eszamanli=a.esz)
    sonuc = y.is_yurut(liste["sunucular"], a.komut, a.zaman_asimi, a.yeniden, is_kimligi=is_kimligi)
    oz = ozetle(sonuc)
    DENETIM.yaz("is_bitti", is_kimligi=is_kimligi, ozet=oz)
    if a.json:
        _yaz({"hedef": liste, "sonuclar": sonuc, "ozet": oz})
    else:
        _tablo(sonuc)
        print(f"özet: {oz['basarili']}/{oz['toplam']} başarılı, hatalı {oz['hatali']}, zaman aşımı {oz['zaman_asimi']}, "
              f"erişilemedi {oz['erisilemedi']}, iptal {oz['iptal']}" + (f", öykünme {oz['oykunme']}" if oz["oykunme"] else ""))
    return 0 if oz["basarili"] == oz["toplam"] else 1


def komut_winrm(a):
    from .erisim import winrm_kontrol
    r = winrm_kontrol()
    for x in r["adimlar"]:
        print(f"[{'tamam' if x['tamam'] else 'EKSİK'}] {x['sinama']}: {x['sonuc']}")
    if r["hazir"]:
        print("WinRM hazır: Windows hedefleri gerçek sunucuda çalışır.")
        return 0
    print("\nWinRM hazır değil; Windows hedefleri 'öykünme' etiketiyle öykünücüden cevaplanır.")
    print("Eksik: " + "; ".join(r["eksik"]))
    print("\nKullanıcının çalıştıracağı komutlar:")
    for k in r["komutlar"]:
        print("  " + k)
    return 1


def komut_denetim(a):
    from .denetim import DENETIM
    if a.dogrula:
        ok, n, bozuk = DENETIM.dogrula()
        print(f"zincir {'sağlam' if ok else 'BOZUK (satır %s)' % bozuk}, {n} satır")
        return 0 if ok else 1
    for r in DENETIM.oku(a.limit)[::-1]:
        govde = {k: v for k, v in r.items() if k not in ("zaman", "tur", "_onceki", "_ozet")}
        print(f"{r['zaman']} {r['tur']:<16} {json.dumps(govde, ensure_ascii=False, default=str)[:160]}")
    return 0


def komut_durdur(a):
    from .denetim import DENETIM
    from .erisim import DURDURMA
    if a.kaldir:
        DURDURMA.kaldir()
        DENETIM.yaz("durdurma_kaldirildi", kaynak="komut_satiri")
        print("durdurma kaldırıldı")
    else:
        n = DURDURMA.bas("komut satırı")
        DENETIM.yaz("durdurma", kaynak="komut_satiri", oldurulen=n)
        print(f"durdurma düğmesi basıldı ({n} süreç kesildi); kaldırmak için: python -m filo durdur --kaldir")
    return 0


def ana(argv=None):
    p = argparse.ArgumentParser(prog="filo", description=f"Filo {__version__}: sunucu ve runbook otomasyonu harness'i")
    alt = p.add_subparsers(dest="komut", required=True)

    x = alt.add_parser("lab", help="Docker laboratuvarı")
    x.add_argument("eylem", choices=["kur", "durum", "sifirla", "kapat", "yeni-sunucu", "depo-derle"])
    x.add_argument("ad", nargs="?", help="yeni-sunucu: açılacak sunucu (PA-WEB-02, PB-APP-02)")
    x.add_argument("--kaldir", action="store_true", help="yeni-sunucu: kapat ve envanterden çıkar")
    x.add_argument("--insa-etme", action="store_true", help="kurarken imajları yeniden kurma")
    x.add_argument("--erisim", action="store_true", help="durumda SSH erişimini de sına")
    x.add_argument("--sunucu", nargs="*", help="sifirla: yalnız bu sunucular")
    x.set_defaults(f=komut_lab)

    x = alt.add_parser("envanter", help="sunucuları listele")
    x.add_argument("--hedef")
    x.set_defaults(f=komut_envanter)

    x = alt.add_parser("calistir", help="salt-okur komutu hedef sunucularda çalıştır")
    x.add_argument("--hedef", required=True, help='ör. "PA*", "grup:web", "os:linux ortam=test !PA-DB-01"')
    x.add_argument("--komut", required=True)
    x.add_argument("--zaman-asimi", type=int, default=60, help="sunucu başına saniye (zorunlu, varsayılan 60)")
    x.add_argument("--esz", type=int, default=8, help="eşzamanlı sunucu sayısı")
    x.add_argument("--yeniden", type=int, default=2, help="başarısızlar için en çok yeniden deneme")
    x.add_argument("--json", action="store_true")
    x.set_defaults(f=komut_calistir)

    x = alt.add_parser("winrm-kontrol", help="bu makinedeki WinRM'i sına (ayar değiştirmez)")
    x.set_defaults(f=komut_winrm)

    x = alt.add_parser("denetim", help="denetim izi")
    x.add_argument("--limit", type=int, default=40)
    x.add_argument("--dogrula", action="store_true")
    x.set_defaults(f=komut_denetim)

    x = alt.add_parser("durdur", help="durdurma düğmesi")
    x.add_argument("--kaldir", action="store_true")
    x.set_defaults(f=komut_durdur)

    from . import cli_ek
    cli_ek.ekle(alt)

    a = p.parse_args(argv)
    from .motor import PlanHatasi
    try:
        return a.f(a) or 0
    except PlanHatasi as e:              # plan reddi (ör. izinli olmayan çalıştırma kimliği): hiçbir şey çalışmadı
        print(f"plan reddedildi: {e}\nHiçbir sunucuda işlem yapılmadı.")
        return 2


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(ana())
