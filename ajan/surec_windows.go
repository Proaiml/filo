//go:build windows

package main

// Windows: derlenir ama gerçek bir Windows sunucuda DENENMEDİ (bkz. docs/ilerleme.md, B2). Betik PowerShell'e
// standart girdiden verilir; başka kullanıcı adına çalıştırma desteklenmez (ajan hizmet hesabıyla çalışır).

import (
	"errors"
	"os/exec"
	"strconv"
)

func kabukKomutu() (string, []string) {
	return "powershell.exe", []string{"-NoProfile", "-NonInteractive", "-Command", "-"}
}

func surecHazirla(cmd *exec.Cmd, kullanici string) error {
	if kullanici != "" {
		return errors.New("Windows ajanı başka kullanıcı adına çalıştırmayı desteklemiyor")
	}
	return nil
}

func surecOldur(cmd *exec.Cmd) {
	if cmd.Process == nil {
		return
	}
	// Alt süreçlerle birlikte sonlandır.
	_ = exec.Command("taskkill", "/T", "/F", "/PID", strconv.Itoa(cmd.Process.Pid)).Run()
	_ = cmd.Process.Kill()
}

func dosyaSahibi(yol, kullanici string) error { return nil }
