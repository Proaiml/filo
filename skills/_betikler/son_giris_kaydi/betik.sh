#!/bin/sh
# Filo laboratuvar giriş kaydının son satırları.
tail -n 20 /var/log/filo/giris.log 2>/dev/null || echo "kayit yok"
