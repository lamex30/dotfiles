#!/bin/sh
dir="$HOME/Pictures/Screenshots"
mkdir -p "$dir"
file="$dir/ps_$(date +%Y%m%d_%H%M%S).png"
case "$1" in
  region) python3 ~/.config/i3/scripts/select.py "$file" || exit 0 ;;
  delay)  sleep 3; maim -u "$file" ;;
  window) maim -u -i "$(xdotool getactivewindow)" "$file" ;;
  *)      maim -u "$file" ;;
esac
xclip -selection clipboard -t image/png -i "$file"
notify-send -i "$file" "Screenshot" "$(basename "$file")"
