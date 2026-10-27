#!/usr/bin/env python3
"""use_busybox_mount.py

init's direct mount(2) call returned EFAULT on this kernel, while
`busybox mount -t vfat ...` from the shell works fine.  Shell out to busybox
instead of fighting the syscall.
"""
import sys

P = '/mnt/d/TB331FCLinux/initramfs/init_v5.c'
t = open(P, encoding='utf-8').read()

if 'sh_mount' in t:
    print('already patched')
    sys.exit(0)

HELPER = '''
/* mount via busybox: the direct mount(2) call returns EFAULT on this kernel
 * while `busybox mount` works, so shell out to it. */
static int sh_mount(const char *dev, const char *type)
{
	pid_t p = fork();
	int st = 0;

	if (p == 0) {
		if (type) {
			char *const av[] = { "/bin/busybox", "mount", "-t",
					     (char *)type, (char *)dev, "/mnt", NULL };
			execv("/bin/busybox", av);
		} else {
			char *const av[] = { "/bin/busybox", "mount",
					     (char *)dev, "/mnt", NULL };
			execv("/bin/busybox", av);
		}
		_exit(127);
	}
	if (p < 0)
		return -1;
	waitpid(p, &st, 0);
	return (WIFEXITED(st) && WEXITSTATUS(st) == 0) ? 0 : -1;
}

'''

anchor = 'static void attach_console(void)'
if anchor not in t:
    sys.exit('anchor not found')
t = t.replace(anchor, HELPER + anchor, 1)

old1 = 'if (mount(CANDS[c], "/mnt", t, 0, "umask=0") == 0) {'
new1 = 'if (sh_mount(CANDS[c], TYPES[t]) == 0) {'
if old1 not in t:
    sys.exit('mount call 1 not found')
t = t.replace(old1, new1, 1)

old2 = 'if (!card_mounted && mount(CANDS[c], "/mnt", NULL, 0, NULL) == 0) {'
new2 = 'if (!card_mounted && sh_mount(CANDS[c], NULL) == 0) {'
if old2 in t:
    t = t.replace(old2, new2, 1)
else:
    print('note: autodetect mount call not found, skipped')

open(P, 'w', encoding='utf-8', newline='\n').write(t)
print('init: SD mounting now goes through busybox mount')
