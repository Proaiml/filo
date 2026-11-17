package main

// İmza ve kimlik: ajana özel gizli anahtardan iki ayrı anahtar türetilir.
//
//	istek anahtarı = HMAC-SHA256(gizli, "filo-istek-v1")   ajanın çekirdeğe giden her isteği
//	iş anahtarı    = HMAC-SHA256(gizli, "filo-is-v1")      çekirdeğin iş paketleri ve cevapları
//
// İki yön ayrı anahtar kullanır: ajanın bir isteğinin imzası, çekirdekten gelmiş bir iş gibi yeniden oynatılamaz.
// Çekirdek tarafındaki karşılığı filo/ajan_kapisi.py içindedir; iki tarafın aynı sonucu verdiği sabit örnekle
// sınanır (imza_test.go ve tests/test_ajan_kapisi.py aynı örneği kullanır).

import (
	"crypto/hmac"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"strings"
	"sync"
	"time"
)

const (
	BaslikAjan  = "X-Filo-Ajan"
	BaslikZaman = "X-Filo-Zaman"
	BaslikNonce = "X-Filo-Nonce"
	BaslikImza  = "X-Filo-Imza"
)

func hmacHex(anahtar []byte, mesaj string) string {
	m := hmac.New(sha256.New, anahtar)
	m.Write([]byte(mesaj))
	return hex.EncodeToString(m.Sum(nil))
}

func turet(gizli []byte, etiket string) []byte {
	m := hmac.New(sha256.New, gizli)
	m.Write([]byte(etiket))
	return m.Sum(nil)
}

type Anahtarlar struct {
	Istek []byte
	Is    []byte
}

func AnahtarTuret(gizliHex string) (Anahtarlar, error) {
	g, err := hex.DecodeString(strings.TrimSpace(gizliHex))
	if err != nil || len(g) < 32 {
		return Anahtarlar{}, errors.New("gizli anahtar geçersiz")
	}
	return Anahtarlar{Istek: turet(g, "filo-istek-v1"), Is: turet(g, "filo-is-v1")}, nil
}

func govdeOzeti(govde []byte) string {
	o := sha256.Sum256(govde)
	return hex.EncodeToString(o[:])
}

// IstekImzasi: yöntem, yol, zaman, nonce ve gövde özeti.
func IstekImzasi(anahtar []byte, yontem, yol, zaman, nonce string, govde []byte) string {
	return hmacHex(anahtar, yontem+"\n"+yol+"\n"+zaman+"\n"+nonce+"\n"+govdeOzeti(govde))
}

// YanitImzasi: çekirdeğin cevabı, isteğin nonce'una bağlıdır (eski bir cevap yeniden oynatılamaz).
func YanitImzasi(anahtar []byte, nonce string, govde []byte) string {
	return hmacHex(anahtar, "yanit\n"+nonce+"\n"+govdeOzeti(govde))
}

// IsZarfi: iş paketi. Govde tam olarak imzalanan metindir; ajan imzayı doğrulamadan Govde'yi ayrıştırmaz.
type IsZarfi struct {
	Govde string `json:"govde"`
	Imza  string `json:"imza"`
}

type DosyaBilgisi struct {
	Ad   string `json:"ad"`
	Yol  string `json:"yol"`
	Ozet string `json:"ozet"`
	Kip  string `json:"kip"`
}

type Is struct {
	Kimlik      string        `json:"kimlik"`
	Ajan        string        `json:"ajan"`
	Tur         string        `json:"tur"` // calistir | dosya_al | sistem_bilgisi | surum
	Betik       string        `json:"betik"`
	ZamanAsimi  int           `json:"zaman_asimi"`
	CiktiSiniri int           `json:"cikti_siniri"`
	Kullanici   string        `json:"kullanici"`
	Dosya       *DosyaBilgisi `json:"dosya,omitempty"`
	Olusturma   int64         `json:"olusturma"`
	Gecerlilik  int64         `json:"gecerlilik"`
}

var IsTurleri = map[string]bool{"calistir": true, "dosya_al": true, "sistem_bilgisi": true, "surum": true}

// GorulenIsler: aynı iş kimliği ikinci kez çalıştırılmaz (yeniden oynatma koruması).
type GorulenIsler struct {
	mu sync.Mutex
	m  map[string]int64
}

func YeniGorulenIsler() *GorulenIsler { return &GorulenIsler{m: map[string]int64{}} }

func (g *GorulenIsler) Ekle(kimlik string, bitis int64) bool {
	g.mu.Lock()
	defer g.mu.Unlock()
	simdi := time.Now().Unix()
	for k, t := range g.m {
		if t < simdi-3600 {
			delete(g.m, k)
		}
	}
	if _, var_ := g.m[kimlik]; var_ {
		return false
	}
	g.m[kimlik] = bitis
	return true
}

// IsDogrula: imza, ajan kimliği, geçerlilik süresi, tür, yeniden oynatma. İmzasız ya da sahte imzalı iş reddedilir.
func IsDogrula(z IsZarfi, a Anahtarlar, ajanKimligi string, gorulen *GorulenIsler, simdi time.Time) (*Is, error) {
	if z.Imza == "" || z.Govde == "" {
		return nil, errors.New("imzasız iş reddedildi")
	}
	beklenen := hmacHex(a.Is, "is\n"+z.Govde)
	if !hmac.Equal([]byte(beklenen), []byte(strings.ToLower(z.Imza))) {
		return nil, errors.New("iş imzası tutmuyor: reddedildi")
	}
	var is Is
	if err := json.Unmarshal([]byte(z.Govde), &is); err != nil {
		return nil, fmt.Errorf("iş gövdesi okunamadı: %v", err)
	}
	if is.Ajan != ajanKimligi {
		return nil, errors.New("iş başka bir ajana ait: reddedildi")
	}
	if is.Gecerlilik == 0 || simdi.Unix() > is.Gecerlilik {
		return nil, errors.New("işin geçerlilik süresi dolmuş: reddedildi")
	}
	if !IsTurleri[is.Tur] {
		return nil, fmt.Errorf("bilinmeyen iş türü: %s", is.Tur)
	}
	if is.Kimlik == "" || !gorulen.Ekle(is.Kimlik, is.Gecerlilik) {
		return nil, errors.New("aynı iş ikinci kez geldi: reddedildi")
	}
	return &is, nil
}
