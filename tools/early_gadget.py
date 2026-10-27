#!/usr/bin/env python3
"""early_gadget.py

1) Bring the USB serial gadget up *before* the card mount / switchroot, so the
   console exists for the whole boot (previously the gadget code sat after the
   switchroot check and never ran when handing over to Alpine).
2) switchroot.sh additionally moves the configfs submount into the new root,
   otherwise the gadget is orphaned and /dev/ttyGS0 disappears.
"""
P = '/mnt/d/TB331FCLinux/initramfs/init_v5.c'
t = open(P, encoding='utf-8').read()

if 'early gadget bring-up' in t:
    print('init already patched')
else:
    ANCHOR = '\tchmod("/bin/busybox", 0755);\n'
    if ANCHOR not in t:
        ANCHOR = '    chmod("/bin/busybox", 0755);\n'
    if ANCHOR not in t:
        raise SystemExit('busybox chmod anchor not found')

    EARLY = (
        "\n"
        "\t/* early gadget bring-up: the serial console must exist before the\n"
        "\t * switchroot to Alpine, otherwise we lose it. */\n"
        "\tif (access(\"/gadget.sh\", R_OK) == 0) {\n"
        "\t\tpid_t gp = fork();\n"
        "\t\tif (gp == 0) {\n"
        "\t\t\tchar *const ga[] = { \"/bin/busybox\", \"sh\", \"/gadget.sh\", NULL };\n"
        "\t\t\texecv(\"/bin/busybox\", ga);\n"
        "\t\t\t_exit(127);\n"
        "\t\t}\n"
        "\t\tif (gp > 0) { int st; waitpid(gp, &st, 0); }\n"
        "\t}\n"
    )
    t = t.replace(ANCHOR, ANCHOR + EARLY, 1)
    open(P, 'w', encoding='utf-8', newline='\n').write(t)
    print('init: early gadget bring-up inserted')

S = '/mnt/d/TB331FCLinux/initramfs/switchroot.sh'
s = open(S, encoding='utf-8').read()
if 'configfs' in s:
    print('switchroot.sh already moves configfs')
else:
    OLD = 'for d in proc sys dev; do'
    NEW = ('# move the configfs submount too, otherwise the USB gadget configured\n'
           '# in the initramfs is orphaned and /dev/ttyGS0 disappears\n'
           'mkdir -p /newroot/sys/kernel/config\n'
           'mount --move /sys/kernel/config /newroot/sys/kernel/config && echo "  moved configfs"\n'
           '\n'
           'for d in proc sys dev; do')
    if OLD not in s:
        raise SystemExit('switchroot loop anchor not found')
    s = s.replace(OLD, NEW, 1)
    # target init again for the production run
    s = s.replace('exec /bin/busybox switch_root /newroot /bin/sh',
                  'exec /bin/busybox switch_root /newroot /sbin/init')
    open(S, 'w', encoding='utf-8', newline='\n').write(s)
    print('switchroot.sh: moves configfs, execs /sbin/init')
