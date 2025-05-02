FROM python:3.12

WORKDIR /app/

COPY aes.py handler.py mac.py server.py /app/

RUN echo "PWNME{Cryptanalysis Mastery. You're a pro!}" > /flag.txt

RUN groupadd -r ctf && \
    useradd -r -g ctf player && \
    chmod u+s /app/handler.py

RUN chown player:ctf /app/handler.py
USER player
EXPOSE 6666

CMD ["python3","handler.py"]