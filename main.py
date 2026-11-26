"""THE WEDNESDAY LEDGER - one image of Wednesday 25 November 2026 world news.

Pure Python 3.13 standard library only. Draws a newspaper front page into a
1024x1024 RGB canvas with a hand-authored 5x7 glyph font and vector scenes,
then writes it as a PNG to $MAKEFUN_OUTPUT_DIR/entry.png.
Deterministic: no clock, no randomness, no network, no file reads.
"""

import os
import struct
import zlib

W = 1024
H = 1024

INK = (22, 20, 18)
PAPER = (252, 250, 243)
CREAM = (246, 241, 228)
GREY = (105, 100, 92)
LIGHT = (228, 222, 208)
RED = (163, 28, 24)
DARKRED = (122, 20, 18)
NAVY = (22, 40, 82)
SKY = (196, 222, 238)
SEA = (52, 96, 138)
ORANGE = (232, 116, 28)
YELLOW = (246, 190, 52)
GREEN = (24, 110, 52)
BLUE = (30, 80, 170)
AMBER = (178, 102, 8)
PURPLE = (118, 48, 148)
WHITE = (255, 255, 255)
BLACK = (8, 8, 8)

LABEL_COLORS = {
    "CONFIRMED": GREEN,
    "REPORTED": BLUE,
    "CLAIM": AMBER,
    "FORECAST": PURPLE,
}


class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bg) * (w * h)

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i] = color[0]
            self.px[i + 1] = color[1]
            self.px[i + 2] = color[2]

    def rect(self, x, y, w, h, color):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(color) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.px[i:i + len(row)] = row

    def frame(self, x, y, w, h, color, t=2):
        self.rect(x, y, w, t, color)
        self.rect(x, y + h - t, w, t, color)
        self.rect(x, y, t, h, color)
        self.rect(x + w - t, y, t, h, color)

    def hline(self, x, y, w, color, t=2):
        self.rect(x, y, w, t, color)

    def vline(self, x, y, h, color, t=2):
        self.rect(x, y, t, h, color)

    def circle(self, cx, cy, r, color):
        for yy in range(cy - r, cy + r + 1):
            dy = yy - cy
            rem = r * r - dy * dy
            if rem < 0:
                continue
            dx = int(rem ** 0.5)
            self.rect(cx - dx, yy, dx * 2 + 1, 1, color)

    def ring(self, cx, cy, r, color, t=2):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d2 = (xx - cx) ** 2 + (yy - cy) ** 2
                if (r - t) ** 2 < d2 <= r * r:
                    self.set(xx, yy, color)

    def tri(self, x1, y1, x2, y2, x3, y3, color):
        minx = max(0, min(x1, x2, x3))
        maxx = min(self.w - 1, max(x1, x2, x3))
        miny = max(0, min(y1, y2, y3))
        maxy = min(self.h - 1, max(y1, y2, y3))
        d = (y2 - y3) * (x1 - x3) + (x3 - x2) * (y1 - y3)
        if d == 0:
            return
        for yy in range(miny, maxy + 1):
            for xx in range(minx, maxx + 1):
                w1 = ((y2 - y3) * (xx - x3) + (x3 - x2) * (yy - y3)) / d
                w2 = ((y3 - y1) * (xx - x3) + (x1 - x3) * (yy - y3)) / d
                w3 = 1.0 - w1 - w2
                if w1 >= 0 and w2 >= 0 and w3 >= 0:
                    self.set(xx, yy, color)

    def line(self, x1, y1, x2, y2, color, t=2):
        steps = max(abs(x2 - x1), abs(y2 - y1), 1)
        for i in range(steps + 1):
            x = x1 + (x2 - x1) * i // steps
            y = y1 + (y2 - y1) * i // steps
            self.rect(x - t // 2, y - t // 2, t, t, color)


def png_bytes(cv):
    raw = bytearray()
    stride = cv.w * 3
    for y in range(cv.h):
        raw.append(0)
        raw += cv.px[y * stride:(y + 1) * stride]

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        out += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))


GLYPHS = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11100", "10010", "10001", "10001", "10001", "10010", "11100"),
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
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    "X": ("10001", "01010", "00100", "00100", "00100", "01010", "10001"),
    "Y": ("10001", "01010", "00100", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01111", "00000", "00000", "00000"),
    "+": ("00000", "00100", "00100", "01111", "00100", "00100", "00000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
}


def text_width(s, scale):
    return len(s) * 6 * scale - scale


def draw_text(cv, x, y, s, scale, color, bold=False, serif=False):
    off = max(1, scale // 3) if bold else 0
    cx = x
    for ch in s.upper():
        g = GLYPHS.get(ch, GLYPHS[" "])
        for r in range(7):
            row = g[r]
            for c in range(5):
                if row[c] == "1":
                    cv.rect(cx + c * scale, y + r * scale, scale, scale, color)
                    if bold:
                        cv.rect(cx + c * scale + off, y + r * scale,
                                scale, scale, color)
        if serif:
            # serif caps: widen only the outer ends of top/bottom stems
            for r in (0, 6):
                for c in range(5):
                    if g[r][c] == "1":
                        if c == 0 or g[r][c - 1] == "0":
                            cv.rect(cx + c * scale - scale, y + r * scale,
                                    scale, scale, color)
                        if c == 4 or g[r][c + 1] == "0":
                            cv.rect(cx + c * scale + scale, y + r * scale,
                                    scale, scale, color)
        cx += 6 * scale
    return cx - scale - x


def draw_centered(cv, cx, y, s, scale, color, bold=False, serif=False):
    w = text_width(s, scale)
    if bold:
        w += scale
    return draw_text(cv, cx - w // 2, y, s, scale, color, bold, serif)


def wrap(s, maxchars):
    lines = []
    cur = ""
    for word in s.split(" "):
        if not cur:
            cur = word
        elif len(cur) + 1 + len(word) <= maxchars:
            cur = cur + " " + word
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def kicker(cv, x, y, w, left, label):
    cv.rect(x, y, w, 18, DARKRED)
    draw_text(cv, x + 7, y + 2, left, 2, WHITE, bold=True)
    lw = text_width(label, 2)
    draw_text(cv, x + w - lw - 7, y + 2, label, 2, WHITE, bold=True)


def scene_port(cv, x, y, w, h):
    cv.rect(x, y, w, h, SKY)
    cv.circle(x + w - 52, y + 20, 11, YELLOW)
    # two dock cranes
    for gx in (x + 50, x + 196):
        cv.rect(gx, y + 16, 7, h - 40, NAVY)
        cv.rect(gx, y + 16, 84, 7, NAVY)
        cv.line(gx + 78, y + 23, gx + 78, y + 42, NAVY, 3)
        cv.rect(gx + 66, y + 42, 24, 15, ORANGE)
        cv.rect(gx - 18, y + 23, 7, 16, NAVY)
    # stacked containers on the quay
    cols = [(196, 60, 40), (30, 90, 160), (30, 140, 80), (220, 150, 30),
            (120, 60, 150), (40, 130, 170)]
    base = y + h - 26
    for i in range(6):
        cv.rect(x + 14 + i * 42, base - 18, 38, 18, cols[i])
        cv.frame(x + 14 + i * 42, base - 18, 38, 18, INK, 1)
    for i in range(4):
        cv.rect(x + 35 + i * 42, base - 36, 38, 18, cols[(i + 2) % 6])
        cv.frame(x + 35 + i * 42, base - 36, 38, 18, INK, 1)
    # sea and a container ship
    cv.rect(x, base, w, h - (base - y), SEA)
    cv.rect(x + w - 218, base - 12, 190, 12, (40, 40, 44))
    cv.tri(x + w - 28, base - 12, x + w - 6, base - 12, x + w - 28, base,
           (40, 40, 44))
    for i in range(4):
        cv.rect(x + w - 208 + i * 42, base - 28, 38, 16, cols[(i + 1) % 6])
    cv.rect(x + w - 66, base - 40, 22, 12, WHITE)
    cv.frame(x, y, w, h, INK, 2)


def scene_cairo(cv, x, y, w, h):
    cv.rect(x, y, w, h, (238, 226, 205))
    cv.rect(x, y + h - 16, w, 16, (70, 66, 62))
    cv.rect(x, y + h - 16, w, 3, (120, 116, 110))
    # smoke
    for (sx, sy, sr) in ((150, 12, 13), (178, 8, 17), (212, 12, 12),
                         (120, 16, 9)):
        cv.circle(x + sx, y + sy, sr, (150, 146, 140))
    # flames behind the tanker
    cv.tri(x + 96, y + h - 18, x + 122, y + 8, x + 148, y + h - 18, ORANGE)
    cv.tri(x + 128, y + h - 18, x + 150, y + 16, x + 172, y + h - 18, RED)
    cv.tri(x + 108, y + h - 18, x + 124, y + 22, x + 140, y + h - 18, YELLOW)
    cv.tri(x + 232, y + h - 18, x + 246, y + 20, x + 260, y + h - 18, ORANGE)
    cv.tri(x + 240, y + h - 18, x + 250, y + 30, x + 258, y + h - 18, YELLOW)
    # tanker truck, side view
    cv.rect(x + 52, y + h - 40, 128, 22, (196, 200, 204))
    cv.frame(x + 52, y + h - 40, 128, 22, INK, 2)
    cv.rect(x + 180, y + h - 36, 30, 18, NAVY)
    cv.tri(x + 210, y + h - 36, x + 226, y + h - 18, x + 180, y + h - 18,
           NAVY)
    for wx in (78, 116, 188):
        cv.circle(x + wx, y + h - 15, 8, BLACK)
        cv.circle(x + wx, y + h - 15, 3, (170, 170, 170))
    # charred cars to the right
    for bx in (268, 356):
        cv.rect(x + bx, y + h - 30, 62, 13, (30, 28, 26))
        cv.rect(x + bx + 12, y + h - 40, 36, 11, (30, 28, 26))
        cv.circle(x + bx + 14, y + h - 16, 6, BLACK)
        cv.circle(x + bx + 48, y + h - 16, 6, BLACK)
    # flames over the tank, drawn last so the fire reads at any height
    cv.tri(x + 66, y + h - 18, x + 86, y + 4, x + 106, y + h - 18, ORANGE)
    cv.tri(x + 80, y + h - 18, x + 94, y + 12, x + 108, y + h - 18, YELLOW)
    cv.tri(x + 118, y + h - 18, x + 132, y + 8, x + 146, y + h - 18, RED)
    cv.frame(x, y, w, h, INK, 2)


def scene_space(cv, x, y, w, h):
    cv.rect(x, y, w, h, (10, 16, 44))
    # deterministic star field
    for i in range(46):
        sx = x + (i * 53 + 17) % (w - 12) + 4
        sy = y + (i * 29 + 7) % (h - 30) + 3
        cv.rect(sx, sy, 2, 2, WHITE)
    # earth horizon along the bottom of the scene
    cv.rect(x, y + h - 13, w, 13, (44, 96, 168))
    cv.rect(x, y + h - 13, w, 4, (120, 180, 230))
    cv.rect(x + 60, y + h - 8, 52, 3, (120, 180, 230))
    cv.rect(x + w - 150, y + h - 8, 52, 3, (120, 180, 230))
    # station: truss, core module, solar wings
    cx = x + w // 2
    cy = y + h // 2
    cv.rect(cx - 118, cy - 3, 236, 6, (200, 204, 210))
    cv.rect(cx - 168, cy - 13, 62, 26, (36, 84, 170))
    cv.frame(cx - 168, cy - 13, 62, 26, (140, 180, 235), 2)
    cv.rect(cx + 106, cy - 13, 62, 26, (36, 84, 170))
    cv.frame(cx + 106, cy - 13, 62, 26, (140, 180, 235), 2)
    cv.rect(cx - 34, cy - 10, 68, 20, (226, 228, 230))
    cv.frame(cx - 34, cy - 10, 68, 20, INK, 2)
    cv.rect(cx - 6, cy - 19, 12, 9, (226, 228, 230))
    # docked capsule on the left of the core
    cv.tri(cx - 62, cy - 7, cx - 62, cy + 7, cx - 36, cy, (240, 200, 90))
    cv.rect(cx - 70, cy - 7, 9, 14, (200, 160, 60))
    cv.frame(x, y, w, h, INK, 2)


BRIEFS_ROW1 = [
    ("AMERICAS", [
        ("CARTAGENA 76 FREE", "CONFIRMED", "1 GUNMAN DEAD"),
        ("IOWA: 5 TONS GONE", "CONFIRMED", "ALL LEAD AZIDE"),
        ("MACY'S PARADE OFF", "CONFIRMED", "FIRST EVER"),
        ("ABREGO IN SPAIN", "CONFIRMED", "SENT IN ERROR"),
        ("KING TIDES THREAT", "FORECAST", "STORM FLOOD WATCH"),
    ]),
    ("MIDDLE EAST", [
        ("GAZA CHIEF KILLED", "REPORTED", "HIS FAMILY TOO"),
        ("NETANYAHU: DROP 2", "CONFIRMED", "JUDGES URGE IT"),
        ("GAZA: 1,000 SITES", "FORECAST", "RAINS THREATEN"),
        ("3 MORE DIE IN GAZA", "REPORTED", "ANOTHER STRIKE"),
    ]),
    ("MARKETS, TECH & SPACE", [
        ("US GROWTH UP: 4.3%", "CONFIRMED", "CORE PCE 3.3%"),
        ("NVIDIA FALLS 3.9%", "CONFIRMED", "AT $149.30"),
        ("FCC OKAYS 1M SATS", "CONFIRMED", "STARMIND PLAN"),
        ("MORTGAGE EASES", "CONFIRMED", "NOW 7.21%"),
        ("CONFIDENCE JUMPS", "CONFIRMED", "NEAR 2-YEAR HIGH"),
    ]),
]

BRIEFS_ROW2 = [
    ("UKRAINE WAR", [
        ("112 DRONES; 7 DEAD", "REPORTED", "88 DOWNED"),
        ("5 JETS HIT AT BASE", "CLAIM", "KYIV SAYS STRIKE"),
        ("490,334 DEAD: LEAK", "REPORTED", "BBC COUNT"),
        ("SAMARA FIRES", "REPORTED", "REFINERY FIRES"),
    ]),
    ("ASIA-PACIFIC & EUROPE", [
        ("N. KOREA EXPELS 1", "REPORTED", "SWISS ENVOY"),
        ("CHEN JINING PROBED", "REPORTED", "SHANGHAI CHIEF"),
        ("INDIA GROUNDS DAS", "CONFIRMED", "PASSPORT HELD"),
        ("ANDY TAYLOR, 65", "CONFIRMED", "OF DURAN DURAN"),
    ]),
    ("AFRICA", [
        ("NIGERIA: 30 KILLED", "REPORTED", "VILLAGES BURNED"),
        ("$227M METH LAB", "REPORTED", "5 MEXICANS HELD"),
        ("FARMGATE CASE ENDS", "CONFIRMED", "RAMAPHOSA SAFE"),
        ("TINUBU VOWS PEACE", "REPORTED", "BORDER REGIONS"),
    ]),
]

MX = 18
CW = 988
COLX = (18, 351, 684)
COLW = 322


def section_bar(cv, x, y, w, name):
    cv.rect(x, y, w, 20, NAVY)
    draw_text(cv, x + 7, y + 3, name, 2, WHITE, bold=True)


def brief_block(cv, x, y, w, items):
    cy = y
    for head, label, body in items:
        draw_text(cv, x + 2, cy, head, 3, INK, bold=True)
        draw_text(cv, x + 2, cy + 25, label, 2,
                  LABEL_COLORS[label], bold=True)
        bx = x + 14 + text_width(label, 2)
        draw_text(cv, bx, cy + 25, "- " + body, 2, (62, 59, 55))
        cy += 40
    return cy


def build():
    cv = Canvas(W, H, PAPER)
    cv.frame(4, 4, W - 8, H - 8, INK, 3)

    # ---- masthead ------------------------------------------------------
    draw_centered(cv, W // 2, 12, "ALL THE DAY'S NEWS - ON ONE PAGE - "
                  "FINAL EDITION", 2, GREY)
    draw_centered(cv, W // 2, 32, "THE WEDNESDAY LEDGER", 7, INK,
                  bold=True, serif=True)
    cv.hline(MX, 88, CW, INK, 4)
    cv.hline(MX, 96, CW, INK, 1)
    draw_centered(cv, W // 2, 104, "WEDNESDAY 25 NOVEMBER 2026", 5, RED,
                  bold=True)
    draw_centered(cv, W // 2, 142, "29 STORIES - 6 REGIONS - TARIFFS "
                  "LEAD THE DAY", 2, INK, bold=True)
    draw_centered(cv, W // 2, 160, "CONFIRMED: SET FACT - REPORTED: 1 "
                  "SOURCE - CLAIM: ONE SIDE - FORECAST: A WARNING",
                  2, GREY, bold=True)
    cv.hline(MX, 178, CW, INK, 2)

    # ---- UTC timeline ---------------------------------------------------
    cv.frame(MX, 184, CW, 34, INK, 2)
    cv.rect(MX, 184, CW, 34, CREAM)
    cv.frame(MX, 184, CW, 34, INK, 2)
    draw_text(cv, MX + 10, 188, "THE DAY IN UTC: 00:18 SHENZHOU-24 "
              "LAUNCHES - 03:56 DOCKS AT TIANGONG", 2, INK, bold=True)
    draw_text(cv, MX + 10, 203, "06:30 CARTAGENA RESCUE - 18:30 CAIRO "
              "TOLL UPDATE - 22:18 CAIRO TOLL 31", 2, INK)

    # ---- lead story: tariffs -------------------------------------------
    kicker(cv, MX, 226, CW, "LEAD STORY - TRADE", "CONFIRMED")
    draw_text(cv, MX, 250, "US PROPOSES NEW TARIFFS", 4, INK, bold=True)
    draw_text(cv, MX, 282, "ON 14 TRADING PARTNERS", 4, INK, bold=True)
    cv.frame(724, 244, 282, 66, RED, 3)
    draw_centered(cv, 865, 248, "20%", 6, RED, bold=True)
    draw_centered(cv, 865, 292, "PROPOSED CHINA RATE", 2, INK, bold=True)
    scene_port(cv, MX, 314, 470, 70)
    body = [
        "WASHINGTON PROPOSED FRESH DUTIES AFTER AN",
        "EIGHT-MONTH PROBE INTO EXCESS FACTORY",
        "CAPACITY. CHINA FACES A PROPOSED 20%, ON",
        "TOP OF ABOUT 25% FROM TRUMP'S FIRST TERM.",
        "PUBLIC COMMENT FIRST; DUTIES MAY SLIP TO",
        "JANUARY. BEIJING REJECTS THE ACCUSATION.",
    ]
    for i, line in enumerate(body):
        draw_text(cv, 502, 312 + i * 14, line, 2, INK)
    cv.hline(MX, 402, CW, INK, 2)

    # ---- secondary leads -------------------------------------------------
    kicker(cv, 18, 410, 482, "EGYPT - CAIRO", "CONFIRMED")
    draw_text(cv, 18, 432, "CAIRO TANKER FIRE:", 3, INK, bold=True)
    draw_text(cv, 18, 456, "AT LEAST 30 KILLED", 3, RED, bold=True)
    scene_cairo(cv, 18, 482, 482, 40)
    draw_text(cv, 18, 528, "TANKER OVERTURNED AND BURNED, CHARRING", 2, INK)
    draw_text(cv, 18, 544, "24+ VEHICLES. TOLL STILL RISING.", 2, INK)

    kicker(cv, 524, 410, 482, "SPACE - CHINA", "CONFIRMED")
    draw_text(cv, 524, 432, "SHENZHOU-24 DOCKS AT", 3, INK, bold=True)
    draw_text(cv, 524, 456, "TIANGONG STATION", 3, NAVY, bold=True)
    scene_space(cv, 524, 482, 482, 40)
    draw_text(cv, 524, 528, "MUHAMMAD ZEESHAN ALI, 40, IS THE FIRST", 2, INK)
    draw_text(cv, 524, 544, "PAKISTANI IN ORBIT. CREW OF THREE.", 2, INK)
    cv.hline(MX, 562, CW, INK, 2)

    # ---- briefs grid ------------------------------------------------------
    for ci, (name, items) in enumerate(BRIEFS_ROW1):
        section_bar(cv, COLX[ci], 568, COLW, name)
        brief_block(cv, COLX[ci], 592, COLW, items)
    cv.vline(340, 568, 224, LIGHT, 2)
    cv.vline(673, 568, 224, LIGHT, 2)

    for ci, (name, items) in enumerate(BRIEFS_ROW2):
        section_bar(cv, COLX[ci], 798, COLW, name)
        brief_block(cv, COLX[ci], 822, COLW, items)
    cv.vline(340, 798, 184, LIGHT, 2)
    cv.vline(673, 798, 184, LIGHT, 2)

    # ---- date check -------------------------------------------------------
    cv.frame(MX, 990, CW, 28, RED, 2)
    draw_centered(cv, W // 2, 997, "DATE CHECK - HELD OUT: HUAWEI, SUDAN, "
                  "RAS TANURA (TUE 24 NOV); HK FIRE (2025)", 2, RED,
                  bold=True)
    return cv


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "out")
    os.makedirs(outdir, exist_ok=True)
    data = png_bytes(build())
    with open(os.path.join(outdir, "entry.png"), "wb") as f:
        f.write(data)


if __name__ == "__main__":
    main()
