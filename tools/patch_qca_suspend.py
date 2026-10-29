path = r"\\wsl.localhost\Ubuntu-24.04\home\pluto\kbuild\linux-next-tb128fu-hx83102-panel-port\drivers\bluetooth\hci_qca.c"
with open(path, "r", encoding="utf-8") as f:
    c = f.read()

target = "\tset_bit(QCA_SUSPENDING, &qca->flags);"
replacement = "\tif (!hu->hdev || !test_bit(HCI_RUNNING, &hu->hdev->flags))\n\t\treturn 0;\n\n\tset_bit(QCA_SUSPENDING, &qca->flags);"

if target in c:
    c = c.replace(target, replacement, 1)
    with open(path, "w", encoding="utf-8") as f:
        f.write(c)
    print("Patched qca_suspend successfully")
else:
    print("Target not found or already patched")
