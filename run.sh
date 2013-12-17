#!/bin/sh

# Erebus IRC bot - Author: John Runyon
# Startup script

python -B "$(dirname $(readlink -f $0))/erebus.py"
