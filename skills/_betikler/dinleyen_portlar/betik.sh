#!/bin/sh
# Dinlemedeki TCP portları.
ss -ltnH 2>/dev/null | awk '{n=split($4,a,":"); print a[n]}' | sort -un | sed 's/^/port=/' | head -50
