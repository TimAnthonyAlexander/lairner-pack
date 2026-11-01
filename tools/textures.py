"""Generate HUD textures, the lairner:df font, hidden food sprites and pack.png.

Font lairner:df (assets/lairner/font/df.json):

  U+E000  crosshair        title-centered (see README: "HUD glyphs")
  U+E001  hit marker       title-centered
  U+E002  headshot marker  title-centered
  U+E003  flash            title-centered, covers the screen
  U+E004  scope overlay    title-centered, covers the screen: black with a round view and a thin cross (AWP, 2026-11-01)
  U+E010  bomb icon        action bar (normal text line)
  U+E011  kit icon
  U+E012  armor (vest) icon
  U+E013  helmet icon
  U+E020..E026  kill feed box pieces, plain, 1,2,4,...,64 px wide, 11 px tall
  U+E030..E036  the same with a red top and bottom border (your own entries)
  U+E037/E038   red border left / right cap (2 px wide)
  U+E040 headshot icon, U+E041 wall icon, U+E042 skull (suicide / world)
  U+F801..U+F808  negative space -1, -2, -4, ... -128
  U+F811..U+F818  positive space +1, +2, +4, ... +128

Title-centered glyphs: the title is drawn at scale 4 from the screen
center, text origin y = -10, so a glyph of height H is centered when
ascent = H/2 - 3. Its x is -width/2 (integer division) with width =
image width * scale + 1, so glyph images are an even number of GUI units
wide and carry an alpha-1 pixel in their last column (the client measures
glyph width from the rightmost non-transparent column; alpha 1 is
discarded by the text shader, so it never shows).

Usage: python3 tools/textures.py
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pngio import blank, write_png  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACK = os.path.join(ROOT, 'pack')
LA = os.path.join(PACK, 'assets', 'lairner')
MC = os.path.join(PACK, 'assets', 'minecraft')

W = (255, 255, 255, 255)
CLEAR = (0, 0, 0, 0)
MARK = (255, 255, 255, 1)   # invisible width marker


def save(path, img):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    write_png(path, len(img[0]), len(img), img)


def put(img, x, y, c):
    if 0 <= y < len(img) and 0 <= x < len(img[0]):
        img[y][x] = c


def fill_rect(img, x0, y0, x1, y1, c):
    for y in range(y0, y1):
        for x in range(x0, x1):
            put(img, x, y, c)

# ------------------------------------------------------------ centered glyphs


def crosshair():
    """24x24 px at height 6 -> 1 px = 1 GUI px under the title's 4x scale.
    Four 2 px lines, 8 px long, 8 px gap (CS classic static)."""
    img = blank(24, 24)
    fill_rect(img, 0, 11, 8, 13, W)
    fill_rect(img, 16, 11, 24, 13, W)
    fill_rect(img, 11, 0, 13, 8, W)
    fill_rect(img, 11, 16, 13, 24, W)
    return img


def hitmarker(r0, r1, thick, size=32):
    """Four diagonal strokes from radius r0 to r1 around the center."""
    img = blank(size, size)
    c = size / 2
    for y in range(size):
        for x in range(size):
            dx, dy = x + 0.5 - c, y + 0.5 - c
            r = math.hypot(dx, dy)
            if r < r0 or r > r1:
                continue
            # distance from the diagonals |dx| = |dy|
            d = abs(abs(dx) - abs(dy)) / math.sqrt(2)
            if d <= thick / 2:
                img[y][x] = W
    img[0][size - 1] = MARK
    return img


def flash():
    return [[W] * 32 for _ in range(16)]

# ------------------------------------------------------------ action bar icons (16x16)

DARK = (40, 40, 48, 255)


def icon_from(rows, colors):
    img = blank(16, 16)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != '.':
                img[y][x] = colors[ch]
    return img


BOMB = [
    "................",
    "................",
    "......kk........",
    ".....k..k.......",
    "..ddddddddddd...",
    "..dssssssssgd...",
    "..dsbbsbbsrsd...",
    "..ddddddddddd...",
    "..tttttttttttt..",
    "..TtttTtttTttT..",
    "..aaaaaaaaaaaa..",
    "..tttttttttttt..",
    "..TtttTtttTttT..",
    "..TTTTTTTTTTTT..",
    "................",
    "................",
]
KIT = [
    "................",
    ".....r....r.....",
    ".....r....r.....",
    ".....rr..rr.....",
    "......rssr......",
    ".......ss.......",
    "..oooooooooooo..",
    "..OOOOOOOOOOOO..",
    "..kkkkkkkkkkkk..",
    "..oooooooooooo..",
    "..oooo....oooo..",
    "..oooommmmoooo..",
    "..oooooooooooo..",
    "..OOOOOOOOOOOO..",
    "................",
    "................",
]
VEST = [
    "................",
    "...vv......vv...",
    "...vV......Vv...",
    "..vvVv....vVvv..",
    "..vvvvvvvvvvvv..",
    "..vVvvvvvvvvVv..",
    "..vvvvvvvvvvvv..",
    "..vppvvvvvvppv..",
    "..vppvvvvvvppv..",
    "..vvvvvvvvvvvv..",
    "..vppvvvvvvppv..",
    "..vppvvvvvvppv..",
    "..vvvvvvvvvvvv..",
    "..VVVVVVVVVVVV..",
    "................",
    "................",
]
HELMET = [
    "................",
    "................",
    "................",
    "......hhhh......",
    "....hhhhhhhh....",
    "...hhhHhhhhhh...",
    "..hhhHhhhhhhhh..",
    "..hhhhhhhhhhhh..",
    "..hhhhhhhhhhhh..",
    "..HHHHHHHHHHHH..",
    ".HHkkkkkkkkkkHH.",
    "..H..........H..",
    "..H..........H..",
    "................",
    "................",
    "................",
]


def icons():
    return {
        'bomb': icon_from(BOMB, {'d': (70, 74, 86, 255), 's': (120, 210, 110, 255), 'b': (196, 200, 210, 255),
                                 'r': (230, 70, 60, 255), 'g': (120, 210, 110, 255), 'k': (230, 70, 60, 255),
                                 't': (206, 180, 128, 255), 'T': (160, 136, 92, 255), 'a': (86, 92, 70, 255)}),
        'kit': icon_from(KIT, {'r': (220, 70, 64, 255), 's': (180, 186, 200, 255), 'o': (102, 122, 82, 255),
                               'O': (70, 86, 58, 255), 'k': DARK, 'm': (150, 160, 170, 255)}),
        'armor': icon_from(VEST, {'v': (110, 140, 190, 255), 'V': (78, 100, 140, 255), 'p': (70, 88, 124, 255)}),
        'helmet': icon_from(HELMET, {'h': (110, 140, 190, 255), 'H': (78, 100, 140, 255), 'k': DARK}),
    }

# ------------------------------------------------------------ kill feed

FEED_H = 11
FEED_FILL = (0, 0, 0, 150)
FEED_FILL_OWN = (50, 0, 0, 170)
FEED_RED = (230, 40, 40, 255)


def feed_piece(w, own, cap=None):
    img = [[FEED_FILL_OWN if own else FEED_FILL] * w for _ in range(FEED_H)]
    if own:
        for x in range(w):
            img[0][x] = FEED_RED
            img[FEED_H - 1][x] = FEED_RED
        if cap == 'l':
            for y in range(FEED_H):
                img[y][0] = FEED_RED
        if cap == 'r':
            for y in range(FEED_H):
                img[y][w - 1] = FEED_RED
    return img


def feed_icon(rows, colors):
    img = blank(8, 8)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != '.':
                img[y][x] = colors[ch]
    return img


SKULL = ['..####..', '.######.', '##.##.##', '##.##.##', '.######.', '..####..', '..#.#.#.', '..####.#']
HEAD = ['..####..', '.#....#.', '#......#', '#..rr..#', '#..rr..#', '#......#', '.#....#.', '..####.#']
WALL = ['###.####', '###.####', '........', '####.###', '####.###', '........', '###.####', '###.####']


def feed_sprites_and_glyphs(providers):
    tex = os.path.join(LA, 'textures', 'font', 'df')
    for i in range(7):
        w = 1 << i
        for own, base, name in ((False, 0xE020, 'feed_%d'), (True, 0xE030, 'feedb_%d')):
            save(os.path.join(tex, name % w + '.png'), feed_piece(w, own))
            providers.append({'type': 'bitmap', 'file': 'lairner:font/df/%s.png' % (name % w),
                              'height': FEED_H, 'ascent': 9, 'chars': [chr(base + i)]})
    for ch, cap, name in ((0xE037, 'l', 'feedb_l'), (0xE038, 'r', 'feedb_r')):
        save(os.path.join(tex, name + '.png'), feed_piece(2, True, cap))
        providers.append({'type': 'bitmap', 'file': 'lairner:font/df/%s.png' % name,
                          'height': FEED_H, 'ascent': 9, 'chars': [chr(ch)]})
    white = (236, 238, 244, 255)
    icons_ = (('feed_hs', 0xE040, HEAD), ('feed_wall', 0xE041, WALL), ('feed_skull', 0xE042, SKULL))
    for name, ch, rows in icons_:
        save(os.path.join(tex, name + '.png'), feed_icon(rows, {'#': white, 'r': FEED_RED}))
        providers.append({'type': 'bitmap', 'file': 'lairner:font/df/%s.png' % name,
                          'height': 8, 'ascent': 7, 'chars': [chr(ch)]})
    # the feed's boss bars (purple) are invisible: only their names show
    bb = os.path.join(MC, 'textures', 'gui', 'sprites', 'boss_bar')
    for n in ('purple_background', 'purple_progress'):
        save(os.path.join(bb, n + '.png'), blank(182, 5))


# ------------------------------------------------------------ scope overlay

SCOPE_W, SCOPE_H = 2048, 1024      # texels; displayed SCOPE_DISPLAY * 4 GUI px tall, 2:1
SCOPE_DISPLAY = 270                # provider height: 1080 GUI px tall (the whole screen at GUI scale 1 on 1080p)
SCOPE_DIAMETER = 245               # the round view in GUI px (1080p at GUI scale 4: 91 % of the screen height)


def scope():
    """U+E004: opaque black everywhere except a round view with a thin black cross (a gap in the middle).
    Texel = 4 x SCOPE_DISPLAY / SCOPE_H GUI px; the round edge is anti-aliased."""
    texel = 4.0 * SCOPE_DISPLAY / SCOPE_H
    radius = SCOPE_DIAMETER / texel / 2
    cx, cy = SCOPE_W / 2, SCOPE_H / 2
    black = (0, 0, 0, 255)
    clear = (0, 0, 0, 0)
    img = []
    gap = 7.0
    for y in range(SCOPE_H):
        row = []
        dy = y + 0.5 - cy
        for x in range(SCOPE_W):
            dx = x + 0.5 - cx
            r = math.hypot(dx, dy)
            if r >= radius + 0.5:
                row.append(black)
                continue
            a = 0.0
            if r > radius - 0.5:
                a = r - (radius - 0.5)                       # the edge
            # thin cross: 1 texel wide lines through the view, a gap around the middle
            if (abs(dy) < 0.75 and abs(dx) > gap) or (abs(dx) < 0.75 and abs(dy) > gap):
                a = 1.0
            if a <= 0:
                row.append(clear)
            else:
                row.append((0, 0, 0, round(255 * min(1.0, a))))
        img.append(row)
    img[SCOPE_H - 1][SCOPE_W - 1] = black
    return img


# ------------------------------------------------------------ vanilla overrides


def cs_crosshair():
    """Replacement for hud/crosshair.png (15x15, drawn with inverting blend)."""
    img = blank(15, 15)
    for i in list(range(1, 5)) + list(range(10, 14)):
        img[7][i] = W
        img[i][7] = W
    return img


def pack_png():
    size = 128
    img = [[(34, 36, 44, 255)] * size for _ in range(size)]
    c = size / 2
    orange = (255, 138, 60, 255)
    for y in range(size):
        for x in range(size):
            dx, dy = x + 0.5 - c, y + 0.5 - c
            r = math.hypot(dx, dy)
            if 40 <= r <= 47:
                img[y][x] = orange
            # crosshair lines with a gap
            if (abs(dy) < 3 and 14 <= abs(dx) <= 58) or (abs(dx) < 3 and 14 <= abs(dy) <= 58):
                img[y][x] = (236, 238, 244, 255)
            if r <= 5:
                img[y][x] = (230, 70, 60, 255)
    return img


def main():
    tex = os.path.join(LA, 'textures', 'font', 'df')
    save(os.path.join(tex, 'crosshair.png'), crosshair())
    save(os.path.join(tex, 'hitmarker.png'), hitmarker(6, 14.5, 2.0))
    save(os.path.join(tex, 'headshot.png'), hitmarker(4, 15.9, 3.2))
    save(os.path.join(tex, 'flash.png'), flash())
    save(os.path.join(tex, 'scope.png'), scope())
    for name, img in icons().items():
        save(os.path.join(tex, 'icon_' + name + '.png'), img)

    providers = [
        {'type': 'bitmap', 'file': 'lairner:font/df/crosshair.png', 'height': 6, 'ascent': 0, 'chars': ['']},
        {'type': 'bitmap', 'file': 'lairner:font/df/hitmarker.png', 'height': 8, 'ascent': 1, 'chars': ['']},
        {'type': 'bitmap', 'file': 'lairner:font/df/headshot.png', 'height': 8, 'ascent': 1, 'chars': ['']},
        {'type': 'bitmap', 'file': 'lairner:font/df/flash.png', 'height': 1024, 'ascent': 509, 'chars': ['']},
        {'type': 'bitmap', 'file': 'lairner:font/df/scope.png', 'height': SCOPE_DISPLAY, 'ascent': SCOPE_DISPLAY // 2 - 3,
         'chars': ['\ue004']},
    ]
    for i, name in enumerate(('bomb', 'kit', 'armor', 'helmet')):
        providers.append({'type': 'bitmap', 'file': 'lairner:font/df/icon_%s.png' % name,
                          'height': 8, 'ascent': 7, 'chars': [chr(0xE010 + i)]})
    feed_sprites_and_glyphs(providers)
    advances = {}
    for i in range(8):
        advances[chr(0xF801 + i)] = -(1 << i)
        advances[chr(0xF811 + i)] = 1 << i
    providers.append({'type': 'space', 'advances': advances})
    os.makedirs(os.path.join(LA, 'font'), exist_ok=True)
    with open(os.path.join(LA, 'font', 'df.json'), 'w') as f:
        json.dump({'providers': providers}, f, indent=2)
        f.write('\n')

    # flash as a camera overlay (equippable head item), 10 opacity steps
    for pct in range(10, 101, 10):
        a = round(255 * pct / 100)
        save(os.path.join(LA, 'textures', 'df', 'flash_%d.png' % pct), [[(255, 255, 255, a)] * 4 for _ in range(4)])

    sprites = os.path.join(MC, 'textures', 'gui', 'sprites', 'hud')
    for n in ('food_empty', 'food_half', 'food_full', 'food_empty_hunger', 'food_half_hunger', 'food_full_hunger'):
        save(os.path.join(sprites, n + '.png'), blank(9, 9))
    save(os.path.join(sprites, 'crosshair.png'), cs_crosshair())

    pp = pack_png()
    write_png(os.path.join(PACK, 'pack.png'), 128, 128, pp)
    print('textures and font written')


if __name__ == '__main__':
    main()
