"""İki ajanın ortak dar soruları. Küçük model için tasarlandı: kısa bağlam, her çağrıda tek karar, seçenekleri kod
daraltır, cevap kodla doğrulanır, uymazsa hata metniyle bir kez daha sorulur (onarım döngüsü).

Kod daraltmaları:
  - aday beceriler: talep sözcükleri ile beceri etiketleri/başlığı arasındaki kök örtüşmesiyle ilk K beceri
  - hedef: model bir seçici yazar; kod envanterde çözer, boş ya da geçersizse hatayla geri sorar
  - parametre: şemadan geçmeyen ya da talepte geçmeyen (uydurulmuş) servis/paket/kullanıcı/e-posta/yol değeri reddedilir
  - biçim ve e-posta: talepte adı geçen biçimler ve talepteki adresler seçenek olur; tek seçenek varsa soru sorulmaz
"""
import json
import re

from .beceri import EPOSTA, SemaHatasi, parametre_dogrula, secenekler
from .envanter import SeciciHatasi
from .gateway import sor_json

SISTEM = ("Sen Filo adlı sunucu otomasyon harness'inin içinde çalışan bir yönetici asistansın. Her soruda yalnız "
          "istenen tek JSON nesnesini yaz; açıklama, kod bloğu ya da başka metin ekleme.")
TR = str.maketrans("çğıöşüÇĞİÖŞÜâîû", "cgiosuCGIOSUaiu")
BICIM_SOZ = {"xml": ["xml"], "csv": ["csv", "excel"], "json": ["json"], "html": ["html", "web sayfa"]}


def normal(metin):
    return str(metin).replace("İ", "i").replace("I", "ı").lower().translate(TR)


def kokler(metin, n=4):
    # 4 harflik kök: Türkçe ek ve ünsüz yumuşaması (betik -> betiğini) 5 harfte kökü bozar
    return {w[:n] for w in re.findall(r"[a-z0-9]+", normal(metin)) if len(w) >= 3}


# Neredeyse her talepte geçen sözcüklerin kökleri aday puanına girmez (ikinci koşu: "sunucularında", "sonucu",
# "adresine gönder" gibi sözcükler açıklaması uzun becerileri her talepte aday yapıyordu)
GENEL_KOKLER = {w[:4] for w in re.findall(r"[a-z0-9]+", "sunucu sunucularda sunucusunda sonucu sonuc adresine gonder "
                                                         "bildir posta eposta ops lab yerel ile icin olarak yap baslayan "
                                                         "adi butun tum talep filo kontrol") if len(w) >= 3}


def aday_beceriler(katalog, talep, k=6, turler=("uzak", "zincir", "yonetim"), haric=()):
    """Talebe en yakın K beceri (kod daraltması)."""
    tk = kokler(talep) - GENEL_KOKLER
    puan = []
    for ad, t in katalog.beceriler.items():
        if t["tur"] not in turler or ad in haric:
            continue
        bk = kokler(" ".join(t.get("etiketler", [])) + " " + t["baslik"] + " " + ad.replace("_", " "))
        ak = kokler(t["aciklama"])
        s = 3 * len(tk & bk) + len(tk & ak)
        if ad == "betik_calistir":
            # Betik kütüphanesindeki bir betiğin adı/açıklaması talebe uyuyorsa betik_calistir öne çıkar (ikinci koşu
            # T09: "dinleyen portları listele" talebinde betik adı geçmediği için aday bile olmadı)
            for b in secenekler({"kaynak": "betikler"}):
                try:
                    m = katalog.betik_meta(b)
                except (OSError, ValueError):
                    continue
                s += 3 * len(tk & kokler(b.replace("_", " ") + " " + m.get("aciklama", "")))
        puan.append((s, ad))
    puan.sort(key=lambda x: (-x[0], x[1]))
    # Sıfır puanlı beceri aday olmaz: ikinci koşuda listeyi alfabetik dolduran ajan_kur, jq_kur_ve_bildir gibi ilgisiz
    # beceriler modelin akışına girmeye çalıştı. Hiç eşleşme yoksa eski davranış (ilk K) korunur.
    pozitif = [(s, ad) for s, ad in puan if s > 0]
    return [ad for s, ad in (pozitif or puan)[:k]]


# Beceri adının ilk sözcüğü çok genel olduğunda (ör. "CSV dosyası" → dosya_dagit) dayanak sayılmaz; etiketlere bakılır.
GENEL_AD_SOZ = {"dosya"}


def dayanak_var(katalog, ad, talep):
    """Akıştaki bir adımın talepte dayanağı var mı (kod daraltması: küçük modeller istenmeyen adım ekler — ör. "jq kur"
    talebine ajan kurulumu ve standart teslim). Salt-okur uzak adım serbest. Değiştiren adım: becerinin adındaki ilk
    sözcüğün kökü ya da 5+ harfli bir etiketi talepte geçmeli. Dönüştürme: talepte bir biçim adı. E-posta: talepte
    adres ya da posta sözcüğü."""
    n = normal(talep)
    if ad == "sonucu_donustur":
        return any(s in n for sozler in BICIM_SOZ.values() for s in sozler)
    if ad == "eposta_gonder":
        return "@" in talep or any(w in n for w in ("posta", "mail", "bildir"))
    t = katalog[ad]
    if t["tur"] in ("uzak", "zincir") and katalog.etkin_risk(t)[0] <= 1:
        return True          # salt-okur adım zarar vermez; denetim sunucuyu değiştiren adımlar içindir
    if ad == "betik_calistir" and any(normal(b) in n for b in secenekler({"kaynak": "betikler"})):
        return True
    if not talep_eylemleri(katalog, talep):
        # Talepte hiçbir değiştirici eylem ifadesi yoksa (ör. yalnız "durumunu kontrol et") değiştiren adımın dayanağı
        # yoktur. Üçüncü tur tam koşusu O05: "servis" sözcüğü beceri adının ilk sözcüğüyle eşleşti, akışa
        # servis_baslat ve servis_yeniden_baslat girdi, sağlam sunucuda servis yeniden başlatıldı.
        return False
    if ad.split("_")[0] not in GENEL_AD_SOZ and kokler(ad.split("_")[0]) & kokler(talep):
        return True
    if any(a.get("desen") in UYDURMA_DENETIMI and "varsayilan" not in a for a in (t.get("girdi") or {}).values()) \
            and talep_eylemleri(katalog, talep):
        # varsayılansız paket/servis/kullanıcı parametresi talepte geçmek zorunda (parametre denetimi). Üçüncü tur tam
        # koşusu O05: yalnız "durumunu kontrol et" diyen talepte servis adı geçtiği için servis_baslat ve
        # servis_yeniden_baslat dayanaklı sayıldı, sağlam sunucuda servis yeniden başlatıldı. Artık talepte bir
        # değiştirici eylem ifadesi de olmalı.
        return True
    return any(len(normal(e)) >= 5 and normal(e) not in GENEL_AD_SOZ and normal(e) in n for e in t.get("etiketler", []))


# ---------------------------------------------------------------- talepteki değiştirici eylemler (kapsam denetimi)
# Kalfa tek beceri yürütür. İkinci koşuda O11'de model "talepte başka iş var mı?" sorusuna "yok" dedi ve Kalfa işin
# yarısını yapıp "başarılı" raporladı (sahte başarı). Kapsamı artık kod da çıkarır: talepteki değiştirici eylem
# ifadeleri, o eylemi yapan becerilere eşlenir; yürütülen beceri (ve zincir adımları) bir eylemi kapsamıyorsa iş
# 'kismi' biter. Model cevabı yalnız EK bilgi olabilir; kodun bulduğu eksiği silemez.
EYLEM_KALIPLARI = (
    ("yeniden başlatma", r"yeniden baslat\w*|\brestart\w*",
     {"servis_yeniden_baslat", "ajan_onar"}),
    ("başlatma", r"(?<!yeniden )\bbaslat(?!ma\b)\w*|\bstart\b",
     {"servis_baslat", "servis_yeniden_baslat", "ajan_onar"}),
    ("dosya dağıtma", r"\bgeri koy\w*|\byerine koy\w*|\bdagit\w*|\bkopyala\w*",
     {"dosya_dagit"}),
    ("kurulum", r"\b(kur|kurun|kursun|kurulsun|kurmak|kurar|kuruver|yukle|yukleyin|yuklesin|install)\b",
     {"paket_kur", "ajan_kur", "depo_onar"}),
    ("onarım", r"\bonar\w*",
     {"paket_onar", "depo_onar", "ajan_onar"}),
    ("kullanıcı açma", r"\b(kullanici|hesa[pb])\w* (ac|acin|acsin|olustur\w*|ekle\w*)\b",
     {"kullanici_ac"}),
    ("temizleme", r"\btemizle\w*|\bsil\b|\bsilin\w*",
     {"gecici_dosya_temizle", "ajan_kaldir"}),
    ("kaldırma", r"\b(kaldir|kaldirin|kaldirilsin)\b",
     {"ajan_kaldir"}),
    ("teslim", r"\bteslim (et|edin|edilsin|edil)\w*|\bhazirla\w*",
     {"teslim_uygula", "standart_sunucu_teslimi"}),
)


def talep_eylemleri(katalog, talep):
    """Talepteki değiştirici eylemler: [(eylem adı, eşleşen ifade, o eylemi yapan katalog becerileri)]."""
    n = normal(talep)
    out = []
    for ad, kalip, beceriler in EYLEM_KALIPLARI:
        m = re.search(kalip, n)
        var = {b for b in beceriler if b in katalog}
        if m and var:
            out.append((ad, m.group(0), var))
    return out


def kapsanan_beceriler(katalog, ad):
    """Bir becerinin kapsadığı beceriler: kendisi + zincir adımları (iç içe) + teslim profillerinin adımları."""
    out, yigin = set(), [ad]
    while yigin:
        b = yigin.pop()
        if b in out or b not in katalog:
            continue
        out.add(b)
        yigin += [a["beceri"] for a in katalog[b].get("adimlar", [])]
    if "teslim_uygula" in out:          # teslim profilleri paket kurar, kullanıcı açar, servis başlatır, dosya dağıtır
        out |= {"paket_kur", "kullanici_ac", "servis_baslat", "dosya_dagit", "depo_onar"}
    return out


def kapsam_eksigi(katalog, talep, yurutulen):
    """Talepteki değiştirici eylemlerden yürütülen becerilerin hiçbirinin yapmadığı eylemler (kod denetimi)."""
    kapsanan = set()
    for b in yurutulen:
        kapsanan |= kapsanan_beceriler(katalog, b)
    return [f"{ad} ('{ifade}')" for ad, ifade, beceriler in talep_eylemleri(katalog, talep) if not beceriler & kapsanan]


def secenek_satiri(katalog, ad):
    t = katalog[ad]
    parca = []
    for a, al in (t.get("girdi") or {}).items():
        se = secenekler(al) if al.get("kaynak") else []
        parca.append(f"{a} [{', '.join(se)}]" if se else a)
    p = ", ".join(parca) or "parametre yok"
    return f"- {ad}: {t['baslik']}. {t['aciklama']} (parametreler: {p}; risk {katalog.etkin_risk(t)[0]})"


# ---------------------------------------------------------------- beceri seçimi
def beceri_sec(model, katalog, talep, adaylar, iz, soru="Bu talebin ANA işini hangi beceri yapar?", ek=""):
    secenek = list(adaylar) + ["hicbiri"]
    metin = (f"Talep: \"{talep}\"\n{ek}\n{soru} Sonuçları dönüştürme (XML/CSV...) ve e-posta gönderme ayrıca ele "
             f"alınır; onları seçme.\nSeçenekler:\n" + "\n".join(secenek_satiri(katalog, a) for a in adaylar)
             + "\n- hicbiri: listedeki becerilerden hiçbiri bu işi yapmıyor\n\n"
             'JSON: {"secim": "<seçenek adı>", "gerekce": "<tek cümle>"}')

    def dogrula(v):
        s = str(v.get("secim", "")).strip()
        if s not in secenek:
            return None, f"'{s}' seçeneklerden biri değil; şunlardan birini yaz: {secenek}"
        if s != "hicbiri" and not dayanak_var(katalog, s, talep):
            # Değiştiren bir becerinin talepte dayanağı olmalı (ilk koşuda "jq kur ve doğrula" talebine standart teslim
            # zinciri seçildi ve istenmeyen paket/motd değişikliği yapıldı).
            return None, f"{s} sunucuda talebin istemediği değişiklikler yapar; talebin istediği işi yapan beceriyi seç"
        return {"secim": s, "gerekce": str(v.get("gerekce", ""))[:300]}, None
    out = sor_json(model, SISTEM, metin, dogrula, iz=iz, etiket="beceri seçimi")[0]
    if out and out["secim"] == "hicbiri":
        # "hiçbiri" cevabı bir kez sınanır: adı talepteki bir sözcükle eşleşen salt-okur aday varsa model ona özellikle
        # sorulur (ilk koşuda "bekleyen yama sayısı" talebine yama_durumu varken hiçbiri denmişti).
        n = normal(talep)
        aday = next((a for a in adaylar if katalog[a]["tur"] == "uzak" and katalog.etkin_risk(katalog[a])[0] <= 1
                     and (kokler(a.split("_")[0]) & kokler(talep)
                          or any(len(normal(e)) >= 5 and normal(e) in n for e in katalog[a].get("etiketler", [])))), None)
        if aday:
            m2 = (f"Talep: \"{talep}\"\nAday beceri: {secenek_satiri(katalog, aday)}\nBu beceri talebin ana işini "
                  f"(okuma/raporlama kısmını) yapar mı? Dönüştürme ve e-posta ayrıca yapılır.\n"
                  'JSON: {"cevap": "evet" | "hayir", "gerekce": "<tek cümle>"}')
            c = sor_json(model, SISTEM, m2, lambda v: ((str(v.get("cevap")).strip(), None) if str(v.get("cevap", "")).strip()
                                                       in ("evet", "hayir") else (None, "evet ya da hayir yaz")),
                         iz=iz, etiket="beceri seçimi: hiçbiri sınaması")[0]
            if c == "evet":
                return {"secim": aday, "gerekce": f"ilk cevap 'hiçbiri' idi; kod {aday} becerisini önerdi, model doğruladı"}
    return out


# ---------------------------------------------------------------- hedef
def hedef_sor(model, envanter, talep, iz):
    adlar = sorted(envanter.sunucular)
    gruplar = sorted(envanter.gruplar())
    oz = envanter.oznitelik_degerleri()
    metin = (f"Talep: \"{talep}\"\nGörev: talebin hangi sunucuları hedeflediğini bir seçiciyle yaz.\n"
             f"Envanterdeki sunucular: {', '.join(adlar[:80])}{' ...' if len(adlar) > 80 else ''}\n"
             f"Gruplar: {', '.join(gruplar)}\nİşletim sistemi (os): linux, windows. Dağıtım ailesi (aile): debian, rhel, alpine, windows.\n"
             f"Öznitelikler: " + "; ".join(f"{k}={'|'.join(v)}" for k, v in oz.items()) + "\n"
             "Ad kalıbında * joker kullan (ör. adı PA ile başlayanlar: PA*); birden çok kalıp virgülle. Yalnız talepte "
             "açıkça söylenen koşulları yaz; söylenmeyen alanı boş bırak (fazla koşul hedefi daraltır).\n"
             'JSON: {"ad": "", "grup": "", "os": "", "aile": "", "oznitelik": {}, "haric": []}')

    notlar = []

    def dogrula(v):
        if not isinstance(v, dict):
            return None, "bir JSON nesnesi yaz"
        sec = {k: v.get(k) for k in ("ad", "grup", "os", "aile", "oznitelik", "haric") if v.get(k)}
        if isinstance(sec.get("haric"), str):
            sec["haric"] = [x.strip() for x in sec["haric"].split(",") if x.strip()]
        if isinstance(sec.get("oznitelik"), str):
            return None, "oznitelik bir nesne olmalı, ör. {\"ortam\": \"test\"}"
        if isinstance(sec.get("oznitelik"), dict):        # boş değerli öznitelik koşulu bütün sunucuları eler
            sec["oznitelik"] = {k: v for k, v in sec["oznitelik"].items() if v not in (None, "", [])}
            if not sec["oznitelik"]:
                sec.pop("oznitelik")
        # Talepte dayanağı olmayan grup/os/aile/öznitelik koşulunu kod çıkarır (küçük modeller sık ekler ve hedefi
        # sessizce daraltır); çıkarılanlar gerekçe izine yazılır. Ad kalıbı ise talepte geçmek zorundadır.
        desteksiz = kosul_destegi(sec, talep)
        for d in desteksiz:
            k_, _ = d.split("=", 1)
            if k_ in sec:
                sec.pop(k_)
            elif k_ in (sec.get("oznitelik") or {}):
                sec["oznitelik"].pop(k_)
        if "oznitelik" in sec and not sec["oznitelik"]:
            sec.pop("oznitelik")
        cevrim = []
        kaliplar = [x.strip() for x in str(sec.get("ad", "")).split(",") if x.strip()]
        yok = [x for x in kaliplar if normal(x.replace("*", "").replace("?", "")).strip("-") not in normal(talep)]
        if yok:
            # Model talepteki grubu (ör. "web grubu") açık sunucu adlarına çevirmiş olabilir: adların kümesi talepte
            # dayanağı olan bir grubun üyeleriyle aynıysa seçici o gruba çevrilir (ilk koşuda T04 bu yüzden kaldı).
            try:
                adlar = {s.ad for s in envanter.sec({"ad": ",".join(kaliplar)})}
            except SeciciHatasi:
                adlar = set()
            for g, uyeler in envanter.gruplar().items():
                if adlar and set(uyeler) == adlar and not kosul_destegi({"grup": g}, talep):
                    sec.pop("ad")
                    sec["grup"] = g
                    cevrim.append(f"ad listesi {sorted(adlar)} talepteki '{g}' grubuna çevrildi")
                    yok = []
                    break
        if yok:
            gruplar = [g for g in envanter.gruplar() if not kosul_destegi({"grup": g}, talep)]
            return None, (f"ad kalıbı talepte geçmiyor: {yok}; talepteki sunucu adlarını ya da öneklerini kullan"
                          + (f". Talepte grup geçiyor: {gruplar}; \"grup\" alanını kullan" if gruplar else ""))
        if not sec:
            return None, ("talepte dayanağı olan bir koşul yok: " + ", ".join(desteksiz)
                          + ". Talepte geçen sunucu adını/önekini ya da grubu yaz")
        notlar[:] = desteksiz + cevrim
        try:
            secilen = envanter.sec(sec)
        except SeciciHatasi as e:
            return None, str(e)
        if not secilen:
            eleyen = []
            for k_ in [x for x in sec if x != "ad"]:
                tek = {**({"ad": sec["ad"]} if sec.get("ad") else {}), k_: sec[k_]}
                try:
                    if sec.get("ad") and not envanter.sec(tek):
                        eleyen.append(f"{k_}={sec[k_]}")
                except SeciciHatasi:
                    eleyen.append(f"{k_}={sec[k_]}")
            return None, ("bu seçiciye uyan sunucu yok" + (f"; şu koşul(lar) bütün sunucuları eliyor: {eleyen}"
                          if eleyen else "; ad kalıbında * kullandın mı, grup ve öznitelik adları listedekilerden mi?"))
        return sec, None
    deger, kayit = sor_json(model, SISTEM, metin, dogrula, iz=iz, etiket="hedef")
    if deger is not None and notlar:
        kayit["kod_notu"] = f"kod düzeltti: {', '.join(notlar)}"
    return deger


# Grup ve öznitelik değerlerinin talepte hangi sözcüklerle anılabileceği (kod denetimi için eş anlamlılar)
ES_ANLAM = {"app": ["app", "uygulama"], "db": ["db", "veritaban", "veri taban"], "web": ["web"],
            "batch": ["batch", "toplu", "yigin"], "prod": ["prod", "uretim", "canli"], "test": ["test"],
            "uygulama": ["uygulama", "app"], "veritabani": ["veritaban", "db"], "windows": ["windows"],
            "linux": ["linux"], "debian": ["debian"], "rhel": ["rhel", "alma", "rocky", "red hat", "redhat"],
            "alpine": ["alpine"]}


def kosul_destegi(sec, talep):
    """Seçicideki grup/os/aile/öznitelik koşullarından talepte dayanağı olmayanlar (modelin eklediği fazla koşul
    hedefi sessizce daraltır; kod bunu reddeder)."""
    # alt çizgili sözcükler (betik adları gibi) koşula dayanak sayılmaz: "uygulama_surumu" rol=uygulama demek değil
    temiz = re.sub(r"\S+@\S+|https?://\S+|/\S+", " ", normal(talep))   # adres, URL, yol koşula dayanak olmaz
    tum = re.findall(r"[\w-]+", temiz)
    # "uygulama servisi", "uygulama kullanıcısıyla", "webd servisinin": servis/kullanıcı/paket adı rol ya da grup değildir
    # (üçüncü tur duman koşusu: "uygulama servisini yeniden başlat" talebinde rol=uygulama koşulu PA grubunu daralttı).
    sozcukler = [w for i, w in enumerate(tum) if "_" not in w and not (
        i + 1 < len(tum) and re.match(r"(servis|kullanici|paket|hesab|daemon|betig)", tum[i + 1]))]
    metin = " " + " ".join(sozcukler) + " "

    def gecer(deger):
        d = normal(deger)
        adaylar = ES_ANLAM.get(d, [d])
        return any(f" {a}" in metin for a in adaylar)
    eksik = []
    for k in ("grup", "os", "aile"):
        if sec.get(k) and not gecer(sec[k]):
            eksik.append(f"{k}={sec[k]}")
    for k, v in (sec.get("oznitelik") or {}).items():
        if not gecer(v):
            eksik.append(f"{k}={v}")
    return eksik


# ---------------------------------------------------------------- parametreler
UYDURMA_DENETIMI = ("servis", "paket", "kullanici")


def _alan_satiri(ad, alan):
    tip = alan.get("tip", "metin")
    s = f"- {ad} ({tip}"
    if alan.get("desen") in UYDURMA_DENETIMI:
        s += f", {alan['desen']} adı"
    s += f"): {alan.get('aciklama', '')}"
    se = secenekler(alan) if tip == "secim" else []
    if se:
        s += f". Seçenekler: {se}"
    if "varsayilan" in alan:
        s += f". Varsayılan: {alan['varsayilan']} (talep söylemiyorsa boş bırak)"
    if alan.get("izinli_onekler"):
        s += f". İzinli dizinler: {alan['izinli_onekler']}"
    if tip == "komut":
        s += ". Yalnız okuyan komutlar (cat, ls, df, grep, systemctl status, dpkg -l ...); yazan komut reddedilir"
    return s


def _gecer_mi(deger, kaynak):
    return normal(str(deger)) in normal(kaynak)


def parametre_sor(model, katalog, beceri, talep, iz, kaynak_metin=None, ek="", sunucu_adlari=()):
    """Şemadan geçmiş parametreler ya da None. Parametresiz becerilerde model çağrılmaz."""
    t = katalog[beceri]
    sema = t.get("girdi") or {}
    if not sema:
        return {}
    kaynak = (kaynak_metin or "") + " " + talep
    betik_bilgi = ""
    if any(a.get("kaynak") == "betikler" for a in sema.values()):
        betik_bilgi = "Betik kütüphanesi:\n" + "\n".join(
            f"  {b}: {katalog.betik_meta(b)['aciklama']}" for b in secenekler({"kaynak": "betikler"})) + "\n"
    metin = (f"Talep: \"{talep}\"\n{ek}Seçilen beceri: {beceri} — {t['aciklama']}\nParametreler:\n"
             + "\n".join(_alan_satiri(a, al) for a, al in sema.items()) + "\n" + betik_bilgi
             + "Değerleri talepten al; talepte geçmeyen bir servis, paket, kullanıcı, yol ya da adres uydurma. "
               "Zorunlu olmayan bir parametreyi talep açıkça istemiyorsa hiç yazma.\n"
             "JSON: {" + ", ".join(f'"{a}": ...' for a in sema) + "}")

    def dogrula(v):
        if not isinstance(v, dict):
            return None, "bir JSON nesnesi yaz"
        v = {k: x for k, x in v.items() if k in sema and x not in (None, "", [])}
        try:
            p = parametre_dogrula(sema, v)
        except SemaHatasi as e:
            return None, str(e)
        for ad, alan in sema.items():
            if ad not in v:
                continue
            degerler = p[ad] if isinstance(p[ad], list) else [p[ad]]
            denetle = alan.get("tip") in ("eposta", "yol") or alan.get("desen") in UYDURMA_DENETIMI
            if denetle:
                # Şemanın kendi varsayılanı uydurma değildir (ikinci koşunun ilk denemesi: dönüştürülmüş becerinin
                # alici varsayılanı talepte geçmediği için her denemede reddedildi).
                vars_ = alan.get("varsayilan")
                vars_ = vars_ if isinstance(vars_, list) else [vars_]
                uydurma = [x for x in degerler if not _gecer_mi(x, kaynak) and x not in vars_]
                if uydurma:
                    return None, f"{ad}: {uydurma} talepte geçmiyor; yalnız talepteki değerleri kullan"
                sunucu = [x for x in degerler if str(x).upper() in {str(s).upper() for s in sunucu_adlari}]
                if sunucu and alan.get("desen") in UYDURMA_DENETIMI:
                    # İkinci koşu I07: servis adı yerine sunucu adı yazıldı ("servis": "pa-app-02")
                    return None, f"{ad}: {sunucu} bir sunucu adı; {alan['desen']} adını yaz (talepteki servis/paket/kullanıcı)"
        return p, None
    return sor_json(model, SISTEM, metin, dogrula, iz=iz, etiket=f"parametre: {beceri}")[0]


# ---------------------------------------------------------------- çıktı biçimi ve e-posta
def bicim_ve_alici(model, talep, iz):
    """(biçim ya da None, alıcı ya da None). Seçenekleri kod daraltır; tek seçenekte model çağrılmaz."""
    n = normal(talep)
    adaylar = [b for b, sozler in BICIM_SOZ.items() if any(s in n for s in sozler)]
    adresler = list(dict.fromkeys(m.group(0).rstrip(".,;") for m in re.finditer(r"[\w.%+-]+@[\w.-]+\.\w+", talep)))
    adresler = [a for a in adresler if EPOSTA.match(a)]
    bicim = adaylar[0] if len(adaylar) == 1 else None
    alici = adresler[0] if len(adresler) == 1 else None
    if len(adaylar) > 1:
        se = adaylar + ["yok"]
        out = sor_json(model, SISTEM, f"Talep: \"{talep}\"\nSonuç hangi biçimde belgeye dönüştürülsün? Seçenekler: {se}\n"
                       'JSON: {"bicim": "<seçenek>"}',
                       lambda v: (v.get("bicim"), None) if v.get("bicim") in se else (None, f"şunlardan biri: {se}"),
                       iz=iz, etiket="çıktı biçimi")[0]
        bicim = None if out in (None, "yok") else out
    if len(adresler) > 1:
        se = adresler + ["gonderme"]
        out = sor_json(model, SISTEM, f"Talep: \"{talep}\"\nRapor hangi adrese gönderilsin? Seçenekler: {se}\n"
                       'JSON: {"alici": "<seçenek>"}',
                       lambda v: (v.get("alici"), None) if v.get("alici") in se else (None, f"şunlardan biri: {se}"),
                       iz=iz, etiket="e-posta alıcısı")[0]
        alici = None if out in (None, "gonderme") else out
    return bicim, alici


def hata_yorumu(model, talep, adimlar, iz):
    """Başarısız sunucular için modelin kısa yorumu (rapora 'model yorumu' diye ayrı girer)."""
    kanit = []
    for a in adimlar:
        for r in a.get("sonuclar", []):
            if r["durum"] != "basarili":
                kanit.append(f"{a['beceri']} / {r['sunucu']}: {r['durum']}; "
                             f"{(r.get('sema_hatasi') or r.get('neden') or r.get('stderr') or '').strip()[:200]}")
    if not kanit:
        return ""
    metin = (f"Talep: \"{talep}\"\nŞu sunucularda iş başarısız oldu:\n" + "\n".join(kanit[:20])
             + "\nOperatöre 2-3 cümlelik Türkçe bir açıklama yaz: olası neden ve önerilen sonraki adım. Başarı iddia etme.\n"
             'JSON: {"yorum": "..."}')
    out = sor_json(model, SISTEM, metin,
                   lambda v: (str(v["yorum"])[:800], None) if str(v.get("yorum", "")).strip() else (None, "yorum boş"),
                   iz=iz, etiket="hata yorumu")[0]
    return out or ""


def kisa(veri, n=600):
    s = veri if isinstance(veri, str) else json.dumps(veri, ensure_ascii=False, default=str)
    return s if len(s) <= n else s[:n] + "…"
