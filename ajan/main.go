// filo-ajan: Filo'nun yönetilen sunucuda çalışan ajanı. Yalnız Go standart kitaplığı.
//
// Ajan sunucuda dinleyen port AÇMAZ; çekirdeğin ajan kapısına dışarı doğru bağlanır:
//
//	kayıt      tek kullanımlık kayıt belirteci -> ajana özel gizli anahtar (diskte 0600)
//	kalp       her 10 saniyede sürüm ve çalışan işler
//	yokla      uzun yoklama: çekirdek iş verene ya da süre dolana kadar bekler
//	sonuc      işin sonucu (filo/yurutme.py ile aynı şema)
//	dosya      dosya alma işinde içerik; özet doğrulanmadan yazılmaz
//
// Her istek imzalı ve zaman damgalıdır; her iş paketi çekirdek tarafından imzalanır, imzasız ya da sahte imzalı iş
// çalışmaz. Gizli anahtar ve kayıt belirteci kayıtlara yazılmaz.
//
//	filo-ajan calis  -dizin /etc/filo-ajan
//	filo-ajan surum
//	filo-ajan sistem
package main

import (
	"bytes"
	"crypto/rand"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"strconv"
	"sync"
	"time"
)

var surum = "0.2.0"

type Ayar struct {
	Cekirdek  string `json:"cekirdek"`
	Sunucu    string `json:"sunucu"`
	Kullanici string `json:"kullanici"`
	Belirtec  string `json:"belirtec,omitempty"`
	EnCokIs   int    `json:"en_cok_is,omitempty"`
}

type Kimlik struct {
	AjanKimligi string `json:"ajan_kimligi"`
	Gizli       string `json:"gizli"`
}

type Ajan struct {
	dizin    string
	ayar     Ayar
	kimlik   Kimlik
	anahtar  Anahtarlar
	http     *http.Client
	gorulen  *GorulenIsler
	mu       sync.Mutex
	calisan  map[string]chan struct{}
	yer      chan struct{}
}

func dosyaYaz0600(yol string, veri []byte) error {
	gecici := yol + ".yeni"
	if err := os.WriteFile(gecici, veri, 0o600); err != nil {
		return err
	}
	_ = os.Chmod(gecici, 0o600)
	return os.Rename(gecici, yol)
}

func nonce() string {
	b := make([]byte, 12)
	_, _ = rand.Read(b)
	return hex.EncodeToString(b)
}

// ---------------------------------------------------------------- HTTP
type hataKodu struct {
	kod   int
	metin string
}

func (h hataKodu) Error() string { return fmt.Sprintf("HTTP %d: %s", h.kod, h.metin) }

func (a *Ajan) istek(yontem, yol string, govde any, bekle time.Duration) ([]byte, error) {
	var veri []byte
	if govde != nil {
		var err error
		if veri, err = json.Marshal(govde); err != nil {
			return nil, err
		}
	}
	req, err := http.NewRequest(yontem, a.ayar.Cekirdek+yol, bytes.NewReader(veri))
	if err != nil {
		return nil, err
	}
	req.Header.Set("Content-Type", "application/json")
	n := nonce()
	if a.kimlik.AjanKimligi != "" {
		zaman := strconv.FormatInt(time.Now().Unix(), 10)
		req.Header.Set(BaslikAjan, a.kimlik.AjanKimligi)
		req.Header.Set(BaslikZaman, zaman)
		req.Header.Set(BaslikNonce, n)
		req.Header.Set(BaslikImza, IstekImzasi(a.anahtar.Istek, yontem, req.URL.Path, zaman, n, veri))
	}
	istemci := a.http
	if bekle > 0 {
		istemci = &http.Client{Timeout: bekle}
	}
	resp, err := istemci.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	cevap, err := io.ReadAll(io.LimitReader(resp.Body, 64<<20))
	if err != nil {
		return nil, err
	}
	if resp.StatusCode/100 != 2 {
		return nil, hataKodu{resp.StatusCode, string(bytes.TrimSpace(cevap[:min(len(cevap), 300)]))}
	}
	if a.kimlik.AjanKimligi != "" {
		// Çekirdeğin cevabı da imzalıdır ve bu isteğin nonce'una bağlıdır.
		if resp.Header.Get(BaslikImza) != YanitImzasi(a.anahtar.Is, n, cevap) {
			return nil, errors.New("çekirdek cevabının imzası tutmuyor: yok sayıldı")
		}
	}
	return cevap, nil
}

// ---------------------------------------------------------------- kayıt
func (a *Ajan) kayitOl() error {
	if a.ayar.Belirtec == "" {
		return errors.New("kimlik yok ve kayıt belirteci verilmemiş")
	}
	govde := map[string]any{"belirtec": a.ayar.Belirtec, "sunucu": a.ayar.Sunucu, "surum": surum, "sistem": SistemOku()}
	cevap, err := a.istek("POST", "/ajan/v1/kayit", govde, 20*time.Second)
	if err != nil {
		return fmt.Errorf("kayıt başarısız: %w", err)
	}
	var k Kimlik
	if err := json.Unmarshal(cevap, &k); err != nil || k.AjanKimligi == "" || k.Gizli == "" {
		return errors.New("kayıt cevabı geçersiz")
	}
	veri, _ := json.MarshalIndent(k, "", " ")
	if err := dosyaYaz0600(filepath.Join(a.dizin, "kimlik.json"), veri); err != nil {
		return err
	}
	// Belirteç tek kullanımlıktır: ayar dosyasından silinir.
	a.ayar.Belirtec = ""
	ayarVeri, _ := json.MarshalIndent(a.ayar, "", " ")
	if err := dosyaYaz0600(filepath.Join(a.dizin, "ajan.json"), ayarVeri); err != nil {
		return err
	}
	a.kimlik = k
	a.anahtar, err = AnahtarTuret(k.Gizli)
	log.Printf("kayıt tamam: ajan %s, sunucu %s", k.AjanKimligi, a.ayar.Sunucu)
	return err
}

// ---------------------------------------------------------------- işler
type yoklamaCevabi struct {
	Isler []IsZarfi `json:"isler"`
	Iptal []string  `json:"iptal"`
}

func (a *Ajan) iptalEt(kimlikler []string) {
	a.mu.Lock()
	defer a.mu.Unlock()
	for _, k := range kimlikler {
		if c, ok := a.calisan[k]; ok {
			close(c)
			delete(a.calisan, k)
			log.Printf("iş %s iptal edildi", k)
		}
	}
}

func (a *Ajan) calisanlar() []string {
	a.mu.Lock()
	defer a.mu.Unlock()
	out := []string{}
	for k := range a.calisan {
		out = append(out, k)
	}
	return out
}

func (a *Ajan) isYurut(z IsZarfi) {
	is, err := IsDogrula(z, a.anahtar, a.kimlik.AjanKimligi, a.gorulen, time.Now())
	if err != nil {
		log.Printf("iş reddedildi: %v", err)
		var kimlik struct {
			Kimlik string `json:"kimlik"`
		}
		_ = json.Unmarshal([]byte(z.Govde), &kimlik)
		if kimlik.Kimlik != "" {
			a.sonucGonder(Sonuc{Kimlik: kimlik.Kimlik, Durum: "reddedildi", Neden: err.Error()})
		}
		return
	}
	iptal := make(chan struct{})
	a.mu.Lock()
	a.calisan[is.Kimlik] = iptal
	a.mu.Unlock()
	a.yer <- struct{}{}
	go func() {
		defer func() {
			<-a.yer
			a.mu.Lock()
			delete(a.calisan, is.Kimlik)
			a.mu.Unlock()
		}()
		var r Sonuc
		switch is.Tur {
		case "calistir":
			r = Calistir(is, a.ayar.Kullanici, iptal)
		case "dosya_al":
			r = a.dosyaAl(is)
		case "sistem_bilgisi":
			v, _ := json.Marshal(SistemOku())
			kod := 0
			r = Sonuc{Kimlik: is.Kimlik, Durum: "basarili", CikisKodu: &kod, Stdout: string(v) + "\n"}
		case "surum":
			kod := 0
			r = Sonuc{Kimlik: is.Kimlik, Durum: "basarili", CikisKodu: &kod, Stdout: surum + "\n"}
		}
		a.sonucGonder(r)
	}()
}

func (a *Ajan) dosyaAl(is *Is) Sonuc {
	r := Sonuc{Kimlik: is.Kimlik, Durum: "hatali", Kullanici: is.Kullanici}
	bas := time.Now()
	d := is.Dosya
	if d == nil || d.Ad == "" || !filepath.IsAbs(d.Yol) || d.Ozet == "" {
		r.Neden = "dosya bilgisi eksik"
		return r
	}
	icerik, err := a.istek("GET", "/ajan/v1/dosya?is="+is.Kimlik, nil, time.Duration(max(is.ZamanAsimi, 10))*time.Second)
	if err != nil {
		r.Neden = "dosya alınamadı: " + err.Error()
		return r
	}
	ozet := sha256.Sum256(icerik)
	if hex.EncodeToString(ozet[:]) != d.Ozet {
		r.Neden = "dosya özeti tutmuyor: yazılmadı"
		return r
	}
	kip := os.FileMode(0o644)
	if d.Kip != "" {
		if n, err := strconv.ParseUint(d.Kip, 8, 32); err == nil {
			kip = os.FileMode(n)
		}
	}
	if err := os.MkdirAll(filepath.Dir(d.Yol), 0o755); err != nil {
		r.Neden = err.Error()
		return r
	}
	gecici := d.Yol + ".filo-yeni"
	if err := os.WriteFile(gecici, icerik, kip); err != nil {
		r.Neden = err.Error()
		return r
	}
	_ = os.Chmod(gecici, kip)
	if err := dosyaSahibi(gecici, is.Kullanici); err != nil {
		_ = os.Remove(gecici)
		r.Neden = "dosya sahibi: " + err.Error()
		return r
	}
	if err := os.Rename(gecici, d.Yol); err != nil {
		r.Neden = err.Error()
		return r
	}
	kod := 0
	r.Durum, r.CikisKodu = "basarili", &kod
	r.Stdout = fmt.Sprintf("dosya=%s\nboyut=%d\nozet=%s\n", d.Yol, len(icerik), d.Ozet)
	r.Sure = float64(time.Since(bas).Milliseconds()) / 1000.0
	return r
}

func (a *Ajan) sonucGonder(r Sonuc) {
	for deneme := 0; deneme < 5; deneme++ {
		if _, err := a.istek("POST", "/ajan/v1/sonuc", r, 30*time.Second); err == nil {
			return
		} else {
			log.Printf("sonuç gönderilemedi (%s): %v", r.Kimlik, err)
		}
		time.Sleep(time.Duration(deneme+1) * time.Second)
	}
}

// ---------------------------------------------------------------- döngüler
func (a *Ajan) kalpDongusu(dur <-chan struct{}) {
	t := time.NewTicker(10 * time.Second)
	defer t.Stop()
	for {
		cevap, err := a.istek("POST", "/ajan/v1/kalp", map[string]any{"surum": surum, "calisan": a.calisanlar()}, 15*time.Second)
		if err == nil {
			var c yoklamaCevabi
			if json.Unmarshal(cevap, &c) == nil {
				a.iptalEt(c.Iptal)
			}
		} else if hk, ok := err.(hataKodu); ok && hk.kod == 410 {
			log.Printf("çekirdek bu ajanı kaldırdı; ajan duruyor")
			os.Exit(3)
		}
		select {
		case <-dur:
			return
		case <-t.C:
		}
	}
}

func (a *Ajan) yoklamaDongusu() {
	bekleme := time.Second
	for {
		cevap, err := a.istek("POST", "/ajan/v1/yokla", map[string]any{"bekle": 25, "surum": surum}, 40*time.Second)
		if err != nil {
			if hk, ok := err.(hataKodu); ok && hk.kod == 410 {
				log.Printf("çekirdek bu ajanı kaldırdı; ajan duruyor")
				os.Exit(3)
			}
			log.Printf("yoklama başarısız: %v (%s sonra yeniden)", err, bekleme)
			time.Sleep(bekleme)
			bekleme = min(bekleme*2, 30*time.Second)
			continue
		}
		bekleme = time.Second
		var c yoklamaCevabi
		if err := json.Unmarshal(cevap, &c); err != nil {
			log.Printf("yoklama cevabı okunamadı: %v", err)
			continue
		}
		a.iptalEt(c.Iptal)
		for _, z := range c.Isler {
			a.isYurut(z)
		}
	}
}

func yukle(dizin string) (*Ajan, error) {
	a := &Ajan{dizin: dizin, gorulen: YeniGorulenIsler(), calisan: map[string]chan struct{}{},
		http: &http.Client{Timeout: 30 * time.Second}}
	veri, err := os.ReadFile(filepath.Join(dizin, "ajan.json"))
	if err != nil {
		return nil, fmt.Errorf("ayar okunamadı: %w", err)
	}
	if err := json.Unmarshal(veri, &a.ayar); err != nil {
		return nil, fmt.Errorf("ayar geçersiz: %w", err)
	}
	if a.ayar.Cekirdek == "" || a.ayar.Sunucu == "" {
		return nil, errors.New("ayarda cekirdek ve sunucu zorunlu")
	}
	if a.ayar.EnCokIs <= 0 {
		a.ayar.EnCokIs = 4
	}
	a.yer = make(chan struct{}, a.ayar.EnCokIs)
	if veri, err := os.ReadFile(filepath.Join(dizin, "kimlik.json")); err == nil {
		if err := json.Unmarshal(veri, &a.kimlik); err != nil {
			return nil, fmt.Errorf("kimlik dosyası geçersiz: %w", err)
		}
		if a.anahtar, err = AnahtarTuret(a.kimlik.Gizli); err != nil {
			return nil, err
		}
	}
	return a, nil
}

func main() {
	log.SetFlags(log.LstdFlags)
	log.SetPrefix("filo-ajan ")
	if len(os.Args) < 2 {
		fmt.Fprintln(os.Stderr, "kullanım: filo-ajan calis -dizin /etc/filo-ajan | surum | sistem")
		os.Exit(2)
	}
	switch os.Args[1] {
	case "surum":
		fmt.Println(surum)
		return
	case "sistem":
		v, _ := json.MarshalIndent(SistemOku(), "", " ")
		fmt.Println(string(v))
		return
	case "calis":
	default:
		fmt.Fprintln(os.Stderr, "bilinmeyen komut:", os.Args[1])
		os.Exit(2)
	}
	fs := flag.NewFlagSet("calis", flag.ExitOnError)
	dizin := fs.String("dizin", "/etc/filo-ajan", "ayar ve kimlik dizini")
	_ = fs.Parse(os.Args[2:])
	a, err := yukle(*dizin)
	if err != nil {
		log.Fatalf("başlatılamadı: %v", err)
	}
	for a.kimlik.AjanKimligi == "" {
		if err := a.kayitOl(); err != nil {
			log.Printf("%v; 5 sn sonra yeniden", err)
			if hk, ok := errors.Unwrap(err).(hataKodu); ok && (hk.kod == 401 || hk.kod == 403) {
				log.Fatalf("kayıt belirteci reddedildi; ajan duruyor")
			}
			time.Sleep(5 * time.Second)
		}
	}
	log.Printf("sürüm %s, sunucu %s, çekirdek %s", surum, a.ayar.Sunucu, a.ayar.Cekirdek)
	dur := make(chan struct{})
	go a.kalpDongusu(dur)
	a.yoklamaDongusu()
}
