FROM almalinux:9
# Depo üst verisi imajda önbellekte kalır: kurulum becerileri hızlı çalışır.
RUN dnf install -y --setopt=install_weak_deps=False openssh-server sudo procps-ng iproute hostname \
 && dnf makecache \
 && useradd -m -s /bin/bash filo && usermod -p '*' filo \
 && echo 'filo ALL=(ALL) NOPASSWD: ALL' > /etc/sudoers.d/filo && chmod 440 /etc/sudoers.d/filo \
 && mkdir -p /veri /etc/filo /opt/uygulama /etc/uygulama \
 && echo "surum=1.4.2" > /opt/uygulama/surum.txt \
 && printf 'port=8080\nlog_duzeyi=info\n' > /etc/uygulama/uygulama.conf
COPY goruntu/ortak/filo-svc /usr/local/sbin/filo-svc
COPY goruntu/ortak/systemctl /usr/local/bin/systemctl
COPY goruntu/ortak/giris.sh /usr/local/sbin/giris.sh
COPY goruntu/ortak/sshd_config /etc/ssh/sshd_config
RUN sed -i 's/\r$//' /usr/local/sbin/filo-svc /usr/local/bin/systemctl /usr/local/sbin/giris.sh /etc/ssh/sshd_config \
 && chmod 755 /usr/local/sbin/filo-svc /usr/local/bin/systemctl /usr/local/sbin/giris.sh \
 && ln -sf /usr/local/bin/systemctl /usr/bin/systemctl  && echo rhel > /etc/filo/aile
# D1: yeniden başlatma öykünmesi ve yerel paket deposu (filo-depo); ayrıntı debian.Dockerfile'da.
COPY goruntu/ortak/filo-yeniden-baslat /usr/local/sbin/filo-yeniden-baslat
COPY depo/srv/el9/ /tmp/depo/
RUN sed -i 's/\r$//' /usr/local/sbin/filo-yeniden-baslat && chmod 755 /usr/local/sbin/filo-yeniden-baslat \
 && rpm -i /tmp/depo/filo-araclar-1.0.0-1.noarch.rpm /tmp/depo/filo-kutuphane-2.0.0-1.noarch.rpm \
      /tmp/depo/filo-cekirdek-5.10.0-1.noarch.rpm /tmp/depo/filo-izleme-3.2.0-1.noarch.rpm \
 && rm -rf /tmp/depo /run/reboot-required /run/reboot-required.pkgs \
 && mkdir -p /etc/yum.repos.d.kapali && mv /etc/yum.repos.d/*.repo /etc/yum.repos.d.kapali/ \
 && printf '[filo-depo]\nname=Filo laboratuvar deposu\nbaseurl=http://filo-depo/el9\nenabled=1\ngpgcheck=0\nmetadata_expire=60\n' > /etc/yum.repos.d/filo-depo.repo \
 && mkdir -p /etc/filo/depo-standart && cp /etc/yum.repos.d/filo-depo.repo /etc/filo/depo-standart/ \
 && dnf clean all >/dev/null
EXPOSE 22
CMD ["/usr/local/sbin/giris.sh"]
