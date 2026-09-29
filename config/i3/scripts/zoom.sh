#!/bin/sh
# zoom.sh start | in | out | reset
FIFO="${XDG_RUNTIME_DIR:-/tmp}/zoom.fifo"
case "$1" in
  start) pkill -f 'i3/scripts/zoom.py'
         o=$(xrandr --query | awk '/ connected/{print $1; exit}'); xrandr --output "$o" --transform none 2>/dev/null
         exec python3 ~/.config/i3/scripts/zoom.py ;;
  reset) if pgrep -f 'i3/scripts/zoom.py' >/dev/null; then echo reset | timeout 0.3 tee "$FIFO" >/dev/null
         else o=$(xrandr --query | awk '/ connected/{print $1; exit}'); xrandr --output "$o" --transform none; fi ;;
  *) [ -p "$FIFO" ] && echo "$1" | timeout 0.3 tee "$FIFO" >/dev/null ;;
esac
