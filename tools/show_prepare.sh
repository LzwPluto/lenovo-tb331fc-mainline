#!/bin/bash
cd ~/kbuild/linux-next-tb128fu-hx83102-panel-port || exit 1
F=drivers/gpu/drm/panel/panel-himax-hx83102.c

echo "=== prepare() ==="
awk '/static int hx83102_prepare\(/{f=1} f{print NR": "$0} f&&/^}/{exit}' "$F"

echo
echo "=== unprepare() ==="
awk '/static int hx83102_unprepare\(/{f=1} f{print NR": "$0} f&&/^}/{exit}' "$F"
