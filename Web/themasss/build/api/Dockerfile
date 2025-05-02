FROM python:3.8-slim

WORKDIR /api

RUN mkdir -p /shared/uploads && mkdir -p /shared/sqlite

COPY shared_db.sqlite /shared/sqlite/shared_db.sqlite

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY ../reset.py /reset.py

COPY . .

CMD ["bash", "-c", "python reset.py && python main.py"]