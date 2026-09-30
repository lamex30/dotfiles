#!/bin/sh
LOG="$HOME/.config/i3/autostart.log"
exec >"$LOG" 2>&1
echo "== $(date '+%T') autostart begins"
# Session services first: give D-Bus/systemd services (portals) our DISPLAY etc.,
# otherwise flatpak apps wait for a portal that can't start.
dbus-update-activation-environment --systemd DISPLAY XAUTHORITY XDG_CURRENT_DESKTOP XDG_SESSION_TYPE QT_QPA_PLATFORMTHEME PATH 2>/dev/null

# Bridge for apps that use the modern tray protocol (StatusNotifierItem) into the panel tray
command -v snixembed >/dev/null && { pkill -x snixembed; snixembed --fork 2>/dev/null || (snixembed &); }

# tray apps: small delay so the panel tray exists and they can minimise into it
echo "-- $(date '+%T') before apps:"; pgrep -a -f 'obs|telegram|Throne' | grep -v pgrep
systemctl --user --no-pager list-units --all 2>/dev/null | grep -iE 'autostart|portal' 
sleep 3
echo "-- $(date '+%T') starting apps"
flatpak run org.telegram.desktop -startintray &
/opt/Throne/Throne -tray -appdata &
sleep 1
# OBS: without the KDE platform theme Qt uses the classic tray icon that polybar shows
env -u QT_QPA_PLATFORMTHEME obs --minimize-to-tray --startreplaybuffer &
~/.local/bin/default-volume &
( sleep 30; echo "-- $(date '+%T') +30s:"; pgrep -a -f 'obs|telegram|Throne|portal' | grep -v pgrep ) &
wait
