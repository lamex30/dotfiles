#!/bin/sh
# lock + turn the screen off
loginctl lock-session
sleep 1
xset dpms force off
