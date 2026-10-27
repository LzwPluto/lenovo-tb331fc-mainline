#!/bin/bash
cd ~/kbuild/linux-next-tb128fu-hx83102-panel-port || exit 1
echo "=== _opp_config_clk_single 源码 ==="
grep -n -A40 "_opp_config_clk_single" drivers/opp/core.c | head -55
echo
echo "=== 谁调用 _opp_config_clk_single ==="
grep -n "_opp_config_clk_single" drivers/opp/core.c
echo
echo "=== dev_pm_opp_set_rate 里 clk 缺失时的行为 ==="
grep -n -A45 "int dev_pm_opp_set_rate" drivers/opp/core.c | sed -n '1,60p'
