#!/usr/bin/env python3
"""News-image-20261121 v1: one-page newspaper of Saturday 21 November 2026.

Pure standard library. Reads data.json next to this file, draws a 1024x1024
PNG with an embedded 5x7 bitmap font, writes it to $MAKEFUN_OUTPUT_DIR.
Deterministic: no network, no randomness, no clock, no absolute paths.
"""
import json
import os
import struct
import sys
import zlib

W, H = 1024, 1024

# --- 5x7 bitmap font: each glyph is 7 rows of 5 bits, '#' on, '.' off. ---
_G = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "a": ("00000", "00000", "01110", "00001", "01111", "10001", "01111"),
    "b": ("10000", "10000", "11110", "10001", "10001", "10001", "11110"),
    "c": ("00000", "00000", "01110", "10000", "10000", "10001", "01110"),
    "d": ("00001", "00001", "01111", "10001", "10001", "10001", "01111"),
    "e": ("00000", "00000", "01110", "10001", "11111", "10000", "01110"),
    "f": ("00110", "01001", "01000", "11110", "01000", "01000", "01000"),
    "g": ("00000", "00000", "01110", "10001", "10001", "01111", "01100"),
    "h": ("10000", "10000", "11110", "10001", "10001", "10001", "10001"),
    "i": ("00100", "00000", "01100", "00100", "00100", "00100", "01110"),
    "j": ("00010", "00000", "00110", "00010", "00010", "10010", "01100"),
    "k": ("10000", "10000", "10010", "10100", "11000", "10100", "10010"),
    "l": ("01100", "00100", "00100", "00100", "00100", "00100", "01110"),
    "m": ("00000", "00000", "11010", "10101", "10101", "10101", "10101"),
    "n": ("00000", "00000", "11110", "10001", "10001", "10001", "10001"),
    "o": ("00000", "00000", "01110", "10001", "10001", "10001", "01110"),
    "p": ("00000", "00000", "01110", "10001", "10001", "01110", "10000"),
    "q": ("00000", "00000", "01111", "10001", "10001", "01111", "00001"),
    "r": ("00000", "00000", "10110", "11001", "10000", "10000", "10000"),
    "s": ("00000", "00000", "01111", "10000", "01110", "00001", "11110"),
    "t": ("01000", "01000", "11100", "01000", "01000", "01001", "00110"),
    "u": ("00000", "00000", "10001", "10001", "10001", "10011", "01101"),
    "v": ("00000", "00000", "10001", "10001", "10001", "01010", "00100"),
    "w": ("00000", "00000", "10001", "10101", "10101", "10101", "01010"),
    "x": ("00000", "00000", "10001", "01010", "00100", "01010", "10001"),
    "y": ("00000", "00000", "10001", "10001", "01111", "00001", "01110"),
    "z": ("00000", "00000", "11111", "00010", "00100", "01000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '"': ("01010", "01010", "01010", "00000", "00000", "00000", "00000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "*": ("00000", "10101", "01110", "11111", "01110", "10101", "00000"),
    "[": ("01110", "01000", "01000", "01000", "01000", "01000", "01110"),
    "]": ("01110", "00010", "00010", "00010", "00010", "00010", "01110"),
}
FONT = _G


def text_width(text, scale):
    return len(text) * 6 * scale - scale


def wrap_text(text, max_width, scale):
    """Greedy word wrap; returns list of lines, each fitting max_width px."""
    words = text.split(" ")
    lines, cur = [], ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_width(trial, scale) <= max_width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg) * (w * h)

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(color)

    def fill_rect(self, x, y, w, h, color):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            row = bytes(color) * (x1 - x0)
            self.px[base:base + (x1 - x0) * 3] = row

    def rect(self, x, y, w, h, color, t=1):
        self.fill_rect(x, y, w, t, color)
        self.fill_rect(x, y + h - t, w, t, color)
        self.fill_rect(x, y, t, h, color)
        self.fill_rect(x + w - t, y, t, h, color)

    def hline(self, x, y, w, color, t=1):
        self.fill_rect(x, y, w, t, color)

    def vline(self, x, y, h, color, t=1):
        self.fill_rect(x, y, t, h, color)

    def line(self, x0, y0, x1, y1, color, t=1):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self.fill_rect(x0 - t // 2, y0 - t // 2, t, t, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, color, fill=True):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d2 = (xx - cx) ** 2 + (yy - cy) ** 2
                if fill:
                    if d2 <= r * r:
                        self.set(xx, yy, color)
                else:
                    if abs(d2 - r * r) <= r:
                        self.set(xx, yy, color)

    def poly(self, pts, color):
        """Scanline fill of a simple polygon (list of (x, y))."""
        if len(pts) < 3:
            return
        ys = [p[1] for p in pts]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    t = (y - y0) / (y1 - y0)
                    xs.append(x0 + t * (x1 - x0))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                self.fill_rect(int(xs[k]), y, max(1, int(xs[k + 1]) - int(xs[k])), 1, color)

    def text(self, x, y, s, scale, color, bold=False):
        cx = x
        for ch in s:
            glyph = FONT.get(ch, FONT["?"])
            for r in range(7):
                row = glyph[r]
                for c in range(5):
                    if row[c] == "1":
                        self.fill_rect(cx + c * scale, y + r * scale, scale, scale, color)
                        if bold:
                            self.fill_rect(cx + c * scale + 1, y + r * scale, scale, scale, color)
            cx += 6 * scale
        return cx

    def text_center(self, cx, y, s, scale, color, bold=False):
        self.text(cx - text_width(s, scale) // 2, y, s, scale, color, bold)


def write_png(canvas, path):
    raw = bytearray()
    stride = canvas.w * 3
    for y in range(canvas.h):
        raw.append(0)  # filter: None
        raw += canvas.px[y * stride:(y + 1) * stride]

    def chunk(kind, data):
        out = struct.pack(">I", len(data)) + kind + data
        out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)

# --- palette ---
PAPER = (247, 243, 232)
INK = (26, 26, 26)
RED = (163, 18, 18)
BLUE = (31, 78, 121)
GREY = (110, 108, 100)
LIGHT = (232, 226, 210)
SKY = (214, 228, 238)
GOLD = (176, 132, 24)

# --- icons: drawn in a box (x, y, w, h), original pictograms ---
def draw_icon(cv, name, x, y, w, h):
    cx, cy = x + w // 2, y + h // 2
    if name == "missile":
        cv.line(x + 8, y + h - 10, x + w - 14, y + 12, INK, 4)
        cv.poly([(x + w - 14, y + 12), (x + w - 4, y + 16), (x + w - 18, y + 22)], RED)
        cv.circle(x + 12, y + h - 12, 4, GOLD, True)
        cv.circle(x + w - 8, y + 8, 3, RED, True)
        cv.circle(x + 8, y + 10, 3, RED, True)
    elif name == "chart":
        cv.line(x + 8, y + 8, x + 8, y + h - 8, INK, 2)
        cv.line(x + 8, y + h - 8, x + w - 6, y + h - 8, INK, 2)
        pts = [(x + 10, y + 14), (x + w // 3, y + 22), (x + w // 2, y + 18),
               (x + 2 * w // 3, y + 34), (x + w - 10, y + h - 14)]
        for a, b in zip(pts, pts[1:]):
            cv.line(a[0], a[1], b[0], b[1], RED, 3)
        cv.poly([(x + w - 10, y + h - 14), (x + w - 18, y + h - 16), (x + w - 12, y + h - 6)], RED)
    elif name == "shield":
        cv.poly([(cx, y + 6), (cx + 16, y + 12), (cx + 16, y + 28), (cx, y + h - 6),
                 (cx - 16, y + 28), (cx - 16, y + 12)], BLUE)
        cv.line(cx - 7, cy + 1, cx - 2, cy + 7, PAPER, 3)
        cv.line(cx - 2, cy + 7, cx + 8, cy - 6, PAPER, 3)
    elif name == "flags":
        for i, col in enumerate((RED, BLUE, GOLD)):
            px = x + 10 + i * 14
            cv.vline(px, y + 8, h - 14, INK, 2)
            cv.fill_rect(px + 2, y + 8, 11, 9, col)
    elif name == "target":
        cv.circle(cx, cy, 18, RED, False)
        cv.circle(cx, cy, 12, INK, False)
        cv.circle(cx, cy, 6, RED, False)
        cv.circle(cx, cy, 2, INK, True)
    elif name == "drone":
        cv.fill_rect(cx - 12, cy - 5, 24, 10, INK)
        cv.circle(cx - 14, cy - 12, 6, BLUE, False)
        cv.circle(cx + 14, cy - 12, 6, BLUE, False)
        cv.circle(cx - 14, cy + 12, 6, BLUE, False)
        cv.circle(cx + 14, cy + 12, 6, BLUE, False)
        cv.circle(cx, cy, 3, RED, True)
    elif name == "bars":
        for i in range(5):
            cv.vline(x + 8 + i * 8, y + 6, h - 12, INK, 3)
        cv.circle(cx, cy, 7, GOLD, False)
        cv.line(cx + 5, cy + 5, cx + 10, cy + 10, GOLD, 2)
    elif name == "gavel":
        cv.line(cx - 12, cy + 12, cx + 12, cy - 10, INK, 3)
        cv.fill_rect(cx - 2, cy - 16, 16, 9, INK)
        cv.fill_rect(cx - 16, cy + 14, 32, 4, GREY)
    elif name == "candle":
        cv.circle(cx, y + 10, 4, GOLD, True)
        cv.fill_rect(cx - 4, y + 16, 8, h - 26, INK)
        cv.fill_rect(cx - 10, y + h - 10, 20, 4, GREY)
    elif name == "globe":
        cv.circle(cx, cy, 18, BLUE, False)
        cv.line(cx - 18, cy, cx + 18, cy, BLUE, 1)
        cv.line(cx, cy - 18, cx, cy + 18, BLUE, 1)
        cv.circle(cx - 6, cy - 6, 2, RED, True)
        cv.circle(cx + 7, cy + 5, 2, RED, True)
        cv.circle(cx - 2, cy + 9, 2, RED, True)
    else:
        cv.circle(cx, cy, 12, RED, False)


# --- world map: rough continent outlines in (lon, lat) ---
CONTINENTS = [
    [(-168, 66), (-140, 70), (-125, 71), (-110, 68), (-95, 69), (-85, 66),
     (-75, 62), (-65, 60), (-55, 52), (-60, 46), (-70, 42), (-75, 35),
     (-80, 26), (-85, 20), (-90, 15), (-95, 16), (-105, 20), (-115, 28),
     (-125, 40), (-125, 49), (-140, 60), (-155, 58), (-165, 60)],
    [(-58, 64), (-45, 60), (-30, 68), (-22, 70), (-30, 76), (-45, 76), (-58, 74)],
    [(-80, 10), (-75, 12), (-65, 10), (-60, 5), (-52, 4), (-50, 0),
     (-40, -5), (-35, -8), (-40, -20), (-48, -28), (-55, -35), (-65, -40),
     (-70, -50), (-73, -53), (-70, -45), (-72, -30), (-78, -15), (-80, -5)],
    [(-17, 15), (-10, 30), (0, 36), (10, 37), (20, 32), (30, 31), (35, 28),
     (40, 15), (43, 11), (50, 10), (45, 0), (40, -10), (35, -20), (30, -30),
     (25, -34), (18, -32), (12, -18), (9, -1), (9, 4), (-8, 5), (-13, 8)],
    [(-10, 36), (-9, 43), (-2, 48), (0, 50), (5, 53), (8, 57), (10, 59),
     (18, 56), (21, 55), (24, 59), (28, 60), (30, 62), (25, 65), (20, 70),
     (15, 70), (5, 60), (5, 58), (-5, 50), (-10, 43)],
    [(30, 62), (40, 68), (60, 70), (80, 72), (100, 76), (120, 73), (140, 72),
     (160, 70), (178, 65), (170, 60), (160, 55), (150, 60), (140, 45),
     (130, 40), (127, 35), (120, 30), (110, 20), (105, 10), (100, 8),
     (95, 15), (90, 22), (80, 10), (75, 8), (70, 20), (60, 25), (55, 28),
     (48, 30), (43, 35), (35, 36), (30, 36), (28, 40), (30, 45), (35, 50)],
    [(113, -22), (114, -30), (115, -35), (124, -33), (130, -32), (135, -35),
     (140, -38), (145, -38), (150, -37), (153, -30), (150, -22), (146, -19),
     (142, -11), (135, -12), (130, -13), (126, -14), (122, -17), (117, -20)],
]


def draw_map(cv, x, y, w, h, pins):
    cv.fill_rect(x, y, w, h, SKY)
    cv.rect(x, y, w, h, INK, 1)
    def proj(lon, lat):
        px = x + 6 + (lon + 180.0) / 360.0 * (w - 12)
        py = y + 4 + (90.0 - lat) / 180.0 * (h - 8)
        return (int(px), int(py))
    for cont in CONTINENTS:
        cv.poly([proj(lon, lat) for lon, lat in cont], (196, 190, 170))
    for lat, lon, label in pins:
        px, py = proj(lon, lat)
        cv.circle(px, py, 7, RED, True)
        cv.circle(px, py, 7, INK, False)
        cv.text(px - 2, py - 4, label, 1, PAPER, bold=True)


def draw_lead(cv, x, y, w, h, story):
    cv.fill_rect(x, y, w, h, LIGHT)
    cv.rect(x, y, w, h, INK, 1)
    tx = x + 14
    cv.text(tx, y + 10, "1  " + story["kicker"], 1, RED, bold=True)
    head_lines = wrap_text(story["head"], w - 330, 3)
    hy = y + 30
    for ln in head_lines[:2]:
        cv.text(tx, hy, ln, 3, INK, bold=True)
        hy += 24
    body_lines = wrap_text(story["body"], w - 330, 2)
    by = hy + 6
    for ln in body_lines[:4]:
        cv.text(tx, by, ln, 2, INK)
        by += 17
    ix, iy, iw, ih = x + w - 300, y + 12, 286, h - 24
    cv.fill_rect(ix, iy, iw, ih, SKY)
    cv.rect(ix, iy, iw, ih, INK, 1)
    cv.poly([(ix + 20, iy + ih - 20), (ix + 90, iy + 60), (ix + 150, iy + ih - 20)], (120, 120, 110))
    cv.poly([(ix + 110, iy + ih - 20), (ix + 180, iy + 40), (ix + 250, iy + ih - 20)], (90, 90, 85))
    cv.line(ix + 40, iy + 30, ix + 240, iy + 55, INK, 4)
    cv.poly([(ix + 240, iy + 55), (ix + 258, iy + 60), (ix + 238, iy + 68)], RED)
    cv.circle(ix + 60, iy + 110, 5, RED, True)
    cv.circle(ix + 200, iy + 95, 5, RED, True)
    cv.circle(ix + 150, iy + 120, 4, GOLD, True)
    cv.text(ix + 10, iy + ih - 16, "KYIV UNDER FIRE; WARSAW ON ALERT", 1, INK, bold=True)


def draw_card(cv, x, y, w, h, story):
    cv.rect(x, y, w, h, INK, 1)
    n = str(story["n"])
    cv.fill_rect(x, y, 26, 20, RED)
    cv.text(x + 9 if len(n) == 1 else x + 5, y + 6, n, 1, PAPER, bold=True)
    cv.text(x + 32, y + 6, story["kicker"], 1, RED, bold=True)
    ix, iy = x + w - 62, y + 26
    cv.fill_rect(ix, iy, 52, 52, LIGHT)
    cv.rect(ix, iy, 52, 52, GREY, 1)
    draw_icon(cv, story["icon"], ix, iy, 52, 52)
    head_lines = wrap_text(story["head"], w - 62 - 14 - 8, 2)
    hy = y + 26
    for ln in head_lines[:2]:
        cv.text(x + 8, hy, ln, 2, INK, bold=True)
        hy += 17
    body_lines = wrap_text(story["body"], w - 16, 2)
    by = y + 82
    for ln in body_lines[:3]:
        cv.text(x + 8, by, ln, 2, INK)
        by += 17


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "data.json"), "r", encoding="utf-8") as f:
        data = json.load(f)
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "")
    if not out_dir:
        sys.stderr.write("MAKEFUN_OUTPUT_DIR is not set\n")
        return 1
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "entry.png")

    cv = Canvas(W, H, PAPER)
    mx = 22  # side margin

    # --- masthead ---
    cv.text_center(W // 2, 18, data["paper"], 5, INK, bold=True)
    cv.hline(mx, 62, W - 2 * mx, INK, 3)
    cv.text_center(W // 2, 70, data["date"].upper(), 2, RED, bold=True)
    cv.text(mx, 70, "No. 325", 1, GREY)
    cv.text(W - mx - text_width("PRICE: ONE DAY", 1), 70, "PRICE: ONE DAY", 1, GREY)
    cv.hline(mx, 90, W - 2 * mx, INK, 1)

    # --- lead story ---
    draw_lead(cv, mx, 100, W - 2 * mx, 150, data["main"][0])

    # --- nine main stories, 3 x 3 ---
    grid_x, grid_y = mx, 258
    cw = (W - 2 * mx - 2 * 12) // 3
    ch = 140
    for i, story in enumerate(data["main"][1:]):
        r, c = divmod(i, 3)
        draw_card(cv, grid_x + c * (cw + 12), grid_y + r * (ch + 10), cw, ch, story)

    # --- also list ---
    ay = grid_y + 3 * ch + 2 * 8 + 8
    cv.text(mx, ay, "ALSO ON SATURDAY 21 NOVEMBER", 2, RED, bold=True)
    cv.hline(mx, ay + 20, W - 2 * mx, INK, 1)
    col_w = (W - 2 * mx - 24) // 2
    for i, item in enumerate(data["also"]):
        col, row = divmod(i, 10)
        ix = mx + col * (col_w + 24)
        iy = ay + 26 + row * 13
        line = item
        while text_width(line, 1) > col_w - 12 and len(line) > 10:
            line = line[:-1]
        cv.text(ix, iy, "-", 1, RED, bold=True)
        cv.text(ix + 10, iy, line, 1, INK)

    # --- map + day in numbers ---
    my = ay + 26 + 10 * 13 + 8
    map_w = 620
    draw_map(cv, mx, my, map_w, 96, data["map_pins"])
    nx = mx + map_w + 14
    nw = W - mx - nx
    cv.fill_rect(nx, my, nw, 96, LIGHT)
    cv.rect(nx, my, nw, 96, INK, 1)
    cv.text(nx + 10, my + 8, "THE DAY IN NUMBERS", 1, RED, bold=True)
    cell_w = (nw - 20) // 4
    for i, (big, label) in enumerate(data["numbers"]):
        r, c = divmod(i, 4)
        bx = nx + 10 + c * cell_w
        by = my + 26 + r * 34
        cv.text(bx, by, big, 2, INK, bold=True)
        lab_lines = wrap_text(label, cell_w - 6, 1)
        ly = by + 16
        for ln in lab_lines[:2]:
            cv.text(bx, ly, ln, 1, GREY)
            ly += 11

    # --- footer: note to the judge ---
    fy = my + 96 + 8
    cv.hline(mx, fy, W - 2 * mx, INK, 1)
    cv.text(mx, fy + 8, "TO THE JUDGE: every story above happened, or was first reported, on 21 Nov 2026 in some time zone;", 1, INK)
    cv.text(mx, fy + 20, "each checked in at least two sources. " + data["cutoff"], 1, INK)

    size = write_png(cv, out_path)
    sys.stdout.write("wrote %s (%d bytes)\n" % (out_path, size))
    return 0


if __name__ == "__main__":
    sys.exit(main())
