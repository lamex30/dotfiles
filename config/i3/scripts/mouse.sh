#!/bin/sh
# No acceleration (flat profile), speed 0 = 1:1 movement. Range -1..1.
SPEED=0
for id in $(xinput list | grep 'slave  pointer' | sed -n 's/.*id=\([0-9]*\).*/\1/p'); do
  props=$(xinput list-props "$id")
  echo "$props" | grep -q 'libinput Accel Speed (' || continue
  n=$(echo "$props" | grep 'libinput Accel Profile Enabled (' | cut -d: -f2 | tr ',' '\n' | wc -l)
  if [ "$n" -ge 3 ]; then xinput set-prop "$id" 'libinput Accel Profile Enabled' 0 1 0
  else xinput set-prop "$id" 'libinput Accel Profile Enabled' 0 1; fi
  xinput set-prop "$id" 'libinput Accel Speed' "$SPEED"
done
