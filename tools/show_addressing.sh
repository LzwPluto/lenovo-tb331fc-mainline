#!/bin/bash
cd ~/kbuild/linux-next-tb128fu-hx83102-panel-port || exit 1
TS=drivers/input/touchscreen/nt36523_ts.c

echo "=== our nvt_ts_check_chip_ver_trim ==="
sed -n '1210,1290p' "$TS"

echo
echo "=== nvt_read_pid ==="
sed -n '565,600p' "$TS"

echo
echo "=== nvt_set_page ==="
grep -n -A12 "void nvt_set_page" "$TS" | head -18

echo
echo "=== CTP_SPI_READ/WRITE address handling ==="
grep -rn -A12 "define CTP_SPI_READ\|define CTP_SPI_WRITE" drivers/input/touchscreen/*.h | head -34
