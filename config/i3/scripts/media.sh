#!/bin/sh
# media.sh vol-up|vol-down|vol-up-small|vol-down-small|mute|mic|bri-up|bri-down|bri-up-small|bri-down-small
FIFO="${XDG_RUNTIME_DIR:-/tmp}/osd.fifo"
osd() { [ -p "$FIFO" ] && printf '%s\n' "$1" | timeout 0.3 tee "$FIFO" >/dev/null; }
S=@DEFAULT_SINK@; M=@DEFAULT_SOURCE@
BL=$( (ls /sys/class/backlight | grep -v "^acpi_video"; ls /sys/class/backlight) 2>/dev/null | head -1)
vol() {
  if pactl get-sink-mute $S | grep -q yes; then osd "Muted|0"
  else osd "Volume $(pactl get-sink-volume $S | grep -o '[0-9]*%' | head -1)|$(pactl get-sink-volume $S | grep -o '[0-9]*%' | head -1 | tr -d %)"; fi
}
bri() { p=$(brightnessctl -d "$BL" -m | cut -d, -f4 | tr -d %); osd "Brightness $p%|$p"; }
case "$1" in
  vol-up)         pactl set-sink-mute $S 0; pactl set-sink-volume $S +5%; vol ;;
  vol-down)       pactl set-sink-volume $S -5%; vol ;;
  vol-up-small)   pactl set-sink-mute $S 0; pactl set-sink-volume $S +1%; vol ;;
  vol-down-small) pactl set-sink-volume $S -1%; vol ;;
  scroll-up)      if python3 ~/.config/i3/scripts/shift-held.py; then st=1; else st=5; fi
                  pactl set-sink-mute $S 0; pactl set-sink-volume $S +$st%; vol ;;
  scroll-down)    if python3 ~/.config/i3/scripts/shift-held.py; then st=1; else st=5; fi
                  pactl set-sink-volume $S -$st%; vol ;;
  mute)           pactl set-sink-mute $S toggle; vol ;;
  mic)            pactl set-source-mute $M toggle
                  if pactl get-source-mute $M | grep -q yes; then osd "Mic muted"; else osd "Mic on"; fi ;;
  bri-scroll-up)  if python3 ~/.config/i3/scripts/shift-held.py; then st=1; else st=5; fi
                  brightnessctl -d "$BL" -q set $st%+; bri ;;
  bri-scroll-down) if python3 ~/.config/i3/scripts/shift-held.py; then st=1; else st=5; fi
                  brightnessctl -d "$BL" -q set $st%-; bri ;;
  bri-up)         brightnessctl -d "$BL" -q set 5%+; bri ;;
  bri-down)       brightnessctl -d "$BL" -q set 5%-; bri ;;
  bri-up-small)   brightnessctl -d "$BL" -q set 1%+; bri ;;
  bri-down-small) brightnessctl -d "$BL" -q set 1%-; bri ;;
esac
