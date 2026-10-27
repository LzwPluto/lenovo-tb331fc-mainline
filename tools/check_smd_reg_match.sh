#!/bin/bash
set +e
cd ~/kbuild/linux-next-tb128fu-hx83102-panel-port || exit 1
echo "=== qcom_smd-regulator compatible table ==="
grep -n -A30 "static const struct of_device_id rpm_of_match" drivers/regulator/qcom_smd-regulator.c | head -40
echo
echo "=== does it support pm6125? ==="
grep -n "pm6125" drivers/regulator/qcom_smd-regulator.c | head -10
