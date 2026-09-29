#!/bin/sh
# NVIDIA load without waking the dGPU from runtime sleep (hybrid laptop)
for d in /sys/bus/pci/drivers/nvidia/0000:*; do
  [ -e "$d" ] || continue
  if [ "$(cat "$d/power/runtime_status" 2>/dev/null)" = "suspended" ]; then echo "off"; exit; fi
done
command -v nvidia-smi >/dev/null || { echo "n/a"; exit; }
u=$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits 2>/dev/null | head -1 | tr -d ' ')
[ -n "$u" ] && echo "$u%" || echo "n/a"
