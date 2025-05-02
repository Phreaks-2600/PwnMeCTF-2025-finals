FROM ubuntu:22.04

ARG DEBIAN_FRONTEND=noninteractive
WORKDIR /app/

RUN apt-get update && apt-get install -y socat python3 python3-pip

RUN python3 -m pip install --upgrade pip
RUN pip3 install -v pycryptodome numpy

COPY ./server.py /app/

RUN groupadd -r ctf && \
    useradd -r -g ctf player && \
    chmod u+s /app/server.py

RUN echo "FLAG=\"PWNME{b@d_id3a_to_make_ur_own_CrYPToGraPHic_Sch3me}\"" > /app/flag.py

RUN chown player:ctf /app/server.py
USER player

ENTRYPOINT ["socat","TCP-LISTEN:3000,reuseaddr,fork","EXEC:'python3.10 /app/server.py',stderr"]