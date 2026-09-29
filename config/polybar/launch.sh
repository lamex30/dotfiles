#!/bin/sh
# (Re)start polybar only when its config actually changed.
# Restarting it recreates the tray, and some apps (OBS) don't come back to a new tray.
STAMP="$HOME/.config/polybar/.launch-stamp"
hash=$(cat "$HOME/.config/polybar/config.ini" "$HOME/.config/polybar/colors.ini" 2>/dev/null | md5sum | cut -d' ' -f1)
if pgrep -u "$(id -u)" -x polybar >/dev/null && [ "$(cat "$STAMP" 2>/dev/null)" = "$hash" ]; then
  exit 0
fi
pkill -x polybar
while pgrep -u "$(id -u)" -x polybar >/dev/null; do sleep 0.2; done
BAT=$(ls /sys/class/power_supply | grep -m1 '^BAT')
ADP=$(ls /sys/class/power_supply | grep -m1 -E '^(AC|ADP|ACAD)')
[ -n "$BAT" ] && export BAT
[ -n "$ADP" ] && export ADP
BACKLIGHT=$( (ls /sys/class/backlight | grep -v "^acpi_video"; ls /sys/class/backlight) 2>/dev/null | head -1)
[ -n "$BACKLIGHT" ] && export BACKLIGHT
echo "$hash" > "$STAMP"
polybar main >"$HOME/.config/polybar/polybar.log" 2>&1 &
