#!/usr/bin/env python3
# Bluetooth popup: power switch, paired devices (click = connect/disconnect, battery if known),
# "Add device…" opens blueman-manager for pairing.
import json, os, re, subprocess, threading, gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib

try: C = json.load(open(os.path.expanduser("~/.config/i3/colors.json")))
except Exception: C = {"bg": "#1a1b26", "bg_alt": "#1f2233", "fg": "#c0caf5", "dim": "#565f89", "accent": "#7aa2f7", "inactive": "#2f334d"}
CSS = f"""
window {{ background: {C['bg']}; border: 2px solid {C['accent']}; }}
label {{ color: {C['fg']}; font: 10pt "JetBrainsMono Nerd Font"; }}
.title {{ font-size: 12pt; color: {C['accent']}; }}
.dim {{ color: {C['dim']}; font-size: 9pt; }}
.on {{ color: {C['accent']}; }}
.item {{ background: {C.get('bg_alt', C['bg'])}; padding: 8px 10px; }}
.item:hover {{ background: {C['inactive']}; }}
button {{ background: transparent; border: none; box-shadow: none; padding: 4px 6px; }}
button label {{ color: {C['dim']}; }}
button:hover label {{ color: {C['accent']}; }}
switch {{ background: {C['inactive']}; border: none; border-radius: 0; min-height: 18px; }}
switch:checked {{ background: {C['accent']}; }}
switch slider {{ background: {C['fg']}; border: none; border-radius: 0; min-width: 16px; min-height: 16px; }}
""".encode()

def bt(*a, timeout=8):
    try: return subprocess.run(["bluetoothctl", *a], capture_output=True, text=True, timeout=timeout).stdout
    except Exception: return ""

def powered(): return "Powered: yes" in bt("show")

def devices():
    out = bt("devices", "Paired")
    if "Device" not in out: out = bt("paired-devices")
    res = []
    for mac, name in re.findall(r"^Device (\S+) (.+)$", out, re.M):
        info = bt("info", mac)
        m = re.search(r"Battery Percentage: \S+ \((\d+)\)", info)
        res.append({"mac": mac, "name": name, "connected": "Connected: yes" in info, "battery": m.group(1) if m else None})
    return sorted(res, key=lambda d: not d["connected"])

prov = Gtk.CssProvider(); prov.load_from_data(CSS)
Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), prov, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

win = Gtk.Window(title="bt-popup"); win.set_wmclass("bt-popup", "bt-popup")
win.set_decorated(False); win.set_default_size(320, -1); win.set_type_hint(Gdk.WindowTypeHint.DIALOG)
outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
for m in ("top", "bottom", "start", "end"): getattr(outer, f"set_margin_{m}")(14)
win.add(outer)

head = Gtk.Box(spacing=8)
t = Gtk.Label(label="Bluetooth", xalign=0); t.get_style_context().add_class("title")
sw = Gtk.Switch(); sw.set_valign(Gtk.Align.CENTER)
head.pack_start(t, True, True, 0); head.pack_end(sw, False, False, 0)
outer.pack_start(head, False, False, 0)
lst = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
outer.pack_start(lst, False, False, 0)
add = Gtk.Button(label="Add device…"); add.set_halign(Gtk.Align.START)
add.connect("clicked", lambda *_: (subprocess.Popen(["blueman-manager"]), Gtk.main_quit()))
outer.pack_start(add, False, False, 0)

busy = {"sw": False}
def run_bg(fn):
    threading.Thread(target=lambda: (fn(), GLib.idle_add(refresh)), daemon=True).start()

def toggle(dev):
    def job():
        bt("disconnect" if dev["connected"] else "connect", dev["mac"], timeout=20)
    for ch in lst.get_children(): ch.set_sensitive(False)
    run_bg(job)

def refresh():
    p = powered()
    busy["sw"] = True; sw.set_active(p); busy["sw"] = False
    for ch in lst.get_children(): lst.remove(ch)
    if not p:
        l = Gtk.Label(label="Bluetooth is off", xalign=0); l.get_style_context().add_class("dim"); lst.pack_start(l, False, False, 0)
    else:
        devs = devices()
        if not devs:
            l = Gtk.Label(label="No paired devices", xalign=0); l.get_style_context().add_class("dim"); lst.pack_start(l, False, False, 0)
        for dv in devs:
            ev = Gtk.EventBox(); ev.get_style_context().add_class("item")
            row = Gtk.Box(spacing=8)
            n = Gtk.Label(label=dv["name"], xalign=0)
            if dv["connected"]: n.get_style_context().add_class("on")
            st = "connected" if dv["connected"] else "click to connect"
            if dv["battery"]: st += f" · {dv['battery']}%"
            s = Gtk.Label(label=st, xalign=1); s.get_style_context().add_class("dim")
            row.pack_start(n, True, True, 0); row.pack_end(s, False, False, 0)
            ev.add(row); ev.connect("button-press-event", lambda _w, e, d=dv: toggle(d) if e.button == 1 else None)
            lst.pack_start(ev, False, False, 0)
    lst.show_all(); win.resize(320, 1)
    return False

def on_switch(s, _p):
    if busy["sw"]: return
    on = s.get_active()
    run_bg(lambda: (subprocess.run(["rfkill", "unblock", "bluetooth"]) if on else None, bt("power", "on" if on else "off")))
sw.connect("notify::active", on_switch)

refresh()
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
