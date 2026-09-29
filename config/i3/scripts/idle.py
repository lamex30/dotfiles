#!/usr/bin/env python3
# Idle manager.
#   on AC:      5 min idle -> lock + screen off
#   on battery: 1 min idle -> dim screen, 2 min -> lock + screen off
# Nothing happens while media is playing (videos, streams, music).
import ctypes, ctypes.util, glob, os, subprocess, time

AC_LOCK, BAT_DIM, BAT_LOCK, DIM_TO = 300, 60, 120, 0.3

class Info(ctypes.Structure):
    _fields_ = [("window", ctypes.c_ulong), ("state", ctypes.c_int), ("kind", ctypes.c_int),
                ("til_or_since", ctypes.c_ulong), ("idle", ctypes.c_ulong), ("mask", ctypes.c_ulong)]
x11 = ctypes.cdll.LoadLibrary(ctypes.util.find_library("X11"))
xss = ctypes.cdll.LoadLibrary(ctypes.util.find_library("Xss") or "libXss.so.1")
x11.XOpenDisplay.restype = ctypes.c_void_p; x11.XDefaultRootWindow.restype = ctypes.c_ulong
xss.XScreenSaverAllocInfo.restype = ctypes.POINTER(Info)
dpy = x11.XOpenDisplay(None); root = x11.XDefaultRootWindow(ctypes.c_void_p(dpy))
info = xss.XScreenSaverAllocInfo()

def idle():
    xss.XScreenSaverQueryInfo(ctypes.c_void_p(dpy), ctypes.c_ulong(root), info)
    return info.contents.idle / 1000

def on_ac():
    for d in glob.glob("/sys/class/power_supply/*"):
        try:
            if open(f"{d}/type").read().strip() == "Mains": return open(f"{d}/online").read().strip() == "1"
        except Exception: pass
    return True

def playing():
    out = subprocess.run(["playerctl", "-a", "status"], capture_output=True, text=True).stdout
    return "Playing" in out

bl = sorted(glob.glob("/sys/class/backlight/*"), key=lambda d: os.path.basename(d).startswith("acpi_video"))
BL = os.path.basename(bl[0]) if bl else None
def get_b():
    return int(open(f"/sys/class/backlight/{BL}/brightness").read()) if BL else None
def set_b(v):
    if BL: subprocess.run(["brightnessctl", "-q", "-d", BL, "set", str(max(1, int(v)))])

def lock_off():
    subprocess.run(["loginctl", "lock-session"]); time.sleep(1.0)
    subprocess.run(["xset", "dpms", "force", "off"])

subprocess.run(["xset", "s", "off"]); subprocess.run(["xset", "+dpms"]); subprocess.run(["xset", "dpms", "0", "0", "0"])
dimmed_from, locked = None, False
while True:
    t = idle()
    if t < 2:                                   # user is back
        if dimmed_from is not None: set_b(dimmed_from); dimmed_from = None
        locked = False
    elif not playing():
        ac = on_ac()
        if not ac and t >= BAT_DIM and dimmed_from is None and not locked:
            dimmed_from = get_b()
            if dimmed_from: set_b(dimmed_from * DIM_TO)
        if not locked and t >= (AC_LOCK if ac else BAT_LOCK):
            lock_off(); locked = True
    time.sleep(1 if dimmed_from is not None or t < 5 else 2)
