/* Yama, Politikalar ve Uyum sayfaları (D4). İşler Kalfa'nın "beceriden başla" yolundan başlar: salt-okur tarama burada
   hemen çalışır; değiştiren iş (risk 2+) Kalfa iş ekranında kuru çalıştırma ve onayla açılır. */
"use strict";
(() => {
  const {$, $$, esc, al, gonder, rozet, risk, zaman, bildir, bos, tablo, sayfa, git} = Filo;

  const ust = (b, a, s = "") => `<div class="baslik-satiri"><div><h1>${esc(b)}</h1><p>${a}</p></div><div class="dugmeler">${s}</div></div>`;
  const metrik = (e, d, a) => `<div class="kart metrik"><div class="etiket">${esc(e)}</div><div class="deger">${d}</div><div class="alt">${a}</div></div>`;
  const liste = v => (v || "").split(",").map(x => x.trim()).filter(Boolean);

  /* Beceriyi çalıştırır. Salt-okur (risk ≤ 1): hemen yürür, bitince `bitti` çağrılır. Değiştiren: plan Kalfa'da açılır. */
  async function calistir(beceri, parametreler, hedef, bitti, talep) {
    try {
      const k = await gonder("/api/kalfa/dogrudan", {beceri, parametreler, hedef});
      const d = await al("/api/is?kimlik=" + encodeURIComponent(k.kimlik));
      const plan = (d.plan || {}).ana || {};
      if ((plan.risk || 0) >= 2) { bildir(`${beceri}: plan hazır (risk ${plan.risk}); kuru çalıştırma ve onay Kalfa iş ekranında`); git("/kalfa?is=" + k.kimlik); return; }
      await gonder("/api/is/yurut", {kimlik: k.kimlik});
      bildir(`${beceri} çalışıyor…`);
      for (let i = 0; i < 120; i++) {
        await new Promise(r => setTimeout(r, 1000));
        const s = await al("/api/is?kimlik=" + encodeURIComponent(k.kimlik));
        if (!Filo.CANLI_DURUM.includes(s.durum)) { bildir(`${beceri}: ${Filo.DURUM_ADI[s.durum] || s.durum}`); if (bitti) bitti(s); return; }
      }
    } catch (x) { bildir(x.message); }
  }

  const uyumRozet = u => ({uyumlu: rozet("basarili", "uyumlu"), uyumsuz: rozet("hatali", "uyumsuz"), sapma: rozet("hatali", "sapma"),
    kapsam_disi: rozet("", "kapsam dışı"), atanmamis: rozet("", "atanmamış")}[u] || rozet("", u || "–"));
  const gecmisKolonlari = [
    {ad: "zaman", baslik: "Zaman", ciz: x => zaman(x.zaman)},
    {ad: "is", baslik: "İş", ciz: x => `<a href="/kalfa?is=${esc(x.is)}"><code>${esc(x.is)}</code></a>`},
    {ad: "beceri", baslik: "Beceri"}, {ad: "sunucu", baslik: "Sunucu"},
    {ad: "eylemler", baslik: "Yapılan", sirala: false, ciz: x => (x.paketler && x.paketler.length ? x.paketler.map(p => `${esc(p.paket)} ${esc(p.eski)} → ${esc(p.yeni)}`).join("<br>")
      : (x.eylemler || []).map(e => `${esc(e.aciklama)} ${rozet(e.durum)}`).join("<br>")) || "–"},
    {ad: "geri", baslik: "Geri alma", sirala: false, ciz: x => x.geri_alindi ? rozet("", `geri alındı (${x.geri_alindi})`) : x.geri_alinabilir ? `<button class="btn kucuk" data-geri="${esc(x.beceri)}" data-sunucu="${esc(x.sunucu)}" data-is="${esc(x.is)}">Geri al</button>` : "–"}];
  const GERI_BECERI = {yama_uygula: "yama_geri_al", yazilim_politikasi_uygula: "yazilim_politikasi_geri_al", uyum_duzelt: "uyum_geri_al"};
  function geriBagla(kap, yenile) {
    kap.addEventListener("click", e => { const b = e.target.closest("[data-geri]"); if (!b) return;
      const p = b.dataset.geri === "yama_uygula" ? {is_kimligi: b.dataset.is} : {};
      calistir(GERI_BECERI[b.dataset.geri], p, b.dataset.sunucu, yenile); });
  }

  /* ------------------------------------------------------------ Yama */
  async function yamaCiz(kap) {
    const v = await al("/api/yama");
    const d = v.durum, s = Object.keys(d);
    const toplam = s.reduce((a, k) => a + d[k].guncellemeler.length, 0);
    const guv = s.reduce((a, k) => a + d[k].guncellemeler.filter(g => g.guvenlik).length, 0);
    const yb = s.filter(k => d[k].yeniden_baslatma).length;
    const uyumsuz = new Set(Object.values(v.uyum).flatMap(p => Object.entries(p).filter(([, x]) => x.uyum === "uyumsuz").map(([k]) => k)));
    kap.innerHTML = `<div class="sayfa">${ust("Yama", "Bekleyen güncellemeler (güvenlik sınıfı dağıtımın kendi verisinden: Debian güvenlik deposu, RHEL updateinfo, Alpine secdb), yama politikaları, uyum ve uygulama geçmişi. Uygulama önce kuru çalıştırma ve onayla Kalfa iş ekranında açılır; test grubu verilirse önce orada denenir.",
      `<button class="btn" id="y-tara">Filoyu tara</button>`)}
      <div class="izgara dort">${metrik("Taranan sunucu", s.length, `${v.sunucular.length} Linux sunucudan`)}${metrik("Bekleyen yama", toplam, `${guv} güvenlik yaması`)}
        ${metrik("Yeniden başlatma bekleyen", yb, "son taramaya göre")}${metrik("Uyumsuz sunucu", uyumsuz.size, "son politika uyum raporlarında")}</div>
      <div class="kart" style="margin-top:14px"><div class="kart-bas"><h2>Filo yama durumu</h2><span class="bilgi">son tarama sunucu başına</span></div><div class="kart-govde" id="y-durum"></div></div>
      <div class="kart" style="margin-top:14px"><div class="kart-bas"><h2>Yama politikaları</h2><span class="bilgi">hedef, kapsam, hariç tutulanlar ve gerekçeli istisnalar</span></div><div class="kart-govde" id="y-pol"></div></div>
      <div class="izgara iki" style="margin-top:14px"><div class="kart"><div class="kart-bas"><h2>Uyum raporu</h2></div><div class="kart-govde" id="y-uyum"></div></div>
        <div class="kart"><div class="kart-bas"><h2 id="yf-baslik">Politika düzenle</h2></div><div class="kart-govde">
          <div class="alanlar"><div><label for="yf-ad">Ad</label><input id="yf-ad" placeholder="ör. db-aylik"></div><div><label for="yf-hedef">Hedef seçici</label><input id="yf-hedef" placeholder="ör. grup:db"></div>
          <div><label for="yf-kapsam">Kapsam</label><select id="yf-kapsam"><option value="guvenlik">Yalnız güvenlik yamaları</option><option value="hepsi">Bütün güncellemeler</option><option value="paketler">Belirli paketler</option></select></div>
          <div><label for="yf-paket">Paketler (kapsam: belirli)</label><input id="yf-paket" placeholder="virgülle"></div>
          <div><label for="yf-yb">Yeniden başlatma</label><select id="yf-yb"><option value="asla">Asla (raporla)</option><option value="gerekirse">Gerekirse hemen</option><option value="pencerede">Bakım penceresinde</option></select></div>
          <div><label for="yf-test">Test grubu</label><input id="yf-test" placeholder="ör. PA-WEB-01"></div></div>
          <label for="yf-haric" style="margin-top:8px;display:block">Hariç tutulan paketler (satır başına: paket | gerekçe | bitiş YYYY-AA-GG)</label><textarea id="yf-haric" rows="2"></textarea>
          <label for="yf-ist" style="margin-top:8px;display:block">Sunucuya özel istisnalar (satır başına: sunucu | paket | gerekçe | bitiş)</label><textarea id="yf-ist" rows="2"></textarea>
          <div class="dugmeler" style="margin-top:10px"><button class="btn birincil" id="yf-kaydet">Kaydet (yeni sürüm)</button><button class="btn" id="yf-temizle">Temizle</button></div></div></div></div>
      <div class="kart" style="margin-top:14px"><div class="kart-bas"><h2>Uygulama geçmişi</h2><span class="bilgi">geri alma önceki sürüme indirir; eski sürüm depoda yoksa açıkça söylenir</span></div><div class="kart-govde" id="y-gecmis"></div></div></div>`;
    const yenile = () => yamaCiz(kap);
    $("#y-tara").addEventListener("click", () => calistir("yama_durumu", {}, "os:linux", yenile));
    tablo($("#y-durum"), [
      {ad: "sunucu", baslik: "Sunucu", ciz: x => `<b>${esc(x.sunucu)}</b>`},
      {ad: "zaman", baslik: "Son tarama", ciz: x => zaman(x.zaman)},
      {ad: "n", baslik: "Bekleyen", sirala: x => x.n},
      {ad: "g", baslik: "Güvenlik", sirala: x => x.g, ciz: x => x.g ? rozet("hatali", x.g) : "0"},
      {ad: "yb", baslik: "Yeniden başlatma", ciz: x => x.yb ? rozet("bekliyor", "gerekiyor") : "–"},
      {ad: "p", baslik: "Paketler", sirala: false, ciz: x => x.gg.map(g => `${esc(g.paket)} <small>${esc(g.kurulu)} → ${esc(g.aday)}</small>${g.guvenlik ? " " + rozet("hata", "güvenlik") : ""}`).join("<br>") || "–"}],
      s.map(k => ({sunucu: k, zaman: d[k].zaman, n: d[k].guncellemeler.length, g: d[k].guncellemeler.filter(g => g.guvenlik).length, yb: d[k].yeniden_baslatma, gg: d[k].guncellemeler})),
      {bosBaslik: "Henüz tarama yok", bosAlt: "Filoyu tara ile bekleyen güncellemeleri toplayın."});
    tablo($("#y-pol"), [
      {ad: "ad", baslik: "Politika", ciz: p => `<b>${esc(p.ad)}</b> <span class="rozet duz">v${esc(p.surum)}</span><br><small class="bilgi">${esc(p.aciklama || "")}</small>`},
      {ad: "hedef", baslik: "Hedef", ciz: p => `<code>${esc(p.hedef)}</code><br><small>${esc(p.sunucular.join(", "))}</small>`},
      {ad: "kapsam", baslik: "Kapsam", ciz: p => esc({guvenlik: "güvenlik", hepsi: "hepsi", paketler: "paketler: " + (p.paketler || []).join(", ")}[p.kapsam])},
      {ad: "haric", baslik: "Hariç / istisna", sirala: false, ciz: p => [...(p.haric || []).map(h => `hariç ${esc(h.paket)} <small>(${esc(h.gerekce)}${h.bitis ? ", " + esc(h.bitis) : ""})</small>`),
        ...(p.istisnalar || []).map(i => `${esc(i.sunucu)}: ${esc(i.paket)} <small>(${esc(i.gerekce)}; bitiş ${esc(i.bitis || "yok")})</small>`)].join("<br>") || "–"},
      {ad: "yeniden_baslatma", baslik: "Yeniden başlatma", ciz: p => esc({asla: "asla", gerekirse: "gerekirse", pencerede: "bakım penceresinde"}[p.yeniden_baslatma] || p.yeniden_baslatma)},
      {ad: "test_grubu", baslik: "Test grubu", ciz: p => esc(p.test_grubu || "–")},
      {ad: "e", baslik: "", sirala: false, ciz: p => `<div class="dugmeler"><button class="btn kucuk" data-uyum="${esc(p.ad)}">Uyum raporu</button><button class="btn kucuk birincil" data-uygula="${esc(p.ad)}">Önizle ve uygula</button><button class="btn kucuk" data-duzenle="${esc(p.ad)}">Düzenle</button></div>`}],
      v.politikalar, {bosBaslik: "Yama politikası yok"});
    const uy = Object.entries(v.uyum).flatMap(([p, x]) => Object.entries(x).map(([sv, r]) => ({politika: p, sunucu: sv, ...r})));
    tablo($("#y-uyum"), [
      {ad: "politika", baslik: "Politika"}, {ad: "sunucu", baslik: "Sunucu"}, {ad: "uyum", baslik: "Durum", ciz: r => uyumRozet(r.uyum)},
      {ad: "eksik", baslik: "Eksik"}, {ad: "istisna", baslik: "İstisna"}, {ad: "neden", baslik: "Neden", sirala: false, ciz: r => `<small>${esc(r.neden)}</small>`}],
      uy, {bosBaslik: "Uyum raporu yok", bosAlt: "Bir politikada 'Uyum raporu'nu çalıştırın."});
    tablo($("#y-gecmis"), gecmisKolonlari, v.gecmis, {bosBaslik: "Henüz yama uygulanmadı"});
    geriBagla($("#y-gecmis"), yenile);
    const doldur = p => { $("#yf-baslik").textContent = p ? `Düzenle: ${p.ad}` : "Yeni politika"; $("#yf-ad").value = p ? p.ad : ""; $("#yf-hedef").value = p ? p.hedef || "" : "";
      $("#yf-kapsam").value = p ? p.kapsam : "guvenlik"; $("#yf-paket").value = p ? (p.paketler || []).join(", ") : ""; $("#yf-yb").value = p ? p.yeniden_baslatma || "asla" : "asla";
      $("#yf-test").value = p ? p.test_grubu || "" : ""; $("#yf-haric").value = p ? (p.haric || []).map(h => [h.paket, h.gerekce, h.bitis || ""].join(" | ")).join("\n") : "";
      $("#yf-ist").value = p ? (p.istisnalar || []).map(i => [i.sunucu, i.paket, i.gerekce, i.bitis || ""].join(" | ")).join("\n") : ""; };
    $("#yf-temizle").addEventListener("click", () => doldur(null));
    $("#yf-kaydet").addEventListener("click", async () => {
      const satir = (t, alanlar) => t.split("\n").map(x => x.split("|").map(y => y.trim())).filter(x => x[0]).map(x => Object.fromEntries(alanlar.map((a, i) => [a, x[i] || null])));
      const politika = {aciklama: (v.politikalar.find(p => p.ad === $("#yf-ad").value.trim()) || {}).aciklama || "", hedef: $("#yf-hedef").value.trim(), kapsam: $("#yf-kapsam").value,
        paketler: liste($("#yf-paket").value), yeniden_baslatma: $("#yf-yb").value, test_grubu: $("#yf-test").value.trim() || null,
        haric: satir($("#yf-haric").value, ["paket", "gerekce", "bitis"]), istisnalar: satir($("#yf-ist").value, ["sunucu", "paket", "gerekce", "bitis"])};
      try { const r = await gonder("/api/yama/politika", {ad: $("#yf-ad").value.trim(), politika}); bildir(r.degisti ? `Kaydedildi: v${r.surum}` : "Değişiklik yok"); yenile(); } catch (x) { bildir(x.message); } });
    $("#y-pol").addEventListener("click", e => { const t = e.target; const p = v.politikalar.find(x => x.ad === (t.dataset.uyum || t.dataset.uygula || t.dataset.duzenle));
      if (!p) return;
      if (t.dataset.uyum) calistir("yama_uyumu", {politika: p.ad}, p.hedef, yenile);
      if (t.dataset.uygula) calistir("yama_uygula", {politika: p.ad}, p.hedef, yenile);
      if (t.dataset.duzenle) doldur(p); });
  }
  sayfa("yama", {baslik: "Yama", ciz: yamaCiz});

  /* ------------------------------------------------------------ Politikalar */
  async function politikaCiz(kap) {
    const v = await al("/api/politikalar");
    const sap = Object.entries(v.sapma).flatMap(([p, x]) => Object.entries(x).map(([sv, r]) => ({politika: p, sunucu: sv, ...r})));
    kap.innerHTML = `<div class="sayfa">${ust("Yazılım politikaları", "İstenen durum: hangi sunuculara atandığı, kurulu olacak / olmayacak paketler, çalışacak / duracak servisler, kullanıcılar ve dosyalar. Sapma taraması farkı gösterir; remediation yalnız farkı kapatır (ikinci koşu bir şey yapmaz), önce önizleme ve onay Kalfa iş ekranında. Teslim profilleri de bu politikaları kullanır.")}
      <div class="kart"><div class="kart-bas"><h2>Düz Türkçe ile politika</h2><span class="bilgi">ör. "web sunucularında jq ve tree kurulu olsun, filo-izleme olmasın" — model listeleri doldurur, kod her adın talepte geçtiğini denetler</span></div>
        <div class="kart-govde"><div class="alanlar"><div style="grid-column:1/-1"><label for="pt-metin">Talep</label><input id="pt-metin" placeholder="ör. PA sunucularında jq kurulu olsun, telnet olmasın; farkı önce göster"></div></div>
        <div class="dugmeler" style="margin-top:8px"><button class="btn birincil" id="pt-gonder">Kalfa'ya gönder</button><button class="btn" id="pt-kaptan">Kaptan'a gönder</button></div></div></div>
      <div class="kart" style="margin-top:14px"><div class="kart-bas"><h2>Politikalar</h2></div><div class="kart-govde" id="pp"></div></div>
      <div class="izgara iki" style="margin-top:14px"><div class="kart"><div class="kart-bas"><h2>Sapma (son tarama)</h2></div><div class="kart-govde" id="ps"></div></div>
        <div class="kart"><div class="kart-bas"><h2 id="pf-b">Politika düzenle</h2></div><div class="kart-govde"><div class="alanlar">
          <div><label for="pf-ad">Ad</label><input id="pf-ad" placeholder="ör. db-standardi"></div><div><label for="pf-ata">Atamalar (seçici, virgülle)</label><input id="pf-ata" placeholder="ör. grup:db"></div>
          <div><label for="pf-kur">Kurulu olacak paketler</label><input id="pf-kur" placeholder="jq, tree"></div><div><label for="pf-yok">Olmayacak paketler</label><input id="pf-yok" placeholder="telnet"></div>
          <div><label for="pf-calis">Çalışacak servisler</label><input id="pf-calis"></div><div><label for="pf-dur">Duracak servisler</label><input id="pf-dur"></div>
          <div><label for="pf-kul">Var olacak kullanıcılar</label><input id="pf-kul"></div><div><label for="pf-ac">Açıklama</label><input id="pf-ac"></div></div>
          <p class="yardim-metni">Dosyalar (kütüphane dosyası, yol, izin) var olan politikada korunur.</p>
          <div class="dugmeler" style="margin-top:8px"><button class="btn birincil" id="pf-kaydet">Kaydet (yeni sürüm)</button><button class="btn" id="pf-temizle">Temizle</button></div></div></div></div>
      <div class="kart" style="margin-top:14px"><div class="kart-bas"><h2>Remediation geçmişi</h2></div><div class="kart-govde" id="pg"></div></div></div>`;
    const yenile = () => politikaCiz(kap);
    const talepGonder = async ajan => { try { const r = await gonder("/api/talep", {metin: $("#pt-metin").value.trim(), ajan}); git(`/${ajan}?is=${r.kimlik}`); } catch (x) { bildir(x.message); } };
    $("#pt-gonder").addEventListener("click", () => talepGonder("kalfa")); $("#pt-kaptan").addEventListener("click", () => talepGonder("kaptan"));
    const ozet = (l, a) => (l || []).map(x => `${esc(x.ad || x.yol)}${a ? " " + rozet(x.durum === "yok" || x.durum === "durmus" ? "hatali" : "basarili", ({kurulu: "kurulu", yok: "yok", calisiyor: "çalışıyor", durmus: "durmuş", var: "var"})[x.durum] || x.durum || "") : ""}${x.surum ? ` <small>${esc(x.surum)}</small>` : ""}${x.kaynak ? ` <small>← ${esc(x.kaynak)} ${esc(x.mod || "")}</small>` : ""}`).join("<br>") || "–";
    tablo($("#pp"), [
      {ad: "ad", baslik: "Politika", ciz: p => `<b>${esc(p.ad)}</b> <span class="rozet duz">v${esc(p.surum)}</span><br><small class="bilgi">${esc(p.aciklama || "")}</small>${p.teslim_profilleri.length ? `<br><small>teslim profili: ${esc(p.teslim_profilleri.join(", "))}</small>` : ""}`},
      {ad: "atamalar", baslik: "Atandığı", ciz: p => `<code>${esc((p.atamalar || []).join(", ") || "–")}</code><br><small>${esc(p.sunucular.join(", "))}</small>`},
      {ad: "paketler", baslik: "Paketler", sirala: false, ciz: p => ozet(p.paketler, true)},
      {ad: "servisler", baslik: "Servisler", sirala: false, ciz: p => ozet(p.servisler, true)},
      {ad: "kullanicilar", baslik: "Kullanıcılar", sirala: false, ciz: p => ozet(p.kullanicilar, true)},
      {ad: "dosyalar", baslik: "Dosyalar", sirala: false, ciz: p => ozet(p.dosyalar)},
      {ad: "e", baslik: "", sirala: false, ciz: p => `<div class="dugmeler"><button class="btn kucuk" data-tara="${esc(p.ad)}">Sapma tara</button><button class="btn kucuk birincil" data-uygula="${esc(p.ad)}">Önizle ve uygula</button><button class="btn kucuk" data-duzenle="${esc(p.ad)}">Düzenle</button></div>`}],
      v.politikalar, {bosBaslik: "Politika yok"});
    tablo($("#ps"), [
      {ad: "politika", baslik: "Politika"}, {ad: "sunucu", baslik: "Sunucu"},
      {ad: "uyum", baslik: "Durum", ciz: r => uyumRozet(r.farklar.length ? "sapma" : "uyumlu")},
      {ad: "farklar", baslik: "Farklar", sirala: false, ciz: r => r.farklar.map(f => `${esc(f.tur)} <b>${esc(f.ad)}</b>: ${esc(f.mevcut)} → ${esc(f.istenen)} ${risk(f.risk)}${f.geri_alinabilir ? "" : " " + rozet("hata", "geri alınamaz")}`).join("<br>") || "–"},
      {ad: "zaman", baslik: "Tarama", ciz: r => zaman(r.zaman)}], sap, {bosBaslik: "Sapma taraması yok"});
    tablo($("#pg"), gecmisKolonlari, v.gecmis, {bosBaslik: "Henüz remediation yok"});
    geriBagla($("#pg"), yenile);
    const doldur = p => { $("#pf-b").textContent = p ? `Düzenle: ${p.ad}` : "Yeni politika"; $("#pf-ad").value = p ? p.ad : ""; $("#pf-ata").value = p ? (p.atamalar || []).join(", ") : "";
      const ad = (l, d) => (l || []).filter(x => (x.durum || "") === d).map(x => x.ad).join(", ");
      $("#pf-kur").value = p ? ad(p.paketler, "kurulu") : ""; $("#pf-yok").value = p ? ad(p.paketler, "yok") : ""; $("#pf-calis").value = p ? ad(p.servisler, "calisiyor") : "";
      $("#pf-dur").value = p ? ad(p.servisler, "durmus") : ""; $("#pf-kul").value = p ? ad(p.kullanicilar, "var") : ""; $("#pf-ac").value = p ? p.aciklama || "" : ""; };
    $("#pf-temizle").addEventListener("click", () => doldur(null));
    $("#pf-kaydet").addEventListener("click", async () => {
      const eski = v.politikalar.find(p => p.ad === $("#pf-ad").value.trim()) || {};
      const politika = {aciklama: $("#pf-ac").value, atamalar: liste($("#pf-ata").value),
        paketler: [...liste($("#pf-kur").value).map(ad => ({ad, durum: "kurulu"})), ...liste($("#pf-yok").value).map(ad => ({ad, durum: "yok"}))],
        servisler: [...liste($("#pf-calis").value).map(ad => ({ad, durum: "calisiyor"})), ...liste($("#pf-dur").value).map(ad => ({ad, durum: "durmus"}))],
        kullanicilar: liste($("#pf-kul").value).map(ad => ({ad, durum: "var", ...(((eski.kullanicilar || []).find(k => k.ad === ad) || {}).aciklama ? {aciklama: (eski.kullanicilar || []).find(k => k.ad === ad).aciklama} : {})})),
        dosyalar: eski.dosyalar || []};
      try { const r = await gonder("/api/yazilim-politikasi", {ad: $("#pf-ad").value.trim(), politika}); bildir(r.degisti ? `Kaydedildi: v${r.surum}` : "Değişiklik yok"); yenile(); } catch (x) { bildir(x.message); } });
    $("#pp").addEventListener("click", e => { const t = e.target; const p = v.politikalar.find(x => x.ad === (t.dataset.tara || t.dataset.uygula || t.dataset.duzenle));
      if (!p) return;
      const hedef = (p.atamalar || []).join(",") || "os:linux";
      if (t.dataset.tara) calistir("yazilim_politikasi_tara", {politika: p.ad}, hedef, yenile);
      if (t.dataset.uygula) calistir("yazilim_politikasi_uygula", {politika: p.ad}, hedef, yenile);
      if (t.dataset.duzenle) doldur(p); });
  }
  sayfa("politikalar", {baslik: "Politikalar", ciz: politikaCiz});

  /* ------------------------------------------------------------ Uyum */
  async function uyumCiz(kap) {
    const v = await al("/api/uyum");
    const setler = v.kural_setleri;
    let secili = (setler[0] || {}).ad;
    const son = v.son[secili] || {};
    const sv = Object.keys(son).sort();
    const ort = sv.length ? Math.round(sv.reduce((a, k) => a + son[k].puan, 0) / sv.length) : null;
    const bugun = new Date().toISOString().slice(0, 10);
    kap.innerHTML = `<div class="sayfa">${ust("Uyum", "Kural setine göre denetim (dosya, paket, servis, kullanıcı, sysctl, port, komut çıktısı), sunucu başına puan ve ihlaller, gerekçeli ve süreli istisnalar, düzeltme (varsayılan: yalnız geri alınabilenler). Anlık görüntüler bir sunucuyu başka bir sunucuyla ya da kendi geçmişiyle karşılaştırır.",
      `<button class="btn" id="u-denetle">Denetimi çalıştır</button><button class="btn birincil" id="u-duzelt">Düzeltmeyi önizle</button>`)}
      <div class="izgara dort">${metrik("Ortalama uyum puanı", ort === null ? "–" : ort + "%", `${esc(secili || "kural seti yok")} · ${sv.length} sunucu`)}
        ${metrik("Açık ihlal", sv.reduce((a, k) => a + son[k].ihlal, 0), "son denetime göre")}${metrik("İstisna", v.istisnalar.length, `${v.istisnalar.filter(i => i.bitis && i.bitis < bugun).length} süresi dolmuş`)}
        ${metrik("Anlık görüntü", v.goruntuler.length, `${new Set(v.goruntuler.map(g => g.sunucu)).size} sunucu`)}</div>
      <div class="kart" style="margin-top:14px"><div class="kart-bas"><h2>Son denetim: ${esc(secili || "")}</h2><span class="bilgi">✓ geçti · ✗ ihlal · İ istisna · – uygulanamaz</span></div><div class="kart-govde"><div class="tablo-sar" id="u-matris"></div></div></div>
      <div class="izgara iki" style="margin-top:14px"><div class="kart"><div class="kart-bas"><h2>İhlaller</h2></div><div class="kart-govde" id="u-ihlal"></div></div>
        <div class="kart"><div class="kart-bas"><h2>İstisnalar</h2></div><div class="kart-govde"><div id="u-ist"></div>
          <div class="alanlar" style="margin-top:10px"><div><label for="ui-kural">Kural</label><select id="ui-kural">${((setler[0] || {}).kurallar || []).map(k => `<option>${esc(k.kimlik)}</option>`).join("")}</select></div>
          <div><label for="ui-sunucu">Sunucu (seçici)</label><input id="ui-sunucu" placeholder="ör. PB-DB-01"></div><div><label for="ui-bitis">Bitiş</label><input id="ui-bitis" type="date"></div>
          <div style="grid-column:1/-1"><label for="ui-gerekce">Gerekçe</label><input id="ui-gerekce" placeholder="ör. değişiklik kaydı DEĞ-2026-140"></div></div>
          <div class="dugmeler" style="margin-top:8px"><button class="btn" id="ui-ekle">İstisna ekle</button></div></div></div></div>
      <div class="kart" style="margin-top:14px"><div class="kart-bas"><h2>Kural seti: ${esc(secili || "")}</h2><span class="bilgi">v${esc((setler[0] || {}).surum || "")} · ${esc((setler[0] || {}).aciklama || "")}</span></div><div class="kart-govde" id="u-kural"></div></div>
      <div class="izgara iki" style="margin-top:14px"><div class="kart"><div class="kart-bas"><h2>Anlık görüntü karşılaştırması</h2><button class="btn kucuk" id="u-goruntu">Görüntü al (bütün Linux)</button></div><div class="kart-govde">
          <div class="alanlar"><div><label for="ug-a">Referans (A)</label><select id="ug-a">${v.goruntuler.map(g => `<option value="${esc(g.kimlik)}">${esc(g.sunucu)} · ${zaman(g.zaman)}${g.etiket ? " · " + esc(g.etiket) : ""}</option>`).join("")}</select></div>
          <div><label for="ug-b">Hedef (B)</label><select id="ug-b">${v.goruntuler.map((g, i) => `<option value="${esc(g.kimlik)}" ${i === v.goruntuler.length - 1 ? "selected" : ""}>${esc(g.sunucu)} · ${zaman(g.zaman)}${g.etiket ? " · " + esc(g.etiket) : ""}</option>`).join("")}</select></div></div>
          <div class="dugmeler" style="margin-top:8px"><button class="btn birincil" id="ug-kars">Karşılaştır</button></div><div id="ug-sonuc" style="margin-top:10px">${v.goruntuler.length ? "" : bos("Görüntü yok", "Görüntü al ile başlayın.")}</div></div></div>
        <div class="kart"><div class="kart-bas"><h2>Denetim ve düzeltme geçmişi</h2></div><div class="kart-govde"><div id="u-kosu"></div><div id="u-gecmis" style="margin-top:10px"></div></div></div></div></div>`;
    const yenile = () => uyumCiz(kap);
    $("#u-denetle").addEventListener("click", () => calistir("uyum_denetle", {kural_seti: secili}, "os:linux", yenile));
    $("#u-duzelt").addEventListener("click", () => calistir("uyum_duzelt", {kural_seti: secili, yalniz_geri_alinabilir: true}, "os:linux", yenile));
    $("#u-goruntu").addEventListener("click", () => calistir("anlik_goruntu_al", {etiket: "konsol"}, "os:linux", yenile));
    const kurallar = (setler[0] || {}).kurallar || [];
    const isaret = {gecti: `<span class="isaret gecti" title="geçti">✓</span>`, ihlal: `<span class="isaret ihlal" title="ihlal">✗</span>`, istisna: `<span class="isaret istisna" title="istisna">İ</span>`, uygulanamaz: `<span class="isaret uygulanamaz" title="uygulanamaz">–</span>`};
    $("#u-matris").innerHTML = sv.length ? `<table><thead><tr><th>Kural</th>${sv.map(s => `<th>${esc(s)}<br><small>${esc(son[s].puan)}%</small></th>`).join("")}</tr></thead><tbody>${kurallar.map(k => `<tr><td><b>${esc(k.kimlik)}</b><br><small class="bilgi">${esc(k.baslik)}</small></td>${sv.map(s => {
      const r = (son[s].kurallar || []).find(x => x.kural === k.kimlik) || {}; return `<td title="${esc(r.aciklama || "")}">${isaret[r.sonuc] || "·"}</td>`; }).join("")}</tr>`).join("")}</tbody></table>` : bos("Denetim yok", "Denetimi çalıştır ile başlayın.");
    tablo($("#u-ihlal"), [
      {ad: "sunucu", baslik: "Sunucu"}, {ad: "kural", baslik: "Kural", ciz: r => `<b>${esc(r.kural)}</b><br><small>${esc(r.baslik)}</small>`},
      {ad: "onem", baslik: "Önem", ciz: r => rozet(r.onem === "yuksek" ? "hatali" : r.onem === "orta" ? "bekliyor" : "", r.onem)},
      {ad: "aciklama", baslik: "Bulgu", sirala: false, ciz: r => `<small>${esc(r.aciklama)}</small>`},
      {ad: "oneri", baslik: "Düzeltme", sirala: false, ciz: r => `<small>${esc(r.oneri || "–")}</small>${r.duzeltilebilir ? "<br>" + (r.geri_alinabilir ? rozet("basarili", "geri alınabilir") : rozet("hatali", "geri alınamaz")) : ""}`}],
      sv.flatMap(s => (son[s].kurallar || []).filter(r => r.sonuc === "ihlal").map(r => ({sunucu: s, ...r}))), {bosBaslik: "İhlal yok"});
    tablo($("#u-ist"), [{ad: "kural", baslik: "Kural"}, {ad: "sunucu", baslik: "Sunucu"}, {ad: "gerekce", baslik: "Gerekçe"},
      {ad: "bitis", baslik: "Bitiş", ciz: i => i.bitis ? (i.bitis < bugun ? rozet("hatali", `${i.bitis} (doldu)`) : esc(i.bitis)) : "süresiz"}, {ad: "ekleyen", baslik: "Ekleyen"}],
      v.istisnalar, {suzgec: false, bosBaslik: "İstisna yok"});
    $("#ui-ekle").addEventListener("click", async () => { try { await gonder("/api/uyum/istisna", {kural_seti: secili, kural: $("#ui-kural").value, sunucu: $("#ui-sunucu").value.trim(),
      gerekce: $("#ui-gerekce").value.trim(), bitis: $("#ui-bitis").value || null}); bildir("İstisna eklendi"); yenile(); } catch (x) { bildir(x.message); } });
    tablo($("#u-kural"), [{ad: "kimlik", baslik: "Kural", ciz: k => `<b>${esc(k.kimlik)}</b><br><small>${esc(k.baslik)}</small>`}, {ad: "tur", baslik: "Tür"},
      {ad: "onem", baslik: "Önem"}, {ad: "ayrinti", baslik: "Beklenti", sirala: false, ciz: k => `<code>${esc(k.yol || k.ad || k.anahtar || k.port || k.komut || "")}</code> <small>${esc(k.icerir || k.icermez || k.mod_en_cok || k.deger || k.beklenen || (k.var === false || k.kurulu === false || k.acik === false ? "olmamalı" : ""))}</small>`},
      {ad: "duzeltme", baslik: "Düzeltme", sirala: false, ciz: k => k.duzeltme ? `<code>${esc(k.duzeltme.tur)}</code>${["kullanici_sil"].includes(k.duzeltme.tur) ? " " + rozet("hatali", "geri alınamaz") : ""}` : `<small>${esc(k.oneri || "elle")}</small>`}],
      kurallar, {bosBaslik: "Kural yok"});
    tablo($("#u-kosu"), [{ad: "zaman", baslik: "Denetim", ciz: k => zaman(k.zaman)}, {ad: "kural_seti", baslik: "Kural seti"}, {ad: "sunucu", baslik: "Sunucu"},
      {ad: "ortalama", baslik: "Ort. puan", ciz: k => k.ortalama === null ? "–" : k.ortalama + "%"}, {ad: "ihlal", baslik: "İhlal"}], v.kosular, {suzgec: false, bosBaslik: "Denetim koşusu yok"});
    tablo($("#u-gecmis"), gecmisKolonlari, v.gecmis, {suzgec: false, bosBaslik: "Düzeltme yok"});
    geriBagla($("#u-gecmis"), yenile);
    $("#ug-kars").addEventListener("click", async () => {
      try { const r = await al(`/api/uyum/karsilastir?a=${encodeURIComponent($("#ug-a").value)}&b=${encodeURIComponent($("#ug-b").value)}`);
        $("#ug-sonuc").innerHTML = `<p class="bilgi">${esc(r.a.sunucu)} (${zaman(r.a.zaman)}) → ${esc(r.b.sunucu)} (${zaman(r.b.zaman)}): <b>${r.fark.toplam}</b> fark</p>`
          + (r.metin.length ? `<pre class="fark">${r.metin.map(s => `<span class="${/yalnız hedefte|→/.test(s) ? "ek" : /yalnız referansta/.test(s) ? "cik" : ""}">${esc(s)}</span>`).join("\n")}</pre>` : bos("Fark yok"));
      } catch (x) { bildir(x.message); } });
  }
  sayfa("uyum", {baslik: "Uyum", ciz: uyumCiz});
})();
