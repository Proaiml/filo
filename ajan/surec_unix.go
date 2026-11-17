//go:build !windows

package main

import (
	"errors"
	"os"
	"os/exec"
	"os/user"
	"strconv"
	"syscall"
)

func kabukKomutu() (string, []string) { return "/bin/sh", []string{"-s"} }

// surecHazirla: süreç kendi grubunda başlar (zaman aşımında bütün grup öldürülür). Ajan root ise iş, istenen
// kullanıcının kimliğiyle (uid, gid, ek gruplar) çalışır; SSH yolundaki gibi `sudo` gerekiyorsa betik kendisi çağırır.
func surecHazirla(cmd *exec.Cmd, kullanici string) error {
	attr := &syscall.SysProcAttr{Setpgid: true}
	cmd.SysProcAttr = attr
	ortam := []string{"PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin", "LANG=C.UTF-8"}
	if kullanici == "" {
		cmd.Env = append(ortam, "HOME=/root", "USER=root")
		return nil
	}
	u, err := user.Lookup(kullanici)
	if err != nil {
		return err
	}
	cmd.Env = append(ortam, "HOME="+u.HomeDir, "USER="+u.Username, "LOGNAME="+u.Username)
	cmd.Dir = u.HomeDir
	if os.Geteuid() != 0 {
		if strconv.Itoa(os.Geteuid()) != u.Uid {
			return errors.New("ajan root değil; başka kullanıcı adına çalıştıramaz")
		}
		return nil
	}
	uid, _ := strconv.Atoi(u.Uid)
	gid, _ := strconv.Atoi(u.Gid)
	var gruplar []uint32
	if ids, err := u.GroupIds(); err == nil {
		for _, g := range ids {
			if n, err := strconv.Atoi(g); err == nil {
				gruplar = append(gruplar, uint32(n))
			}
		}
	}
	attr.Credential = &syscall.Credential{Uid: uint32(uid), Gid: uint32(gid), Groups: gruplar}
	return nil
}

func surecOldur(cmd *exec.Cmd) {
	if cmd.Process == nil {
		return
	}
	_ = syscall.Kill(-cmd.Process.Pid, syscall.SIGKILL)
	_ = cmd.Process.Kill()
}

func dosyaSahibi(yol, kullanici string) error {
	if kullanici == "" || os.Geteuid() != 0 {
		return nil
	}
	u, err := user.Lookup(kullanici)
	if err != nil {
		return err
	}
	uid, _ := strconv.Atoi(u.Uid)
	gid, _ := strconv.Atoi(u.Gid)
	return os.Chown(yol, uid, gid)
}
