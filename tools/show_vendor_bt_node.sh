#!/bin/bash
set +e
D=/mnt/d/TB331FCLinux/ref/android/vendor.dts
echo "=== /soc/bt_wcn3990 node ==="
sed -n '2805,2850p' "$D"
echo
echo "=== icnss node head ==="
sed -n '14455,14485p' "$D"
