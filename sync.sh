#!/usr/bin/env bash
# Copies the current rice from ~/.config into this repo (run before committing).
set -e
cd "$(dirname "$0")"
C="$HOME/.config"
cp_f(){ mkdir -p "config/$(dirname "$1")"; cp -p "$C/$1" "config/$1"; }
cd "$C"; files=$(ls i3/scripts/* | grep -v -e '\.bak$' -e 'cleanup-xfce.sh' -e 'tg-test.sh'); cd - >/dev/null
for f in $files; do cp_f "$f"; done
cd "$C"; files=$(ls i3/config i3/colors.conf i3/colors.json i3/wallpaper.* polybar/scripts/* rofi/*.rasi i3/sddm/wired/* i3/sddm/10-wired.conf); cd - >/dev/null
for f in $files polybar/config.ini polybar/colors.ini polybar/launch.sh dunst/dunstrc dunst/sound.sh dunst/wired.wav \
         alacritty/alacritty.toml alacritty/wallpaper.toml fastfetch/wired-fetch fastfetch/config.template.jsonc \
         fastfetch/logo/wired.txt fetch/config cava/config gtk-3.0/settings.ini gtk-4.0/settings.ini \
         fontconfig/conf.d/50-i3-fonts.conf fontconfig/conf.d/60-jetbrains-default.conf \
         xdg-desktop-portal/portals.conf menus/applications.menu; do cp_f "$f"; done
echo "synced. now: git add -A && git commit -m '...' && git push"
