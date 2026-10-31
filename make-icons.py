#!/usr/bin/env python3
"""Regenerate the PWA icons from official-icon.png.

Why this exists. make-icons-v2.ps1 scaled the source straight onto the canvas,
so every icon kept the source's ~8% transparent margin. MIUI/HyperOS draws a
legacy ("any") icon on a white rounded rect, so that margin showed up as a
white border around the icon -- that is the bug this fixes. The maskable
variant had a second problem: it pasted the whole source (transparent margin
included) inside a rounded rect filled with #0e0f11, so the source's own
near-black plate appeared as a lighter square with a seam ring around it.

What this script does instead. The source artwork is a rounded dark plate with
a vertical gradient and a white Z on it. Launchers already mask icons to their
own shape, so the plate's rounded corners serve no purpose -- they only leave
transparent pixels for the launcher background to shine through. This script
therefore rebuilds each icon as a *full-bleed, fully opaque* square:

  1. crop the source to its opaque bounding box, dropping the margin;
  2. measure the plate's own per-row colour (median of its solid pixels) and
     use that to synthesise a background, so the plate's boundary disappears
     into a continuous vertical gradient instead of ending in a visible edge;
  3. scale the artwork to ART_RATIO of the canvas and centre it on that
     background. The white mark then sits well inside the maskable safe circle
     (radius 40% of the icon), so a launcher may crop to any shape without
     clipping it.

Every pixel ends up opaque, so no launcher background can show through. That
also makes a separate `maskable` file unnecessary: the 512 icon is full-bleed
and safe-zone clean, so the manifest declares it as `any maskable` and one
image serves both roles.

Pure stdlib (zlib + struct), no Pillow. Usage: python3 make-icons.py
"""

import struct
import sys
import zlib

SRC = "official-icon.png"
CANVAS = 512
ART_RATIO = 0.92          # artwork size as a fraction of the canvas
ALPHA_SOLID = 32          # alpha at or above this counts as solid artwork
ALPHA_MIN = 8             # anything below this is treated as empty margin
OUT = [
    (192, "icon-192-v3.png"),
    (512, "icon-512-v3.png"),
]


# ---------- PNG decode ----------

def _paeth(a, b, c):
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    return b if pb <= pc else c


def read_png(path):
    data = open(path, "rb").read()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "not a PNG"
    pos, idat, meta = 8, bytearray(), None
    while pos < len(data):
        (length,) = struct.unpack(">I", data[pos:pos + 4])
        ctype = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + length]
        if ctype == b"IHDR":
            meta = struct.unpack(">IIBBBBB", body)
        elif ctype == b"IDAT":
            idat += body
        elif ctype == b"IEND":
            break
        pos += 12 + length
    w, h, depth, color, _comp, _filt, interlace = meta
    assert depth == 8 and interlace == 0, "only 8-bit non-interlaced PNGs"
    channels = {0: 1, 2: 3, 4: 2, 6: 4}[color]
    raw = zlib.decompress(bytes(idat))
    stride = w * channels
    out = bytearray(h * stride)
    prev = bytearray(stride)
    p = 0
    for y in range(h):
        f = raw[p]
        p += 1
        line = bytearray(raw[p:p + stride])
        p += stride
        if f == 1:
            for i in range(channels, stride):
                line[i] = (line[i] + line[i - channels]) & 0xFF
        elif f == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif f == 3:
            for i in range(stride):
                left = line[i - channels] if i >= channels else 0
                line[i] = (line[i] + ((left + prev[i]) >> 1)) & 0xFF
        elif f == 4:
            for i in range(stride):
                left = line[i - channels] if i >= channels else 0
                ul = prev[i - channels] if i >= channels else 0
                line[i] = (line[i] + _paeth(left, prev[i], ul)) & 0xFF
        elif f != 0:
            raise ValueError("bad filter %d" % f)
        out[y * stride:(y + 1) * stride] = line
        prev = line
    rgba = bytearray(w * h * 4)
    for i in range(w * h):
        px = out[i * channels:(i + 1) * channels]
        if channels == 4:
            rgba[i * 4:i * 4 + 4] = px
        elif channels == 3:
            rgba[i * 4:i * 4 + 3] = px
            rgba[i * 4 + 3] = 255
        elif channels == 2:
            g, a = px
            rgba[i * 4:i * 4 + 4] = bytes((g, g, g, a))
        else:
            g = px[0]
            rgba[i * 4:i * 4 + 4] = bytes((g, g, g, 255))
    return w, h, rgba


# ---------- PNG encode ----------

def write_png(path, w, h, rgba):
    raw = bytearray()
    stride = w * 4
    for y in range(h):
        raw.append(0)
        raw += rgba[y * stride:(y + 1) * stride]

    def chunk(tag, body):
        return (struct.pack(">I", len(body)) + tag + body
                + struct.pack(">I", zlib.crc32(tag + body) & 0xFFFFFFFF))

    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
           + chunk(b"IEND", b""))
    open(path, "wb").write(png)


# ---------- image ops ----------

def alpha_bbox(w, h, rgba, threshold=ALPHA_MIN):
    x0, y0, x1, y1 = w, h, -1, -1
    for y in range(h):
        row = y * w * 4
        for x in range(w):
            if rgba[row + x * 4 + 3] >= threshold:
                x0 = min(x0, x)
                x1 = max(x1, x)
                y0 = min(y0, y)
                y1 = max(y1, y)
    return x0, y0, x1 + 1, y1 + 1


def square_box(box, w, h):
    """Grow the bbox to a square centred on it, staying inside the image."""
    x0, y0, x1, y1 = box
    side = max(x1 - x0, y1 - y0)
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    nx0 = max(0, min(int(round(cx - side / 2.0)), w - side))
    ny0 = max(0, min(int(round(cy - side / 2.0)), h - side))
    return nx0, ny0, nx0 + side, ny0 + side


def crop(w, rgba, box):
    x0, y0, x1, y1 = box
    cw, ch = x1 - x0, y1 - y0
    out = bytearray(cw * ch * 4)
    for y in range(ch):
        src = ((y + y0) * w + x0) * 4
        out[y * cw * 4:(y + 1) * cw * 4] = rgba[src:src + cw * 4]
    return cw, ch, out


def resize(w, h, rgba, nw, nh):
    """Box-average downscale on premultiplied alpha, so soft edges do not pick
    up a dark fringe from the transparent margin."""
    pre = bytearray(w * h * 4)
    for i in range(w * h):
        a = rgba[i * 4 + 3]
        pre[i * 4] = rgba[i * 4] * a // 255
        pre[i * 4 + 1] = rgba[i * 4 + 1] * a // 255
        pre[i * 4 + 2] = rgba[i * 4 + 2] * a // 255
        pre[i * 4 + 3] = a
    out = bytearray(nw * nh * 4)
    for y in range(nh):
        sy0 = y * h // nh
        sy1 = max(sy0 + 1, (y + 1) * h // nh)
        for x in range(nw):
            sx0 = x * w // nw
            sx1 = max(sx0 + 1, (x + 1) * w // nw)
            r = g = b = a = n = 0
            for sy in range(sy0, sy1):
                base = sy * w * 4
                for sx in range(sx0, sx1):
                    o = base + sx * 4
                    r += pre[o]
                    g += pre[o + 1]
                    b += pre[o + 2]
                    a += pre[o + 3]
                    n += 1
            o = (y * nw + x) * 4
            if a:
                out[o] = min(255, r * 255 // a)
                out[o + 1] = min(255, g * 255 // a)
                out[o + 2] = min(255, b * 255 // a)
            out[o + 3] = a // n
    return out


def row_colours(w, h, rgba):
    """Colour of the plate itself for each row -- its vertical gradient.

    Sampling the whole row does not work: rows through the middle of the Z are
    more than half white, so a median there reports white and the background
    fill turns white too. The plate is what sits at the row's outer edges, so
    sample there and only fall back to the row median where the plate has not
    started yet (the rounded corners, where the edge is still transparent).
    Rows with nothing solid are left empty for the caller to interpolate.
    """
    edge = max(1, w // 8)
    rows = []
    for y in range(h):
        base = y * w * 4
        solid = [(rgba[base + x * 4], rgba[base + x * 4 + 1], rgba[base + x * 4 + 2])
                 for x in range(w) if rgba[base + x * 4 + 3] >= ALPHA_SOLID]
        if not solid:
            rows.append(None)
            continue
        picks = [solid[x] for x in list(range(min(edge, len(solid))))
                 + list(range(max(0, len(solid) - edge), len(solid)))]
        if not picks:
            picks = solid
        picks.sort()
        rows.append(picks[len(picks) // 2])
    return rows


def fill_gaps(rows):
    """Replace empty entries with the nearest measured row colour."""
    known = [i for i, c in enumerate(rows) if c is not None]
    assert known, "artwork is fully transparent"
    for i, c in enumerate(rows):
        if c is None:
            near = min(known, key=lambda k: (abs(k - i), k))
            rows[i] = rows[near]
    return rows


def compose(out, w, h, rgba, canvas, bg_rows, ox, oy):
    """Composite the artwork over a canvas pre-filled with bg_rows, honouring
    its alpha so the plate's soft edge fades into the matching background."""
    for y in range(h):
        drow = (y + oy) * canvas
        srow = y * w
        bg = bg_rows[y + oy]
        for x in range(w):
            s = (srow + x) * 4
            d = (drow + x + ox) * 4
            a = rgba[s + 3]
            if a >= 255:
                out[d:d + 3] = rgba[s:s + 3]
            else:
                inv = 255 - a
                out[d] = (rgba[s] * a + bg[0] * inv) // 255
                out[d + 1] = (rgba[s + 1] * a + bg[1] * inv) // 255
                out[d + 2] = (rgba[s + 2] * a + bg[2] * inv) // 255
            out[d + 3] = 255


def main():
    w, h, rgba = read_png(SRC)
    print("source        %dx%d" % (w, h))
    box = square_box(alpha_bbox(w, h, rgba), w, h)
    print("opaque bbox   %s (%dx%d)" % (box, box[2] - box[0], box[3] - box[1]))
    cw, ch, art = crop(w, rgba, box)

    side = int(round(CANVAS * ART_RATIO))
    art = resize(cw, ch, art, side, side)
    off = (CANVAS - side) // 2
    print("artwork       %dpx (%.0f%% of canvas), offset %d" % (side, ART_RATIO * 100, off))

    # Background: the plate's own gradient, stretched to the whole canvas. The
    # artwork is scaled first so the background is measured at final resolution.
    plate = fill_gaps(row_colours(side, side, art))
    bg_rows = [plate[min(side - 1, max(0, y - off))] for y in range(CANVAS)]

    master = bytearray(CANVAS * CANVAS * 4)
    for y in range(CANVAS):
        r, g, b = bg_rows[y]
        base = y * CANVAS * 4
        for x in range(CANVAS):
            o = base + x * 4
            master[o] = r
            master[o + 1] = g
            master[o + 2] = b
            master[o + 3] = 255
    compose(master, side, side, art, CANVAS, bg_rows, off, off)
    print("master        %dx%d, full-bleed, opaque" % (CANVAS, CANVAS))

    for size, name in OUT:
        img = master if size == CANVAS else resize(CANVAS, CANVAS, master, size, size)
        write_png(name, size, size, img)
        print("wrote %s (%dx%d)" % (name, size, size))
    return 0


if __name__ == "__main__":
    sys.exit(main())
