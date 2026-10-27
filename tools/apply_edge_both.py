# 1. Update nt36523.h
h_path = r'\\wsl.localhost\Ubuntu-24.04\home\pluto\kbuild\linux-next-tb128fu-hx83102-panel-port\drivers\input\touchscreen\nt36523.h'
with open(h_path, 'r', encoding='utf-8') as f:
    h = f.read()

target = '#define INT_TRIGGER_TYPE IRQ_TYPE_EDGE_RISING'
repl = '#define INT_TRIGGER_TYPE IRQ_TYPE_EDGE_BOTH'
assert target in h
h = h.replace(target, repl)

with open(h_path, 'w', encoding='utf-8', newline='\n') as f:
    f.write(h)
print('nt36523.h updated to IRQ_TYPE_EDGE_BOTH')

# 2. Update nt36523_ts.c
ts_path = r'\\wsl.localhost\Ubuntu-24.04\home\pluto\kbuild\linux-next-tb128fu-hx83102-panel-port\drivers\input\touchscreen\nt36523_ts.c'
with open(ts_path, 'r', encoding='utf-8') as f:
    ts = f.read()

log_target = '\tinput_report_key(ts->input_dev, BTN_TOUCH, (finger_cnt > 0));\n\tinput_sync(ts->input_dev);'
log_repl = '''\tinput_report_key(ts->input_dev, BTN_TOUCH, (finger_cnt > 0));
\tinput_sync(ts->input_dev);
\tNVT_LOG("touch_irq: p1=0x%02X p66=0x%02X cnt=%d\\n", point_data[1], point_data[66], finger_cnt);'''

assert log_target in ts
ts = ts.replace(log_target, log_repl, 1)

with open(ts_path, 'w', encoding='utf-8', newline='\n') as f:
    f.write(ts)
print('nt36523_ts.c updated with touch_irq logging')
