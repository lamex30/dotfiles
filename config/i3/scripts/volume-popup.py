#!/usr/bin/env python3
# Audio popup: Output (device picker + volume), Input (device picker + volume), then per-app volumes.
import json, os, subprocess, threading, gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango

try: C = json.load(open(os.path.expanduser("~/.config/i3/colors.json")))
except Exception: C = {"bg": "#1a1b26", "bg_alt": "#1f2233", "fg": "#c0caf5", "dim": "#565f89", "accent": "#7aa2f7", "inactive": "#2f334d"}
CSS = f"""
window {{ background: {C['bg']}; border: 2px solid {C['accent']}; }}
label {{ color: {C['fg']}; font: 10pt "JetBrainsMono Nerd Font"; }}
.title {{ font-size: 11pt; color: {C['accent']}; }}
.dim {{ color: {C['dim']}; font-size: 9pt; }}
.icon {{ font-size: 13pt; }}
.muted {{ color: {C['dim']}; }}
button {{ background: transparent; border: none; box-shadow: none; padding: 2px 4px; min-height: 0; min-width: 0; }}
button:hover {{ background: {C['inactive']}; }}
.device {{ background: {C.get('bg_alt', C['bg'])}; padding: 4px 8px; }}
.device label {{ color: {C['fg']}; }}
.pick {{ padding: 6px 10px; }}
.pick.current label {{ color: {C['accent']}; }}
scale trough {{ background: {C['inactive']}; min-height: 5px; border: none; border-radius: 0; }}
scale highlight {{ background: {C['accent']}; border: none; border-radius: 0; }}
scale slider {{ background: {C['fg']}; min-width: 12px; min-height: 12px; border: none; border-radius: 0; margin: -4px 0; }}
separator {{ background: {C['inactive']}; min-height: 1px; }}
""".encode()
ICON = {"out": chr(0xF057E), "out_m": chr(0xF075F), "in": chr(0xF036C), "in_m": chr(0xF036D), "app": chr(0xF075A)}

def pactl_json(*a):
    try: return json.loads(subprocess.run(["pactl", "-f", "json", *a], capture_output=True, text=True).stdout or "[]")
    except Exception: return []
def pactl(*a): subprocess.Popen(["pactl", *a], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
def default(kind):
    return subprocess.run(["pactl", f"get-default-{kind}"], capture_output=True, text=True).stdout.strip()
def vol(obj):
    try: v = list(obj["volume"].values()); return round(sum(int(x["value_percent"].rstrip("%")) for x in v) / len(v))
    except Exception: return 0

prov = Gtk.CssProvider(); prov.load_from_data(CSS)
Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), prov, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
win = Gtk.Window(title="volume-popup"); win.set_wmclass("volume-popup", "volume-popup")
win.set_decorated(False); win.set_default_size(400, -1); win.set_type_hint(Gdk.WindowTypeHint.DIALOG)
outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
for m in ("top", "bottom", "start", "end"): getattr(outer, f"set_margin_{m}")(14)
win.add(outer)
dragging = set()
open_pickers = set()   # which device lists are expanded (kept across live refreshes)

def slider(value, on_change):
    sc = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
    sc.set_draw_value(False); sc.set_value(min(value, 100)); sc.set_hexpand(True)
    sc.connect("button-press-event", lambda *_: dragging.add(sc))
    sc.connect("button-release-event", lambda *_: dragging.discard(sc))
    pend = {"id": None}
    def fire():
        on_change(int(sc.get_value())); pend["id"] = None; return False
    def changed(_s):
        if pend["id"] is None: pend["id"] = GLib.timeout_add(30, fire)
    sc.connect("value-changed", changed)
    return sc

def device_section(title, kind, items, cur):
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    t = Gtk.Label(label=title, xalign=0); t.get_style_context().add_class("title"); box.pack_start(t, False, False, 0)
    current = next((x for x in items if x["name"] == cur), items[0] if items else None)
    if not current:
        l = Gtk.Label(label="No devices", xalign=0); l.get_style_context().add_class("dim"); box.pack_start(l, False, False, 0)
        return box
    # device picker (click to expand)
    btn = Gtk.Button(); btn.get_style_context().add_class("device")
    bl = Gtk.Label(label=f"{current.get('description', current['name'])}  ▾", xalign=0)
    bl.set_ellipsize(Pango.EllipsizeMode.END); bl.set_max_width_chars(40); btn.add(bl)
    rev = Gtk.Revealer(); rev.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)
    picks = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    for it in items:
        pb = Gtk.Button(); pb.get_style_context().add_class("pick")
        if it["name"] == current["name"]: pb.get_style_context().add_class("current")
        pl = Gtk.Label(label=it.get("description", it["name"]), xalign=0); pl.set_ellipsize(Pango.EllipsizeMode.END)
        pl.set_max_width_chars(42); pb.add(pl)
        pb.connect("clicked", lambda _b, n=it["name"]: (open_pickers.discard(kind), pactl(f"set-default-{kind}", n), GLib.timeout_add(250, rebuild)))
        picks.pack_start(pb, False, False, 0)
    rev.add(picks)
    if kind in open_pickers:
        rev.set_transition_duration(0); rev.set_reveal_child(True); rev.set_transition_duration(250)
    def toggle(*_):
        show = not rev.get_reveal_child()
        (open_pickers.add if show else open_pickers.discard)(kind)
        rev.set_reveal_child(show)
    btn.connect("clicked", toggle)
    box.pack_start(btn, False, False, 0); box.pack_start(rev, False, False, 0)
    # volume row
    row = Gtk.Box(spacing=8)
    muted = current.get("mute", False)
    ic = "out" if kind == "sink" else "in"
    mb = Gtk.Button(label=ICON[ic + "_m"] if muted else ICON[ic])
    mb.get_child().get_style_context().add_class("icon")
    if muted: mb.get_child().get_style_context().add_class("muted")
    pct = Gtk.Label(label=f"{vol(current)}%"); pct.set_width_chars(4); pct.get_style_context().add_class("dim")
    sc = slider(vol(current), lambda v, n=current["name"]: (pactl(f"set-{kind}-volume", n, f"{v}%"), pct.set_text(f"{v}%")))
    mb.connect("clicked", lambda *_: (pactl(f"set-{kind}-mute", current["name"], "toggle"), GLib.timeout_add(150, rebuild)))
    row.pack_start(mb, False, False, 0); row.pack_start(sc, True, True, 0); row.pack_end(pct, False, False, 0)
    box.pack_start(row, False, False, 0)
    return box

def apps_section(inputs):
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    t = Gtk.Label(label="Applications", xalign=0); t.get_style_context().add_class("title"); box.pack_start(t, False, False, 0)
    if not inputs:
        l = Gtk.Label(label="Nothing is playing", xalign=0); l.get_style_context().add_class("dim"); box.pack_start(l, False, False, 0)
    for si in inputs:
        p = si.get("properties", {})
        name = p.get("application.name") or p.get("media.name") or "app"
        media = p.get("media.name", "")
        head = Gtk.Box(spacing=6)
        nl = Gtk.Label(label=name, xalign=0); nl.set_ellipsize(Pango.EllipsizeMode.END)
        head.pack_start(nl, False, False, 0)
        if media and media != name:
            ml = Gtk.Label(label=media, xalign=0); ml.set_ellipsize(Pango.EllipsizeMode.END); ml.get_style_context().add_class("dim")
            head.pack_start(ml, True, True, 0)
        box.pack_start(head, False, False, 0)
        row = Gtk.Box(spacing=8)
        muted = si.get("mute", False)
        mb = Gtk.Button(label=ICON["out_m"] if muted else ICON["app"])
        mb.get_child().get_style_context().add_class("icon")
        if muted: mb.get_child().get_style_context().add_class("muted")
        sid = str(si["index"])
        pct = Gtk.Label(label=f"{vol(si)}%"); pct.set_width_chars(4); pct.get_style_context().add_class("dim")
        sc = slider(vol(si), lambda v, i=sid: (pactl("set-sink-input-volume", i, f"{v}%"), pct.set_text(f"{v}%")))
        mb.connect("clicked", lambda *_, i=sid: (pactl("set-sink-input-mute", i, "toggle"), GLib.timeout_add(150, rebuild)))
        row.pack_start(mb, False, False, 0); row.pack_start(sc, True, True, 0); row.pack_end(pct, False, False, 0)
        box.pack_start(row, False, False, 0)
    return box

def rebuild(force=False):
    if dragging: return False
    for ch in outer.get_children(): outer.remove(ch)
    sinks = pactl_json("list", "sinks")
    sources = [s for s in pactl_json("list", "sources") if not s["name"].endswith(".monitor")]
    inputs = pactl_json("list", "sink-inputs")
    outer.pack_start(device_section("Output", "sink", sinks, default("sink")), False, False, 0)
    outer.pack_start(Gtk.Separator(), False, False, 0)
    outer.pack_start(device_section("Input", "source", sources, default("source")), False, False, 0)
    outer.pack_start(Gtk.Separator(), False, False, 0)
    outer.pack_start(apps_section(inputs), False, False, 0)
    more = Gtk.Button(label="Advanced mixer…"); more.set_halign(Gtk.Align.START)
    more.get_child().get_style_context().add_class("dim")
    more.connect("clicked", lambda *_: (subprocess.Popen(["env", "GTK_THEME=Adwaita:dark", "pavucontrol"]), Gtk.main_quit()))
    outer.pack_start(more, False, False, 0)
    outer.show_all(); win.resize(400, 1)
    return False

# live updates (new streams, device changes, keys) with a small debounce
pending = {"id": None}
def schedule():
    if pending["id"] is None:
        def go():
            pending["id"] = None
            if not open_pickers: rebuild()
            return False
        pending["id"] = GLib.timeout_add(300, go)
    return False
def watch():
    p = subprocess.Popen(["pactl", "subscribe"], stdout=subprocess.PIPE, text=True)
    for line in p.stdout:
        if any(k in line for k in ("sink-input", "'change' on sink", "'change' on source", "'new'", "'remove'", "server")):
            GLib.idle_add(schedule)
threading.Thread(target=watch, daemon=True).start()

rebuild()
_hover = {"in": False, "t": None}
def _enter(_w, e):
    _hover["in"] = True
    if _hover["t"]: GLib.source_remove(_hover["t"]); _hover["t"] = None
def _leave(_w, e):
    if e.detail == Gdk.NotifyType.INFERIOR or e.mode != Gdk.CrossingMode.NORMAL or not _hover["in"] or dragging: return
    if not _hover["t"]: _hover["t"] = GLib.timeout_add(350, Gtk.main_quit)
win.add_events(Gdk.EventMask.ENTER_NOTIFY_MASK | Gdk.EventMask.LEAVE_NOTIFY_MASK)
win.connect("enter-notify-event", _enter); win.connect("leave-notify-event", _leave)
win.connect("key-press-event", lambda w, e: Gtk.main_quit() if e.keyval == Gdk.KEY_Escape else None)
win.connect("focus-out-event", lambda *_: GLib.timeout_add(150, Gtk.main_quit))
win.connect("destroy", Gtk.main_quit)
win.show_all(); win.present()
Gtk.main()
