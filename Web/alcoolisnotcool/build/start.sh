#!/bin/bash

echo $FLAG > /app/flag.txt

python app.py &

node server.js &

wait
