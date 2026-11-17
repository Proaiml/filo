FROM alpine:3.20
RUN apk add openssh-server sudo procps iproute2 \
 && apk update \
 && adduser -D -s /bin/sh filo && echo 'filo:*' | chpasswd -e \
 && mkdir -p /etc/sudoers.d && echo 'filo ALL=(ALL) NOPASSWD: ALL' > /etc/sudoers.d/filo && chmod 440 /etc/sudoers.d/filo \
 && mkdir -p /veri /etc/filo /opt/uygulama /etc/uygulama \
 && echo "surum=1.4.2" > /opt/uygulama/surum.txt \
 && printf 'port=8080\nlog_duzeyi=info\n' > /etc/uygulama/uygulama.conf
COPY goruntu/ortak/filo-svc /usr/local/sbin/filo-svc
COPY goruntu/ortak/rc-service /usr/local/bin/rc-service
COPY goruntu/ortak/giris.sh /usr/local/sbin/giris.sh
COPY goruntu/ortak/sshd_config /etc/ssh/sshd_config
RUN sed -i 's/\r$//' /usr/local/sbin/filo-svc /usr/local/bin/rc-service /usr/local/sbin/giris.sh /etc/ssh/sshd_config \
 && chmod 755 /usr/local/sbin/filo-svc /usr/local/bin/rc-service /usr/local/sbin/giris.sh \
 && echo alpine > /etc/filo/aile
# D1: yeniden başlatma öykünmesi ve yerel paket deposu (filo-depo); ayrıntı debian.Dockerfile'da. Depo laboratuvar
# anahtarıyla imzalıdır; açık anahtar /etc/apk/keys altına aynı adla konur.
COPY goruntu/ortak/filo-yeniden-baslat /usr/local/sbin/filo-yeniden-baslat
COPY depo/srv/alpine/ /tmp/depo/
RUN sed -i 's/\r$//' /usr/local/sbin/filo-yeniden-baslat && chmod 755 /usr/local/sbin/filo-yeniden-baslat \
 && ln -sf /usr/local/sbin/filo-yeniden-baslat /usr/local/sbin/reboot \
 && cp /tmp/depo/*.rsa.pub /etc/apk/keys/ \
 && apk add -q --no-network /tmp/depo/x86_64/filo-araclar-1.0.0-r0.apk /tmp/depo/x86_64/filo-kutuphane-2.0.0-r0.apk \
      /tmp/depo/x86_64/filo-cekirdek-5.10.0-r0.apk /tmp/depo/x86_64/filo-izleme-3.2.0-r0.apk \
 && rm -rf /tmp/depo /run/reboot-required /run/reboot-required.pkgs \
 && echo 'http://filo-depo/alpine' > /etc/apk/repositories \
 && mkdir -p /etc/filo/depo-standart && cp /etc/apk/repositories /etc/filo/depo-standart/ \
 && rm -rf /var/cache/apk/* /lib/apk/db/../../var/cache/apk/*
EXPOSE 22
CMD ["/usr/local/sbin/giris.sh"]
