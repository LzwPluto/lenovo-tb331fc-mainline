path = r"\\wsl.localhost\Ubuntu-24.04\home\pluto\kbuild\linux-next-tb128fu-hx83102-panel-port\.config"
with open(path, "r", encoding="utf-8") as f:
    cfg = f.read()

for l in cfg.splitlines():
    if any(k in l for k in ['CONFIG_SOUND', 'CONFIG_SND_SOC', 'CONFIG_SND']):
        if not l.startswith('#') and '=y' in l or '=m' in l:
            print(l)
