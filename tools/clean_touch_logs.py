p = '/home/pluto/kbuild/linux-next-tb128fu-hx83102-panel-port/drivers/input/touchscreen/nt36523_ts.c'
s = open(p).read()
s = s.replace('NVT_LOG("touch: cnt=%d', '// NVT_LOG("touch: cnt=%d')
s = s.replace('NVT_LOG("HB int=%d', '// NVT_LOG("HB int=%d')
open(p, 'w').write(s)
print('Done clean_touch_logs')
