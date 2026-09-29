#!/bin/sh
# Clipboard history popup at the mouse cursor (rofi + CopyQ)
list=$(copyq eval -- '
for (var i = 0; i < size() && i < 30; ++i) {
  var t = str(read(i)).replace(/\s+/g, " ").trim();
  if (!t) t = "[image]";
  if (t.length > 48) t = t.substring(0, 47) + "…";
  print(i + "\t" + t + "\n");
}')
[ -z "$list" ] && exit 0
sel=$(printf '%s' "$list" | rofi -dmenu -i -monitor -3 -theme ~/.config/rofi/clip.rasi \
      -display-columns 2 -display-column-separator '\t' -no-custom \
      -hover-select -me-select-entry '' -me-accept-entry MousePrimary) || exit 0
copyq select "$(printf '%s' "$sel" | cut -f1)"
