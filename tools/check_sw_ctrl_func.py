path = r"\\wsl.localhost\Ubuntu-24.04\home\pluto\kbuild\linux-next-tb128fu-hx83102-panel-port\drivers\bluetooth\hci_qca.c"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

idx = text.find("sw_ctrl_state")
print(text[idx-200:idx+600])
