/* Kalfa · iş konsolu: hazır becerilerle çalışan ajan. Talep → eşleşen beceri kartı → parametre formu → dondurulmuş
   hedef → yürütme ızgarası → rapor. "Beceriden başla" kipi modeli hiç çağırmaz (sunucu otomasyonu'daki Run Server Script'in üç adımı). */
"use strict";
(() => {
  const {$, $$, esc, al, gonder, rozet, risk, zaman, bildir, bos, hataKutu, tablo, sayfa, zamanla} = Filo;
  const SON = ["bitti", "kismi", "basarisiz", "iptal", "beceri_yok", "reddedildi", "hata", "oneri", "zamanlandi", "ertelendi"];
  let durum = {kip: "talep", is: null, beceri: null, katalog: null, envanter: null};

  function adimDurumu(d) {
    if (!d) return 0;
    if (["planlaniyor"].includes(d.durum)) return 1;
    if (d.durum === "plan_hazir") return 3;
    if (["calisiyor", "onay_bekliyor", "duraklatildi", "devredildi", "yarida_kaldi"].includes(d.durum)) return 4;
    return 5;
  }
  function adimlarHtml(d) {
    const ad = ["Talep", "Beceri", "Parametreler", "Hedef", "Yürütme", "Rapor"];
    const alt = [d ? esc(d.talep.slice(0, 40)) : "yaz ya da beceri seç", d && d.plan ? esc(d.plan.ana.beceri) : "", d && d.plan ? `${Object.keys(d.plan.ana.parametreler).length} alan` : "",
      d && d.plan && d.plan.ana.hedef ? `${d.plan.ana.hedef.sayi} sunucu` : "", d ? esc(Filo.DURUM_ADI[d.durum] || d.durum) : "", d && d.rapor ? "hazır" : ""];
    const n = adimDurumu(d);
    return `<ol class="adimlar">${ad.map((a, i) => `<li class="${i < n ? "tamam" : i === n ? "simdi" : ""}">${a}<span>${alt[i] || "&nbsp;"}</span></li>`).join("")}</ol>`;
  }

  function alanHtml(ad, a, deger) {
    const id = "kp-" + ad, v = deger ?? a.varsayilan ?? "";
    const yard = `<div class="yardim-metni">${esc(a.aciklama || "")}${a.izinli_onekler ? " · izinli: " + esc(a.izinli_onekler.join(", ")) : ""}</div>`;
    if (a.tip === "secim" || a.secenekler) return `<div><label for="${id}">${esc(ad)}</label><select id="${id}" data-alan="${esc(ad)}" data-tip="secim">${(a.secenekler || []).map(s => `<option ${String(s) === String(v) ? "selected" : ""}>${esc(s)}</option>`).join("")}</select>${yard}</div>`;
    if (a.tip === "mantik") return `<div><label><input type="checkbox" data-alan="${esc(ad)}" data-tip="mantik" ${v ? "checked" : ""}> ${esc(ad)}</label>${yard}</div>`;
    const tip = a.tip === "tamsayi" ? "number" : a.tip === "eposta" ? "email" : "text";
    const deg = Array.isArray(v) ? v.join(", ") : v;
    return `<div><label for="${id}">${esc(ad)} <span class="bilgi">(${esc(a.tip || "metin")}${a.zorunlu === false || "varsayilan" in a ? "" : ", zorunlu"})</span></label><input id="${id}" type="${tip}" data-alan="${esc(ad)}" data-tip="${esc(a.tip || "metin")}" value="${esc(deg)}">${yard}</div>`;
  }
  function formDegerleri(kap) {
    const out = {};
    $$("[data-alan]", kap).forEach(x => {
      const t = x.dataset.tip;
      if (t === "mantik") out[x.dataset.alan] = x.checked;
      else if (x.value === "") return;
      else if (t === "liste") out[x.dataset.alan] = x.value.split(/[,\s]+/).filter(Boolean);
      else if (t === "tamsayi") out[x.dataset.alan] = +x.value;
      else out[x.dataset.alan] = x.value;
    });
    return out;
  }

  async function girisCiz() {
    const k = $("#k-giris");
    if (durum.kip === "talep") {
      const bg = await al("/api/baglantilar");
      k.innerHTML = `<div class="kart"><div class="kart-bas"><h2>1 · Talep</h2><span class="bilgi">Model yalnız beceri seçer, hedefi ve parametreleri doldurur; kod doğrular ve dondurur.</span></div><div class="kart-govde">
        <label for="k-metin">Talep</label><textarea id="k-metin" rows="3" placeholder="ör. Adı PA ile başlayan sunucularda uygulama_surumu betiğini çalıştır, sonucu XML yap, ops@lab.yerel adresine gönder"></textarea>
        <div class="alanlar"><div><label for="k-baglanti">Model bağlantısı</label><select id="k-baglanti">${bg.baglantilar.map(b => `<option value="${esc(b.ad)}" ${b.ad === bg.varsayilan ? "selected" : ""}>${esc(b.ad)} · ${esc(b.model || b.tur)}</option>`).join("")}</select></div></div>
        <div class="dugmeler" style="margin-top:10px"><button class="btn birincil" id="k-planla">Planla</button><span class="bilgi">Plan çalışmaz; önce gösterilir.</span></div></div></div>`;
      $("#k-planla").addEventListener("click", async () => {
        const metin = $("#k-metin").value.trim(); if (!metin) return bildir("Talep yazın");
        try { const r = await gonder("/api/talep", {metin, ajan: "kalfa", baglanti: $("#k-baglanti").value}); isAc(r.kimlik); } catch (x) { bildir(x.message); }
      });
      return;
    }
    durum.katalog = durum.katalog || await al("/api/beceriler");
    const uzak = durum.katalog.beceriler.filter(b => b.tur !== "yerel");
    k.innerHTML = `<div class="izgara iki"><div class="kart"><div class="kart-bas"><h2>1 · Beceri seç</h2><span class="bilgi">${uzak.length} beceri</span></div><div class="kart-govde">
        <input type="search" id="k-ara" placeholder="Beceri ara (ör. betik, paket, servis)" aria-label="Beceri ara"><div class="beceri-listesi" id="k-liste" style="margin-top:8px"></div></div></div>
      <div class="kart"><div class="kart-bas"><h2>2 · Parametreler ve hedef</h2></div><div class="kart-govde" id="k-dform">${bos("Soldan bir beceri seçin")}</div></div></div>`;
    const liste = q => { const l = uzak.filter(b => !q || JSON.stringify(b).toLocaleLowerCase("tr").includes(q.toLocaleLowerCase("tr")));
      $("#k-liste").innerHTML = l.map(b => `<button type="button" data-b="${esc(b.ad)}" aria-pressed="${durum.beceri === b.ad}"><b>${esc(b.ad)}</b> ${risk(b.risk)} <small>${esc(b.baslik)} · ${esc(b.tur)} · v${b.surum}</small></button>`).join("") || bos("Eşleşen beceri yok"); };
    liste("");
    $("#k-ara").addEventListener("input", e => liste(e.target.value));
    $("#k-liste").addEventListener("click", async e => { const b = e.target.closest("[data-b]"); if (!b) return; durum.beceri = b.dataset.b; liste($("#k-ara").value); dformCiz(); });
  }

  async function dformCiz() {
    const d = await al("/api/beceri?ad=" + encodeURIComponent(durum.beceri));
    const f = $("#k-dform");
    f.innerHTML = `<div class="beceri-karti"><h3>${esc(d.ad)} ${risk(d.risk)} <span class="rozet duz">v${esc(d.surum)}</span></h3><div class="bilgi">${esc(d.aciklama)}</div></div>
      <div class="alanlar" id="k-alanlar" style="margin-top:6px">${Object.entries(d.girdi || {}).map(([a, x]) => alanHtml(a, x)).join("") || '<p class="bilgi">Parametre yok.</p>'}</div>
      <label for="k-hedef">Hedef seçici</label><input id="k-hedef" placeholder="ör. PA*  ya da  grup:web os:linux"><div class="yardim-metni" id="k-hedef-onizleme">Sunucular iş başlamadan dondurulur.</div>
      <div class="alanlar"><div><label for="k-bicim">Sonucu dönüştür</label><select id="k-bicim"><option value="">dönüştürme</option><option>csv</option><option>xml</option><option>json</option><option>html</option></select></div>
      <div><label for="k-alici">E-posta alıcısı</label><input id="k-alici" type="email" placeholder="ör. ops@lab.yerel"></div></div>
      <div class="dugmeler" style="margin-top:10px"><button class="btn birincil" id="k-dplanla">Planla</button><span class="bilgi">Model çağrılmaz.</span></div>`;
    let zaman_;
    $("#k-hedef").addEventListener("input", () => { clearTimeout(zaman_); zaman_ = setTimeout(async () => {
      try { const v = await al("/api/envanter/sec?hedef=" + encodeURIComponent($("#k-hedef").value)); $("#k-hedef-onizleme").textContent = `${v.sunucular.length} sunucu: ${v.sunucular.join(", ")}`; }
      catch (x) { $("#k-hedef-onizleme").textContent = x.message; } }, 300); });
    $("#k-dplanla").addEventListener("click", async () => {
      try { const r = await gonder("/api/kalfa/dogrudan", {beceri: durum.beceri, parametreler: formDegerleri($("#k-alanlar")), hedef: $("#k-hedef").value,
        bicim: $("#k-bicim").value || null, alici: $("#k-alici").value.trim() || null}); isAc(r.kimlik); } catch (x) { bildir(x.message); }
    });
  }

  function isAc(kimlik) { history.replaceState({}, "", "/kalfa?is=" + kimlik); durum.is = kimlik; durum.sonDurum = "planlaniyor"; isYukle(); }

  async function isYukle() {
    if (!durum.is) { $("#k-is").innerHTML = ""; $("#k-adimlar").innerHTML = adimlarHtml(null); return; }
    let d;
    try { d = await al("/api/is?kimlik=" + encodeURIComponent(durum.is)); } catch (x) { $("#k-is").innerHTML = hataKutu(x); durum.sonDurum = null; return; }
    durum.sonDurum = d.durum;
    $("#k-adimlar").innerHTML = adimlarHtml(d);
    const p = d.plan && d.plan.ana;
    let h = `<div class="kart"><div class="kart-bas"><div><h2>İş <code>${esc(d.kimlik)}</code> ${rozet(d.durum)}</h2><span class="bilgi">${esc(d.talep)}</span></div>
      <div class="dugmeler"><span class="bilgi">${esc(d.baglanti || "")} · model çağrısı ${esc(d.model_cagri)}</span>${SON.includes(d.durum) ? `<button class="btn kucuk" id="k-yeni">Yeni iş</button>` : ""}</div></div>
      ${d.hata ? `<div class="kart-govde">${hataKutu(d.hata)}</div>` : ""}${d.durum === "planlaniyor" ? `<div class="kart-govde"><span class="bilgi">Model beceri seçiyor, hedefi ve parametreleri dolduruyor…</span></div>` : ""}</div>`;
    if (p) {
      const t = await al("/api/beceri?ad=" + encodeURIComponent(p.beceri)).catch(() => null);
      const sec = d.gerekce.find(g => g.soru && g.soru.startsWith("beceri"));
      h += `<div class="izgara iki"><div class="kart"><div class="kart-bas"><h2>2 · Eşleşen beceri</h2></div><div class="kart-govde"><div class="beceri-karti"><h3>${esc(p.beceri)} ${risk(p.risk)} <span class="rozet duz">v${esc(p.surum)}</span></h3>
          <div>${esc(p.baslik)}</div><div class="bilgi" style="margin-top:4px">${esc(t ? t.aciklama : "")}</div>
          ${d.plan.gerekce ? `<div style="margin-top:6px"><b>Gerekçe:</b> ${esc(d.plan.gerekce)}</div>` : ""}<div class="bilgi" style="margin-top:4px">Risk gerekçesi: ${esc(p.risk_neden)}</div></div>
          <dl class="kv" style="margin-top:10px"><dt>Ek adımlar</dt><dd>${esc(d.plan.adimlar.slice(1).join(" → ") || "yok")}</dd><dt>Onay</dt><dd>${p.onay_gerekli ? rozet("bekliyor", "insan onayı gerekli (risk 3+)") : rozet("basarili", "gerekmez")}${p.kuru_once ? " · önce kuru çalıştırma" : ""}</dd>
          <dt>Zaman aşımı</dt><dd>${esc(p.zaman_asimi)} sn / sunucu</dd>${sec && sec.denemeler.length > 1 ? `<dt>Onarım</dt><dd>model ${sec.denemeler.length} denemede geçerli cevap verdi</dd>` : ""}</dl></div></div>
        <div class="kart"><div class="kart-bas"><h2>3 · Parametreler</h2>${d.durum === "plan_hazir" && t ? `<button class="btn kucuk" id="k-param-uygula">Parametreleri uygula</button>` : ""}</div><div class="kart-govde">
          ${t ? `<div class="alanlar" id="k-palanlar">${Object.entries(t.girdi || {}).map(([a, x]) => alanHtml(a, x, p.parametreler[a])).join("") || '<p class="bilgi">Parametre yok.</p>'}</div>` : `<pre>${esc(JSON.stringify(p.parametreler, null, 1))}</pre>`}
          ${d.plan.bicim || d.plan.alici ? `<dl class="kv" style="margin-top:8px"><dt>Biçim</dt><dd>${esc(d.plan.bicim || "–")}</dd><dt>Alıcı</dt><dd>${esc(d.plan.alici || "–")}</dd></dl>` : ""}</div></div></div>`;
      if (p.hedef) {
        h += `<div class="kart"><div class="kart-bas"><div><h2>4 · Dondurulmuş hedef</h2><span class="bilgi">${p.hedef.sayi} sunucu · seçici <code>${esc(JSON.stringify(p.hedef.secici))}</code> · ${zaman(p.hedef.zaman)} · özet ${esc(p.hedef.ozet)}</span></div>
          <div class="dugmeler">${d.durum === "plan_hazir" ? `<button class="btn" id="k-vazgec">Vazgeç</button><button class="btn birincil" id="k-yurut">Yürüt (${p.hedef.sayi} sunucu)</button>` : ""}</div></div><div class="kart-govde" id="k-hedef-tablo"></div></div>`;
      }
    }
    if (p && d.durum === "plan_hazir") h += Filo.nezamanHtml(d);
    if (p && p.kimlik_calistirma) h += `<div class="not" style="margin-bottom:12px">Çalıştırma kimliği: <b>${esc(p.kimlik_calistirma)}</b> (sudo -n ile; sunucu izin vermezse sonuç "yetki yok" olur)</div>`;
    if (!["planlaniyor", "plan_hazir"].includes(d.durum)) h += `<div id="k-denetim">${Filo.isDenetimiHtml(d)}</div>`;
    if (d.adimlar.length || Object.keys(d.izgara || {}).length) {
      h += `<div class="kart"><div class="kart-bas"><h2>5 · Yürütme</h2>${d.onay ? `<span>${rozet("onay_bekliyor", "onay " + d.onay.kimlik)} <a href="/onaylar">Onaylar</a></span>` : ""}</div><div class="kart-govde">
        <div class="sunucu-izgarasi">${Object.entries(d.izgara || {}).map(([s, x]) => `<div class="sunucu-kutu ${esc(x.durum)}"><b>${esc(s)}</b><small>${esc(Filo.DURUM_ADI[x.durum] || x.durum)} · ${esc(x.adim)}${x.deneme > 1 ? " · deneme " + x.deneme : ""}</small><small title="${esc(x.neden || "")}">${esc(x.neden || " ")}</small></div>`).join("")}</div>
        <div id="k-sonuclar" style="margin-top:12px"></div></div></div>`;
    }
    if (d.rapor || d.yorum) {
      const belge = d.adimlar.find(a => a.belge);
      h += `<div class="kart"><div class="kart-bas"><h2>6 · Rapor</h2></div><div class="kart-govde"><pre>${esc(d.rapor)}</pre>
        ${d.yorum ? `<div class="not" style="margin-top:8px"><b>Model yorumu</b> (kod denetiminden geçmez, öneridir): ${esc(d.yorum)}</div>` : ""}
        ${belge ? `<h3 style="margin:10px 0 4px">Belge: ${esc(belge.belge.ad)}</h3><pre>${esc(belge.belge.onizleme)}</pre>` : ""}
        ${d.durum === "bitti" ? `<div class="dugmeler" style="margin-top:10px"><button class="btn" id="k-donustur">Bu işi beceriye dönüştür</button><span class="bilgi">Tek seferlik betik/komut işi katalogda yeni beceri olur.</span></div><div id="k-donustur-sonuc"></div>` : ""}</div></div>`;
    }
    $("#k-is").innerHTML = h;
    if (p && p.hedef) {
      const env = durum.envanter || (durum.envanter = await al("/api/envanter"));
      const aj = await al("/api/ajanlar").catch(() => ({sunucular: []}));
      const yol = Object.fromEntries(aj.sunucular.map(x => [x.sunucu, x.fiili_yol]));
      const ex = Object.fromEntries(env.sunucular.map(s => [s.ad, s]));
      tablo($("#k-hedef-tablo"), [{ad: "ad", baslik: "Sunucu", ciz: s => `<b>${esc(s.ad)}</b>`}, {ad: "aile", baslik: "Aile", ciz: s => esc((ex[s.ad] || {}).aile || "")},
        {ad: "gruplar", baslik: "Gruplar", ciz: s => esc(((ex[s.ad] || {}).gruplar || []).join(", "))}, {ad: "yol", baslik: "İş yolu", ciz: s => yol[s.ad] === "ajan" ? rozet("basarili", "ajan") : rozet("bekliyor", yol[s.ad] || "ssh")}],
        p.hedef.sunucular.map(a => ({ad: a})), {suzgec: p.hedef.sayi > 10});
    }
    const son = [...d.adimlar].reverse().find(a => (a.sonuclar || []).length);
    if (son && $("#k-sonuclar")) tablo($("#k-sonuclar"), [{ad: "sunucu", baslik: "Sunucu"}, {ad: "durum", baslik: "Durum", ciz: r => rozet(r.durum)},
      {ad: "cikis_kodu", baslik: "Kod"}, {ad: "sure", baslik: "Süre"}, {ad: "deneme", baslik: "Deneme"},
      {ad: "veri", baslik: "Çıktı (şemadan geçmiş)", sinif: "kirp", sirala: false, ciz: r => `<code>${esc(r.sema_hatasi || (r.veri != null && r.veri !== "" ? JSON.stringify(r.veri) : (r.stdout || r.neden || r.stderr || "")).slice(0, 300))}</code>${r.kesildi ? " " + rozet("zaman_asimi", "kesildi") : ""}`}],
      son.sonuclar, {suzgec: son.sonuclar.length > 10, yerTutucu: "Sonuç süz…"});
    const bag = (s, f) => { const e = $(s); if (e) e.addEventListener("click", f); };
    if ($("#k-denetim")) Filo.isDenetimiBagla($("#k-denetim"), d, isYukle, isAc);
    if (d.durum === "plan_hazir") Filo.nezamanBagla($("#k-is"), d, isYukle);
    bag("#k-yurut", async () => { try { await gonder("/api/is/yurut", {kimlik: d.kimlik, kip: "simdi"}); isYukle(); } catch (x) { bildir(x.message); } });
    bag("#k-vazgec", async () => { try { await gonder("/api/is/vazgec", {kimlik: d.kimlik}); isYukle(); } catch (x) { bildir(x.message); } });
    bag("#k-yeni", () => { durum.is = null; history.replaceState({}, "", "/kalfa"); isYukle(); });
    bag("#k-param-uygula", async () => { try { await gonder("/api/kalfa/parametre", {kimlik: d.kimlik, parametreler: formDegerleri($("#k-palanlar"))}); bildir("Plan yeniden kuruldu"); isYukle(); } catch (x) { bildir(x.message); } });
    bag("#k-donustur", async () => { try { const r = await gonder("/api/beceriye-donustur", {kimlik: d.kimlik});
      $("#k-donustur-sonuc").innerHTML = `<div class="not" style="margin-top:8px">${rozet("katalogda", "katalogda")} <a href="/beceriler?ad=${esc(r.beceri)}"><b>${esc(r.beceri)}</b></a> v${r.surum} ${risk(r.risk)} · girdi: <code>${esc(Object.keys(r.girdi || {}).join(", ") || "yok")}</code></div>`; } catch (x) { bildir(x.message); } });
    if (SON.includes(d.durum)) sonIslerCiz();
  }

  async function sonIslerCiz() {
    const l = await al("/api/isler?ajan=kalfa");
    $("#k-son").innerHTML = l.slice(0, 14).map(x => `<div style="padding:6px 0;border-bottom:1px solid var(--cizgi)"><a href="/kalfa?is=${esc(x.kimlik)}" data-is="${esc(x.kimlik)}"><code>${esc(x.kimlik)}</code></a> ${rozet(x.durum)}<br><span class="bilgi">${esc((x.talep || "").slice(0, 90))}</span></div>`).join("") || bos("Henüz Kalfa işi yok");
  }

  sayfa("kalfa", {baslik: "Kalfa · iş konsolu", urun: "kalfa", async ciz(kap) {
    durum = {kip: "talep", is: new URLSearchParams(location.search).get("is"), beceri: null, katalog: null, envanter: null};
    kap.innerHTML = `<div class="sayfa"><div class="baslik-satiri"><div><div class="urun-baslik"><span class="urun-rozeti">Kalfa</span><h1>İş konsolu</h1></div>
        <p>Hazır becerilerle çalışır: beceriyi seçer, parametreyi doldurur, hedefi çözüp dondurur, yürütür ve raporlar. Beceri değiştirmez; uygun beceri yoksa söyler. Değişiklik yapan iş planı göstermeden çalışmaz.</p></div>
        <div class="mod-secici" role="group" aria-label="Başlangıç kipi"><button type="button" data-kip="talep" aria-pressed="true">Talep yaz</button><button type="button" data-kip="beceri" aria-pressed="false">Beceriden başla</button></div></div>
      <div id="k-adimlar"></div>
      <div class="izgara yan-panelli"><div><div id="k-giris"></div><div id="k-is" style="margin-top:14px"></div></div>
        <div><div class="kart"><div class="kart-bas"><h2>Son Kalfa işleri</h2></div><div class="kart-govde" id="k-son"></div></div></div></div></div>`;
    $$("[data-kip]").forEach(b => b.addEventListener("click", () => { durum.kip = b.dataset.kip; $$("[data-kip]").forEach(x => x.setAttribute("aria-pressed", x === b)); girisCiz(); }));
    $("#k-son").addEventListener("click", e => { const a = e.target.closest("[data-is]"); if (!a) return; e.preventDefault(); e.stopPropagation(); isAc(a.dataset.is); });
    await girisCiz(); await isYukle(); await sonIslerCiz();
    zamanla(() => {
      const yazilan = document.activeElement && document.activeElement.closest && document.activeElement.closest("#k-denetim, .nezaman");
      if (!yazilan && durum.is && [...Filo.CANLI_DURUM, ...Filo.BEKLEYEN_DURUM].includes(durum.sonDurum)) isYukle(); }, 1500);
  }});
})();
