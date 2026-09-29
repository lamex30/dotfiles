#!/bin/sh
pkill -f "i3/scripts/clock-hover.py"
exec python3 ~/.config/i3/scripts/clock-hover.py
