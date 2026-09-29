#!/usr/bin/env python3
# Notification center: Do Not Disturb switch + history (click = show again, × = remove)
import html, json, os, re, subprocess, time, gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango

try: C = json.load(open(os.path.expanduser("~/.config/i3/colors.json")))
except Exception: C = {"bg": "#1a1b26", "bg_alt": "#1f2233", "fg": "#c0caf5", "dim": "#565f89", "accent": "#7aa2f7", "inactive": "#2f334d"}
CSS = f"""
window {{ background: {C['bg']}; border: 2px solid {C['accent']}; }}
label {{ color: {C['fg']}; font: 10pt "JetBrainsMono Nerd Font"; }}
.title {{ font-size: 12pt; color: {C['accent']}; }}
.dim {{ color: {C['dim']}; font-size: 9pt; }}
.summary {{ font-weight: bold; }}
.item {{ background: {C.get('bg_alt', C['bg'])}; padding: 8px 10px; }}
.item:hover {{ background: {C['inactive']}; }}
button {{ background: transparent; border: none; box-shadow: none; color: {C['dim']}; padding: 0 6px; min-height: 0; }}
button:hover {{ color: {C['accent']}; }}
button label {{ color: inherit; }}
switch {{ background: {C['inactive']}; border: none; border-radius: 0; min-height: 18px; }}
switch:checked {{ background: {C['accent']}; }}
switch slider {{ background: {C['fg']}; border: none; border-radius: 0; min-width: 16px; min-height: 16px; }}
scrolledwindow, viewport {{ background: transparent; border: none; }}
""".encode()

def dctl(*a):
    return subprocess.run(["dunstctl", *a], capture_output=True, text=True).stdout.strip()

def history():
    try: data = json.loads(dctl("history"))["data"][0]
    except Exception: return []
    out = []
    for n in data:
        g = lambda k: n.get(k, {}).get("data", "")
        out.append({"id": g("id"), "app": g("appname"), "summary": g("summary"),
                    "body": html.unescape(re.sub(r"<[^>]+>", "", str(g("body")))), "ts": g("timestamp")})
    return out

def ago(ts):
    try: s = time.monotonic() - int(ts) / 1e6
    except Exception: return ""
    if s < 60: return "now"
    if s < 3600: return f"{int(s // 60)}m ago"
    if s < 86400: return f"{int(s // 3600)}h ago"
    return f"{int(s // 86400)}d ago"

prov = Gtk.CssProvider(); prov.load_from_data(CSS)
Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), prov, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

win = Gtk.Window(title="notif-popup"); win.set_wmclass("notif-popup", "notif-popup")
win.set_decorated(False); win.set_default_size(380, -1); win.set_type_hint(Gdk.WindowTypeHint.DIALOG)
outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
for m in ("top", "bottom", "start", "end"): getattr(outer, f"set_margin_{m}")(14)
win.add(outer)

head = Gtk.Box(spacing=8)
t = Gtk.Label(label="Notifications", xalign=0); t.get_style_context().add_class("title")
clear = Gtk.Button(label="Clear all")
head.pack_start(t, True, True, 0); head.pack_end(clear, False, False, 0)
outer.pack_start(head, False, False, 0)

dnd_row = Gtk.Box(spacing=8)
dnd_row.pack_start(Gtk.Label(label="Do not disturb", xalign=0), True, True, 0)
sw = Gtk.Switch(); sw.set_active(dctl("is-paused") == "true")
sw.connect("notify::active", lambda s, _p: dctl("set-paused", "true" if s.get_active() else "false"))
dnd_row.pack_end(sw, False, False, 0)
outer.pack_start(dnd_row, False, False, 0)

scroll = Gtk.ScrolledWindow(); scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
scroll.set_propagate_natural_height(True); scroll.set_max_content_height(460)
lst = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
scroll.add(lst); outer.pack_start(scroll, True, True, 0)

def reshow(nid):
    dctl("history-pop", str(nid)); Gtk.main_quit()

def remove(nid, row):
    dctl("history-rm", str(nid)); lst.remove(row); fill_empty()

def fill_empty():
    if not lst.get_children():
        e = Gtk.Label(label="No notifications", xalign=0.5); e.get_style_context().add_class("dim")
        e.set_margin_top(12); e.set_margin_bottom(12); lst.pack_start(e, False, False, 0); e.show()

def build():
    for ch in lst.get_children(): lst.remove(ch)
    for n in history():
        ev = Gtk.EventBox(); ev.get_style_context().add_class("item")
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        top = Gtk.Box(spacing=6)
        meta = Gtk.Label(label=f"{n['app']} · {ago(n['ts'])}", xalign=0); meta.get_style_context().add_class("dim")
        x = Gtk.Button(label="×")
        top.pack_start(meta, True, True, 0); top.pack_end(x, False, False, 0)
        box.pack_start(top, False, False, 0)
        s = Gtk.Label(label=n["summary"], xalign=0); s.get_style_context().add_class("summary")
        s.set_line_wrap(True); s.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR); s.set_max_width_chars(40)
        box.pack_start(s, False, False, 0)
        if n["body"]:
            b = Gtk.Label(label=n["body"], xalign=0); b.set_line_wrap(True)
            b.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR); b.set_max_width_chars(40); b.set_lines(3)
            b.set_ellipsize(Pango.EllipsizeMode.END)
            box.pack_start(b, False, False, 0)
        ev.add(box)
        ev.connect("button-press-event", lambda _w, e, i=n["id"]: reshow(i) if e.button == 1 else None)
        x.connect("clicked", lambda _b, i=n["id"], r=ev: remove(i, r))
        lst.pack_start(ev, False, False, 0)
    fill_empty(); lst.show_all()

clear.connect("clicked", lambda *_: (dctl("history-clear"), build()))
build()

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
