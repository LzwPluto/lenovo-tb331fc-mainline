path = r"\\wsl.localhost\Ubuntu-24.04\home\pluto\kbuild\linux-next-tb128fu-hx83102-panel-port\sound\soc\qcom\sm8250.c"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

idx = text.find("static int sm8250_platform_probe")
print(text[idx:idx+1200])
