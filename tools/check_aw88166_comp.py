path = r"\\wsl.localhost\Ubuntu-24.04\home\pluto\kbuild\linux-next-tb128fu-hx83102-panel-port\sound\soc\codecs\aw88166.c"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

import re
matches = [l.strip() for l in text.splitlines() if 'register_component' in l or 'dai' in l.lower()]
print(f"Lines mentioning dai or register_component: {len(matches)}")
for l in matches[:20]:
    print("  ", l)
