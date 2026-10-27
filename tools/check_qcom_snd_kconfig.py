path = r"\\wsl.localhost\Ubuntu-24.04\home\pluto\kbuild\linux-next-tb128fu-hx83102-panel-port\sound\soc\qcom\Kconfig"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

import re
configs = re.findall(r'config\s+([A-Z0-9_]+)', text)
print("Configs in sound/soc/qcom/Kconfig:")
for c in configs:
    if any(k in c for k in ['8250', 'QDSP', 'QCOM', 'COMMON', 'SM6115', 'RB2', 'LPASS', 'BCONFIG']):
        print("  CONFIG_" + c)
