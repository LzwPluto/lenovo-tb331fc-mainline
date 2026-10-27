#!/bin/bash
set +e
D=/mnt/d/TB331FCLinux/ref/android/vendor.dts

echo "=== anything bluetooth-ish ==="
grep -niE "\bbluetooth\b|wcn399|bt-enable|bt_en|btfm" "$D" | head -15

echo
echo "=== cnss / wlan nodes ==="
grep -niE "cnss|wlan|wifi@" "$D" | head -15

echo
echo "=== serial nodes under geniqup ==="
grep -nE "serial@4a[0-9a-f]+" "$D" | head -10
