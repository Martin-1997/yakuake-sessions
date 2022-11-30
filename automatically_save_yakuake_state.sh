#!/bin/bash

filename="yakuake_state.txt"
sleep_time=5

while true
do
    python ysess.py -o $filename --force-overwrite
    sleep $sleep_time
done