# Meme Blitz

A Contra-style NES run-and-gun written in C (cc65). The opening screen shows the
current version, **1.1.0** (maintained in `GAME_VERSION` in `src/main.c`).
Level 1 is **Meme Zone**: one or two
human commandos run right, shoot enemies, grab power-ups (shoot the floating capsule, then
touch the dropped supply package: S = spread, R = rapid fire) and beat the boss, which has hit points.

Defeating the first boss unlocks **Level 2: Lunar Outpost**, with cratered grey
terrain, violet ridges, silver alien invaders, and an eerie space music
loop. Its final boss, the **Moon Warden**, is an armoured flying saucer with
40 hit points and faster blasts at alternating heights. Lives, weapons, player
count, and score carry over; defeating it completes the campaign. A new game
resets both players and starts again at Level 1.

Controls: D-pad move (down = lie down), A jump, B shoot, Select toggles 1/2 players on the
title screen, and Start begins, pauses, or resumes a game.

## Build and run

Requires `cc65`, `python3` and FCEUX (with Lua support).

    make        # builds release/memeblitz.nes (including sprites from assets/sprites.png)
    make release # creates release/memeblitz.nes locally
    make run    # launches it in FCEUX
    make capture # runs a scripted playtest and saves game-only PNGs in tmp/

If FCEUX is outside your command search path, set `FCEUX` to its executable
when invoking make (for example, `make capture FCEUX=/usr/games/fceux`).

The HUD displays score: each enemy is worth 100 points and the boss is worth
1,000 points, both multiplied by the level number. Jump input is buffered for
a few frames so it remains responsive while running over ledges or beneath
one-way platforms. Meme Zone features human enemy soldiers; Lunar Outpost has large-headed
aliens with dark eyes and jointed limbs. Both stages have compact player shots, and large floating supply targets that release labelled packages. Meme
Zone has dark grey ground with blue highlights. Its 40-pixel alien boss hovers
vertically and fires red blasts. The game uses
NES pulse channels for a looping background melody and weapon-fire effects;
the boss defeat sequence adds explosions and a victory fanfare that continues
through the stage-clear or mission-complete screen.

## Editing character sprites

`assets/sprites/player_soldier.png` contains seven transparent 24x24 soldier
poses, with frame positions and NES tile numbers in the adjacent JSON. Shaded
helmets, faces, layered vests, rifles, and articulated legs restore the original
human combatants with more natural proportions and detail within NES limits.
The players retain idle, running, jumping, falling, landing, prone, and firing
animations. Player one wears blue, player two red, and Earth enemies green, with skin-tone faces. Lunar enemies and the Moon
Warden use black, silver, and white. Animation freezes while paused.

`assets/sprites.png` is the editable source for enemies, projectiles,
and combat effects. It is a 128x64 transparent PNG arranged on an 8-pixel grid;
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
`make` verifies the cc65 ROM build. `make capture` uses FCEUX's native Lua
`gui.savescreenshotas` API to save the native NES image without window borders
or desktop content (256x224 with FCEUX's default overscan crop). It captures
the black title screen and blue logo, toggles
player selection, starts Meme Zone, then moves, jumps, and fires. Captures and
a completion report are saved in ignored `tmp/`; they must not be checked in.
The capture directory must exist and `CAPDIR` must be an absolute path if
running the Lua script directly; the make target handles both requirements.
FCEUX 2.6.5 has been used to verify the title and scrolling gameplay. The
scripted playtest mutes audio; sound and full campaign difficulty still need
manual assessment.
