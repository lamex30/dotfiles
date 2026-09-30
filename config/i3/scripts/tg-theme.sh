#!/bin/sh
# Opens the generated wallpaper theme in Telegram Desktop (it shows a preview -> "Apply").
T="$HOME/.config/i3/telegram/wired.tdesktop-theme"
[ -f "$T" ] || exit 0
if flatpak info org.telegram.desktop >/dev/null 2>&1; then
  exec flatpak run --file-forwarding org.telegram.desktop -- @@ "$T" @@
elif command -v telegram-desktop >/dev/null; then
  exec telegram-desktop -- "$T"
fi
