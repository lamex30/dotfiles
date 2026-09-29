#!/bin/sh
# Start the OSD daemon (restarted on every i3 reload)
pkill -f 'i3/scripts/osd.py'
exec python3 ~/.config/i3/scripts/osd.py
