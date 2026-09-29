#!/bin/sh
pkill -f "i3/scripts/bar-sidebuttons.py"
exec python3 ~/.config/i3/scripts/bar-sidebuttons.py
