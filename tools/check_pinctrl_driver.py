path = r"\\wsl.localhost\Ubuntu-24.04\home\pluto\kbuild\linux-next-tb128fu-hx83102-panel-port\drivers\pinctrl\qcom\pinctrl-sm6115.c"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

import re
matches = [l.strip() for l in text.splitlines() if 'gpio8' in l or 'gpio9' in l or 'gpio10' in l or 'gpio11' in l or 'qup3' in l]
print(f"Matches in pinctrl-sm6115.c: {len(matches)}")
for l in matches[:30]:
    print("  ", l)
