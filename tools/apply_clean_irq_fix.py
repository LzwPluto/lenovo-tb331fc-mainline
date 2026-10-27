import os

# 1. Update nt36523.h
h_path = r'\\wsl.localhost\Ubuntu-24.04\home\pluto\kbuild\linux-next-tb128fu-hx83102-panel-port\drivers\input\touchscreen\nt36523.h'
with open(h_path, 'r', encoding='utf-8') as f:
    h = f.read()

# Make sure INT_TRIGGER_TYPE is IRQ_TYPE_EDGE_RISING
if '#define INT_TRIGGER_TYPE IRQ_TYPE_EDGE_BOTH' in h:
    h = h.replace('#define INT_TRIGGER_TYPE IRQ_TYPE_EDGE_BOTH', '#define INT_TRIGGER_TYPE IRQ_TYPE_EDGE_RISING')

# Add restore function prototypes if not present
if 'int32_t nvt_restore_cmd_func(void);' not in h:
    h += '''
int32_t nvt_cmd_store(uint8_t cmd);
int32_t nvt_ext_cmd_store(uint8_t cmd, uint8_t data);
int32_t nvt_restore_cmd_func(void);
'''

with open(h_path, 'w', encoding='utf-8', newline='\n') as f:
    f.write(h)
print("nt36523.h updated!")

# 2. Update nt36523_fw_update.c
fw_path = r'\\wsl.localhost\Ubuntu-24.04\home\pluto\kbuild\linux-next-tb128fu-hx83102-panel-port\drivers\input\touchscreen\nt36523_fw_update.c'
with open(fw_path, 'r', encoding='utf-8') as f:
    fw = f.read()

# Make sure Boot_Update_Firmware calls nvt_restore_cmd_func without polling
old_boot = '''void Boot_Update_Firmware(struct work_struct *work)
{
\tmutex_lock(&ts->lock);
\tnvt_update_firmware(ts->fw_name);
\tdisable_pen_input_device(false);
\tnvt_get_fw_info();
\tmutex_unlock(&ts->lock);
}'''

new_boot = '''void Boot_Update_Firmware(struct work_struct *work)
{
\tmutex_lock(&ts->lock);
\tnvt_update_firmware(ts->fw_name);
\tnvt_get_fw_info();
\tnvt_set_page(ts->mmap->EVENT_BUF_ADDR);
\tmutex_unlock(&ts->lock);

\t/* TB331FC: Send restore commands (0xBA, 0x7F, 0x79, 0x7B) to kick controller into active scanning mode */
\tnvt_restore_cmd_func();

\tNVT_LOG("Boot_Update_Firmware done, gpio%d before drain = %d\\n", ts->irq_gpio, gpio_get_value(ts->irq_gpio));
\tnvt_ts_work_func(ts->client->irq, ts);
\tNVT_LOG("Boot_Update_Firmware done, gpio%d after drain = %d\\n", ts->irq_gpio, gpio_get_value(ts->irq_gpio));
}'''

if old_boot in fw:
    fw = fw.replace(old_boot, new_boot, 1)

with open(fw_path, 'w', encoding='utf-8', newline='\n') as f:
    f.write(fw)
print("nt36523_fw_update.c updated!")

# 3. Update nt36523_ts.c
ts_path = r'\\wsl.localhost\Ubuntu-24.04\home\pluto\kbuild\linux-next-tb128fu-hx83102-panel-port\drivers\input\touchscreen\nt36523_ts.c'
with open(ts_path, 'r', encoding='utf-8') as f:
    ts = f.read()

# Replace nvt_ts_work_func
start_marker = "irqreturn_t nvt_ts_work_func(int irq, void *data)\n{\n"
end_marker = "static int8_t nvt_ts_check_chip_ver_trim(uint32_t chip_ver_trim_addr)"
start_idx = ts.index(start_marker)
end_idx = ts.index(end_marker)

new_work_func = """irqreturn_t nvt_ts_work_func(int irq, void *data)
{
\tstruct nvt_ts_data *ts = (struct nvt_ts_data *)data;
\tint32_t ret = -1;
\tuint8_t point_data[NVT_TOUCH_PACKET_LEN + 1] = {0};
\tuint32_t position = 0;
\tuint32_t input_x = 0;
\tuint32_t input_y = 0;
\tuint32_t input_w = 0;
\tuint8_t input_id = 0;
\tuint8_t press_id[TOUCH_MAX_FINGER_NUM] = {0};
\tint32_t i = 0;
\tint32_t finger_cnt = 0;
\tuint8_t pen_format_id = 0;
\tuint32_t pen_x = 0;
\tuint32_t pen_y = 0;
\tuint32_t pen_pressure = 0;
\tuint32_t pen_distance = 0;
\tint8_t pen_tilt_x = 0;
\tint8_t pen_tilt_y = 0;
\tuint32_t pen_btn1 = 0;
\tuint32_t pen_btn2 = 0;
\tuint32_t pen_battery = 0;
\tuint32_t csum = 0;

\tmutex_lock(&ts->lock);

\tif (ts->dev_pm_suspend) {
\t\tret = wait_for_completion_timeout(&ts->dev_pm_suspend_completion, msecs_to_jiffies(500));
\t\tif (!ret) {
\t\t\tNVT_ERR("system(spi) can't finished resuming procedure, skip it\\n");
\t\t\tgoto XFER_ERROR;
\t\t}
\t}

\tnvt_set_page(ts->mmap->EVENT_BUF_ADDR);
\tpoint_data[0] = (ts->mmap->EVENT_BUF_ADDR) & 0x7F;
\tret = CTP_SPI_READ(ts->client, point_data, NVT_TOUCH_PACKET_LEN);
\tif (ret < 0) {
\t\tNVT_ERR("CTP_SPI_READ failed.(%d)\\n", ret);
\t\tgoto XFER_ERROR;
\t}

\t/* Vendor idle / wake packet (all 0x77) */
\tif (point_data[1] == 0x77 && point_data[2] == 0x77 && point_data[3] == 0x77 &&
\t    point_data[4] == 0x77 && point_data[5] == 0x77 && point_data[6] == 0x77) {
\t\tgoto XFER_ERROR;
\t}

#if NVT_TOUCH_WDT_RECOVERY
\t/* Controller WDT reset recovery (0xFD / 0xFE) */
\tif ((point_data[1] == 0xFD || point_data[1] == 0xFE) &&
\t    (point_data[2] == 0xFD || point_data[2] == 0xFE) &&
\t    (point_data[3] == 0xFD || point_data[3] == 0xFE)) {
\t\tif (nvt_wdt_fw_recovery(point_data)) {
\t\t\tNVT_ERR("Recover for fw reset, 0x%02X\\n", point_data[1]);
\t\t\tnvt_update_firmware(ts->fw_name);
\t\t\tnvt_restore_cmd_func();
\t\t}
\t\tgoto XFER_ERROR;
\t}
#endif

\t/* Boot / initial drain packet */
\tif (point_data[1] == 0xFF && point_data[2] == 0x00) {
\t\tgoto XFER_ERROR;
\t}

\t/* Checksum verification (64 bytes touch buffer) */
\tcsum = 0;
\tfor (i = 0; i < 64; i++) {
\t\tcsum += point_data[1 + i];
\t}
\tif (((uint8_t)(-csum)) != point_data[65]) {
\t\tNVT_LOG("packet csum mismatch: calc=0x%02X != 0x%02X, raw: %*ph\\n",
\t\t\t(uint8_t)(-csum), point_data[65], 8, point_data + 1);
\t\tgoto XFER_ERROR;
\t}

\tif (!bTouchIsAwake) {
\t\tgoto XFER_ERROR;
\t}

\t/* Touch coordinates processing */
\tfinger_cnt = 0;
\tfor (i = 0; i < ts->max_touch_num; i++) {
\t\tposition = 1 + 6 * i;
\t\tinput_id = (uint8_t)(point_data[position + 0] >> 3);
\t\tif ((input_id == 0) || (input_id > ts->max_touch_num))
\t\t\tcontinue;

\t\tuint8_t status = point_data[position + 0] & 0x07;
\t\tif (status == 0x01 || status == 0x02) {
\t\t\tinput_x = (uint32_t)((point_data[position + 1] << 8) | point_data[position + 2]);
\t\t\tinput_y = (uint32_t)((point_data[position + 3] << 8) | point_data[position + 4]);
\t\t\tinput_w = (uint32_t)(point_data[position + 5]);
\t\t\tif (input_w == 0)
\t\t\t\tinput_w = 1;

\t\t\tpress_id[input_id - 1] = 1;
\t\t\tinput_mt_slot(ts->input_dev, input_id - 1);
\t\t\tinput_mt_report_slot_state(ts->input_dev, MT_TOOL_FINGER, true);
\t\t\ttouchscreen_report_pos(ts->input_dev, &ts->props_ts, input_x, input_y, true);
\t\t\tinput_report_abs(ts->input_dev, ABS_MT_TOUCH_MAJOR, input_w);
\t\t\tinput_report_abs(ts->input_dev, ABS_MT_PRESSURE, input_w);
\t\t\tfinger_cnt++;
\t\t}
\t}

\tfor (i = 0; i < ts->max_touch_num; i++) {
\t\tif (press_id[i] != 1) {
\t\t\tinput_mt_slot(ts->input_dev, i);
\t\t\tinput_report_abs(ts->input_dev, ABS_MT_TOUCH_MAJOR, 0);
\t\t\tinput_report_abs(ts->input_dev, ABS_MT_PRESSURE, 0);
\t\t\tinput_mt_report_slot_state(ts->input_dev, MT_TOOL_FINGER, false);
\t\t}
\t}

\tinput_report_key(ts->input_dev, BTN_TOUCH, (finger_cnt > 0));
\tinput_sync(ts->input_dev);

\t/* Stylus Pen processing */
\tif (ts->pen_support && ts->pen_input_dev_enable && !(ts->pen_is_charge)) {
\t\tpen_format_id = point_data[66];
\t\tif (pen_format_id == 0x01) {
\t\t\tpen_x = (uint32_t)((point_data[67] << 8) | point_data[68]);
\t\t\tpen_y = (uint32_t)((point_data[69] << 8) | point_data[70]);
\t\t\tif (pen_x >= ts->abs_x_max * 2 - 1)
\t\t\t\tpen_x -= 1;
\t\t\tif (pen_y >= ts->abs_y_max * 2 - 1)
\t\t\t\tpen_y -= 1;
\t\t\tpen_pressure = (uint32_t)((point_data[71] << 8) | point_data[72]);
\t\t\tpen_tilt_x = (int32_t)(int8_t)point_data[73];
\t\t\tpen_tilt_y = (int32_t)(int8_t)point_data[74];
\t\t\tpen_distance = (uint32_t)((point_data[75] << 8) | point_data[76]);
\t\t\tpen_btn1 = (uint32_t)(point_data[77] & 0x01);
\t\t\tpen_btn2 = (uint32_t)((point_data[77] >> 1) & 0x01);
\t\t\tpen_battery = (uint32_t)point_data[78];

\t\t\tinput_report_abs(ts->pen_input_dev, ABS_X, pen_x);
\t\t\tinput_report_abs(ts->pen_input_dev, ABS_Y, pen_y);
\t\t\tinput_report_abs(ts->pen_input_dev, ABS_PRESSURE, pen_pressure);
\t\t\tinput_report_key(ts->pen_input_dev, BTN_TOUCH, !!pen_pressure);
\t\t\tinput_report_abs(ts->pen_input_dev, ABS_TILT_X, pen_tilt_x);
\t\t\tinput_report_abs(ts->pen_input_dev, ABS_TILT_Y, pen_tilt_y);
\t\t\tinput_report_abs(ts->pen_input_dev, ABS_DISTANCE, pen_distance);
\t\t\tinput_report_key(ts->pen_input_dev, BTN_TOOL_PEN, !!pen_distance || !!pen_pressure);
\t\t\tinput_report_key(ts->pen_input_dev, BTN_STYLUS, pen_btn1);
\t\t\tinput_report_key(ts->pen_input_dev, BTN_STYLUS2, pen_btn2);
\t\t\tinput_sync(ts->pen_input_dev);
\t\t} else if (pen_format_id == 0xFF) {
\t\t\trelease_pen_event();
\t\t} else if (pen_format_id == 0xF0) {
\t\t\tinput_sync(ts->pen_input_dev);
\t\t}
\t}

XFER_ERROR:
\tmutex_unlock(&ts->lock);
\treturn IRQ_HANDLED;
}

/*******************************************************
Description:
\tNovatek touchscreen check chip version trim function.

return:
\tExecutive outcomes. 0---NVT IC. -1---not NVT IC.
*******************************************************/
"""

ts = ts[:start_idx] + new_work_func + ts[end_idx:]

# Insert restore commands implementations before static void nvt_suspend_work
cmd_impl = '''int32_t nvt_cmd_store(uint8_t cmd)
{
\tuint8_t buf[4] = {0};
\tint32_t ret = 0, retry = 0;

\tif (!ts)
\t\treturn -ENODEV;

\tmutex_lock(&ts->lock);
\tret = nvt_set_page(ts->mmap->EVENT_BUF_ADDR | EVENT_MAP_HOST_CMD);
\tif (ret < 0) {
\t\tNVT_ERR("set page failed (%d)\\n", ret);
\t\tgoto out;
\t}

\tfor (retry = 0; retry < 5; retry++) {
\t\tbuf[0] = EVENT_MAP_HOST_CMD;
\t\tbuf[1] = cmd;
\t\tret = CTP_SPI_WRITE(ts->client, buf, 2);
\t\tif (ret < 0) {
\t\t\tNVT_ERR("write cmd 0x%02X failed (%d)\\n", cmd, ret);
\t\t\tbreak;
\t\t}
\t\tmsleep(20);

\t\tbuf[0] = EVENT_MAP_HOST_CMD;
\t\tbuf[1] = 0xFF;
\t\tret = CTP_SPI_READ(ts->client, buf, 2);
\t\tif (ret == 0 && buf[1] == 0x00) {
\t\t\tNVT_LOG("send Cmd 0x%02X success, tried %d times\\n", cmd, retry);
\t\t\tbreak;
\t\t}
\t}

\tif (retry >= 5) {
\t\tNVT_ERR("send Cmd 0x%02X failed, tried %d times (ret=%d, buf[1]=0x%02X)\\n",
\t\t\tcmd, retry, ret, buf[1]);
\t\tret = -EIO;
\t}

\tnvt_set_page(ts->mmap->EVENT_BUF_ADDR);

out:
\tmutex_unlock(&ts->lock);
\treturn ret;
}

int32_t nvt_ext_cmd_store(uint8_t cmd, uint8_t data)
{
\tuint8_t buf[4] = {0};
\tint32_t ret = 0, retry = 0;

\tif (!ts)
\t\treturn -ENODEV;

\tmutex_lock(&ts->lock);
\tret = nvt_set_page(ts->mmap->EVENT_BUF_ADDR | EVENT_MAP_HOST_CMD);
\tif (ret < 0) {
\t\tNVT_ERR("set page failed (%d)\\n", ret);
\t\tgoto out;
\t}

\tfor (retry = 0; retry < 5; retry++) {
\t\tbuf[0] = EVENT_MAP_HOST_CMD;
\t\tbuf[1] = cmd;
\t\tbuf[2] = data;
\t\tret = CTP_SPI_WRITE(ts->client, buf, 3);
\t\tif (ret < 0) {
\t\t\tNVT_ERR("write ext cmd 0x%02X failed (%d)\\n", cmd, ret);
\t\t\tbreak;
\t\t}
\t\tmsleep(20);

\t\tbuf[0] = EVENT_MAP_HOST_CMD;
\t\tbuf[1] = 0xFF;
\t\tret = CTP_SPI_READ(ts->client, buf, 2);
\t\tif (ret == 0 && buf[1] == 0x00) {
\t\t\tNVT_LOG("send Cmd 0x%02X 0x%02X success, tried %d times\\n", cmd, data, retry);
\t\t\tbreak;
\t\t}
\t}

\tif (retry >= 5) {
\t\tNVT_ERR("send Cmd 0x%02X 0x%02X failed, tried %d times (ret=%d, buf[1]=0x%02X)\\n",
\t\t\tcmd, data, retry, ret, buf[1]);
\t\tret = -EIO;
\t}

\tnvt_set_page(ts->mmap->EVENT_BUF_ADDR);

out:
\tmutex_unlock(&ts->lock);
\treturn ret;
}

int32_t nvt_restore_cmd_func(void)
{
\tuint8_t buf[12] = {0};
\tint32_t ret = 0, retry = 0;

\tif (!ts)
\t\treturn -ENODEV;

\tNVT_LOG("nvt_restore_cmd_func++\\n");

\t/* 1. Host Cmd 0xBA: Start active touch sensor scanning */
\tret = nvt_cmd_store(0xBA);
\tif (ret < 0)
\t\tNVT_ERR("send Cmd 0xBA failed! (%d)\\n", ret);

\t/* 2. Host Cmd 0x7F 0x01: Edge grid zone */
\tmutex_lock(&ts->lock);
\tnvt_set_page(ts->mmap->EVENT_BUF_ADDR | EVENT_MAP_HOST_CMD);
\tbuf[0] = EVENT_MAP_HOST_CMD;
\tbuf[1] = 0x7F;
\tbuf[2] = 0x01;
\tfor (retry = 0; retry < 5; retry++) {
\t\tCTP_SPI_WRITE(ts->client, buf, 9);
\t\tmsleep(20);
\t\tbuf[0] = EVENT_MAP_HOST_CMD;
\t\tbuf[1] = 0xFF;
\t\tret = CTP_SPI_READ(ts->client, buf, 2);
\t\tif (ret == 0 && buf[1] == 0x00) {
\t\t\tNVT_LOG("send Cmd 0x7F 0x01 success, tried %d times\\n", retry);
\t\t\tbreak;
\t\t}
\t}
\tnvt_set_page(ts->mmap->EVENT_BUF_ADDR);
\tmutex_unlock(&ts->lock);

\t/* 3. Host Ext Cmd 0x79 0x00: Normal game/operation mode */
\tret = nvt_ext_cmd_store(0x79, 0x00);
\tif (ret < 0)
\t\tNVT_ERR("send Cmd 0x79 0x00 failed! (%d)\\n", ret);

\t/* 4. Host Ext Cmd 0x7B 0x01: Support Pen */
\tif (ts->pen_support) {
\t\tret = nvt_ext_cmd_store(0x7B, 0x01);
\t\tif (ret < 0)
\t\t\tNVT_ERR("send Cmd 0x7B 0x01 failed! (%d)\\n", ret);
\t}

\tNVT_LOG("nvt_restore_cmd_func--\\n");
\treturn ret;
}

'''
if 'int32_t nvt_restore_cmd_func(void)' not in ts:
    susp = 'static void nvt_suspend_work(struct work_struct *work)'
    assert susp in ts
    ts = ts.replace(susp, cmd_impl + susp, 1)

# In nvt_ts_probe: call nvt_restore_cmd_func() before bTouchIsAwake = 1;
probe_wake = '\tbTouchIsAwake = 1;\n\tNVT_LOG("end\\n");\n\n\tnvt_irq_enable(true);'
probe_wake_new = '\tnvt_restore_cmd_func();\n\tbTouchIsAwake = 1;\n\tNVT_LOG("end\\n");\n\n\tnvt_irq_enable(true);'
if probe_wake in ts:
    ts = ts.replace(probe_wake, probe_wake_new, 1)

# In nvt_ts_resume: call nvt_restore_cmd_func()
resume_pen = '\tdisable_pen_input_device(false);'
resume_pen_new = '\tnvt_restore_cmd_func();\n\tdisable_pen_input_device(false);'
if resume_pen in ts:
    ts = ts.replace(resume_pen, resume_pen_new, 1)

with open(ts_path, 'w', encoding='utf-8', newline='\n') as f:
    f.write(ts)
print("nt36523_ts.c updated cleanly!")
