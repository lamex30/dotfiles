#!/bin/sh
# Запуск OSD-демона (перезапускается при каждом рестарте i3)
pkill -f 'i3/scripts/osd.py'
exec python3 ~/.config/i3/scripts/osd.py
