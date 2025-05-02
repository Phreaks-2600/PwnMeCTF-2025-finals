FROM ubuntu:latest

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    build-essential \
    socat

RUN echo "PWNME{e1005fb19895b5d54696d06430281303}" > /flag.txt

RUN useradd -m -s /bin/bash user
USER user

WORKDIR /home/user

COPY pdf_generator .


ENV PDF_GENERATOR_PORT=12345

CMD  socat TCP-LISTEN:${PDF_GENERATOR_PORT},reuseaddr,fork EXEC:./pdf_generator
