#!/bin/sh
# Toggle the audio popup
if pgrep -f 'i3/scripts/volume-popup.py' >/dev/null; then pkill -f 'i3/scripts/volume-popup.py'
else exec python3 ~/.config/i3/scripts/volume-popup.py; fi
