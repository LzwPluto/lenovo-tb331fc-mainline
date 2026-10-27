#!/bin/bash
cd ~/kbuild/linux-next-tb128fu-hx83102-panel-port || exit 1

echo "=== /tmp/mods.log tail ==="
tail -15 /tmp/mods.log 2>/dev/null || echo "(no log)"

echo
echo "=== find .ko (any) ==="
find . -name '*.ko' 2>/dev/null | head -10
echo "count: $(find . -name '*.ko' 2>/dev/null | wc -l)"

echo
echo "=== ath10k firmware request sites ==="
grep -rn "request_firmware\|firmware-name\|ath10k_core_fetch_firmware" \
    drivers/net/wireless/ath/ath10k/*.c 2>/dev/null | head -12

echo
echo "=== qmi / bdf function bodies ==="
grep -rn "mdt\|mbn\|bdf\|\.bin" drivers/net/wireless/ath/ath10k/qmi.c 2>/dev/null | head -12
