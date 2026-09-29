#!/bin/sh
# Builds i3lock-color (not in Debian repos) and installs it to /usr/local/bin/i3lock.
# The regular Debian i3lock stays installed as a fallback.
set -e
sudo apt install -y git autoconf automake gcc make pkg-config libpam0g-dev libcairo2-dev \
  libfontconfig1-dev libxcb-composite0-dev libev-dev libx11-xcb-dev libxcb-xkb-dev \
  libxcb-xinerama0-dev libxcb-randr0-dev libxcb-image0-dev libxcb-util0-dev libxcb-xrm-dev \
  libxkbcommon-dev libxkbcommon-x11-dev libjpeg-dev libgif-dev
tmp=$(mktemp -d); cd "$tmp"
git clone --depth 1 https://github.com/Raymo111/i3lock-color.git
cd i3lock-color
autoreconf -fiv
mkdir -p build && cd build
../configure --prefix=/usr/local --sysconfdir=/etc --disable-sanitizers
make -j"$(nproc)"
sudo make install
echo ">> i3lock-color installed: $(/usr/local/bin/i3lock --version 2>&1 | head -1)"
