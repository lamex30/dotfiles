#!/bin/sh
if pgrep -f 'i3/scripts/wallpicker.py' >/dev/null; then pkill -f 'i3/scripts/wallpicker.py'
else exec python3 ~/.config/i3/scripts/wallpicker.py; fi
