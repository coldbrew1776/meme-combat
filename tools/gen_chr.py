#!/usr/bin/env python3
"""Generate the NES CHR (graphics) bank for Meme Blitz.

Usage: gen_chr.py OUTPUT.chr
The same 4K tile set is written to both pattern tables (sprites and
background), so tile numbers mean the same thing everywhere.
"""
import sys

tiles = {}  # tile index -> 8x8 list of pixel values 0..3


def tile(i):
    return tiles.setdefault(i, [[0] * 8 for _ in range(8)])


def blit(art, base, w_tiles):
    """Slice an ASCII-art picture ('.'=0, '1'..'3') into tiles, row-major."""
    h = len(art)
    w = w_tiles * 8
    for y in range(h):
        row = art[y].ljust(w, ".")[:w]
        for x in range(w):
            c = row[x]
            v = 0 if c == "." else int(c)
            t = tile(base + (y // 8) * w_tiles + x // 8)
            t[y % 8][x % 8] = v


# ---- sprites -------------------------------------------------------------
def canvas(w, h):
    return [["."] * w for _ in range(h)]


def rect(g, x0, y0, x1, y1, c):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            g[y][x] = c


def soldier(run, enemy):
    """24x24 soldier facing right; the rifle ends on the last column."""
    g = canvas(24, 24)
    if enemy:
        # Tall monochrome invader: dome, antennae, huge eyes and tentacles.
        rect(g, 10, 0, 11, 2, 3)
        g[0][8] = g[0][13] = 3
        rect(g, 5, 3, 18, 5, 3)
        rect(g, 3, 6, 20, 14, 2)
        rect(g, 5, 5, 18, 16, 3)
        rect(g, 6, 7, 10, 12, 1)
        rect(g, 14, 7, 18, 12, 1)
        rect(g, 7, 8, 9, 10, 3)
        rect(g, 15, 8, 17, 10, 3)
        rect(g, 8, 14, 16, 15, 1)
        rect(g, 4, 15, 20, 18, 2)
        for x in (5, 9, 14, 18):
            rect(g, x, 19, x + 1, 22, 3)
            g[23][x - 1] = g[23][x] = g[23][x + 1] = 3
        return ["".join(str(v) for v in r) for r in g]
    rect(g, 7, 0, 14, 2, 1)             # helmet / hair
    rect(g, 6, 2, 15, 3, 1)
    if not enemy:
        rect(g, 6, 4, 15, 8, 2)         # fuller face
    rect(g, 7, 4, 14, 8, 2)             # face
    rect(g, 8, 9, 13, 9, 2)             # neck
    if not enemy:
        rect(g, 6, 3, 15, 3, 3)         # headband
        g[5][12] = g[5][13] = 1         # eye
        rect(g, 11, 7, 14, 7, 1)        # smirk
    t = 0 if enemy else 1               # the hero is built a little thicker
    rect(g, 5 - t, 10, 16 + t, 16, 3)   # torso
    rect(g, 5 - t, 10, 16 + t, 10, 1)   # collar
    rect(g, 5 - t, 15, 16 + t, 16, 1)   # belt
    g[15][10] = g[15][11] = 3           # buckle
    rect(g, 2 - t, 11, 5 - t, 15, 2)    # rear arm
    rect(g, 16 + t, 11, 18 + t, 14, 2)  # front arm
    rect(g, 17 + t, 11, 23, 12, 1)      # rifle barrel
    rect(g, 16 + t, 13, 20, 14, 1)      # rifle body
    g[11][22] = 3
    if run:
        for y in range(17, 24):
            x = 9 - (y - 17)
            rect(g, x - t, y, x + 2 + t, y, 3 if y == 23 else 1)
            x = 12 + (y - 17)
            rect(g, x - t, y, x + 2 + t, y, 3 if y == 23 else 1)
    else:
        rect(g, 6 - t, 17, 9, 22, 1)
        rect(g, 12, 17, 15 + t, 22, 1)
        rect(g, 5 - t, 23, 10, 23, 3)
        rect(g, 11, 23, 16 + t, 23, 3)
    return ["".join(str(v) for v in r) for r in g]


def lying(enemy):
    g = canvas(24, 8)
    rect(g, 0, 4, 5, 6, 1)              # legs
    rect(g, 6, 3, 15, 6, 3)             # torso
    rect(g, 6, 5, 15, 5, 1)
    rect(g, 16, 2, 20, 6, 2)            # head
    rect(g, 16, 1, 20, 2, 1)
    g[4][19] = 3 if enemy else 1
    rect(g, 14, 4, 18, 5, 2)            # arm
    rect(g, 17, 5, 23, 6, 1)            # rifle
    return ["".join(str(v) for v in r) for r in g]


# Chomp is drawn as a compact, three-colour 24x24 metasprite.  Dots are
# transparent, which makes the outline read cleanly against every backdrop.
# The small variations deliberately use the same NES palette: idle bobs its
# fin, walk shifts its tail, jump stretches upward, and attack opens a big
# bite at the nose.
def chomp_frame(kind):
    g = canvas(24, 24)
    lift = 1 if kind == "idle_b" else 0
    # Rounded blue body, tapering into Chomp's pointed nose on the right.
    for y in range(3 - lift, 20 - lift):
        yy = y + lift
        half = 8 - abs(yy - 11) // 2
        left = 10 - half
        right = 15 + (3 if 7 <= yy <= 15 else 0)
        for x in range(max(0, left), min(23, right) + 1):
            g[y][x] = 3 if x in (left, right) or y in (3 - lift, 19 - lift) else (2 if x > 9 else 1)
    # A swept tail and dorsal fin make the logo silhouette recognizable.
    tail_shift = -1 if kind == "walk_b" else 0
    for y in range(8 - lift, 17 - lift):
        x = 4 + (y - (8 - lift)) // 2 + tail_shift
        if 0 <= x < 24:
            g[y][x] = 3
            if x > 0: g[y][x - 1] = 2
    for y in range(1 - lift, 7 - lift):
        for x in range(8, 13 - y + lift):
            if 0 <= y < 24: g[y][x] = 3 if x == 8 or y == 1 - lift else 2
    # White eye and a dark pupil.
    g[8 - lift][15] = g[8 - lift][16] = 3
    g[9 - lift][16] = 1
    # The mouth is the defining animation: closed at rest, opening while
    # walking, and a wide, obvious chomp while firing.
    mouth_y = 14 - lift
    if kind == "attack":
        for y in range(11 - lift, 18 - lift):
            start = 15 + abs(y - (14 - lift)) // 2
            for x in range(start, 24): g[y][x] = 0
        for x in range(15, 23):
            g[10 - lift][x] = 3
            g[18 - lift][x] = 3
        g[11 - lift][22] = g[17 - lift][22] = 3
    else:
        for x in range(15, 22): g[mouth_y][x] = 1
        if kind == "walk_b":
            for x in range(17, 22): g[mouth_y + 1][x] = 0
    if kind == "jump":
        # Vertical motion gets a taller dorsal fin and a tucked tail.
        for y in range(0, 4):
            for x in range(9, 14 - y): g[y][x] = 3 if x == 9 else 2
        rect(g, 3, 15, 7, 17, 2)
    return ["".join(str(v) for v in r) for r in g]


CHOMP_IDLE_A = chomp_frame("idle_a")
CHOMP_IDLE_B = chomp_frame("idle_b")
CHOMP_WALK_A = chomp_frame("walk_a")
CHOMP_WALK_B = chomp_frame("walk_b")
CHOMP_JUMP = chomp_frame("jump")
CHOMP_ATTACK = chomp_frame("attack")
ENEMY_A = soldier(False, True)
ENEMY_B = soldier(True, True)
# A 16x16 supply crate is deliberately a generous target and remains a
# recognizable package as it drops after being shot.
PACKAGE = [
    "..333333333333..", ".322222222222223.", "3211111111111123", "3213333333333123",
    "3213222222223123", "3213222222223123", "3213222222223123", "3213222222223123",
    "3213222222223123", "3213222222223123", "3213222222223123", "3213222222223123",
    "3213333333333123", "3211111111111123", ".322222222222223.", "..333333333333..",
]
# A tighter 4x4 shot leaves more space between the action than the old orb.
BULLET = ["........", "........", "..3333..", "..3223..", "..3223..", "..3333..",
          "........", "........"]
BOSS_BULLET = ["........", ".222222.", ".233332.", ".233332.", ".233332.", ".233332.",
               ".222222.", "........"]
EXPLOSION = ["...33...", ".3.33.3.", "..3223..", "33222233", "33222233", "..3223..",
             ".3.33.3.", "...33..."]
ARROW = ["..3.....", "..33....", "..333...", "..3333..", "..333...", "..33....",
         "..3.....", "........"]

# tile numbers (keep in sync with src/main.c)
T_CHOMP_IDLE_A, T_CHOMP_IDLE_B, T_CHOMP_WALK_A = 0x70, 0x79, 0x82
T_CHOMP_WALK_B, T_CHOMP_JUMP, T_CHOMP_ATTACK = 0xC0, 0xC9, 0xD2
T_BULLET = 11
T_ENEMY_A, T_ENEMY_B, T_CAPSULE, T_BOSS = 0x85, 0x8E, 0x98, 0xA0
T_BOSS_BULLET, T_EXPLOSION, T_ARROW = 37, 38, 42

blit(CHOMP_IDLE_A, T_CHOMP_IDLE_A, 3)
blit(CHOMP_IDLE_B, T_CHOMP_IDLE_B, 3)
blit(CHOMP_WALK_A, T_CHOMP_WALK_A, 3)
blit(CHOMP_WALK_B, T_CHOMP_WALK_B, 3)
blit(CHOMP_JUMP, T_CHOMP_JUMP, 3)
blit(CHOMP_ATTACK, T_CHOMP_ATTACK, 3)
blit(BULLET, T_BULLET, 1)
blit(ENEMY_A, T_ENEMY_A, 3)
blit(ENEMY_B, T_ENEMY_B, 3)
blit(PACKAGE, T_CAPSULE, 2)
blit(BOSS_BULLET, T_BOSS_BULLET, 1)
blit(EXPLOSION, T_EXPLOSION, 1)
blit(ARROW, T_ARROW, 1)


def boss_art():
    """A 40x40 floating alien commander with a large black-and-white dome."""
    g = [["."] * 40 for _ in range(40)]
    for y in range(40):
        for x in range(40):
            d = ((x - 19.5) / 20.0) ** 2 + ((y - 18.0) / 19.0) ** 2
            if d <= 1.0:
                g[y][x] = "1" if d > 0.80 else "2"
    for x0 in (7, 23):
        rect(g, x0, 12, x0 + 9, 20, "1")
        rect(g, x0 + 2, 14, x0 + 7, 18, "3")
    for i in range(10):
        g[8 + i // 3][7 + i] = "1"
        g[8 + i // 3][32 - i] = "1"
    rect(g, 11, 26, 28, 31, "1")
    for x in range(12, 28, 3):
        rect(g, x, 26, x + 1, 27, "3")
        rect(g, x, 30, x + 1, 31, "3")
    for x in (4, 34):
        rect(g, x, 20, x + 2, 31, "1")
    return ["".join(str(v) for v in r) for r in g]


blit(boss_art(), T_BOSS, 5)

# ---- font (3x5, ASCII-indexed so tile == character code) -------------------
FONT = {
    "A": "010101111101101", "B": "110101110101110", "C": "011100100100011",
    "D": "110101101101110", "E": "111100110100111", "F": "111100110100100",
    "G": "011100101101011", "H": "101101111101101", "I": "111010010010111",
    "J": "001001001101010", "K": "101101110101101", "L": "100100100100111",
    "M": "101111111101101", "N": "110101101101101", "O": "010101101101010",
    "P": "110101110100100", "Q": "010101101111011", "R": "110101110101101",
    "S": "011100010001110", "T": "111010010010010", "U": "101101101101111",
    "V": "101101101101010", "W": "101101111111101", "X": "101101010101101",
    "Y": "101101010010010", "Z": "111001010100111", "0": "111101101101111",
    "1": "010110010010111", "2": "110001010100111", "3": "110001010001110",
    "4": "101101111001001", "5": "111100110001110", "6": "011100111101111",
    "7": "111001010010010", "8": "111101111101111", "9": "111101111001110",
}
for ch, bits in FONT.items():
    t = tile(ord(ch))
    for i, b in enumerate(bits):
        if b == "1":
            t[2 + i // 3][2 + i % 3] = 3

# ---- background tiles ------------------------------------------------------
T_GRASS, T_EARTH, T_CLOUD, T_MOUNTAIN, T_PINE, T_LOGO, T_PLATFORM = 0x5B, 0x5C, 0x5D, 0x5E, 0x5F, 0x60, 0x61
g = tile(T_GRASS)
for y in range(8):
    for x in range(8):
        g[y][x] = 3 if y < 3 else (2 if (x + y) % 4 == 0 else 1)
b = tile(T_EARTH)
for y in range(8):
    for x in range(8):
        b[y][x] = 1 if (x + y * 3) % 5 else 2
cl = tile(T_CLOUD)
for y in range(8):
    for x in range(8):
        cl[y][x] = 2 if (2 <= y <= 5 and 1 <= x <= 6) or (y == 1 and 3 <= x <= 5) else 0
mt = tile(T_MOUNTAIN)
for y in range(8):
    for x in range(8):
        mt[y][x] = 1 if y >= (7 - x if x < 4 else x - 1) else 0
        if mt[y][x] and (x + y) % 5 == 0:
            mt[y][x] = 2
pn = tile(T_PINE)
for y in range(8):
    for x in range(8):
        wide = y // 2 + 1
        pn[y][x] = 3 if (abs(x - 3) <= wide and y < 6) else (2 if x in (3, 4) and y >= 5 else 0)
lg = tile(T_LOGO)
for y in range(8):
    for x in range(8):
        lg[y][x] = 1 if x in (0, 7) or y in (0, 7) else 2
pl = tile(T_PLATFORM)
for y in range(8):
    for x in range(8):
        pl[y][x] = 3 if y < 2 else (1 if (x + y) % 3 else 2)


def encode(t):
    p0 = bytes(sum((t[y][x] & 1) << (7 - x) for x in range(8)) for y in range(8))
    p1 = bytes(sum(((t[y][x] >> 1) & 1) << (7 - x) for x in range(8)) for y in range(8))
    return p0 + p1


bank = bytearray(4096)
for i, t in tiles.items():
    bank[i * 16:i * 16 + 16] = encode(t)
with open(sys.argv[1], "wb") as f:
    f.write(bytes(bank) * 2)
