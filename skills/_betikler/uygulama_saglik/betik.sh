#!/bin/sh
# Uygulama sağlık kontrolü. /etc/uygulama/uyumlu-kutuphane varsa uygulama yalnız o kütüphane sürümüyle çalışır.
echo "sunucu=$(hostname)"
servis=$( (systemctl is-active uygulama || rc-service uygulama status) 2>/dev/null | head -1)
bekl=$(cat /etc/uygulama/uyumlu-kutuphane 2>/dev/null)
kurulu=$(cat /usr/lib/filo-ornek/filo-kutuphane.surum 2>/dev/null)
if [ -n "$bekl" ] && [ -n "$kurulu" ] && [ "$bekl" != "$kurulu" ]; then
  echo "saglik=bozuk"
  echo "uygulama filo-kutuphane $kurulu ile başlamıyor (uyumlu sürüm: $bekl)" >&2
  exit 1
fi
echo "saglik=iyi"
