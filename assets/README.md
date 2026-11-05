# Editable NES sprites

`sprites.png` is the source artwork for the game's enemy and combat
graphics. It is deliberately a normal transparent PNG, so it can be edited in
Preview, Paint, GIMP, Aseprite, Photoshop, or any similar modern editor.

Keep the canvas at **128 by 64 pixels** and retain the 8-pixel grid. The build
reads only these regions:

| Position | Size | Sprite |
| --- | --- | --- |
| 0,0 through 71,23 | unused | player moved to independent Chomp sheet |
| 72,0 / 96,0 | 24x24 each | alien standing / running |
| 0,24 through 40,40 | 8x8 / 16x16 | projectiles, effects, arrow, package |
| 48,24 | 40x40 | boss |

Use transparent pixels for colour 0, and exactly these opaque colours for the
three NES palette values: dark blue `#182659`, blue `#2A7AC9`, and gold
`#FFD35E`. The image is colourful for easier editing; the converter maps them
to the three NES colour slots selected by each character. Preserve native pixel
dimensions and use nearest-neighbour scaling. `make` converts the PNG to the
CHR bank used by the NES program; no image-library installation is needed.

## Level 2 artwork

`lunar.png` is the independent 128x64 transparent source for the Lunar Outpost.
Use the same three opaque colours and grid as `sprites.png`:

| Position | Size | Sprite |
| --- | --- | --- |
| 72,0 / 96,0 | 24x24 each | alien standing / running |
| 48,24 | 40x40 | Moon Warden saucer boss |

Other areas of this sheet are unused. The build imports these regions into
separate tiles, preserving Level 1 artwork. The lunar terrain remains generated
in `tools/gen_chr.py`. The developer option `--export-lunar OUTPUT.png` recreates
the default lunar sheet; use it only when intentionally replacing hand edits.

The floating 24x24 supply target is generated from the default package design
in `tools/gen_chr.py`; the editable 16x16 package is used after it is shot.
Alien palette slots render as black, grey, and white in both stages. Player
shots use a compact 4x4 silhouette within their 8x8 tile.

## Chomp player

`sprites/player_chomp.png` is a 168x24 RGBA sheet of seven 24x24 poses.
`sprites/player_chomp.json` records each frame's position, tile base, palette,
and timing at 60 game updates per second. Its pixels use transparent, dark
`#081828`, cyan `#00C0D8`, and white `#FFFFFF`; these map to NES transparency,
black, cyan (blue for player two), and white. The build reads this sheet last
so neither stage can replace the player artwork.

The supplied issue logo was isolated from its connected pale background,
resampled with nearest neighbour to 22x22, and reduced to three opaque colours.
White highlights inside the logo were retained. Poses use nearest-neighbour
squash/stretch, a one-pixel idle bob, and an enlarged bite. Keep the sheet at
native resolution with no antialiasing. The crouch frame fills the bottom twelve
rows; standing damage bounds exclude the splash tips (16x18, or 16x12 crouched).
Landing reuses the squashed run pose for six updates. Shooting opens the bite
while preserving existing projectile controls. Damage/death and respawn blink.
Tile ranges 0C–1D and ED–FE are reserved for the additional Chomp poses; tile 00
stays blank for title/background fills. The original player regions in
`sprites.png` are unused and are no longer imported or exported.
