#!/bin/sh
# AlmaLinux 9 deposu: örnek paketler (rpmbuild) + aynalanan jq/oniguruma/tree (dnf download) + repodata + updateinfo
# (güvenlik sınıfı). Yalnız `python -m filo lab depo-derle` çalıştırır (bir kez internet ister).
set -e
dnf -y -q install rpm-build createrepo_c 'dnf-command(download)' >/dev/null
R=/depo/srv/el9
rm -rf "$R"; mkdir -p "$R"
cd "$R" && dnf -q download --arch=x86_64 jq oniguruma tree
mkdir -p /root/rpmbuild/SPECS
paket() {  # ad surum reboot aciklama
  ad=$1; v=$2; rb=$3; ac=$(echo "$4" | tr '_' ' ')
  post=""
  if [ "$rb" = evet ]; then post="%post
touch /var/run/reboot-required
echo $ad >> /var/run/reboot-required.pkgs"; fi
  cat > /root/rpmbuild/SPECS/$ad-$v.spec <<EOF
%define _build_id_links none
Name: $ad
Version: $v
Release: 1
Summary: $ac
License: MIT
BuildArch: noarch
%description
$ac
%install
mkdir -p %{buildroot}/usr/bin %{buildroot}/usr/lib/filo-ornek
printf '#!/bin/sh\necho "$ad $v"\n' > %{buildroot}/usr/bin/$ad
chmod 755 %{buildroot}/usr/bin/$ad
echo $v > %{buildroot}/usr/lib/filo-ornek/$ad.surum
$post
%files
/usr/bin/$ad
/usr/lib/filo-ornek/$ad.surum
EOF
  rpmbuild -bb --quiet /root/rpmbuild/SPECS/$ad-$v.spec >/dev/null 2>&1
  cp /root/rpmbuild/RPMS/noarch/$ad-$v-1.noarch.rpm "$R/"
}
{
echo '<?xml version="1.0" encoding="UTF-8"?>'
echo '<updates>'
} > /tmp/updateinfo.xml
grep -v '^#' /tmp/paketler.txt | while read -r ad eski yeni gv rb ac; do
  [ -n "$ad" ] || continue
  paket "$ad" "$eski" "$rb" "$ac"
  paket "$ad" "$yeni" "$rb" "$ac"
  if [ "$gv" = evet ]; then tur=security; sid="FILO-SV-2026:$ad"; else tur=bugfix; sid="FILO-BA-2026:$ad"; fi
  cve=$(echo "$ac" | sed -n 's/.*(\(LAB-[0-9-]*\)).*/\1/p')
  cat >> /tmp/updateinfo.xml <<EOF
 <update from="lab@filo.yerel" status="stable" type="$tur" version="1">
  <id>$sid</id>
  <title>$ad $yeni</title>
  <issued date="2026-11-01 00:00:00"/>
  <severity>$( [ "$gv" = evet ] && echo Important || echo None )</severity>
  <description>$(echo "$ac" | tr '_' ' ')</description>
  <references>$( [ -n "$cve" ] && echo "<reference href=\"http://filo-depo/guvenlik/$cve\" id=\"$cve\" type=\"cve\" title=\"$cve\"/>" )</references>
  <pkglist><collection short="filo-lab"><name>Filo lab</name>
   <package name="$ad" version="$yeni" release="1" epoch="0" arch="noarch"><filename>$ad-$yeni-1.noarch.rpm</filename></package>
  </collection></pkglist>
 </update>
EOF
done
echo '</updates>' >> /tmp/updateinfo.xml
createrepo_c -q "$R"
modifyrepo_c --mdtype=updateinfo /tmp/updateinfo.xml "$R/repodata"
ls -la "$R" "$R/repodata"
