"""Build dist/lairner-pack.zip from pack/ and print its SHA-1.

Steps: regenerate models and textures (deterministic; sounds are built
separately with tools/sounds.py because they need the source libraries),
validate every reference, write a reproducible zip (sorted entries, fixed
timestamps), write dist/lairner-pack.zip.sha1.

Usage: python3 tools/build.py [--no-gen]
"""
import hashlib
import json
import os
import subprocess
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACK = os.path.join(ROOT, 'pack')
DIST = os.path.join(ROOT, 'dist')
ZIP = os.path.join(DIST, 'lairner-pack.zip')
DIST_TEST = os.path.join(ROOT, 'dist-test')
ZIP_TEST = os.path.join(DIST_TEST, 'lairner-pack-test.zip')
# The core shader (kill feed anchored to the right screen edge) ships only in the test zip until Tim has
# confirmed it on a client; then set this to True and rebuild (dist/ gets it too).
SHADER_LIVE = False
SHADER_DIR = 'assets/minecraft/shaders/'
PACK_FORMAT = 97          # 26.3 client: resource pack format 97.1
MAX_ELEMENTS = 300

errors = []


def err(msg):
    errors.append(msg)


def asset_path(ref, kind, ext):
    ns, _, path = ref.partition(':') if ':' in ref else ('minecraft', '', ref)
    return os.path.join(PACK, 'assets', ns, kind, path + ext)


def load(path):
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:  # noqa: BLE001
        err('%s: %s' % (os.path.relpath(path, ROOT), e))
        return None


def validate():
    # every json parses
    for dp, _, fns in os.walk(PACK):
        for fn in fns:
            if fn.endswith('.json') or fn.endswith('.mcmeta'):
                load(os.path.join(dp, fn))

    meta = load(os.path.join(PACK, 'pack.mcmeta')) or {}
    p = meta.get('pack', {})
    if p.get('min_format') != PACK_FORMAT or p.get('max_format') != PACK_FORMAT:
        err('pack.mcmeta: min_format/max_format must be %d' % PACK_FORMAT)
    if not os.path.exists(os.path.join(PACK, 'pack.png')):
        err('pack.png missing')

    la = os.path.join(PACK, 'assets', 'lairner')
    # item definitions -> models -> textures
    idir = os.path.join(la, 'items', 'df')
    for fn in sorted(os.listdir(idir)):
        item = load(os.path.join(idir, fn))
        if not item:
            continue
        mref = item['model']['model']
        mpath = asset_path(mref, 'models', '.json')
        if not os.path.exists(mpath):
            err('items/df/%s -> missing model %s' % (fn, mref))
            continue
        model = load(mpath)
        els = model.get('elements', [])
        if not els or len(els) > MAX_ELEMENTS:
            err('%s: %d elements' % (mref, len(els)))
        for el in els:
            for c in el['from'] + el['to']:
                if not -16 <= c <= 32:
                    err('%s: coordinate %s outside -16..32' % (mref, c))
                    break
            for face in el['faces'].values():
                key = face['texture'].lstrip('#')
                if key not in model['textures']:
                    err('%s: face uses undefined texture #%s' % (mref, key))
        for key, tref in model.get('textures', {}).items():
            if not os.path.exists(asset_path(tref, 'textures', '.png')):
                err('%s: texture %s missing' % (mref, tref))
        for ctx, d in model.get('display', {}).items():
            if any(abs(t) > 80 for t in d.get('translation', [])) or any(s > 4 for s in d.get('scale', [])):
                err('%s: display %s out of range' % (mref, ctx))

    # font
    font = load(os.path.join(la, 'font', 'df.json')) or {}
    seen = set()
    for prov in font.get('providers', []):
        if prov['type'] == 'bitmap':
            if not os.path.exists(asset_path(prov['file'].replace('.png', ''), 'textures', '.png')):
                err('font: missing %s' % prov['file'])
            if prov['ascent'] > prov.get('height', 8):
                err('font: ascent > height for %s' % prov['file'])
            chars = ''.join(prov['chars'])
        else:
            chars = ''.join(prov.get('advances', {}))
        for ch in chars:
            if ch in seen:
                err('font: U+%04X defined twice' % ord(ch))
            seen.add(ch)

    # sounds
    sounds = load(os.path.join(la, 'sounds.json')) or {}
    used = set()
    for ev, entry in sounds.items():
        for s in entry['sounds']:
            name = s['name'] if isinstance(s, dict) else s
            path = asset_path(name, 'sounds', '.ogg')
            used.add(os.path.normpath(path))
            if not os.path.exists(path):
                err('sounds.json %s -> missing %s' % (ev, name))
    for dp, _, fns in os.walk(os.path.join(la, 'sounds')):
        for fn in fns:
            if os.path.normpath(os.path.join(dp, fn)) not in used:
                err('unused sound file %s' % os.path.relpath(os.path.join(dp, fn), PACK))

    # vanilla overrides we ship
    hud = os.path.join(PACK, 'assets', 'minecraft', 'textures', 'gui', 'sprites', 'hud')
    for n in ('food_empty', 'food_half', 'food_full', 'food_empty_hunger', 'food_half_hunger',
              'food_full_hunger', 'crosshair'):
        if not os.path.exists(os.path.join(hud, n + '.png')):
            err('missing hud sprite %s' % n)


def build_zip(zip_path, with_shaders):
    os.makedirs(os.path.dirname(zip_path), exist_ok=True)
    files = []
    for dp, _, fns in os.walk(PACK):
        for fn in fns:
            full = os.path.join(dp, fn)
            arc = os.path.relpath(full, PACK).replace(os.sep, '/')
            if arc.startswith(SHADER_DIR) and not with_shaders:
                continue
            files.append((arc, full))
    files.sort()
    tmp = zip_path + '.tmp'
    with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for arc, full in files:
            info = zipfile.ZipInfo(arc, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_STORED if arc.endswith(('.ogg', '.png')) else zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            with open(full, 'rb') as f:
                z.writestr(info, f.read())
    os.replace(tmp, zip_path)
    data = open(zip_path, 'rb').read()
    sha1 = hashlib.sha1(data).hexdigest()
    with open(zip_path + '.sha1', 'w') as f:
        f.write(sha1 + '\n')
    return sha1, len(data), len(files)


def main():
    if '--no-gen' not in sys.argv:
        for script in ('models.py', 'textures.py'):
            subprocess.run([sys.executable, '-I', os.path.join(ROOT, 'tools', script)], check=True,
                           stdout=subprocess.DEVNULL)
    validate()
    if errors:
        print('\n'.join('ERROR ' + e for e in errors))
        sys.exit(1)
    sha1, size, n = build_zip(ZIP, SHADER_LIVE)
    print('dist/lairner-pack.zip  %d files  %.1f KB  (shader: %s)' % (n, size / 1024, SHADER_LIVE))
    print('SHA-1 %s' % sha1)
    if not SHADER_LIVE:
        sha1, size, n = build_zip(ZIP_TEST, True)
        print('dist-test/lairner-pack-test.zip  %d files  %.1f KB  (with the core shader)' % (n, size / 1024))
        print('SHA-1 %s' % sha1)
    elif os.path.exists(ZIP_TEST):
        os.remove(ZIP_TEST)
        os.remove(ZIP_TEST + '.sha1')


if __name__ == '__main__':
    main()
