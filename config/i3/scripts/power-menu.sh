#!/bin/sh
# Fullscreen power menu (grid): shut down / reboot / sleep / log out
i=$(printf '%b' "<span font_desc='JetBrainsMono Nerd Font 48'>󰐥</span>\nShut down|<span font_desc='JetBrainsMono Nerd Font 48'>󰜉</span>\nReboot|<span font_desc='JetBrainsMono Nerd Font 48'>󰤄</span>\nSleep|<span font_desc='JetBrainsMono Nerd Font 48'>󰍃</span>\nLog out" |
  rofi -dmenu -sep '|' -eh 5 -l 1 -markup-rows -format i -no-custom -theme ~/.config/rofi/power.rasi \
       -hover-select -me-select-entry '' -me-accept-entry MousePrimary) || exit 0
case "$i" in
  0) systemctl poweroff ;;
  1) systemctl reboot ;;
  2) loginctl lock-session; sleep 0.5; systemctl suspend ;;
  3) i3-msg exit ;;
esac
