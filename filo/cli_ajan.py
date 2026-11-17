"""Komut satırı: talep (Kalfa/Kaptan), bağlantılar, sabit akışlar, web, bench."""
import json


def _ajan_kur(ajan, baglanti, onayla, model=None):
    from .cli_ek import motor_kur
    from .gateway import baglan
    from .kalfa import Kalfa
    from .kaptan import Kaptan
    motor = motor_kur("komut_satiri" if onayla else "etkilesimli")
    model = model or baglan(baglanti)
    sinif = Kalfa if ajan == "kalfa" else Kaptan
    return sinif(model, motor), model


def kayit_yaz(k, ayrinti=False):
    print(f"\n[{k.ajan}] iş {k.kimlik}: {k.durum}")
    if k.plan:
        p = k.plan.get("ana") or k.plan
        hedef = (p.get("hedef") or {}).get("sunucular") if isinstance(p.get("hedef"), dict) else None
        print(f"plan: {' → '.join(k.plan.get('adimlar') or [p.get('beceri', '')])}" + (f"  hedef: {', '.join(hedef)}" if hedef else ""))
    for g in k.gerekce:
        son = g["denemeler"][-1] if g["denemeler"] else {}
        print(f"  model · {g['soru']}: {json.dumps(g.get('sonuc'), ensure_ascii=False)[:140]}"
              + (f"  ({len(g['denemeler'])} deneme)" if len(g["denemeler"]) > 1 else "")
              + (f"  [son hata: {son.get('hata')}]" if g.get("sonuc") is None and son.get("hata") else "")
              + (f"  [kod: {g['kod_notu']}]" if g.get("kod_notu") else ""))
    for d in k.degisiklikler:
        print(f"  değişiklik: {d['kayit']} {d['ad']} v{d['eski_surum']}→v{d['yeni_surum']} risk {d['risk_onceki']}→{d['risk_yeni']}")
        if ayrinti:
            print(d["fark"])
    if k.rapor:
        print("\nRapor:\n" + k.rapor)
    if k.yorum:
        print("\nModel yorumu (kod denetiminden geçmez, öneridir):\n" + k.yorum)
    print(f"\nmodel çağrısı: {k.model_cagri}")


def komut_talep(a):
    ajan, model = _ajan_kur(a.ajan, a.baglanti, a.onayla)
    if a.plan:
        k = ajan.planla(a.metin)
    else:
        k = ajan.calistir(a.metin)
    kayit_yaz(k, a.ayrinti)
    return 0 if k.durum in ("bitti", "plan_hazir") else 1


def komut_baglanti(a):
    from .gateway import Baglantilar, Model
    b = Baglantilar()
    if a.eylem == "liste":
        v = b.varsayilan()
        for x in b.hepsi():
            o = b.ozet(x)
            print(f"{'*' if x['ad'] == v else ' '} {x['ad']:<18} {x['tur']:<14} {x.get('model') or '(model yok)':<24} "
                  f"{x.get('adres', '')}  anahtar: {'var (' + o['anahtar_kaynagi'] + ')' if o['anahtar_var'] else 'yok'}")
        return 0
    profil = b.getir(a.ad or b.varsayilan())
    m = Model(profil, b.anahtar(profil))
    if a.eylem == "modeller":
        for x in m.modeller():
            print(x)
        return 0
    r = m.sina(sohbetle=a.sohbet)
    print(json.dumps(r, ensure_ascii=False, indent=2))
    return 0 if r["tamam"] else 1


def komut_akis(a):
    from .cli_ek import motor_kur
    from .kaptan import akis_listesi, akis_yurut
    if a.eylem == "liste":
        for x in akis_listesi():
            print(f"{x['ad']:<50} {' → '.join(s['beceri'] for s in x['adimlar'])}   ({x['talep'][:60]})")
        return 0
    k = akis_yurut(motor_kur("komut_satiri" if a.onayla else "etkilesimli"), a.ad, a.hedef)
    kayit_yaz(k)
    return 0 if k.durum == "bitti" else 1


def komut_web(a):
    from .web import serve
    serve(port=a.port, ajan_kapisi=not a.ajan_kapisi_yok)
    return 0


def komut_teslim(a):
    """Teslim politikaları: liste, denetle, baslat (elle; normalde yeni ajan kaydı başlatır)."""
    from .teslim import Teslim, motor_olustur, politika_denetle, politikalar, profil_bul, teslim_kaydet
    pol = politikalar()
    motor = motor_olustur("komut_satiri" if a.onayla else "etkilesimli")
    if a.eylem == "liste":
        for k in pol["kurallar"]:
            print(f"kural: {k.get('ad_kalibi') or 'grup:' + k.get('grup', '')} -> {k['profil']}")
        for ad, p in pol["profiller"].items():
            print(f"\n{ad}: {p.get('baslik')}  (yarıda kalırsa: {p.get('yarida_kalirsa', 'insan')}"
                  + (f", Kaptan düzeyi {p.get('kaptan_inisiyatif')}" if p.get("yarida_kalirsa") == "kaptan" else "") + ")")
            for x in p["adimlar"]:
                print(f"   - {x['beceri']} {json.dumps(x.get('parametre') or {}, ensure_ascii=False)}"
                      + ("  [ön onaylı]" if x.get("on_onayli") else ""))
        print("\nSunucular:")
        for s in motor.envanter.sunucular.values():
            print(f"   {s.ad:<13} -> {profil_bul(s, pol)[0] or '-'}")
        return 0
    if a.eylem == "denetle":
        h = politika_denetle(pol, motor.katalog)
        print("politika geçerli" if not h else "\n".join(h))
        return 0 if not h else 1
    if not a.sunucu:
        raise SystemExit("sunucu adı gerekli")
    from .gateway import baglan
    t = Teslim(motor, a.sunucu, a.profil, pol, model_fabrikasi=lambda: baglan(a.baglanti), neden="operatör başlattı")
    k = t.yurut()
    teslim_kaydet(a.sunucu, t.profil_adi, k)
    kayit_yaz(k)
    return 0 if k.durum == "bitti" else 1


def komut_ajan(a):
    """Filo ajanı (Go): derle, kapı, durum, belirteç, kur/onar/kaldır (beceri motoru üzerinden, onay kurallarıyla)."""
    if a.eylem == "derle":
        from .ajan_yonetimi import CIKTI, derle
        rc, cikti = derle(testler=not a.testsiz)
        print(cikti[-6000:])
        print(f"\n{'derlendi: ' + str(CIKTI) if rc == 0 else 'DERLEME BAŞARISIZ (çıkış ' + str(rc) + ')'}")
        return rc
    if a.eylem == "kapi":
        from .ajan_kapisi import calistir
        from .teslim import kapi_dinleyicisi
        calistir(a.port, kayit_dinleyici=kapi_dinleyicisi())
        return 0
    if a.eylem == "durum":
        from .ajan_istemci import ajan_durumlari, yerel_istek, AjanYok
        try:
            yerel_istek("/yerel/v1/ajanlar", zaman_asimi=3)
        except AjanYok as e:
            print(f"ajan kapısı çalışmıyor ({e}); bütün işler SSH'tan gider")
            return 1
        from .envanter import Envanter
        d = ajan_durumlari(onbellek_sn=0)
        for s in Envanter().sunucular.values():
            x = d.get(s.ad)
            if x:
                print(f"{s.ad:<13} {x['durum']:<9} {x['ajan']:<18} v{x.get('surum') or '?':<7} son kalp {x.get('son_kalp') or '-'}"
                      f"  {(x.get('sistem') or {}).get('dagitim_ad', '')}")
            elif s.tasiyici == "ssh":
                print(f"{s.ad:<13} kayıtsız  (iş SSH'tan gider)")
            else:
                print(f"{s.ad:<13} kayıtsız  (taşıyıcı: {s.tasiyici})")
        return 0
    if a.eylem == "belirtec":
        from .ajan_istemci import yerel_istek
        if not a.hedef:
            raise SystemExit("--hedef <sunucu adı> gerekli")
        print(yerel_istek("/yerel/v1/belirtec", {"sunucu": a.hedef})["belirtec"])
        print("(tek kullanımlıktır ve yalnız bu kez gösterilir)")
        return 0
    from .cli_ek import _adim_yaz, motor_kur
    beceri = {"kur": "ajan_kur", "onar": "ajan_onar", "kaldir": "ajan_kaldir"}[a.eylem]
    if not a.hedef:
        raise SystemExit("--hedef gerekli (ör. \"PA*\")")
    motor = motor_kur("komut_satiri" if a.onayla else "etkilesimli")
    plan = motor.plan(beceri, {}, a.hedef, talep=f"komut satırı: ajan {a.eylem}", ajan="operatör")
    print(f"plan: {beceri} risk {plan['risk']}, hedef: {', '.join(plan['hedef']['sunucular'])}")
    adim = motor.yurut(plan, {"adimlar": []})
    _adim_yaz(adim)
    if adim["durum"] == "onay_bekliyor":
        print(f"onay bekleniyor: python -m filo onay ver {adim['onay']['kimlik']}  (ya da --onayla)")
    return 0 if adim["durum"] == "basarili" else 1


def komut_bench(a):
    from .bench import kos
    return kos.cli(a)


def ekle(alt):
    x = alt.add_parser("talep", help="doğal dilde talep: Kalfa ya da Kaptan")
    x.add_argument("metin")
    x.add_argument("--ajan", choices=["kalfa", "kaptan"], default="kalfa")
    x.add_argument("--baglanti", help="ayarlar/baglantilar.json içindeki ad (varsayılan bağlantı)")
    x.add_argument("--onayla", action="store_true", help="düzey 3+ için operatör onayını şimdi ver")
    x.add_argument("--plan", action="store_true", help="yalnız planla, yürütme")
    x.add_argument("--ayrinti", action="store_true")
    x.set_defaults(f=komut_talep)

    x = alt.add_parser("baglanti", help="model bağlantıları")
    x.add_argument("eylem", choices=["liste", "sina", "modeller"])
    x.add_argument("ad", nargs="?")
    x.add_argument("--sohbet", action="store_true", help="sınamada kısa bir JSON sorusu da sor")
    x.set_defaults(f=komut_baglanti)

    x = alt.add_parser("akis", help="Kaptan'ın kaydettiği sabit akışlar")
    x.add_argument("eylem", choices=["liste", "calistir"])
    x.add_argument("ad", nargs="?")
    x.add_argument("--hedef")
    x.add_argument("--onayla", action="store_true")
    x.set_defaults(f=komut_akis)

    x = alt.add_parser("web", help="arayüz (yalnız 127.0.0.1)")
    x.add_argument("--port", type=int, default=8790)
    x.add_argument("--ajan-kapisi-yok", action="store_true", help="ajan kapısını bu süreçte başlatma")
    x.set_defaults(f=komut_web)

    x = alt.add_parser("teslim", help="yeni sunucu teslim politikaları")
    x.add_argument("eylem", choices=["liste", "denetle", "baslat"])
    x.add_argument("sunucu", nargs="?")
    x.add_argument("--profil")
    x.add_argument("--baglanti", help="yarıda kalırsa Kaptan'ın kullanacağı model bağlantısı")
    x.add_argument("--onayla", action="store_true", help="ön onaylı olmayan düzey 3 adımlar için onayı şimdi ver")
    x.set_defaults(f=komut_teslim)

    x = alt.add_parser("ajan", help="Filo ajanı (Go): derle, kapı, durum, belirteç, kur, onar, kaldır")
    x.add_argument("eylem", choices=["derle", "kapi", "durum", "belirtec", "kur", "onar", "kaldir"])
    x.add_argument("--hedef")
    x.add_argument("--port", type=int)
    x.add_argument("--onayla", action="store_true", help="düzey 3 işlem için operatör onayını şimdi ver")
    x.add_argument("--testsiz", action="store_true", help="derle: Go testlerini atla")
    x.set_defaults(f=komut_ajan)

    x = alt.add_parser("bench", help="Filo Admin Bench")
    x.add_argument("eylem", choices=["dogrula", "kos", "rapor", "liste"])
    x.add_argument("--senaryo", nargs="*", help="yalnız bu senaryo kimlikleri")
    x.add_argument("--seviye", choices=["temel", "orta", "ileri"])
    x.add_argument("--kol", nargs="*", choices=["yardimsiz", "kalfa", "kaptan"])
    x.add_argument("--baglanti")
    x.add_argument("--kosu", help="sonuç dizini adı")
    x.set_defaults(f=komut_bench)
