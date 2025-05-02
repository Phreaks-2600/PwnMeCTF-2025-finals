#!/bin/bash

# Start netcat listener that runs test script on connect
while true; do
  nc -lvkp 1337 -e ./run_tests.sh
done
