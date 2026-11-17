package main

import (
	"bufio"
	"os"
	"os/exec"
	"runtime"
	"strings"
)

type SistemBilgisi struct {
	AnaBilgisayar   string `json:"ana_bilgisayar"`
	Isletim         string `json:"isletim"`
	Mimari          string `json:"mimari"`
	Dagitim         string `json:"dagitim"`
	DagitimSurum    string `json:"dagitim_surum"`
	DagitimAd       string `json:"dagitim_ad"`
	Aile            string `json:"aile"`
	Cekirdek        string `json:"cekirdek"`
	PaketYoneticisi string `json:"paket_yoneticisi"`
	AjanSurum       string `json:"ajan_surum"`
	HizmetYoneticisi string `json:"hizmet_yoneticisi"`
}

func osRelease(yol string) map[string]string {
	m := map[string]string{}
	f, err := os.Open(yol)
	if err != nil {
		return m
	}
	defer f.Close()
	s := bufio.NewScanner(f)
	for s.Scan() {
		k, v, ok := strings.Cut(s.Text(), "=")
		if ok {
			m[k] = strings.Trim(v, `"'`)
		}
	}
	return m
}

func aileBul(id, benzer string) string {
	t := " " + id + " " + benzer + " "
	switch {
	case strings.Contains(t, " debian ") || strings.Contains(t, " ubuntu "):
		return "debian"
	case strings.Contains(t, " rhel ") || strings.Contains(t, " fedora ") || strings.Contains(t, " centos "):
		return "rhel"
	case strings.Contains(t, " alpine "):
		return "alpine"
	case strings.Contains(t, " suse ") || strings.Contains(t, " opensuse "):
		return "suse"
	}
	return id
}

func SistemOku() SistemBilgisi {
	b := SistemBilgisi{Isletim: runtime.GOOS, Mimari: runtime.GOARCH, AjanSurum: surum}
	b.AnaBilgisayar, _ = os.Hostname()
	if runtime.GOOS == "windows" {
		b.Dagitim, b.Aile, b.PaketYoneticisi, b.HizmetYoneticisi = "windows", "windows", "winget", "scm"
		return b
	}
	r := osRelease("/etc/os-release")
	b.Dagitim, b.DagitimSurum, b.DagitimAd = r["ID"], r["VERSION_ID"], r["PRETTY_NAME"]
	b.Aile = aileBul(r["ID"], r["ID_LIKE"])
	if k, err := os.ReadFile("/proc/sys/kernel/osrelease"); err == nil {
		b.Cekirdek = strings.TrimSpace(string(k))
	}
	for _, p := range []string{"apt-get", "dnf", "yum", "apk", "zypper"} {
		if _, err := exec.LookPath(p); err == nil {
			b.PaketYoneticisi = p
			break
		}
	}
	switch {
	case dizinVar("/run/systemd/system"):
		b.HizmetYoneticisi = "systemd"
	case dosyaVar("/usr/local/sbin/filo-svc"):
		b.HizmetYoneticisi = "filo-svc"
	case dosyaVar("/sbin/openrc-run"):
		b.HizmetYoneticisi = "openrc"
	default:
		b.HizmetYoneticisi = "yok"
	}
	return b
}

func dizinVar(y string) bool {
	s, err := os.Stat(y)
	return err == nil && s.IsDir()
}

func dosyaVar(y string) bool {
	s, err := os.Stat(y)
	return err == nil && !s.IsDir()
}
