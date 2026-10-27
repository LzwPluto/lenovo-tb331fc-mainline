#!/bin/bash
cd ~/kbuild/linux-next-tb128fu-hx83102-panel-port || exit 1
echo "=== msm 里的 pm_opp 用法 ==="
grep -rn "devm_pm_opp\|dev_pm_opp_set_rate\|opp_set_clkname" drivers/gpu/drm/msm/*.c | head -10
echo
echo "=== _opp_config_clk_single 定义位置 ==="
grep -rn "_opp_config_clk_single" drivers/gpu/drm/msm/ | head -5
echo
echo "=== dpu_core_perf 附近的调用 ==="
grep -rn -B3 -A8 "failed to set core clock rate" drivers/gpu/drm/msm/disp/dpu1/dpu_core_perf.c | head -40
echo
echo "=== dispcc 驱动文件 ==="
ls drivers/clk/qcom/ | grep -iE "dispcc.*(sm6115|sm6225)"
echo
echo "=== dispcc 里的 MDSS_MDP_CLK ==="
grep -rn -B2 -A6 "MDSS_MDP_CLK" drivers/clk/qcom/dispcc-sm6115.c 2>/dev/null | head -40
