FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    libtasn1-6 \
    gdbserver \
    socat \
    && apt-get clean

RUN mkdir -p /workdir

WORKDIR /workdir

COPY ./pwnmyasn1 /workdir/

RUN echo "PWNME{f873f7c3b72f439d597cce044707c505}" > /workdir/flag.txt

RUN groupadd --system ctf && \
	useradd -M -d /workdir -g ctf player && \
	chmod +r /workdir/flag.txt && \
	chmod +x /workdir/pwnmyasn1 && \
	chown -R player:ctf /workdir

USER player

ENTRYPOINT ["socat", "TCP-LISTEN:31000,reuseaddr,fork", "EXEC:'/workdir/pwnmyasn1',stderr"]