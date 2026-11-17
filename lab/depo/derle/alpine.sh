#!/bin/sh
# Alpine 3.20 deposu: örnek paketler (abuild, laboratuvar anahtarıyla imzalı) + aynalanan jq/oniguruma/tree (apk fetch)
# + imzalı APKINDEX + secdb.json (güvenlik düzeltmeleri; Alpine secdb biçimi). Yalnız `python -m filo lab depo-derle`
# çalıştırır (bir kez internet ister). Özel anahtar konteynerde kalır ve atılır; depoya yalnız açık anahtar yazılır.
set -e
apk add -q abuild >/dev/null
R=/depo/srv/alpine; A=$R/x86_64
rm -rf "$R"; mkdir -p "$A"
export USER=filo-lab PACKAGER='Filo Lab <lab@filo.yerel>'
abuild-keygen -a -n -q 2>/dev/null || abuild-keygen -a -n
. /root/.abuild/abuild.conf
cp "$PACKAGER_PRIVKEY.pub" /etc/apk/keys/
cd "$A" && apk fetch -q jq oniguruma tree
paket() {  # ad surum reboot aciklama
  ad=$1; v=$2; rb=$3; ac=$(echo "$4" | tr '_' ' '); d=/tmp/b/filo/$ad-$v
  rm -rf "$d"; mkdir -p "$d"; cd "$d"
  kur=""
  if [ "$rb" = evet ]; then
    printf '#!/bin/sh\ntouch /var/run/reboot-required\necho %s >> /var/run/reboot-required.pkgs\nexit 0\n' "$ad" > "$ad.post-install"
    cp "$ad.post-install" "$ad.post-upgrade"; chmod 755 "$ad.post-install" "$ad.post-upgrade"
    kur="install=\"\$pkgname.post-install \$pkgname.post-upgrade\""
  fi
  cat > APKBUILD <<EOF
pkgname=$ad
pkgver=$v
pkgrel=0
pkgdesc="$ac"
url="http://filo-depo/"
arch="noarch"
license="MIT"
options="!check"
$kur
source=""
package() {
	mkdir -p "\$pkgdir"/usr/bin "\$pkgdir"/usr/lib/filo-ornek
	printf '#!/bin/sh\necho "%s %s"\n' "$ad" "$v" > "\$pkgdir"/usr/bin/$ad
	chmod 755 "\$pkgdir"/usr/bin/$ad
	echo "$v" > "\$pkgdir"/usr/lib/filo-ornek/$ad.surum
}
EOF
  abuild -F -d -q -P /tmp/cikti >/dev/null 2>&1 || abuild -F -d -P /tmp/cikti
  cp /tmp/cikti/filo/x86_64/$ad-$v-r0.apk "$A/"
}
echo '{"apkurl": "{{urlprefix}}/{{reponame}}/{{arch}}/{{pkg.name}}-{{pkg.ver}}.apk", "archs": ["x86_64"], "reponame": "alpine", "urlprefix": "http://filo-depo", "distroversion": "v3.20", "packages": [' > /tmp/secdb.json
ilk=1
grep -v '^#' /tmp/paketler.txt | while read -r ad eski yeni gv rb ac; do
  [ -n "$ad" ] || continue
  paket "$ad" "$eski" "$rb" "$ac"
  paket "$ad" "$yeni" "$rb" "$ac"
  if [ "$gv" = evet ]; then
    cve=$(echo "$ac" | sed -n 's/.*(\(LAB-[0-9-]*\)).*/\1/p')
    [ -f /tmp/secdb.ilk ] && printf ',' >> /tmp/secdb.json
    touch /tmp/secdb.ilk
    printf '{"pkg": {"name": "%s", "secfixes": {"%s-r0": ["%s"]}}}' "$ad" "$yeni" "$cve" >> /tmp/secdb.json
  fi
done
echo ']}' >> /tmp/secdb.json
cp /tmp/secdb.json "$R/secdb.json"
cd "$A"
apk index -q --rewrite-arch x86_64 -o APKINDEX.tar.gz --description "filo-lab" *.apk
abuild-sign -q APKINDEX.tar.gz
# apk imzayı anahtar dosyasının ADIYLA eşler (.SIGN.RSA.<ad>): imajlara aynı adla /etc/apk/keys altına konur
cp "$PACKAGER_PRIVKEY.pub" "$R/"
ls -la "$R" "$A"
