#!/bin/sh
pkill -f 'i3/scripts/idle.py'
exec python3 ~/.config/i3/scripts/idle.py
