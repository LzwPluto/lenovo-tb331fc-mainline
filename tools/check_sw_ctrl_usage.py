path = r"\\wsl.localhost\Ubuntu-24.04\home\pluto\kbuild\linux-next-tb128fu-hx83102-panel-port\drivers\bluetooth\hci_qca.c"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

idx = text.find("qcadev->sw_ctrl")
while idx != -1:
    line_start = text.rfind('\n', 0, idx)
    line_end = text.find('\n', idx)
    print(text[line_start:line_end].strip())
    idx = text.find("qcadev->sw_ctrl", idx + 1)
