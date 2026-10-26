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
STAND = [
    "......1111......", ".....133331.....", ".....122221.....", ".....122321.....",
    ".....122221.....", "......1221......", "....33333333....", "...33133331333..",
    "....33333333....", ".....311113.....", ".....31..13.....", "....331..133....",
    "....31....13....", "....31....13....", "...331....133...", "...11......11...",
]
RUN = STAND[:11] + [
    "....111..111....", "...111....111...", "..111......111..", "..11........11..",
    ".111.........111",
]
LIE = [
    "................", "..........2222..", ".11111111122322.", "111111111122222.",
    "11111111111133333", "................", "................", "................",
]
ENEMY_A = [
    "......3333......", ".....311113.....", ".....122221.....", ".....123321.....",
    ".....122221.....", "......1221......", "....11111111....", ".1111311113111..",
    "....11111111....", ".....113311.....", ".....13..31.....", "....113..311....",
    "....13....31....", "....13....31....", "...113....311...", "...33......33...",
]
ENEMY_B = ENEMY_A[:11] + [
    "....111..111....", "...111....111...", "..111......111..", "..11........11..",
    ".111.........111",
]
CAPSULE = [".333333.", "32222223", "32233223", "32233223", "32222223", "32222223",
           "32222223", ".333333."]
BULLET = ["........", "........", "..3333..", "..3333..", "..3333..", "..3333..",
          "........", "........"]
BOSS_BULLET = ["........", ".222222.", ".233332.", ".233332.", ".233332.", ".233332.",
               ".222222.", "........"]
EXPLOSION = ["...33...", ".3.33.3.", "..3223..", "33222233", "33222233", "..3223..",
             ".3.33.3.", "...33..."]
ARROW = ["..3.....", "..33....", "..333...", "..3333..", "..333...", "..33....",
         "..3.....", "........"]

# tile numbers (keep in sync with src/main.c)
T_STAND, T_RUN, T_LIE, T_BULLET = 1, 5, 9, 11
T_ENEMY_A, T_ENEMY_B, T_CAPSULE, T_BOSS = 12, 16, 20, 21
T_BOSS_BULLET, T_EXPLOSION, T_ARROW = 37, 38, 42

blit(STAND, T_STAND, 2)
blit(RUN, T_RUN, 2)
blit(LIE, T_LIE, 2)
blit(BULLET, T_BULLET, 1)
blit(ENEMY_A, T_ENEMY_A, 2)
blit(ENEMY_B, T_ENEMY_B, 2)
blit(CAPSULE, T_CAPSULE, 1)
blit(BOSS_BULLET, T_BOSS_BULLET, 1)
blit(EXPLOSION, T_EXPLOSION, 1)
blit(ARROW, T_ARROW, 1)


def boss_art():
    g = [["."] * 32 for _ in range(32)]
    for y in range(32):
        for x in range(32):
            d = ((x - 15.5) / 16.0) ** 2 + ((y - 15.5) / 16.0) ** 2
            if d <= 1.0:
                g[y][x] = "1" if d > 0.82 else "2"
    for x0 in (7, 18):  # eyes
        for y in range(10, 16):
            for x in range(x0, x0 + 7):
                g[y][x] = "3"
        for y in range(12, 16):
            for x in range(x0 + 2, x0 + 5):
                g[y][x] = "1"
    for i in range(7):  # angry brows
        g[7 + i // 3][7 + i] = "1"
        g[7 + i // 3][24 - i] = "1"
    for y in range(21, 27):  # mouth with teeth
        for x in range(9, 23):
            g[y][x] = "1"
    for x in range(9, 23, 3):
        g[21][x] = g[21][x + 1] = "3"
        g[26][x] = g[26][x + 1] = "3"
    return ["".join(r) for r in g]


blit(boss_art(), T_BOSS, 4)

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
T_GRASS, T_EARTH, T_CLOUD, T_MOUNTAIN, T_PINE, T_LOGO = 0x5B, 0x5C, 0x5D, 0x5E, 0x5F, 0x60
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


def encode(t):
    p0 = bytes(sum((t[y][x] & 1) << (7 - x) for x in range(8)) for y in range(8))
    p1 = bytes(sum(((t[y][x] >> 1) & 1) << (7 - x) for x in range(8)) for y in range(8))
    return p0 + p1


bank = bytearray(4096)
for i, t in tiles.items():
    bank[i * 16:i * 16 + 16] = encode(t)
with open(sys.argv[1], "wb") as f:
    f.write(bytes(bank) * 2)
