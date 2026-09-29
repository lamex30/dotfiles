#!/bin/sh
# Lock screen: blurred wallpaper + ring in the system colors, layout below.
# Type the password and press Enter.
eval "$(python3 - <<'PY'
import json, os
try: c = json.load(open(os.path.expanduser("~/.config/i3/colors.json")))
except Exception: c = {"bg": "#141414", "fg": "#e0e0e0", "accent": "#db8095", "accent2": "#e0a390", "urgent": "#ef6c7c", "dim": "#808080"}
for k, v in c.items(): print(f'{k.upper()}={v.lstrip("#")}')
PY
)"
IMG="$HOME/.config/i3/lock.png"
IMGARG=""; [ -f "$IMG" ] && IMGARG="-i $IMG"
F="JetBrainsMono Nerd Font"

if [ -x /usr/local/bin/i3lock ]; then
  exec /usr/local/bin/i3lock -n -e -f -c "$BG" $IMGARG \
    --indicator --radius 110 --ring-width 7 \
    --inside-color="${BG}cc" --ring-color="${ACCENT}ff" --line-uses-inside \
    --separator-color=00000000 --keyhl-color="${FG}ff" --bshl-color="${URGENT}ff" \
    --insidever-color="${BG}cc" --ringver-color="${ACCENT2}ff" \
    --insidewrong-color="${BG}cc" --ringwrong-color="${URGENT}ff" \
    --time-str="" --date-str="" --time-color=00000000 --date-color=00000000 \
    --verif-text="…" --wrong-text="nope" --noinput-text="empty" \
    --verif-color="${FG}ff" --wrong-color="${URGENT}ff" --verif-font="$F" --wrong-font="$F" \
    --keylayout 0 --layout-color="${FG}ff" --layout-font="$F" --layout-size=16 \
    --layout-pos="ix:iy+150"
else
  exec i3lock -n -e -f -c "$BG" $IMGARG
fi
