import re

path = r"D:\TB331FCLinux\build\CANONICAL_383_dma.dts"
with open(path, "r", encoding="utf-8") as f:
    c = f.read()

target = 'max-speed = <0x30d400>;'
replacement = 'max-speed = <0x30d400>;\n\t\t\t\t\tswctrl-gpios = <0x28 0x57 0x00>;'

if 'swctrl-gpios' in c:
    print("swctrl-gpios already present")
elif target in c:
    c = c.replace(target, replacement, 1)
    with open(path, "w", encoding="utf-8") as f:
        f.write(c)
    print("Successfully added swctrl-gpios to CANONICAL_383_dma.dts")
else:
    print("Target string not found!")
