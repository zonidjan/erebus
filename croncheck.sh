#!/bin/bash
exec &>/dev/null

cd /home/jrunyon/erebus

if ! kill -0 "$(cat pidfile)"; then
	nohup ./run.sh >nohup.out &
fi
