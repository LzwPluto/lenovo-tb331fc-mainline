#!/bin/bash
# Fetch the .apk files for a package set (recursively) into apks/, using the
# versions already recorded in the stage root's installed database.
set -e
cd /mnt/d/TB331FCLinux/rootfs/alpine

MIRROR=https://mirrors.tuna.tsinghua.edu.cn/alpine
VER=v3.24
OUT=/mnt/d/TB331FCLinux/rootfs/alpine/apks
rm -rf "$OUT"; mkdir -p "$OUT"

echo "=== try apk fetch ==="
if ./apk.static fetch --arch aarch64 --root stage --usermode \
        --repository "$MIRROR/$VER/main" \
        --repository "$MIRROR/$VER/community" \
        --allow-untrusted -o "$OUT" \
        wayland-libs-server seatd seatd-openrc mesa-utils evtest 2>&1 | tail -10; then
    true
fi

n=$(ls -1 "$OUT" 2>/dev/null | wc -l)
echo "  fetched: $n files"

if [ "$n" -eq 0 ]; then
    echo
    echo "=== fallback: resolve from installed db and curl ==="
    DB=stage/lib/apk/db/installed
    want="wayland-libs-server seatd seatd-openrc mesa-utils evtest libseat"
    for p in $want; do
        # find the package block in the installed db
        ver=$(awk -v pkg="$p" '
            BEGIN{RS=""; FS="\n"}
            { name=""; ver="";
              for(i=1;i<=NF;i++){
                if($i ~ /^P:/) name=substr($i,3);
                if($i ~ /^V:/) ver=substr($i,3);
              }
              if(name==pkg){print ver; exit}
            }' "$DB")
        [ -z "$ver" ] && { echo "  $p: not installed"; continue; }
        for repo in main community; do
            url="$MIRROR/$VER/$repo/aarch64/$p-$ver.apk"
            if curl -sf -o "$OUT/$p-$ver.apk" "$url"; then
                echo "  $p-$ver.apk  ($repo)"
                break
            fi
        done
    done
fi

echo
echo "=== result ==="
ls -lh "$OUT" 2>/dev/null
du -sh "$OUT" 2>/dev/null
