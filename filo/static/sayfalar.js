/* Konsolun ortak sayfaları: Genel bakış, Onaylar, Envanter, Ajanlar, Teslim politikaları, Beceriler, Bench,
   Karşılaştırma, Model bağlantıları, Denetim izi. Kalfa ve Kaptan ayrı dosyalardadır. */
"use strict";
(() => {
  const {$, $$, esc, al, gonder, rozet, risk, zaman, bildir, bos, hataKutu, tablo, sekmeler, farkHtml, sayfa, zamanla} = Filo;
  const baslik = (b, alt, sag = "") => `<div class="baslik-satiri"><div><h1>${esc(b)}</h1>${alt ? `<p>${alt}</p>` : ""}</div><div class="dugmeler">${sag}</div></div>`;
  const isBag = (x) => `<a href="/${x.ajan === "kaptan" ? "kaptan" : "kalfa"}?is=${esc(x.kimlik)}"><code>${esc(x.kimlik)}</code></a>`;

  /* ---------------------------------------------------------------- Genel bakış */
  sayfa("genel", {baslik: "Genel bakış", async ciz(kap) {
    const g = await al("/api/genel");
    const toplamIs = Object.values(g.is_sayaci).reduce((a, b) => a + b, 0);
    kap.innerHTML = `<div class="sayfa">${baslik("Genel bakış", "Filo sağlığı, ajanlar, son işler ve bekleyen onaylar. Ajanlar sunucudan çekirdeğe dışarı doğru bağlanır; canlı ajanı olan sunucuda iş ajandan, olmayanda SSH'tan gider.",
      `<a class="btn birincil" href="/kalfa">Kalfa ile iş başlat</a><a class="btn" href="/kaptan">Kaptan'a akış ver</a>`)}
      <div class="izgara dort">
        <div class="kart metrik"><div class="etiket">Sunucu</div><div class="deger">${g.sunucu}</div><div class="alt">${g.linux} Linux · ${g.windows} Windows</div></div>
        <div class="kart metrik"><div class="etiket">Filo ajanı</div><div class="deger">${g.ajan.canli} <small class="bilgi">canlı</small></div><div class="alt">${g.ajan.yok} ajan yok · ${g.ajan.kayitsiz} kayıtsız (SSH)</div></div>
        <div class="kart metrik"><div class="etiket">Bekleyen onay</div><div class="deger">${g.bekleyen_onaylar.length}</div><div class="alt"><a href="/onaylar">Onaylar sayfası</a></div></div>
        <div class="kart metrik"><div class="etiket">Denetim izi</div><div class="deger">${g.denetim.saglam ? "sağlam" : "BOZUK"}</div><div class="alt">${g.denetim.satir} satır, özet zinciri · ${g.beceri_sayisi} beceri</div></div>
      </div>
      <div class="izgara yan-panelli" style="margin-top:14px">
        <div class="kart"><div class="kart-bas"><h2>Son işler</h2><span class="bilgi">${toplamIs} iş kaydı</span></div><div class="kart-govde" id="g-isler"></div></div>
        <div class="kart"><div class="kart-bas"><h2>Bekleyen onaylar</h2></div><div class="kart-govde" id="g-onay"></div></div>
      </div>
      <div class="izgara iki" style="margin-top:14px">
        <div class="kart"><div class="kart-bas"><h2>Yeni sunucu teslimleri</h2><a href="/teslim">Politikalar</a></div><div class="kart-govde" id="g-teslim"></div></div>
        <div class="kart"><div class="kart-bas"><h2>Son bench sonuçları</h2><a href="/bench">Bench</a></div><div class="kart-govde" id="g-bench"></div></div>
      </div></div>`;
    tablo($("#g-isler"), [{ad: "kimlik", baslik: "İş", ciz: isBag}, {ad: "ajan", baslik: "Ajan"}, {ad: "talep", baslik: "Talep", sinif: "kirp", ciz: x => esc((x.talep || "").slice(0, 120))},
      {ad: "durum", baslik: "Durum", ciz: x => rozet(x.durum)}, {ad: "olusturma", baslik: "Zaman", ciz: x => zaman(x.olusturma)}], g.son_isler, {suzgec: false, bosBaslik: "Henüz iş yok"});
    $("#g-onay").innerHTML = g.bekleyen_onaylar.length ? g.bekleyen_onaylar.map(o => `<div style="padding:6px 0;border-bottom:1px solid var(--cizgi)"><b>${esc(o.beceri)}</b> ${risk(o.risk)} <span class="bilgi">${esc(o.hedefler.join(", "))}</span><br><span class="bilgi">${esc((o.talep || "").slice(0, 100))}</span></div>`).join("") + `<p><a class="btn kucuk" href="/onaylar">Karar ver</a></p>` : bos("Bekleyen onay yok");
    const t = Object.entries(g.teslimler);
    $("#g-teslim").innerHTML = t.length ? `<table><thead><tr><th>Sunucu</th><th>Profil</th><th>Sonuç</th><th>Zaman</th></tr></thead><tbody>${t.map(([s, x]) => `<tr><td>${esc(s)}</td><td>${esc(x.profil)}</td><td>${rozet(x.durum)}</td><td>${zaman(x.zaman)}</td></tr>`).join("")}</tbody></table>` : bos("Henüz teslim yok", "Yeni sunucuya ajan kurulunca politika kendiliğinden başlar.");
    $("#g-bench").innerHTML = g.bench.length ? `<table><thead><tr><th>Koşu</th><th>Kol</th><th>Seviye</th><th>Geçen</th><th>Zararlı</th></tr></thead><tbody>${g.bench.map(r => `<tr><td>${esc(r.kosu)}</td><td>${esc(r.kol)}</td><td>${esc(r.seviye)}</td><td>${r.gecen}/${r.n}</td><td>${r.zararli}</td></tr>`).join("")}</tbody></table>` : bos("Koşu yok");
  }});

  /* ---------------------------------------------------------------- Onaylar */
  sayfa("onaylar", {baslik: "Onaylar", async ciz(kap) {
    kap.innerHTML = `<div class="sayfa">${baslik("Onaylar", "Risk 3 (servis/paket değişikliği) ve 4 (yıkıcı) adımlar insan onayı ister. Onay plana bağlıdır: beceri, sürüm ya da hedef değişirse geçersiz olur. Kuru çalıştırma çıktısı neyin değişeceğini gösterir.")}
      <div class="kart"><div class="kart-bas"><h2>Bekleyen</h2></div><div class="kart-govde" id="o-bekleyen"></div></div>
      <div class="kart"><div class="kart-bas"><h2>Geçmiş</h2></div><div class="kart-govde" id="o-gecmis"></div></div></div>`;
    async function yukle() {
      const b = await al("/api/onaylar"), h = await al("/api/onaylar?hepsi=1");
      $("#o-bekleyen").innerHTML = b.length ? b.map(o => `<div class="kart" style="margin-bottom:10px"><div class="kart-bas"><div><b>${esc(o.beceri)}</b> v${o.surum} ${risk(o.risk)} <span class="bilgi">${esc(o.ajan)} · iş <code>${esc(o.is_kimligi)}</code> · ${zaman(o.zaman)}</span></div>
        <div class="dugmeler"><button class="btn birincil" data-onay="ver" data-k="${esc(o.kimlik)}">Onayla</button><button class="btn tehlike" data-onay="reddet" data-k="${esc(o.kimlik)}">Reddet</button></div></div>
        <div class="kart-govde"><dl class="kv"><dt>Talep</dt><dd>${esc(o.talep)}</dd><dt>Hedef (dondurulmuş)</dt><dd>${esc(o.hedefler.join(", "))}</dd><dt>Parametreler</dt><dd><code>${esc(JSON.stringify(o.parametreler))}</code></dd><dt>Risk gerekçesi</dt><dd>${esc(o.risk_neden || "")}</dd></dl>
        ${(o.kuru || []).length ? `<h3 style="margin:10px 0 4px">Kuru çalıştırma</h3>${o.kuru.map(r => `<div><b>${esc(r.sunucu)}</b> ${rozet(r.durum)}<pre>${esc((r.stdout || r.neden || "").trim())}</pre></div>`).join("")}` : ""}</div></div>`).join("") : bos("Bekleyen onay yok");
      tablo($("#o-gecmis"), [{ad: "zaman", baslik: "Zaman", ciz: x => zaman(x.zaman)}, {ad: "beceri", baslik: "Beceri"}, {ad: "risk", baslik: "Risk", ciz: x => risk(x.risk)},
        {ad: "hedefler", baslik: "Hedef", ciz: x => esc((x.hedefler || []).join(", "))}, {ad: "durum", baslik: "Karar", ciz: x => rozet(x.durum)}, {ad: "karar_veren", baslik: "Karar veren"}], h.filter(x => x.durum !== "bekliyor"));
    }
    kap.addEventListener("click", async e => { const b = e.target.closest("[data-onay]"); if (!b) return;
      try { await gonder("/api/onay", {kimlik: b.dataset.k, karar: b.dataset.onay}); bildir(b.dataset.onay === "ver" ? "Onaylandı" : "Reddedildi"); yukle(); } catch (x) { bildir(x.message); } });
    await yukle(); zamanla(yukle, 5000);
  }});

  /* ---------------------------------------------------------------- Envanter */
  sayfa("envanter", {baslik: "Envanter", async ciz(kap) {
    const [e, a] = await Promise.all([al("/api/envanter"), al("/api/ajanlar")]);
    const aj = Object.fromEntries(a.sunucular.map(x => [x.sunucu, x]));
    kap.innerHTML = `<div class="sayfa">${baslik("Envanter", "Sunucular, gruplar, öznitelikler ve fiili taşıyıcı. Kimlik alanı bir profil adıdır; anahtar burada durmaz. Seçici sözdizimi: <code>PA* grup:web os:linux ortam=test !PA-DB-01</code>.")}
      <div class="kart"><div class="kart-bas"><h2>Hedef seçici</h2></div><div class="kart-govde"><div class="dugmeler" style="flex-wrap:nowrap"><input id="e-secici" placeholder="ör. PA* grup:web" aria-label="Hedef seçici"><button class="btn" id="e-onizle">Önizle</button><button class="btn birincil" id="e-sina">Erişim sınaması</button></div><div id="e-sonuc" style="margin-top:8px"></div></div></div>
      <div class="kart"><div class="kart-bas"><h2>Sunucular</h2><span class="bilgi">gruplar: ${esc(Object.keys(e.gruplar).join(", "))}</span></div><div class="kart-govde" id="e-tablo"></div></div></div>`;
    tablo($("#e-tablo"), [{ad: "ad", baslik: "Ad", ciz: x => `<b>${esc(x.ad)}</b>`}, {ad: "aile", baslik: "OS / aile", ciz: x => `${esc(x.os)} / ${esc(x.aile)}`},
      {ad: "gruplar", baslik: "Gruplar", ciz: x => esc(x.gruplar.join(", "))}, {ad: "oznitelikler", baslik: "Öznitelikler", sinif: "kirp", ciz: x => esc(Object.entries(x.oznitelikler).map(([k, v]) => `${k}=${v}`).join(" "))},
      {ad: "yol", baslik: "Fiili taşıyıcı", sirala: x => (aj[x.ad] || {}).fiili_yol, ciz: x => { const y = (aj[x.ad] || {}).fiili_yol || x.tasiyici; return y === "ajan" ? rozet("basarili", "ajan") : rozet("bekliyor", y); }},
      {ad: "surum", baslik: "Ajan sürümü", sirala: x => (aj[x.ad] || {}).surum, ciz: x => esc((aj[x.ad] || {}).surum || "–")},
      {ad: "kalp", baslik: "Son kalp atışı", sirala: x => (aj[x.ad] || {}).son_kalp, ciz: x => zaman((aj[x.ad] || {}).son_kalp)},
      {ad: "adres", baslik: "Adres", ciz: x => `<code>${esc(x.adres)}:${esc(x.port)}</code>`}], e.sunucular, {yerTutucu: "Sunucu, grup, öznitelik süz…"});
    $("#e-onizle").addEventListener("click", async () => { try { const v = await al("/api/envanter/sec?hedef=" + encodeURIComponent($("#e-secici").value));
      $("#e-sonuc").innerHTML = `${v.sunucular.length} sunucu: <code>${esc(v.sunucular.join(", ") || "yok")}</code>`; } catch (x) { $("#e-sonuc").innerHTML = hataKutu(x); } });
    $("#e-sina").addEventListener("click", async () => { $("#e-sonuc").innerHTML = "sınanıyor…";
      try { const v = await gonder("/api/envanter/sina", {hedef: $("#e-secici").value || "*"});
        $("#e-sonuc").innerHTML = `${rozet("basarili", v.erisilen.length + " erişilebilir")} ${v.erisilemeyen.length ? rozet("hatali", v.erisilemeyen.length + " erişilemedi") : ""}
          ${v.erisilemeyen.map(r => `<div><b>${esc(r.sunucu)}</b>: ${esc(r.neden)}</div>`).join("")}${v.oykunme.length ? `<div class="not uyari" style="margin-top:6px">Öykünme: ${esc(v.oykunme.join(", "))} (WinRM kapalı)</div>` : ""}`;
      } catch (x) { $("#e-sonuc").innerHTML = hataKutu(x); } });
  }});

  /* ---------------------------------------------------------------- Ajanlar */
  sayfa("ajanlar", {baslik: "Ajanlar", async ciz(kap) {
    kap.innerHTML = `<div class="sayfa">${baslik("Filo ajanları", "Go ile yazılmış <code>filo-ajan</code> sunucuda port açmaz; çekirdeğin ajan kapısına dışarı doğru bağlanır (kayıt, kalp atışı, uzun yoklama). Her istek ve her iş paketi imzalıdır. Kurulum ve onarım SSH'tan yapılır; kurulumdan sonra işler ajandan gider.")}
      <div id="a-kapi"></div>
      <div class="izgara yan-panelli" style="margin-top:14px">
        <div class="kart"><div class="kart-bas"><h2>Sunucular</h2><div class="dugmeler"><button class="btn birincil" data-eylem="kur">Seçililere kur</button><button class="btn" data-eylem="onar">Onar</button><button class="btn tehlike" data-eylem="kaldir">Kaldır</button></div></div><div class="kart-govde" id="a-tablo"></div></div>
        <div>
          <div class="kart"><div class="kart-bas"><h2>Kurulum belirteci</h2></div><div class="kart-govde"><p class="bilgi" style="margin-top:0">Elle kurulum için tek kullanımlık, sunucuya bağlı, süreli belirteç. Yalnız bir kez gösterilir; diskte özeti saklanır.</p>
            <label for="a-sunucu">Sunucu</label><select id="a-sunucu"></select><div class="dugmeler" style="margin-top:8px"><button class="btn" id="a-belirtec">Belirteç üret</button></div><div id="a-belirtec-sonuc" style="margin-top:8px"></div></div></div>
          <div class="kart"><div class="kart-bas"><h2>Derleme</h2></div><div class="kart-govde" id="a-derleme"></div></div>
          <div class="kart"><div class="kart-bas"><h2>Son ajan işleri</h2></div><div class="kart-govde" id="a-isler"></div></div>
        </div></div></div>`;
    let secili = new Set(), tbl = null;
    async function yukle() {
      const v = await al("/api/ajanlar");
      $("#a-kapi").innerHTML = v.kapi === true ? `<div class="not">Ajan kapısı çalışıyor: <code>127.0.0.1:${esc(v.ayar.kapi_port)}</code> · sunucular için adres <code>${esc(v.ayar.sunucular_icin_adres)}</code> · canlılık sınırı ${esc(v.ayar.canli_sinir_sn)} sn · iş alma süresi ${esc(v.ayar.alim_suresi_sn)} sn (almazsa SSH'a düşülür).</div>`
        : `<div class="not uyari">Ajan kapısı çalışmıyor (${esc(v.kapi)}). Bütün işler SSH'tan gider. Başlatmak için: <code>python -m filo web</code> (kapı aynı süreçte) ya da <code>python -m filo ajan kapi</code>.</div>`;
      const d = v.derleme;
      $("#a-derleme").innerHTML = d.surum ? `<dl class="kv"><dt>Sürüm</dt><dd>${esc(d.surum)}</dd><dt>İmaj</dt><dd><code>${esc(d.imaj)}</dd><dt>Zaman</dt><dd>${zaman(d.zaman)}</dd></dl><table style="margin-top:8px"><tbody>${(d.ikililer || []).map(([o, a]) => `<tr><td><code>${esc(a)}</code></td><td class="kirp"><code title="${esc(o)}">${esc(o.slice(0, 16))}…</code></td></tr>`).join("")}</tbody></table><p class="bilgi">Windows ikilisi derlenir ama gerçek Windows'ta denenmedi.</p>`
        : bos("Derlenmemiş", "python -m filo ajan derle");
      $("#a-sunucu").innerHTML = v.sunucular.filter(s => s.os === "linux").map(s => `<option>${esc(s.sunucu)}</option>`).join("");
      const kol = [{ad: "sec", baslik: "", sirala: false, ciz: s => s.os === "linux" ? `<input type="checkbox" aria-label="${esc(s.sunucu)} seç" data-sec="${esc(s.sunucu)}" ${secili.has(s.sunucu) ? "checked" : ""}>` : ""},
        {ad: "sunucu", baslik: "Sunucu", ciz: s => `<b>${esc(s.sunucu)}</b>${s.teslim === "bekliyor" ? ' <span class="rozet uyari duz">teslim bekliyor</span>' : ""}`},
        {ad: "durum", baslik: "Durum", ciz: s => rozet(s.durum)}, {ad: "surum", baslik: "Sürüm", ciz: s => esc(s.surum || "–")},
        {ad: "son_kalp", baslik: "Son kalp", ciz: s => zaman(s.son_kalp)}, {ad: "son_temas_sn", baslik: "Son temas", ciz: s => s.son_temas_sn == null ? "–" : esc(s.son_temas_sn) + " sn"},
        {ad: "dagitim", baslik: "Dağıtım (ajan)", sirala: s => s.sistem.dagitim_ad, ciz: s => esc(s.sistem.dagitim_ad || "–")},
        {ad: "hizmet", baslik: "Hizmet", sirala: s => s.sistem.hizmet_yoneticisi, ciz: s => esc(s.sistem.hizmet_yoneticisi || "–")},
        {ad: "fiili_yol", baslik: "İş yolu", ciz: s => s.fiili_yol === "ajan" ? rozet("basarili", "ajan") : rozet("bekliyor", s.fiili_yol)}];
      if (tbl) tbl.yenile(v.sunucular); else tbl = tablo($("#a-tablo"), kol, v.sunucular, {yerTutucu: "Süz…"});
      const isler = await al("/api/isler?ajan=kalfa");
      $("#a-isler").innerHTML = isler.filter(x => /ajan (kur|onar|kaldir)/.test(x.talep || "")).slice(0, 6).map(x => `<div>${isBag(x)} ${rozet(x.durum)} <span class="bilgi">${esc(x.talep)}</span></div>`).join("") || bos("Yok");
    }
    kap.addEventListener("change", e => { const c = e.target.closest("[data-sec]"); if (c) c.checked ? secili.add(c.dataset.sec) : secili.delete(c.dataset.sec); });
    kap.addEventListener("click", async e => {
      const b = e.target.closest("[data-eylem]"); if (!b) return;
      if (!secili.size) return bildir("Önce sunucu seçin");
      const hedef = [...secili].join(",");
      try { const k = await gonder("/api/ajan/eylem", {eylem: b.dataset.eylem, hedef});
        bildir(`İş ${k.kimlik} başladı: risk 3 olduğu için onay ister (Onaylar sayfası)`); } catch (x) { bildir(x.message); }
    });
    $("#a-belirtec").addEventListener("click", async () => {
      try { const v = await gonder("/api/ajan/belirtec", {sunucu: $("#a-sunucu").value});
        $("#a-belirtec-sonuc").innerHTML = `<pre>${esc(v.belirtec)}</pre><p class="bilgi">Sunucuda <code>/etc/filo-ajan/ajan.json</code> içine <code>"belirtec"</code> olarak yazın (0600). Bu sayfadan ayrılınca bir daha gösterilmez.</p>`;
      } catch (x) { $("#a-belirtec-sonuc").innerHTML = hataKutu(x); }
    });
    await yukle(); zamanla(yukle, 5000);
  }});

  /* ---------------------------------------------------------------- Teslim politikaları */
  sayfa("teslim", {baslik: "Teslim politikaları", async ciz(kap) {
    const v = await al("/api/teslim");
    const p = v.politika;
    kap.innerHTML = `<div class="sayfa">${baslik("Yeni sunucu teslim politikaları", "Envanterde <code>teslim=bekliyor</code> işaretli bir sunucuya Filo ajanı kaydolunca ilk uyan kurala göre bir profile düşer ve profilin beceri zinciri kendiliğinden başlar. Risk 3+ adım yalnız <b>ön onaylı</b> ise onaysız çalışır. Zincir yarıda kalırsa profil Kaptan'ı belirtilen inisiyatif düzeyiyle devreye alabilir. Kaynak: <code>ayarlar/teslim_politikalari.json</code>.")}
      ${v.hatalar.length ? `<div class="not hata">${esc(v.hatalar.join("; "))}</div>` : ""}
      <div class="izgara iki">
        <div class="kart"><div class="kart-bas"><h2>Kurallar</h2></div><div class="kart-govde"><table><thead><tr><th>#</th><th>Koşul</th><th>Profil</th></tr></thead><tbody>${p.kurallar.map((k, i) => `<tr><td>${i + 1}</td><td><code>${esc(k.ad_kalibi ? "ad ~ " + k.ad_kalibi : "grup = " + k.grup)}</code></td><td><b>${esc(k.profil)}</b></td></tr>`).join("")}</tbody></table>
          <h3 style="margin:14px 0 6px">Sunuculara göre</h3><div id="t-sunucular"></div></div></div>
        <div class="kart"><div class="kart-bas"><h2>Teslim geçmişi</h2></div><div class="kart-govde" id="t-gecmis"></div></div>
      </div>
      ${Object.entries(p.profiller).map(([ad, pr]) => `<div class="kart"><div class="kart-bas"><div><h2>${esc(ad)} · ${esc(pr.baslik)}</h2><span class="bilgi">${esc(pr.aciklama || "")}</span></div>
        <div>${pr.yarida_kalirsa === "kaptan" ? `<span class="rozet uyari duz">yarıda kalırsa Kaptan devralır · düzey ${esc(pr.kaptan_inisiyatif)}</span>` : `<span class="rozet duz">yarıda kalırsa insana devredilir</span>`}
        ${pr.rapor ? ` <span class="rozet bilgi duz">rapor: ${esc(pr.rapor.alici)}</span>` : ""}</div></div>
        <div class="kart-govde"><table><thead><tr><th>#</th><th>Beceri</th><th>Parametreler</th><th>Onay</th></tr></thead><tbody>${pr.adimlar.map((a, i) => `<tr><td>${i + 1}</td><td><code>${esc(a.beceri)}</code></td><td class="kirp"><code>${esc(JSON.stringify(a.parametre || {}))}</code></td><td>${a.on_onayli ? rozet("basarili", "ön onaylı") : rozet("bekliyor", "risk 3+ ise insan onayı")}</td></tr>`).join("")}</tbody></table></div></div>`).join("")}
    </div>`;
    tablo($("#t-sunucular"), [{ad: "sunucu", baslik: "Sunucu"}, {ad: "profil", baslik: "Profil", ciz: s => esc(s.profil || "–")},
      {ad: "teslim", baslik: "İşaret", ciz: s => s.teslim ? rozet(s.teslim === "bekliyor" ? "bekliyor" : "basarili", s.teslim) : "–"},
      {ad: "x", baslik: "", sirala: false, ciz: s => s.profil ? `<button class="btn kucuk" data-teslim="${esc(s.sunucu)}">Teslimi başlat</button>` : ""}], v.sunucular, {suzgec: false});
    const g = Object.entries(v.teslimler);
    $("#t-gecmis").innerHTML = g.length ? `<table><thead><tr><th>Sunucu</th><th>Profil</th><th>Sonuç</th><th>İş</th><th>Zaman</th></tr></thead><tbody>${g.map(([s, x]) => `<tr><td>${esc(s)}</td><td>${esc(x.profil)}</td><td>${rozet(x.durum)}</td><td><code>${esc(x.is)}</code></td><td>${zaman(x.zaman)}</td></tr>`).join("")}</tbody></table>` : bos("Henüz teslim yok", "Deneme: python -m filo lab yeni-sunucu PA-WEB-02, sonra Ajanlar sayfasından ajan kurun.");
    kap.addEventListener("click", async e => { const b = e.target.closest("[data-teslim]"); if (!b) return;
      if (!confirm(`${b.dataset.teslim} için teslim profili şimdi elle başlatılsın mı? (Sunucuda paket, kullanıcı, servis değişikliği yapar.)`)) return;
      try { const k = await gonder("/api/teslim/baslat", {sunucu: b.dataset.teslim}); bildir(`Teslim işi ${k.kimlik} başladı`); } catch (x) { bildir(x.message); } });
  }});

  /* ---------------------------------------------------------------- Beceriler */
  sayfa("beceriler", {baslik: "Beceriler", async ciz(kap) {
    const v = await al("/api/beceriler");
    kap.innerHTML = `<div class="sayfa">${baslik("Beceri kataloğu", "Tipli girdi ve çıktı şeması, kodla sınıflanan risk, kuru çalıştırma, geri alma ve sürüm geçmişi. Kaptan'ın değiştirdiği beceri yeni sürüm olarak kaydedilir; eski sürüme dönüş de yeni sürümdür.")}
      <div class="izgara yan-panelli"><div class="kart"><div class="kart-bas"><h2>Katalog</h2><span class="bilgi">${v.beceriler.length} beceri · ${v.betikler.length} betik</span></div><div class="kart-govde" id="b-tablo"></div></div>
      <div><div class="kart"><div class="kart-bas"><h2>Tariften yeni beceri</h2></div><div class="kart-govde">
        <p class="bilgi" style="margin-top:0">Model taslağı yazar; kod şemayı, yer tutucuları ve riski denetler; taslak sınama sunucusunda kuru çalıştırmadan geçmeden kataloğa girmez.</p>
        <label for="b-tarif">Tarif</label><textarea id="b-tarif" placeholder="ör. sunucudaki açık dosya tanıtıcısı sayısını raporla"></textarea>
        <label for="b-sunucu">Sınama sunucusu</label><select id="b-sunucu"></select>
        <div class="dugmeler" style="margin-top:8px"><button class="btn birincil" id="b-taslak">Taslak üret ve sına</button></div><div id="b-taslak-sonuc" style="margin-top:8px"></div></div></div></div></div>
      <div class="kart" id="b-detay-kart"><div class="kart-bas"><h2 id="b-detay-baslik">Beceri ayrıntısı</h2></div><div class="kart-govde" id="b-detay">${bos("Ayrıntı için katalogdan bir beceri seçin")}</div></div></div>`;
    const env = await al("/api/envanter");
    $("#b-sunucu").innerHTML = env.sunucular.filter(s => s.os === "linux").map(s => `<option>${esc(s.ad)}</option>`).join("");
    tablo($("#b-tablo"), [{ad: "ad", baslik: "Beceri", ciz: b => `<button class="btn kucuk" data-beceri="${esc(b.ad)}">${esc(b.ad)}</button>`},
      {ad: "baslik", baslik: "Başlık", sinif: "kirp"}, {ad: "tur", baslik: "Tür"}, {ad: "risk", baslik: "Risk", ciz: b => risk(b.risk) + (b.risk > b.risk_beyan ? ` <span class="bilgi" title="${esc(b.risk_neden)}">kod yükseltti</span>` : "")},
      {ad: "surum", baslik: "Sürüm", ciz: b => "v" + esc(b.surum)}, {ad: "isletim", baslik: "Komut", ciz: b => esc((b.isletim || []).join(", ") || "–")}], v.beceriler, {yerTutucu: "Beceri, etiket süz…"});
    async function detay(ad) {
      const d = await al("/api/beceri?ad=" + encodeURIComponent(ad));
      $("#b-detay-baslik").textContent = `${d.ad} · ${d.baslik}`;
      $("#b-detay").innerHTML = `<p style="margin-top:0">${esc(d.aciklama)}</p><dl class="kv"><dt>Tür</dt><dd>${esc(d.tur)}${d.tanim.islem ? " (kod işleyicisi: " + esc(d.tanim.islem) + ")" : ""}</dd><dt>Risk</dt><dd>${risk(d.risk)} ${esc(d.risk_neden)}</dd><dt>Etiketler</dt><dd>${esc(d.etiketler.join(", "))}</dd>
        <dt>Kuru / geri alma</dt><dd>${d.kuru ? "kuru var" : "kuru yok"} · ${d.geri_al ? "geri alma var" : "geri alma yok"}</dd>${d.tanim.kaynak ? `<dt>Kaynak</dt><dd><code>${esc(JSON.stringify(d.tanim.kaynak))}</code></dd>` : ""}</dl>
        <div class="izgara iki" style="margin-top:12px"><div><h3>Girdi şeması</h3><pre>${esc(JSON.stringify(d.girdi, null, 1))}</pre></div><div><h3>Çıktı şeması</h3><pre>${esc(JSON.stringify(d.cikti, null, 1))}</pre></div></div>
        <h3 style="margin:12px 0 4px">${d.tanim.adimlar ? "Zincir adımları" : "Komutlar"}</h3><pre>${esc(JSON.stringify(d.tanim.adimlar || d.tanim.komut || {}, null, 1))}</pre>
        <h3 style="margin:12px 0 4px">Sürüm geçmişi</h3><table><thead><tr><th>Sürüm</th><th>Risk</th><th>Değiştiren</th><th>Neden</th><th></th></tr></thead><tbody>${d.gecmis.map(g => `<tr><td>v${g.surum}${g.guncel ? " (güncel)" : ""}</td><td>${risk(g.risk)}</td><td>${esc((g.degisiklik || {}).degistiren || "")}</td><td>${esc((g.degisiklik || {}).neden || "")}</td>
        <td>${g.guncel ? "" : `<button class="btn kucuk" data-fark="${g.surum}" data-ad="${esc(d.ad)}">Fark</button> <button class="btn kucuk" data-geri="${g.surum}" data-ad="${esc(d.ad)}">Bu sürüme dön</button>`}</td></tr>`).join("")}</tbody></table><div id="b-fark"></div>`;
      $("#b-detay-kart").scrollIntoView({behavior: "smooth", block: "start"});
    }
    kap.addEventListener("click", async e => {
      const b = e.target.closest("[data-beceri]"); if (b) return detay(b.dataset.beceri);
      const f = e.target.closest("[data-fark]"); if (f) { const d = await al("/api/beceri"+ "?ad=" + encodeURIComponent(f.dataset.ad)); const g = d.gecmis.find(x => x.guncel);
        const v2 = await al(`/api/beceri/fark?ad=${encodeURIComponent(f.dataset.ad)}&s1=${f.dataset.fark}&s2=${g.surum}`); $("#b-fark").innerHTML = farkHtml(v2.fark); return; }
      const r = e.target.closest("[data-geri]"); if (r) { if (!confirm(`${r.dataset.ad} v${r.dataset.geri} içeriğine dönülsün mü? (yeni sürüm olarak yazılır)`)) return;
        try { await gonder("/api/beceri/geri-don", {ad: r.dataset.ad, surum: +r.dataset.geri}); bildir("Yeni sürüm yazıldı"); detay(r.dataset.ad); } catch (x) { bildir(x.message); } }
    });
    $("#b-taslak").addEventListener("click", async () => {
      const s = $("#b-taslak-sonuc"); s.innerHTML = "model taslak yazıyor…";
      try { const g = await gonder("/api/beceri/tarif", {tarif: $("#b-tarif").value, sunucu: $("#b-sunucu").value});
        const bekle = async () => { const d = await al("/api/gorev?kimlik=" + g.kimlik);
          if (d.durum === "calisiyor") return setTimeout(bekle, 1500);
          if (d.durum === "hata") return s.innerHTML = hataKutu(d.hata);
          const r = d.sonuc; s.innerHTML = r.durum === "katalogda" ? `${rozet("katalogda", "kataloğa girdi")} <b>${esc(r.tanim.ad)}</b> v1 ${risk(r.tanim.risk)}<p class="bilgi">${esc(r.sinama)}</p><pre>${esc(r.stdout)}</pre>`
            : `${rozet("taslak", "taslak olarak kaldı")}<p>${esc(r.neden)}</p><p class="bilgi">${esc(r.taslak || "")}</p>`; };
        bekle(); } catch (x) { s.innerHTML = hataKutu(x); }
    });
    const q = new URLSearchParams(location.search).get("ad"); if (q) detay(q);
  }});

  /* ---------------------------------------------------------------- Bench */
  sayfa("bench", {baslik: "Bench", async ciz(kap) {
    const [v, bg] = await Promise.all([al("/api/bench"), al("/api/baglantilar")]);
    const kosular = [...new Set(v.sonuclar.map(r => r.kosu))];
    kap.innerHTML = `<div class="sayfa">${baslik("Filo Admin Bench", "Senaryolar laboratuvara bozukluk koyar; hakem laboratuvarın gerçek durumuna (paket, servis, dosya, Mailpit kutusu) bakar, kolun beyanına değil. Zararlı sonuçlar (yanlış sunucuda değişiklik, sahte başarı, onaysız değişiklik) ayrı sayılır. Kollar aynı modelle: <b>yardimsiz</b> (yalnız ham kabuk ve ham e-posta), <b>kalfa</b>, <b>kaptan</b>.")}
      <div class="kart"><div class="kart-bas"><h2>Koşular yan yana</h2></div><div class="kart-govde" id="bn-yan"></div></div>
      <div class="kart"><div class="kart-bas"><h2>Senaryolar</h2><div class="dugmeler"><select id="bn-baglanti" aria-label="Bağlantı" style="width:auto">${bg.baglantilar.map(b => `<option ${b.ad === bg.varsayilan ? "selected" : ""}>${esc(b.ad)}</option>`).join("")}</select>
        <label style="margin:0;display:flex;gap:4px;align-items:center"><input type="checkbox" value="kalfa" class="bn-kol" checked>kalfa</label><label style="margin:0;display:flex;gap:4px;align-items:center"><input type="checkbox" value="kaptan" class="bn-kol" checked>kaptan</label><label style="margin:0;display:flex;gap:4px;align-items:center"><input type="checkbox" value="yardimsiz" class="bn-kol">yardimsiz</label>
        <button class="btn" id="bn-dogrula">Seçilenleri doğrula</button><button class="btn birincil" id="bn-kos">Seçilenleri koş</button></div></div><div class="kart-govde"><div id="bn-durum"></div><div id="bn-senaryolar"></div></div></div></div>`;
    const tablo_ = {};
    v.sonuclar.forEach(r => { const a = `${r.kol}|${r.seviye}`; (tablo_[a] = tablo_[a] || {})[r.kosu] = r; });
    const satirlar = Object.keys(tablo_).sort();
    $("#bn-yan").innerHTML = kosular.length ? `<div class="tablo-sar"><table><thead><tr><th>Kol</th><th>Seviye</th>${kosular.map(k => `<th>${esc(k)}<br><span class="bilgi">geçen · zararlı · ort. çağrı</span></th>`).join("")}</tr></thead><tbody>${satirlar.map(a => { const [kol, sv] = a.split("|");
      return `<tr><td><b>${esc(kol)}</b></td><td>${esc(sv)}</td>${kosular.map(k => { const r = tablo_[a][k]; return `<td>${r ? `${r.gecen}/${r.n} · ${r.zararli} · ${r.cagri}` : '<span class="bilgi">ölçülmedi</span>'}</td>`; }).join("")}</tr>`; }).join("")}</tbody></table></div>` : bos("Henüz koşu yok");
    tablo($("#bn-senaryolar"), [{ad: "sec", baslik: "", sirala: false, ciz: s => `<input type="checkbox" class="bn-s" value="${esc(s.kimlik)}" aria-label="${esc(s.kimlik)} seç">`},
      {ad: "kimlik", baslik: "Senaryo", ciz: s => `<code>${esc(s.kimlik)}</code>`}, {ad: "seviye", baslik: "Seviye"}, {ad: "talep", baslik: "Talep", sinif: "kirp"},
      {ad: "kaynak_turu", baslik: "Kaynak", ciz: s => s.kaynak && s.kaynak.startsWith("http") ? `<a href="${esc(s.kaynak)}" target="_blank" rel="noreferrer">${esc(s.kaynak_turu)}</a>` : esc(s.kaynak_turu)},
      {ad: "dogrulama", baslik: "Doğrulama", sirala: s => s.dogrulama ? (s.dogrulama.gecti ? 1 : 0) : -1, ciz: s => s.dogrulama ? rozet(s.dogrulama.gecti ? "basarili" : "hatali", s.dogrulama.gecti ? "referans geçti, boş kaldı" : "sorunlu") : rozet("bekliyor", "doğrulanmadı")}], v.senaryolar, {yerTutucu: "Senaryo süz…"});
    const durumYaz = d => { $("#bn-durum").innerHTML = d.calisiyor || (d.ilerleme || []).length ? `<div class="not">${d.calisiyor ? "Çalışıyor…" : "Son koşu"}<pre>${esc((d.ilerleme || []).slice(-15).join("\n"))}</pre></div>` : ""; };
    durumYaz(v.durum);
    const secilen = () => $$(".bn-s:checked").map(x => x.value);
    $("#bn-dogrula").addEventListener("click", async () => { try { await gonder("/api/bench/dogrula", {senaryolar: secilen()}); bildir("Doğrulama başladı"); } catch (x) { bildir(x.message); } });
    $("#bn-kos").addEventListener("click", async () => { if (!secilen().length) return bildir("Senaryo seçin");
      try { await gonder("/api/bench/kos", {senaryolar: secilen(), kollar: $$(".bn-kol:checked").map(x => x.value), baglanti: $("#bn-baglanti").value}); bildir("Koşu başladı (ısı bekçisi çalışıyor olmalı)"); } catch (x) { bildir(x.message); } });
    zamanla(async () => { try { durumYaz((await al("/api/bench")).durum); } catch (e) {} }, 4000);
  }});

  /* ---------------------------------------------------------------- Karşılaştırma */
  sayfa("karsilastirma", {baslik: "sunucu/akış karşılaştırması", async ciz(kap) {
    const v = await al("/api/karsilastirma");
    const olc = t => { const s = Object.entries(t.olcum); if (!s.length) return '<span class="rozet duz">ölçülmedi</span>';
      return s.map(([sen, l]) => { const son = {}; l.forEach(r => son[r.kol] = r);
        return `<div style="margin-bottom:4px"><code>${esc(sen)}</code><br>${Object.values(son).map(r => `${esc(r.kol)}: ${r.gecti ? rozet("basarili", "geçti") : rozet("hatali", "kaldı")}${r.zararli ? rozet("hata", "zararlı") : ""} <span class="bilgi">${r.cagri ?? "-"} çağrı · ${esc(r.kosu)}</span>`).join("<br>")}</div>`; }).join(""); };
    kap.innerHTML = `<div class="sayfa">${baslik("Tipik talepler: sunucu/akış yolu ile Filo yolu", `sunucu/akış sütunları yalnız <code>${esc(v.kaynak || "-")}</code> dosyasından gelir (kaynakta olmayan iddia yazılmaz; "doğrulanamadı" diyen yer öyle kalır). Filo sütunu yalnız gerçekten koşulmuş bench senaryolarının sonucudur; karşılığı koşulmamış talep "ölçülmedi" der. Filo'da operatörün adımı: talep (ya da beceri) + plan onayı + risk 3+ ise onay.`)}
      ${!v.talepler.length ? `<div class="not uyari">${esc(v.not || "kaynak okunamadı")}</div>` : ""}
      <div class="kart"><div class="kart-govde" id="k-tablo"></div></div>
      <div class="kart"><div class="kart-bas"><h2>Benzer işler beceriye dönüşür</h2></div><div class="kart-govde"><p style="margin-top:0">sunucu otomasyonu'da "Run Server Script" her seferinde betik, grup, kimlik, zaman aşımı ve bildirim ayarı ister; akış otomasyonu'da akış Studio'da tasarlanır. Filo'da Kaptan'ın bir kez çözdüğü akış ya da tek seferlik bir betik işi <b>Beceriye dönüştür</b> düğmesiyle katalogda sürüm 1 beceri olur (parametreler ve risk kodla çıkarılır); benzer bir sonraki talebi Kalfa 2-3 model çağrısında yürütür. Ölçüm: <code>tests/test_donustur.py</code> (sahte model) ve <code>docs/ilerleme.md</code> B5 (qwen3:8b).</p></div></div></div>`;
    tablo($("#k-tablo"), [{ad: "kod", baslik: "No", genislik: "48px"}, {ad: "talep", baslik: "Talep", ciz: t => `<b>${esc(t.talep)}</b>${t.ornek_talep ? `<br><span class="bilgi">${esc(t.ornek_talep.replace(/^"|"$/g, ""))}</span>` : ""}`},
      {ad: "sa_adim", baslik: "sunucu otomasyonu adımı"}, {ad: "oo_adim", baslik: "akış otomasyonu adımı"}, {ad: "on_hazirlik", baslik: "Ön hazırlık", sinif: "kirp"}, {ad: "kirilma", baslik: "Kırıldığı yer", sinif: "kirp"},
      {ad: "olculdu", baslik: "Filo (ölçülen)", sirala: t => t.olculdu ? 1 : 0, ciz: olc}], v.talepler, {yerTutucu: "Talep süz…"});
  }});

  /* ---------------------------------------------------------------- Bağlantılar */
  const ORNEK_ADRES = {"ollama": "http://127.0.0.1:11434", "openai-uyumlu": "http://127.0.0.1:1234/v1", "anthropic": "https://api.anthropic.com",
    "openai": "https://api.openai.com/v1", "gemini": "https://generativelanguage.googleapis.com/v1beta/openai", "agy": ""};
  sayfa("baglantilar", {baslik: "Model bağlantıları", async ciz(kap) {
    kap.innerHTML = `<div class="sayfa">${baslik("Model bağlantıları", "Yerel (Ollama, OpenAI uyumlu uç: LM Studio, llama.cpp, vLLM) ve API (Anthropic, OpenAI, Gemini) bağlantıları. Anahtar ya ortam değişkeninin ADIYLA ya da git dışındaki <code>ayarlar/gizli.json</code> içinde durur; hiçbir zaman geri gösterilmez.")}
      <div class="izgara iki"><div class="kart"><div class="kart-bas"><h2>Bağlantılar</h2></div><div class="kart-govde" id="bg-liste"></div></div>
      <div class="kart"><div class="kart-bas"><h2 id="bg-form-baslik">Bağlantı ekle / düzenle</h2></div><div class="kart-govde">
        <div class="alanlar"><div><label for="bg-ad">Ad</label><input id="bg-ad" placeholder="ör. yerel-qwen"></div><div><label for="bg-tur">Tür</label><select id="bg-tur"></select></div></div>
        <div id="bg-yardim" class="not" style="margin-top:10px"></div>
        <label for="bg-adres">Adres (base URL)</label><input id="bg-adres">
        <label for="bg-model">Model</label><input id="bg-model" list="bg-modeller" placeholder="ör. qwen3:8b"><datalist id="bg-modeller"></datalist>
        <div id="bg-anahtar-alan"><label for="bg-ortam">Anahtarın ortam değişkeni ADI (isteğe bağlı)</label><input id="bg-ortam" placeholder="ör. ANTHROPIC_API_KEY">
          <label for="bg-anahtar">Anahtar (isteğe bağlı; ayarlar/gizli.json'a yazılır, geri gösterilmez)</label><input id="bg-anahtar" type="password" autocomplete="new-password" placeholder="boş bırakılırsa mevcut anahtar korunur"></div>
        <div class="dugmeler" style="margin-top:10px"><button class="btn birincil" id="bg-kaydet">Kaydet</button><button class="btn" id="bg-temizle">Temizle</button></div><div id="bg-sonuc" style="margin-top:10px"></div></div></div></div></div>`;
    let bgVeri;
    const turDegisti = () => { const t = $("#bg-tur").value; $("#bg-yardim").textContent = (bgVeri && bgVeri.yardim[t]) || ""; $("#bg-adres").placeholder = ORNEK_ADRES[t] || ""; $("#bg-anahtar-alan").classList.toggle("gizli", t === "agy" || t === "ollama"); };
    async function yukle() {
      bgVeri = await al("/api/baglantilar");
      if (!$("#bg-tur").options.length) { $("#bg-tur").innerHTML = bgVeri.turler.map(t => `<option>${esc(t)}</option>`).join(""); turDegisti(); }
      $("#bg-liste").innerHTML = bgVeri.baglantilar.map(b => `<div style="border-bottom:1px solid var(--cizgi);padding:10px 0"><b>${esc(b.ad)}</b> ${b.ad === bgVeri.varsayilan ? rozet("basarili", "varsayılan") : ""} <span class="bilgi">${esc(b.tur)}</span>
        <dl class="kv" style="margin-top:6px"><dt>Model</dt><dd><code>${esc(b.model || "—")}</code></dd><dt>Adres</dt><dd><code>${esc(b.adres || "—")}</code></dd><dt>Anahtar</dt><dd>${b.anahtar_var ? rozet("basarili", "var · " + b.anahtar_kaynagi) : (["anthropic", "openai", "gemini"].includes(b.tur) ? rozet("hatali", "yok") : rozet("bekliyor", "gerekmez/yok"))}</dd></dl>
        <div class="dugmeler" style="margin-top:6px"><button class="btn kucuk" data-bg="sina" data-ad="${esc(b.ad)}">Sına</button><button class="btn kucuk" data-bg="sohbet" data-ad="${esc(b.ad)}">Sına + kısa soru</button><button class="btn kucuk" data-bg="modeller" data-ad="${esc(b.ad)}">Modelleri listele</button><button class="btn kucuk" data-bg="duzenle" data-ad="${esc(b.ad)}">Düzenle</button><button class="btn kucuk" data-bg="varsayilan" data-ad="${esc(b.ad)}">Varsayılan yap</button><button class="btn kucuk tehlike" data-bg="sil" data-ad="${esc(b.ad)}">Sil</button></div>
        <div class="bg-cikti" data-ad="${esc(b.ad)}" style="margin-top:6px"></div></div>`).join("") || bos("Bağlantı yok");
    }
    $("#bg-tur").addEventListener("change", turDegisti);
    $("#bg-temizle").addEventListener("click", () => { ["#bg-ad", "#bg-adres", "#bg-model", "#bg-ortam", "#bg-anahtar"].forEach(s => $(s).value = ""); $("#bg-sonuc").innerHTML = ""; });
    $("#bg-kaydet").addEventListener("click", async () => {
      const g = {ad: $("#bg-ad").value.trim(), tur: $("#bg-tur").value, adres: $("#bg-adres").value.trim(), model: $("#bg-model").value.trim(), anahtar_ortam: $("#bg-ortam").value.trim()};
      const anahtar = $("#bg-anahtar").value; if (anahtar) g.anahtar = anahtar;
      try { const o = await gonder("/api/baglanti/kaydet", g); $("#bg-anahtar").value = ""; $("#bg-sonuc").innerHTML = `${rozet("basarili", "kaydedildi")} anahtar: ${o.anahtar_var ? "var (" + esc(o.anahtar_kaynagi) + ")" : "yok"}`; yukle(); }
      catch (e) { $("#bg-sonuc").innerHTML = rozet("hatali", e.message); }
    });
    kap.addEventListener("click", async e => {
      const b = e.target.closest("[data-bg]"); if (!b) return;
      const ad = b.dataset.ad, cikti = $(`.bg-cikti[data-ad="${CSS.escape(ad)}"]`);
      try {
        if (b.dataset.bg === "duzenle") { const x = bgVeri.baglantilar.find(y => y.ad === ad);
          $("#bg-ad").value = x.ad; $("#bg-tur").value = x.tur; turDegisti(); $("#bg-adres").value = x.adres || ""; $("#bg-model").value = x.model || ""; $("#bg-ortam").value = x.anahtar_ortam || ""; $("#bg-anahtar").value = ""; $("#bg-ad").focus(); return; }
        if (b.dataset.bg === "sil") { if (!confirm(ad + " silinsin mi? (gizli.json'daki anahtarı da silinir)")) return; await gonder("/api/baglanti/sil", {ad}); return yukle(); }
        if (b.dataset.bg === "varsayilan") { await gonder("/api/baglanti/varsayilan", {ad}); return yukle(); }
        cikti.innerHTML = `<span class="bilgi">sınanıyor…</span>`;
        if (b.dataset.bg === "modeller") { const v = await gonder("/api/baglanti/modeller", {ad}); cikti.innerHTML = `<pre>${esc(v.modeller.join("\n"))}</pre>`; $("#bg-modeller").innerHTML = v.modeller.map(m => `<option value="${esc(m)}">`).join(""); return; }
        const v = await gonder("/api/baglanti/sina", {ad, sohbet: b.dataset.bg === "sohbet"});
        cikti.innerHTML = `${v.tamam ? rozet("basarili", "bağlantı tamam") : rozet("hatali", "başarısız")} <span class="bilgi">${esc(v.sure)} sn${v.model_var === false ? " · model listede yok" : ""}</span>${v.hata ? `<pre>${esc(v.hata)}</pre>` : ""}${v.cevap ? `<pre>${esc(v.cevap)}</pre>` : ""}`;
      } catch (x) { if (cikti) cikti.innerHTML = rozet("hatali", x.message); else bildir(x.message); }
    });
    await yukle();
  }});

  /* ---------------------------------------------------------------- Denetim izi */
  sayfa("denetim", {baslik: "Denetim izi", async ciz(kap) {
    const v = await al("/api/denetim?limit=600");
    kap.innerHTML = `<div class="sayfa">${baslik("Denetim izi", `Eklemeli JSONL; her satır öncekinin özetine bağlıdır. Zincir: ${v.zincir.saglam ? rozet("basarili", "sağlam") : rozet("hatali", "bozuk (satır " + v.zincir.bozuk_satir + ")")} · ${v.zincir.satir} satır. Gizli adlı alanlar maskelenir.`)}
      <div class="kart"><div class="kart-govde" id="d-tablo"></div></div></div>`;
    tablo($("#d-tablo"), [{ad: "zaman", baslik: "Zaman", ciz: r => zaman(r.zaman), genislik: "150px"}, {ad: "tur", baslik: "Tür", ciz: r => `<code>${esc(r.tur)}</code>`},
      {ad: "is_kimligi", baslik: "İş", ciz: r => esc(r.is_kimligi || "")}, {ad: "govde", baslik: "Ayrıntı", sinif: "kirp", sirala: false,
        ciz: r => `<code>${esc(JSON.stringify(Object.fromEntries(Object.entries(r).filter(([k]) => !["zaman", "tur", "is_kimligi", "_onceki", "_ozet"].includes(k)))).slice(0, 400))}</code>`}],
      v.satirlar, {yerTutucu: "Tür, iş, beceri, sunucu süz…"});
  }});
})();
