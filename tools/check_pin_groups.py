path = r"\\wsl.localhost\Ubuntu-24.04\home\pluto\kbuild\linux-next-tb128fu-hx83102-panel-port\drivers\pinctrl\qcom\pinctrl-sm6115.c"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

for g in ["PINGROUP(8,", "PINGROUP(9,", "PINGROUP(10,", "PINGROUP(11,"]:
    idx = text.find(g)
    if idx != -1:
        end = text.find(")", idx)
        print(text[idx:end+1])
