#!/bin/bash

if [ -f "src/admin_data_uploaded/bf8fdd545086e4e7.json" ]; then
    echo "DROP_FILENAME=src/admin_data_uploaded/$(openssl rand -hex 8).json" > .env
    export $(cat .env | xargs)
    mv src/admin_data_uploaded/bf8fdd545086e4e7.json $DROP_FILENAME
else
    export $(cat .env | xargs)
fi

if [ -f "instance/database.db" ];then rm instance/database.db; fi # reset DB

exec python -u main.py
