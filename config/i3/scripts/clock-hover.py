#!/usr/bin/env python3
# Polybar has no hover events, so this watches the pointer: when it rests on the clock
# widget, a small tooltip with the day of the week appears under it.
# The clock position is computed from the bar layout (it is the second module from the right).
import json, os, subprocess, time, gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango

BAR_H, FONT = 26, "JetBrainsMono Nerd Font 10"
try: C = json.load(open(os.path.expanduser("~/.config/i3/colors.json")))
except Exception: C = {"bg": "#141414", "fg": "#e0e0e0", "accent": "#db8095"}
prov = Gtk.CssProvider(); prov.load_from_data(f"""
window {{ background: {C['bg']}; border: 2px solid {C['accent']}; }}
label {{ color: {C['fg']}; font: 10pt "JetBrainsMono Nerd Font"; padding: 4px 10px; }}
""".encode())
Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), prov, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

ctx = Gtk.Label().get_pango_context()
fd = Pango.FontDescription.from_string(FONT)
def tw(text):
    l = Pango.Layout.new(ctx); l.set_font_description(fd); l.set_text(text, -1)
    return l.get_pixel_size()[0]

def notif_label():
    try:
        out = subprocess.run([os.path.expanduser("~/.config/polybar/scripts/notif.sh")], capture_output=True, text=True, timeout=2).stdout.strip()
        return out or chr(0xF009A)
    except Exception: return chr(0xF009A)

tip = Gtk.Window(type=Gtk.WindowType.POPUP); lbl = Gtk.Label(); tip.add(lbl); lbl.show()
state = {"notif": notif_label(), "t": 0, "shown": False}

def clock_rect():
    mon = Gdk.Display.get_default().get_monitor(0).get_geometry()
    sp = tw(" ")
    date = time.strftime("%d.%m.%y"); full = date + "  " + time.strftime("%I:%M %p")
    right = mon.x + mon.width - 2 * sp - sp - tw(state["notif"]) - sp - tw("|") - sp
    start = right - tw(full)                 # only the date part, not the time
    return start - 3, start + tw(date) + 3, mon

def tick():
    if time.time() - state["t"] > 2: state["notif"] = notif_label(); state["t"] = time.time()
    _, x, y, _ = Gdk.get_default_root_window().get_pointer()
    x0, x1, mon = clock_rect()
    inside = mon.y <= y < mon.y + BAR_H and x0 <= x <= x1
    if inside and not state["shown"]:
        lbl.set_text(time.strftime("%A"))
        tip.resize(1, 1); tip.show()
        w, _h = tip.get_size()
        tip.move(min(max(x - w // 2, mon.x + 4), mon.x + mon.width - w - 4), mon.y + BAR_H + 6)
        state["shown"] = True
    elif not inside and state["shown"]:
        tip.hide(); state["shown"] = False
    return True

GLib.timeout_add(120, tick)
Gtk.main()
