#!/bin/bash
cd ~/kbuild/linux-next-tb128fu-hx83102-panel-port || exit 1
F=drivers/input/touchscreen/nt36523_fw_update.c

echo "=== chunk size / delays / spi params in fw update ==="
grep -nE "CHUNK|chunk|usleep|msleep|delay|spi_sync|spi_write|spi_read|mode|max_speed|bpw" "$F" | head -40

echo
echo "=== writing dlm function ==="
grep -nE "^static int32_t nvt_.*\(|^static int nvt_.*\(" "$F" | head -20
