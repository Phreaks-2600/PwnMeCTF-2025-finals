FROM python:3.9-slim

WORKDIR /app

RUN mkdir -p /shared/uploads && mkdir -p /shared/sqlite

COPY shared_db.sqlite /shared/sqlite/shared_db.sqlite

COPY entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY . .

CMD ["bash", "/entrypoint.sh"]