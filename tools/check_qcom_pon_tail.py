path = r"\\wsl.localhost\Ubuntu-24.04\home\pluto\kbuild\linux-next-tb128fu-hx83102-panel-port\drivers\power\reset\qcom-pon.c"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

idx = text.find("pm8916_pon_probe")
print(text[idx+400:idx+1200])
