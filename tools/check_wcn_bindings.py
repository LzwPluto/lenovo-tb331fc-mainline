import glob
import os

dts_dir = r"\\wsl.localhost\Ubuntu-24.04\home\pluto\kbuild\linux-next-tb128fu-hx83102-panel-port\arch\arm64\boot\dts\qcom"
matches = glob.glob(os.path.join(dts_dir, "*sm6115*.dts*")) + glob.glob(os.path.join(dts_dir, "*qrb4210*.dts*")) + glob.glob(os.path.join(dts_dir, "*sm6225*.dts*"))

for fpath in matches:
    with open(fpath, "r", encoding="utf-8") as f:
        c = f.read()
    if 'wcn3990-bt' in c:
        idx = c.find('wcn3990-bt')
        start = c.rfind('{', 0, idx)
        end = c.find('};', idx)
        print(f"=== {os.path.basename(fpath)} ===")
        print(c[start-10:end+2])
