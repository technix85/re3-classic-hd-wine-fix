#!/usr/bin/env python3
"""
Wine/Proton fix for the Resident Evil 3 (1999) HD mod (TeamX "Resident Evil 3 HDtools",
bio3hd.asi, as shipped with Seamless HD Project / RE:Enhance for Classic REbirth).

Symptom under Wine/Proton (WineD3D or any DXVK version): HD backgrounds are drawn small in
the upper-left corner, title-screen menu text piles up. See Wine bug 57395 / 53775.

Cause: four hook stubs in bio3hd.asi read the locked bits pointer and the texture width from
undocumented fields inside Microsoft's d3d9 texture object ([tex+0x90], [tex+0x20]).
This patch makes them use the D3DLOCKED_RECT that Classic REbirth itself received from
IDirect3DTexture9::LockRect (width = Pitch / 4), which is valid on any D3D9 implementation.

Usage:   python3 patch_bio3hd_wine.py [path/to/bio3hd.asi]          (default: ./bio3hd.asi)
Revert:  python3 patch_bio3hd_wine.py --revert [path/to/bio3hd.asi]

A backup "bio3hd.asi.orig" is written next to the file before patching.
No third-party modules needed.
"""
import hashlib, os, shutil, sys

# (file offset, original bytes, patched bytes)
SITES = [
    # stub 1 (RVA 0x4466): lea eax,[ebp-0x80]; push [eax-0x1c]; mov ecx,[eax-0x24]; shr ecx,2; push ecx; push ecx; push [eax-0x20]; nop
    (0x3866, 'ffb564ffffffff7024ff7020ffb090000000', '8d4580ff70e48b48dcc1e9025151ff70e090'),
    # stub 2 (RVA 0x4496): push [ebp+0x3c]; mov ecx,[ebp-0x18]; shr ecx,2; push ecx; push ecx; push [ebp-0x14]; nop
    (0x3896, 'ff753cff7024ff7020ffb090000000',       'ff753c8b4de8c1e9025151ff75ec90'),
    # stub 3 (RVA 0x44f6): mov ecx,[ebp-0x10]; shr ecx,2; push ecx; push ecx; push [ebp-0xc]; nop
    (0x38f6, 'ff7024ff7020ffb090000000',             '8b4df0c1e9025151ff75f490'),
    # stub 4 (RVA 0x4566): lea eax,[ebp-0x80]; push [eax-0x10]; mov ecx,[eax-0x18]; shr ecx,2; push ecx; push ecx; push [eax-0x14]; nop
    (0x3966, 'ffb570ffffffff7124ff7120ffb190000000', '8d4580ff70f08b48e8c1e9025151ff70ec90'),
]
KNOWN_ORIGINAL_MD5 = '6d8747064854bec9e8de07e5769a5b4f'
KNOWN_PATCHED_MD5 = '704dd640ff209d70ba15c0bf8ee919c1'


def md5(b):
    return hashlib.md5(b).hexdigest()


def state(data):
    orig = all(data[o:o + len(bytes.fromhex(a))] == bytes.fromhex(a) for o, a, _ in SITES)
    patched = all(data[o:o + len(bytes.fromhex(b))] == bytes.fromhex(b) for o, _, b in SITES)
    return 'original' if orig else 'patched' if patched else 'unknown'


def main():
    args = [a for a in sys.argv[1:] if a != '--revert']
    revert = '--revert' in sys.argv[1:]
    path = args[0] if args else 'bio3hd.asi'
    if not os.path.isfile(path):
        sys.exit(f'File not found: {path}')
    data = bytearray(open(path, 'rb').read())
    st = state(data)
    print(f'{path}: md5 {md5(data)}, state: {st}')
    if st == 'unknown':
        sys.exit('The bytes at the patch sites do not match this build. Nothing was changed.')
    if md5(data) not in (KNOWN_ORIGINAL_MD5, KNOWN_PATCHED_MD5):
        print('Note: md5 differs from the tested build; continuing only because the bytes at all four sites match.')

    # SITES entries: (offset, original, patched) -> index 2 = patched bytes, index 1 = original bytes
    want, frm = ('original', 1) if revert else ('patched', 2)
    if st == want:
        sys.exit(f'Already {want}. Nothing to do.')

    if not revert:
        backup = path + '.orig'
        if os.path.exists(backup):
            print(f'Backup {backup} already exists, keeping it.')
        else:
            shutil.copy2(path, backup)
            print(f'Backup written: {backup}')

    for site in SITES:
        o, new = site[0], bytes.fromhex(site[frm])
        data[o:o + len(new)] = new
    tmp = path + '.tmp'
    open(tmp, 'wb').write(data)
    os.replace(tmp, path)
    print(f'{"Reverted" if revert else "Patched"}: md5 now {md5(data)}')


if __name__ == '__main__':
    main()
