"""Minimal PNG reader/writer (stdlib only).

read_png(path) -> (width, height, rows) where rows[y][x] = (r, g, b, a)
write_png(path, width, height, pixels) where pixels[y][x] = (r, g, b, a)
"""
import struct
import zlib


def _paeth(a, b, c):
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def read_png(path):
    with open(path, 'rb') as f:
        data = f.read()
    if data[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError('not a PNG: %s' % path)
    pos = 8
    idat = b''
    palette = None
    trns = None
    while pos < len(data):
        length, ctype = struct.unpack('>I4s', data[pos:pos + 8])
        chunk = data[pos + 8:pos + 8 + length]
        pos += 12 + length
        if ctype == b'IHDR':
            w, h, depth, color, _, _, interlace = struct.unpack('>IIBBBBB', chunk)
        elif ctype == b'PLTE':
            palette = [tuple(chunk[i:i + 3]) for i in range(0, len(chunk), 3)]
        elif ctype == b'tRNS':
            trns = chunk
        elif ctype == b'IDAT':
            idat += chunk
        elif ctype == b'IEND':
            break
    if interlace:
        raise ValueError('interlaced PNG not supported')
    if depth != 8:
        raise ValueError('only 8-bit PNG supported')
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[color]
    raw = zlib.decompress(idat)
    stride = w * channels
    rows = []
    prev = bytearray(stride)
    i = 0
    for _ in range(h):
        ftype = raw[i]
        line = bytearray(raw[i + 1:i + 1 + stride])
        i += 1 + stride
        for x in range(stride):
            a = line[x - channels] if x >= channels else 0
            b = prev[x]
            c = prev[x - channels] if x >= channels else 0
            if ftype == 1:
                line[x] = (line[x] + a) & 255
            elif ftype == 2:
                line[x] = (line[x] + b) & 255
            elif ftype == 3:
                line[x] = (line[x] + ((a + b) >> 1)) & 255
            elif ftype == 4:
                line[x] = (line[x] + _paeth(a, b, c)) & 255
        prev = line
        row = []
        for x in range(w):
            px = line[x * channels:(x + 1) * channels]
            if color == 6:
                row.append(tuple(px))
            elif color == 2:
                row.append((px[0], px[1], px[2], 255))
            elif color == 0:
                row.append((px[0], px[0], px[0], 255))
            elif color == 4:
                row.append((px[0], px[0], px[0], px[1]))
            else:
                idx = px[0]
                r, g, b = palette[idx]
                a = trns[idx] if trns is not None and idx < len(trns) else 255
                row.append((r, g, b, a))
        rows.append(row)
    return w, h, rows


def write_png(path, w, h, pixels):
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        for x in range(w):
            raw.extend(bytes(pixels[y][x]))

    def chunk(t, d):
        c = struct.pack('>I', len(d)) + t + d
        return c + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)

    out = b'\x89PNG\r\n\x1a\n'
    out += chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0))
    out += chunk(b'IDAT', zlib.compress(bytes(raw), 9))
    out += chunk(b'IEND', b'')
    with open(path, 'wb') as f:
        f.write(out)


def blank(w, h, color=(0, 0, 0, 0)):
    return [[color for _ in range(w)] for _ in range(h)]
