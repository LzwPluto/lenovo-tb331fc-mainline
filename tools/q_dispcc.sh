#!/bin/bash
cd ~/kbuild/linux-next-tb128fu-hx83102-panel-port || exit 1

echo "=== dispcc node in CANONICAL.dts ==="
grep -n -A5 'clock-controller@5f00000' /mnt/d/TB331FCLinux/build/CANONICAL.dts | head -10

echo
echo "=== mdp_clk_src tables in every dispcc driver ==="
for f in drivers/clk/qcom/dispcc-*.c; do
    echo "--- $f"
    grep -A12 'ftbl_disp_cc_mdss_mdp_clk_src\[\]' "$f" | grep -E 'F\(|};' | head -12
done

echo
echo "=== rcg definition (mnd/hid/ops) for mdp_clk_src ==="
grep -n -A16 'static struct clk_rcg2 disp_cc_mdss_mdp_clk_src' drivers/clk/qcom/dispcc-*.c | head -40
