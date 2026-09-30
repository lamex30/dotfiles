#!/usr/bin/env python3
# Тайлинг как dwindle в Hyprland: новое окно делит фокусное окно
# по длинной стороне (широкое -> рядом, высокое -> снизу).
import i3ipc

def on_focus(i3, e):
    con = i3.get_tree().find_focused()
    if not con or con.type != "con" or con.floating in ("user_on", "auto_on"):
        return
    if con.fullscreen_mode or con.parent.layout in ("tabbed", "stacked"):
        return
    want = "splitv" if con.rect.height > con.rect.width else "splith"
    if con.parent.layout != want:
        i3.command(want)

i3 = i3ipc.Connection()
i3.on("window::focus", on_focus)
i3.on("window::new", on_focus)
i3.main()
