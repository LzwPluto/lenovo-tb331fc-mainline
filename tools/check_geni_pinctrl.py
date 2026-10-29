path = r"\\wsl.localhost\Ubuntu-24.04\home\pluto\kbuild\linux-next-tb128fu-hx83102-panel-port\drivers\tty\serial\qcom_geni_serial.c"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

import re
matches = [l.strip() for l in text.splitlines() if 'pinctrl' in l.lower()]
print(f"Pinctrl lines in qcom_geni_serial.c: {len(matches)}")
for l in matches:
    print("  ", l)
