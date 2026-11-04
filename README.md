# Meme Blitz

A Contra-style NES run-and-gun written in C (cc65). The opening screen shows the
current version, **1.1.0** (maintained in `GAME_VERSION` in `src/main.c`).
Level 1 is **Meme Zone**: one or two
meme soldiers run right, shoot enemies, grab power-ups (shoot the floating capsule, then
touch the dropped letter: S = spread, R = rapid fire) and beat the boss, which has hit points.

Defeating the first boss unlocks **Level 2: Lunar Outpost**, with cratered grey
terrain, violet ridges, green extraterrestrial enemies, and an eerie space music
loop. Its final boss, the **Moon Warden**, is an armoured flying saucer with
40 hit points and faster blasts at alternating heights. Lives, weapons, player
count, and score carry over; defeating it completes the campaign. A new game
resets both players and starts again at Level 1.

Controls: D-pad move (down = lie down), A jump, B shoot, Select toggles 1/2 players on the
title screen, and Start begins, pauses, or resumes a game.

## Build and run

Requires `cc65`, `python3` and Mesen.

    make        # builds release/memeblitz.nes (including sprites from assets/sprites.png)
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
with nearest-neighbour scaling only, then run `make release` to convert it into NES
CHR graphics automatically. The checked-in PNG works in common modern image
editors and the build uses only Python's standard library. The completed ROM is
written to `release/memeblitz.nes`.

Level 2 enemies and the Moon Warden use `assets/lunar.png`, a separate editable
128x64 sheet with the same palette. Both sheets are required by the build.

## Validation

`python3 tests/check_campaign.py` checks stage resets, carried progress, boss
combat, lunar music selection, and generated graphics using a host C compiler.
`make` verifies the cc65 ROM build. Emulator playtesting is still needed to assess
visual timing, sound, and difficulty on NES hardware.
