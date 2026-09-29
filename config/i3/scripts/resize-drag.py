#!/usr/bin/env python3
# Meta + right-drag resize, KDE style: the window is split into a 3x3 grid.
#   corners -> resize both ways from that corner
#   left/right middle -> width only;  top/bottom middle -> height only
#   center -> the nearest edge only
# Works for floating (exact) and tiled windows (grow/shrink toward that side).
import ctypes, ctypes.util, time, i3ipc

x = ctypes.cdll.LoadLibrary(ctypes.util.find_library("X11"))
x.XOpenDisplay.restype = ctypes.c_void_p; x.XDefaultRootWindow.restype = ctypes.c_ulong
dpy = x.XOpenDisplay(None); root = x.XDefaultRootWindow(ctypes.c_void_p(dpy))
def pointer():
    r, c = ctypes.c_ulong(), ctypes.c_ulong(); rx, ry, wx, wy = (ctypes.c_int() for _ in range(4)); m = ctypes.c_uint()
    x.XQueryPointer(ctypes.c_void_p(dpy), ctypes.c_ulong(root), ctypes.byref(r), ctypes.byref(c), ctypes.byref(rx),
                    ctypes.byref(ry), ctypes.byref(wx), ctypes.byref(wy), ctypes.byref(m))
    return rx.value, ry.value, m.value
BUTTON3 = 1 << 10

i3 = i3ipc.Connection()
px, py, _ = pointer()
ws = i3.get_tree().find_focused().workspace()
floats = [fc for f in ws.floating_nodes for fc in ([f] + f.leaves())]
cands = floats + [l for l in ws.leaves() if l not in floats]   # floating first (they are on top)
con = None
for c in cands:
    r = c.rect
    if r.x <= px < r.x + r.width and r.y <= py < r.y + r.height:
        con = c; break
if con is None: raise SystemExit
floating = con.floating in ("user_on", "auto_on") or (con.parent and con.parent.type == "floating_con")
if floating and con.parent and con.parent.type == "floating_con": con = con.parent
r = con.rect
fx, fy = (px - r.x) / max(r.width, 1), (py - r.y) / max(r.height, 1)
hx = -1 if fx < 1/3 else (1 if fx > 2/3 else 0)     # -1 left, 1 right, 0 none
hy = -1 if fy < 1/3 else (1 if fy > 2/3 else 0)     # -1 top,  1 bottom, 0 none
if hx == 0 and hy == 0:                              # center: nearest edge only
    if min(fx, 1 - fx) < min(fy, 1 - fy): hx = -1 if fx < .5 else 1
    else: hy = -1 if fy < .5 else 1
i3.command(f"[con_id={con.id}] focus")
x0, y0, w0, h0 = r.x, r.y, r.width, r.height
last_x, last_y, tiled_x, tiled_y = px, py, px, py
MIN = 80
while True:
    cx, cy, mask = pointer()
    if not mask & BUTTON3: break
    if (cx, cy) != (last_x, last_y):
        dx, dy = cx - px, cy - py
        if floating:
            w = max(MIN, w0 + dx * hx) if hx else w0
            h = max(MIN, h0 + dy * hy) if hy else h0
            nx = x0 + (w0 - w) if hx == -1 else x0
            ny = y0 + (h0 - h) if hy == -1 else y0
            i3.command(f"[con_id={con.id}] resize set {w} px {h} px, move position {nx} px {ny} px")
        else:
            cmds = []
            ddx, ddy = cx - tiled_x, cy - tiled_y
            if hx and abs(ddx) >= 4:
                side = "left" if hx == -1 else "right"
                grow = (ddx * hx) > 0
                cmds.append(f"resize {'grow' if grow else 'shrink'} {side} {abs(ddx)} px"); tiled_x = cx
            if hy and abs(ddy) >= 4:
                side = "up" if hy == -1 else "down"
                grow = (ddy * hy) > 0
                cmds.append(f"resize {'grow' if grow else 'shrink'} {side} {abs(ddy)} px"); tiled_y = cy
            for cmd in cmds: i3.command(f"[con_id={con.id}] {cmd}")
        last_x, last_y = cx, cy
    time.sleep(0.016)
