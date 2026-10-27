# 1. Update nt36523.h
h_path = r'\\wsl.localhost\Ubuntu-24.04\home\pluto\kbuild\linux-next-tb128fu-hx83102-panel-port\drivers\input\touchscreen\nt36523.h'
with open(h_path, 'r', encoding='utf-8') as f:
    h = f.read()

old_trig = '#define INT_TRIGGER_TYPE IRQ_TYPE_EDGE_RISING'
new_trig = '#define INT_TRIGGER_TYPE IRQ_TYPE_LEVEL_LOW\nirqreturn_t nvt_ts_work_func(int irq, void *data);'
assert old_trig in h, 'old_trig not found'
h = h.replace(old_trig, new_trig, 1)

with open(h_path, 'w', encoding='utf-8', newline='\n') as f:
    f.write(h)
print('nt36523.h updated!')

# 2. Update nt36523_ts.c
ts_path = r'\\wsl.localhost\Ubuntu-24.04\home\pluto\kbuild\linux-next-tb128fu-hx83102-panel-port\drivers\input\touchscreen\nt36523_ts.c'
with open(ts_path, 'r', encoding='utf-8') as f:
    ts = f.read()

old_func = 'static irqreturn_t nvt_ts_work_func(int irq, void *data)'
new_func = 'irqreturn_t nvt_ts_work_func(int irq, void *data)'
assert old_func in ts, 'old_func not found'
ts = ts.replace(old_func, new_func, 1)

old_read = '\tif (ret < 0) {\n\t\tNVT_ERR("CTP_SPI_READ failed.(%d)\\n", ret);\n\t\tgoto XFER_ERROR;\n\t}'
new_read = '\tif (ret < 0) {\n\t\tNVT_ERR("CTP_SPI_READ failed.(%d)\\n", ret);\n\t\tgoto XFER_ERROR;\n\t}\n\tNVT_LOG("work_func: irq=%d, gpio=%d, p1=0x%02X 0x%02X 0x%02X\\n", irq, gpio_get_value(ts->irq_gpio), point_data[1], point_data[2], point_data[3]);'
assert old_read in ts, 'old_read not found'
ts = ts.replace(old_read, new_read, 1)

old_touch = '\t\t\tinput_w = (uint32_t)(point_data[position + 4]);'
new_touch = '\t\t\tinput_w = (uint32_t)(point_data[position + 4]);\n\t\t\tNVT_LOG("TOUCH EVENT: id=%d x=%d y=%d\\n", input_id, input_x, input_y);'
assert old_touch in ts, 'old_touch not found'
ts = ts.replace(old_touch, new_touch, 1)

with open(ts_path, 'w', encoding='utf-8', newline='\n') as f:
    f.write(ts)
print('nt36523_ts.c updated!')

# 3. Update nt36523_fw_update.c
fw_path = r'\\wsl.localhost\Ubuntu-24.04\home\pluto\kbuild\linux-next-tb128fu-hx83102-panel-port\drivers\input\touchscreen\nt36523_fw_update.c'
with open(fw_path, 'r', encoding='utf-8') as f:
    fw = f.read()

old_boot = 'void Boot_Update_Firmware(struct work_struct *work)\n{\n\tmutex_lock(&ts->lock);\n\tnvt_update_firmware(ts->fw_name);\n\tdisable_pen_input_device(false);\n\tnvt_get_fw_info();\n\tmutex_unlock(&ts->lock);\n}'
new_boot = 'void Boot_Update_Firmware(struct work_struct *work)\n{\n\tmutex_lock(&ts->lock);\n\tnvt_update_firmware(ts->fw_name);\n\tdisable_pen_input_device(false);\n\tnvt_get_fw_info();\n\tmutex_unlock(&ts->lock);\n\n\tNVT_LOG("Boot_Update_Firmware done, gpio%d before drain = %d\\n", ts->irq_gpio, gpio_get_value(ts->irq_gpio));\n\tnvt_ts_work_func(ts->client->irq, ts);\n\tNVT_LOG("Boot_Update_Firmware done, gpio%d after drain = %d\\n", ts->irq_gpio, gpio_get_value(ts->irq_gpio));\n}'
assert old_boot in fw, 'old_boot not found'
fw = fw.replace(old_boot, new_boot, 1)

with open(fw_path, 'w', encoding='utf-8', newline='\n') as f:
    f.write(fw)
print('nt36523_fw_update.c updated!')
