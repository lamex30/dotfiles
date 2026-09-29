#!/bin/sh
pkill -f 'i3/scripts/autotiling.py'
exec python3 ~/.config/i3/scripts/autotiling.py
