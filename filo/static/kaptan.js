/* Kaptan · akış tuvali: talepten akış kurar, adım adım yürütür; hata ya da şema uyumsuzluğunda teşhis koyar, onarır,
   gerekirse beceriyi yeni sürümle değiştirir. Sayfanın başında inisiyatif düzeyi: kodla uygulanır, her karar hangi
   düzeyle geçtiğini taşır. Başarılı akış beceriye dönüşür ya da sabit akış olarak kaydedilir. */
"use strict";
(() => {
  const {$, $$, esc, al, gonder, rozet, risk, zaman, bildir, bos, hataKutu, tablo, sekmeler, farkHtml, sayfa, zamanla} = Filo;
  const CANLI = ["planlaniyor", "calisiyor", "onay_bekliyor"];
  const KARAR_ADI = {izinli: "bu düzeyde izinli", onay_gerekli: "onay gerekti", reddedildi: "reddedildi", kapali: "kapalı", onerildi: "önerildi"};
  let d_ = {is: null, duzey: null, duzeyler: null, secili: null, sekme: "gerekce", son: null};

  function duzeyHtml(kilitli) {
    const v = d_.duzeyler;
    return `<div class="inisiyatif" role="group" aria-label="İnisiyatif düzeyi"><div class="inisiyatif-bas"><div><h2>İnisiyatif düzeyi</h2>
      <span class="bilgi">${kilitli ? `Bu iş <b>düzey ${kilitli.duzey}</b> ile yürüyor; düzey işin başında sabitlenir.` : `Operatörün Kaptan'a verdiği serbestlik. Kodla uygulanır: model ne derse desin sınır aşılmaz. Varsayılan: ${v.varsayilan}.`}</span></div>
      <span class="rozet uyari duz">${esc(v.not)}</span></div>
      <div class="duzeyler">${Object.entries(v.duzeyler).map(([n, x]) => `<button type="button" class="duzey" data-duzey="${n}" aria-pressed="${String((kilitli ? kilitli.duzey : d_.duzey) == n)}" ${kilitli ? "disabled" : ""}>
        <span class="no">${n}</span><b>${esc(x.ad)}</b><small>${esc(x.izin)}</small></button>`).join("")}</div></div>`;
  }

  /* İş kaydından tuval düğümleri: planlanan adımlar ana düğüm; teşhis, onarım, yeniden deneme, beceri değişikliği alt düğüm. */
  function dugumler(d) {
    const plan = (d.plan && (d.plan.adimlar || (d.plan.akis || {}).adimlar)) || [];
    const ana = plan.map((b, i) => ({beceri: typeof b === "string" ? b : b.beceri, sira: i, durum: d.durum === "oneri" ? "onerildi" : "bekliyor", alt: [], adimlar: []}));
    let simdiki = null;
    for (const a of d.adimlar || []) {
      const ac = String(a.aciklama || "");
      const tur = ac.startsWith("teşhis") ? "teşhis" : ac.startsWith("onarım") ? "onarım" : ac.startsWith("gerileme") ? "gerileme sınaması" : null;
      if (tur && simdiki) { simdiki.alt.push({tur, adim: a}); continue; }
      const hedef = ana.find(n => n.beceri === a.beceri && (n.adimlar.length === 0 || n === simdiki));
      if (hedef) {
        if (hedef.adimlar.length) hedef.alt.push({tur: "yeniden deneme", adim: a});
        hedef.adimlar.push(a); hedef.durum = a.durum; simdiki = hedef;
      } else if (simdiki) simdiki.alt.push({tur: "ek adım", adim: a});
    }
    for (const c of d.degisiklikler || []) {
      const n = ana.find(x => x.beceri === c.adim) || simdiki;
      if (n) n.alt.push({tur: "beceri değişikliği", degisiklik: c});
    }
    const kar = (d.inisiyatif || {}).kararlar || [];
    ana.forEach(n => { n.karar = [...kar].reverse().find(k => k.beceri === n.beceri && k.amac === "adım"); });
    if (CANLI.includes(d.durum)) { const ilk = ana.find(n => n.durum === "bekliyor"); if (ilk && d.durum === "calisiyor" && !ana.some(n => n.durum === "calisiyor")) ilk.durum = "calisiyor"; }
    return ana;
  }

  /* Yapılı akış (sürüm 2): dal, sunucu dalı, döngü, paralel kollar, alt akış, bekleme, onay, bildirim iç içe çizilir.
     Düğüm durumu motorun izinden (ek.akis_izleri), beceri sonuçları iş kaydındaki adımlardan (adim.dugum) gelir. */
  const ISARET = {esit: "=", esit_degil: "≠", icerir: "∋", buyuk: ">", kucuk: "<"};
  function kosulMetni(c) {
    const i = Object.keys(ISARET).find(x => x in c) || "esit";
    const sol = c.adim ? `${c.adim}.${c.olcu || c.alan}` : c.degisken || `sunucu.${c.sunucu}`;
    return `${sol} ${ISARET[i]} ${c[i]}`;
  }
  function yapiliHtml(d) {
    const iz = (d.ek || {}).akis_izleri || {};
    const son = {};
    for (const a of d.adimlar || []) if (a.dugum) son[a.dugum] = a;
    const kutu = (x, ic, ek = "") => { const z = iz[x.kimlik] || {}; const a = son[x.kimlik];
      const durum = (a && a.durum) || z.durum || (d.durum === "oneri" ? "onerildi" : "bekliyor");
      return `<div class="yapi-dugum ${esc(x.tur || "beceri")}"><button type="button" class="dugum ${esc(durum)} ${d_.secili === "k:" + x.kimlik ? "secili" : ""}" data-dugum="k:${esc(x.kimlik)}">
        <div class="ust-satir"><span class="ad">${ic}</span>${rozet(durum)}</div><div class="alt-satir"><code>${esc(x.kimlik)}</code>${ek}${a && a.ozet && a.ozet.toplam ? ` · ${a.ozet.basarili}/${a.ozet.toplam} sunucu` : ""}</div></button>`; };
    const blok = (b, etiket) => `<div class="yapi-blok">${etiket ? `<div class="yapi-etiket">${etiket}</div>` : ""}${(b || []).map(dugumHtml).join('<div class="ok-asagi" aria-hidden="true">↓</div>') || '<span class="bilgi">—</span>'}</div>`;
    function dugumHtml(x) {
      const t = x.tur || "beceri", z = iz[x.kimlik] || {};
      if (t === "beceri") return kutu(x, esc(x.beceri), x.hata_durumunda === "devam" ? " · hata olsa da devam" : "") + "</div>";
      if (t === "dal") return kutu(x, `koşul: ${esc(kosulMetni(x.kosul || {}))}`) + `<div class="yapi-kollar">${blok(x.evet, `evet${z.evet ? ": " + esc(z.evet.join(", ") || "—") : z.kol === "evet" ? " (seçildi)" : ""}`)}${blok(x.hayir, `hayır${z.hayir ? ": " + esc(z.hayir.join(", ") || "—") : z.kol === "hayir" ? " (seçildi)" : ""}`)}</div></div>`;
      if (t === "sunucu_dal") return kutu(x, `${esc(x.adim)} sonucuna göre ayır`) + `<div class="yapi-kollar">${blok(x.basarili, `başarılılar${z.basarili ? ": " + esc(z.basarili.join(", ") || "—") : ""}`)}${blok(x.basarisiz, `başarısızlar${z.basarisiz ? ": " + esc(z.basarisiz.join(", ") || "—") : ""}`)}</div></div>`;
      if (t === "dongu") return kutu(x, "liste" in x ? `döngü: ${esc(x.degisken)} ∈ ${esc(JSON.stringify(x.liste))}` : `döngü: ${esc(kosulMetni(x.kadar || {}))} olana kadar`, ` · en çok ${esc(x.en_cok)}${z.yineleme ? ` · yineleme ${z.yineleme}/${z.toplam || x.en_cok}` : ""}`) + `<div class="yapi-kollar tek">${blok(x.govde, "↻ gövde")}</div></div>`;
      if (t === "paralel") return kutu(x, `paralel: ${(x.kollar || []).length} kol`) + `<div class="yapi-kollar">${(x.kollar || []).map((k, i) => blok(k, `kol ${i + 1}`)).join("")}</div><div class="yapi-etiket">⇉ birleşme</div></div>`;
      if (t === "alt_akis") return kutu(x, `alt akış: ${esc(x.akis)}`, x.girdi && Object.keys(x.girdi).length ? ` · girdi ${esc(JSON.stringify(x.girdi))}` : "") + "</div>";
      if (t === "bekle") return kutu(x, "sure_sn" in x ? `bekle ${esc(x.sure_sn)} sn` : `bekle: ${esc(x.kosul.beceri)}.${esc(x.kosul.alan)} (en çok ${esc(x.zaman_asimi_sn)} sn)`) + "</div>";
      if (t === "onay") return kutu(x, "insan onayı", ` · ${esc((x.mesaj || "").slice(0, 60))}`) + (x.reddedilirse && x.reddedilirse.length ? `<div class="yapi-kollar tek">${blok(x.reddedilirse, "reddedilirse")}</div>` : "") + "</div>";
      if (t === "bildirim") return kutu(x, `bildirim → ${esc(x.alici)}`) + "</div>";
      return kutu(x, `bitir: ${esc(x.sonuc || "basarili")}`) + "</div>";
    }
    return `<div class="tuval" aria-label="Yapılı akış tuvali"><div class="akis-yapisi">${blok(d.plan.akis.adimlar)}</div></div>`;
  }

  function tuvalHtml(d) {
    if (d.plan && d.plan.akis && d.plan.akis.bicim === "filo-akis") return yapiliHtml(d);
    const n = dugumler(d);
    if (!n.length) return `<div class="tuval">${bos(d.durum === "planlaniyor" ? "Model akışı kuruyor…" : "Akış yok", d.durum === "beceri_yok" ? "Katalogdaki beceriler bu talebi karşılamıyor." : "")}</div>`;
    return `<div class="tuval" aria-label="Akış tuvali"><div class="akis">${n.map((x, i) => `${i ? `<div class="ok-baglanti ${n[i - 1].durum === "basarili" ? "gecti" : ""}" aria-hidden="true"></div>` : ""}
      <div class="dugum-kolon"><button type="button" class="dugum ${esc(x.durum)} ${d_.secili === "a" + i ? "secili" : ""}" data-dugum="a${i}">
        <div class="ust-satir"><span class="ad">${i + 1}. ${esc(x.beceri)}</span>${rozet(x.durum)}</div>
        <div class="alt-satir">${x.adimlar.length ? (() => { const s = x.adimlar[x.adimlar.length - 1], o = s.ozet || {};
          return `v${esc(s.surum)}${x.adimlar.length > 1 ? ` · ${x.adimlar.length} çalıştırma · son` : ""}${o.toplam ? ` · ${o.basarili}/${o.toplam} sunucu` : ""}`; })() : ""}
        ${x.karar ? `<span class="inis-etiketi ${esc(x.karar.karar)}" title="${esc(x.karar.aciklama)}">R${x.karar.risk} · ${esc(KARAR_ADI[x.karar.karar] || x.karar.karar)}</span>` : ""}</div></button>
        ${x.alt.length ? `<div class="alt-dugum">${x.alt.map((a, j) => `<button type="button" class="dugum ${esc(a.adim ? a.adim.durum : "basarili")} ${d_.secili === `a${i}-${j}` ? "secili" : ""}" data-dugum="a${i}-${j}" style="margin-top:6px">
          <div class="tur">${esc(a.tur)}</div><div class="ad">${a.degisiklik ? `${esc(a.degisiklik.kayit)} ${esc(a.degisiklik.ad)} v${a.degisiklik.eski_surum}→v${a.degisiklik.yeni_surum}` : esc(a.adim.beceri)}</div>
          <div class="alt-satir">${a.degisiklik ? `risk ${a.degisiklik.risk_onceki}→${a.degisiklik.risk_yeni}${a.degisiklik.geri_alindi ? " · geri alındı" : ""}` : rozet(a.adim.durum)}</div></button>`).join("")}</div>` : ""}</div>`).join("")}</div></div>`;
  }

  function dugumDetay(d) {
    const n = dugumler(d);
    if (!d_.secili) return bos("Ayrıntı için tuvalde bir düğüme tıklayın");
    if (d_.secili.startsWith("k:")) {                 // yapılı akış düğümü
      const kim = d_.secili.slice(2);
      const adimlar = (d.adimlar || []).filter(a => a.dugum === kim);
      const iz = ((d.ek || {}).akis_izleri || {})[kim];
      if (!adimlar.length) return `<h3><code>${esc(kim)}</code></h3>${iz ? `<pre>${esc(JSON.stringify(iz, null, 1))}</pre>` : '<p class="bilgi">Henüz çalışmadı.</p>'}`;
      d_.secili = null;
      const x = adimlar[adimlar.length - 1];
      const html = `<h3><code>${esc(kim)}</code> · ${esc(x.beceri)} v${esc(x.surum)} ${rozet(x.durum)}${adimlar.length > 1 ? ` <span class="bilgi">(${adimlar.length} çalıştırma; sonuncusu)</span>` : ""}</h3>
        <dl class="kv" style="margin:8px 0"><dt>Parametreler</dt><dd><code>${esc(JSON.stringify(x.parametreler || {}))}</code></dd>${x.kimlik_calistirma ? `<dt>Kimlik</dt><dd>${esc(x.kimlik_calistirma)}</dd>` : ""}</dl>
        <div class="tablo-sar"><table><thead><tr><th>Sunucu</th><th>Durum</th><th>Çıktı / neden</th></tr></thead><tbody>${(x.sonuclar || []).map(r => `<tr><td>${esc(r.sunucu)}</td><td>${rozet(r.durum)}</td><td class="kirp"><code>${esc((r.sema_hatasi || (r.veri != null && r.veri !== "" ? JSON.stringify(r.veri) : (r.stdout || r.neden || ""))).slice(0, 300))}</code></td></tr>`).join("")}</tbody></table></div>`;
      d_.secili = "k:" + kim;
      return html;
    }
    const [a, b] = d_.secili.slice(1).split("-").map(Number);
    const x = n[a]; if (!x) return "";
    const alt = b !== undefined ? x.alt[b] : null;
    if (alt && alt.degisiklik) {
      const c = alt.degisiklik;
      return `<h3>${esc(c.kayit)} ${esc(c.ad)}: v${c.eski_surum} → v${c.yeni_surum}</h3><dl class="kv" style="margin:8px 0"><dt>Neden</dt><dd>${esc(c.neden)}</dd><dt>Risk</dt><dd>${risk(c.risk_onceki)} → ${risk(c.risk_yeni)} ${c.risk_yukseldi ? rozet("uyari", "yükseldi: onay gerekir") : ""} <span class="bilgi">${esc(c.risk_neden || "")}</span></dd>
        ${c.geri_alindi ? `<dt>Geri alındı</dt><dd>${esc(c.geri_alindi.neden)} (v${c.geri_alindi.yeni_surum})</dd>` : ""}</dl>${farkHtml(c.fark)}`;
    }
    const adim = alt ? alt.adim : x.adimlar[x.adimlar.length - 1];
    if (!adim) return `<h3>${esc(x.beceri)}</h3><p class="bilgi">Henüz çalışmadı.</p>${x.karar ? `<p>İnisiyatif: ${esc(x.karar.aciklama)}</p>` : ""}`;
    return `<h3>${alt ? esc(alt.tur) + ": " : ""}${esc(adim.beceri)} v${esc(adim.surum)} ${rozet(adim.durum)}</h3>
      <dl class="kv" style="margin:8px 0"><dt>Parametreler</dt><dd><code>${esc(JSON.stringify(adim.parametreler || {}))}</code></dd><dt>Açıklama</dt><dd>${esc(adim.aciklama || "–")}</dd>
      ${adim.onay ? `<dt>Onay</dt><dd>${esc(JSON.stringify(adim.onay))}</dd>` : ""}</dl>
      <div class="tablo-sar"><table><thead><tr><th>Sunucu</th><th>Durum</th><th>Kod</th><th>Süre</th><th>Çıktı / neden</th></tr></thead><tbody>${(adim.sonuclar || []).map(r => `<tr><td>${esc(r.sunucu)}</td><td>${rozet(r.durum)}</td><td>${esc(r.cikis_kodu ?? "")}</td><td>${esc(r.sure)}</td>
        <td class="kirp"><code>${esc((r.sema_hatasi || (r.veri != null && r.veri !== "" ? JSON.stringify(r.veri) : (r.stdout || r.neden || r.stderr || ""))).slice(0, 400))}</code></td></tr>`).join("") || `<tr><td colspan="5">${bos("Sunucu sonucu yok (yerel adım)")}</td></tr>`}</tbody></table></div>`;
  }

  function yanPanel(d) {
    if (d_.sekme === "gerekce") {
      return `<div class="iz-listesi">${(d.gerekce || []).map(g => `<div class="iz-ogesi"><div class="soru">${esc(g.soru)}${g.denemeler.length > 1 ? ` · ${g.denemeler.length} deneme` : ""}</div>
        <div class="cevap">${esc(JSON.stringify(g.sonuc)).slice(0, 300)}</div>${g.denemeler.filter(x => x.hata).map(x => `<div class="kod">kod reddetti: ${esc(x.hata).slice(0, 200)}</div>`).join("")}${g.kod_notu ? `<div class="kod">${esc(g.kod_notu)}</div>` : ""}</div>`).join("") || bos("Model henüz bir şey söylemedi")}</div>`;
    }
    if (d_.sekme === "inisiyatif") {
      const k = (d.inisiyatif || {}).kararlar || [];
      return `<div style="padding:10px 12px">${d.inisiyatif ? `<p class="bilgi" style="margin-top:0">Düzey <b>${d.inisiyatif.duzey}</b> · ${esc(d.inisiyatif.ad)}: ${esc(d.inisiyatif.izin)}</p>` : ""}<div class="zaman-cizgisi">${k.map(x => `<div class="zc ${esc(x.karar)}"><b>${esc(x.beceri)}</b> ${x.risk != null ? risk(x.risk) : ""} <span class="inis-etiketi ${esc(x.karar)}">${esc(KARAR_ADI[x.karar] || x.karar)}</span><br>
        <small>${esc(x.amac)} · ${esc(x.aciklama)}${x.sonuc ? " → " + esc(x.sonuc) : ""} · ${zaman(x.zaman).slice(11)}</small></div>`).join("") || bos("Henüz karar yok")}</div></div>`;
    }
    return `<div style="padding:10px 12px" class="zaman-cizgisi">${(d.olaylar || []).filter(o => o.tur !== "iz").map(o => `<div class="zc"><b>${esc(o.tur)}</b> <small>${zaman(o.zaman).slice(11)}</small><br><span>${esc(o.metin)}</span></div>`).join("") || bos("Olay yok")}</div>`;
  }

  async function isYukle() {
    const kap = $("#c-is");
    if (!d_.is) { kap.innerHTML = ""; $("#c-duzey").innerHTML = duzeyHtml(null); duzeyBagla(); d_.son = null; return; }
    let d; try { d = await al("/api/is?kimlik=" + encodeURIComponent(d_.is)); } catch (x) { kap.innerHTML = hataKutu(x); d_.son = null; return; }
    d_.son = d;
    $("#c-duzey").innerHTML = duzeyHtml(d.inisiyatif); duzeyBagla();
    const devr = (d.ek || {}).devralinan_teslim;
    kap.innerHTML = `<div class="kart" style="margin-top:14px"><div class="kart-bas"><div><h2>İş <code>${esc(d.kimlik)}</code> ${rozet(d.durum)}</h2><span class="bilgi">${esc(d.talep)}</span>
        ${devr ? `<div class="not uyari" style="margin-top:6px">Teslimden devralındı: ${esc(devr.sunucu)} sunucusunun '${esc(devr.profil)}' teslimi ${esc(devr.durdugu_adim)} adımında yarıda kalmıştı (teslim işi <code>${esc(devr.teslim_isi)}</code>).</div>` : ""}</div>
        <div class="dugmeler"><span class="bilgi">${esc(d.baglanti || "")} · model çağrısı ${esc(d.model_cagri)}</span>
        ${d.durum === "plan_hazir" ? `<button class="btn" id="c-vazgec">Vazgeç</button><button class="btn birincil" id="c-yurut">Akışı yürüt</button>` : ""}
        ${!CANLI.includes(d.durum) && d.durum !== "plan_hazir" ? `<button class="btn kucuk" id="c-yeni">Yeni akış</button>` : ""}</div></div>
        ${d.hata ? `<div class="kart-govde">${hataKutu(d.hata)}</div>` : ""}
        ${d.plan && d.plan.hedef ? `<div class="kart-govde" style="padding-bottom:0"><span class="bilgi">Dondurulmuş hedef (${d.plan.hedef.sayi}): <code>${esc(d.plan.hedef.sunucular.join(", "))}</code> · en yüksek risk ${risk(d.plan.risk)} · gerekçe: ${esc(d.plan.gerekce || "–")}</span></div>` : ""}
        <div class="kart-govde">${tuvalHtml(d)}</div></div>
      ${d.durum === "plan_hazir" ? `<div style="margin-top:14px">${Filo.nezamanHtml(d)}</div>` : ""}
      ${!["planlaniyor", "plan_hazir"].includes(d.durum) ? `<div id="c-denetim" style="margin-top:14px">${Filo.isDenetimiHtml(d)}</div>` : ""}
      <div class="izgara yan-panelli" style="margin-top:14px"><div><div class="kart"><div class="kart-bas"><h2>Düğüm ayrıntısı</h2></div><div class="kart-govde" id="c-detay">${dugumDetay(d)}</div></div>
        ${d.rapor ? `<div class="kart"><div class="kart-bas"><h2>Rapor</h2></div><div class="kart-govde"><pre>${esc(d.rapor)}</pre>${d.yorum ? `<div class="not" style="margin-top:8px"><b>Model yorumu</b> (öneridir): ${esc(d.yorum)}</div>` : ""}</div></div>` : ""}
        ${d.durum === "bitti" && (d.ek || {}).yapilan ? `<div class="kart"><div class="kart-bas"><h2>Bu akışı kalıcı yap</h2></div><div class="kart-govde">
          <p class="bilgi" style="margin-top:0">Beceriye dönüştür: adımların değerleri parametreye döner, sunucu adları hedefe; şema ve risk kodla üretilir; katalogda sürüm 1 olur ve Kalfa bir sonraki benzer talepte onu seçebilir. Sabit akış: aynı adımlar modele sorulmadan yeniden yürür.</p>
          <div class="alanlar"><div><label for="c-ad">Beceri adı (isteğe bağlı)</label><input id="c-ad" placeholder="ör. uygulama_surum_raporu"></div><div><label for="c-baslik">Başlık</label><input id="c-baslik" placeholder="ör. Uygulama sürüm raporu"></div></div>
          <div class="dugmeler" style="margin-top:10px"><button class="btn birincil" id="c-donustur">Beceriye dönüştür</button><button class="btn" id="c-akis">Sabit akış olarak kaydet</button></div><div id="c-kalici" style="margin-top:8px"></div></div></div>` : ""}</div>
        <div class="kart"><div class="kart-bas" style="padding-bottom:0;border:0"><div id="c-sekmeler" style="width:100%"></div></div><div id="c-yan"></div></div></div>`;
    sekmeler($("#c-sekmeler"), [["gerekce", "Gerekçe izi"], ["inisiyatif", "İnisiyatif kararları"], ["olaylar", "Olaylar"]], d_.sekme, k => { d_.sekme = k; $("#c-yan").innerHTML = yanPanel(d_.son || d); });
    const bag = (s, f) => { const e = $(s); if (e) e.addEventListener("click", f); };
    const isAc = k => { d_.is = k; d_.secili = null; history.replaceState({}, "", "/kaptan?is=" + k); isYukle(); };
    if ($("#c-denetim")) Filo.isDenetimiBagla($("#c-denetim"), d, isYukle, isAc);
    if (d.durum === "plan_hazir") Filo.nezamanBagla(kap, d, isYukle);
    bag("#c-yurut", async () => { try { await gonder("/api/is/yurut", {kimlik: d.kimlik, kip: "simdi"}); isYukle(); } catch (x) { bildir(x.message); } });
    bag("#c-vazgec", async () => { try { await gonder("/api/is/vazgec", {kimlik: d.kimlik}); isYukle(); } catch (x) { bildir(x.message); } });
    bag("#c-yeni", () => { d_.is = null; d_.secili = null; history.replaceState({}, "", "/kaptan"); isYukle(); });
    bag("#c-donustur", async () => { try { const r = await gonder("/api/beceriye-donustur", {kimlik: d.kimlik, ad: $("#c-ad").value.trim(), baslik: $("#c-baslik").value.trim()});
      $("#c-kalici").innerHTML = `<div class="not">${rozet("katalogda", "katalogda")} <a href="/beceriler?ad=${esc(r.beceri)}"><b>${esc(r.beceri)}</b></a> v${r.surum} · ${esc(r.tur)} ${risk(r.risk)} · girdi: <code>${esc(Object.keys(r.girdi || {}).join(", ") || "yok")}</code> · etiketler: ${esc((r.etiketler || []).join(", "))}</div>`; } catch (x) { $("#c-kalici").innerHTML = hataKutu(x); } });
    bag("#c-akis", async () => { try { const r = await gonder("/api/akis/kaydet", {kimlik: d.kimlik}); $("#c-kalici").innerHTML = `<div class="not">Sabit akış kaydedildi: <code>${esc(r.akis)}</code> · <code>python -m filo akis calistir ${esc(r.akis)}</code></div>`; } catch (x) { $("#c-kalici").innerHTML = hataKutu(x); } });
  }

  function duzeyBagla() {
    $$("[data-duzey]").forEach(b => b.addEventListener("click", () => { d_.duzey = +b.dataset.duzey; $$("[data-duzey]").forEach(x => x.setAttribute("aria-pressed", String(x === b))); }));
  }

  async function sonIsler() {
    const l = await al("/api/isler?ajan=kaptan,teslim");
    $("#c-son").innerHTML = l.slice(0, 14).map(x => `<div style="padding:6px 0;border-bottom:1px solid var(--cizgi)"><a href="/kaptan?is=${esc(x.kimlik)}" data-is="${esc(x.kimlik)}"><code>${esc(x.kimlik)}</code></a> ${rozet(x.durum)} <span class="rozet duz">${esc(x.ajan)}</span><br><span class="bilgi">${esc((x.talep || "").slice(0, 100))}</span></div>`).join("") || bos("Henüz Kaptan işi yok");
  }

  sayfa("kaptan", {baslik: "Kaptan · akış tuvali", urun: "kaptan", async ciz(kap) {
    d_ = {is: new URLSearchParams(location.search).get("is"), duzey: null, duzeyler: await al("/api/kaptan/duzeyler"), secili: null, sekme: "gerekce", son: null};
    d_.duzey = d_.duzeyler.varsayilan;
    const bg = await al("/api/baglantilar");
    kap.innerHTML = `<div class="sayfa"><div class="baslik-satiri"><div><div class="urun-baslik"><span class="urun-rozeti">Kaptan</span><h1>Akış tuvali</h1></div>
        <p>Talepten bir beceri akışı kurar ve adım adım yürütür. Adım hata verir ya da çıktısı şemaya uymazsa salt-okur becerilerle teşhis koyar, onarım dener, gerekirse beceriyi yeni sürümle değiştirir; olmazsa insana devreder. Ne kadarını kendi başına yapacağını inisiyatif düzeyi belirler.</p></div></div>
      <div id="c-duzey"></div>
      <div class="izgara yan-panelli" style="margin-top:14px"><div class="kart"><div class="kart-bas"><h2>Talep</h2></div><div class="kart-govde">
        <textarea id="c-metin" rows="3" aria-label="Talep" placeholder="ör. PA-APP-01 ve PA-APP-02'de uygulama_surumu betiğini çalıştır, sonucu CSV yap, ops@lab.yerel adresine gönder"></textarea>
        <div class="dugmeler" style="margin-top:8px"><select id="c-baglanti" aria-label="Model bağlantısı" style="width:auto">${bg.baglantilar.map(b => `<option value="${esc(b.ad)}" ${b.ad === bg.varsayilan ? "selected" : ""}>${esc(b.ad)} · ${esc(b.model || b.tur)}</option>`).join("")}</select>
        <button class="btn birincil" id="c-kur">Akışı kur</button><span class="bilgi">Akış yürütülmeden önce tuvalde gösterilir.</span></div></div></div>
        <div class="kart"><div class="kart-bas"><h2>Son akışlar</h2></div><div class="kart-govde" id="c-son" style="max-height:200px;overflow:auto"></div></div></div>
      <div id="c-is"></div></div>`;
    $("#c-kur").addEventListener("click", async () => {
      const metin = $("#c-metin").value.trim(); if (!metin) return bildir("Talep yazın");
      try { const r = await gonder("/api/talep", {metin, ajan: "kaptan", baglanti: $("#c-baglanti").value, inisiyatif: d_.duzey});
        d_.is = r.kimlik; d_.secili = null; history.replaceState({}, "", "/kaptan?is=" + r.kimlik); isYukle(); } catch (x) { bildir(x.message); }
    });
    kap.addEventListener("click", e => {
      const n = e.target.closest("[data-dugum]"); if (n && d_.son) { d_.secili = n.dataset.dugum; $$(".dugum").forEach(x => x.classList.toggle("secili", x === n)); $("#c-detay").innerHTML = dugumDetay(d_.son); return; }
      const a = e.target.closest("[data-is]"); if (a) { e.preventDefault(); e.stopPropagation(); d_.is = a.dataset.is; d_.secili = null; history.replaceState({}, "", "/kaptan?is=" + a.dataset.is); isYukle(); }
    });
    await isYukle(); await sonIsler();
    zamanla(() => {
      const yazilan = document.activeElement && document.activeElement.closest && document.activeElement.closest("#c-denetim, .nezaman");
      if (!yazilan && d_.son && [...CANLI, ...Filo.BEKLEYEN_DURUM].includes(d_.son.durum)) isYukle(); }, 1500);
    zamanla(sonIsler, 10000);
  }});
})();
