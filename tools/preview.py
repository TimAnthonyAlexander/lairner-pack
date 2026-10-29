"""Render previews of every df item model into previews/<id>.png.

Each sheet: model (iso) | GUI slot | first person right hand | third person
(side) | third person (front) | ground. Reads the built pack, so it shows
exactly what the zip contains.

Usage: python3 tools/preview.py [id ...]
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render as R  # noqa: E402
from pngio import read_png  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NS = os.path.join(ROOT, 'pack', 'assets', 'lairner')
MDIR = os.path.join(NS, 'models', 'item', 'df')
OUT = os.path.join(ROOT, 'previews')


def main(ids):
    palette = read_png(os.path.join(NS, 'textures', 'item', 'df', 'palette.png'))
    os.makedirs(OUT, exist_ok=True)
    ids = ids or sorted(f[:-5] for f in os.listdir(MDIR) if f.endswith('.json'))
    for mid in ids:
        model = json.load(open(os.path.join(MDIR, mid + '.json')))
        quads = R.face_quads(model, palette)
        views = [R.render_side(model, quads, 220), R.render_iso(model, quads, 220), R.render_gui(model, quads, 220),
                 R.render_first_person(model, quads, 392, 220),
                 R.render_third_person(model, quads, 220, 220, side=True),
                 R.render_third_person(model, quads, 220, 220, side=False),
                 R.render_ground(model, quads, 220)]
        R.sheet(views, os.path.join(OUT, mid + '.png'))
        print('previews/%s.png' % mid)


if __name__ == '__main__':
    main(sys.argv[1:])
