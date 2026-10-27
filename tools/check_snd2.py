path = r"\\wsl.localhost\Ubuntu-24.04\home\pluto\kbuild\linux-next-tb128fu-hx83102-panel-port\.config"
with open(path, "r", encoding="utf-8") as f:
    cfg = f.read()

for l in cfg.splitlines():
    if "CONFIG_SOUND" in l:
        print(l)
