dts_path = r"D:\TB331FCLinux\build\CANONICAL_383_dma.dts"

with open(dts_path, "r", encoding="utf-8") as f:
    text = f.read()

# Replace sy6974-int-default-state with hall-sensor-default-state
text = text.replace("sy6974-int-default-state {", "hall-sensor-default-state {")

# Remove sy6974-en-state
import re
text = re.sub(r'\tsy6974-en-state\s*\{[^}]+\};\s*', '', text)

with open(dts_path, "w", encoding="utf-8") as f:
    f.write(text)

print("Renamed sy6974-int-default-state to hall-sensor-default-state and removed sy6974-en-state")
