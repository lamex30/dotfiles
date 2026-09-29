#!/bin/sh
THEME=Bibata-Original-Classic
mkdir -p "$HOME/.icons"
[ -e "$HOME/.icons/$THEME" ] || ln -s "$HOME/.local/share/icons/$THEME" "$HOME/.icons/$THEME"
if [ ! -e "$HOME/.icons/default" ]; then
  mkdir -p "$HOME/.icons/default"
  printf '[Icon Theme]\nInherits=%s\n' "$THEME" > "$HOME/.icons/default/index.theme"
fi
printf 'Xcursor.theme: %s\nXcursor.size: 20\n' "$THEME" | xrdb -merge
xsetroot -cursor_name left_ptr
# panel icon font
if [ ! -f "$HOME/.local/share/fonts/SymbolsNerdFontMono-Regular.ttf" ]; then
  mkdir -p "$HOME/.local/share/fonts"
  cp "$HOME/.config/i3/fonts/SymbolsNerdFontMono-Regular.ttf" "$HOME/.local/share/fonts/"
  fc-cache -f "$HOME/.local/share/fonts" "$HOME/.config/i3/fonts" && ~/.config/polybar/launch.sh
fi
