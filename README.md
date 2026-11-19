# Resident Evil 3 HD mod on Linux / Steam Deck: fix for small backgrounds in the corner

## Who needs this?
You play Resident Evil 3 (1999) with Classic REbirth and an HD mod that includes `bio3hd.asi`
(Seamless HD Project, RE:Enhance, TeamX HD mod) under Wine, Proton, Steam Deck, Heroic,
Lutris or Bottles, and:

- the backgrounds (and the title screen) appear small in the upper-left corner, or
- the title-screen menu text is drawn on top of itself.

Changing the Proton or DXVK version does not help. The mod reads internal data of
Microsoft's Direct3D that does not exist under Wine/DXVK
([Wine bug 57395](https://bugs.winehq.org/show_bug.cgi?id=57395)).

## Fix
You need Python 3. It is preinstalled on most Linux distributions and on SteamOS.

1. Close the game.
2. Open a terminal in the game folder (where `bio3hd.asi` is) and download the script:
   ```
   curl -LO https://raw.githubusercontent.com/technix85/re3-classic-hd-wine-fix/main/patch_bio3hd_wine.py
   ```
3. Run it:
   ```
   python3 patch_bio3hd_wine.py
   ```
   The script checks that your `bio3hd.asi` is the expected version, saves the original as
   `bio3hd.asi.orig` and patches four small spots. If the bytes do not match, it changes nothing.
4. Start the game as usual.

To undo it: `python3 patch_bio3hd_wine.py --revert`

If you re-extract or reinstall the HD mod, `bio3hd.asi` is overwritten. Run the script again.

## Tested with
- GOG version (Japanese install, required by the mod) + RE:Enhance v2.2 (Classic REbirth 1.0.1)
- Heroic (Flatpak), GE-Proton11-12 (DXVK 3.1.1), AMD GPU, fullscreen 2560x1440
- Checked: title screen, intro, first room, inventory

Not tested: the standalone Seamless HD Project package, the TeamX mod alone,
Steam Deck, WineD3D. Please open an issue and report whether it works for you.

## Other pitfalls we ran into
- **Heroic:** Set the alternative executable to `BIOHAZARD(R) 3 PC.exe`. By default, Heroic starts
  GOG's `BH3Launcher.exe` / `Bio3_PC.exe`, which ignores the mod (old graphics, only the movies are HD).
  Other launchers may need the same setting.
- **Resolution list in the Classic REbirth dialog:** Under Wine the dropdown opens only one row
  high, so it looks as if 640x480 were the only choice. The other entries exist; the last one,
  "Fullscreen" (4:3 at full screen height), is what you want. Reliable way: close the game, set
  `Display_mode` in `config.ini` to the position of "Fullscreen" (counting from 0), then start.
  The list is 640x480 plus steps of 320x240 below your screen height, then "Fullscreen", so
  `Display_mode` is 4 on 1440p (verified), 3 on 1080p and 2 on Steam Deck (800p). The last two
  are derived from Classic REbirth's code and not tested.
- **F8 in game** cycles the window size and saves it, so you can end up in a small window by accident.

## Technical details
`bio3hd.asi` (version info "teamx" / "Resident Evil 3 HDtools", md5 `6d8747064854bec9e8de07e5769a5b4f`)
hooks four places in Classic REbirth's `ddraw.dll`, right before `IDirect3DTexture9::UnlockRect`.
The hook stubs (RVA 0x4460, 0x4490, 0x44e0, 0x4560) pass `[tex+0x90]` (pixel pointer) and
`[tex+0x20]` (texture width) to the texture handler. Those are private fields of Microsoft's
d3d9 texture object; under WineD3D/DXVK they contain unrelated data, the handler's width check
never matches and the HD textures are never registered.

The patch makes the stubs take the pixel pointer and `Pitch / 4` from the `D3DLOCKED_RECT` that
Classic REbirth itself received from `LockRect`. It is still on REbirth's stack at all four sites.
This only uses values from the public D3D9 API, so it does not depend on the Wine or DXVK version.
The proper fix belongs in the mod's source (use `LockRect`/`GetLevelDesc` values instead of object
internals); this repository is a stopgap until then.

## License
MIT, see [LICENSE](LICENSE). This repository contains no files from the game or the mods, only the
patch script.
