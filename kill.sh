#!/bin/bash

cd "$(dirname $(readlink -f $0))"

kill "$(cat pidfile)"
