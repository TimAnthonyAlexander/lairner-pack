"""Turn a Kenney OBJ mesh (flat palette colors) into Minecraft cuboid elements.

Pipeline: parse OBJ -> orient (barrel to -Z, top +Y) -> sample the surface
densely and vote a color per voxel -> flood-fill the outside so the inside is
solid -> merge voxels into boxes (greedy; inside voxels are wildcards and may
be shared by several boxes, they are never visible) -> drop faces that are
fully covered by solid neighbours.

The result is a list of boxes in voxel coordinates with one RGB color each.
"""
import math

from pngio import read_png


def load_obj(path):
    verts, uvs, tris = [], [], []
    for line in open(path):
        p = line.split()
        if not p:
            continue
        if p[0] == 'v':
            verts.append(tuple(float(c) for c in p[1:4]))
        elif p[0] == 'vt':
            uvs.append((float(p[1]), float(p[2])))
        elif p[0] == 'f':
            idx = []
            for c in p[1:]:
                parts = c.split('/')
                vi = int(parts[0]) - 1
                ti = int(parts[1]) - 1 if len(parts) > 1 and parts[1] else 0
                idx.append((vi, ti))
            for k in range(1, len(idx) - 1):
                tris.append((idx[0], idx[k], idx[k + 1]))
    return verts, uvs, tris


class Texture:
    def __init__(self, path):
        self.w, self.h, self.rows = read_png(path)

    def sample(self, u, v):
        x = min(self.w - 1, max(0, int(u * self.w)))
        y = min(self.h - 1, max(0, int((1.0 - v) * self.h)))
        return self.rows[y][x][:3]


def orient(verts, flip=None, rot_y=0):
    """Return vertices rotated so the barrel points to -Z.

    Kenney blasters lie along Z. The grip is the lowest part and sits behind
    the middle, so the muzzle is the far end from the grip. flip=True/False
    overrides the guess.
    """
    out = verts
    if rot_y:
        a = math.radians(rot_y)
        c, s = math.cos(a), math.sin(a)
        out = [(x * c + z * s, y, -x * s + z * c) for x, y, z in out]
    if flip is None:
        ys = [v[1] for v in out]
        lo, hi = min(ys), max(ys)
        low = [v for v in out if v[1] < lo + 0.3 * (hi - lo)]
        zs = [v[2] for v in out]
        zmid = (min(zs) + max(zs)) / 2
        gz = sum(v[2] for v in low) / len(low)
        flip = gz < zmid  # grip at -Z means muzzle at +Z -> turn around
    if flip:
        out = [(-x, y, -z) for x, y, z in out]
    return out


def muzzle(verts):
    """Center (x, y) and z of the front end (-Z) of an oriented gun."""
    zmin = min(v[2] for v in verts)
    front = [v for v in verts if v[2] < zmin + 0.015]
    return (sum(v[0] for v in front) / len(front), sum(v[1] for v in front) / len(front), zmin)


def voxelize(meshes, tex, per_unit, recolor=None):
    """meshes: [(verts, uvs, tris)] already oriented. Returns (solid, dims)."""
    allv = [v for m in meshes for v in m[0]]
    mins = [min(v[i] for v in allv) for i in range(3)]
    maxs = [max(v[i] for v in allv) for i in range(3)]
    dims = [int(math.ceil((maxs[i] - mins[i]) * per_unit - 1e-6)) + 1 for i in range(3)]
    votes = {}
    for verts, uvs, tris in meshes:
        for tri in tris:
            P = [verts[vi] for vi, _ in tri]
            Tc = [uvs[ti] if uvs else (0, 0) for _, ti in tri]
            edge = max(math.dist(P[a], P[b]) for a, b in ((0, 1), (1, 2), (2, 0)))
            n = max(1, int(math.ceil(edge * per_unit * 3)))
            for i in range(n + 1):
                for j in range(n + 1 - i):
                    a = i / n
                    b = j / n
                    c = 1.0 - a - b
                    p = [P[0][k] * a + P[1][k] * b + P[2][k] * c for k in range(3)]
                    u = Tc[0][0] * a + Tc[1][0] * b + Tc[2][0] * c
                    v = Tc[0][1] * a + Tc[1][1] * b + Tc[2][1] * c
                    cell = tuple(min(dims[k] - 1, int((p[k] - mins[k]) * per_unit)) for k in range(3))
                    col = tex.sample(u, v)
                    if recolor:
                        col = recolor(col)
                    d = votes.setdefault(cell, {})
                    d[col] = d.get(col, 0) + 1
    surface = {c: max(d.items(), key=lambda kv: kv[1])[0] for c, d in votes.items()}
    return fill(surface, dims), dims


def fill(surface, dims):
    """Solid cells = everything not reachable from outside. Returns
    {cell: color or None}; None marks an interior (invisible) cell."""
    X, Y, Z = dims
    outside = set()
    stack = [(-1, -1, -1)]
    outside.add((-1, -1, -1))
    while stack:
        x, y, z = stack.pop()
        for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
            q = (x + dx, y + dy, z + dz)
            if q in outside or q in surface:
                continue
            if not (-1 <= q[0] <= X and -1 <= q[1] <= Y and -1 <= q[2] <= Z):
                continue
            outside.add(q)
            stack.append(q)
    solid = {}
    for x in range(X):
        for y in range(Y):
            for z in range(Z):
                c = (x, y, z)
                if c in outside:
                    continue
                solid[c] = surface.get(c)
    # A surface cell with no outside neighbour is invisible: make it a wildcard.
    for c, col in list(solid.items()):
        if col is None:
            continue
        x, y, z = c
        if all((x + dx, y + dy, z + dz) in solid for dx, dy, dz in
               ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))):
            solid[c] = None
    return solid


def quantize(solid, max_dist=26):
    """Merge near colors (Kenney gradients) so boxes can grow."""
    counts = {}
    for col in solid.values():
        if col is not None:
            counts[col] = counts.get(col, 0) + 1
    reps = []
    mapping = {}
    for col, _ in sorted(counts.items(), key=lambda kv: -kv[1]):
        best = None
        for r in reps:
            d = math.dist(col, r)
            if d <= max_dist and (best is None or d < best[0]):
                best = (d, r)
        if best:
            mapping[col] = best[1]
        else:
            reps.append(col)
            mapping[col] = col
    return {c: (mapping[col] if col is not None else None) for c, col in solid.items()}


def greedy_boxes(solid):
    """Cover all visible cells with boxes of one color each."""
    assigned = set()
    boxes = []
    cells = sorted((c for c, col in solid.items() if col is not None),
                   key=lambda c: (c[1], c[2], c[0]))

    def ok(cell, color):
        col = solid.get(cell, 'missing')
        if col == 'missing':
            return False
        if col is None:
            return True
        return col == color and cell not in assigned

    def grow(start, color, order):
        lo = list(start)
        hi = [s + 1 for s in start]
        for axis in order:
            for direction in (1, -1):
                while True:
                    if direction == 1:
                        layer = hi[axis]
                    else:
                        layer = lo[axis] - 1
                    rng = [range(lo[k], hi[k]) if k != axis else [layer] for k in range(3)]
                    good = all(ok((x, y, z), color) for x in rng[0] for y in rng[1] for z in rng[2])
                    if not good:
                        break
                    if direction == 1:
                        hi[axis] += 1
                    else:
                        lo[axis] -= 1
        return lo, hi

    orders = ((0, 1, 2), (0, 2, 1), (1, 0, 2), (1, 2, 0), (2, 0, 1), (2, 1, 0))
    for c in cells:
        if c in assigned:
            continue
        color = solid[c]
        best = None
        for order in orders:
            lo, hi = grow(c, color, order)
            gain = sum(1 for x in range(lo[0], hi[0]) for y in range(lo[1], hi[1])
                       for z in range(lo[2], hi[2])
                       if solid.get((x, y, z)) is not None and (x, y, z) not in assigned)
            vol = (hi[0] - lo[0]) * (hi[1] - lo[1]) * (hi[2] - lo[2])
            key = (gain, -vol)
            if best is None or key > best[0]:
                best = (key, lo, hi)
        _, lo, hi = best
        for x in range(lo[0], hi[0]):
            for y in range(lo[1], hi[1]):
                for z in range(lo[2], hi[2]):
                    if solid.get((x, y, z)) is not None:
                        assigned.add((x, y, z))
        boxes.append((tuple(lo), tuple(hi), color))
    return boxes


def visible_faces(box, solid):
    """Faces of a box that have at least one non-solid cell in front."""
    lo, hi, _ = box
    faces = []
    spec = {
        'west': (0, -1), 'east': (0, 1),
        'down': (1, -1), 'up': (1, 1),
        'north': (2, -1), 'south': (2, 1),
    }
    for name, (axis, d) in spec.items():
        layer = lo[axis] - 1 if d < 0 else hi[axis]
        rng = [range(lo[k], hi[k]) if k != axis else [layer] for k in range(3)]
        covered = all((x, y, z) in solid for x in rng[0] for y in rng[1] for z in rng[2])
        if not covered:
            faces.append(name)
    return faces
