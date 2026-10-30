# Meme Blitz

A Contra-style NES run-and-gun written in C (cc65). Level 1 is **Meme Zone**: one or two
meme soldiers run right, shoot enemies, grab power-ups (shoot the floating capsule, then
touch the dropped letter: S = spread, R = rapid fire) and beat the boss, which has hit points.

Controls: D-pad move (down = lie down), A jump, B shoot, Select toggles 1/2 players on the
title screen, and Start begins, pauses, or resumes a game.

## Build and run

Requires `cc65`, `python3` and Mesen.

    make        # builds build/memeblitz.nes (including sprites from assets/sprites.png)
    make release # creates release/memeblitz.nes locally
    make run    # launches it in Mesen

The HUD displays score: each enemy is worth 100 points and the boss is worth
1,000 points, both multiplied by the level number. Jump input is buffered for
a few frames so it remains responsive while running over ledges. The game uses
NES pulse channels for a looping background melody and weapon-fire effects;
the boss defeat sequence adds explosions and a victory fanfare.

## Editing character sprites

`assets/sprites.png` is the editable source for every character, projectile,
and combat sprite. It is a 128x64 transparent PNG arranged on an 8-pixel grid;
see `assets/README.md` for its layout and palette. Edit it at its native size
with nearest-neighbour scaling only, then run `make` to convert it into NES
CHR graphics automatically. The checked-in PNG works in common modern image
editors and the build uses only Python's standard library.
