#!/bin/sh
# Kısa sistem özeti.
. /etc/os-release 2>/dev/null
echo "sunucu=$(hostname)"
echo "isletim=$PRETTY_NAME"
echo "cekirdek=$(uname -r)"
echo "aile=$(cat /etc/filo/aile 2>/dev/null || echo bilinmiyor)"
