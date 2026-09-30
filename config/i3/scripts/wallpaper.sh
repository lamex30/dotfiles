#!/bin/sh
# wallpaper.sh            -> apply current ~/.config/i3/wallpaper.*
# wallpaper.sh /path/img  -> make it the wallpaper and retheme everything
if [ -n "$1" ]; then
  ext="${1##*.}"
  for f in ~/.config/i3/wallpaper.*; do [ -e "$f" ] && mv "$f" "$f.old"; done
  cp "$1" ~/.config/i3/wallpaper."$ext" && rm -f ~/.config/i3/wallpaper.*.old
fi
feh --no-fehbg --bg-fill ~/.config/i3/wallpaper.* 2>/dev/null
if python3 ~/.config/i3/scripts/theme.py >/dev/null; then
  # i3 "reload" re-reads the window border colors but does NOT re-run exec_always,
  # so everything that bakes colors in at start is restarted here explicitly
  i3-msg reload >/dev/null
  dunstctl reload 2>/dev/null
  ~/.config/polybar/launch.sh
  setsid -f ~/.config/i3/scripts/osd.sh >/dev/null 2>&1
  setsid -f ~/.config/i3/scripts/clock-hover.sh >/dev/null 2>&1
  # Telegram picks up the rewritten theme file by itself (after it was applied once via tg-theme.sh)
fi
