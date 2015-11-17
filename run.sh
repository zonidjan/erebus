#!/bin/sh

# Erebus IRC bot - Author: John Runyon
# Startup script

cd "$(dirname $(readlink -f $0))"
PYTHONPATH=".:$PYTHONPATH" python -O -B erebus.py
