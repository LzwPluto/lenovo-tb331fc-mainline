import glob
import os
import re

dts_dir = r"\\wsl.localhost\Ubuntu-24.04\home\pluto\kbuild\linux-next-tb128fu-hx83102-panel-port\arch\arm64\boot\dts\qcom"
matches = glob.glob(os.path.join(dts_dir, "*sm6115*.dts*")) + glob.glob(os.path.join(dts_dir, "*sm6225*.dts*")) + glob.glob(os.path.join(dts_dir, "*qrb4210*.dts*"))

print("Found DTS files:", [os.path.basename(m) for m in matches])
for fpath in matches:
    with open(fpath, "r", encoding="utf-8") as f:
        c = f.read()
    if 'sound' in c:
        print(f"\n=== sound in {os.path.basename(fpath)} ===")
        idx = c.find('sound')
        print(c[idx:idx+600])
