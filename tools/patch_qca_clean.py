path = '/home/pluto/kbuild/linux-next-tb128fu-hx83102-panel-port/drivers/bluetooth/hci_qca.c'
content = open(path, 'r').read()

target1 = '\thci_uart_set_flow_control(hu, false);'
rep1 = '\tqca_set_speed(hu, QCA_INIT_SPEED);\n\thci_uart_set_flow_control(hu, false);'

target2 = '\tset_bit(QCA_SUSPENDING, &qca->flags);'
rep2 = '\tif (!hu->hdev || !test_bit(HCI_RUNNING, &hu->hdev->flags))\n\t\treturn 0;\n\n\tset_bit(QCA_SUSPENDING, &qca->flags);'

if target1 in content and target2 in content:
    content = content.replace(target1, rep1, 1)
    content = content.replace(target2, rep2, 1)
    open(path, 'w').write(content)
    print('Applied hci_qca patches cleanly!')
else:
    print('Targets not found!')
