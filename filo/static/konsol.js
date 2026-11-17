/* Filo konsolu: kabuk, yönlendirici ve ortak bileşenler (tablo, rozet, sekme, bildirim). Bağımlılık yok. */
"use strict";
const Filo = (() => {
  const $ = (s, k = document) => k.querySelector(s);
  const $$ = (s, k = document) => [...k.querySelectorAll(s)];
  const esc = v => String(v ?? "").replace(/[&<>"']/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}[c]));
  const sayfalar = {};
  let simdiki = null, zamanlayicilar = [];

  async function al(yol) {
    const r = await fetch(yol, {cache: "no-store"});
    const v = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(v.hata || `HTTP ${r.status}`);
    return v;
  }
  async function gonder(yol, govde = {}) {
    const r = await fetch(yol, {method: "POST", headers: {"Content-Type": "application/json", "X-Filo": "1"}, body: JSON.stringify(govde)});
    const v = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(v.hata || `HTTP ${r.status}`);
    return v;
  }

  const DURUM_SINIFI = {basarili: "basari", bitti: "basari", canli: "basari", onaylandi: "basari", katalogda: "basari", tamam: "basari",
    hatali: "hata", basarisiz: "hata", erisilemedi: "hata", hata: "hata", reddedildi: "hata", "ajan yok": "hata", iptal: "hata",
    zaman_asimi: "uyari", kismi: "uyari", onay_bekliyor: "uyari", bekliyor: "uyari", devredildi: "uyari", taslak: "uyari",
    duraklatildi: "uyari", yarida_kaldi: "uyari", ertelendi: "uyari", sinira_ulasti: "uyari", yarida: "uyari",
    calisiyor: "bilgi", planlaniyor: "bilgi", plan_hazir: "bilgi", oneri: "bilgi", zamanlandi: "bilgi", yapilmadi: "",
    calisti: "basari", kacirildi: "uyari", atlandi: "", soruldu: "uyari", onay_dustu: "hata", olusturuldu: "bilgi", degistirildi: ""};
  const DURUM_ADI = {basarili: "başarılı", bitti: "bitti", hatali: "hatalı", basarisiz: "başarısız", erisilemedi: "erişilemedi",
    zaman_asimi: "zaman aşımı", kismi: "kısmi", onay_bekliyor: "onay bekliyor", calisiyor: "çalışıyor", planlaniyor: "planlanıyor",
    plan_hazir: "plan hazır", devredildi: "devredildi", reddedildi: "reddedildi", iptal: "iptal", beceri_yok: "beceri yok",
    oneri: "öneri", canli: "canlı", kayitsiz: "kayıtsız", bekliyor: "bekliyor", onaylandi: "onaylandı", hata: "hata",
    duraklatildi: "duraklatıldı", yarida_kaldi: "yarıda kaldı", zamanlandi: "zamanlandı", ertelendi: "ertelendi",
    sinira_ulasti: "üst sınıra ulaştı", yarida: "yarıda", yapilmadi: "yapılmadı", tamam: "tamam", calisti: "çalıştı",
    kacirildi: "kaçırıldı", atlandi: "atlandı", soruldu: "soruldu", onay_dustu: "onay düştü", olusturuldu: "oluşturuldu",
    degistirildi: "değiştirildi"};
  const rozet = (d, metin) => `<span class="rozet ${DURUM_SINIFI[d] || ""}">${esc(metin ?? DURUM_ADI[d] ?? d)}</span>`;
  const risk = r => r === null || r === undefined ? "" : `<span class="risk r${r}" title="risk düzeyi">R${r}</span>`;
  const zaman = z => z ? esc(String(z).replace("T", " ")) : "–";

  function bildir(metin, sure = 3500) {
    const t = document.createElement("div");
    t.className = "toast"; t.setAttribute("role", "status"); t.textContent = metin;
    document.body.appendChild(t); setTimeout(() => t.remove(), sure);
  }
  const bos = (baslik, alt = "") => `<div class="bos"><b>${esc(baslik)}</b>${esc(alt)}</div>`;
  const hataKutu = e => `<div class="hata-kutu" role="alert">${esc(e.message || e)}</div>`;

  /* Tablo: sıralama (başlığa tıkla / Enter), süzme (metin), boş durum. kolonlar: [{ad, baslik, ciz?(satir), sirala?(satir), genislik?}] */
  function tablo(kap, kolonlar, satirlar, sec = {}) {
    let sira = sec.sira || null, yon = 1, suzgec = "";
    const id = "t" + Math.random().toString(36).slice(2, 8);
    kap.innerHTML = (sec.suzgec !== false ? `<div class="tablo-arac"><input type="search" placeholder="${esc(sec.yerTutucu || "Süz…")}" aria-label="Tabloyu süz" id="${id}-s">
      <span class="bilgi" id="${id}-n"></span>${sec.arac || ""}</div>` : "") + `<div class="tablo-sar"><table><thead><tr>${kolonlar.map((k, i) =>
      `<th class="${k.sirala === false ? "" : "siralanir"}" data-i="${i}" ${k.sirala === false ? "" : 'tabindex="0" aria-sort="none"'} style="${k.genislik ? "width:" + k.genislik : ""}">${esc(k.baslik)} <span class="ok"></span></th>`).join("")}</tr></thead><tbody></tbody></table></div>`;
    const govde = $("tbody", kap);
    function deger(k, s) { const v = typeof k.sirala === "function" ? k.sirala(s) : s[k.ad]; return v ?? ""; }
    function ciz() {
      let l = satirlar;
      if (suzgec) { const q = suzgec.toLocaleLowerCase("tr"); l = l.filter(s => JSON.stringify(s).toLocaleLowerCase("tr").includes(q)); }
      if (sira !== null) { const k = kolonlar[sira]; l = [...l].sort((a, b) => { const x = deger(k, a), y = deger(k, b);
        return (typeof x === "number" && typeof y === "number" ? x - y : String(x).localeCompare(String(y), "tr", {numeric: true})) * yon; }); }
      govde.innerHTML = l.length ? l.map(s => `<tr ${sec.satirOz ? sec.satirOz(s) : ""}>${kolonlar.map(k => `<td class="${k.sinif || ""}">${k.ciz ? k.ciz(s) : esc(s[k.ad])}</td>`).join("")}</tr>`).join("")
        : `<tr><td colspan="${kolonlar.length}">${bos(sec.bosBaslik || "Kayıt yok", sec.bosAlt || "")}</td></tr>`;
      const n = $(`#${id}-n`, kap); if (n) n.textContent = `${l.length} / ${satirlar.length} kayıt`;
      $$("th", kap).forEach(th => { const i = +th.dataset.i; const ok = $(".ok", th);
        if (ok) ok.textContent = i === sira ? (yon > 0 ? "▲" : "▼") : "";
        if (th.hasAttribute("aria-sort")) th.setAttribute("aria-sort", i === sira ? (yon > 0 ? "ascending" : "descending") : "none"); });
      if (sec.sonra) sec.sonra(govde);
    }
    $$("th.siralanir", kap).forEach(th => {
      const f = () => { const i = +th.dataset.i; if (sira === i) yon = -yon; else { sira = i; yon = 1; } ciz(); };
      th.addEventListener("click", f); th.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); f(); } });
    });
    const s = $(`#${id}-s`, kap); if (s) s.addEventListener("input", () => { suzgec = s.value.trim(); ciz(); });
    ciz();
    return {yenile(y) { satirlar = y; ciz(); }};
  }

  /* Sekmeler: liste [[anahtar, başlık]], secildi(anahtar) çağrılır. Ok tuşlarıyla gezilir. */
  function sekmeler(kap, liste, sec, secildi) {
    kap.innerHTML = `<div class="sekmeler" role="tablist">${liste.map(([k, b]) => `<button role="tab" type="button" data-k="${esc(k)}" aria-selected="${k === sec}" tabindex="${k === sec ? 0 : -1}">${esc(b)}</button>`).join("")}</div>`;
    const dugmeler = $$("button", kap);
    const sec_ = b => { dugmeler.forEach(x => { x.setAttribute("aria-selected", x === b); x.tabIndex = x === b ? 0 : -1; }); secildi(b.dataset.k); };
    dugmeler.forEach((b, i) => {
      b.addEventListener("click", () => sec_(b));
      b.addEventListener("keydown", e => { const j = e.key === "ArrowRight" ? i + 1 : e.key === "ArrowLeft" ? i - 1 : null;
        if (j !== null) { const n = dugmeler[(j + dugmeler.length) % dugmeler.length]; n.focus(); sec_(n); } });
    });
    secildi(sec);
  }

  function farkHtml(metin) {
    return `<pre class="fark">${(metin || "(fark yok)").split("\n").map(s => `<span class="${s.startsWith("+") && !s.startsWith("+++") ? "ek" : s.startsWith("-") && !s.startsWith("---") ? "cik" : s.startsWith("@@") ? "bas" : ""}">${esc(s)}</span>`).join("\n")}</pre>`;
  }

  /* ------------------------------------------------------------ koşu denetimi (C3) ve "ne zaman" paneli (C2) */
  const CANLI_DURUM = ["planlaniyor", "calisiyor", "onay_bekliyor"];
  const BEKLEYEN_DURUM = ["duraklatildi", "devredildi", "yarida_kaldi"];
  const EYLEM_ADI = {duraklat: "duraklattı", surdur: "sürdürdü", iptal: "iptal etti", devret: "devretti"};

  function isDenetimiHtml(d) {
    const canli = CANLI_DURUM.includes(d.durum), bekleyen = BEKLEYEN_DURUM.includes(d.durum);
    const devir = (d.ek || {}).devir, ek = d.ek || {};
    const gecmis = d.kontrol_gecmisi || [];
    let h = `<div class="kart is-denetim"><div class="kart-bas"><div><h2>Koşu denetimi</h2><span class="bilgi">${d.sahip ? `Sahip: <b>${esc(d.sahip)}</b> · ` : ""}`
      + `${canli ? "İş çalışıyor: duraklatınca çalışan adım/sunucu biter, sonraki başlamaz." : bekleyen ? "İş bekliyor: not yazıp sürdürebilir, başkasına devredebilir ya da iptal edebilirsiniz." : "İş bitti: tamamlanan her adım bir devam noktasıdır."}</span></div>
      <div class="dugmeler">${d.durum === "calisiyor" ? `<button class="btn" data-eylem="duraklat">Duraklat</button>` : ""}
      ${bekleyen && !devir ? `<button class="btn birincil" data-eylem="surdur">Sürdür</button>` : ""}
      ${canli || bekleyen ? `<button class="btn" data-eylem="devret-ac">Devret</button><button class="btn tehlike" data-eylem="iptal">İptal et</button>` : ""}</div></div><div class="kart-govde">`;
    if (devir) {
      h += `<div class="not uyari" role="alert"><b>Kaptan insana devretti:</b> ${esc(devir.adim)} adımında ${esc((devir.sunucular || []).join(", "))} başarısız.<br><small>${esc(devir.neden)}</small>
        <fieldset class="secenekler"><legend>Kararınız (Kaptan'a girdi olur)</legend>${Object.entries(devir.secenekler || {}).map(([k, v], i) =>
          `<label><input type="radio" name="devir-karar" value="${esc(k)}" ${i === 0 ? "checked" : ""}> <b>${esc(k)}</b> · ${esc(v)}</label>`).join("")}</fieldset>
        <label for="devir-not">Not</label><textarea id="devir-not" rows="2" placeholder="ör. depo ayarını elle düzelttim; yeniden dene"></textarea>
        <div class="dugmeler" style="margin-top:8px"><button class="btn birincil" data-eylem="devir-karar">Kararı gönder ve sürdür</button></div></div>`;
    } else if (bekleyen) {
      h += `<label for="surdur-not">Sürdürme notu (isteğe bağlı)</label><input id="surdur-not" placeholder="ör. bakım bitti, devam">`;
    }
    h += `<div class="gizli" id="devret-form" style="margin-top:8px"><div class="alanlar"><div><label for="devret-kime">Kime (operatör ya da rol)</label><input id="devret-kime" placeholder="ör. vardiya-2 ya da veritabani-ekibi"></div>
      <div><label for="devret-not">Not</label><input id="devret-not" placeholder="ör. gece penceresinde devam edin"></div></div>
      <div class="dugmeler" style="margin-top:8px"><button class="btn birincil" data-eylem="devret">Devret</button></div></div>`;
    if (!canli && !bekleyen && d.devam) h += `<div id="devam-noktalari" style="margin-top:10px"><span class="bilgi">Devam noktaları yükleniyor…</span></div>`;
    if (ek.kaynak_is || ek.devam_noktasi || ek.zamanlama || gecmis.length || (ek.ertelenen || []).length) {
      h += `<h3 style="margin:12px 0 4px">İş geçmişi</h3><div class="zaman-cizgisi">`
        + (ek.kaynak_is ? `<div class="zc"><b>devam koşusu</b> · kaynak iş <a href="?is=${esc(ek.kaynak_is)}" data-is="${esc(ek.kaynak_is)}"><code>${esc(ek.kaynak_is)}</code></a>${ek.devam_noktasi ? `, ${ek.devam_noktasi.adim + 1}. adımdan (${ek.devam_noktasi.kapsam === "hepsi" ? "hepsi" : "yalnız başarısızlar"}: ${esc((ek.devam_noktasi.sunucular || []).join(", ") || "-")})` : ""}</div>` : "")
        + (ek.zamanlama ? `<div class="zc"><b>zamanlama</b> · <a href="/zamanlama">zamanlanmış iş <code>${esc(ek.zamanlama)}</code></a>${ek.zamanlama_notu ? ` · ${esc(ek.zamanlama_notu)}` : ""}</div>` : "")
        + (ek.ertelenen || []).map(x => `<div class="zc"><b>ertelendi</b> · ${esc(x.sunucular.join(", "))} → ${zaman(x.zaman)} (<a href="/zamanlama">zamanlanmış iş ${esc(x.zamanlama)}</a>)</div>`).join("")
        + gecmis.map(x => `<div class="zc"><b>${esc(x.kim || "")} ${esc(EYLEM_ADI[x.olay] || x.olay)}</b> <small>${zaman(x.zaman).slice(11)}</small>${x.kime ? ` → <b>${esc(x.kime)}</b>` : ""}${x.karar ? ` · karar: ${esc(x.karar)}` : ""}<br><span>${esc(x.not_ || x.metin || "")}</span></div>`).join("")
        + `</div>`;
    }
    return h + `</div></div>`;
  }

  async function isDenetimiBagla(kap, d, yenile, isAc) {
    const ac = s => $(s, kap);
    const eylem = async (e, govde = {}) => { try { await gonder("/api/is/kontrol", {kimlik: d.kimlik, eylem: e, ...govde}); bildir("İş " + (EYLEM_ADI[e] || e)); yenile(); } catch (x) { bildir(x.message); } };
    kap.addEventListener("click", async ev => {
      const b = ev.target.closest("[data-eylem]"); if (!b || !kap.contains(b)) return;
      const e = b.dataset.eylem;
      if (e === "duraklat") return eylem("duraklat");
      if (e === "surdur") return eylem("surdur", {not: (ac("#surdur-not") || {}).value || ""});
      if (e === "iptal") { if (confirm("İş iptal edilsin mi? Çalışan sunucu işi biter, kalan adımlar çalışmaz.")) eylem("iptal"); return; }
      if (e === "devret-ac") { ac("#devret-form").classList.toggle("gizli"); return; }
      if (e === "devret") { const kime = ac("#devret-kime").value.trim(); if (!kime) return bildir("Kime devredileceğini yazın"); return eylem("devret", {kime, not: ac("#devret-not").value}); }
      if (e === "devir-karar") { const r = kap.querySelector("input[name=devir-karar]:checked"); return eylem("surdur", {karar: r ? r.value : null, not: ac("#devir-not").value}); }
      if (e === "devam") {
        try { const r = await gonder("/api/is/devam", {kimlik: d.kimlik, adim: +b.dataset.adim, kapsam: b.dataset.kapsam}); bildir("Devam koşusu başladı: " + r.kimlik); isAc(r.kimlik); } catch (x) { bildir(x.message); }
      }
    });
    const dn = ac("#devam-noktalari");
    if (dn) {
      try {
        const v = await al("/api/is/devam-noktalari?kimlik=" + encodeURIComponent(d.kimlik));
        dn.innerHTML = `<h3 style="margin:0 0 4px">Adımdan yeniden çalıştır</h3><p class="bilgi" style="margin:0 0 6px">Önceki adımlar yeniden çalışmaz; sonuçları kayıttan gelir.</p>
          <div class="tablo-sar"><table><thead><tr><th>Adım</th><th>Durum</th><th>Giren</th><th>Başarısız</th><th></th></tr></thead><tbody>${v.noktalar.map(n => `<tr><td>${n.adim + 1}. ${esc(n.ad)}</td><td>${rozet(n.durum)}</td>
            <td>${esc((n.sunucular || []).length || "–")}</td><td>${esc((n.basarisiz || []).join(", ") || "–")}</td>
            <td class="dugmeler">${(n.basarisiz || []).length ? `<button class="btn kucuk" data-eylem="devam" data-adim="${n.adim}" data-kapsam="basarisiz">Başarısızlarla</button>` : ""}<button class="btn kucuk" data-eylem="devam" data-adim="${n.adim}" data-kapsam="hepsi">Hepsiyle</button></td></tr>`).join("")}</tbody></table></div>`;
      } catch (x) { dn.innerHTML = `<span class="bilgi">${esc(x.message)}</span>`; }
    }
  }

  function nezamanHtml(d) {
    const zm = (d.plan || {}).zamanlama;
    const risk3 = (d.plan && ((d.plan.ana && d.plan.ana.onay_gerekli) || d.plan.risk >= 3));
    return `<div class="kart nezaman"><div class="kart-bas"><div><h2>Ne zaman?</h2><span class="bilgi">${zm ? `Talepte zamanlama bulundu (${esc(zm.kaynak === "model" ? "model çözdü, kod doğruladı" : "kod çözdü")}): <b>${esc(zm.okunakli)}</b>` : "Şimdi çalıştırabilir ya da zamanlayabilirsiniz."}</span></div>
      <div class="mod-secici" role="group" aria-label="Çalıştırma zamanı"><button type="button" data-nz="simdi" aria-pressed="${!zm}">Şimdi çalıştır</button><button type="button" data-nz="zamanla" aria-pressed="${!!zm}">Zamanla</button></div></div>
      <div class="kart-govde ${zm ? "" : "gizli"}" id="nz-form"><div class="alanlar">
        <div><label for="nz-metin">Zamanlama</label><input id="nz-metin" value="${esc(zm ? zm.okunakli.replace(/^bir kez: /, "") : "")}" placeholder="ör. her gün 02:00 · her cumartesi 03:00 · yarın 23:30 · bakım penceresinde"><div class="yardim-metni" id="nz-onizleme">${zm ? "Sonraki 3 çalışma: " + zm.sonraki.map(zaman).join(" · ") : "Önizle ile sonraki 3 çalışma zamanını görün."}</div></div>
        <div><label for="nz-hedef">Hedef çözümü</label><select id="nz-hedef"><option value="simdi" ${!zm || zm.hedef_cozumu !== "calisma_aninda" ? "selected" : ""}>Şimdi dondur (liste değişmez)</option><option value="calisma_aninda" ${zm && zm.hedef_cozumu === "calisma_aninda" ? "selected" : ""}>Her koşuda yeniden çöz</option></select></div>
        <div><label for="nz-kacan">Konsol kapalıyken kaçırılan koşu</label><select id="nz-kacan"><option value="atla">Atla</option><option value="hemen" ${zm && zm.kacirilan === "hemen" ? "selected" : ""}>Açılınca hemen çalıştır</option></select></div>
        <div><label for="nz-yasak">Yasak pencerede</label><select id="nz-yasak"><option value="bekle">Pencere kapanınca çalıştır</option><option value="sor" ${zm && zm.yasak_politikasi === "sor" ? "selected" : ""}>Operatöre sor</option><option value="atla" ${zm && zm.yasak_politikasi === "atla" ? "selected" : ""}>Bu koşuyu atla</option></select></div></div>
        ${risk3 ? `<label style="margin-top:8px;display:block"><input type="checkbox" id="nz-onay"> Önceden onaylıyorum (kim, ne zaman, hangi tanım sürümü için verildiği yazılır; tanım değişirse onay düşer)</label>` : ""}
        <div class="dugmeler" style="margin-top:10px"><button class="btn" id="nz-onizle" type="button">Önizle</button><button class="btn birincil" id="nz-zamanla" type="button">Zamanla</button></div></div></div>`;
  }

  function nezamanBagla(kap, d, yenile) {
    const f = $("#nz-form", kap); if (!f) return;
    $$("[data-nz]", kap).forEach(b => b.addEventListener("click", () => { $$("[data-nz]", kap).forEach(x => x.setAttribute("aria-pressed", String(x === b))); f.classList.toggle("gizli", b.dataset.nz !== "zamanla"); }));
    const metin = () => $("#nz-metin", kap).value.trim();
    $("#nz-onizle", kap).addEventListener("click", async () => {
      try { const r = await gonder("/api/zamanlama/onizle", {metin: metin()}); $("#nz-onizleme", kap).textContent = `${r.okunakli} · sonraki 3 çalışma: ${r.sonraki.map(x => x.replace("T", " ")).join(" · ")}`; }
      catch (x) { $("#nz-onizleme", kap).textContent = x.message; } });
    $("#nz-zamanla", kap).addEventListener("click", async () => {
      try {
        const r = await gonder("/api/zamanlama/onizle", {metin: metin()});
        await gonder("/api/is/yurut", {kimlik: d.kimlik, kip: "zamanla", zamanlama: r.zamanlama, hedef_cozumu: $("#nz-hedef", kap).value,
          kacirilan: $("#nz-kacan", kap).value, yasak_politikasi: $("#nz-yasak", kap).value, on_onay: !!($("#nz-onay", kap) || {}).checked});
        bildir("Zamanlandı: " + r.okunakli); yenile();
      } catch (x) { bildir(x.message); } });
  }

  /* ------------------------------------------------------------ kabuk */
  function sayfa(ad, tanim) { sayfalar[ad] = tanim; }
  function yolAdi(yol) { const a = yol.split("?")[0].replace(/^\/+|\/+$/g, ""); return a === "" ? "genel" : a; }
  // Yoklama hataları (sunucu yeniden başlarken bağlantı yok) sessiz geçer; üst çubuk bağlantı durumunu zaten gösterir.
  function zamanla(f, ms) { zamanlayicilar.push(setInterval(() => Promise.resolve().then(f).catch(() => {}), ms)); }
  async function git(yol, gecmis = true) {
    const ad = yolAdi(yol);
    const t = sayfalar[ad] || sayfalar.genel;
    zamanlayicilar.forEach(clearInterval); zamanlayicilar = [];
    if (simdiki && simdiki.birak) simdiki.birak();
    simdiki = t;
    if (gecmis) history.pushState({}, "", yol);
    document.body.className = t.urun ? `urun-${t.urun}` : "";
    document.title = `${t.baslik} · Filo`;
    $$("#yan a").forEach(a => a.classList.toggle("etkin", a.dataset.sayfa === (sayfalar[ad] ? ad : "genel")));
    $$("#yan a").forEach(a => a.removeAttribute("aria-current"));
    const etkin = $(`#yan a.etkin`); if (etkin) etkin.setAttribute("aria-current", "page");
    const kap = $("#sayfa");
    kap.innerHTML = `<div class="sayfa"><div class="bos">Yükleniyor…</div></div>`;
    try { await t.ciz(kap); } catch (e) { kap.innerHTML = `<div class="sayfa">${hataKutu(e)}</div>`; }
  }

  let sonDurum = null;
  async function durumYokla() {
    try {
      const d = await al("/api/durum");
      sonDurum = d;
      $("#baglanti-nokta").className = "nokta iyi"; $("#baglanti-metni").textContent = `bağlı · v${d.surum}`;
      $("#durdur").classList.toggle("basili", d.durdurma.basili);
      $("#durdur").textContent = d.durdurma.basili ? "Durduruldu" : "Durdur";
      $("#durdurma-bandi").classList.toggle("gizli", !d.durdurma.basili);
      const s = $("#onay-sayac"); s.textContent = d.bekleyen_onay; s.classList.toggle("gizli", !d.bekleyen_onay);
      const a = d.ajanlar || {};
      $("#ajan-nokta").className = "nokta " + (a.kapi === false ? "" : a.yok ? "uyari" : a.canli ? "iyi" : "");
      $("#ajan-metni").textContent = a.kapi === false ? "ajan kapısı kapalı (SSH)" : `ajanlar: ${a.canli || 0} canlı${a.yok ? ", " + a.yok + " yok" : ""}`;
    } catch (e) {
      $("#baglanti-nokta").className = "nokta kotu"; $("#baglanti-metni").textContent = "bağlantı yok";
    }
  }

  function baslat() {
    document.addEventListener("click", e => {
      const a = e.target.closest("a[href^='/']");
      if (!a || a.target || e.ctrlKey || e.metaKey || e.shiftKey || a.hasAttribute("download") || a.getAttribute("href").startsWith("/api/")) return;
      e.preventDefault(); git(a.getAttribute("href"));
    });
    window.addEventListener("popstate", () => git(location.pathname, false));
    $("#tema").addEventListener("click", () => {
      const yeni = document.documentElement.dataset.tema === "koyu" ? "acik" : "koyu";
      document.documentElement.dataset.tema = yeni; try { localStorage.setItem("filo-tema", yeni); } catch (e) {}
    });
    $("#durdur").addEventListener("click", async () => {
      if (sonDurum && sonDurum.durdurma.basili) return;
      if (!confirm("Bütün ajan eylemleri kesilsin mi? Çalışan uzak işlemler öldürülür, yenisi başlamaz.")) return;
      await gonder("/api/durdur"); durumYokla(); bildir("Durdurma düğmesi basıldı");
    });
    $("#durdur-kaldir").addEventListener("click", async () => { await gonder("/api/durdur/kaldir"); durumYokla(); });
    durumYokla(); setInterval(durumYokla, 4000);
    git(location.pathname, false);
  }

  return {$, $$, esc, al, gonder, rozet, risk, zaman, bildir, bos, hataKutu, tablo, sekmeler, farkHtml, sayfa, git, zamanla, baslat,
          durum: () => sonDurum, DURUM_ADI, isDenetimiHtml, isDenetimiBagla, nezamanHtml, nezamanBagla, CANLI_DURUM, BEKLEYEN_DURUM};
})();
