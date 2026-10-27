#!/usr/bin/env python3
"""apply_battery_hall_bt.py

Applies hardware configurations for TB331FC to CANONICAL_383_dma.dts:
1. Replaces incorrect fuel-gauge@55 (ti,bq27541) on i2c@4a84000 with real Mitsumi MM8013 on i2c@4a88000
2. Adds Hall Sensor (SW_LID, GPIO 66) to gpio-keys
3. Corrects QUP UART3 (4a8c000) 4-wire pinctrl biases matching vendor specs
"""
import re
import sys

DTS = "/mnt/d/TB331FCLinux/build/CANONICAL_383_dma.dts"

with open(DTS, "r", encoding="utf-8") as f:
    s = f.read()

# 1. Remove bogus fuel-gauge@55 from i2c@4a84000
bogus_fuel = """\t\t\t\tfuel-gauge@55 {
\t\t\t\t\tcompatible = "ti,bq27541";
\t\t\t\t\treg = <0x55>;
\t\t\t\t\tinterrupts-extended = <0x28 0x1c 0x00>;
\t\t\t\t\tmonitored-battery = <0x4f>;
\t\t\t\t};"""

if bogus_fuel in s:
    s = s.replace(bogus_fuel, "")
    print("1a. Removed bogus fuel-gauge@55 (ti,bq27541) from i2c@4a84000")
else:
    print("1a. Bogus fuel-gauge@55 not present or already removed")

# 1b. Add Mitsumi MM8013 to i2c@4a88000
mm8013_node = """\t\t\t\tbattery@55 {
\t\t\t\t\tcompatible = "mitsumi,mm8013", "mm8013c10";
\t\t\t\t\treg = <0x55>;
\t\t\t\t};"""

if 'compatible = "mitsumi,mm8013"' in s:
    print("1b. MM8013 battery node already present in DTS")
else:
    # insert inside i2c@4a88000 right after status = "okay";
    i2c88_anchor = """\t\t\ti2c@4a88000 {
\t\t\t\tcompatible = "qcom,geni-i2c";
\t\t\t\treg = <0x00 0x4a88000 0x00 0x4000>;
\t\t\t\tclock-names = "se";
\t\t\t\tclocks = <0x02 0x6d>;
\t\t\t\tpinctrl-names = "default";
\t\t\t\tpinctrl-0 = <0x52>;
\t\t\t\tinterrupts = <0x00 0x149 0x04>;
\t\t\t\tdmas = <0x46 0x00 0x02 0x03 0x46 0x01 0x02 0x03>;
\t\t\t\tdma-names = "tx\\0rx";
\t\t\t\t#address-cells = <0x01>;
\t\t\t\t#size-cells = <0x00>;
\t\t\t\tstatus = "okay";"""

    if i2c88_anchor in s:
        s = s.replace(i2c88_anchor, i2c88_anchor + "\n\n" + mm8013_node, 1)
        print("1b. Added MM8013 battery@55 to i2c@4a88000")
    else:
        print("ERROR: i2c@4a88000 anchor not matched!")
        sys.exit(1)

# 2. Add Hall Sensor (SW_LID, GPIO 66) to gpio-keys
hall_node = """\t\thall-sensor {
\t\t\tlabel = "Hall Sensor";
\t\t\tgpios = <0x28 0x42 0x01>;
\t\t\tlinux,input-type = <0x05>;
\t\t\tlinux,code = <0x00>;
\t\t\twakeup-source;
\t\t};"""

if 'label = "Hall Sensor";' in s:
    print("2. Hall Sensor already present in gpio-keys")
else:
    gpio_keys_anchor = """\t\tkey-volume-up {
\t\t\tlabel = "Volume Up";
\t\t\tlinux,code = <0x73>;
\t\t\tgpios = <0x36 0x05 0x01>;
\t\t\tdebounce-interval = <0x0f>;
\t\t\tlinux,can-disable;
\t\t\twakeup-source;
\t\t};"""
    if gpio_keys_anchor in s:
        s = s.replace(gpio_keys_anchor, gpio_keys_anchor + "\n\n" + hall_node, 1)
        print("2. Added hall-sensor (SW_LID, GPIO 66) to gpio-keys")
    else:
        print("ERROR: key-volume-up anchor not found in gpio-keys")
        sys.exit(1)

# 3. Correct QUP UART3 4-wire pinctrl biases
# Properties must precede subnodes in device tree!
new_pinctrl_fixed = """\t\t\tqup-uart3-active-state {
\t\t\t\tphandle = <0x57>;

\t\t\t\tcts-pins {
\t\t\t\t\tpins = "gpio8";
\t\t\t\t\tfunction = "qup3";
\t\t\t\t\tdrive-strength = <0x02>;
\t\t\t\t\tbias-disable;
\t\t\t\t};

\t\t\t\trts-pins {
\t\t\t\t\tpins = "gpio9";
\t\t\t\t\tfunction = "qup3";
\t\t\t\t\tdrive-strength = <0x02>;
\t\t\t\t\tbias-pull-down;
\t\t\t\t};

\t\t\t\ttx-pins {
\t\t\t\t\tpins = "gpio10";
\t\t\t\t\tfunction = "qup3";
\t\t\t\t\tdrive-strength = <0x02>;
\t\t\t\t\tbias-pull-up;
\t\t\t\t};

\t\t\t\trx-pins {
\t\t\t\t\tpins = "gpio11";
\t\t\t\t\tfunction = "qup3";
\t\t\t\t\tdrive-strength = <0x02>;
\t\t\t\t\tbias-disable;
\t\t\t\t};
\t\t\t};"""

# If previous bad replacement happened:
bad_pinctrl = """\t\t\tqup-uart3-active-state {
\t\t\t\tcts-pins {
\t\t\t\t\tpins = "gpio8";
\t\t\t\t\tfunction = "qup3";
\t\t\t\t\tdrive-strength = <0x02>;
\t\t\t\t\tbias-disable;
\t\t\t\t};

\t\t\t\trts-pins {
\t\t\t\t\tpins = "gpio9";
\t\t\t\t\tfunction = "qup3";
\t\t\t\t\tdrive-strength = <0x02>;
\t\t\t\t\tbias-pull-down;
\t\t\t\t};

\t\t\t\ttx-pins {
\t\t\t\t\tpins = "gpio10";
\t\t\t\t\tfunction = "qup3";
\t\t\t\t\tdrive-strength = <0x02>;
\t\t\t\t\tbias-pull-up;
\t\t\t\t};

\t\t\t\trx-pins {
\t\t\t\t\tpins = "gpio11";
\t\t\t\t\tfunction = "qup3";
\t\t\t\t\tdrive-strength = <0x02>;
\t\t\t\t\tbias-disable;
\t\t\t\t};

\t\t\t\tphandle = <0x57>;
\t\t\t};"""

if bad_pinctrl in s:
    s = s.replace(bad_pinctrl, new_pinctrl_fixed, 1)
    print("3. Fixed property order in qup-uart3-active-state")
elif new_pinctrl_fixed in s:
    print("3. qup-uart3-active-state already properly formatted")

with open(DTS, "w", encoding="utf-8") as f:
    f.write(s)

print("CANONICAL_383_dma.dts updated successfully!")
