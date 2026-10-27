#!/usr/bin/env python3
"""apply_audio_and_tcpc.py

Updates CANONICAL_383_dma.dts with:
1. Removal of fake sy6974@6b (which conflicted with Hall sensor on GPIO 66)
2. Correction of RT1711H Type-C TCPC: GPIO 93 (0x5d), status = "okay"
3. Addition of 4x Awinic AW88166 Smart PA nodes on I2C-0 and I2C-1
4. Addition of FSA4480 USB-C audio switch on I2C-0 (0x42)
"""
import re
import sys

dts_path = r"D:\TB331FCLinux\build\CANONICAL_383_dma.dts"

with open(dts_path, "r", encoding="utf-8") as f:
    text = f.read()

# 1. Remove sy6974@6b node
sy_match = re.search(r'\tsy6974@6b\s*\{[^}]+\};', text)
if sy_match:
    text = text[:sy_match.start()] + text[sy_match.end():]
    print("Removed sy6974@6b node successfully")
else:
    print("sy6974@6b node not found")

# 2. Add AW88166 and FSA4480 to i2c@4a84000
# Target anchor: inside i2c@4a84000 right after backlight@11 { ... };
i2c0_anchor = re.search(r'(backlight@11\s*\{[^}]+\};\s*)', text)
if i2c0_anchor and "speaker@34" not in text:
    smartpa_i2c0 = """\n\t\t\t\tspeaker@34 {
\t\t\t\t\tcompatible = "awinic,aw88166", "awinic,aw883xx_smartpa";
\t\t\t\t\treg = <0x34>;
\t\t\t\t\treset-gpios = <0x28 0x55 0x01>;
\t\t\t\t\tinterrupt-parent = <0x28>;
\t\t\t\t\tinterrupts = <0x67 0x08>;
\t\t\t\t\tsound-channel = <0x03>;
\t\t\t\t\t#sound-dai-cells = <0x00>;
\t\t\t\t\tfirmware-name = "aw883xx_acf.bin";
\t\t\t\t\tstatus = "okay";
\t\t\t\t};

\t\t\t\tspeaker@35 {
\t\t\t\t\tcompatible = "awinic,aw88166", "awinic,aw883xx_smartpa";
\t\t\t\t\treg = <0x35>;
\t\t\t\t\treset-gpios = <0x28 0x19 0x01>;
\t\t\t\t\tinterrupt-parent = <0x28>;
\t\t\t\t\tinterrupts = <0x41 0x08>;
\t\t\t\t\tsound-channel = <0x02>;
\t\t\t\t\t#sound-dai-cells = <0x00>;
\t\t\t\t\tfirmware-name = "aw883xx_acf.bin";
\t\t\t\t\tstatus = "okay";
\t\t\t\t};

\t\t\t\ttypec-switch@42 {
\t\t\t\t\tcompatible = "qcom,fsa4480-i2c";
\t\t\t\t\treg = <0x42>;
\t\t\t\t\tstatus = "okay";
\t\t\t\t};
"""
    idx = i2c0_anchor.end()
    text = text[:idx] + smartpa_i2c0 + text[idx:]
    print("Added AW88166 (0x34, 0x35) and FSA4480 (0x42) to i2c@4a84000")

# 3. Add AW88166 to i2c@4a88000
# Target anchor: right after battery@55 { ... };
i2c1_anchor = re.search(r'(battery@55\s*\{[^}]+\};\s*)', text)
if i2c1_anchor and "sound-channel = <0x01>;" not in text:
    smartpa_i2c1 = """\n\t\t\t\tspeaker@34 {
\t\t\t\t\tcompatible = "awinic,aw88166", "awinic,aw883xx_smartpa";
\t\t\t\t\treg = <0x34>;
\t\t\t\t\treset-gpios = <0x28 0x60 0x01>;
\t\t\t\t\tinterrupt-parent = <0x28>;
\t\t\t\t\tinterrupts = <0x61 0x08>;
\t\t\t\t\tsound-channel = <0x01>;
\t\t\t\t\t#sound-dai-cells = <0x00>;
\t\t\t\t\tfirmware-name = "aw883xx_acf.bin";
\t\t\t\t\tstatus = "okay";
\t\t\t\t};

\t\t\t\tspeaker@35 {
\t\t\t\t\tcompatible = "awinic,aw88166", "awinic,aw883xx_smartpa";
\t\t\t\t\treg = <0x35>;
\t\t\t\t\treset-gpios = <0x28 0x6a 0x01>;
\t\t\t\t\tinterrupt-parent = <0x28>;
\t\t\t\t\tinterrupts = <0x66 0x08>;
\t\t\t\t\tsound-channel = <0x00>;
\t\t\t\t\t#sound-dai-cells = <0x00>;
\t\t\t\t\tfirmware-name = "aw883xx_acf.bin";
\t\t\t\t\tstatus = "okay";
\t\t\t\t};
"""
    idx = i2c1_anchor.end()
    text = text[:idx] + smartpa_i2c1 + text[idx:]
    print("Added AW88166 (0x34, 0x35) to i2c@4a88000")

# 4. Correct RT1711H on i2c@4a94000
# Update status from "disabled" to "okay" and interrupts from <0x11 0x08> to <0x5d 0x08> (GPIO 93)
rt_old = """\t\t\t\trt1715@4e {
\t\t\tstatus = "disabled";
\t\t\t\t\tcompatible = "richtek,rt1711h";
\t\t\t\t\treg = <0x4e>;
\t\t\t\t\tinterrupt-parent = <0x28>;
\t\t\t\t\tinterrupts = <0x11 0x08>;"""

rt_new = """\t\t\t\trt1711h@4e {
\t\t\t\t\tstatus = "okay";
\t\t\t\t\tcompatible = "richtek,rt1711h";
\t\t\t\t\treg = <0x4e>;
\t\t\t\t\tinterrupt-parent = <0x28>;
\t\t\t\t\tinterrupts = <0x5d 0x08>;"""

if rt_old in text:
    text = text.replace(rt_old, rt_new, 1)
    print("Corrected RT1711H TCPC node (GPIO 93, status okay)")
else:
    print("rt_old pattern not matched exactly, checking with regex")
    text = re.sub(
        r'rt1715@4e\s*\{\s*status\s*=\s*"disabled";\s*compatible\s*=\s*"richtek,rt1711h";\s*reg\s*=\s*<0x4e>;\s*interrupt-parent\s*=\s*<0x28>;\s*interrupts\s*=\s*<0x11\s+0x08>;',
        'rt1711h@4e {\n\t\t\t\t\tstatus = "okay";\n\t\t\t\t\tcompatible = "richtek,rt1711h";\n\t\t\t\t\treg = <0x4e>;\n\t\t\t\t\tinterrupt-parent = <0x28>;\n\t\t\t\t\tinterrupts = <0x5d 0x08>;',
        text
    )

with open(dts_path, "w", encoding="utf-8") as f:
    f.write(text)

print("apply_audio_and_tcpc.py complete!")
