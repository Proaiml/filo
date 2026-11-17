FROM debian:bookworm-slim
# Paket listeleri imajda kalır: kurulum becerileri depo üst verisini yeniden indirmeden çalışır.
RUN apt-get update \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends openssh-server sudo procps iproute2 ca-certificates \
 && rm -f /var/cache/apt/archives/*.deb \
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
 && echo debian > /etc/filo/aile
# D1: yeniden başlatma öykünmesi ve yerel paket deposu (filo-depo). Eski sürüm örnek paketler kurulur (bekleyen yama
# tekrarlanabilir olsun); internet kaynakları kapatılır, tek kaynak laboratuvar deposudur. Kurum standardı depo tanımı
# /etc/filo/depo-standart altında saklanır (depo_onar buna döner).
COPY goruntu/ortak/filo-yeniden-baslat /usr/local/sbin/filo-yeniden-baslat
COPY depo/srv/debian/ /tmp/depo/
RUN sed -i 's/\r$//' /usr/local/sbin/filo-yeniden-baslat && chmod 755 /usr/local/sbin/filo-yeniden-baslat \
 && dpkg -i /tmp/depo/filo-araclar_1.0.0-1_all.deb /tmp/depo/filo-kutuphane_2.0.0-1_all.deb \
      /tmp/depo/filo-cekirdek_5.10.0-1_all.deb /tmp/depo/filo-izleme_3.2.0-1_all.deb >/dev/null \
 && rm -rf /tmp/depo /run/reboot-required /run/reboot-required.pkgs \
 && rm -f /etc/apt/sources.list.d/debian.sources /etc/apt/sources.list \
 && printf 'deb [trusted=yes] http://filo-depo/debian ./\ndeb [trusted=yes] http://filo-depo/debian-guvenlik ./\n' > /etc/apt/sources.list.d/filo-depo.list \
 && mkdir -p /etc/filo/depo-standart && cp /etc/apt/sources.list.d/filo-depo.list /etc/filo/depo-standart/ \
 && rm -rf /var/lib/apt/lists/* && mkdir -p /var/lib/apt/lists/partial
EXPOSE 22
CMD ["/usr/local/sbin/giris.sh"]
