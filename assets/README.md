# Editable NES sprites

`sprites.png` is the source artwork for all of the game's moving combat
graphics. It is deliberately a normal transparent PNG, so it can be edited in
Preview, Paint, GIMP, Aseprite, Photoshop, or any similar modern editor.

Keep the canvas at **128 by 64 pixels** and retain the 8-pixel grid. The build
reads only these regions:

| Position | Size | Sprite |
| --- | --- | --- |
| 0,0 | 24x24 | player standing |
| 24,0 | 24x24 | player running |
| 48,0 | 24x8 | player down |
| 72,0 / 96,0 | 24x24 each | enemy standing / running |
| 0,24 through 40,40 | 8x8 / 16x16 | projectiles, effects, arrow, package |
| 48,24 | 40x40 | boss |

Use transparent pixels for colour 0, and exactly these opaque colours for the
three NES palette values: `#111111`, `#777777`, and `#FFFFFF`. Preserve native
pixel dimensions and use nearest-neighbour scaling. `make` converts the PNG
to the CHR bank used by the NES program; no image-library installation is
needed.
