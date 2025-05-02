FROM python:3.9-slim

RUN apt-get update && apt-get install -y curl
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
RUN apt-get install -y nodejs
RUN apt-get clean

WORKDIR /app

COPY flask-app/requirements.txt .
COPY flask-app/app.py .
COPY flask-app/templates/ ./templates/

RUN pip install --no-cache-dir -r requirements.txt

COPY node-server/server.js .

RUN npm init -y && npm install express

COPY start.sh . 
RUN chmod +x start.sh

EXPOSE 1337
CMD ["./start.sh"]