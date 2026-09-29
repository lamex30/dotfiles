#!/bin/sh
# "Title - Artist" of the current player; dimmed when paused, empty when nothing plays
exec python3 - <<'PY'
import json, os, subprocess, sys
try: dim = json.load(open(os.path.expanduser("~/.config/i3/colors.json")))["dim"]
except Exception: dim = "#808080"
EMPTY = f"%{{F{dim}}}No media found%{{F-}}"
print(EMPTY, flush=True)
p = subprocess.Popen(["playerctl", "--follow", "metadata", "--format", "{{status}}\t{{title}}\t{{artist}}"],
                     stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
for line in p.stdout:
    status, title, artist = (line.rstrip("\n").split("\t") + ["", "", ""])[:3]
    if not title: print(EMPTY, flush=True); continue
    t = f"{title} - {artist}" if artist else title
    if len(t) > 25: t = t[:24] + "…"   # ~200px in JetBrainsMono 10pt
    t = t.replace("%", "%%")
    print(t if status == "Playing" else f"%{{F{dim}}}{t}%{{F-}}", flush=True)
PY
