import os

path = r'\\wsl.localhost\Ubuntu-24.04\home\pluto\kbuild\linux-next-tb128fu-hx83102-panel-port\drivers\bluetooth\hci_qca.c'
with open(path, 'r', encoding='utf-8') as f:
    s = f.read()

target = """\tret = serdev_device_open(hu->serdev);
\tif (ret) {
\t\tbt_dev_err(hu->hdev, "failed to open port");
\t\treturn ret;
\t}

\thci_uart_set_flow_control(hu, false);"""

repl = """\tret = serdev_device_open(hu->serdev);
\tif (ret) {
\t\tbt_dev_err(hu->hdev, "failed to open port");
\t\treturn ret;
\t}

\tqca_set_speed(hu, QCA_INIT_SPEED);
\thci_uart_set_flow_control(hu, false);"""

if target in s:
    with open(path, 'w', encoding='utf-8') as f:
        f.write(s.replace(target, repl, 1))
    print("SUCCESS: patched hci_qca.c")
else:
    print("TARGET NOT FOUND in hci_qca.c")
