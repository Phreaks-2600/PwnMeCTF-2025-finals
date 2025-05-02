FROM ubuntu:22.04

ARG DEBIAN_FRONTEND=noninteractive
WORKDIR /app/

RUN apt-get update -y && apt-get install -y socat python3 python3-pip

RUN python3 -m pip install --upgrade pip

RUN echo "PWNME{8ce8910cd620f3c71d2d608738530ab4}" > /flag.txt

COPY ./wankel /app/wankel
RUN pip3 install /app/wankel

RUN groupadd -r ctf && \
    useradd -r -g ctf player

USER player

ENTRYPOINT ["socat","TCP-LISTEN:1234,reuseaddr,fork","EXEC:'wankel --source-from-stdin',stderr"]
