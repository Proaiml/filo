FROM alpine:3.20
RUN apk add openssh-server sudo procps iproute2 \
 && apk update \
 && adduser -D -s /bin/sh filo && echo 'filo:*' | chpasswd -e \
 && mkdir -p /etc/sudoers.d && echo 'filo ALL=(ALL) NOPASSWD: ALL' > /etc/sudoers.d/filo && chmod 440 /etc/sudoers.d/filo \
 && mkdir -p /veri /etc/filo /opt/uygulama /etc/uygulama \
 && echo "surum=1.4.2" > /opt/uygulama/surum.txt \
 && printf 'port=8080\nlog_duzeyi=info\n' > /etc/uygulama/uygulama.conf
COPY ortak/filo-svc /usr/local/sbin/filo-svc
COPY ortak/rc-service /usr/local/bin/rc-service
COPY ortak/giris.sh /usr/local/sbin/giris.sh
COPY ortak/sshd_config /etc/ssh/sshd_config
RUN sed -i 's/\r$//' /usr/local/sbin/filo-svc /usr/local/bin/rc-service /usr/local/sbin/giris.sh /etc/ssh/sshd_config \
 && chmod 755 /usr/local/sbin/filo-svc /usr/local/bin/rc-service /usr/local/sbin/giris.sh \
 && echo alpine > /etc/filo/aile
EXPOSE 22
CMD ["/usr/local/sbin/giris.sh"]
