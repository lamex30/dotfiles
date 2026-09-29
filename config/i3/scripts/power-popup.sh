#!/bin/sh
if pgrep -f 'i3/scripts/power-popup.py' >/dev/null; then pkill -f 'i3/scripts/power-popup.py'
else exec python3 ~/.config/i3/scripts/power-popup.py; fi
