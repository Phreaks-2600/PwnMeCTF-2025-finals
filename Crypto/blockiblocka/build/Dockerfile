FROM ubuntu:22.04

ARG DEBIAN_FRONTEND=noninteractive
WORKDIR /app/

RUN apt-get update && apt-get install -y socat python3 python3-pip

RUN python3 -m pip install --upgrade pip
RUN pip3 install -v pycryptodome tinyec

RUN echo "FLAG=\"PWNME{6067e7997e0302ad4b822f45bb085af7}\"" > /app/flag.py

COPY ./challenge.py /app/

RUN groupadd -r ctf && \
    useradd -r -g ctf player && \
    chmod u+s /app/challenge.py

RUN chown player:ctf /app/challenge.py
USER player

ENTRYPOINT ["socat","TCP-LISTEN:3000,reuseaddr,fork","EXEC:'python3.10 /app/challenge.py',stderr"]
