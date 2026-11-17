#!/bin/sh
# Debian deposu: örnek paketler (dpkg-deb) + aynalanan jq/tree (apt-get download) + Packages/Release.
# Yalnız `python -m filo lab depo-derle` çalıştırır (bir kez internet ister); çıktı lab/depo/srv altında kalır.
set -e
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq --no-install-recommends dpkg-dev apt-utils >/dev/null
N=/depo/srv/debian; G=/depo/srv/debian-guvenlik
rm -rf "$N" "$G"; mkdir -p "$N" "$G"
cd "$N" && apt-get download -qq jq libjq1 libonig5 tree
paket() {  # ad surum guvenlik reboot aciklama hedef_dizin
  ad=$1; v=$2; rb=$4; ac=$(echo "$5" | tr '_' ' '); d=/tmp/p/$ad-$v
  rm -rf "$d"; mkdir -p "$d/DEBIAN" "$d/usr/bin" "$d/usr/lib/filo-ornek"
  printf '#!/bin/sh\necho "%s %s"\n' "$ad" "$v" > "$d/usr/bin/$ad"; chmod 755 "$d/usr/bin/$ad"
  echo "$v" > "$d/usr/lib/filo-ornek/$ad.surum"
  printf 'Package: %s\nVersion: %s-1\nArchitecture: all\nMaintainer: Filo Lab <lab@filo.yerel>\nSection: misc\nPriority: optional\nDescription: %s\n' \
    "$ad" "$v" "$ac" > "$d/DEBIAN/control"
  if [ "$rb" = evet ]; then
    printf '#!/bin/sh\ntouch /var/run/reboot-required\necho %s >> /var/run/reboot-required.pkgs\nexit 0\n' "$ad" > "$d/DEBIAN/postinst"
    chmod 755 "$d/DEBIAN/postinst"
  fi
  dpkg-deb --root-owner-group -Zgzip --build "$d" "$6/${ad}_${v}-1_all.deb" >/dev/null
}
grep -v '^#' /tmp/paketler.txt | while read -r ad eski yeni gv rb ac; do
  [ -n "$ad" ] || continue
  paket "$ad" "$eski" "$gv" "$rb" "$ac" "$N"
  if [ "$gv" = evet ]; then paket "$ad" "$yeni" "$gv" "$rb" "$ac" "$G"; else paket "$ad" "$yeni" "$gv" "$rb" "$ac" "$N"; fi
done
for d in "$N:filo-lab:Filo:Filo-Lab" "$G:filo-lab-security:Filo-Security:Filo-Lab-Security"; do
  dir=${d%%:*}; r=${d#*:}; suite=${r%%:*}; r=${r#*:}; origin=${r%%:*}; label=${r#*:}
  cd "$dir"
  dpkg-scanpackages -m . /dev/null > Packages 2>/dev/null
  gzip -9kf Packages
  apt-ftparchive -o APT::FTPArchive::Release::Origin="$origin" -o APT::FTPArchive::Release::Label="$label" \
    -o APT::FTPArchive::Release::Suite="$suite" -o APT::FTPArchive::Release::Codename="$suite" \
    -o APT::FTPArchive::Release::Architectures="amd64 all" release . > Release
done
ls -la "$N" "$G"
