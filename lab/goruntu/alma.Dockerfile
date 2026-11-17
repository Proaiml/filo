FROM almalinux:9
# Depo üst verisi imajda önbellekte kalır: kurulum becerileri hızlı çalışır.
RUN dnf install -y --setopt=install_weak_deps=False openssh-server sudo procps-ng iproute hostname \
 && dnf makecache \
 && useradd -m -s /bin/bash filo && usermod -p '*' filo \
 && echo 'filo ALL=(ALL) NOPASSWD: ALL' > /etc/sudoers.d/filo && chmod 440 /etc/sudoers.d/filo \
 && mkdir -p /veri /etc/filo /opt/uygulama /etc/uygulama \
 && echo "surum=1.4.2" > /opt/uygulama/surum.txt \
 && printf 'port=8080\nlog_duzeyi=info\n' > /etc/uygulama/uygulama.conf
COPY ortak/filo-svc /usr/local/sbin/filo-svc
COPY ortak/systemctl /usr/local/bin/systemctl
COPY ortak/giris.sh /usr/local/sbin/giris.sh
COPY ortak/sshd_config /etc/ssh/sshd_config
RUN sed -i 's/\r$//' /usr/local/sbin/filo-svc /usr/local/bin/systemctl /usr/local/sbin/giris.sh /etc/ssh/sshd_config \
 && chmod 755 /usr/local/sbin/filo-svc /usr/local/bin/systemctl /usr/local/sbin/giris.sh \
 && ln -sf /usr/local/bin/systemctl /usr/bin/systemctl  && echo rhel > /etc/filo/aile
EXPOSE 22
CMD ["/usr/local/sbin/giris.sh"]
