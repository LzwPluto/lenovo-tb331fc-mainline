#!/bin/bash
# Verify the rebuilt vendor_boot: header sizes, DTB content, gadget.sh content.
cd /mnt/d/TB331FCLinux || exit 1
IMG=build/vb_noacm.img

echo "=== header / dtb ==="
python3 tools/verify_vb2.py "$IMG"

echo
echo "=== gadget.sh inside the new image ==="
T=$(mktemp -d)
python3 - "$IMG" "$T" <<'PYEOF'
import struct, sys, os, subprocess
img, tmp = sys.argv[1], sys.argv[2]
d = open(img,'rb').read()
page = struct.unpack_from('<I', d, 0x0C)[0]
vr_size = struct.unpack_from('<I', d, 0x18)[0]
open(os.path.join(tmp,'rd.cpio'),'wb').write(d[page:page+vr_size])
PYEOF
mkdir -p "$T/rd"
( cd "$T/rd" && cpio -idm --quiet < "$T/rd.cpio" 2>/dev/null )
echo "--- rndis lines (should all be commented) ---"
grep -n 'rndis' "$T/rd/gadget.sh" 2>/dev/null || echo "  (no rndis lines at all)"
echo "--- active function creation ---"
grep -nE 'mkdir -p functions|ln -sf functions' "$T/rd/gadget.sh" 2>/dev/null
echo "--- file count in ramdisk ---"
find "$T/rd" -type f | wc -l
rm -rf "$T"
