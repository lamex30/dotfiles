#!/usr/bin/env python3
# Wallpaper picker: big centered window with a thumbnail grid of a folder (subfolders included).
# "Change folder" picks another folder; the choice is remembered until changed again.
# Click a wallpaper -> it is applied and the whole system is re-themed from it.
import hashlib, json, os, subprocess, threading, gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, GdkPixbuf, Pango

HOME = os.path.expanduser("~")
STATE = f"{HOME}/.config/i3/wallpicker.json"
CACHE = f"{HOME}/.cache/wallpicker"
EXTS = (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif")
TW, TH = 288, 162
os.makedirs(CACHE, exist_ok=True)

def load_state():
    try: return json.load(open(STATE))
    except Exception:
        for d in (f"{HOME}/Documents/walls", f"{HOME}/Pictures/Wallpapers", f"{HOME}/Pictures"):
            if os.path.isdir(d): return {"folder": d}
        return {"folder": HOME}
def save_state(s): json.dump(s, open(STATE, "w"), indent=2)
state = load_state()

try: C = json.load(open(f"{HOME}/.config/i3/colors.json"))
except Exception: C = {"bg": "#141414", "bg_alt": "#212121", "fg": "#e0e0e0", "dim": "#808080", "accent": "#db8095", "inactive": "#333333"}
CSS = f"""
window {{ background: {C['bg']}; border: 2px solid {C['accent']}; }}
label {{ color: {C['fg']}; font: 10pt "JetBrainsMono Nerd Font"; }}
.title {{ font-size: 13pt; color: {C['accent']}; }}
.dim {{ color: {C['dim']}; }}
button {{ background: {C.get('bg_alt', C['bg'])}; border: none; box-shadow: none; border-radius: 0; padding: 6px 12px; }}
button:hover {{ background: {C['inactive']}; }}
button label {{ color: {C['fg']}; }}
flowbox, flowboxchild, scrolledwindow, viewport {{ background: transparent; border: none; }}
flowboxchild {{ padding: 6px; border: 2px solid transparent; }}
flowboxchild:hover {{ background: {C.get('bg_alt', C['bg'])}; }}
flowboxchild:selected {{ background: transparent; }}
.current {{ border: 2px solid {C['accent']}; }}
""".encode()
prov = Gtk.CssProvider(); prov.load_from_data(CSS)
Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), prov, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

def current_wall():
    return state.get("current", "")

def thumb(path):
    key = hashlib.md5(f"{path}:{os.path.getmtime(path)}".encode()).hexdigest()
    cp = f"{CACHE}/{key}.png"
    if os.path.exists(cp): return GdkPixbuf.Pixbuf.new_from_file(cp)
    pb = GdkPixbuf.Pixbuf.new_from_file_at_scale(path, TW * 2, TH * 2, True)
    # crop to 16:9 cover
    s = max(TW / pb.get_width(), TH / pb.get_height())
    w, h = max(TW, int(pb.get_width() * s)), max(TH, int(pb.get_height() * s))
    pb = pb.scale_simple(w, h, GdkPixbuf.InterpType.BILINEAR)
    pb = pb.new_subpixbuf((w - TW) // 2, (h - TH) // 2, TW, TH).copy()
    pb.savev(cp, "png", [], [])
    return pb

mon = Gdk.Display.get_default().get_monitor(0).get_geometry()
win = Gtk.Window(title="wallpicker"); win.set_wmclass("wallpicker", "wallpicker")
win.set_decorated(False); win.set_default_size(int(mon.width * 0.78), int(mon.height * 0.78))
outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
for m in ("top", "bottom", "start", "end"): getattr(outer, f"set_margin_{m}")(24)
win.add(outer)

head = Gtk.Box(spacing=12)
title = Gtk.Label(label=chr(0xF02E9) + "  Wallpapers", xalign=0); title.get_style_context().add_class("title")
path_lbl = Gtk.Label(xalign=0); path_lbl.get_style_context().add_class("dim")
path_lbl.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
change = Gtk.Button(label=chr(0xF024B) + "  Change folder")
close = Gtk.Button(label="✕")
head.pack_start(title, False, False, 0); head.pack_start(path_lbl, True, True, 0)
head.pack_end(close, False, False, 0); head.pack_end(change, False, False, 0)
outer.pack_start(head, False, False, 0)

scroll = Gtk.ScrolledWindow(); scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
flow = Gtk.FlowBox(); flow.set_valign(Gtk.Align.START); flow.set_homogeneous(True)
flow.set_selection_mode(Gtk.SelectionMode.NONE); flow.set_max_children_per_line(12)
flow.set_column_spacing(8); flow.set_row_spacing(8)
scroll.add(flow); outer.pack_start(scroll, True, True, 0)
gen = {"n": 0}

def apply(path):
    state["current"] = path; save_state(state)
    win.hide()
    subprocess.Popen([f"{HOME}/.config/i3/scripts/wallpaper.sh", path])
    GLib.timeout_add(100, Gtk.main_quit)

def add_item(path, pb, g):
    if g != gen["n"]: return False
    img = Gtk.Image.new_from_pixbuf(pb)
    ev = Gtk.EventBox(); ev.add(img); ev.set_tooltip_text(os.path.basename(path))
    ev.connect("button-press-event", lambda *_: apply(path))
    child = Gtk.FlowBoxChild(); child.add(ev)
    if path == current_wall(): child.get_style_context().add_class("current")
    flow.add(child); child.show_all()
    return False

def load_folder():
    gen["n"] += 1; g = gen["n"]
    for ch in flow.get_children(): flow.remove(ch)
    folder = state["folder"]
    path_lbl.set_text(folder.replace(HOME, "~"))
    files = []
    for dp, _dn, fn in os.walk(folder):
        files += [os.path.join(dp, f) for f in sorted(fn) if f.lower().endswith(EXTS)]
    if not files:
        l = Gtk.Label(label="No images in this folder"); l.get_style_context().add_class("dim")
        flow.add(l); l.show(); return
    def worker():
        for f in files:
            if g != gen["n"]: return
            try: pb = thumb(f)
            except Exception: continue
            GLib.idle_add(add_item, f, pb, g)
    threading.Thread(target=worker, daemon=True).start()

def pick_folder(*_):
    dlg = Gtk.FileChooserDialog(title="Choose wallpaper folder", parent=win, action=Gtk.FileChooserAction.SELECT_FOLDER)
    dlg.add_buttons("Cancel", Gtk.ResponseType.CANCEL, "Select", Gtk.ResponseType.OK)
    dlg.set_current_folder(state["folder"])
    if dlg.run() == Gtk.ResponseType.OK:
        state["folder"] = dlg.get_filename(); save_state(state); load_folder()
    dlg.destroy()

change.connect("clicked", pick_folder)
close.connect("clicked", lambda *_: Gtk.main_quit())
win.connect("key-press-event", lambda w, e: Gtk.main_quit() if e.keyval == Gdk.KEY_Escape else None)
win.connect("destroy", Gtk.main_quit)
load_folder()
win.show_all(); win.present()
Gtk.main()
