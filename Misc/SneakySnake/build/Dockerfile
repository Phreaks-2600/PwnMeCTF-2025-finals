FROM ubuntu:22.04

ARG DEBIAN_FRONTEND=noninteractive
WORKDIR /app/

RUN apt-get update && apt-get install -y socat python3 python3-pip

COPY ./challenge.py /app/

RUN groupadd -r ctf && \
    useradd -r -g ctf player && \
    chmod u+s /app/challenge.py

RUN chown player:ctf /app/challenge.py
USER player

ENTRYPOINT ["socat","TCP-LISTEN:3000,reuseaddr,fork","EXEC:'python3.10 /app/challenge.py',stderr"]
