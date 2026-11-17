package main

// Komut/betik çalıştırma. Sonuç şeması çekirdekteki filo/yurutme.py ile aynıdır:
// durum basarili | hatali | zaman_asimi | iptal, çıkış kodu, stdout, stderr, süre, kesildi.
// Betik standart girdiden kabuğa verilir (SSH yolundaki `sh -s` ile aynı anlam): komut satırında tırnak sorunu ve
// gizli bilgi olmaz. Zaman aşımında ve iptalde bütün süreç grubu öldürülür.

import (
	"bytes"
	"os/exec"
	"strings"
	"sync"
	"time"
)

type Sonuc struct {
	Kimlik    string  `json:"kimlik"`
	Durum     string  `json:"durum"`
	CikisKodu *int    `json:"cikis_kodu"`
	Stdout    string  `json:"stdout"`
	Stderr    string  `json:"stderr"`
	Sure      float64 `json:"sure"`
	Kesildi   bool    `json:"kesildi"`
	Kullanici string  `json:"kullanici"`
	Neden     string  `json:"neden"`
}

// sinirliYazici: ilk `sinir` baytı tutar, fazlasını sayar.
type sinirliYazici struct {
	mu      sync.Mutex
	b       bytes.Buffer
	sinir   int
	kesildi bool
}

func (s *sinirliYazici) Write(p []byte) (int, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	kalan := s.sinir - s.b.Len()
	if kalan <= 0 {
		if len(p) > 0 {
			s.kesildi = true
		}
		return len(p), nil
	}
	if len(p) > kalan {
		s.b.Write(p[:kalan])
		s.kesildi = true
		return len(p), nil
	}
	s.b.Write(p)
	return len(p), nil
}

func (s *sinirliYazici) metin() string {
	s.mu.Lock()
	defer s.mu.Unlock()
	return strings.ToValidUTF8(s.b.String(), "")
}

// Calistir: betiği kullanıcı adına çalıştırır. iptal kanalı kapanırsa süreç grubu öldürülür.
func Calistir(is *Is, varsayilanKullanici string, iptal <-chan struct{}) Sonuc {
	kullanici := is.Kullanici
	if kullanici == "" {
		kullanici = varsayilanKullanici
	}
	r := Sonuc{Kimlik: is.Kimlik, Durum: "hatali", Kullanici: kullanici}
	zaman := is.ZamanAsimi
	if zaman <= 0 {
		r.Neden = "zaman aşımı zorunlu ve pozitif olmalı"
		return r
	}
	sinir := is.CiktiSiniri
	if sinir <= 0 {
		sinir = 65536
	}
	ad, arg := kabukKomutu()
	cmd := exec.Command(ad, arg...)
	cmd.Stdin = strings.NewReader(is.Betik)
	out := &sinirliYazici{sinir: sinir}
	errw := &sinirliYazici{sinir: sinir / 4}
	cmd.Stdout, cmd.Stderr = out, errw
	if err := surecHazirla(cmd, kullanici); err != nil {
		r.Neden = "çalıştırma kullanıcısı: " + err.Error()
		return r
	}
	bas := time.Now()
	if err := cmd.Start(); err != nil {
		r.Neden = "başlatılamadı: " + err.Error()
		return r
	}
	bitti := make(chan error, 1)
	go func() { bitti <- cmd.Wait() }()
	zamanlayici := time.NewTimer(time.Duration(zaman) * time.Second)
	defer zamanlayici.Stop()
	var bekleHata error
	select {
	case bekleHata = <-bitti:
		r.Durum = "basarili"
	case <-zamanlayici.C:
		surecOldur(cmd)
		<-bitti
		r.Durum, r.Neden = "zaman_asimi", "süre doldu"
	case <-iptal:
		surecOldur(cmd)
		<-bitti
		r.Durum, r.Neden = "iptal", "çekirdek işi iptal etti"
	}
	r.Sure = float64(time.Since(bas).Milliseconds()) / 1000.0
	r.Stdout, r.Stderr = out.metin(), errw.metin()
	r.Kesildi = out.kesildi || errw.kesildi
	if r.Durum == "basarili" {
		kod := 0
		if bekleHata != nil {
			if ee, ok := bekleHata.(*exec.ExitError); ok {
				kod = ee.ExitCode()
			} else {
				kod = -1
				r.Neden = bekleHata.Error()
			}
		}
		r.CikisKodu = &kod
		if kod != 0 {
			r.Durum = "hatali"
		}
	}
	return r
}
