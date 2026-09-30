#!/usr/bin/env python3
# Mini OSD, top center under the bar.
# Shows volume/brightness (via FIFO), layout, Caps Lock, clipboard copies.
import ctypes, ctypes.util, os, gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib

BAR_H, GAP, WIDTH, HIDE_MS = 26, 8, 260, 1300
FIFO = os.path.join(os.environ.get("XDG_RUNTIME_DIR", "/tmp"), "osd.fifo")
LAYOUTS = ["EN", "RU"]

import json
try: C = json.load(open(os.path.expanduser("~/.config/i3/colors.json")))
except Exception: C = {"bg": "#1a1b26", "fg": "#c0caf5", "accent": "#7aa2f7", "inactive": "#2f334d"}
CSS = f"""
window {{ background: {C['bg']}; border: 2px solid {C['accent']}; }}
label {{ color: {C['fg']}; font: 11pt "JetBrainsMono Nerd Font"; }}
progressbar trough {{ background: {C['inactive']}; min-height: 6px; border: none; border-radius: 0; }}
progressbar progress {{ background: {C['accent']}; min-height: 6px; border: none; border-radius: 0; }}
""".encode()

class XkbState(ctypes.Structure):
    _fields_ = [("group", ctypes.c_ubyte), ("locked_group", ctypes.c_ubyte),
                ("base_group", ctypes.c_ushort), ("latched_group", ctypes.c_ushort),
                ("mods", ctypes.c_ubyte), ("base_mods", ctypes.c_ubyte),
                ("latched_mods", ctypes.c_ubyte), ("locked_mods", ctypes.c_ubyte),
                ("compat_state", ctypes.c_ubyte), ("grab_mods", ctypes.c_ubyte),
                ("compat_grab_mods", ctypes.c_ubyte), ("lookup_mods", ctypes.c_ubyte),
                ("compat_lookup_mods", ctypes.c_ubyte), ("ptr_buttons", ctypes.c_ushort)]

class OSD:
    def __init__(self):
        prov = Gtk.CssProvider(); prov.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), prov,
                                                 Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        self.win = Gtk.Window(type=Gtk.WindowType.POPUP)
        self.win.set_default_size(WIDTH, -1)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_margin_top(8); box.set_margin_bottom(10)
        box.set_margin_start(14); box.set_margin_end(14)
        self.label = Gtk.Label(); self.bar = Gtk.ProgressBar()
        box.pack_start(self.label, False, False, 0); box.pack_start(self.bar, False, False, 0)
        self.win.add(box); box.show_all()
        self.timer = None

        # XKB (раскладка + Caps)
        self.x11 = ctypes.cdll.LoadLibrary(ctypes.util.find_library("X11"))
        self.x11.XOpenDisplay.restype = ctypes.c_void_p
        self.dpy = self.x11.XOpenDisplay(None)
        self.last = self.xkb()
        GLib.timeout_add(100, self.poll_xkb)

        # буфер обмена
        self.ready = False
        GLib.timeout_add(1500, lambda: setattr(self, "ready", True) or False)
        self.clip = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        self.clip.connect("owner-change", self.on_clip)
        self.clip_pending = False

        # FIFO для громкости/яркости
        if not os.path.exists(FIFO): os.mkfifo(FIFO)
        fd = os.open(FIFO, os.O_RDWR | os.O_NONBLOCK)
        GLib.io_add_watch(fd, GLib.IO_IN, self.on_fifo)

    def xkb(self):
        st = XkbState()
        self.x11.XkbGetState(ctypes.c_void_p(self.dpy), 0x100, ctypes.byref(st))
        return st.group, bool(st.locked_mods & 2)

    def poll_xkb(self):
        cur = self.xkb()
        if cur != self.last:
            if cur[0] != self.last[0]:
                g = cur[0]
                self.show(LAYOUTS[g] if g < len(LAYOUTS) else f"Layout {g+1}")
            if cur[1] != self.last[1]:
                self.show("Caps Lock on" if cur[1] else "Caps Lock off")
            self.last = cur
        return True

    def on_clip(self, *_):
        if not self.ready or self.clip_pending: return
        self.clip_pending = True
        GLib.timeout_add(150, self.clip_show)

    def clip_show(self):
        self.clip_pending = False
        def got(_c, text):
            if text:
                t = " ".join(text.split())
                self.show("Copied: " + (t[:22] + "…" if len(t) > 22 else t))
            else:
                self.show("Copied")
        self.clip.request_text(got)
        return False

    def on_fifo(self, fd, _cond):
        try: data = os.read(fd, 4096).decode(errors="ignore")
        except BlockingIOError: return True
        for line in data.strip().splitlines():
            text, _, val = line.partition("|")
            self.show(text, int(val) if val.strip().isdigit() else None)
        return True

    def show(self, text, value=None):
        self.label.set_text(text)
        if value is None: self.bar.hide()
        else: self.bar.set_fraction(max(0, min(value, 100)) / 100); self.bar.show()
        self.win.resize(WIDTH, 1)
        mon = Gdk.Display.get_default().get_monitor(0).get_geometry()
        self.win.move(mon.x + (mon.width - WIDTH) // 2, mon.y + BAR_H + GAP)
        self.win.show()
        if self.timer: GLib.source_remove(self.timer)
        self.timer = GLib.timeout_add(HIDE_MS, self.hide)

    def hide(self):
        self.win.hide(); self.timer = None
        return False

OSD()
Gtk.main()
