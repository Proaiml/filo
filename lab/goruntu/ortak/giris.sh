#!/bin/sh
# Laboratuvar konteynerinin girişi: anahtarı yerleştirir, servisleri tanımlayıp başlatır, sshd'yi ön planda çalıştırır.
set -e
mkdir -p /home/filo/.ssh /run/sshd /run/filo-svc /etc/filo-svc /var/log/filo
if [ -f /etc/filo/authorized_keys ]; then
  cp /etc/filo/authorized_keys /home/filo/.ssh/authorized_keys
fi
chown -R filo:filo /home/filo/.ssh
chmod 700 /home/filo/.ssh
chmod 600 /home/filo/.ssh/authorized_keys 2>/dev/null || true
if [ -f /etc/filo/hostkey ]; then
  cp /etc/filo/hostkey /etc/ssh/ssh_host_ed25519_key
  chmod 600 /etc/ssh/ssh_host_ed25519_key
fi
chown filo:filo /veri 2>/dev/null || true

# Çalıştırma kimlikleri (C1): servis kullanıcıları ve filo'nun sudo yetkisi.
#   FILO_KULLANICILAR=uygulama        oluşturulacak servis kullanıcıları (oturum açamaz)
#   FILO_SUDO=tam | kok | yok         tam: her kullanıcıya parolasız sudo; kok: yalnız root'a; yok: parolasız sudo yok
for k in $(echo "${FILO_KULLANICILAR:-uygulama}" | tr ',' ' '); do
  id "$k" >/dev/null 2>&1 || useradd -M -r -s /sbin/nologin "$k" 2>/dev/null || adduser -S -D -H -s /sbin/nologin "$k" 2>/dev/null || true
done
case "${FILO_SUDO:-tam}" in
  kok) echo 'filo ALL=(root) NOPASSWD: ALL' > /etc/sudoers.d/filo ;;
  yok) rm -f /etc/sudoers.d/filo ;;
  *)   echo 'filo ALL=(ALL) NOPASSWD: ALL' > /etc/sudoers.d/filo ;;
esac
[ -f /etc/sudoers.d/filo ] && chmod 440 /etc/sudoers.d/filo

# Servisler: FILO_SERVISLER=uygulama,webd
for s in $(echo "${FILO_SERVISLER:-uygulama}" | tr ',' ' '); do
  if [ ! -f "/etc/filo-svc/$s.cmd" ]; then
    printf 'while :; do date +%%s > /run/filo-svc/%s.hb; sleep 10; done\n' "$s" > "/etc/filo-svc/$s.cmd"
  fi
  /usr/local/sbin/filo-svc start "$s" || true
done
echo "$(hostname) hazir" > /var/log/filo/giris.log
exec /usr/sbin/sshd -D -e -f /etc/ssh/sshd_config
