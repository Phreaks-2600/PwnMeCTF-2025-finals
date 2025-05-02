FROM python:3.10-slim

RUN apt-get update && apt-get install -y curl && apt-get clean

RUN pip install torch
RUN pip install pycryptodome
RUN pip install numpy

ARG FLAG
ENV FLAG=${FLAG}

WORKDIR /app

COPY server.py .
COPY mlp_backdoor.pth .

EXPOSE 4444

CMD ["python", "server.py"]
