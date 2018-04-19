#!/bin/bash

cd "$(dirname $(readlink -f $0))"
exec &>nohup.out

if [ -e dontstart ]; then
	exit 0
fi

if ! kill -0 "$(cat pidfile)"; then
	nohup ./run &
fi
