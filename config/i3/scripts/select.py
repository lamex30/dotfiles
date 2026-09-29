#!/usr/bin/env python3
# Region screenshot: freezes the screen, dims everything outside the selection.
# Usage: select.py OUTPUT.png   (exit 1 if cancelled with Esc / right click)
import json, os, sys, gi
gi.require_version("Gtk", "3.0"); gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk
import cairo

OUT = sys.argv[1]
try: ACC = json.load(open(os.path.expanduser("~/.config/i3/colors.json")))["accent"]
except Exception: ACC = "#7aa2f7"
acc = Gdk.RGBA(); acc.parse(ACC)

root = Gdk.get_default_root_window()
W, H = root.get_width(), root.get_height()
pix = Gdk.pixbuf_get_from_window(root, 0, 0, W, H)
surf = Gdk.cairo_surface_create_from_pixbuf(pix, 1, None)
sel = {"x0": 0, "y0": 0, "x1": 0, "y1": 0, "drag": False}
result = {"ok": False}

def rect():
    x, y = min(sel["x0"], sel["x1"]), min(sel["y0"], sel["y1"])
    return int(x), int(y), int(abs(sel["x1"] - sel["x0"])), int(abs(sel["y1"] - sel["y0"]))

def draw(_w, cr):
    cr.set_source_surface(surf, 0, 0); cr.paint()
    x, y, w, h = rect()
    cr.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    cr.rectangle(0, 0, W, H)
    if w and h: cr.rectangle(x, y, w, h)
    cr.set_source_rgba(0, 0, 0, 0.40); cr.fill()
    if w and h:
        cr.set_source_rgba(acc.red, acc.green, acc.blue, 1); cr.set_line_width(1)
        cr.rectangle(x + .5, y + .5, w - 1, h - 1); cr.stroke()

def press(_w, e):
    if e.button != 1: quit_(False); return
    sel.update(x0=e.x, y0=e.y, x1=e.x, y1=e.y, drag=True)

def motion(_w, e):
    if sel["drag"]: sel.update(x1=e.x, y1=e.y); win.queue_draw()

def release(_w, e):
    if e.button != 1 or not sel["drag"]: return
    sel["drag"] = False
    x, y, w, h = rect()
    if w < 3 or h < 3: sel.update(x0=0, y0=0, x1=0, y1=0); win.queue_draw(); return
    pix.new_subpixbuf(x, y, w, h).savev(OUT, "png", [], [])
    quit_(True)

def quit_(ok):
    result["ok"] = ok
    Gdk.Display.get_default().get_default_seat().ungrab()
    Gtk.main_quit()

win = Gtk.Window(type=Gtk.WindowType.POPUP)
win.set_app_paintable(True); win.move(0, 0); win.resize(W, H)
win.add_events(Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.BUTTON_RELEASE_MASK |
               Gdk.EventMask.POINTER_MOTION_MASK | Gdk.EventMask.KEY_PRESS_MASK)
win.connect("draw", draw); win.connect("button-press-event", press)
win.connect("button-release-event", release); win.connect("motion-notify-event", motion)
win.connect("key-press-event", lambda w, e: quit_(False) if e.keyval == Gdk.KEY_Escape else None)
win.show_all()
gw = win.get_window()
gw.set_cursor(Gdk.Cursor.new_from_name(gw.get_display(), "crosshair"))
from gi.repository import GLib
tries = {"n": 0}
def grab():
    # the window must be mapped before X lets us grab the keyboard -> retry until it works
    st = Gdk.Display.get_default().get_default_seat().grab(gw, Gdk.SeatCapabilities.ALL, False, None, None, None, None)
    tries["n"] += 1
    return st != Gdk.GrabStatus.SUCCESS and tries["n"] < 50
GLib.timeout_add(20, grab)
Gtk.main()
sys.exit(0 if result["ok"] else 1)
