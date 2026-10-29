import re

dts_path = r"D:\TB331FCLinux\build\CANONICAL_383_dma.dts"

with open(dts_path, "r", encoding="utf-8") as f:
    text = f.read()

# 1. Add phandle = <0x228>; to backlight@11
old_bkl = """				backlight@11 {
					compatible = "kinetic,ktz8866";
					reg = <0x11>;
					enable-gpios = <0x28 0x1b 0x00>;
					vddpos-supply = <0x226>;
					vddneg-supply = <0x227>;
					current-num-sinks = <0x06>;
					kinetic,current-ramp-delay-ms = <0x80>;
					kinetic,led-enable-ramp-delay-ms = <0x01>;
				};"""

new_bkl = """				backlight@11 {
					compatible = "kinetic,ktz8866";
					reg = <0x11>;
					enable-gpios = <0x28 0x1b 0x00>;
					vddpos-supply = <0x226>;
					vddneg-supply = <0x227>;
					current-num-sinks = <0x06>;
					kinetic,current-ramp-delay-ms = <0x80>;
					kinetic,led-enable-ramp-delay-ms = <0x01>;
					phandle = <0x228>;
				};"""

if old_bkl in text:
    text = text.replace(old_bkl, new_bkl, 1)
    print("1. Added phandle = <0x228> to backlight@11")
elif "phandle = <0x228>;" in text:
    print("1. backlight@11 already has phandle 0x228")
else:
    print("ERROR: old_bkl pattern not found!")

# 2. Add backlight = <0x228>; to panel@0
old_panel = """				panel@0 {
					compatible = "lenovo,p255-inx";
					reg = <0x00>;
					pinctrl-names = "default";
					pinctrl-0 = <0x7a 0x7b>;
					rotation = <0xb4>;
					enable-gpios = <0x28 0x52 0x00>;
					pp1800-supply = <0x4c>;
					phandle = <0x4d>;"""

new_panel = """				panel@0 {
					compatible = "lenovo,p255-inx";
					reg = <0x00>;
					pinctrl-names = "default";
					pinctrl-0 = <0x7a 0x7b>;
					rotation = <0xb4>;
					enable-gpios = <0x28 0x52 0x00>;
					pp1800-supply = <0x4c>;
					backlight = <0x228>;
					phandle = <0x4d>;"""

if old_panel in text:
    text = text.replace(old_panel, new_panel, 1)
    print("2. Added backlight = <0x228> to panel@0")
elif "backlight = <0x228>;" in text:
    print("2. panel@0 already has backlight = <0x228>")
else:
    print("ERROR: old_panel pattern not found!")

with open(dts_path, "w", encoding="utf-8") as f:
    f.write(text)

print("CANONICAL_383_dma.dts updated successfully!")
