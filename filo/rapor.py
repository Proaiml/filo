"""Sonuç dönüştürme (CSV, XML, JSON, HTML) ve SMTP ile e-posta.

Satır şeması her biçimde aynıdır: sunucu, durum, cikis_kodu, sure, kesildi, oykunme, sonra becerinin ayrıştırılmış
alanları (anahtar=değer becerilerinde alanlar, satır becerilerinde her satır ayrı kayıt), ayrıştırılmamış çıktıda
`cikti`. Kısmi başarısızlık rapordan düşmez: erişilemeyen ve hatalı sunucular da satır olarak yer alır.
"""
import csv
import datetime
import email.message
import email.utils
import html
import io
import json
import smtplib
import xml.etree.ElementTree as ET

from . import AYARLAR

TEMEL = ("sunucu", "durum", "cikis_kodu", "sure", "kesildi", "oykunme")
MIME = {"csv": "text/csv", "xml": "application/xml", "json": "application/json", "html": "text/html"}


def satirlar(adim):
    out = []
    for r in adim.get("sonuclar", []):
        temel = {k: r.get(k) for k in TEMEL}
        if r.get("neden"):
            temel["neden"] = r["neden"]
        if r.get("sema_hatasi"):
            temel["sema_hatasi"] = r["sema_hatasi"]
        veri = r.get("veri")

        def birlestir(v):
            # Becerinin çıktısındaki alan temel sütunla aynı adı taşıyorsa (ör. servis_durumu'nun "durum"u) atılmaz,
            # "cikti_<ad>" sütununa yazılır. İkinci koşu T04: webd "inactive" bilgisi XML'den bu yüzden düşüyordu.
            return {**temel, **{(k if k not in temel else f"cikti_{k}"): x for k, x in v.items()
                                if not (k == "sunucu" and x == temel.get("sunucu"))}}
        if isinstance(veri, dict):
            out.append(birlestir(veri))
        elif isinstance(veri, list) and veri:
            for v in veri:
                out.append(birlestir(v))
        else:
            out.append({**temel, "cikti": (r.get("stdout") or "").strip()[:4000]})
    return out


def _alanlar(kayitlar):
    adlar = []
    for k in kayitlar:
        for a in k:
            if a not in adlar:
                adlar.append(a)
    return adlar


def donustur(adim, bicim):
    """(dosya_adi, icerik, mime)"""
    kayitlar = satirlar(adim)
    adlar = _alanlar(kayitlar)
    zaman = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    ad = f"filo-{adim.get('beceri', 'sonuc')}-{zaman}.{bicim}"
    if bicim == "json":
        govde = {"beceri": adim.get("beceri"), "surum": adim.get("surum"), "is_kimligi": adim.get("is_kimligi"),
                 "ozet": adim.get("ozet"), "sunucular": kayitlar}
        return ad, json.dumps(govde, ensure_ascii=False, indent=2, default=str), MIME[bicim]
    if bicim == "csv":
        f = io.StringIO()
        w = csv.DictWriter(f, fieldnames=adlar, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        for k in kayitlar:
            w.writerow({a: ("" if k.get(a) is None else k.get(a)) for a in adlar})
        return ad, f.getvalue(), MIME[bicim]
    if bicim == "xml":
        kok = ET.Element("filo_rapor", {"beceri": str(adim.get("beceri")), "surum": str(adim.get("surum")),
                                        "is": str(adim.get("is_kimligi")), "zaman": zaman})
        oz = adim.get("ozet") or {}
        ET.SubElement(kok, "ozet", {k: str(v) for k, v in oz.items()})
        for k in kayitlar:
            s = ET.SubElement(kok, "sunucu", {"ad": str(k.get("sunucu")), "durum": str(k.get("durum"))})
            for a in adlar:
                if a in ("sunucu", "durum"):
                    continue
                e = ET.SubElement(s, "alan", {"ad": a})
                e.text = "" if k.get(a) is None else str(k.get(a))
        ET.indent(kok)
        return ad, '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(kok, encoding="unicode"), MIME[bicim]
    if bicim == "html":
        bas = "".join(f"<th>{html.escape(a)}</th>" for a in adlar)
        govde = "".join("<tr>" + "".join(f"<td>{html.escape('' if k.get(a) is None else str(k.get(a)))}</td>" for a in adlar)
                        + "</tr>" for k in kayitlar)
        return ad, (f"<!doctype html><meta charset='utf-8'><title>Filo raporu</title>"
                    f"<h1>{html.escape(str(adim.get('beceri')))}</h1><table border='1'><tr>{bas}</tr>{govde}</table>"), MIME[bicim]
    raise ValueError(f"bilinmeyen biçim: {bicim}")


def ozet_metni(adimlar):
    """İnsanın okuyacağı dürüst özet: her adımda kaç sunucu, kaçı başarılı, başarısızlar ve nedenleri."""
    satir = []
    for a in adimlar:
        oz = a.get("ozet") or {}
        if a.get("sonuclar"):
            satir.append(f"- {a['beceri']} (v{a.get('surum')}): {oz.get('basarili', 0)}/{oz.get('toplam', 0)} başarılı"
                         + (f", {oz['oykunme']} öykünme" if oz.get("oykunme") else ""))
            for r in a["sonuclar"]:
                if r["durum"] != "basarili":
                    satir.append(f"    {r['sunucu']}: {r['durum']} - {(r.get('sema_hatasi') or r.get('neden') or r.get('stderr') or '').strip()[:160]}")
                elif r.get("oykunme"):
                    satir.append(f"    {r['sunucu']}: öykünme (gerçek sunucu değil)")
        else:
            satir.append(f"- {a['beceri']}: {a.get('durum')}" + (f" ({a['aciklama']})" if a.get("aciklama") else ""))
    return "\n".join(satir)


def posta_ayari():
    yol = AYARLAR / "posta.json"
    return json.loads(yol.read_text(encoding="utf-8"))


class PostaReddi(ValueError):
    pass


def eposta_gonder(alici, konu, govde, ekler=(), ayar=None):
    """ekler: [(dosya_adi, icerik, mime)]. Dönüş: Message-ID."""
    ayar = ayar or posta_ayari()
    alan = alici.rsplit("@", 1)[-1].lower()
    izinli = [a.lower() for a in ayar.get("izinli_alanlar", [])]
    if izinli and alan not in izinli:
        raise PostaReddi(f"alıcı alan adı izinli değil: {alan} (izinli: {izinli})")
    m = email.message.EmailMessage()
    m["From"], m["To"], m["Subject"] = ayar["kimden"], alici, konu
    m["Message-ID"] = email.utils.make_msgid(domain=ayar["kimden"].split("@")[-1])
    m.set_content(govde)
    for ad, icerik, mime in ekler:
        ana, alt = mime.split("/", 1)
        m.add_attachment(icerik.encode("utf-8"), maintype=ana, subtype=alt, filename=ad)
    with smtplib.SMTP(ayar["sunucu"], int(ayar["port"]), timeout=20) as s:
        if ayar.get("starttls"):
            s.starttls()
        s.send_message(m)
    return m["Message-ID"]

