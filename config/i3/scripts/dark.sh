#!/bin/sh
# Dark theme for everything that follows the system setting (Firefox, Electron, GTK4, Telegram)
gsettings set org.gnome.desktop.interface color-scheme 'prefer-dark'
gsettings set org.gnome.desktop.interface gtk-theme 'Adwaita-dark'
gsettings set org.gnome.desktop.interface icon-theme 'Papirus-Dark-Wall'
gsettings set org.gnome.desktop.interface cursor-theme 'Bibata-Original-Classic'
gsettings set org.gnome.desktop.interface cursor-size 20
gsettings set org.gnome.desktop.interface font-name 'JetBrainsMono Nerd Font 10'
gsettings set org.gnome.desktop.interface document-font-name 'JetBrainsMono Nerd Font 10'
gsettings set org.gnome.desktop.interface monospace-font-name 'JetBrainsMono Nerd Font Mono 10'
