import re

path = r"\\wsl.localhost\Ubuntu-24.04\home\pluto\kbuild\linux-next-tb128fu-hx83102-panel-port\arch\arm64\boot\dts\qcom\sm6115.dtsi"
try:
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
except Exception as e:
    print("Cannot read via WSL UNC path, trying another way:", e)
    content = ""

if content:
    print("Found sm6115.dtsi, length:", len(content))
    matches = re.findall(r'([a-zA-Z0-9_\-]+@[0-9a-fA-F]+\s*\{[^}]*compatible\s*=\s*"[^"]+"[^}]*\})', content)
    for m in matches:
        if any(k in m for k in ['audio', 'sound', 'remoteproc', 'adsp', 'lpass', 'q6']):
            print("---")
            print(m[:300])
