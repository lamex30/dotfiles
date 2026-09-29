#!/bin/sh
# bell; crossed bell + number of held notifications when Do Not Disturb is on
if [ "$(dunstctl is-paused 2>/dev/null)" = "true" ]; then
  n=$(dunstctl count waiting 2>/dev/null); [ "${n:-0}" -gt 0 ] && echo "󰂛 $n" || echo "󰂛"
else echo "󰂚"; fi
