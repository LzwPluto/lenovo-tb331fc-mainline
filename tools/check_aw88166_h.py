path = r"\\wsl.localhost\Ubuntu-24.04\home\pluto\kbuild\linux-next-tb128fu-hx83102-panel-port\sound\soc\codecs\aw88166.h"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

for l in text.splitlines():
    if "ACF" in l:
        print(l)
