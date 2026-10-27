path = r"\\wsl.localhost\Ubuntu-24.04\home\pluto\kbuild\linux-next-tb128fu-hx83102-panel-port\drivers\input\touchscreen\nt36523_ts.c"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

import re
matches = [l.strip() for l in text.splitlines() if 'suspend' in l.lower() or 'resume' in l.lower()]
print(f"Suspend/resume lines in nt36523_ts.c: {len(matches)}")
for l in matches[:20]:
    print("  ", l)
