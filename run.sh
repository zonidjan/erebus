#!/bin/sh

python -B "$(dirname $(readlink -f $0))/erebus.py"
