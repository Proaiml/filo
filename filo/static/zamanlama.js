/* Zamanlanmış işler ve bakım/yasak pencereleri (C2). Zamanlayıcı konsol sürecinde çalışır; durum dosyadadır. */
"use strict";
(() => {
  const {$, $$, esc, al, gonder, rozet, risk, zaman, bildir, bos, hataKutu, tablo, sayfa, zamanla} = Filo;
  const GUNLER = [["pazartesi", "Pzt"], ["sali", "Sal"], ["carsamba", "Çar"], ["persembe", "Per"], ["cuma", "Cum"], ["cumartesi", "Cmt"], ["pazar", "Paz"]];
  const POL = {bekle: "pencere kapanınca", sor: "operatöre sor", atla: "atla"};

  function tanimOzeti(t) {
    if (t.tur === "beceri") return `<b>${esc(t.beceri)}</b> <code>${esc(JSON.stringify(t.parametreler || {}))}</code>${t.kimlik ? ` · kimlik <b>${esc(t.kimlik)}</b>` : ""}${t.bicim ? " · " + esc(t.bicim) : ""}${t.alici ? " → " + esc(t.alici) : ""}`;
    if (t.tur === "akis") return `akış <b>${esc((t.akis || {}).ad || "Kaptan akışı")}</b> · ${esc(((t.akis || {}).adimlar || []).length)} adım · düzey ${esc(t.inisiyatif)}`;
    return `talep (${esc(t.ajan)}): ${esc((t.metin || "").slice(0, 80))}`;
  }
  function onayHtml(z) {
    if (!z.onay_gerekli) return `<span class="bilgi">gerekmez</span>`;
    if (z.onay_gecerli) return rozet("onaylandi", `${z.onay.veren} · v${z.onay.tanim_surumu}`) + `<br><small>${zaman(z.onay.zaman)}</small>`;
    const dustu = (z.gecmis || []).some(g => g.olay === "onay_dustu");
    return rozet(dustu ? "onay_dustu" : "bekliyor", dustu ? "onay düştü" : "önceden onay yok") + `<br><small>koşu anında onay istenir</small>`;
  }

  async function zamanlamaCiz(kap) {
    const [v, bec, akislar] = await Promise.all([al("/api/zamanlama"), al("/api/beceriler"), al("/api/akislar")]);
    const sorular = v.isler.filter(z => z.bekleyen_soru);
    kap.innerHTML = `<div class="sayfa"><div class="baslik-satiri"><div><h1>Zamanlanmış işler</h1><p>Tek seferlik ve tekrarlı işler. Zamanlayıcı konsol sürecinde 20 saniyede bir bakar; şu an <b>${zaman(v.simdi)}</b>. Yasak pencerede değiştiren iş başlamaz (varsayılan: ${esc(POL[v.politika])}). Kalfa ve Kaptan sayfalarında planı "Zamanla" ile de buraya ekleyebilirsiniz; talepteki "her gece 02:00'de", "cumartesi bakım penceresinde" ifadelerini ajan zamanlamaya çevirir.</p></div></div>
      ${sorular.map(z => `<div class="not uyari" role="alert" style="margin-bottom:10px"><b>${esc(z.ad)}</b>: ${esc(z.bekleyen_soru.soru)}
        <div class="dugmeler" style="margin-top:6px"><button class="btn kucuk tehlike" data-soru="${esc(z.kimlik)}" data-karar="simdi">Şimdi çalıştır (yasağı bu koşu için kaldır)</button><button class="btn kucuk birincil" data-soru="${esc(z.kimlik)}" data-karar="bekle">Pencere kapanınca</button><button class="btn kucuk" data-soru="${esc(z.kimlik)}" data-karar="atla">Bu koşuyu atla</button></div></div>`).join("")}
      <div class="kart"><div class="kart-bas"><h2>İşler</h2><span class="bilgi">${v.isler.length} zamanlanmış iş</span></div><div class="kart-govde" id="zt"></div></div>
      <div class="izgara iki" style="margin-top:14px"><div class="kart"><div class="kart-bas"><h2>Geçmiş</h2></div><div class="kart-govde" id="zg">${bos("Ayrıntı için bir işe tıklayın")}</div></div>
      <div class="kart"><div class="kart-bas"><h2>Yeni zamanlanmış iş</h2></div><div class="kart-govde">
        <div class="mod-secici" role="group" aria-label="Tanım türü"><button type="button" data-tur="beceri" aria-pressed="true">Beceri (model yok)</button><button type="button" data-tur="akis" aria-pressed="false">Sabit akış</button><button type="button" data-tur="talep" aria-pressed="false">Serbest talep</button></div>
        <div id="zy-form" style="margin-top:10px"></div>
        <div class="alanlar" style="margin-top:8px"><div><label for="zy-zaman">Zamanlama</label><input id="zy-zaman" placeholder="ör. her gün 02:00 · her cumartesi 03:00 · yarın 23:30 · bakım penceresinde"><div class="yardim-metni" id="zy-onizleme">Sonraki 3 çalışma burada görünür.</div></div>
          <div><label for="zy-hedefc">Hedef çözümü</label><select id="zy-hedefc"><option value="simdi">Şimdi dondur</option><option value="calisma_aninda">Her koşuda yeniden çöz</option></select></div>
          <div><label for="zy-kacan">Kaçırılan koşu</label><select id="zy-kacan"><option value="atla">Atla</option><option value="hemen">Hemen çalıştır</option></select></div>
          <div><label for="zy-yasak">Yasak pencerede</label><select id="zy-yasak"><option value="bekle">Pencere kapanınca</option><option value="sor">Operatöre sor</option><option value="atla">Atla</option></select></div></div>
        <label style="display:block;margin-top:8px"><input type="checkbox" id="zy-onay"> Önceden onaylıyorum (risk 3+ işlerde; tanım değişirse onay düşer)</label>
        <div class="dugmeler" style="margin-top:10px"><button class="btn" id="zy-onizle">Önizle</button><button class="btn birincil" id="zy-kaydet">Zamanla</button></div></div></div></div></div>`;
    let tur = "beceri";
    const formCiz = () => {
      const f = $("#zy-form");
      if (tur === "beceri") f.innerHTML = `<div class="alanlar"><div><label for="zy-beceri">Beceri</label><select id="zy-beceri">${bec.beceriler.filter(b => b.tur !== "yerel").map(b => `<option>${esc(b.ad)}</option>`).join("")}</select></div>
          <div><label for="zy-hedef">Hedef seçici</label><input id="zy-hedef" placeholder="ör. PA* ya da grup:web"></div>
          <div><label for="zy-param">Parametreler (JSON)</label><input id="zy-param" value="{}"></div><div><label for="zy-kimlik">Çalıştırma kimliği</label><input id="zy-kimlik" placeholder="boş: bağlantı kullanıcısı · root · kullanıcı adı"></div>
          <div><label for="zy-bicim">Biçim</label><select id="zy-bicim"><option value="">yok</option><option>csv</option><option>xml</option><option>json</option><option>html</option></select></div><div><label for="zy-alici">E-posta</label><input id="zy-alici" type="email" placeholder="ops@lab.yerel"></div></div>`;
      else if (tur === "akis") f.innerHTML = `<div class="alanlar"><div><label for="zy-akis">Sabit akış</label><select id="zy-akis">${akislar.map(a => `<option value="${esc(a.ad)}">${esc(a.ad)}${a.yapili ? " (yapılı)" : ""}</option>`).join("") || "<option value=''>kayıtlı akış yok</option>"}</select></div>
          <div><label for="zy-hedef">Hedef seçici (boş: akışınki)</label><input id="zy-hedef"></div><div><label for="zy-duzey">Kaptan düzeyi</label><select id="zy-duzey"><option>1</option><option selected>2</option><option>3</option></select></div></div>`;
      else f.innerHTML = `<div class="alanlar"><div><label for="zy-ajan">Ajan</label><select id="zy-ajan"><option>kalfa</option><option>kaptan</option></select></div><div style="grid-column:span 2"><label for="zy-metin">Talep</label><input id="zy-metin" placeholder="koşu anında model planlar"></div></div>`;
    };
    formCiz();
    $$("[data-tur]").forEach(b => b.addEventListener("click", () => { tur = b.dataset.tur; $$("[data-tur]").forEach(x => x.setAttribute("aria-pressed", String(x === b))); formCiz(); }));
    const govde = () => {
      const t = {tur};
      if (tur === "beceri") { Object.assign(t, {beceri: $("#zy-beceri").value, hedef_secici: $("#zy-hedef").value.trim(), parametreler: JSON.parse($("#zy-param").value || "{}"),
        kimlik: $("#zy-kimlik").value.trim() || null, bicim: $("#zy-bicim").value || null, alici: $("#zy-alici").value.trim() || null}); }
      else if (tur === "akis") Object.assign(t, {akis_adi: $("#zy-akis").value, hedef_secici: $("#zy-hedef").value.trim() || null, inisiyatif: +$("#zy-duzey").value});
      else Object.assign(t, {ajan: $("#zy-ajan").value, metin: $("#zy-metin").value.trim()});
      return {tanim: t, zamanlama_metni: $("#zy-zaman").value.trim(), hedef_cozumu: $("#zy-hedefc").value, kacirilan: $("#zy-kacan").value,
              yasak_politikasi: $("#zy-yasak").value, on_onay: $("#zy-onay").checked};
    };
    $("#zy-onizle").addEventListener("click", async () => { try { const r = await gonder("/api/zamanlama/onizle", {metin: $("#zy-zaman").value.trim(), hedef: ($("#zy-hedef") || {}).value});
      $("#zy-onizleme").textContent = `${r.okunakli} · sonraki: ${r.sonraki.map(x => x.replace("T", " ")).join(" · ")}`; } catch (x) { $("#zy-onizleme").textContent = x.message; } });
    $("#zy-kaydet").addEventListener("click", async () => { try { const z = await gonder("/api/zamanlama/yeni", govde()); bildir(`Zamanlandı: ${z.okunakli}`); zamanlamaCiz(kap); } catch (x) { bildir(x.message); } });
    tablo($("#zt"), [
      {ad: "ad", baslik: "İş", ciz: z => `<a href="#" data-z="${esc(z.kimlik)}"><b>${esc(z.ad)}</b></a><br><small class="bilgi">${tanimOzeti(z.tanim)}</small>`},
      {ad: "okunakli", baslik: "Zamanlama", ciz: z => `${esc(z.okunakli)}${z.hata ? `<br>${rozet("hata", z.hata)}` : ""}`},
      {ad: "sonraki", baslik: "Sonraki 3 çalışma", ciz: z => z.etkin ? (z.sonraki_uc || []).map(zaman).join("<br>") || "–" : rozet("", "pasif")},
      {ad: "hedef_cozumu", baslik: "Hedef", ciz: z => z.hedef_cozumu === "simdi" ? `dondurulmuş<br><small>${esc((z.dondurulmus_liste || []).join(", "))}</small>` : "her koşuda çözülür"},
      {ad: "risk", baslik: "Risk", ciz: z => risk(z.risk)},
      {ad: "onay", baslik: "Önceden onay", ciz: onayHtml, sirala: false},
      {ad: "kural", baslik: "Kaçırılan / yasak", ciz: z => `${z.kacirilan === "atla" ? "atla" : "hemen"} / ${esc(POL[z.yasak_politikasi])}`, sirala: false},
      {ad: "son", baslik: "Son çalışma", ciz: z => z.son_calisma ? `${zaman(z.son_calisma.zaman)}${z.son_calisma.is ? `<br><a href="/kalfa?is=${esc(z.son_calisma.is)}">${esc(z.son_calisma.is)}</a>` : ""}` : "–", sirala: false},
      {ad: "eylem", baslik: "", sirala: false, ciz: z => `<div class="dugmeler"><button class="btn kucuk" data-calistir="${esc(z.kimlik)}">Şimdi çalıştır</button>
        <button class="btn kucuk" data-etkin="${esc(z.kimlik)}" data-deger="${z.etkin ? "0" : "1"}">${z.etkin ? "Durdur" : "Etkinleştir"}</button>
        ${z.onay_gerekli && !z.onay_gecerli ? `<button class="btn kucuk" data-onayla="${esc(z.kimlik)}">Önceden onayla</button>` : ""}<button class="btn kucuk tehlike" data-sil="${esc(z.kimlik)}">Sil</button></div>`}],
      v.isler, {bosBaslik: "Zamanlanmış iş yok", bosAlt: "Kalfa ya da Kaptan planında 'Zamanla'yı seçin ya da sağdaki formu kullanın."});
    kap.querySelector(".sayfa").addEventListener("click", async e => {
      const t = e.target;
      const is_ = async (f, mesaj) => { try { await f(); bildir(mesaj); zamanlamaCiz(kap); } catch (x) { bildir(x.message); } };
      if (t.dataset.soru) return is_(() => gonder("/api/zamanlama/soru", {kimlik: t.dataset.soru, karar: t.dataset.karar}), "Karar kaydedildi");
      if (t.dataset.calistir) return is_(() => gonder("/api/zamanlama/calistir", {kimlik: t.dataset.calistir}), "Çalıştırıldı");
      if (t.dataset.etkin) return is_(() => gonder("/api/zamanlama/degistir", {kimlik: t.dataset.etkin, etkin: t.dataset.deger === "1"}), "Güncellendi");
      if (t.dataset.onayla) return is_(() => gonder("/api/zamanlama/onayla", {kimlik: t.dataset.onayla}), "Önceden onay verildi");
      if (t.dataset.sil) { if (confirm("Zamanlanmış iş silinsin mi?")) return is_(() => gonder("/api/zamanlama/sil", {kimlik: t.dataset.sil}), "Silindi"); return; }
      const a = t.closest("[data-z]");
      if (a) { e.preventDefault(); const z = v.isler.find(x => x.kimlik === a.dataset.z);
        $("#zg").innerHTML = `<h3 style="margin-top:0">${esc(z.ad)} <span class="rozet duz">tanım v${esc(z.tanim_surumu)}</span></h3><dl class="kv"><dt>Oluşturan</dt><dd>${esc(z.olusturan)} · ${zaman(z.olusturma)}</dd><dt>Tanım</dt><dd>${tanimOzeti(z.tanim)}</dd><dt>Tanım özeti</dt><dd><code>${esc(z.tanim_ozeti)}</code></dd></dl>
          <div class="zaman-cizgisi" style="margin-top:8px">${[...(z.gecmis || [])].reverse().map(g => `<div class="zc">${rozet(g.olay)} <small>${zaman(g.zaman)}${g.plan_zamani ? " · plan " + zaman(g.plan_zamani) : ""}</small>${g.is_ ? ` · iş <code>${esc(g.is_)}</code> ${rozet(g.durum || "")}` : ""}${g.kim ? ` · ${esc(g.kim)}` : ""}<br><span>${esc(g.not_ || g.neden || (g.yeni ? "yeni zaman: " + g.yeni : ""))}</span></div>`).join("") || bos("Geçmiş yok")}</div>`; }
    });
  }

  sayfa("zamanlama", {baslik: "Zamanlanmış işler", async ciz(kap) { await zamanlamaCiz(kap); zamanla(() => { if (!document.activeElement || !document.activeElement.closest(".kart-govde input, .kart-govde select")) zamanlamaCiz(kap); }, 20000); }});

  async function pencerelerCiz(kap) {
    const v = await al("/api/pencereler");
    kap.innerHTML = `<div class="sayfa"><div class="baslik-satiri"><div><h1>Bakım ve yasak pencereleri</h1><p>Bakım penceresi: işin "bakım penceresinde çalıştır" zamanlaması buna bağlanır. Yasak (blackout) pencere: sunucuyu değiştiren iş (risk 2+) bu aralıkta başlamaz; salt-okur işler etkilenmez. Şu an <b>${zaman(v.simdi)}</b>.</p></div>
      <div><label for="pp-pol">Varsayılan yasak politikası</label><select id="pp-pol" style="width:auto">${Object.entries(POL).map(([k, x]) => `<option value="${k}" ${k === v.politika ? "selected" : ""}>${esc(x)}</option>`).join("")}</select></div></div>
      <div class="kart"><div class="kart-bas"><h2>Pencereler</h2></div><div class="kart-govde" id="pt"></div></div>
      <div class="kart" style="margin-top:14px"><div class="kart-bas"><h2 id="pf-baslik">Yeni pencere</h2></div><div class="kart-govde"><div class="alanlar">
        <div><label for="pf-ad">Ad</label><input id="pf-ad" placeholder="ör. db-pazar"></div><div><label for="pf-tur">Tür</label><select id="pf-tur"><option value="bakim">Bakım penceresi</option><option value="yasak">Yasak (blackout)</option></select></div>
        <div><label for="pf-kapsam">Kapsam (seçici)</label><input id="pf-kapsam" placeholder="ör. grup:db ya da PA-APP-01,PA-APP-02"><div class="yardim-metni" id="pf-onizleme"></div></div>
        <div><label for="pf-tekrar">Tekrar</label><select id="pf-tekrar"><option value="haftalik">Haftalık</option><option value="gunluk">Her gün</option><option value="tek">Bir kez (tarih aralığı)</option></select></div>
        <div class="pf-tekrarli"><label for="pf-bas">Başlangıç saati</label><input id="pf-bas" placeholder="02:00"></div><div class="pf-tekrarli"><label for="pf-sure">Süre (dakika)</label><input id="pf-sure" type="number" value="120"></div>
        <div class="pf-tek gizli"><label for="pf-tbas">Başlangıç</label><input id="pf-tbas" type="datetime-local"></div><div class="pf-tek gizli"><label for="pf-tbit">Bitiş</label><input id="pf-tbit" type="datetime-local"></div>
        <div style="grid-column:1/-1"><label for="pf-aciklama">Açıklama</label><input id="pf-aciklama"></div></div>
        <fieldset class="gunler pf-haftalik"><legend>Günler</legend>${GUNLER.map(([g, k]) => `<label><input type="checkbox" value="${g}"> ${k}</label>`).join("")}</fieldset>
        <div class="dugmeler" style="margin-top:10px"><button class="btn birincil" id="pf-kaydet">Kaydet</button><button class="btn" id="pf-temizle">Temizle</button></div></div></div></div>`;
    const tekrarGoster = () => { const t = $("#pf-tekrar").value; $$(".pf-tekrarli").forEach(x => x.classList.toggle("gizli", t === "tek")); $$(".pf-tek").forEach(x => x.classList.toggle("gizli", t !== "tek")); $(".pf-haftalik").classList.toggle("gizli", t !== "haftalik"); };
    $("#pf-tekrar").addEventListener("change", tekrarGoster); tekrarGoster();
    let zm_; $("#pf-kapsam").addEventListener("input", () => { clearTimeout(zm_); zm_ = setTimeout(async () => { try { const r = await al("/api/envanter/sec?hedef=" + encodeURIComponent($("#pf-kapsam").value)); $("#pf-onizleme").textContent = `${r.sunucular.length} sunucu: ${r.sunucular.join(", ")}`; } catch (x) { $("#pf-onizleme").textContent = x.message; } }, 300); });
    $("#pp-pol").addEventListener("change", async e => { try { await gonder("/api/pencere/politika", {politika: e.target.value}); bildir("Varsayılan politika kaydedildi"); } catch (x) { bildir(x.message); } });
    const doldur = p => { $("#pf-baslik").textContent = p ? `Düzenle: ${p.ad}` : "Yeni pencere"; $("#pf-ad").value = p ? p.ad : ""; $("#pf-tur").value = p ? p.tur : "bakim"; $("#pf-kapsam").value = p ? p.kapsam : "";
      $("#pf-tekrar").value = p ? p.tekrar.tur : "haftalik"; $("#pf-bas").value = p && p.tekrar.baslangic && p.tekrar.tur !== "tek" ? p.tekrar.baslangic : ""; $("#pf-sure").value = p && p.tekrar.sure_dk || 120;
      $("#pf-tbas").value = p && p.tekrar.tur === "tek" ? p.tekrar.baslangic : ""; $("#pf-tbit").value = p && p.tekrar.tur === "tek" ? p.tekrar.bitis : ""; $("#pf-aciklama").value = p ? p.aciklama || "" : "";
      $$(".gunler input").forEach(x => { x.checked = !!(p && (p.tekrar.gunler || []).includes(x.value)); }); tekrarGoster(); };
    $("#pf-temizle").addEventListener("click", () => doldur(null));
    $("#pf-kaydet").addEventListener("click", async () => {
      const t = $("#pf-tekrar").value;
      const tekrar = t === "tek" ? {tur: t, baslangic: $("#pf-tbas").value, bitis: $("#pf-tbit").value}
        : {tur: t, baslangic: $("#pf-bas").value, sure_dk: +$("#pf-sure").value, ...(t === "haftalik" ? {gunler: $$(".gunler input:checked").map(x => x.value)} : {})};
      try { await gonder("/api/pencere/kaydet", {ad: $("#pf-ad").value.trim(), tur: $("#pf-tur").value, kapsam: $("#pf-kapsam").value.trim(), tekrar, aciklama: $("#pf-aciklama").value}); bildir("Pencere kaydedildi"); pencerelerCiz(kap); } catch (x) { bildir(x.message); }
    });
    tablo($("#pt"), [
      {ad: "ad", baslik: "Ad", ciz: p => `<b>${esc(p.ad)}</b><br><small class="bilgi">${esc(p.aciklama || "")}</small>`},
      {ad: "tur", baslik: "Tür", ciz: p => p.tur === "yasak" ? rozet("hata", "yasak") : rozet("basarili", "bakım")},
      {ad: "kapsam", baslik: "Kapsam", ciz: p => `<code>${esc(p.kapsam)}</code><br><small>${esc(p.sunucular.join(", "))}</small>`},
      {ad: "okunakli", baslik: "Zaman"},
      {ad: "acik", baslik: "Şu an", ciz: p => p.acik ? rozet(p.tur === "yasak" ? "hata" : "basarili", `açık · ${zaman(p.kapanis).slice(11)} kapanır`) : `<span class="bilgi">kapalı</span>`},
      {ad: "sonraki_acilis", baslik: "Sonraki açılış", ciz: p => zaman(p.sonraki_acilis)},
      {ad: "eylem", baslik: "", sirala: false, ciz: p => `<div class="dugmeler"><button class="btn kucuk" data-duzenle="${esc(p.ad)}">Düzenle</button><button class="btn kucuk tehlike" data-psil="${esc(p.ad)}">Sil</button></div>`}],
      v.pencereler, {bosBaslik: "Pencere yok"});
    $("#pt").addEventListener("click", async e => {
      if (e.target.dataset.duzenle) doldur(v.pencereler.find(p => p.ad === e.target.dataset.duzenle));
      if (e.target.dataset.psil && confirm("Pencere silinsin mi?")) { try { await gonder("/api/pencere/sil", {ad: e.target.dataset.psil}); pencerelerCiz(kap); } catch (x) { bildir(x.message); } }
    });
  }
  sayfa("pencereler", {baslik: "Bakım pencereleri", ciz: pencerelerCiz});
})();
