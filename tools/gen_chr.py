#!/usr/bin/env python3
"""Generate the NES CHR (graphics) bank for Meme Blitz.

Usage: gen_chr.py OUTPUT.chr
The same 4K tile set is written to both pattern tables (sprites and
background), so tile numbers mean the same thing everywhere.
"""
import os
import struct
import sys
import zlib

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
    """A shaded 24x24 commando; the original human combatants, redrawn."""
    g = canvas(24, 24)
    # Helmet, brim, face, eye, and chin create a readable human profile.
    rect(g, 7, 1, 13, 1, 1)
    rect(g, 5, 2, 15, 3, 1)
    rect(g, 4, 4, 16, 4, 3)              # helmet rim / enemy beret band
    rect(g, 6, 5, 14, 8, 2)
    rect(g, 7, 8, 13, 9, 2)
    g[6][13] = g[6][14] = 1              # brow and eye
    g[8][14] = 1                         # nose
    g[9][11] = g[9][12] = 1              # jaw shadow
    # The opposing soldier has a cap badge and a darker collar; silhouette
    # remains deliberately human rather than the recent alien replacement.
    if enemy:
        g[3][9] = g[3][10] = 3
        rect(g, 7, 10, 14, 11, 1)
    else:
        rect(g, 4, 3, 6, 3, 3)           # hero's bandana tail
        g[2][14] = 3
        rect(g, 7, 10, 14, 11, 3)
    # Layered vest, belt, hands, rifle stock, receiver, and barrel.
    rect(g, 6, 11, 15, 16, 1)
    rect(g, 7, 12, 14, 15, 3)
    rect(g, 8, 12, 10, 14, 2)            # chest highlight
    rect(g, 6, 16, 15, 17, 1)
    rect(g, 2, 12, 5, 15, 1)
    rect(g, 3, 14, 6, 16, 2)
    rect(g, 15, 11, 18, 14, 2)
    rect(g, 17, 11, 22, 12, 1)
    rect(g, 16, 13, 20, 15, 1)
    rect(g, 18, 13, 20, 13, 3)
    g[11][22] = 3
    # Distinct leg poses give the restored protagonist and enemies real
    # running weight rather than the former flat, symmetric blocks.
    if run:
        rect(g, 7, 18, 10, 19, 1)
        rect(g, 5, 20, 8, 21, 1)
        rect(g, 3, 22, 7, 23, 3)
        rect(g, 12, 18, 15, 19, 1)
        rect(g, 14, 20, 17, 21, 1)
        rect(g, 16, 22, 21, 23, 3)
    else:
        rect(g, 7, 18, 10, 22, 1)
        rect(g, 12, 18, 15, 22, 1)
        rect(g, 5, 23, 10, 23, 3)
        rect(g, 11, 23, 16, 23, 3)
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


STAND = soldier(False, False)
RUN = soldier(True, False)
LIE = lying(False)
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
# A compact circular shot leaves space between the action without reading as a
# square block at NES resolution.
BULLET = ["...33...", "..3333..", ".332233.", ".322223.", ".322223.", ".332233.",
          "..3333..", "...33..."]
BOSS_BULLET = ["........", ".222222.", ".233332.", ".233332.", ".233332.", ".233332.",
               ".222222.", "........"]
EXPLOSION = ["...33...", ".3.33.3.", "..3223..", "33222233", "33222233", "..3223..",
             ".3.33.3.", "...33..."]
ARROW = ["..3.....", "..33....", "..333...", "..3333..", "..333...", "..33....",
         "..3.....", "........"]

# tile numbers (keep in sync with src/main.c)
T_STAND, T_RUN, T_LIE = 0x62, 0x6B, 0x74
T_BULLET = 11
T_ENEMY_A, T_ENEMY_B, T_CAPSULE, T_BOSS = 0x7D, 0x86, 0x98, 0xA0
T_BOSS_BULLET, T_EXPLOSION, T_ARROW = 37, 38, 42

blit(STAND, T_STAND, 3)
blit(RUN, T_RUN, 3)
blit(LIE, T_LIE, 3)
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

# ---- editable sprite source ------------------------------------------------
# Sprites live in a single transparent true-colour PNG so they can be adjusted
# in ordinary image editors.  The converter accepts RGB or RGBA PNGs; use the
# four colours documented in assets/README.md.  These are deliberately vivid
# editor colours; each still maps to one of the NES palette indices.  A
# one-pixel change maps
# directly to one NES pixel, so no resampling is involved.
SPRITE_SHEET = os.path.join(os.path.dirname(__file__), "..", "assets", "sprites.png")
COLOURS = {0: (0, 0, 0, 0), 1: (24, 38, 89, 255),
           2: (42, 122, 201, 255), 3: (255, 211, 94, 255)}
COLOUR_VALUES = {rgb[:3]: value for value, rgb in COLOURS.items() if value}


def png_rows(path):
    """Read a non-interlaced RGB/RGBA PNG without requiring external modules."""
    data = open(path, "rb").read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG file")
    pos = 8
    chunks = []
    while pos < len(data):
        size = struct.unpack(">I", data[pos:pos + 4])[0]
        kind = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + size]
        pos += size + 12
        chunks.append((kind, body))
    header = next(body for kind, body in chunks if kind == b"IHDR")
    width, height, depth, colour, compression, filtering, interlace = struct.unpack(">IIBBBBB", header)
    if depth != 8 or colour not in (2, 6) or compression or filtering or interlace:
        raise ValueError("sprites.png must be a non-interlaced 8-bit RGB or RGBA PNG")
    bpp = 4 if colour == 6 else 3
    raw = zlib.decompress(b"".join(body for kind, body in chunks if kind == b"IDAT"))
    stride = width * bpp
    rows, previous, offset = [], [0] * stride, 0
    for _ in range(height):
        mode = raw[offset]
        source = list(raw[offset + 1:offset + 1 + stride])
        offset += stride + 1
        row = [0] * stride
        for x, value in enumerate(source):
            left = row[x - bpp] if x >= bpp else 0
            above = previous[x]
            upper_left = previous[x - bpp] if x >= bpp else 0
            if mode == 1: value = (value + left) & 255
            elif mode == 2: value = (value + above) & 255
            elif mode == 3: value = (value + ((left + above) >> 1)) & 255
            elif mode == 4:
                p, pa, pb, pc = left + above - upper_left, 0, 0, 0
                pa, pb, pc = abs(p - left), abs(p - above), abs(p - upper_left)
                value = (value + (left if pa <= pb and pa <= pc else above if pb <= pc else upper_left)) & 255
            elif mode != 0: raise ValueError("sprites.png uses an unsupported PNG filter")
            row[x] = value
        rows.append(row)
        previous = row
    return width, height, bpp, rows


def sprite_value(row, x, bpp):
    pixel = row[x * bpp:x * bpp + bpp]
    if bpp == 4 and pixel[3] == 0:
        return 0
    try:
        return COLOUR_VALUES[tuple(pixel[:3])]
    except KeyError:
        raise ValueError("sprites.png has a pixel outside the documented four-colour palette")


def import_sprite_sheet(path):
    width, height, bpp, rows = png_rows(path)
    if (width, height) != (128, 64):
        raise ValueError("sprites.png must be exactly 128x64 pixels")
    regions = ((T_STAND, 0, 0, 3, 3), (T_RUN, 24, 0, 3, 3),
               (T_LIE, 48, 0, 3, 1), (T_ENEMY_A, 72, 0, 3, 3),
               (T_ENEMY_B, 96, 0, 3, 3), (T_BULLET, 0, 24, 1, 1),
               (T_BOSS_BULLET, 8, 24, 1, 1), (T_EXPLOSION, 16, 24, 1, 1),
               (T_ARROW, 24, 24, 1, 1), (T_CAPSULE, 32, 24, 2, 2),
               (T_BOSS, 48, 24, 5, 5))
    for base, left, top, w_tiles, h_tiles in regions:
        for y in range(h_tiles * 8):
            for x in range(w_tiles * 8):
                tile(base + (y // 8) * w_tiles + x // 8)[y % 8][x % 8] = sprite_value(rows[top + y], left + x, bpp)


def write_sprite_sheet(path):
    width, height = 128, 64
    pixels = [[0] * width for _ in range(height)]
    regions = ((T_STAND, 0, 0, 3, 3), (T_RUN, 24, 0, 3, 3),
               (T_LIE, 48, 0, 3, 1), (T_ENEMY_A, 72, 0, 3, 3),
               (T_ENEMY_B, 96, 0, 3, 3), (T_BULLET, 0, 24, 1, 1),
               (T_BOSS_BULLET, 8, 24, 1, 1), (T_EXPLOSION, 16, 24, 1, 1),
               (T_ARROW, 24, 24, 1, 1), (T_CAPSULE, 32, 24, 2, 2),
               (T_BOSS, 48, 24, 5, 5))
    for base, left, top, w_tiles, h_tiles in regions:
        for y in range(h_tiles * 8):
            for x in range(w_tiles * 8):
                pixels[top + y][left + x] = tile(base + (y // 8) * w_tiles + x // 8)[y % 8][x % 8]
    raw = b"".join(b"\0" + b"".join(bytes(COLOURS[value]) for value in row) for row in pixels)
    chunk = lambda kind, body: struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body) & 0xffffffff)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "wb") as output:
        output.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))

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
T_SKY, T_MOUNTAIN_PEAK, T_MOUNTAIN_SHADE = 0xD2, 0xD3, 0xD4
sky = tile(T_SKY)
for y in range(8):
    for x in range(8):
        # A nearly-solid midnight tile with sparse pinprick stars gives the
        # level a proper deep backdrop rather than an empty black field.
        sky[y][x] = 1
        if (x * 5 + y * 3) % 29 == 0: sky[y][x] = 2
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
        mt[y][x] = 1 if y < 2 else 2
        if y >= 4 and (x + y * 2) % 5 == 0: mt[y][x] = 3
peak = tile(T_MOUNTAIN_PEAK)
for y in range(8):
    for x in range(8):
        peak[y][x] = 0 if y < 4 - x // 2 else (3 if x < 3 and y < 6 else 2)
shade = tile(T_MOUNTAIN_SHADE)
for y in range(8):
    for x in range(8):
        shade[y][x] = 1 if (x + y) % 4 else 2
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
if len(sys.argv) == 3 and sys.argv[1] == "--export-sprites":
    write_sprite_sheet(sys.argv[2])
    sys.exit(0)
if len(sys.argv) != 2:
    raise SystemExit("usage: gen_chr.py OUTPUT.chr | --export-sprites OUTPUT.png")
if not os.path.exists(SPRITE_SHEET):
    raise SystemExit("missing editable sprite sheet: " + SPRITE_SHEET)
import_sprite_sheet(SPRITE_SHEET)
for i, t in tiles.items():
    bank[i * 16:i * 16 + 16] = encode(t)
with open(sys.argv[1], "wb") as f:
    f.write(bytes(bank) * 2)
