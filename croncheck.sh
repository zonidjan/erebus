#!/bin/bash

cd "$(dirname $(readlink -f $0))"
exec &>nohup.out

if ! kill -0 "$(cat pidfile)"; then
	nohup ./run.sh &
fi
