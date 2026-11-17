#!/bin/sh
# Uygulama dizinlerinin kapladığı alan (KB).
for d in /veri /opt/uygulama /etc/uygulama; do
  [ -d "$d" ] && echo "$d|$(du -sk "$d" 2>/dev/null | cut -f1)"
done
