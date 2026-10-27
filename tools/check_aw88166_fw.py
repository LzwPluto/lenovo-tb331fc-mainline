path = r"\\wsl.localhost\Ubuntu-24.04\home\pluto\kbuild\linux-next-tb128fu-hx83102-panel-port\sound\soc\codecs\aw88166.c"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

import re
matches = [l.strip() for l in text.splitlines() if 'request_firmware' in l or 'acf' in l.lower() or 'bin' in l.lower()]
print(f"Firmware lines: {len(matches)}")
for l in matches[:15]:
    print("  ", l)
