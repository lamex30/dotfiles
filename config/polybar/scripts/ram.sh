#!/bin/sh
# used/total RAM, e.g. 5.2/23.3 GiB
awk '/^MemTotal:/{t=$2} /^MemAvailable:/{a=$2} END{printf "%.1f/%.1f GiB\n", (t-a)/1048576, t/1048576}' /proc/meminfo
