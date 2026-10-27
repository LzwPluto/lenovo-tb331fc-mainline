import os
import re

dts_dir = r"\\wsl.localhost\Ubuntu-24.04\home\pluto\kbuild\linux-next-tb128fu-hx83102-panel-port\arch\arm64\boot\dts\qcom"

for fname in ['sm6115p-lenovo-j606f.dts', 'sm6115-fxtec-pro1x.dts', 'qrb4210-rb2.dts']:
    fpath = os.path.join(dts_dir, fname)
    with open(fpath, "r", encoding="utf-8") as f:
        c = f.read()
    
    # search for soundcard or sound { ... }
    m = re.search(r'sound\s*\{[^}]*compatible\s*=\s*"([^"]+)"', c)
    if m:
        print(f"{fname} has sound compatible:", m.group(1))
        # print sound node
        start = m.start()
        end = c.find('};', start)
        print(c[start:end+2])
    else:
        print(f"{fname} has no direct sound {{ compatible = ... }}")
