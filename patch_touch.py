import re

path = '/home/pluto/kbuild/linux-next-tb128fu-hx83102-panel-port/drivers/input/touchscreen/nt36523_ts.c'
with open(path, 'r') as f:
    s = f.read()

pattern = re.compile(r'#define POINT_DATA_LEN 65\s+/\*.*?\*/\s+irqreturn_t nvt_ts_work_func\(int irq, void \*data\)\s*\{.*?return IRQ_HANDLED;\s*\}', re.DOTALL)
m = pattern.search(s)
if not m:
    print('Pattern not matched!')
    exit(1)

replacement = '''#define POINT_DATA_LEN 65
#define NVT_TOUCH_PACKET_LEN 109
/*******************************************************
Description:
\tNovatek touchscreen work function.

return:
\tn.a.
*******************************************************/
irqreturn_t nvt_ts_work_func(int irq, void *data)
{
\tint32_t ret = -1;
\tuint8_t point_data[128] = {0};
\tuint32_t position = 0;
\tuint32_t input_x = 0;
\tuint32_t input_y = 0;
\tuint32_t input_w = 0;
\tuint32_t input_p = 0;
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
\tNVT_LOG("work_func: irq=%d, gpio=%d, p1=0x%02X 0x%02X 0x%02X, csum=0x%02X\\n",
\t\tirq, gpio_get_value(ts->irq_gpio), point_data[1], point_data[2], point_data[3], point_data[65]);

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

#if NVT_TOUCH_WDT_RECOVERY
\t/* ESD protect by WDT */
\tif (nvt_wdt_fw_recovery(point_data)) {
\t\tNVT_ERR("Recover for fw reset, %02X\\n", point_data[1]);
\t\tif (point_data[1] == 0xFD) {
\t\t\tNVT_ERR("Dump FW history:\\n");
\t\t\tnvt_dump_fw_history();
\t\t}
\t\tnvt_update_firmware(ts->fw_name);
\t\tgoto XFER_ERROR;
\t}
#endif /* #if NVT_TOUCH_WDT_RECOVERY */

\t/* ESD protect by FW handshake */
\tif (nvt_fw_recovery(point_data)) {
#if NVT_TOUCH_ESD_PROTECT
\t\tnvt_esd_check_enable(true);
#endif /* #if NVT_TOUCH_ESD_PROTECT */
\t\tgoto XFER_ERROR;
\t}

\tfinger_cnt = 0;

\tfor (i = 0; i < ts->max_touch_num; i++) {
\t\tposition = 1 + 6 * i;
\t\tinput_id = (uint8_t)(point_data[position + 0] >> 3);
\t\tif ((input_id == 0) || (input_id > ts->max_touch_num))
\t\t\tcontinue;

\t\tuint8_t status = point_data[position + 0] & 0x07;
\t\tif (status == 0x01 || status == 0x02) {
#if NVT_TOUCH_ESD_PROTECT
\t\t\t/* update interrupt timer */
\t\t\tirq_timer = jiffies;
#endif /* #if NVT_TOUCH_ESD_PROTECT */
\t\t\tinput_x = (uint32_t)((point_data[position + 1] << 8) | point_data[position + 2]);
\t\t\tinput_y = (uint32_t)((point_data[position + 3] << 8) | point_data[position + 4]);
\t\t\tinput_w = (uint32_t)(point_data[position + 5]);
\t\t\tNVT_LOG("TOUCH EVENT: id=%d x=%d y=%d w=%d\\n", input_id, input_x, input_y, input_w);
\t\t\tif (input_w == 0)
\t\t\t\tinput_w = 1;
\t\t\tinput_p = input_w;

\t\t\tpress_id[input_id - 1] = 1;
\t\t\tinput_mt_slot(ts->input_dev, input_id - 1);
\t\t\tinput_mt_report_slot_state(ts->input_dev, MT_TOOL_FINGER, true);

\t\t\ttouchscreen_report_pos(ts->input_dev, &ts->props_ts, input_x, input_y, true);

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

#if TOUCH_KEY_NUM > 0
\tif (point_data[61] == 0xF8) {
#if NVT_TOUCH_ESD_PROTECT
\t\t/* update interrupt timer */
\t\tirq_timer = jiffies;
#endif /* #if NVT_TOUCH_ESD_PROTECT */
\t\tfor (i = 0; i < ts->max_button_num; i++) {
\t\t\tinput_report_key(ts->input_dev, touch_key_array[i], ((point_data[62] >> i) & 0x01));
\t\t}
\t} else {
\t\tfor (i = 0; i < ts->max_button_num; i++) {
\t\t\tinput_report_key(ts->input_dev, touch_key_array[i], 0);
\t\t}
\t}
#endif

\tinput_sync(ts->input_dev);

\tif (ts->pen_support && ts->pen_input_dev_enable && !(ts->pen_is_charge)) {
\t\tpen_format_id = point_data[66];
\t\tif (pen_format_id == 0xFF) {
\t\t\trelease_pen_event();
\t\t} else if (pen_format_id == 0x01) {
\t\t\tpen_x = (uint32_t)((point_data[67] << 8) | point_data[68]);
\t\t\tpen_y = (uint32_t)((point_data[69] << 8) | point_data[70]);
\t\t\tif (pen_x >= ts->abs_x_max * 2 - 1) {
\t\t\t\tpen_x -= 1;
\t\t\t}
\t\t\tif (pen_y >= ts->abs_y_max * 2 - 1) {
\t\t\t\tpen_y -= 1;
\t\t\t}
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
\t\t} else if (pen_format_id == 0xF0) {
\t\t\t// report Pen ID
\t\t} else {
\t\t\tNVT_LOG("pen_format_id 0x%02X\\n", pen_format_id);
\t\t}
\t}

XFER_ERROR:

\tmutex_unlock(&ts->lock);
\treturn IRQ_HANDLED;
}'''

idx_start = m.start()
idx_end = m.end()
s = s[:idx_start] + replacement + s[idx_end:]

s = s.replace('msecs_to_jiffies(14000)', 'msecs_to_jiffies(2500)')

with open(path, 'w') as f:
    f.write(s)
print('Successfully updated nt36523_ts.c!')
