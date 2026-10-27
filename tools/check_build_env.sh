#!/bin/bash
echo "=== CPU ==="
nproc
echo "=== memory ==="
free -h | head -2
echo "=== WSL root disk ==="
df -h / | tail -1
echo "=== tools ==="
for t in unzip bsdtar make bc flex bison git ccache; do
    if command -v "$t" >/dev/null 2>&1; then
        printf "  %-10s yes\n" "$t"
    else
        printf "  %-10s NO\n" "$t"
    fi
done
echo "=== headers ==="
if [ -f /usr/include/openssl/opensslv.h ]; then
    echo "  openssl dev: yes"
else
    echo "  openssl dev: NO"
fi
for h in /usr/include/libelf.h /usr/include/elf.h /usr/include/flex; do
    [ -e "$h" ] && echo "  $h yes"
done
echo "=== cross compiler ==="
command -v aarch64-linux-gnu-gcc && aarch64-linux-gnu-gcc --version | head -1
echo "=== gcc ==="
gcc --version | head -1
