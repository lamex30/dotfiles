#!/usr/bin/env python3
# Polybar can't handle mouse side buttons (8/9): it misreads them and fires random
# actions. This grabs buttons 8/9 on the bar window so polybar never sees them, and
# uses them for music: back = previous track, forward = next track.
import ctypes, ctypes.util, select, subprocess, time

x = ctypes.cdll.LoadLibrary(ctypes.util.find_library("X11"))
x.XOpenDisplay.restype = ctypes.c_void_p
dpy = x.XOpenDisplay(None)
fd = x.XConnectionNumber(ctypes.c_void_p(dpy))

class XButtonEvent(ctypes.Structure):
    _fields_ = [("type", ctypes.c_int), ("serial", ctypes.c_ulong), ("send_event", ctypes.c_int),
                ("display", ctypes.c_void_p), ("window", ctypes.c_ulong), ("root", ctypes.c_ulong),
                ("subwindow", ctypes.c_ulong), ("time", ctypes.c_ulong), ("x", ctypes.c_int),
                ("y", ctypes.c_int), ("x_root", ctypes.c_int), ("y_root", ctypes.c_int),
                ("state", ctypes.c_uint), ("button", ctypes.c_uint)]
class XEvent(ctypes.Union):
    _fields_ = [("type", ctypes.c_int), ("xbutton", XButtonEvent), ("pad", ctypes.c_long * 24)]

ButtonPress, ButtonPressMask, AnyModifier, GrabModeAsync = 4, 1 << 2, 1 << 15, 1
ACTIONS = {8: "previous", 9: "next"}

def bar_windows():
    out = subprocess.run(["xdotool", "search", "--class", "polybar"], capture_output=True, text=True).stdout
    return sorted(int(w) for w in out.split())

grabbed = []
def grab(wins):
    for w in grabbed:
        for b in ACTIONS: x.XUngrabButton(ctypes.c_void_p(dpy), b, AnyModifier, ctypes.c_ulong(w))
    for w in wins:
        for b in ACTIONS:
            x.XGrabButton(ctypes.c_void_p(dpy), b, AnyModifier, ctypes.c_ulong(w), 0, ButtonPressMask,
                          GrabModeAsync, GrabModeAsync, 0, 0)
    x.XFlush(ctypes.c_void_p(dpy))
    grabbed[:] = wins

x.XSetErrorHandler(ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p)(lambda d, e: 0))
ev, last_check = XEvent(), 0
while True:
    if time.time() - last_check > 3:          # polybar may have been restarted
        wins = bar_windows()
        if wins != grabbed: grab(wins)
        last_check = time.time()
    while x.XPending(ctypes.c_void_p(dpy)):
        x.XNextEvent(ctypes.c_void_p(dpy), ctypes.byref(ev))
        if ev.type == ButtonPress and ev.xbutton.button in ACTIONS:
            subprocess.Popen(["playerctl", ACTIONS[ev.xbutton.button]])
    select.select([fd], [], [], 1)
