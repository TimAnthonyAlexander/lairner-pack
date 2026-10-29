"""Generate the df item models, item definitions and the palette texture.

Guns, grenades and the smoke puff come from Kenney's Blaster Kit (CC0,
source/kenney), voxelized into cuboids. Knife, bomb and defuse kit are
built here from boxes in the same flat palette style.

Usage: python3 tools/models.py   (writes into pack/)
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import voxelize as vx  # noqa: E402
from pngio import write_png  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'source', 'kenney')
PACK = os.path.join(ROOT, 'pack')
NS = os.path.join(PACK, 'assets', 'lairner')
PALETTE_TEX = 'lairner:item/df/palette'
CELL = 8           # pixels per palette color (keeps mipmaps clean)
GRID = 16          # colors per palette row/column -> 256 colors max

# ------------------------------------------------------------ display math


def _rot(axis, deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    if axis == 'x':
        return [[1, 0, 0], [0, c, -s], [0, s, c]]
    if axis == 'y':
        return [[c, 0, s], [0, 1, 0], [-s, 0, c]]
    return [[c, -s, 0], [s, c, 0], [0, 0, 1]]


def _mul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def euler_xyz(*steps):
    """Compose rotations given as ('x'|'y'|'z', degrees) in the order they
    act on the model (first one first, about the fixed view axes) and return
    the [x, y, z] Euler angles Minecraft expects (R = Rx * Ry * Rz)."""
    m = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
    for axis, deg in steps:
        m = _mul(_rot(axis, deg), m)
    b = math.asin(max(-1.0, min(1.0, m[0][2])))
    if abs(math.cos(b)) > 1e-6:
        a = math.atan2(-m[1][2], m[2][2])
        c = math.atan2(-m[0][1], m[0][0])
    else:
        a = math.atan2(m[2][1], m[1][1])
        c = 0.0
    return [round(math.degrees(v), 2) + 0.0 for v in (a, b, c)]


def disp(rot_steps, translation, scale):
    return {'rotation': euler_xyz(*rot_steps), 'translation': translation,
            'scale': [scale, scale, scale]}


def gun_display(fp_scale, fp_t, tp_scale, tp_t, gui_scale, gui_tilt=0, ground_scale=0.35, fixed_scale=None):
    """Models face -Z (barrel), +Y up, centered on (8, 8, 8)."""
    fixed_scale = fixed_scale or gui_scale
    # first person: barrel forward, pitched up a little and turned toward the
    # crosshair so the left side of the gun shows
    lt = list(fp_t)  # vanilla convention: left hand mirrors rotation, keeps translation
    return {
        'firstperson_righthand': disp([('x', 4), ('y', 14)], fp_t, fp_scale),
        'firstperson_lefthand': disp([('x', 4), ('y', -14)], lt, fp_scale),
        'thirdperson_righthand': disp([('x', 90), ('x', -18)], tp_t, tp_scale),
        'thirdperson_lefthand': disp([('x', 90), ('x', -18)], tp_t, tp_scale),
        # side view, barrel to the right, slightly from above
        'gui': disp([('y', -90), ('z', gui_tilt), ('x', 12), ('y', -15)], [0, 0, 0], gui_scale),
        'ground': disp([], [0, 2, 0], ground_scale),
        'fixed': disp([('y', -90)], [0, 0, 0], fixed_scale),
        'head': disp([('y', -90)], [0, 4, 0], 0.8),
    }


def compact_display(fp_scale, fp_t, tp_scale, tp_t, gui_scale, ground_scale=0.45):
    """Grenades, bomb, kit: upright objects held in the palm."""
    return {
        'firstperson_righthand': disp([('y', 20)], fp_t, fp_scale),
        'firstperson_lefthand': disp([('y', -20)], fp_t, fp_scale),
        'thirdperson_righthand': disp([('x', 72)], tp_t, tp_scale),
        'thirdperson_lefthand': disp([('x', 72)], tp_t, tp_scale),
        'gui': disp([('y', -135), ('x', 25)], [0, 0, 0], gui_scale),
        'ground': disp([], [0, 2, 0], ground_scale),
        'fixed': disp([('y', -90)], [0, 0, 0], gui_scale),
        'head': disp([], [0, 6, 0], 0.8),
    }

# ------------------------------------------------------------ palette


class Palette:
    def __init__(self):
        self.colors = []

    def index(self, rgb):
        rgb = tuple(int(c) for c in rgb)
        if rgb not in self.colors:
            self.colors.append(rgb)
            if len(self.colors) > GRID * GRID:
                raise SystemExit('palette full (%d colors)' % len(self.colors))
        return self.colors.index(rgb)

    def uv(self, rgb):
        i = self.index(rgb)
        u, v = i % GRID, i // GRID
        # 16 uv units across the texture -> one unit per color cell; sample the middle
        return [u + 0.375, v + 0.375, u + 0.625, v + 0.625]

    def write(self, path):
        size = GRID * CELL
        px = [[(0, 0, 0, 0)] * size for _ in range(size)]
        for i, rgb in enumerate(self.colors):
            u, v = i % GRID, i // GRID
            for y in range(v * CELL, (v + 1) * CELL):
                for x in range(u * CELL, (u + 1) * CELL):
                    px[y][x] = rgb + (255,)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        write_png(path, size, size, px)

# ------------------------------------------------------------ elements


def r4(v):
    v = round(v, 4)
    return int(v) if v == int(v) else v


def element(lo, hi, rgb, faces, pal):
    return {
        'from': [r4(c) for c in lo],
        'to': [r4(c) for c in hi],
        'faces': {f: {'uv': pal.uv(rgb), 'texture': '#0'} for f in faces},
    }


ALL_FACES = ['north', 'east', 'south', 'west', 'up', 'down']


def voxel_model(meshes, per_unit, length, pal, recolor=None, qdist=26):
    """Voxelize meshes and scale so the longest side is `length` model units,
    centered on (8, 8, 8)."""
    tex = vx.Texture(os.path.join(SRC, 'colormap.png'))
    solid, dims = vx.voxelize(meshes, tex, per_unit, recolor)
    solid = vx.quantize(solid, qdist)
    boxes = vx.greedy_boxes(solid)
    unit = length / max(dims)
    off = [8 - dims[i] * unit / 2 for i in range(3)]
    els = []
    for box in boxes:
        faces = vx.visible_faces(box, solid)
        if not faces:
            continue
        lo, hi, rgb = box
        els.append(element([off[i] + lo[i] * unit for i in range(3)],
                           [off[i] + hi[i] * unit for i in range(3)], rgb, faces, pal))
    return els, dims


def kenney(name, flip=None, turn=False):
    """Load and orient a Kenney mesh; turn=True turns it around when the
    grip heuristic in vx.orient picks the wrong end (checked in previews)."""
    verts, uvs, tris = vx.load_obj(os.path.join(SRC, name + '.obj'))
    verts = vx.orient(verts, flip)
    if turn:
        verts = [(-x, y, -z) for x, y, z in verts]
    return verts, uvs, tris


def with_silencer(gun, silencer, scale=0.85, sink=0.01):
    """Attach a Kenney silencer to the muzzle of an oriented gun mesh."""
    verts, uvs, tris = gun
    mx, my, mz = vx.muzzle(verts)
    sv, su, st = vx.load_obj(os.path.join(SRC, silencer + '.obj'))
    # silencer runs from z=0 to negative z, centered on x=y=0
    sv = [(mx + x * scale, my + y * scale, mz + sink + z * scale) for x, y, z in sv]
    return [gun, (sv, su, st)]

# ------------------------------------------------------------ recolors


def hue_shift(target_body, target_dark=None):
    """Map Kenney's orange/yellow swatches to another color, keeping shade."""
    def f(rgb):
        r, g, b = rgb
        if r > g + 30 and r > b + 60:      # orange / yellow body
            lum = (r + g + b) / 3 / 190.0
            return tuple(max(0, min(255, int(c * lum))) for c in target_body)
        return rgb
    return f


def gray_cloud(rgb):
    r, g, b = rgb
    lum = 0.3 * r + 0.59 * g + 0.11 * b
    v = int(118 + (lum - 150) * 0.55)
    v = max(96, min(196, v))
    return (v, v, min(255, v + 4))

# ------------------------------------------------------------ hand-built models

STEEL = (164, 170, 186)
STEEL_DARK = (110, 116, 132)
EDGE = (214, 220, 232)
GRIP = (58, 56, 68)
GRIP_DARK = (40, 39, 48)
TAN = (196, 170, 120)
TAN_DARK = (160, 136, 92)
TAPE = (86, 92, 70)
PANEL = (70, 74, 86)
SCREEN = (120, 210, 110)
RED = (214, 72, 64)
YELLOW = (250, 190, 64)
BLUE = (96, 150, 214)
OLIVE = (92, 110, 74)
OLIVE_DARK = (70, 86, 58)


def boxes_model(spec, pal):
    """spec: [(from, to, rgb)] in model units."""
    els = []
    for lo, hi, rgb in spec:
        els.append(element(lo, hi, rgb, ALL_FACES, pal))
    return els


def knife_spec():
    """CS-style knife along -Z: handle at the back, blade forward."""
    s = []
    # handle (z 10..16), grip ridges
    s.append(([7.25, 6.5, 10], [8.75, 8.75, 16], GRIP))
    for z in (11, 12.5, 14):
        s.append(([7.1, 6.4, z], [8.9, 8.9, z + 0.6], GRIP_DARK))
    s.append(([7.1, 6.3, 15.6], [8.9, 8.9, 16.4], STEEL_DARK))      # pommel
    # guard
    s.append(([6.75, 5.75, 9.4], [9.25, 9.6, 10], STEEL_DARK))
    # blade: spine on top, edge on the bottom, tapering to a point
    s.append(([7.6, 7.0, 1.5], [8.4, 9.2, 9.4], STEEL))
    s.append(([7.75, 6.2, 1.5], [8.25, 7.0, 9.4], EDGE))
    s.append(([7.6, 7.4, -0.5], [8.4, 9.0, 1.5], STEEL))
    s.append(([7.75, 6.8, -0.5], [8.25, 7.4, 1.5], EDGE))
    s.append(([7.65, 7.8, -2.0], [8.35, 8.8, -0.5], STEEL))
    s.append(([7.8, 7.5, -2.0], [8.2, 7.8, -0.5], EDGE))
    s.append(([7.75, 8.1, -3.0], [8.25, 8.6, -2.0], EDGE))
    s.append(([7.55, 8.6, 3.0], [8.45, 9.3, 8.0], STEEL_DARK))     # fuller / spine detail
    return s


def bomb_spec():
    """C4-style charge: three tan bricks, tape, a keypad with a screen, wires."""
    s = []
    # bricks (x 2..14, y 4..8, z 4..12), each 4 deep, with dark seams
    for i, z in enumerate((4, 8.05, 12.1)):
        s.append(([2, 4, z], [14, 7.6, z + 3.9], TAN if i != 1 else (204, 178, 128)))
    s.append(([1.9, 3.9, 6.2], [14.1, 7.7, 7.4], TAPE))
    s.append(([1.9, 3.9, 13.2], [14.1, 7.7, 14.4], TAPE))
    # keypad body on top
    s.append(([4, 7.6, 5], [12, 9.0, 12], PANEL))
    s.append(([5, 9.0, 5.6], [11, 9.3, 7.4], SCREEN))              # screen
    s.append(([10.2, 9.0, 8.0], [11, 9.4, 8.8], RED))               # LED
    for row, z in enumerate((8.4, 9.6, 10.8)):
        for col, x in enumerate((5.2, 6.6, 8.0)):
            s.append(([x, 9.0, z], [x + 0.9, 9.35, z + 0.8], (196, 200, 210)))
    # wires
    s.append(([12, 7.6, 6.0], [12.6, 8.2, 11.0], RED))
    s.append(([12.6, 7.6, 7.0], [13.2, 8.0, 10.6], BLUE))
    s.append(([3.4, 7.6, 6.4], [4.0, 8.2, 10.2], YELLOW))
    s.append(([12.0, 6.0, 15.9], [12.6, 8.2, 16.4], RED))
    return s


def kit_spec():
    """Defuse kit: a small olive pouch with a zip and wire-cutter handles."""
    s = []
    s.append(([4, 4, 5], [12, 10, 11], OLIVE))
    s.append(([4.4, 10, 5.4], [11.6, 10.6, 10.6], OLIVE_DARK))       # flap
    s.append(([3.8, 9.2, 4.8], [12.2, 9.6, 11.2], GRIP_DARK))       # zip line
    s.append(([6.5, 5.2, 4.6], [9.5, 7.6, 5.0], OLIVE_DARK))         # front pocket
    s.append(([7.5, 7.0, 4.4], [8.5, 7.8, 4.7], STEEL))               # clasp
    # wire cutters sticking out of the top
    s.append(([6.2, 10.6, 7.4], [7.0, 14.5, 8.2], RED))
    s.append(([9.0, 10.6, 7.4], [9.8, 14.0, 8.2], RED))
    s.append(([6.8, 10.6, 7.5], [9.2, 11.4, 8.1], STEEL_DARK))
    s.append(([7.4, 14.2, 7.6], [8.6, 15.4, 8.0], STEEL))
    # strap
    s.append(([3.6, 6.4, 7.4], [4.0, 8.2, 8.6], GRIP_DARK))
    s.append(([12.0, 6.4, 7.4], [12.4, 8.2, 8.6], GRIP_DARK))
    return s

# ------------------------------------------------------------ the roster

# id: (source, model length in units, voxel density per Kenney meter, extra)
# Display numbers were tuned with tools/preview.py.
PISTOL_DISPLAY = dict(fp_scale=0.62, fp_t=[-2.5, 3.0, -1.0], tp_scale=0.62, tp_t=[0, 0.4, 2.2], gui_scale=0.85)
SMG_DISPLAY = dict(fp_scale=0.66, fp_t=[-2.5, 3.0, -2.0], tp_scale=0.66, tp_t=[0, 0.6, 2.6], gui_scale=0.8, gui_tilt=12)
RIFLE_DISPLAY = dict(fp_scale=0.6, fp_t=[-2.5, 3.2, -3.5], tp_scale=0.7, tp_t=[0, 1.0, 2.0], gui_scale=0.6, gui_tilt=25)


def build(pal):
    models = {}

    def gun(mid, obj, length, per_unit, display, silencer=None, turn=False, qdist=26):
        mesh = kenney(obj, turn=turn)
        meshes = with_silencer(mesh, silencer) if silencer else [mesh]
        els, dims = voxel_model(meshes, per_unit, length, pal, qdist=qdist)
        models[mid] = {'elements': els, 'display': gun_display(**display), 'src': obj}

    gun('glock', 'blaster-k', 13, 64, PISTOL_DISPLAY, turn=True)
    gun('usp', 'blaster-a', 16, 52, PISTOL_DISPLAY, silencer='silencer-small')
    gun('deagle', 'blaster-j', 15, 60, PISTOL_DISPLAY, turn=True)
    gun('mac10', 'blaster-c', 15, 60, SMG_DISPLAY)
    gun('mp9', 'blaster-i', 16, 60, SMG_DISPLAY, turn=True)
    gun('ak', 'blaster-n', 24, 56, RIFLE_DISPLAY)
    gun('m4s', 'blaster-d', 28, 48, RIFLE_DISPLAY, silencer='silencer-larger')

    nade_display = compact_display(fp_scale=0.55, fp_t=[0, 6.0, 0], tp_scale=0.5, tp_t=[0, 1.5, 1.0], gui_scale=1.05)
    flash_col = hue_shift((236, 236, 240))
    smoke_col = hue_shift((120, 170, 150))
    for mid, obj, rec in (('flashbang', 'grenade-a', flash_col), ('smoke', 'grenade-a', smoke_col),
                          ('he', 'grenade-b', None)):
        els, _ = voxel_model([kenney(obj, flip=False)], 90, 8, pal, recolor=rec)
        models[mid] = {'elements': els, 'display': nade_display, 'src': obj}

    # Kenney's smoke is a flat cloud; make it rounder for volume smoke
    pv, pu, pt = kenney('smoke', flip=False)
    pv = [(x, y * 1.4, z) for x, y, z in pv]
    puff, _ = voxel_model([(pv, pu, pt)], 40, 16, pal, recolor=gray_cloud, qdist=40)
    models['smoke_puff'] = {'elements': puff, 'display': {
        'gui': disp([('y', -135), ('x', 25)], [0, 0, 0], 0.6),
        'ground': disp([], [0, 2, 0], 0.5),
        'fixed': disp([], [0, 0, 0], 1.0),
        'head': disp([], [0, 0, 0], 1.0),
    }, 'src': 'smoke'}

    models['knife'] = {'elements': boxes_model(knife_spec(), pal),
                       'display': gun_display(fp_scale=0.75, fp_t=[-0.6, 1.6, -1.4], tp_scale=0.7,
                                              tp_t=[0, 0.8, 1.6], gui_scale=0.85), 'src': 'lairner'}
    models['bomb'] = {'elements': boxes_model(bomb_spec(), pal),
                      'display': compact_display(fp_scale=0.55, fp_t=[0, 5.0, -1.0], tp_scale=0.5,
                                                 tp_t=[0, 1.6, 1.2], gui_scale=0.95, ground_scale=0.4), 'src': 'lairner'}
    models['kit'] = {'elements': boxes_model(kit_spec(), pal),
                     'display': compact_display(fp_scale=0.55, fp_t=[0, 5.0, -0.5], tp_scale=0.5,
                                                tp_t=[0, 1.6, 1.2], gui_scale=1.0), 'src': 'lairner'}
    return models


GUNS = ('glock', 'usp', 'deagle', 'mac10', 'mp9', 'ak', 'm4s', 'knife')


def main():
    pal = Palette()
    models = build(pal)
    mdir = os.path.join(NS, 'models', 'item', 'df')
    idir = os.path.join(NS, 'items', 'df')
    os.makedirs(mdir, exist_ok=True)
    os.makedirs(idir, exist_ok=True)
    for mid, m in sorted(models.items()):
        out = {
            'credit': 'lairner (pack: github.com/TimAnthonyAlexander/lairner-pack)' + (
                '; mesh: Kenney Blaster Kit %s (CC0)' % m['src'] if m['src'] != 'lairner' else ''),
            'texture_size': [GRID * CELL, GRID * CELL],
            'textures': {'0': PALETTE_TEX, 'particle': PALETTE_TEX},
            'elements': m['elements'],
            'display': m['display'],
        }
        with open(os.path.join(mdir, mid + '.json'), 'w') as f:
            json.dump(out, f, separators=(',', ':'))
        item = {'model': {'type': 'minecraft:model', 'model': 'lairner:item/df/' + mid}}
        if mid in GUNS:
            # the gun stack changes on every shot (ammo); don't replay the equip bob
            item['hand_animation_on_swap'] = False
        with open(os.path.join(idir, mid + '.json'), 'w') as f:
            json.dump(item, f, indent=2)
            f.write('\n')
        print('%-11s %4d elements' % (mid, len(m['elements'])))
    pal.write(os.path.join(NS, 'textures', 'item', 'df', 'palette.png'))
    print('palette: %d colors' % len(pal.colors))


if __name__ == '__main__':
    main()
