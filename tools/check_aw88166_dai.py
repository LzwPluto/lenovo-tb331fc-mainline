path = r"\\wsl.localhost\Ubuntu-24.04\home\pluto\kbuild\linux-next-tb128fu-hx83102-panel-port\sound\soc\codecs\aw88166.c"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

import re
m = re.search(r'struct snd_soc_dai_driver\s+[a-zA-Z0-9_]+\s*=\s*\{[^;]+\};', text)
if m:
    print("DAI driver:")
    print(m.group(0))
else:
    print("snd_soc_dai_driver not matched")
