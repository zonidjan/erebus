#!/bin/bash

cd /home/jrunyon/erebus
exec &>nohup.out

if ! kill -0 "$(cat pidfile)"; then
	nohup ./run.sh &
fi
