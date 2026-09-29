#!/bin/sh
# restart.sh NAME [CMD...] - kill a running process by name and start it again
name=$1; shift
pkill -x "$name"
[ $# -gt 0 ] && exec "$@" || exec "$name"
