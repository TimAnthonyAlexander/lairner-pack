"""Software previews of the item models (stdlib only).

Renders a model JSON (cuboid elements, palette texture) the way the 26.3
client places it: GUI slot, first person right hand (camera transform taken
from FirstPersonHandsAndItemsRenderer), third person right hand (the player
model chain from ItemInHandLayer) and on the ground. Used to check the
display transforms without a client.
"""
import json
import math
import os

from pngio import read_png, write_png

# ---------------------------------------------------------------- matrices

def mat_id():
    return [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]


def mul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]


def T(x, y, z):
    m = mat_id()
    m[0][3], m[1][3], m[2][3] = x, y, z
    return m


def S(x, y=None, z=None):
    y = x if y is None else y
    z = x if z is None else z
    m = mat_id()
    m[0][0], m[1][1], m[2][2] = x, y, z
    return m


def Rx(deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return [[1, 0, 0, 0], [0, c, -s, 0], [0, s, c, 0], [0, 0, 0, 1]]


def Ry(deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return [[c, 0, s, 0], [0, 1, 0, 0], [-s, 0, c, 0], [0, 0, 0, 1]]


def Rz(deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return [[c, -s, 0, 0], [s, c, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]


def chain(*ms):
    out = mat_id()
    for m in ms:
        out = mul(out, m)
    return out


def apply(m, p):
    x, y, z = p
    return (m[0][0] * x + m[0][1] * y + m[0][2] * z + m[0][3],
            m[1][0] * x + m[1][1] * y + m[1][2] * z + m[1][3],
            m[2][0] * x + m[2][1] * y + m[2][2] * z + m[2][3])


def display_matrix(model, ctx):
    """ItemTransform.apply for the right hand + the -0.5 shift, in block units."""
    d = model.get('display', {}).get(ctx, {})
    r = d.get('rotation', [0, 0, 0])
    t = d.get('translation', [0, 0, 0])
    s = d.get('scale', [1, 1, 1])
    # rotationXYZ(x, y, z) = Rx * Ry * Rz
    return chain(T(t[0] / 16, t[1] / 16, t[2] / 16), Rx(r[0]), Ry(r[1]), Rz(r[2]),
                 S(s[0], s[1], s[2]), T(-0.5, -0.5, -0.5), S(1 / 16))

# ---------------------------------------------------------------- geometry

SHADE = {'up': 1.0, 'down': 0.5, 'north': 0.8, 'south': 0.8, 'east': 0.6, 'west': 0.6}


def face_quads(model, palette):
    """[(4 corner points in model units, rgb, face name)]"""
    out = []
    for el in model['elements']:
        f, t = el['from'], el['to']
        x0, y0, z0 = f
        x1, y1, z1 = t
        corners = {
            'north': [(x1, y1, z0), (x0, y1, z0), (x0, y0, z0), (x1, y0, z0)],
            'south': [(x0, y1, z1), (x1, y1, z1), (x1, y0, z1), (x0, y0, z1)],
            'west': [(x0, y1, z0), (x0, y1, z1), (x0, y0, z1), (x0, y0, z0)],
            'east': [(x1, y1, z1), (x1, y1, z0), (x1, y0, z0), (x1, y0, z1)],
            'up': [(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)],
            'down': [(x0, y0, z1), (x1, y0, z1), (x1, y0, z0), (x0, y0, z0)],
        }
        for name, face in el['faces'].items():
            uv = face['uv']
            px = int((uv[0] + uv[2]) / 2 * palette[0] / 16)
            py = int((uv[1] + uv[3]) / 2 * palette[1] / 16)
            rgb = palette[2][py][px][:3]
            out.append((corners[name], rgb, name))
    return out

# ---------------------------------------------------------------- raster


class Canvas:
    def __init__(self, w, h, bg=(58, 62, 70)):
        self.w, self.h = w, h
        self.px = [[bg + (255,) for _ in range(w)] for _ in range(h)]
        self.z = [[float('inf')] * w for _ in range(h)]

    def tri(self, a, b, c, rgb):
        (ax, ay, az), (bx, by, bz), (cx, cy, cz) = a, b, c
        minx = max(0, int(math.floor(min(ax, bx, cx))))
        maxx = min(self.w - 1, int(math.ceil(max(ax, bx, cx))))
        miny = max(0, int(math.floor(min(ay, by, cy))))
        maxy = min(self.h - 1, int(math.ceil(max(ay, by, cy))))
        den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
        if abs(den) < 1e-12:
            return
        col = rgb + (255,)
        for y in range(miny, maxy + 1):
            py = y + 0.5
            for x in range(minx, maxx + 1):
                px = x + 0.5
                w0 = ((by - cy) * (px - cx) + (cx - bx) * (py - cy)) / den
                w1 = ((cy - ay) * (px - cx) + (ax - cx) * (py - cy)) / den
                w2 = 1 - w0 - w1
                if w0 < -1e-6 or w1 < -1e-6 or w2 < -1e-6:
                    continue
                z = w0 * az + w1 * bz + w2 * cz
                if z < self.z[y][x]:
                    self.z[y][x] = z
                    self.px[y][x] = col

    def quad(self, pts, rgb):
        self.tri(pts[0], pts[1], pts[2], rgb)
        self.tri(pts[0], pts[2], pts[3], rgb)

    def rect(self, x0, y0, x1, y1, rgb):
        for y in range(max(0, y0), min(self.h, y1)):
            for x in range(max(0, x0), min(self.w, x1)):
                self.px[y][x] = rgb + (255,)

    def save(self, path):
        write_png(path, self.w, self.h, self.px)


def shade(rgb, k):
    return tuple(min(255, int(c * k)) for c in rgb)


def normal_shade(p):
    """Light from the face normal (world space) like MC's diffuse lighting."""
    ux, uy, uz = (p[1][i] - p[0][i] for i in range(3))
    vx, vy, vz = (p[3][i] - p[0][i] for i in range(3))
    n = (uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx)
    ln = math.sqrt(sum(c * c for c in n)) or 1
    n = tuple(c / ln for c in n)
    # two lights like the item lighting, roughly from up-front-left and up-back-right
    l1 = (0.2, 1.0, -0.7)
    l2 = (-0.2, 1.0, 0.7)
    def dot(l):
        ll = math.sqrt(sum(c * c for c in l))
        return max(0.0, -sum(n[i] * l[i] / ll for i in range(3)))
    # normal from the corner winding points inward for our winding; flip sign
    return min(1.0, 0.4 + 0.6 * (dot(l1) + dot(l2)) * 0.75)


def draw(canvas, quads, world, project, flat=True):
    for pts, rgb, name in quads:
        wp = [apply(world, p) for p in pts]
        sp = [project(p) for p in wp]
        if any(p is None for p in sp):
            continue
        k = SHADE[name] if flat else normal_shade(wp)
        canvas.quad(sp, shade(rgb, k))


def ortho(scale, cx, cy):
    def f(p):
        return (cx + p[0] * scale, cy - p[1] * scale, -p[2])
    return f


def perspective(w, h, fov_y=70.0):
    f = 1.0 / math.tan(math.radians(fov_y) / 2)

    def proj(p):
        x, y, z = p
        if z > -0.01:
            return None
        sx = (f * x / -z) * (h / 2) + w / 2
        sy = -(f * y / -z) * (h / 2) + h / 2
        return (sx, sy, -z)
    return proj


def look_at(eye, target):
    fx, fy, fz = (target[i] - eye[i] for i in range(3))
    l = math.sqrt(fx * fx + fy * fy + fz * fz)
    f = (fx / l, fy / l, fz / l)
    up = (0, 1, 0)
    s = (f[1] * up[2] - f[2] * up[1], f[2] * up[0] - f[0] * up[2], f[0] * up[1] - f[1] * up[0])
    l = math.sqrt(sum(c * c for c in s))
    s = tuple(c / l for c in s)
    u = (s[1] * f[2] - s[2] * f[1], s[2] * f[0] - s[0] * f[2], s[0] * f[1] - s[1] * f[0])
    m = [[s[0], s[1], s[2], 0], [u[0], u[1], u[2], 0], [-f[0], -f[1], -f[2], 0], [0, 0, 0, 1]]
    return mul(m, T(-eye[0], -eye[1], -eye[2]))

# ---------------------------------------------------------------- player


def box_quads(x, y, z, w, h, d, rgb):
    el = {'from': [x, y, z], 'to': [x + w, y + h, z + d],
          'faces': {n: {'uv': [0, 0, 0, 0]} for n in SHADE}}
    pal = (1, 1, [[rgb + (255,)]])
    return face_quads({'elements': [el]}, pal)


def player_parts():
    """Player model parts in model space (pixels, y down) with pivots."""
    skin, shirt, pants = (200, 160, 130), (60, 110, 170), (50, 50, 90)
    return {
        'head': ((0, 0, 0), box_quads(-4, -8, -4, 8, 8, 8, skin)),
        'body': ((0, 0, 0), box_quads(-4, 0, -2, 8, 12, 4, shirt)),
        'right_arm': ((-5, 2, 0), box_quads(-3, -2, -2, 4, 12, 4, shirt)),
        'left_arm': ((5, 2, 0), box_quads(-1, -2, -2, 4, 12, 4, shirt)),
        'right_leg': ((-1.9, 12, 0), box_quads(-2, 0, -2, 4, 12, 4, pants)),
        'left_leg': ((1.9, 12, 0), box_quads(-2, 0, -2, 4, 12, 4, pants)),
    }


def entity_base():
    # LivingEntityRenderer: rotate Y (180 - bodyYaw), scale(-1,-1,1), player scale 0.9375,
    # translate(0, -1.501, 0); model parts are in pixels (1/16).
    return chain(Ry(180), S(-1, -1, 1), S(0.9375), T(0, -1.501, 0))


def part_matrix(pivot, xrot_deg=0.0):
    # ModelPart.translateAndRotate: translate(pivot/16) then rotationZYX(z, y, x)
    return chain(T(pivot[0] / 16, pivot[1] / 16, pivot[2] / 16), Rx(xrot_deg))

# ---------------------------------------------------------------- views


def load_model(models_dir, name, palette):
    model = json.load(open(os.path.join(models_dir, name)))
    return model, face_quads(model, palette)


def render_gui(model, quads, size=256):
    c = Canvas(size, size, (139, 139, 139))
    world = chain(display_matrix(model, 'gui'))
    draw(c, quads, world, ortho(size, size / 2, size / 2))
    return c


def render_ground(model, quads, size=256):
    c = Canvas(size, size, (90, 120, 70))
    world = chain(Rx(-30), Ry(30), display_matrix(model, 'ground'))
    draw(c, quads, world, ortho(size * 1.6, size / 2, size / 2), flat=False)
    return c


def render_first_person(model, quads, w=480, h=270):
    c = Canvas(w, h, (120, 160, 210))
    # floor hint
    c.rect(0, int(h * 0.62), w, h, (110, 110, 100))
    world = chain(T(0.56, -0.52, -0.72), display_matrix(model, 'firstperson_righthand'))
    draw(c, quads, world, perspective(w, h, 70), flat=False)
    # vanilla crosshair position
    for d in range(-6, 7):
        if abs(d) > 1:
            c.px[h // 2][w // 2 + d] = (255, 255, 255, 255)
            c.px[h // 2 + d][w // 2] = (255, 255, 255, 255)
    return c


def render_third_person(model, quads, w=320, h=320, side=True):
    c = Canvas(w, h, (120, 160, 210))
    eye = (-2.6, 1.6, 1.6) if side else (-0.9, 1.5, 3.2)
    view = look_at(eye, (0, 1.0, 0.3))
    proj = perspective(w, h, 50)
    base = entity_base()
    arm_x = -18.0  # HumanoidModel ITEM pose: xRot * 0.5 - PI/10
    for name, (pivot, pq) in player_parts().items():
        xr = arm_x if name == 'right_arm' else 0.0
        m = chain(view, base, part_matrix(pivot, xr), S(1 / 16))
        draw(c, pq, m, proj, flat=False)
    hand = chain(view, base, part_matrix((-5, 2, 0), arm_x),
                 Rx(-90), Ry(180), T(1 / 16, 2 / 16, -10 / 16),
                 display_matrix(model, 'thirdperson_righthand'))
    draw(c, quads, hand, proj, flat=False)
    return c


def render_side(model, quads, size=256):
    """Plain side view (model +X side), barrel (-Z) pointing right."""
    c = Canvas(size, size, (58, 62, 70))
    world = chain(Ry(-90), T(-0.5, -0.5, -0.5), S(1 / 16))
    draw(c, quads, world, ortho(size * 0.75, size / 2, size / 2))
    return c


def render_iso(model, quads, size=256):
    c = Canvas(size, size, (58, 62, 70))
    world = chain(Rx(30), Ry(-135), T(-0.5, -0.5, -0.5), S(1 / 16))
    draw(c, quads, world, ortho(size * 0.9, size / 2, size / 2), flat=False)
    return c


def sheet(canvases, path, bg=(30, 30, 30)):
    w = sum(cv.w for cv in canvases) + 4 * (len(canvases) + 1)
    h = max(cv.h for cv in canvases) + 8
    out = Canvas(w, h, bg)
    x = 4
    for cv in canvases:
        for yy in range(cv.h):
            out.px[4 + yy][x:x + cv.w] = cv.px[yy]
        x += cv.w + 4
    out.save(path)
