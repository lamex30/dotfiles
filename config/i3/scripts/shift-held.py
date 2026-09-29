#!/usr/bin/env python3
# exit 0 if Shift is currently held, 1 otherwise
import ctypes, ctypes.util, sys
x = ctypes.cdll.LoadLibrary(ctypes.util.find_library("X11"))
x.XOpenDisplay.restype = ctypes.c_void_p; x.XDefaultRootWindow.restype = ctypes.c_ulong
d = x.XOpenDisplay(None); r = x.XDefaultRootWindow(ctypes.c_void_p(d))
a, b = ctypes.c_ulong(), ctypes.c_ulong(); i = [ctypes.c_int() for _ in range(4)]; m = ctypes.c_uint()
x.XQueryPointer(ctypes.c_void_p(d), ctypes.c_ulong(r), ctypes.byref(a), ctypes.byref(b),
                *[ctypes.byref(v) for v in i], ctypes.byref(m))
sys.exit(0 if m.value & 1 else 1)
