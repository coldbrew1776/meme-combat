/* Meme Blitz - a Contra style NES game (cc65). Level 1: Meme Zone. */
#include <string.h>
#define REG(a) (*(volatile unsigned char *)(a))
#define PPUCTRL   REG(0x2000)
#define PPUMASK   REG(0x2001)
#define PPUSTATUS REG(0x2002)
#define PPUSCROLL REG(0x2005)
#define PPUADDR   REG(0x2006)
#define PPUDATA   REG(0x2007)
#define OAMDMA    REG(0x4014)
#define JOY1      REG(0x4016)
#define JOY2      REG(0x4017)
#define APU_P1    REG(0x4000)
#define APU_P1LO  REG(0x4002)
#define APU_P1HI  REG(0x4003)
#define APU_P2    REG(0x4004)
#define APU_P2LO  REG(0x4006)
#define APU_P2HI  REG(0x4007)
#define APU_TRI   REG(0x4008)
#define APU_TRILO REG(0x400A)
#define APU_TRIHI REG(0x400B)
#define APU_NOISE REG(0x400C)
#define APU_NZLO  REG(0x400E)
#define APU_NZHI  REG(0x400F)
#define APU_ON    REG(0x4015)
#define OAM       ((unsigned char *)0x0200)

/* controller bits */
#define BTN_A 0x80
#define BTN_B 0x40
#define BTN_SELECT 0x20
#define BTN_START 0x10
#define BTN_UP 0x08
#define BTN_DOWN 0x04
#define BTN_LEFT 0x02
#define BTN_RIGHT 0x01

/* tile numbers (keep in sync with tools/gen_chr.py) */
#define T_STAND 0x62
#define T_RUN 0x6B
#define T_LIE 0x74
#define T_BULLET 11
#define T_ENEMY_A 0x7D
#define T_ENEMY_B 0x86
#define T_CAPSULE 0x98
#define T_BOSS 0xA0
#define T_BOSS_BULLET 37
#define T_EXPLOSION 38
#define T_ARROW 42
#define T_GRASS 0x5B
#define T_EARTH 0x5C
#define T_CLOUD 0x5D
#define T_MOUNTAIN 0x5E
#define T_PINE 0x5F
#define T_LOGO 0x60
#define T_PLATFORM 0x61
#define T_SKY 0xD2
#define T_MOUNTAIN_PEAK 0xD3
#define T_MOUNTAIN_SHADE 0xD4
#define T_MOON_A 0xD5
#define T_MOON_B 0xD6
#define T_MOON_C 0xD7
#define T_MOON_D 0xD8

#define GROUND 192          /* y of the players' feet */
#define LEVEL_END 1800      /* camera stops here and the boss arrives */
#define MAX_PB 12
#define MAX_BB 6
#define MAX_EN 6
#define BOSS_HP 30
#define NUM_PU 2

typedef struct {
    int x, y;               /* world x, feet y */
    signed char vy;
    unsigned char face;     /* 0 right, 1 left */
    unsigned char lie;
    unsigned char state;    /* 0 out, 1 alive, 2 dead (waiting to respawn) */
    unsigned char lives;
    unsigned char timer;    /* respawn delay */
    unsigned char inv;      /* invulnerability frames */
    unsigned char wpn;      /* 0 normal, 1 spread, 2 rapid */
    unsigned char cool;
    unsigned char step;
    unsigned char moving;
    unsigned char attack;
    unsigned char jump_buffer, coyote;
} Player;

static Player pl[2];
static unsigned char pad[2], pressed[2], old_pad[2];
static unsigned char nplayers;
static int cam;
static unsigned char frame, oam_n, rng = 0x5A, title_anim, freeze_frame;
/* Advanced by game logic, rather than by rendering, for stable animation. */
static unsigned char anim_timer;

static int pb_x[MAX_PB]; static unsigned char pb_y[MAX_PB];
static signed char pb_dx[MAX_PB], pb_dy[MAX_PB]; static unsigned char pb_on[MAX_PB];
static int bb_x[MAX_BB]; static unsigned char bb_y[MAX_BB], bb_on[MAX_BB];
static int en_x[MAX_EN]; static unsigned char en_on[MAX_EN], en_spd[MAX_EN];
static unsigned char spawn_t;
static unsigned char boss_on, boss_hp, boss_flash, boss_shot, boss_dying;
static int boss_x; static unsigned char boss_y;
static unsigned int score;
static unsigned char level_number = 1, shot_sound, death_sound, victory_sound;
/* The capsules sit just above usable ledges, rather than out in the sky. */
static const int pu_world_x[NUM_PU] = { 670, 1170 };
static unsigned char pu_state[NUM_PU], pu_y[NUM_PU];

static const unsigned char palette[32] = {
    /* background */
    0x0F, 0x0C, 0x1C, 0x30,  0x0F, 0x01, 0x11, 0x28,
    0x0F, 0x00, 0x11, 0x21,  0x0F, 0x06, 0x16, 0x26,
    /* sprites */
    0x0F, 0x11, 0x27, 0x30,  0x0F, 0x16, 0x27, 0x30,
    0x0F, 0x00, 0x10, 0x30,  0x0F, 0x06, 0x16, 0x26
};

/* Relaxed Am - F - C - G loop: plucked pulse arpeggio over a triangle bass.
   Pulse 2 is kept free for shots, noise for the gunfire crack. */
static const unsigned int music_arp[4][4] = {
    { 253, 213, 169, 126 }, { 319, 253, 213, 159 },
    { 213, 169, 142, 106 }, { 284, 225, 189, 142 }
};
static const unsigned int music_bass[4] = { 507, 640, 427, 570 };
static const unsigned char arp_order[8] = { 0, 1, 2, 3, 2, 1, 2, 1 };
static const unsigned char title_blue[8] = { 0x02, 0x12, 0x22, 0x32, 0x22, 0x12, 0x02, 0x01 };
static const unsigned int victory_notes[8] = { 213, 169, 142, 106, 142, 106, 84, 106 };

static const char *const art[7][5] = {
    { "#..#", "####", "####", "#..#", "#..#" },   /* M */
    { "####", "#...", "###.", "#...", "####" },   /* E */
    { "###.", "#..#", "###.", "#..#", "###." },   /* B */
    { "#...", "#...", "#...", "#...", "####" },   /* L */
    { "####", ".##.", ".##.", ".##.", "####" },   /* I */
    { "####", ".##.", ".##.", ".##.", ".##." },   /* T */
    { "####", "...#", "..#.", ".#..", "####" }    /* Z */
};

/* ---------------------------------------------------------------- PPU --- */

static void wait_vblank(void) {
    while (!(PPUSTATUS & 0x80)) ;
}

static void ppu_addr(unsigned int a) {
    (void)PPUSTATUS;
    PPUADDR = a >> 8;
    PPUADDR = a & 0xFF;
}

static void fill_nt(unsigned int base, unsigned char tile, unsigned char attr) {
    unsigned int i;
    ppu_addr(base);
    for (i = 0; i < 960; ++i) PPUDATA = tile;
    for (i = 0; i < 64; ++i) PPUDATA = attr;
}

static void put_text(unsigned char col, unsigned char row, const char *s) {
    ppu_addr(0x2000 + (unsigned int)row * 32 + col);
    while (*s) { PPUDATA = (*s == ' ') ? 0 : *s; ++s; }
}

static void load_palette(void) {
    unsigned char i;
    ppu_addr(0x3F00);
    for (i = 0; i < 32; ++i) PPUDATA = palette[i];
}

static void screen_off(void) { PPUMASK = 0; }
static void screen_on(void) {
    /* Both pattern tables are at $0000.  Set the scroll latch while the
       display is still off so the first visible frame is the finished one. */
    PPUCTRL = 0; cam = 0;
    ppu_addr(0x2000);
    PPUSCROLL = 0; PPUSCROLL = 0;
    PPUMASK = 0x1E;
}

static void oam_clear_from(unsigned char n) {
    unsigned char i;
    for (i = n; i < 64; ++i) OAM[i * 4] = 0xF0;
}

/* Animated blue gradient: logo bands use palettes 1-3, each offset in time. */
static void title_palette(void) {
    unsigned char p, t = frame >> 2;
    for (p = 1; p < 4; ++p) {
        ppu_addr(0x3F00 + p * 4 + 1);
        PPUDATA = 0x01;
        PPUDATA = title_blue[(t + p * 3) & 7];
    }
}

/* wait for vblank, upload sprites, apply scroll */
static void present(void) {
    oam_clear_from(oam_n);
    wait_vblank();
    OAMDMA = 2;
    if (title_anim) title_palette();
    PPUCTRL = (cam >> 8) & 1;
    PPUSCROLL = cam & 0xFF;
    PPUSCROLL = 0;
    oam_n = 0;
    if (!freeze_frame) ++frame;
}

static void add_spr(int sx, int sy, unsigned char tile, unsigned char attr) {
    unsigned char *o;
    if (oam_n >= 64 || sx < 0 || sx > 248 || sy < 1 || sy > 238) return;
    o = OAM + oam_n * 4;
    o[0] = sy - 1; o[1] = tile; o[2] = attr; o[3] = sx;
    ++oam_n;
}

/* 16x16 metasprite, tiles base..base+3 (TL, TR, BL, BR) */
static void add_spr16(int sx, int sy, unsigned char base, unsigned char attr, unsigned char flip) {
    unsigned char l = flip ? 1 : 0, r = flip ? 0 : 1;
    if (flip) attr |= 0x40;
    add_spr(sx, sy, base + l, attr);
    add_spr(sx + 8, sy, base + r, attr);
    add_spr(sx, sy + 8, base + 2 + l, attr);
    add_spr(sx + 8, sy + 8, base + 2 + r, attr);
}

/* 24x24 metasprite, 3x3 tiles row-major */
static void add_spr24(int sx, int sy, unsigned char base, unsigned char attr, unsigned char flip) {
    unsigned char r, c;
    if (flip) attr |= 0x40;
    for (r = 0; r < 3; ++r)
        for (c = 0; c < 3; ++c)
            add_spr(sx + c * 8, sy + r * 8, base + r * 3 + (flip ? 2 - c : c), attr);
}

/* A 40-pixel boss is visibly larger than the old 32-pixel sprite while
   leaving enough OAM slots for the players, shots, and HUD. */
static void add_spr40(int sx, int sy, unsigned char base, unsigned char attr) {
    unsigned char r, c;
    for (r = 0; r < 5; ++r)
        for (c = 0; c < 5; ++c) add_spr(sx + c * 8, sy + r * 8, base + r * 5 + c, attr);
}

static void add_text(int sx, int sy, const char *s) {
    while (*s) { if (*s != ' ') add_spr(sx, sy, *s, 0); sx += 8; ++s; }
}

static void add_score(unsigned int value) {
    unsigned char digit, i;
    for (i = 0; i < 5; ++i) {
        digit = value / 10000;
        add_spr(104 + i * 8, 8, '0' + digit, 0);
        value = (value - (unsigned int)digit * 10000) * 10;
    }
}

static void sound_off(void) { APU_ON = 0; }

static void sound_start(void) {
    APU_ON = 0x0F;
    APU_P1 = 0x43;                 /* 25% duty, short decaying pluck */
    APU_P2 = 0x7F;
    APU_TRI = 0xC0;
    shot_sound = 0; death_sound = 0; victory_sound = 0;
}

/* Bullet: a noise crack plus a fast falling "pew" on pulse 2. */
static void sound_shoot(void) {
    APU_NOISE = 0x05;              /* decaying envelope */
    APU_NZLO = 0x03;
    APU_NZHI = 0x08;
    APU_P2 = 0x7F;
    APU_P2LO = 0x30;
    APU_P2HI = 0x08;
    shot_sound = 8;
}

/* Sad descending wail on pulse 2 that fades out. */
static void sound_death(void) {
    shot_sound = 0;
    death_sound = 48;
    APU_P2 = 0xBF;
    APU_P2LO = 0xA0;
    APU_P2HI = 0x08;
}

static void sound_boss_defeat(void) {
    shot_sound = death_sound = 0;
    victory_sound = 180;
    APU_NOISE = 0x0F;
    APU_NZLO = 0x04;
    APU_NZHI = 0x18;
}

static void sound_update(void) {
    unsigned int note;
    unsigned char chord = (frame >> 7) & 3;
    if (victory_sound) {
        unsigned char beat = (180 - victory_sound) >> 3;
        if ((victory_sound & 7) == 0) {
            note = victory_notes[beat & 7];
            APU_P1 = 0x47; APU_P1LO = note & 0xFF; APU_P1HI = (note >> 8) & 7;
            APU_TRILO = (note << 1) & 0xFF; APU_TRIHI = (note >> 7) & 7;
        }
        if ((victory_sound % 18) == 0) {
            APU_NOISE = 0x0C; APU_NZLO = 0x03 + (beat & 3); APU_NZHI = 0x08;
        }
        --victory_sound;
        return;
    }
    if ((frame & 15) == 0) {
        note = music_arp[chord][arp_order[(frame >> 4) & 7]];
        APU_P1 = 0x43;
        APU_P1LO = note & 0xFF; APU_P1HI = (note >> 8) & 7;
    }
    if ((frame & 127) == 0) {
        note = music_bass[chord];
        APU_TRILO = note & 0xFF; APU_TRIHI = (note >> 8) & 7;
    }
    if (death_sound) {
        unsigned char t = 48 - death_sound;
        unsigned int period = 0xA0 + t * 6;
        APU_P2 = 0xB0 | (15 - t / 4);
        APU_P2LO = period & 0xFF;
        if (--death_sound == 0) APU_P2 = 0x30;
    } else if (shot_sound) {
        APU_P2LO = 0x30 + (8 - shot_sound) * 0x18;
        if (--shot_sound == 0) APU_P2 = 0x30;
    }
}

static unsigned char rnd(void) {
    rng = (rng << 1) ^ ((rng & 0x80) ? 0x1D : 0);
    return rng;
}

/* ------------------------------------------------------------- input --- */

static void read_pads(void) {
    unsigned char i, a = 0, b = 0;
    JOY1 = 1; JOY1 = 0;
    for (i = 0; i < 8; ++i) {
        a = (a << 1) | (JOY1 & 1);
        b = (b << 1) | (JOY2 & 1);
    }
    pad[0] = a; pad[1] = b;
    for (i = 0; i < 2; ++i) {
        pressed[i] = pad[i] & ~old_pad[i];
        old_pad[i] = pad[i];
    }
}

/* ------------------------------------------------------------ screens --- */

static void draw_letter(unsigned char col, unsigned char row, unsigned char idx) {
    unsigned char y, x;
    for (y = 0; y < 5; ++y) {
        ppu_addr(0x2000 + (unsigned int)(row + y) * 32 + col);
        for (x = 0; x < 4; ++x) PPUDATA = (art[idx][y][x] == '#') ? T_LOGO : 0;
    }
}

static void title_screen(void) {
    unsigned char i;
    static const unsigned char meme[4] = { 0, 1, 0, 1 };
    static const unsigned char blitz[5] = { 2, 3, 4, 5, 6 };
    sound_off();
    screen_off();
    /* Tile zero uses the universal background colour ($0F: black).  Filling
       the whole name table first guarantees that the title never exposes the
       emulator's power-on grey while the logo is being drawn. */
    fill_nt(0x2000, 0, 0);
    fill_nt(0x2400, 0, 0);
    load_palette();
    for (i = 0; i < 4; ++i) draw_letter(6 + i * 5, 4, meme[i]);
    for (i = 0; i < 5; ++i) draw_letter(3 + i * 5, 11, blitz[i]);
    /* attributes: logo rows alternate palettes 1-3 every 16 pixels */
    ppu_addr(0x23C0);
    for (i = 0; i < 64; ++i) {
        unsigned char by = i >> 3, top = by * 2, v = 0;
        if (by >= 1 && by <= 3) {
            unsigned char a = 1 + top % 3, b = 1 + (top + 1) % 3;
            v = a | (a << 2) | (b << 4) | (b << 6);
        }
        PPUDATA = v;
    }
    title_anim = 1;
    put_text(13, 19, "1 PLAYER");
    put_text(13, 21, "2 PLAYERS");
    put_text(11, 25, "PRESS START");
    put_text(8, 27, "SELECT CHOOSES PLAYERS");
    screen_on();
    nplayers = 1;
    for (;;) {
        read_pads();
        if (pressed[0] & BTN_SELECT) nplayers = 3 - nplayers;
        if (pressed[0] & BTN_START) break;
        add_spr(88, 19 * 8 + (nplayers - 1) * 16, T_ARROW, 0);
        present();
    }
    title_anim = 0;
}

static void message_screen(const char *l1, const char *l2, unsigned char frames) {
    screen_off();
    fill_nt(0x2000, 0, 0);
    load_palette();
    put_text(16 - (unsigned char)strlen(l1) / 2, 11, l1);
    put_text(16 - (unsigned char)strlen(l2) / 2, 14, l2);
    screen_on();
    while (frames--) present();
}

/* ---------------------------------------------------------- level BG --- */

static void build_level_bg(void) {
    unsigned char nt, col, row, h, top, c;
    unsigned int base;
    screen_off();
    load_palette();
    for (nt = 0; nt < 2; ++nt) {
        base = nt ? 0x2400 : 0x2000;
        ppu_addr(base);
        for (row = 0; row < 30; ++row) {
            for (col = 0; col < 32; ++col) {
                c = nt * 32 + col;
                /* Cool slate ground with electric-blue seams replaces earth. */
                h = 4 + ((c * 3 + 5) % 9);
                top = 22 - h;
                if (row >= 25) PPUDATA = T_EARTH;
                else if (row == 24) PPUDATA = T_GRASS;
                /* Solid ledges: three heights provide stepping stones. */
                else if ((row == 20 && c >= 18 && c <= 25) ||
                         (row == 18 && c >= 38 && c <= 46) ||
                         (row == 21 && c >= 56 && c <= 62)) PPUDATA = T_PLATFORM;
                /* A distant, cratered moon replaces the former clouds. */
                else if (c >= 10 && c <= 11 && row >= 3 && row <= 4)
                    PPUDATA = (row == 3) ? (c == 10 ? T_MOON_A : T_MOON_B) : (c == 10 ? T_MOON_C : T_MOON_D);
                else if (c >= 45 && c <= 46 && row >= 5 && row <= 6)
                    PPUDATA = (row == 5) ? (c == 45 ? T_MOON_A : T_MOON_B) : (c == 45 ? T_MOON_C : T_MOON_D);
                /* Jagged slate ridges make the horizon read as lunar terrain. */
                else if (row == top) PPUDATA = T_MOUNTAIN_PEAK;
                else if (row > top && row < 22)
                    PPUDATA = ((c + row) % 5 == 0) ? T_MOUNTAIN_SHADE : T_MOUNTAIN;
                else if (row >= 19 && (c % 7 == 2 || c % 11 == 5)) PPUDATA = T_MOUNTAIN_SHADE;
                else PPUDATA = T_SKY;
            }
        }
        /* attributes: sky pal0, mountains pal1, ground pal2 */
        for (row = 0; row < 8; ++row)
            for (col = 0; col < 8; ++col)
                PPUDATA = (row < 3) ? 0x00 : (row < 6) ? 0x55 : 0xAA;
    }
}

/* -------------------------------------------------------------- logic --- */

static unsigned char overlap(int ax, int ay, int aw, int ah, int bx, int by, int bw, int bh) {
    return ax < bx + bw && bx < ax + aw && ay < by + bh && by < ay + ah;
}

static void new_game(void) {
    unsigned char i;
    cam = 0; frame = anim_timer = 0; spawn_t = 60; score = 0;
    boss_on = boss_dying = 0; boss_hp = BOSS_HP; boss_flash = 0; boss_shot = 0; boss_y = 136;
    for (i = 0; i < MAX_PB; ++i) pb_on[i] = 0;
    for (i = 0; i < MAX_BB; ++i) bb_on[i] = 0;
    for (i = 0; i < MAX_EN; ++i) en_on[i] = 0;
    for (i = 0; i < NUM_PU; ++i) { pu_state[i] = 0; pu_y[i] = 132; }
    for (i = 0; i < 2; ++i) {
        pl[i].x = 24 + i * 24; pl[i].y = GROUND; pl[i].vy = 0; pl[i].face = 0;
        pl[i].lie = 0; pl[i].lives = 3; pl[i].timer = 0; pl[i].inv = 60;
        pl[i].wpn = 0; pl[i].cool = 0; pl[i].step = 0; pl[i].moving = pl[i].attack = 0;
        pl[i].jump_buffer = pl[i].coyote = 0;
        pl[i].state = (i < nplayers) ? 1 : 0;
    }
}

static void fire_bullet(Player *p, signed char dx, signed char dy) {
    unsigned char i;
    for (i = 0; i < MAX_PB; ++i) {
        if (pb_on[i]) continue;
        pb_on[i] = 1;
        pb_x[i] = p->face ? p->x - 6 : p->x + 22;
        pb_y[i] = p->lie ? p->y - 6 : p->y - 15;
        pb_dx[i] = p->face ? -dx : dx;
        pb_dy[i] = dy;
        if (!death_sound) sound_shoot();
        return;
    }
}

static void player_shoot(Player *p, unsigned char btn_pressed, unsigned char btn_held) {
    if (p->cool) --p->cool;
    if (p->cool) return;
    if (p->wpn == 2) {
        if (!btn_held) return;
        fire_bullet(p, 6, 0); p->cool = 5; p->attack = 7;
    } else if (btn_pressed) {
        if (p->wpn == 1) {
            fire_bullet(p, 6, -2); fire_bullet(p, 6, 0); fire_bullet(p, 6, 2);
            p->cool = 12; p->attack = 9;
        } else {
            fire_bullet(p, 6, 0); p->cool = 8; p->attack = 9;
        }
    }
}

static void kill_player(Player *p) {
    if (p->inv) return;
    p->state = 2; p->timer = 70; p->wpn = 0;
    sound_death();
    if (p->lives) --p->lives;
}

/* The landscape repeats every two name tables (512 pixels).  Return the
   walkable top under a player's centre; every other location is ground. */
static unsigned char platform_floor(int x) {
    unsigned int local = (unsigned int)x & 0x01FF;
    if (local >= 144 && local <= 207) return 160;
    if (local >= 304 && local <= 375) return 144;
    if (local >= 448 && local <= 503) return 168;
    return GROUND;
}

static void update_player(unsigned char i) {
    Player *p = &pl[i];
    unsigned char pd = pad[i];
    unsigned char ground, floor;
    int old_y;
    if (p->state == 2) {
        if (--p->timer == 0) {
            if (p->lives) {
                p->state = 1; p->x = cam + 32; p->y = 40; p->vy = 0; p->inv = 100;
            } else p->state = 0;
        }
        return;
    }
    if (p->state == 0) return;
    if (p->inv) --p->inv;
    if (p->attack) --p->attack;
    p->moving = 0;
    floor = platform_floor(p->x + 12);
    ground = (p->y == floor);
    /* Keep a short input buffer and a few frames of grace after an edge.
       This makes jumping dependable even while running across ledges. */
    if (pressed[i] & BTN_A) p->jump_buffer = 6;
    else if (p->jump_buffer) --p->jump_buffer;
    if (ground) p->coyote = 6;
    else if (p->coyote) --p->coyote;
    p->lie = ground && (pd & BTN_DOWN);
    if (!p->lie) {
        if (pd & BTN_LEFT) { p->x -= 3; p->face = 1; ++p->step; p->moving = 1; }
        else if (pd & BTN_RIGHT) { p->x += 3; p->face = 0; ++p->step; p->moving = 1; }
        floor = platform_floor(p->x + 12);
        ground = (p->y == floor);
        /* A is the only jump input; B is passed exclusively to shooting. */
        if (p->jump_buffer && p->coyote) {
            p->vy = -10; p->jump_buffer = 0; p->coyote = 0;
        }
    }
    if (p->x < cam) p->x = cam;
    if (p->x > cam + 232) p->x = cam + 232;
    /* jump physics: strong gravity applied every frame for a smooth arc */
    if (p->y < GROUND || p->vy < 0) {
        old_y = p->y;
        p->y += p->vy;
        if (p->vy < 10) ++p->vy;
        floor = platform_floor(p->x + 12);
        if (p->vy >= 0 && old_y <= floor && p->y >= floor) { p->y = floor; p->vy = 0; }
    }
    player_shoot(p, pressed[i] & BTN_B, pd & BTN_B);
}

static void update_camera(void) {
    unsigned char i;
    int want;
    if (boss_on) return;
    for (i = 0; i < 2; ++i) {
        if (pl[i].state != 1) continue;
        want = pl[i].x - 112;
        if (want > cam) cam = want;
    }
    if (cam >= LEVEL_END) { cam = LEVEL_END; boss_on = 1; boss_x = cam + 260; }
}

static void update_bullets(void) {
    unsigned char i, j;
    int sx;
    for (i = 0; i < MAX_PB; ++i) {
        if (!pb_on[i]) continue;
        pb_x[i] += pb_dx[i];
        pb_y[i] += pb_dy[i];
        sx = pb_x[i] - cam;
        if (sx < -8 || sx > 256 || pb_y[i] < 8 || pb_y[i] > 200) { pb_on[i] = 0; continue; }
        for (j = 0; j < MAX_EN; ++j) {
            if (en_on[j] == 1 && overlap(pb_x[i] + 2, pb_y[i] + 2, 4, 4, en_x[j] + 7, GROUND - 24, 10, 24)) {
                en_on[j] = 2; score += 100 * level_number; pb_on[i] = 0; break;   /* 2 = dying */
            }
        }
        if (!pb_on[i]) continue;
        for (j = 0; j < NUM_PU; ++j) {
            if (pu_state[j] == 0 && overlap(pb_x[i] + 2, pb_y[i] + 2, 4, 4, pu_world_x[j], pu_y[j], 16, 16)) {
                pu_state[j] = 1; pb_on[i] = 0; break;
            }
        }
        if (!pb_on[i]) continue;
        if (boss_on && !boss_dying && overlap(pb_x[i] + 2, pb_y[i] + 2, 4, 4, boss_x + 2, boss_y + 2, 36, 38)) {
            pb_on[i] = 0; boss_flash = 4;
            if (boss_hp) --boss_hp;
            if (!boss_hp) { score += 1000 * level_number; boss_dying = 90; sound_boss_defeat(); for (j = 0; j < MAX_BB; ++j) bb_on[j] = 0; }
        }
    }
}

static void update_enemies(void) {
    unsigned char i;
    if (!boss_on && --spawn_t == 0) {
        spawn_t = 35 + (rnd() & 31);
        for (i = 0; i < MAX_EN; ++i) {
            if (en_on[i]) continue;
            en_on[i] = 1; en_x[i] = cam + 258; en_spd[i] = 2 + (rnd() & 1);
            break;
        }
    }
    for (i = 0; i < MAX_EN; ++i) {
        if (en_on[i] == 1) {
            en_x[i] -= en_spd[i];
            if (en_x[i] < cam - 24) en_on[i] = 0;
        } else if (en_on[i] >= 2) {
            if (++en_on[i] > 12) en_on[i] = 0;
        }
    }
}

static void update_boss(void) {
    unsigned char i;
    int target;
    if (!boss_on) return;
    if (boss_flash) --boss_flash;
    if (boss_dying) { --boss_dying; return; }
    target = cam + 196 + ((frame & 64) ? (frame & 63) : (63 - (frame & 63))) / 3;
    if (boss_x > target) boss_x -= 2;
    else if (boss_x < target) boss_x += 1;
    boss_y = 132 + (((frame & 64) ? (frame & 63) : (63 - (frame & 63))) >> 3);
    if (boss_x < cam + 250 && ++boss_shot >= 45) {
        boss_shot = 0;
        for (i = 0; i < MAX_BB; ++i) {
            if (bb_on[i]) continue;
            bb_on[i] = 1; bb_x[i] = boss_x - 6;
            bb_y[i] = boss_y + 22;                  /* red alien blast */
            break;
        }
    }
    for (i = 0; i < MAX_BB; ++i) {
        if (!bb_on[i]) continue;
        bb_x[i] -= 4;
        if (bb_x[i] < cam - 8) bb_on[i] = 0;
    }
}

static void check_damage(void) {
    unsigned char i, j;
    int px, py, ph;
    for (i = 0; i < 2; ++i) {
        Player *p = &pl[i];
        if (p->state != 1 || p->inv) continue;
        /* Chomp is rounder than the former soldier: keep collisions inside
           its visible blue body instead of its transparent tail and bite. */
        px = p->x + 4;
        ph = p->lie ? 18 : 21;
        py = p->y - ph;
        for (j = 0; j < MAX_EN; ++j)
            if (en_on[j] == 1 && overlap(px, py, 16, ph, en_x[j] + 7, GROUND - 24, 10, 24)) kill_player(p);
        for (j = 0; j < MAX_BB; ++j)
            if (bb_on[j] && overlap(px, py, 16, ph, bb_x[j] + 1, bb_y[j] + 1, 6, 6)) kill_player(p);
        if (boss_on && !boss_dying && overlap(px, py, 16, ph, boss_x + 4, boss_y + 3, 32, 36)) kill_player(p);
        for (j = 0; j < NUM_PU; ++j)
            if (pu_state[j] == 1 && overlap(px, py, 16, ph, pu_world_x[j], pu_y[j], 16, 16)) {
                p->wpn = j + 1; pu_state[j] = 2;
            }
    }
}

static void update_powerups(void) {
    unsigned char i;
    for (i = 0; i < NUM_PU; ++i) {
        if (pu_state[i] == 0) pu_y[i] = 132 + ((frame >> 3) & 3) * 2;
        else if (pu_state[i] == 1 && pu_y[i] < GROUND - 16) pu_y[i] += 2;
    }
}

/* ------------------------------------------------------------ drawing --- */

static void draw_all(void) {
    unsigned char i, base;
    int sx;
    for (i = 0; i < 2; ++i) {
        Player *p = &pl[i];
        if (p->state == 2 && p->timer > 6 && (p->timer > 24 || (p->timer & 2))) {
            /* death: tumble up, fall, then lie flat and blink out */
            unsigned char t = 70 - p->timer;
            int dy = (t < 24) ? (int)t * (24 - t) / 8 : 0;
            unsigned char fl = (t < 24) ? 0x80 : 0;
            sx = p->x - cam;
            add_spr24(sx, p->y - 24 - dy, T_STAND, i | fl, p->face);
            continue;
        }
        if (p->state != 1 || (p->inv & 2)) continue;
        sx = p->x - cam;
        if (p->lie) {
            add_spr24(sx, p->y - 20, T_LIE, i, p->face);
        } else {
            if (p->moving) base = ((anim_timer >> 3) & 1) ? T_RUN : T_STAND;
            else base = T_STAND;
            add_spr24(sx, p->y - 24, base, i, p->face);
        }
    }
    for (i = 0; i < MAX_EN; ++i) {
        if (!en_on[i]) continue;
        sx = en_x[i] - cam;
        if (en_on[i] == 1)
            add_spr24(sx, GROUND - 24, ((en_x[i] >> 3) & 1) ? T_ENEMY_A : T_ENEMY_B, 2, 1);
        else
            add_spr(sx + 8, GROUND - 16, T_EXPLOSION, 2);
    }
    for (i = 0; i < MAX_PB; ++i)
        if (pb_on[i]) add_spr(pb_x[i] - cam, pb_y[i], T_BULLET, 3);
    for (i = 0; i < MAX_BB; ++i)
        if (bb_on[i]) add_spr(bb_x[i] - cam, bb_y[i], T_BOSS_BULLET, 3);
    for (i = 0; i < NUM_PU; ++i) {
        sx = pu_world_x[i] - cam;
        if (pu_state[i] == 0 || pu_state[i] == 1) {
            add_spr16(sx, pu_y[i], T_CAPSULE, 0, 0);
            if (pu_state[i] == 1) add_spr(sx + 5, pu_y[i] + 4, i ? 'R' : 'S', 3);
        }
    }
    if (boss_on) {
        sx = boss_x - cam;
        if (boss_dying) {
            if (frame & 2) {
                add_spr(sx + (rnd() % 40), boss_y + (rnd() % 40), T_EXPLOSION, 3);
                add_spr(sx + (rnd() % 40), boss_y + (rnd() % 40), T_EXPLOSION, 3);
            }
        } else if (!(boss_flash & 2)) {
            add_spr40(sx, boss_y, T_BOSS, 2);
        }
    }
    /* HUD: lives, boss health bar */
    add_text(8, 8, "P1");
    add_spr(28, 8, '0' + pl[0].lives, 0);
    if (nplayers == 2) {
        add_text(200, 8, "P2");
        add_spr(220, 8, '0' + pl[1].lives, 0);
    }
    add_text(56, 8, "SCORE");
    add_score(score);
    if (boss_on) {
        add_text(8, 24, "BOSS");
        for (i = 0; i < (boss_hp + 1) / 2; ++i) add_spr(48 + i * 8, 24, T_BOSS_BULLET, 3);
    }
}

/* -------------------------------------------------------------- level --- */

/* Pause uses edge-triggered Start input, so holding Start when pausing does
   not immediately resume the game.  Rendering continues while frame-based
   game state and audio remain frozen. */
static void pause_game(void) {
    freeze_frame = 1;
    sound_off();
    for (;;) {
        read_pads();
        if ((pressed[0] | pressed[1]) & BTN_START) break;
        draw_all();
        add_text(104, 104, "PAUSED");
        present();
    }
    freeze_frame = 0;
    sound_start();
}

/* returns 1 if the level was cleared, 0 on game over */
static unsigned char play_level(void) {
    unsigned char i;
    message_screen("LEVEL 1", "MEME ZONE", 90);
    build_level_bg();
    new_game();
    sound_start();
    screen_on();
    for (;;) {
        read_pads();
        if ((pressed[0] | pressed[1]) & BTN_START) {
            pause_game();
            continue;
        }
        ++anim_timer;
        for (i = 0; i < 2; ++i) update_player(i);
        update_camera();
        update_bullets();
        update_enemies();
        update_boss();
        update_powerups();
        check_damage();
        sound_update();
        draw_all();
        present();
        if (boss_on && boss_dying == 1) return 1;
        if (pl[0].state == 0 && (nplayers == 1 || pl[1].state == 0)) return 0;
    }
}

void main(void) {
    PPUCTRL = 0; PPUMASK = 0;
    /* Let the PPU finish power-on before touching its address/data ports. */
    wait_vblank(); wait_vblank();
    oam_n = 0;
    for (;;) {
        title_screen();
        if (play_level()) message_screen("STAGE CLEAR", "MEME ZONE DEFEATED", 180);
        else message_screen("GAME OVER", "TRY AGAIN", 150);
    }
}
