path = r"\\wsl.localhost\Ubuntu-24.04\home\pluto\kbuild\linux-next-tb128fu-hx83102-panel-port\drivers\bluetooth\hci_qca.c"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

import re
matches = [l.strip() for l in text.splitlines() if 'wcn3990' in l or 'sw_ctrl' in l.lower() or 'enable-gpio' in l.lower() or 'supply' in l.lower()]
print(f"Matching lines in hci_qca.c: {len(matches)}")
for l in matches[:30]:
    print("  ", l)
