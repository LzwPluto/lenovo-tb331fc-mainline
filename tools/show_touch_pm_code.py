path = r"\\wsl.localhost\Ubuntu-24.04\home\pluto\kbuild\linux-next-tb128fu-hx83102-panel-port\drivers\input\touchscreen\nt36523_ts.c"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

idx = text.find("static int32_t nvt_ts_suspend(struct device *dev)")
idx2 = text.find("static int32_t nvt_ts_resume(struct device *dev)")
idx3 = text.find("static const struct dev_pm_ops nvt_ts_dev_pm_ops", idx2)

print("=== SUSPEND ===")
print(text[idx:idx+1000])

print("\n=== RESUME ===")
print(text[idx2:idx2+1200])
