#!/usr/bin/env bash
# wired dotfiles installer (Debian testing/sid).
# Every package is checked with apt first: available ones get installed,
# missing ones are listed at the end instead of breaking the install.
set -e
cd "$(dirname "$0")"

PKGS=(
  # core
  i3 polybar rofi dunst picom feh xss-lock i3lock lxpolkit network-manager-applet
  x11-utils x11-xserver-utils xinput xdotool xclip maim libnotify-bin libxss1 dbus-x11
  # audio / media / hardware
  pulseaudio-utils pavucontrol playerctl brightnessctl bluez blueman
  # python bits used by the popups, OSD, tiling and theme generator
  python3 python3-gi python3-gi-cairo gir1.2-gtk-3.0 python3-i3ipc python3-pil libglib2.0-bin
  # apps
  alacritty copyq fastfetch cava btop arandr dolphin gwenview okular mpv
  # theming
  gnome-themes-extra papirus-icon-theme xdg-desktop-portal-gtk plasma-integration breeze
  fonts-noto-color-emoji curl
)

echo ">> checking packages"
ok=(); missing=()
for p in "${PKGS[@]}"; do
  if apt-cache show "$p" >/dev/null 2>&1; then ok+=("$p"); else missing+=("$p"); fi
done
sudo apt install -y --no-install-recommends "${ok[@]}"

echo ">> backing up existing configs"
BK="$HOME/.config/dotfiles-backup-$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BK"
for d in config/*; do
  n=$(basename "$d"); [ -e "$HOME/.config/$n" ] && cp -r "$HOME/.config/$n" "$BK/" || true
done
echo "   saved to $BK"

echo ">> installing configs"
mkdir -p "$HOME/.config"
cp -r config/. "$HOME/.config/"
chmod +x "$HOME"/.config/i3/scripts/* "$HOME"/.config/polybar/*.sh "$HOME"/.config/polybar/scripts/* \
         "$HOME"/.config/dunst/sound.sh "$HOME"/.config/fastfetch/wired-fetch

echo ">> fonts (JetBrainsMono Nerd Font + Symbols Nerd Font)"
F="$HOME/.local/share/fonts"; mkdir -p "$F"; tmp=$(mktemp -d)
for z in JetBrainsMono NerdFontsSymbolsOnly; do
  curl -fsSL "https://github.com/ryanoasis/nerd-fonts/releases/latest/download/$z.tar.xz" -o "$tmp/$z.tar.xz" \
    && tar xf "$tmp/$z.tar.xz" -C "$F" --wildcards '*.ttf' || echo "   !! could not download $z"
done
fc-cache -f >/dev/null

echo ">> cursor (Bibata Original Classic)"
I="$HOME/.local/share/icons"; mkdir -p "$I"
curl -fsSL "https://github.com/ful1e5/Bibata_Cursor/releases/latest/download/Bibata-Original-Classic.tar.xz" \
  | tar xJ -C "$I" || echo "   !! could not download the cursor theme"

echo ">> generating colors from the wallpaper"
python3 "$HOME/.config/i3/scripts/theme.py" --force >/dev/null || true

if [ "$1" = "--lock-color" ]; then
  echo ">> building i3lock-color"
  "$HOME/.config/i3/scripts/install-i3lock-color.sh"
fi

echo
echo ">> done. Log out and pick i3 on the login screen."
echo "   Optional: ./install.sh --lock-color  builds i3lock-color for the themed lock screen."
echo "   Optional: add  export QT_QPA_PLATFORMTHEME=kde  to ~/.xsessionrc for dark KDE/Qt apps."
if [ ${#missing[@]} -gt 0 ]; then
  echo
  echo "!! not found in your apt sources (install them another way or skip):"
  printf '   %s\n' "${missing[@]}"
fi
