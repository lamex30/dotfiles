#!/usr/bin/env python3
# Screen magnifier: freezes a snapshot of the screen into a fullscreen overlay
# and zooms it toward the cursor on the GPU-free cairo path (smooth, no xrandr).
# Scroll = zoom, zooming back to 1x / Esc / click = exit.
# FIFO commands (from i3 Meta+Ctrl+scroll): in / out / reset.
import os, gi
gi.require_version("Gtk", "3.0"); gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk, GLib
import cairo

FIFO = os.path.join(os.environ.get("XDG_RUNTIME_DIR", "/tmp"), "zoom.fifo")
STEP, MAX_Z = 1.15, 10.0

class Zoom:
    def __init__(self):
        self.z, self.surf, self.cx, self.cy = 1.0, None, 0, 0
        self.win = Gtk.Window(type=Gtk.WindowType.POPUP)
        self.win.set_app_paintable(True)
        self.win.add_events(Gdk.EventMask.SCROLL_MASK | Gdk.EventMask.SMOOTH_SCROLL_MASK |
                            Gdk.EventMask.POINTER_MOTION_MASK | Gdk.EventMask.BUTTON_PRESS_MASK |
                            Gdk.EventMask.KEY_PRESS_MASK)
        self.win.connect("draw", self.draw)
        self.win.connect("scroll-event", self.on_scroll)
        self.win.connect("motion-notify-event", self.on_motion)
        self.win.connect("button-press-event", lambda *_: self.close())
        self.win.connect("key-press-event", lambda w, e: self.close() if e.keyval == Gdk.KEY_Escape else None)
        if not os.path.exists(FIFO): os.mkfifo(FIFO)
        fd = os.open(FIFO, os.O_RDWR | os.O_NONBLOCK)
        GLib.io_add_watch(fd, GLib.IO_IN, self.on_fifo)

    def pointer(self):
        _, x, y, _ = Gdk.get_default_root_window().get_pointer()
        return x, y

    def open(self):
        mon = Gdk.Display.get_default().get_monitor(0).get_geometry()
        self.ox, self.oy, self.w, self.h = mon.x, mon.y, mon.width, mon.height
        root = Gdk.get_default_root_window()
        pix = Gdk.pixbuf_get_from_window(root, self.ox, self.oy, self.w, self.h)
        self.surf = Gdk.cairo_surface_create_from_pixbuf(pix, 1, None)
        self.cx, self.cy = self.pointer(); self.cx -= self.ox; self.cy -= self.oy
        self.win.move(self.ox, self.oy); self.win.resize(self.w, self.h)
        self.win.show_all()
        seat = Gdk.Display.get_default().get_default_seat()
        tries = {"n": 0}
        def grab():
            st = seat.grab(self.win.get_window(), Gdk.SeatCapabilities.ALL, False, None, None, None, None)
            tries["n"] += 1
            return st != Gdk.GrabStatus.SUCCESS and tries["n"] < 50
        GLib.timeout_add(20, grab)

    def close(self):
        self.z = 1.0
        Gdk.Display.get_default().get_default_seat().ungrab()
        self.win.hide(); self.surf = None

    def set_zoom(self, nz):
        if self.surf is None:
            if nz <= 1.0: return
            self.open()
        self.z = min(nz, MAX_Z)
        if self.z <= 1.02: self.close()
        else: self.win.queue_draw()

    def draw(self, _w, cr):
        if self.surf is None: return
        z, cx, cy = self.z, self.cx, self.cy
        # screen point s shows snapshot point  s/z + c*(1-1/z)  -> content under the cursor stays put
        cr.scale(z, z)
        cr.translate(-cx * (1 - 1 / z), -cy * (1 - 1 / z))
        cr.set_source_surface(self.surf, 0, 0)
        cr.get_source().set_filter(cairo.FILTER_BILINEAR if z < 3 else cairo.FILTER_NEAREST)
        cr.paint()

    def on_motion(self, _w, e):
        self.cx, self.cy = e.x, e.y; self.win.queue_draw()

    def on_scroll(self, _w, e):
        d = 0
        if e.direction == Gdk.ScrollDirection.UP: d = 1
        elif e.direction == Gdk.ScrollDirection.DOWN: d = -1
        elif e.direction == Gdk.ScrollDirection.SMOOTH: d = -e.delta_y
        if d: self.set_zoom(self.z * (STEP ** d))
        return True

    def on_fifo(self, fd, _c):
        try: data = os.read(fd, 1024).decode()
        except BlockingIOError: return True
        for cmd in data.split():
            if cmd == "in": self.set_zoom(self.z * STEP)
            elif cmd == "out": self.set_zoom(self.z / STEP)
            elif cmd == "reset" and self.surf is not None: self.close()
        return True

Zoom(); Gtk.main()
