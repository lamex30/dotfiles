#!/bin/sh
# CopyQ: запуск + настройки меню как у Klipper (Meta+V -> меню у курсора)
copyq --start-server >/dev/null 2>&1 &
for i in 1 2 3 4 5 6 7 8 9 10; do copyq version >/dev/null 2>&1 && break; sleep 0.5; done
copyq config tray_items 15 >/dev/null
copyq config tray_item_paste false >/dev/null
copyq config tray_commands false >/dev/null
