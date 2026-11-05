"""Check campaign state on the host; hardware registers are replaced with RAM."""
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
source = (root / 'src/main.c').read_text()
source = source.replace('#define REG(a) (*(volatile unsigned char *)(a))',
                        'static unsigned char registers[65536];\n#define REG(a) registers[a]')
source = source.replace('void main(void)', 'void nes_main(void)')
harness = r'''
#include <assert.h>
int main(void) {
    nplayers = 2; level_number = 1; score = 0;
    start_level();
    assert(pl[0].lives == 3 && pl[1].state == 1 && boss_hp == 30);
    score = 1200; pl[0].lives = 2; pl[0].wpn = 1;
    pl[1].lives = 0; pl[1].state = 0;
    pb_on[0] = bb_on[0] = en_on[0] = pu_state[0] = 1;
    level_number = 2; start_level();
    assert(score == 1200 && pl[0].lives == 2 && pl[0].wpn == 1);
    assert(pl[1].state == 0 && pl[1].lives == 0);
    assert(!pb_on[0] && !bb_on[0] && !en_on[0] && !pu_state[0]);
    assert(cam == 0 && boss_hp == 40 && !boss_on);
    pl[0].x = LEVEL_END + 112; update_camera();
    assert(boss_on && cam == LEVEL_END);
    boss_x = cam + 200; boss_shot = 29; frame = 32;
    update_boss();
    assert(bb_on[0] && bb_y[0] == boss_y + 38);
    boss_hp = 1;
    pb_on[0] = 1; pb_x[0] = boss_x; pb_y[0] = boss_y + 12;
    pb_dx[0] = pb_dy[0] = 0;
    update_bullets();
    assert(boss_hp == 0 && boss_dying == 90 && score == 3200);
    assert(!bb_on[0] && victory_sound);
    level_number = 1; score = 0; start_level();
    assert(pl[0].lives == 3 && pl[1].state == 1 && !pl[0].wpn);
    /* Jump from the ground even when a one-way platform is overhead. */
    pl[0].x = 150; pad[0] = pressed[0] = BTN_A;
    update_player(0);
    assert(pl[0].y < GROUND && pl[0].vy < 0);
    pad[0] = pressed[0] = 0;
    /* Falling below a platform must still land on the ground. */
    pl[0].y = 185; pl[0].vy = 9;
    update_player(0);
    assert(pl[0].y == GROUND && pl[0].vy == 0);
    /* A buffered jump just before landing fires on the next update. */
    pl[0].y = 190; pl[0].vy = 4; pressed[0] = BTN_A;
    update_player(0); pressed[0] = 0; update_player(0);
    assert(pl[0].vy < 0 && pl[0].y < GROUND);
    /* Grace after leaving a ledge; consumed jumps cannot double jump. */
    pl[0].x = 194; pl[0].y = 160; pl[0].vy = 0;
    pad[0] = BTN_RIGHT; update_player(0);
    pressed[0] = BTN_A; update_player(0);
    assert(pl[0].vy < 0 && !pl[0].coyote);
    pl[0].vy = 2; update_player(0);
    assert(pl[0].vy == 3);
    /* The larger target accepts shots outside the dropped crate's bounds. */
    cam = 600; boss_on = 0; pu_state[0] = 0; pu_y[0] = 132;
    pb_on[0] = 1; pb_x[0] = pu_world_x[0] - 5; pb_y[0] = 132;
    pb_dx[0] = pb_dy[0] = 0; update_bullets();
    assert(pu_state[0] == 1 && !pb_on[0]);
    boss_on = 1; boss_dying = 0; frame = 0; update_boss();
    assert(boss_y == 143);
    frame = 63; update_boss(); assert(boss_y == 112);
    sound_boss_defeat(); sound_update();
    assert(APU_NOISE && victory_sound == 179 && APU_P1 == 0x47);
    frame = 0; level_number = 2; sound_start(); sound_update();
    assert(APU_P1LO == (lunar_arp[0][0] & 255));
    assert(APU_TRILO == (lunar_bass[0] & 255));
    return 0;
}
'''
with tempfile.TemporaryDirectory() as directory:
    path = Path(directory)
    (path / 'campaign.c').write_text(source + harness)
    subprocess.run(['cc', '-Wno-int-to-pointer-cast', str(path / 'campaign.c'),
                    '-o', str(path / 'campaign')], check=True)
    subprocess.run([str(path / 'campaign')], check=True)
    subprocess.run(['python3', str(root / 'tools/gen_chr.py'), str(path / 'chr.bin')], check=True)
    data = (path / 'chr.bin').read_bytes()
    assert len(data) == 8192 and data[:4096] == data[4096:]
    for start, count in ((0xB9, 25), (0xD9, 9), (0xE2, 9), (0xEB, 2)):
        assert any(data[start * 16:(start + count) * 16])
    assert data[0xA0 * 16:0xB9 * 16] != data[0xB9 * 16:0xD2 * 16]
print('Campaign, jump physics, supply targets, boss movement, audio, and CHR checks passed.')
