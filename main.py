#!/usr/bin/env python3
"""news-image-20261124: draw a newspaper front page summing up 24 Nov 2026.

Standard library only. Deterministic: no time, no randomness, no network.
Writes /output/entry.png (or $MAKEFUN_OUTPUT_DIR/entry.png), 1024x1024 PNG.
"""

import math
import os
import struct
import zlib

W, H = 1024, 1024

NAVY = (20, 38, 63)
GOLD = (212, 175, 55)
WHITE = (255, 255, 255)
INK = (17, 24, 39)
GREY = (100, 116, 139)
LIGHT_GREY = (237, 239, 242)
CARD_BG = (255, 255, 255)
CARD_BORDER = (203, 213, 225)

# 5x7 bitmap font, uppercase only. Each glyph is 7 rows of 5 bits,
# leftmost pixel is bit 4 (0x10), rightmost is bit 0 (0x01).
GLYPHS = {
    "A": (0x0E, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    "B": (0x1E, 0x11, 0x11, 0x1E, 0x11, 0x11, 0x1E),
    "C": (0x0E, 0x11, 0x10, 0x10, 0x10, 0x11, 0x0E),
    "D": (0x1E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x1E),
    "E": (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x1F),
    "F": (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x10),
    "G": (0x0E, 0x11, 0x10, 0x17, 0x11, 0x11, 0x0F),
    "H": (0x11, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    "I": (0x0E, 0x04, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "J": (0x07, 0x02, 0x02, 0x02, 0x02, 0x12, 0x0C),
    "K": (0x11, 0x12, 0x14, 0x18, 0x14, 0x12, 0x11),
    "L": (0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x1F),
    "M": (0x11, 0x1B, 0x15, 0x15, 0x11, 0x11, 0x11),
    "N": (0x11, 0x19, 0x15, 0x13, 0x11, 0x11, 0x11),
    "O": (0x0E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    "P": (0x1E, 0x11, 0x11, 0x1E, 0x10, 0x10, 0x10),
    "Q": (0x0E, 0x11, 0x11, 0x11, 0x15, 0x12, 0x0D),
    "R": (0x1E, 0x11, 0x11, 0x1E, 0x14, 0x12, 0x11),
    "S": (0x0F, 0x10, 0x10, 0x0E, 0x01, 0x01, 0x1E),
    "T": (0x1F, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04),
    "U": (0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    "V": (0x11, 0x11, 0x11, 0x11, 0x11, 0x0A, 0x04),
    "W": (0x11, 0x11, 0x11, 0x15, 0x15, 0x1B, 0x11),
    "X": (0x11, 0x11, 0x0A, 0x04, 0x0A, 0x11, 0x11),
    "Y": (0x11, 0x11, 0x0A, 0x04, 0x04, 0x04, 0x04),
    "Z": (0x1F, 0x01, 0x02, 0x04, 0x08, 0x10, 0x1F),
    "0": (0x0E, 0x11, 0x13, 0x15, 0x19, 0x11, 0x0E),
    "1": (0x04, 0x0C, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "2": (0x0E, 0x11, 0x01, 0x06, 0x08, 0x10, 0x1F),
    "3": (0x1F, 0x02, 0x04, 0x02, 0x01, 0x11, 0x0E),
    "4": (0x02, 0x06, 0x0A, 0x12, 0x1F, 0x02, 0x02),
    "5": (0x1F, 0x10, 0x1E, 0x01, 0x01, 0x11, 0x0E),
    "6": (0x06, 0x08, 0x10, 0x1E, 0x11, 0x11, 0x0E),
    "7": (0x1F, 0x01, 0x02, 0x04, 0x08, 0x08, 0x08),
    "8": (0x0E, 0x11, 0x11, 0x0E, 0x11, 0x11, 0x0E),
    "9": (0x0E, 0x11, 0x11, 0x0F, 0x01, 0x02, 0x0C),
    " ": (0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00),
    ".": (0x00, 0x00, 0x00, 0x00, 0x00, 0x0C, 0x0C),
    ",": (0x00, 0x00, 0x00, 0x00, 0x0C, 0x04, 0x08),
    ":": (0x00, 0x0C, 0x0C, 0x00, 0x0C, 0x0C, 0x00),
    ";": (0x00, 0x0C, 0x0C, 0x00, 0x0C, 0x04, 0x08),
    "'": (0x04, 0x04, 0x08, 0x00, 0x00, 0x00, 0x00),
    "-": (0x00, 0x00, 0x00, 0x0E, 0x00, 0x00, 0x00),
    "/": (0x01, 0x02, 0x02, 0x04, 0x08, 0x08, 0x10),
    "(": (0x02, 0x04, 0x08, 0x08, 0x08, 0x04, 0x02),
    ")": (0x08, 0x04, 0x02, 0x02, 0x02, 0x04, 0x08),
    "!": (0x04, 0x04, 0x04, 0x04, 0x04, 0x00, 0x04),
    "?": (0x0E, 0x11, 0x01, 0x06, 0x04, 0x00, 0x04),
    "&": (0x0C, 0x12, 0x14, 0x08, 0x15, 0x12, 0x0D),
    "%": (0x19, 0x1A, 0x02, 0x04, 0x08, 0x0B, 0x13),
    "+": (0x00, 0x04, 0x04, 0x1F, 0x04, 0x04, 0x00),
    "*": (0x00, 0x04, 0x15, 0x0E, 0x15, 0x04, 0x00),
    "=": (0x00, 0x00, 0x1F, 0x00, 0x1F, 0x00, 0x00),
    "_": (0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x1F),
    '"': (0x0A, 0x0A, 0x00, 0x00, 0x00, 0x00, 0x00),
    "•": (0x00, 0x04, 0x0E, 0x0E, 0x0E, 0x04, 0x00),
}


def char_width(scale):
    return 6 * scale


def text_width(text, scale):
    return len(text) * char_width(scale) - scale


def wrap_text(text, max_chars):
    """Greedy word wrap, returns a list of lines."""
    lines = []
    for para in text.split("\n"):
        words = para.split(" ")
        cur = ""
        for word in words:
            trial = word if not cur else cur + " " + word
            if len(trial) <= max_chars:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
    return lines


class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(w * h * 3)
        self.fill_rect(0, 0, w, h, bg)

    def set_pixel(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = color

    def fill_rect(self, x, y, w, h, color):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.px[i], self.px[i + 1], self.px[i + 2] = color

    def rect_outline(self, x, y, w, h, color, t=1):
        self.fill_rect(x, y, w, t, color)
        self.fill_rect(x, y + h - t, w, t, color)
        self.fill_rect(x, y, t, h, color)
        self.fill_rect(x + w - t, y, t, h, color)

    def fill_circle(self, cx, cy, r, color):
        for dy in range(-r, r + 1):
            dx = int(math.sqrt(max(0, r * r - dy * dy)))
            self.fill_rect(cx - dx, cy + dy, 2 * dx + 1, 1, color)

    def circle_outline(self, cx, cy, r, color, t=3):
        for dy in range(-r - t, r + t + 1):
            for dx in range(-r - t, r + t + 1):
                d = math.sqrt(dx * dx + dy * dy)
                if r - t <= d <= r:
                    self.set_pixel(cx + dx, cy + dy, color)

    def draw_line(self, x0, y0, x1, y1, color, t=2):
        steps = max(abs(x1 - x0), abs(y1 - y0), 1)
        for i in range(steps + 1):
            x = x0 + (x1 - x0) * i // steps
            y = y0 + (y1 - y0) * i // steps
            self.fill_rect(x - t // 2, y - t // 2, t, t, color)

    def draw_char(self, x, y, ch, scale, color):
        glyph = GLYPHS.get(ch, GLYPHS["?"])
        for row in range(7):
            bits = glyph[row]
            for col in range(5):
                if bits & (0x10 >> col):
                    self.fill_rect(x + col * scale, y + row * scale,
                                   scale, scale, color)

    def draw_text(self, x, y, text, scale, color):
        text = text.upper()
        cx = x
        for ch in text:
            self.draw_char(cx, y, ch, scale, color)
            cx += char_width(scale)
        return cx


# --- pictograms, drawn inside a circle of radius r centred at (cx, cy) ---

def pic_ship(c, cx, cy, r, color):
    c.fill_rect(cx - r + 12, cy - 6, 2 * r - 24, 10, color)          # hull
    c.fill_rect(cx - 4, cy - 26, 4, 20, color)                       # mast
    c.fill_rect(cx - 12, cy - 26, 22, 6, color)                     # sail
    c.fill_rect(cx - r + 18, cy + 8, 2 * r - 36, 3, color)          # waterline


def pic_drone(c, cx, cy, r, color):
    c.fill_rect(cx - 12, cy - 6, 24, 12, color)                     # body
    for sx, sy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        ax, ay = cx + sx * (r - 12), cy + sy * (r - 12)
        c.circle_outline(ax, ay, 9, color, 3)
        c.draw_line(cx, cy, ax, ay, color, 3)


def pic_court(c, cx, cy, r, color):
    c.draw_line(cx - r + 10, cy - 18, cx, cy - 30, color, 3)        # roof L
    c.draw_line(cx, cy - 30, cx + r - 10, cy - 18, color, 3)        # roof R
    for dx in (-24, -8, 8, 24):
        c.fill_rect(cx + dx - 3, cy - 14, 6, 34, color)             # columns
    c.fill_rect(cx - r + 10, cy + 20, 2 * r - 20, 5, color)         # base


def pic_target(c, cx, cy, r, color):
    c.circle_outline(cx, cy, r - 12, color, 4)
    c.circle_outline(cx, cy, r - 24, color, 4)
    c.fill_circle(cx, cy, 7, color)


def pic_tower(c, cx, cy, r, color):
    c.fill_rect(cx - 10, cy - r + 8, 20, 2 * r - 16, color)         # tower
    for wy in range(cy - r + 16, cy + r - 12, 12):
        c.fill_rect(cx - 5, wy, 10, 5, WHITE)                       # windows
    c.draw_line(cx, cy - r + 8, cx + 14, cy - r - 2, color, 3)      # antenna


def pic_shop(c, cx, cy, r, color):
    c.fill_rect(cx - r + 12, cy - 8, 2 * r - 24, 30, color)         # shop
    for i in range(5):
        if i % 2 == 0:
            c.fill_rect(cx - r + 12 + i * 11, cy - 18, 11, 10, color)
    c.fill_rect(cx - 8, cy + 8, 16, 14, WHITE)                      # door


PICTOGRAMS = {
    "ship": pic_ship,
    "drone": pic_drone,
    "court": pic_court,
    "target": pic_target,
    "tower": pic_tower,
    "shop": pic_shop,
}

STORIES = [
    {
        "num": "1", "region": "HORMUZ", "color": (180, 35, 24),
        "pic": "ship",
        "headline": "FOUR TANKERS HIT MINES",
        "summary": "IRAN SAYS FOUR TANKERS HIT MINES IN THE STRAIT OF "
                   "HORMUZ. ITS NAVY SAYS IT ATTACKED A CONTAINER SHIP THERE.",
        "tag": "MIDDLE EAST  •  SHIPPING",
    },
    {
        "num": "2", "region": "UKRAINE", "color": (29, 78, 216),
        "pic": "drone",
        "headline": "UKRAINE STRIKES RUSSIAN SHIPS",
        "summary": "DRONES HIT THE CARGO SHIP SPARTA II IN THE GULF OF "
                   "FINLAND. NAVAL DRONES HIT A CORVETTE OFF LIBYA, CLAIMED SUNK.",
        "tag": "EUROPE  •  WAR AT SEA",
    },
    {
        "num": "3", "region": "HUAWEI", "color": (107, 33, 168),
        "pic": "court",
        "headline": "HUAWEI GUILTY ON 10 COUNTS",
        "summary": "A US JURY CONVICTS HUAWEI OF TRADE-SECRET THEFT AND BANK "
                   "FRAUD, AND ACQUITS IT OF RACKETEERING.",
        "tag": "US-CHINA  •  TECH / COURTS",
    },
    {
        "num": "4", "region": "GAZA", "color": (146, 64, 14),
        "pic": "target",
        "headline": "ISRAEL KILLS HAMAS SECURITY CHIEF",
        "summary": "AN ISRAELI STRIKE KILLS BRIG. GEN. NAEEM ABU NAHEL IN "
                   "GAZA. SIX OTHERS ARE KILLED, OFFICIALS SAY.",
        "tag": "MIDDLE EAST  •  GAZA",
    },
    {
        "num": "5", "region": "RIYADH", "color": (180, 83, 9),
        "pic": "tower",
        "headline": "DRONE HITS PIF TOWER IN RIYADH",
        "summary": "A SUSPECTED DRONE ATTACK ON THE SAUDI FUND'S TOWER "
                   "WOUNDS AT LEAST 11. IT IS THE SECOND HIT IN A WEEK.",
        "tag": "SAUDI ARABIA  •  DRONE ATTACK",
    },
    {
        "num": "6", "region": "COLOMBIA", "color": (4, 120, 87),
        "pic": "shop",
        "headline": "25 HELD HOSTAGE IN CARTAGENA",
        "summary": "ARMED MEN SEIZE A SUPERMARKET IN CARTAGENA AND HOLD 25 "
                   "PEOPLE. FIVE OLDER WOMEN ARE RELEASED.",
        "tag": "LATIN AMERICA  •  COLOMBIA",
    },
]


def draw_card(c, x, y, w, h, story):
    color = story["color"]
    c.fill_rect(x, y, w, h, CARD_BG)
    c.rect_outline(x, y, w, h, CARD_BORDER, 2)
    c.fill_rect(x, y, w, 8, color)
    # number + region label
    c.draw_text(x + 16, y + 20, story["num"] + "  " + story["region"], 3, color)
    # headline, up to 2 lines
    head_lines = wrap_text(story["headline"], 24)
    hy = y + 52
    for line in head_lines[:2]:
        c.draw_text(x + 16, hy, line, 3, INK)
        hy += 27
    # pictogram in a circle, left of the summary
    icon_cx, icon_cy, icon_r = x + 58, y + 168, 42
    c.circle_outline(icon_cx, icon_cy, icon_r, color, 3)
    PICTOGRAMS[story["pic"]](c, icon_cx, icon_cy, icon_r, color)
    # summary, to the right of the icon
    text_x = x + 116
    max_chars = (x + w - 16 - text_x) // char_width(2)
    sum_lines = wrap_text(story["summary"], max_chars)
    sy = y + 132
    for line in sum_lines[:5]:
        c.draw_text(text_x, sy, line, 2, INK)
        sy += 18
    # tag line at the bottom
    c.draw_text(x + 16, y + h - 28, story["tag"], 2, GREY)


def build_image():
    c = Canvas(W, H, WHITE)
    # header
    c.fill_rect(0, 0, W, 152, NAVY)
    c.draw_text(28, 16, "THE WORLD IN ONE DAY", 6, WHITE)
    c.draw_text(28, 68, "TUESDAY 24 NOVEMBER 2026", 4, GOLD)
    c.draw_text(28, 112, "SIX STORIES THAT DEFINED THE DAY  •  WORLD NEWS, "
                         "24 NOVEMBER 2026", 2, WHITE)
    # six cards, 2 columns x 3 rows
    card_w, card_h = 488, 250
    xs = [16, 520]
    ys = [168, 434, 700]
    for i, story in enumerate(STORIES):
        draw_card(c, xs[i % 2], ys[i // 2], card_w, card_h, story)
    # footer
    c.fill_rect(16, 966, 992, 44, LIGHT_GREY)
    c.draw_text(28, 974, "ALSO:  MALAYSIA TO RETURN THOUSANDS OF MIGRANTS "
                         "TO MYANMAR", 2, INK)
    c.draw_text(28, 992, "TURKISH HELICOPTER CRASH KILLS FIVE  •  NATO VOWS "
                         "TO DEFEND SPACE", 2, INK)
    return c


def _chunk(chunk_type, data):
    out = struct.pack(">I", len(data)) + chunk_type + data
    out += struct.pack(">I", zlib.crc32(chunk_type + data) & 0xFFFFFFFF)
    return out


def write_png(path, canvas):
    raw = bytearray()
    stride = canvas.w * 3
    for row in range(canvas.h):
        raw.append(0)
        raw += canvas.px[row * stride:(row + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0)
    data = (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr)
            + _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + _chunk(b"IEND", b""))
    with open(path, "wb") as fh:
        fh.write(data)


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(out_dir, exist_ok=True)
    canvas = build_image()
    out_path = os.path.join(out_dir, "entry.png")
    write_png(out_path, canvas)
    print("wrote " + out_path)


if __name__ == "__main__":
    main()
