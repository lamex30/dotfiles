#!/bin/sh
# Plays the notification sound, except for apps that already make their own sound.
app=$(printf '%s' "$DUNST_APP_NAME" | tr 'A-Z' 'a-z')
case "$app" in
  *telegram*|*discord*|*vesktop*|*webcord*|*slack*|*element*|*signal*|*whatsapp*|*skype*|*zoom*|*teams*) exit 0 ;;
esac
[ "$(dunstctl is-paused 2>/dev/null)" = "true" ] && exit 0
paplay "$HOME/.config/dunst/wired.wav" >/dev/null 2>&1 &
