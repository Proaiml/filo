package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"runtime"
	"strings"
	"testing"
	"time"
)

const gizliOrnek = "1111111111111111111111111111111111111111111111111111111111111111"

// Python tarafı (tests/test_ajan_kapisi.py) aynı örnekle aynı değerleri üretir.
func TestCaprazDilImzaOrnegi(t *testing.T) {
	a, err := AnahtarTuret(gizliOrnek)
	if err != nil {
		t.Fatal(err)
	}
	if g := IstekImzasi(a.Istek, "POST", "/ajan/v1/kalp", "1700000000", "abc", []byte(`{"a":1}`)); g != "f2afbca3d724ce59c012cafd270d78e81f384934d247f31ff4c63edc467cc51e" {
		t.Fatalf("istek imzası: %s", g)
	}
	if g := YanitImzasi(a.Is, "abc", []byte(`{"a":1}`)); g != "6ecc4b57561c813290ed33942b82f5e034e15a260d544f32be5569af8564b24d" {
		t.Fatalf("yanıt imzası: %s", g)
	}
	if g := hmacHex(a.Is, "is\n"+`{"kimlik":"x"}`); g != "bd19c45e981e7b75241cb419ffcbbc39a09e1e70a972361e0718701fb6475833" {
		t.Fatalf("iş imzası: %s", g)
	}
}

func zarf(t *testing.T, a Anahtarlar, is Is) IsZarfi {
	v, _ := json.Marshal(is)
	return IsZarfi{Govde: string(v), Imza: hmacHex(a.Is, "is\n"+string(v))}
}

func TestSahteImzaliIsReddedilir(t *testing.T) {
	a, _ := AnahtarTuret(gizliOrnek)
	baska, _ := AnahtarTuret(strings.Repeat("22", 32))
	simdi := time.Now()
	is := Is{Kimlik: "i1", Ajan: "A", Tur: "calistir", Betik: "echo x", ZamanAsimi: 5, Gecerlilik: simdi.Unix() + 60}
	g := YeniGorulenIsler()

	if _, err := IsDogrula(IsZarfi{Govde: zarf(t, a, is).Govde}, a, "A", g, simdi); err == nil {
		t.Fatal("imzasız iş kabul edildi")
	}
	if _, err := IsDogrula(zarf(t, baska, is), a, "A", g, simdi); err == nil {
		t.Fatal("başka anahtarla imzalı iş kabul edildi")
	}
	z := zarf(t, a, is)
	z.Govde = strings.Replace(z.Govde, "echo x", "rm -rf /", 1)
	if _, err := IsDogrula(z, a, "A", g, simdi); err == nil {
		t.Fatal("gövdesi değiştirilmiş iş kabul edildi")
	}
	if _, err := IsDogrula(zarf(t, a, is), a, "B", g, simdi); err == nil {
		t.Fatal("başka ajanın işi kabul edildi")
	}
	eski := is
	eski.Kimlik, eski.Gecerlilik = "i2", simdi.Unix()-1
	if _, err := IsDogrula(zarf(t, a, eski), a, "A", g, simdi); err == nil {
		t.Fatal("süresi dolmuş iş kabul edildi")
	}
	if _, err := IsDogrula(zarf(t, a, is), a, "A", g, simdi); err != nil {
		t.Fatalf("geçerli iş reddedildi: %v", err)
	}
	if _, err := IsDogrula(zarf(t, a, is), a, "A", g, simdi); err == nil {
		t.Fatal("aynı iş ikinci kez kabul edildi")
	}
}

func unixGerek(t *testing.T) {
	if runtime.GOOS == "windows" {
		t.Skip("yalnız Unix")
	}
}

func TestCalistirSonucSemasi(t *testing.T) {
	unixGerek(t)
	r := Calistir(&Is{Kimlik: "c1", Betik: "echo merhaba; echo uyari >&2; exit 3", ZamanAsimi: 5}, "", nil)
	if r.Durum != "hatali" || r.CikisKodu == nil || *r.CikisKodu != 3 || r.Stdout != "merhaba\n" || r.Stderr != "uyari\n" {
		t.Fatalf("beklenmeyen sonuç: %+v", r)
	}
	r = Calistir(&Is{Kimlik: "c2", Betik: "echo tamam", ZamanAsimi: 5}, "", nil)
	if r.Durum != "basarili" || *r.CikisKodu != 0 {
		t.Fatalf("beklenmeyen sonuç: %+v", r)
	}
}

func TestZamanAsimiSurecGrubunuOldurur(t *testing.T) {
	unixGerek(t)
	bas := time.Now()
	r := Calistir(&Is{Kimlik: "z1", Betik: "sleep 30 & sleep 30", ZamanAsimi: 1}, "", nil)
	if r.Durum != "zaman_asimi" || r.CikisKodu != nil {
		t.Fatalf("zaman aşımı bekleniyordu: %+v", r)
	}
	if time.Since(bas) > 5*time.Second {
		t.Fatal("zaman aşımı süreci zamanında kesmedi")
	}
}

func TestCiktiSiniriKesildiIsareti(t *testing.T) {
	unixGerek(t)
	r := Calistir(&Is{Kimlik: "k1", Betik: "i=0; while [ $i -lt 500 ]; do echo 0123456789; i=$((i+1)); done", ZamanAsimi: 5, CiktiSiniri: 100}, "", nil)
	if !r.Kesildi || len(r.Stdout) != 100 || r.Durum != "basarili" {
		t.Fatalf("kesilme: %v uzunluk %d durum %s", r.Kesildi, len(r.Stdout), r.Durum)
	}
}

func TestIptal(t *testing.T) {
	unixGerek(t)
	iptal := make(chan struct{})
	go func() { time.Sleep(300 * time.Millisecond); close(iptal) }()
	r := Calistir(&Is{Kimlik: "p1", Betik: "sleep 20", ZamanAsimi: 30}, "", iptal)
	if r.Durum != "iptal" {
		t.Fatalf("iptal bekleniyordu: %+v", r)
	}
}

func TestKullaniciAdinaCalistirma(t *testing.T) {
	unixGerek(t)
	if os.Geteuid() != 0 {
		t.Skip("root gerekir")
	}
	r := Calistir(&Is{Kimlik: "u1", Betik: "id -un", ZamanAsimi: 5, Kullanici: "nobody"}, "", nil)
	if r.Durum != "basarili" || strings.TrimSpace(r.Stdout) != "nobody" {
		t.Fatalf("kullanıcı: %+v", r)
	}
}

// Dosya alma: özet tutmazsa dosya yazılmaz; tutarsa yazılır. Çekirdek sahte bir httptest sunucusudur ve cevaplarını
// gerçek çekirdek gibi imzalar.
func TestDosyaAlOzetDogrulamasi(t *testing.T) {
	unixGerek(t)
	a, _ := AnahtarTuret(gizliOrnek)
	icerik := []byte("filo dosyasi\n")
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set(BaslikImza, YanitImzasi(a.Is, r.Header.Get(BaslikNonce), icerik))
		_, _ = w.Write(icerik)
	}))
	defer srv.Close()
	ajan := &Ajan{ayar: Ayar{Cekirdek: srv.URL}, kimlik: Kimlik{AjanKimligi: "A", Gizli: gizliOrnek}, anahtar: a,
		http: srv.Client()}
	hedef := filepath.Join(t.TempDir(), "alt", "f.txt")
	r := ajan.dosyaAl(&Is{Kimlik: "d1", ZamanAsimi: 5, Dosya: &DosyaBilgisi{Ad: "f", Yol: hedef, Ozet: strings.Repeat("0", 64)}})
	if r.Durum != "hatali" || !strings.Contains(r.Neden, "özeti") {
		t.Fatalf("özet tutmazken yazıldı: %+v", r)
	}
	if _, err := os.Stat(hedef); err == nil {
		t.Fatal("özet tutmayan dosya diske yazıldı")
	}
	r = ajan.dosyaAl(&Is{Kimlik: "d2", ZamanAsimi: 5, Dosya: &DosyaBilgisi{Ad: "f", Yol: hedef, Ozet: govdeOzeti(icerik), Kip: "0640"}})
	if r.Durum != "basarili" {
		t.Fatalf("dosya alınamadı: %+v", r)
	}
	if v, _ := os.ReadFile(hedef); string(v) != string(icerik) {
		t.Fatal("içerik farklı")
	}
	if s, _ := os.Stat(hedef); s.Mode().Perm() != 0o640 {
		t.Fatalf("kip %v", s.Mode().Perm())
	}
}

// Çekirdeğin imzasız cevabı yok sayılır.
func TestImzasizCevapYokSayilir(t *testing.T) {
	a, _ := AnahtarTuret(gizliOrnek)
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		_, _ = w.Write([]byte(`{"isler":[]}`))
	}))
	defer srv.Close()
	ajan := &Ajan{ayar: Ayar{Cekirdek: srv.URL}, kimlik: Kimlik{AjanKimligi: "A"}, anahtar: a, http: srv.Client()}
	if _, err := ajan.istek("POST", "/ajan/v1/yokla", map[string]int{"bekle": 1}, 0); err == nil {
		t.Fatal("imzasız cevap kabul edildi")
	}
}

func TestKayitGizliAnahtari0600Yazar(t *testing.T) {
	unixGerek(t)
	dizin := t.TempDir()
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		_, _ = w.Write([]byte(`{"ajan_kimligi":"A1","gizli":"` + gizliOrnek + `"}`))
	}))
	defer srv.Close()
	ayar, _ := json.Marshal(Ayar{Cekirdek: srv.URL, Sunucu: "S1", Belirtec: "tek-kullanimlik"})
	_ = os.WriteFile(filepath.Join(dizin, "ajan.json"), ayar, 0o600)
	a, err := yukle(dizin)
	if err != nil {
		t.Fatal(err)
	}
	if err := a.kayitOl(); err != nil {
		t.Fatal(err)
	}
	s, err := os.Stat(filepath.Join(dizin, "kimlik.json"))
	if err != nil || s.Mode().Perm() != 0o600 {
		t.Fatalf("kimlik dosyası 0600 değil: %v %v", err, s)
	}
	v, _ := os.ReadFile(filepath.Join(dizin, "ajan.json"))
	if strings.Contains(string(v), "tek-kullanimlik") {
		t.Fatal("kayıt belirteci ayar dosyasında kaldı")
	}
}

func TestSistemBilgisi(t *testing.T) {
	b := SistemOku()
	if b.Isletim == "" || b.Mimari == "" || b.AjanSurum == "" {
		t.Fatalf("eksik: %+v", b)
	}
}
