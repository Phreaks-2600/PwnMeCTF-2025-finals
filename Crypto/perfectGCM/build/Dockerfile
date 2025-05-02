FROM alpine:3.16.0

ARG DEBIAN_FRONTEND=noninteractive
WORKDIR /app/

RUN apk add socat python3 py-pip

RUN python3 -m pip install pycryptodome

COPY ./server.py /app/
COPY ./challenge.py /app/

RUN addgroup -S ctf && \
    adduser -S player -G ctf && \
    chmod u+s /app/server.py

RUN echo "FLAG=\"PWNME{luck1ly_1_th0ugh7_t0_ch3ck}\"" > /app/secret.py

RUN chown player:ctf /app/challenge.py
USER player

ENTRYPOINT ["socat","TCP-LISTEN:3000,reuseaddr,fork","EXEC:'python3 /app/server.py',stderr"]
