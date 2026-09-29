#!/bin/sh
# Turn the screen off WITHOUT locking.
# X treats "screen forced off" as "screensaver started", and xss-lock would lock on that,
# so xss-lock is paused while the screen is off and started again once it is back on.
pkill -x xss-lock
sleep 0.3
xset dpms force off
sleep 1
while xset q | grep -qE 'Monitor is (Off|in Standby|in Suspend)'; do sleep 0.5; done
sleep 1
setsid -f xss-lock --transfer-sleep-lock -- "$HOME/.config/i3/scripts/lock.sh" >/dev/null 2>&1
