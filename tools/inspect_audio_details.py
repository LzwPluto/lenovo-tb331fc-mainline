import re

dmesg_path = r"D:\TB331FCLinux\ref\android\android-dmesg.txt"
with open(dmesg_path, "r", encoding="utf-16", errors="ignore") as f:
    dmesg = f.read()

print("==================== AUDIO IN DMESG ====================")
audio_lines = [l for l in dmesg.splitlines() if any(k in l.lower() for k in ['bengal-asoc', 'aw883xx', 'soundcard', 'snd_soc', 'audio-prm', 'q6dsp', 'wcd', 'bolero'])]
print(f"Total matching audio lines: {len(audio_lines)}")
for l in audio_lines[:30]:
    print(l)

print("\n==================== SOUND CARD IN VENDOR DTS ====================")
with open(r"D:\TB331FCLinux\ref\android\vendor.dts", "r", encoding="utf-8", errors="ignore") as f:
    dts = f.read()

# Search for sound / asoc / soundcard nodes
sound_matches = re.finditer(r'sound\s*\{[^}]*compatible\s*=\s*"([^"]+)"[^}]*\}', dts)
for m in sound_matches:
    print("Sound node:", m.group(0)[:500])

snd_matches = [l for l in dts.splitlines() if 'sound' in l.lower() or 'audio' in l.lower() or 'qcom,model' in l.lower()]
print(f"Lines mentioning sound/audio in vendor DTS: {len(snd_matches)}")
for l in snd_matches[:20]:
    print("  ", l.strip())
