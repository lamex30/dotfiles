#!/bin/sh
# bluetooth icon: off / on / connected
if ! bluetoothctl show 2>/dev/null | grep -q "Powered: yes"; then echo "%{F$(python3 -c "import json,os;print(json.load(open(os.path.expanduser('~/.config/i3/colors.json')))['dim'])" 2>/dev/null || echo '#808080')}%{T3}󰂲%{T-}%{F-}"; exit; fi
for m in $( (bluetoothctl devices Connected 2>/dev/null || true) | awk '/^Device/{print $2}'); do echo "%{T3}󰂱%{T-}"; exit; done
echo "%{T3}󰂯%{T-}"
