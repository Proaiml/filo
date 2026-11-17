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
# Açılış kimliği (yeniden başlatma öykünmesi bunu yeniler; beceriler "yeniden başladı mı" sorusunu buna bakarak cevaplar)
cat /proc/sys/kernel/random/uuid > /run/filo-acilis-kimligi
date +%s > /run/filo-acilis-zamani
rm -f /run/reboot-required /run/reboot-required.pkgs

# Yerel paket deposu (D1): laboratuvar ağındaki filo-depo konteyneri tek paket kaynağıdır (kurum içi ayna gibi; internet
# gerekmez). Depo üst verisi açılışta yenilenir; depo henüz hazır değilse birkaç kez denenir.
aile=$(cat /etc/filo/aile 2>/dev/null)
for i in 1 2 3 4 5 6 7 8 9 10 11 12; do
  case "$aile" in
    debian) apt-get update -qq >/dev/null 2>&1 && break ;;
    rhel) dnf -q makecache >/dev/null 2>&1 && break ;;
    alpine) apk update -q >/dev/null 2>&1 && break ;;
    *) break ;;
  esac
  sleep 1
done
# FILO_YAMALI=hepsi | guvenlik: bu sunucu açılışta yamalanmış olsun (filo yama uyumu raporunda karışık bir filo görünsün)
case "${FILO_YAMALI:-}" in
  hepsi) pk="filo-araclar filo-kutuphane filo-cekirdek filo-izleme" ;;
  guvenlik) pk="filo-kutuphane filo-cekirdek" ;;
  *) pk="" ;;
esac
if [ -n "$pk" ]; then
  case "$aile" in
    debian) DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --only-upgrade $pk >/dev/null 2>&1 || true ;;
    rhel) dnf -y -q upgrade $pk >/dev/null 2>&1 || true ;;
    alpine) apk add -q -u $pk >/dev/null 2>&1 || true ;;
  esac
  rm -f /run/reboot-required /run/reboot-required.pkgs
fi
echo "$(hostname) hazir" > /var/log/filo/giris.log
exec /usr/sbin/sshd -D -e -f /etc/ssh/sshd_config
