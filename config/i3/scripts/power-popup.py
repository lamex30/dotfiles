#!/usr/bin/env python3
# Popup: battery status + brightness slider. Opens at the mouse, closes on
# focus loss / Esc / second click on the panel widget.
import glob, json, os, subprocess, gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib

try: C = json.load(open(os.path.expanduser("~/.config/i3/colors.json")))
except Exception: C = {"bg": "#1a1b26", "fg": "#c0caf5", "dim": "#565f89", "accent": "#7aa2f7", "inactive": "#2f334d"}

CSS = f"""
window {{ background: {C['bg']}; border: 2px solid {C['accent']}; }}
label {{ color: {C['fg']}; font: 11pt "JetBrainsMono Nerd Font"; }}
.dim {{ color: {C['dim']}; font-size: 10pt; }}
.big {{ font-size: 20pt; color: {C['accent']}; }}
scale trough {{ background: {C['inactive']}; min-height: 6px; border: none; border-radius: 0; }}
scale highlight {{ background: {C['accent']}; border: none; border-radius: 0; }}
scale slider {{ background: {C['fg']}; min-width: 14px; min-height: 14px; border: none; border-radius: 0; margin: -5px 0; }}
""".encode()

def read(p, d=""):
    try: return open(p).read().strip()
    except Exception: return d

def battery():
    bats = sorted(glob.glob("/sys/class/power_supply/BAT*"))
    if not bats: return None
    b = bats[0]
    cap, status = read(f"{b}/capacity", "?"), read(f"{b}/status", "Unknown")
    now = read(f"{b}/energy_now") or read(f"{b}/charge_now")
    full = read(f"{b}/energy_full") or read(f"{b}/charge_full")
    rate = read(f"{b}/power_now") or read(f"{b}/current_now")
    eta = ""
    try:
        now, full, rate = float(now), float(full), float(rate)
        if rate > 0:
            h = (now / rate) if status == "Discharging" else ((full - now) / rate) if status == "Charging" else 0
            if h: eta = f"{int(h)}h {int(h * 60 % 60):02d}m " + ("left" if status == "Discharging" else "to full")
    except Exception: pass
    return cap, status, eta

_bl = sorted(glob.glob("/sys/class/backlight/*"), key=lambda d: os.path.basename(d).startswith("acpi_video"))
BL = (_bl or [None])[0]
def bright():
    # same math as the polybar widget: actual_brightness / max_brightness, rounded
    try:
        return round(int(read(f"{BL}/actual_brightness")) * 100 / int(read(f"{BL}/max_brightness")))
    except Exception: return 50

prov = Gtk.CssProvider(); prov.load_from_data(CSS)
Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), prov, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

win = Gtk.Window(title="power-popup")
win.set_wmclass("power-popup", "power-popup")
win.set_decorated(False); win.set_default_size(300, -1)
win.set_type_hint(Gdk.WindowTypeHint.DIALOG)
box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
for m in ("top", "bottom", "start", "end"): getattr(box, f"set_margin_{m}")(16)
win.add(box)

bat = battery()
if bat:
    cap, status, eta = bat
    big = Gtk.Label(label=f"{cap}%", xalign=0); big.get_style_context().add_class("big")
    st = Gtk.Label(label=status + (f" · {eta}" if eta else ""), xalign=0); st.get_style_context().add_class("dim")
    box.pack_start(big, False, False, 0); box.pack_start(st, False, False, 0)
    box.pack_start(Gtk.Separator(), False, False, 6)

bl = Gtk.Label(label="Brightness", xalign=0)
val = Gtk.Label(xalign=1); val.get_style_context().add_class("dim")
row = Gtk.Box(spacing=6); row.pack_start(bl, True, True, 0); row.pack_end(val, False, False, 0)
scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 1, 100, 1)
scale.set_draw_value(False); scale.set_value(bright()); val.set_text(f"{int(scale.get_value())}%")
pending = {"id": None}
state = {"ours": False}
def apply():
    try: raw = round(int(scale.get_value()) * int(read(f"{BL}/max_brightness")) / 100)
    except Exception: raw = None
    subprocess.Popen(["brightnessctl", "-q", "-d", os.path.basename(BL or ""), "set", str(raw) if raw else f"{int(scale.get_value())}%"])
    pending["id"] = None
    return False
def changed(s):
    val.set_text(f"{int(s.get_value())}%")
    if state["ours"]: return
    if pending["id"] is None: pending["id"] = GLib.timeout_add(40, apply)
scale.connect("value-changed", changed)
def sync():
    # follow changes made elsewhere (keys, scrolling the widget)
    if pending["id"] is None:
        cur = bright()
        if cur != int(scale.get_value()):
            state["ours"] = True; scale.set_value(cur); state["ours"] = False
    return True
GLib.timeout_add(300, sync)
box.pack_start(row, False, False, 0); box.pack_start(scale, False, False, 0)

win.connect("key-press-event", lambda w, e: Gtk.main_quit() if e.keyval == Gdk.KEY_Escape else None)
win.connect("focus-out-event", lambda *_: GLib.timeout_add(150, Gtk.main_quit))
win.connect("destroy", Gtk.main_quit)
# close when the pointer leaves the popup (after it has been inside once)
_hover = {"in": False, "t": None}
def _enter(_w, e):
    _hover["in"] = True
    if _hover["t"]: GLib.source_remove(_hover["t"]); _hover["t"] = None
def _leave(_w, e):
    if e.detail == Gdk.NotifyType.INFERIOR or e.mode != Gdk.CrossingMode.NORMAL or not _hover["in"]: return
    if not _hover["t"]: _hover["t"] = GLib.timeout_add(350, Gtk.main_quit)
win.add_events(Gdk.EventMask.ENTER_NOTIFY_MASK | Gdk.EventMask.LEAVE_NOTIFY_MASK)
win.connect("enter-notify-event", _enter); win.connect("leave-notify-event", _leave)
win.show_all(); win.present()
Gtk.main()
