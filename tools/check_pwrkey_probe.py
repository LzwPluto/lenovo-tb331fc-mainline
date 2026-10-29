path = r"\\wsl.localhost\Ubuntu-24.04\home\pluto\kbuild\linux-next-tb128fu-hx83102-panel-port\drivers\input\misc\pm8941-pwrkey.c"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

idx = text.find("pm8941_pwrkey_probe")
print(text[idx-50:idx+800])
