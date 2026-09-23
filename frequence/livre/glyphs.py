# -*- coding: utf-8 -*-
"""House-drawn glyph library for words no emoji set has: prepositions, deixis,
quantity, frequency, comparatives, direction, days and months.

Ported from the approved prototype (rendered, printed, signed off) — the
drawings themselves are not to be redesigned here, only exposed under the
stable interface: GLYPHS, render(key, accent).

Grammar, held everywhere: a grey REFERENCE object (box, track, frame) and a
coloured SUBJECT (dot, fill, marker). Where the subject sits relative to the
reference IS the meaning.

Days and months are typographic tiles, not drawings — a drawn 7-cell week
strip was prototyped and is an illegible grey smudge at 14pt. Type survives
any size; keep it that way.

Coordinates are on a 24x24 grid. SVG's y-axis points down, so `_y` flips
every y a glyph passes in, letting the glyph bodies below read as normal
Cartesian coordinates (bigger y = higher up).

CONTRACT: the functions stored in GLYPHS return the INNER BODY only (the
markup that goes inside <svg>...</svg>) — not a complete, standalone SVG
document. `render()` is what calls `_svg()` to wrap that body into a real
<svg viewBox="0 0 24 24" ...> element. When appending new glyphs here
(Task 9's clock dials), write the drawing function to return body markup
the same way every glyph below does, and let `render()` do the wrapping —
do not call `_svg()` inside a glyph function.
"""
import math

GREY = "#9A9A96"
INK = "#29303D"


def _y(y, h=0.0):
    return 24.0 - y - h


def _box(x, y, w, h, col=GREY, fill="none", lw=1.6):
    return (f'<rect x="{x}" y="{_y(y, h)}" width="{w}" height="{h}" '
            f'fill="{fill}" stroke="{col}" stroke-width="{lw}" '
            f'vector-effect="non-scaling-stroke"/>')


def _rect(x, y, w, h, fill):
    return f'<rect x="{x}" y="{_y(y, h)}" width="{w}" height="{h}" fill="{fill}"/>'


def _rrect(x, y, w, h, r, fill):
    return f'<rect x="{x}" y="{_y(y, h)}" width="{w}" height="{h}" rx="{r}" fill="{fill}"/>'


def _dot(x, y, r, col):
    return f'<circle cx="{x}" cy="{_y(y)}" r="{r}" fill="{col}"/>'


def _ring(x, y, r, col, lw=1.6):
    return (f'<circle cx="{x}" cy="{_y(y)}" r="{r}" fill="none" stroke="{col}" '
            f'stroke-width="{lw}"/>')


def _line(x1, y1, x2, y2, col=GREY, lw=1.6, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<line x1="{x1}" y1="{_y(y1)}" x2="{x2}" y2="{_y(y2)}" stroke="{col}" '
            f'stroke-width="{lw}" stroke-linecap="round"{d}/>')


def _arrow(x1, y1, x2, y2, col, lw=1.7, head=4.0):
    a = math.atan2(_y(y2) - _y(y1), x2 - x1)
    bx, by = x2 - head * .85 * math.cos(a), _y(y2) - head * .85 * math.sin(a)
    p1 = (x2 - head * math.cos(a - .45), _y(y2) - head * math.sin(a - .45))
    p2 = (x2 - head * math.cos(a + .45), _y(y2) - head * math.sin(a + .45))
    return (f'<line x1="{x1}" y1="{_y(y1)}" x2="{bx:.2f}" y2="{by:.2f}" stroke="{col}" '
            f'stroke-width="{lw}" stroke-linecap="round"/>'
            f'<polygon points="{x2},{_y(y2)} {p1[0]:.2f},{p1[1]:.2f} '
            f'{p2[0]:.2f},{p2[1]:.2f}" fill="{col}"/>')


def _text(x, y, s, col, size=11.5, weight="700", family="Alegreya Sans"):
    return (f'<text x="{x}" y="{_y(y)}" fill="{col}" font-size="{size}" '
            f'font-weight="{weight}" font-family="{family},sans-serif" '
            f'text-anchor="middle">{s}</text>')


def _svg(body, size=24):
    return (f'<svg class="gl" viewBox="0 0 24 24" width="{size}" height="{size}" '
            f'xmlns="http://www.w3.org/2000/svg">{body}</svg>')


GLYPHS = {}


def _g(name):
    def deco(f):
        GLYPHS[name] = f
        return f
    return deco


# ---- spatial prepositions ---------------------------------------------
@_g("on_box")        # sur — dot resting on top of the box
def _(a): return _box(4, 3, 16, 9) + _dot(12, 16, 3.4, a)


@_g("under_box")     # sous — dot beneath the box
def _(a): return _box(4, 12, 16, 9) + _dot(12, 7, 3.4, a)


@_g("in_box")        # dans — dot inside the box
def _(a): return _box(4, 5, 16, 15) + _dot(12, 12.5, 3.4, a)


@_g("out_box")       # hors — dot outside the box
def _(a): return _box(3, 5, 13, 15) + _dot(20.5, 12.5, 3.2, a)


@_g("front_box")     # devant — dot overlapping the box's near edge
def _(a): return _box(6, 7, 14, 13) + _dot(7.5, 8.5, 4.9, "#fff") + _dot(7.5, 8.5, 3.6, a)


@_g("behind_box")    # derriere — dot masked by the box in front of it
def _(a): return _dot(14, 15, 5, a) + _rect(3, 4, 11.5, 16, "#fff") + _box(3, 4, 11.5, 16)


@_g("between_box")   # entre — dot between two boxes
def _(a): return _box(2, 6, 6, 12) + _box(16, 6, 6, 12) + _dot(12, 12, 3.4, a)


@_g("beside_box")    # a cote — dot beside the box
def _(a): return _box(3, 6, 10, 12) + _dot(18, 12, 3.4, a)


@_g("around_box")    # autour — dots surrounding the box
def _(a): return _box(8.5, 8.5, 7, 7) + "".join(
    _dot(x, y, 2.0, a) for x, y in ((12, 20.5), (12, 3.5), (3.5, 12), (20.5, 12)))


@_g("against_box")   # contre — dot pressed against the box's edge
def _(a): return _box(11, 5, 10, 14) + _dot(7.5, 12, 3.4, a) + _line(10.4, 5, 10.4, 19, GREY, 1.2)


@_g("toward_box")    # vers — dot moving toward a target
def _(a): return _dot(4, 12, 3.2, a) + _arrow(8.5, 12, 21, 12, a)


@_g("through_box")   # a travers — arrow passing through a narrow gap
def _(a): return _box(9, 4, 6, 16) + _arrow(2, 12, 22, 12, a)


@_g("above_gap")     # au dessus — dot above a dashed reference line
def _(a): return _box(4, 2, 16, 7) + _line(4, 11.5, 20, 11.5, GREY, 1.0, "1.6 1.6") + _dot(12, 17.5, 3.4, a)


@_g("below_gap")     # au dessous — dot below a dashed reference line
def _(a): return _box(4, 15, 16, 7) + _line(4, 12.5, 20, 12.5, GREY, 1.0, "1.6 1.6") + _dot(12, 6.5, 3.4, a)


# ---- deixis / distance ---------------------------------------------------
@_g("here")          # ici — dot at the centre of concentric rings
def _(a): return _ring(12, 12, 7.5, GREY, 1.3) + _ring(12, 12, 4.2, GREY, 1.3) + _dot(12, 12, 2.8, a)


@_g("there_mid")     # la — dot a middling distance from the reference
def _(a): return _dot(4, 12, 3.2, GREY) + _line(8, 12, 13, 12, GREY, 1.0, "1.8 1.8") + _dot(16, 12, 3.0, a)


@_g("there_far")     # la-bas — small dot far from the reference
def _(a): return _dot(3.5, 12, 3.2, GREY) + _line(7.5, 12, 17, 12, GREY, 1.0, "1.8 1.8") + _dot(20, 12, 2.0, a)


@_g("near")          # pres — two dots close together
def _(a): return _dot(8.5, 12, 3.2, GREY) + _dot(15.5, 12, 3.2, a)


@_g("far")           # loin — two dots spread far apart
def _(a): return _dot(3.5, 12, 3.2, GREY) + _line(7, 12, 17, 12, GREY, 1.0, "1.8 1.8") + _dot(20.5, 12, 3.2, a)


@_g("everywhere")    # partout — a grid of dots filling the frame
def _(a): return "".join(_dot(x, y, 1.9, a) for x in (5, 12, 19) for y in (5, 12, 19))


@_g("nowhere")       # nulle part — a crossed-out ring, the slash carries the accent
def _(a): return _ring(12, 12, 8, GREY, 1.7) + _line(6.4, 6.4, 17.6, 17.6, a, 1.7)


@_g("somewhere")     # quelque part — dot at an unspecified point in a fuzzy area
def _(a): return (f'<rect x="3" y="{_y(21, 18)}" width="18" height="18" fill="none" '
                   f'stroke="{GREY}" stroke-width="1.4" stroke-dasharray="2 2"/>'
                   + _dot(9, 15, 3.2, a))


# ---- quantity --------------------------------------------------------------
def _glass(a, level, over=False):
    s = (f'<path d="M6,{_y(21)} L8,{_y(3)} L16,{_y(3)} L18,{_y(21)}" fill="none" '
         f'stroke="{GREY}" stroke-width="1.6"/>')
    h = 3 + level * 17
    s += _rect(8.3, 3.3, 7.4, max(h - 3.3, 0), a)
    if over:
        s += _dot(7.0, 22, 1.7, a) + _dot(17.0, 22, 1.7, a)
    return s


@_g("q_enough")      # assez — glass filled to a marked line
def _(a): return _glass(a, .62) + _line(3.5, 3 + .62 * 17, 20.5, 3 + .62 * 17, INK, 1.1, "1.5 1.5")


@_g("q_too_much")    # trop — glass overflowing
def _(a): return _glass(a, 1.05, True)


@_g("q_little")      # peu — two small dots
def _(a): return _dot(9, 12, 2.6, a) + _dot(15, 12, 2.6, a)


@_g("q_lots")        # beaucoup — a cluster of dots
def _(a): return "".join(_dot(x, y, 1.9, a) for x, y in
                          ((5, 17), (11, 19), (17, 16), (4, 10), (10, 12), (16, 9), (7, 4), (14, 3), (20, 6)))


# ---- frequency -------------------------------------------------------------
def _track(a, n):
    out = ""
    for i in range(5):
        x = 2.4 + i * 4.3
        if i < n:
            out += _rect(x, 8, 3.3, 8, a)
        else:
            out += _rect(x, 8, 3.3, 8, "#E7E9EC") + _box(x, 8, 3.3, 8, GREY, "none", 0.9)
    return out


@_g("freq_always")   # toujours — full track
def _(a): return _track(a, 5)


@_g("freq_often")    # souvent — mostly-full track
def _(a): return _track(a, 4)


@_g("freq_rarely")   # rarement — mostly-empty track
def _(a): return _track(a, 1)


@_g("freq_never")    # jamais — empty track, struck through with the accent
def _(a): return _track(a, 0) + _line(1.6, 6.4, 22.4, 17.6, a, 2.0)


# ---- comparatives -----------------------------------------------------------
def _pair(a, wa, ha, wb, hb, ya=None, yb=None):
    return (_box(2, ya if ya is not None else 12 - ha / 2, wa, ha) +
            _rect(22 - wb, yb if yb is not None else 12 - hb / 2, wb, hb, a))


@_g("cmp_big")       # grand — small reference, big coloured shape
def _(a): return _pair(a, 7, 7, 13, 13)


@_g("cmp_small")     # petit — big reference, small coloured shape
def _(a): return _pair(a, 13, 13, 6, 6)


@_g("cmp_high")      # haut — short reference, tall coloured shape
def _(a): return _pair(a, 7, 8, 8, 18, 4, 4)


@_g("cmp_low")       # bas — tall reference, short coloured shape
def _(a): return _pair(a, 7, 18, 8, 6, 4, 4)


@_g("cmp_strong")    # fort — small reference, big coloured shape
def _(a): return _pair(a, 6, 6, 14, 14)


@_g("cmp_weak")      # faible — big reference, small coloured shape
def _(a): return _pair(a, 14, 14, 5, 5)


@_g("cmp_heavy")     # lourd — coloured block pressing down under a line
def _(a): return _rect(5, 9, 14, 9, a) + _line(2, 6.5, 22, 6.5, GREY, 2.0) + _arrow(12, 8.2, 12, 2.6, a, 1.5, 3.4)


@_g("cmp_light")     # leger — coloured block floating up above a line
def _(a): return _box(5, 12, 14, 8, a) + _line(2, 6.5, 22, 6.5, GREY, 2.0) + _arrow(12, 9.4, 12, 21.4, a, 1.5, 3.4)


# ---- direction ---------------------------------------------------------
@_g("dir_up")        # en haut — arrow rising from a grey origin
def _(a): return _dot(12, 4, 1.6, GREY) + _arrow(12, 4, 12, 20, a)


@_g("dir_down")      # en bas — arrow falling from a grey origin
def _(a): return _dot(12, 20, 1.6, GREY) + _arrow(12, 20, 12, 4, a)


@_g("dir_left")      # a gauche — arrow pointing left from a grey origin
def _(a): return _dot(20, 12, 1.6, GREY) + _arrow(20, 12, 4, 12, a)


@_g("dir_right")     # a droite — arrow pointing right from a grey origin
def _(a): return _dot(4, 12, 1.6, GREY) + _arrow(4, 12, 20, 12, a)


@_g("dir_straight")  # tout droit — a road narrowing to a vanishing point, arrow running along it
def _(a): return (
    f'<path d="M {3},{_y(2)} L {21},{_y(2)} L {15},{_y(21)} L {9},{_y(21)} Z" '
    f'fill="none" stroke="{GREY}" stroke-width="1.6" stroke-linejoin="round"/>'
    + _arrow(12, 3, 12, 19, a, 2.0, 4.2)
)


@_g("dir_back")      # en arriere — path hooking back from a grey origin
def _(a): return _dot(19, 19, 1.6, GREY) + _line(19, 19, 19, 9, a, 1.9) + _arrow(19, 9, 6, 9, a, 1.9)


# ---- typographic tiles: days & months --------------------------------------
def _tile(a, s):
    return _rrect(2, 4.5, 20, 15, 3.4, a) + _text(12, 8.4, s, "#fff")


def _tf(s):
    return lambda a: _tile(a, s)


for _i, _ab in enumerate(("Lu", "Ma", "Me", "Je", "Ve", "Sa", "Di"), 1):
    GLYPHS[f"day_{_i}"] = _tf(_ab)

for _i in range(1, 13):
    GLYPHS[f"month_{_i}"] = _tf(str(_i))


# ---- clock dials --------------------------------------------------------
def _dial(hour, minute, accent, mark=None):
    """A clock face at a given time. The dial IS the meaning — this is the one
    glyph in the book that is unambiguous in every language at every age.

    A bare 12-hour analogue face cannot encode AM/PM by hand position alone —
    that is why `midi` and `minuit` used to draw the same picture. `mark`
    adds a structural, non-linework indicator for the handful of times the
    WORD itself disambiguates:
      - "day"   — midi, quatorze heures: a bold accent ring around the face.
      - "night" — minuit: the face fills solid dark, like a night sky.
      - "sharp" — pile: a bold accent-filled hub at the centre pivot, showing
        the hands landing exactly on the mark. Without this, `pile` (an
        arbitrary example dial) is byte-identical to whatever plain hour the
        card also shows at the same o'clock. A highlighted tick was tried
        first and rejected: at 26px it fuses against the hand tip into one
        indistinct patch, whereas a hub at the centre cannot be confused with
        either hand.
      - None    — everything else, including deux heures. `deux heures`
        genuinely is ambiguous between 2h and 14h in French, so it stays a
        plain unmarked face on purpose; the bare "2" next to the marked "14"
        is what teaches why the 24h form exists.
    Every marker survives 26px because it is a solid shape, not fine linework.
    """
    night = mark == "night"
    tick_col = "#fff" if night else GREY
    face_fill = INK if night else "none"

    def hand(angle_deg, length, width, dot=False):
        a = math.radians(angle_deg - 90)
        x = 12 + length * math.cos(a)
        y = 12 + length * math.sin(a)
        out = ""
        if night:
            # a white keyline under the hand so it reads on any accent hue
            # against the dark face, whatever colour this card uses.
            out += (f'<line x1="12" y1="12" x2="{x:.2f}" y2="{y:.2f}" '
                    f'stroke="#fff" stroke-width="{width + 1.3}" '
                    f'stroke-linecap="round"/>')
        out += (f'<line x1="12" y1="12" x2="{x:.2f}" y2="{y:.2f}" '
                f'stroke="{accent}" stroke-width="{width}" '
                f'stroke-linecap="round"/>')
        if dot:
            out += f'<circle cx="{x:.2f}" cy="{y:.2f}" r="1.0" fill="{accent}"/>'
        return out

    halo = ""
    if mark == "day":
        halo = (f'<circle cx="12" cy="12" r="10.6" fill="none" '
                f'stroke="{accent}" stroke-width="1.6"/>')

    face = (f'<circle cx="12" cy="12" r="9.5" fill="{face_fill}" '
            f'stroke="{GREY}" stroke-width="1.4"/>')
    ticks = "".join(
        f'<circle cx="{12 + 8 * math.cos(math.radians(t * 30 - 90)):.2f}" '
        f'cy="{12 + 8 * math.sin(math.radians(t * 30 - 90)):.2f}" '
        f'r="1.1" fill="{tick_col}"/>' for t in range(12))
    hub = f'<circle cx="12" cy="12" r="2.4" fill="{accent}"/>' if mark == "sharp" else ""
    h_ang = (hour % 12) * 30 + minute * 0.5
    # Hour and minute hands are told apart by LENGTH and END TREATMENT, not
    # just width — a short thick blunt hand vs. a longer, thinner hand with
    # a ball tip. Width alone cannot fix a degenerate angle: see hand_sep().
    return (halo + face + ticks
            + hand(h_ang, 4.6, 2.0)
            + hand(minute * 6, 7.6, 1.4, dot=True)
            + hub)


def hand_sep(hour, minute):
    """Angle between hour and minute hands, 0-180. Below ~45 the hands read
    as one blob (coincident); above ~135 they read as one straight bar
    (opposite) — both are degenerate at 26px, however the hands are drawn."""
    h_ang = (hour % 12) * 30 + minute * 0.5
    m_ang = minute * 6
    d = abs(h_ang - m_ang) % 360
    return min(d, 360 - d)


for _h in range(1, 13):
    GLYPHS[f"clock_{_h}"] = (lambda h: lambda a: _dial(h, 0, a))(_h)
GLYPHS["clock_12"] = lambda a: _dial(12, 0, a, mark="day")     # midi
GLYPHS["clock_00"] = lambda a: _dial(12, 0, a, mark="night")   # minuit

# The hour shown for these four is arbitrary — they teach the MINUTE
# expression, not the hour — so it is picked to keep the hands well apart
# (target ~45-135 degrees; see hand_sep()). Do not "tidy" these back to a
# uniform 3 o'clock: 3:15 and 3:45 were tried and both collapse the hands
# into a single blob or bar. See test_minute_expression_dials_have_separated_hands.
MINUTE_DIALS = {
    "clock_q15": (6, 15),   # et quart        -> 97.5 deg apart
    "clock_q30": (3, 30),   # et demie        -> 75.0 deg apart
    "clock_q45": (6, 45),   # moins le quart  -> 67.5 deg apart
    "clock_m10": (1, 50),   # moins dix       -> 115.0 deg apart
}
for _key, (_hh, _mm) in MINUTE_DIALS.items():
    GLYPHS[_key] = (lambda h, m: lambda a: _dial(h, m, a))(_hh, _mm)

GLYPHS["clock_sharp"] = lambda a: _dial(3, 0, a, mark="sharp")  # pile
GLYPHS["clock_24"] = lambda a: _dial(2, 0, a, mark="day")      # quatorze heures



# ---- numerals and unit tiles -------------------------------------------
# The single case where showing the SYMBOL beats any drawing: a numeral is
# already a picture, understood before either language is. `vingt` next to a
# tile reading 20 needs no Greek and no translation — which is exactly what a
# number card was missing when every one of its 38 rows had an empty gutter.
#
# The tile is the same object as the day and month tiles above, so the book
# has one typographic tile, not three. Only the type size changes, and it
# changes by measurement rather than by taste: Alegreya Sans Bold runs about
# 0.56 em per digit, the tile's usable width is 18 units, so a string of n
# characters gets 18/(0.56n) — capped at 12.5 so a single digit does not
# outgrow the tile it sits in.
def _fit(s):
    return min(12.5, 18.0 / (0.56 * max(len(s), 1)))


def _numtile(a, s):
    size = _fit(s)
    # `_text` takes a y-up baseline; 0.35 em below the tile's centre line is
    # where a cap-height string sits optically centred.
    return (_rrect(2, 4.5, 20, 15, 3.4, a)
            + _text(12, 12 - 0.35 * size, s, "#fff", size))


def _nt(s):
    return lambda a: _numtile(a, s)


for _n in list(range(0, 21)) + [30, 40, 50, 60, 70, 80, 90, 100, 1000]:
    GLYPHS[f"num_{_n}"] = _nt(str(_n))

for _name, _s in (("num_half", "½"), ("num_quarter", "¼"),
                  ("num_third", "⅓"),
                  ("qty_kg", "1kg"), ("qty_halfkg", "½kg"),
                  ("qty_100g", "100g"), ("qty_litre", "1L"),
                  ("qty_min", "1min"), ("qty_sec", "1s"),
                  ("money_franc", "CHF"), ("money_centime", "ct."),
                  ("deg_minus5", "−5°")):
    GLYPHS[_name] = _nt(_s)


# ---- typographic marks -------------------------------------------------
# A spelling card names the marks themselves, so the mark IS the icon. Drawn
# on the same tile as the numerals for the same reason: type survives 26px
# where linework does not.
for _name, _s in (("typ_acute", "é"), ("typ_grave", "è"),
                  ("typ_circ", "ê"), ("typ_trema", "ë"),
                  ("typ_cedilla", "ç"), ("typ_apos", "’"),
                  ("typ_at", "@"), ("typ_dot", "."), ("typ_slash", "/"),
                  ("typ_upper", "A"), ("typ_lower", "a"),
                  ("typ_double", "LL"), ("typ_space", "␣")):
    GLYPHS[_name] = _nt(_s)


# ---- colour swatches ---------------------------------------------------
# The ONE glyph family that ignores the card accent: on a colour card the
# colour is the meaning, so painting `rouge` in the card's blue would be a
# lie. Every swatch keeps a grey keyline, which is what lets `blanc`, `beige`
# and `argenté` exist at all on white paper.
_SWATCH = {
    "col_rouge": "#D5352B", "col_bleu": "#2166B0", "col_vert": "#3E8E41",
    "col_jaune": "#F2C230", "col_noir": "#23262B", "col_blanc": "#FFFFFF",
    "col_gris": "#9A9A96", "col_orange": "#E8802B", "col_rose": "#E68AAE",
    "col_violet": "#7D4C9E", "col_marron": "#8A5A34", "col_beige": "#E6D8BE",
    "col_dore": "#C9A227", "col_argente": "#BFC3C7",
}


def _sw(col):
    return lambda a: (_rrect(3, 5.5, 18, 13, 3.0, col)
                      + f'<rect x="3" y="{_y(5.5, 13)}" width="18" height="13" '
                        f'rx="3.0" fill="none" stroke="{GREY}" stroke-width="1.2"/>')


for _name, _col in _SWATCH.items():
    GLYPHS[_name] = _sw(_col)


# ---- the body figure ---------------------------------------------------
# Joints have no emoji in any set — OpenMoji, Twemoji, Apple, Fluent and MDI
# all stop at hand and foot — which left the body card 20 empty gutters. The
# house grammar already answers it: a grey REFERENCE (the whole figure) and a
# coloured SUBJECT (where on it). The figure is deliberately the same drawing
# on every row, so the eye compares dot positions rather than re-reading a
# new picture each time.
_FIG_PARTS = {          # y-up landmark for the accent dot
    "head": (12, 20.0), "neck": (12, 17.3), "shoulder": (16.1, 16.2),
    "arm": (17.3, 14.3), "elbow": (18.6, 12.4), "wrist": (19.1, 9.0),
    "hand": (19.3, 7.6), "chest": (12, 14.6), "back": (12, 14.6),
    "belly": (12, 11.6), "hip": (14.7, 9.5), "thigh": (15.0, 7.4),
    "knee": (15.1, 5.4), "leg": (15.0, 4.0), "ankle": (15.3, 2.2),
    "foot": (16.4, 1.3), "toe": (17.6, 1.2),
}


def _figure(skin=None):
    """The grey standing figure every body row shares."""
    col = skin or GREY
    j = 'stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" fill="none"'

    def path(d):
        return f'<path d="{d}" stroke="{col}" {j}/>'

    return (
        f'<circle cx="12" cy="{_y(20)}" r="2.7" '
        f'fill="{col if skin else "none"}" stroke="{col}" stroke-width="1.7"/>'
        + path(f'M12,{_y(17.3)} L12,{_y(9.5)}')
        + path(f'M7.9,{_y(16.2)} L16.1,{_y(16.2)}')
        + path(f'M7.9,{_y(16.2)} L5.4,{_y(12.4)} L4.9,{_y(9.0)}')
        + path(f'M16.1,{_y(16.2)} L18.6,{_y(12.4)} L19.1,{_y(9.0)}')
        + path(f'M9.3,{_y(9.5)} L14.7,{_y(9.5)}')
        + path(f'M9.3,{_y(9.5)} L8.9,{_y(5.4)} L8.7,{_y(1.9)} L7.3,{_y(1.9)}')
        + path(f'M14.7,{_y(9.5)} L15.1,{_y(5.4)} L15.3,{_y(1.9)} L16.7,{_y(1.9)}')
    )


def _bodyglyph(part):
    def f(a):
        if part == "skin":
            return _figure(skin=a)
        if part == "waist":
            return _figure() + _line(9.0, 10.6, 15.0, 10.6, a, 2.4)
        if part == "back":
            return _figure() + _line(12, 16.0, 12, 10.2, a, 2.6)
        x, y = _FIG_PARTS[part]
        return _figure() + _dot(x, y, 2.5, "#fff") + _dot(x, y, 1.9, a)
    return f


for _p in list(_FIG_PARTS) + ["skin", "waist"]:
    GLYPHS[f"body_{_p}"] = _bodyglyph(_p)


# ---- the hand -----------------------------------------------------------
# doigt, pouce and ongle all live inside one 3-unit square of the figure
# above, where three dots would be indistinguishable. They get their own
# reference object at their own scale.
def _handbase():
    palm = (f'<path d="M8.2,{_y(3.5)} L15.8,{_y(3.5)} L15.8,{_y(11)} '
            f'L8.2,{_y(11)} Z" fill="none" stroke="{GREY}" stroke-width="1.6" '
            f'stroke-linejoin="round"/>')
    fingers = "".join(
        _line(x, 11, x, top, GREY, 1.7)
        for x, top in ((9.4, 17.0), (11.4, 18.6), (13.4, 17.6), (15.2, 15.6)))
    thumb = _line(8.2, 7.0, 4.4, 10.4, GREY, 1.7)
    return palm + fingers + thumb


def _hg(fn):
    return lambda a: _handbase() + fn(a)


GLYPHS["hand_finger"] = _hg(lambda a: _line(11.4, 11, 11.4, 18.6, a, 2.2))
GLYPHS["hand_thumb"] = _hg(lambda a: _line(8.2, 7.0, 4.4, 10.4, a, 2.2))
GLYPHS["hand_nail"] = _hg(lambda a: _rrect(10.4, 16.4, 2.0, 2.4, 0.8, a))
GLYPHS["hand_palm"] = _hg(lambda a: _rrect(8.8, 4.2, 6.4, 6.0, 1.4, a))


# ---- the face -----------------------------------------------------------
def _facebase():
    oval = (f'<ellipse cx="12" cy="{_y(12)}" rx="6.7" ry="8.3" fill="none" '
            f'stroke="{GREY}" stroke-width="1.6"/>')
    eyes = _dot(9.4, 13.6, 1.0, GREY) + _dot(14.6, 13.6, 1.0, GREY)
    nose = _line(12, 12.6, 12, 10.4, GREY, 1.3)
    mouth = _line(9.8, 8.2, 14.2, 8.2, GREY, 1.5)
    return oval + eyes + nose + mouth


def _fg(fn):
    return lambda a: _facebase() + fn(a)


GLYPHS["face_head"] = _fg(lambda a: _ring(12, 12, 8.6, a, 1.8))
GLYPHS["face_hair"] = _fg(lambda a: (
    f'<path d="M5.6,{_y(16.4)} Q12,{_y(23.4)} 18.4,{_y(16.4)}" fill="none" '
    f'stroke="{a}" stroke-width="2.6" stroke-linecap="round"/>'))
GLYPHS["face_forehead"] = _fg(lambda a: _line(8.4, 16.8, 15.6, 16.8, a, 2.2))
GLYPHS["face_eyebrow"] = _fg(lambda a: _line(7.9, 15.6, 11.1, 15.6, a, 1.9)
                             + _line(12.9, 15.6, 16.1, 15.6, a, 1.9))
GLYPHS["face_eyelash"] = _fg(lambda a: "".join(
    _line(x, 14.5, x, 15.6, a, 1.2) for x in (8.6, 9.4, 10.2, 13.8, 14.6, 15.4)))
GLYPHS["face_cheek"] = _fg(lambda a: _dot(8.0, 10.8, 2.0, a) + _dot(16.0, 10.8, 2.0, a))
GLYPHS["face_lips"] = _fg(lambda a: _line(9.4, 8.2, 14.6, 8.2, a, 2.4))
GLYPHS["face_chin"] = _fg(lambda a: _dot(12, 4.6, 2.0, a))
GLYPHS["face_jaw"] = _fg(lambda a: (
    f'<path d="M6.1,{_y(9.4)} Q12,{_y(2.8)} 17.9,{_y(9.4)}" fill="none" '
    f'stroke="{a}" stroke-width="2.2" stroke-linecap="round"/>'))
GLYPHS["face_throat"] = _fg(lambda a: _rrect(10.2, 0.6, 3.6, 3.6, 1.2, a))
GLYPHS["face_nose"] = _fg(lambda a: _line(12, 12.8, 12, 10.2, a, 2.2))
GLYPHS["face_eye"] = _fg(lambda a: _dot(9.4, 13.6, 1.7, a) + _dot(14.6, 13.6, 1.7, a))


# ---- the calendar strip -------------------------------------------------
# Day deixis is a closed five-term set — avant-hier, hier, aujourd'hui,
# demain, après-demain — and it is a POSITION, not a thing. Five cells with
# one filled says that in a way no picture of a calendar page can.
def _strip(n, marks, accent, y=6.0, h=10.0, grow=3.2):
    """n cells in a row, the marked ones in the accent.

    Position alone does not survive 26px: `hier` and `avant-hier` differ by
    one cell of about four printed pixels. So the marked cell also stands
    TALLER than its neighbours — a silhouette difference the eye catches
    before it has counted anything. Unmarked cells are a solid mid-grey
    rather than a hairline outline, which at this size fills in to a smudge.
    """
    gap = 0.9
    w = (22.0 - gap * (n - 1)) / n
    out = ""
    for i in range(n):
        x = 1.0 + i * (w + gap)
        if i in marks:
            out += _rect(x, y, w, h + grow, accent)
        else:
            out += _rect(x, y, w, h, "#D3D7DC")
    return out


for _i, _name in enumerate(("cal_m2", "cal_m1", "cal_0", "cal_p1", "cal_p2")):
    GLYPHS[_name] = (lambda k: lambda a: _strip(5, {k}, a))(_i)

GLYPHS["cal_week"] = lambda a: _strip(7, set(range(7)), a, grow=0.0)
GLYPHS["cal_weekend"] = lambda a: _strip(7, {5, 6}, a)


def _grid(cols, rows, accent):
    """A calendar page: an accent header bar over a grey block of cells. The
    header is what says "calendar" at 26px, so it is drawn thick enough to
    read on its own; the cell count is the only thing that separates a month
    from a year, and it is a second-glance cue, not the first."""
    head = _rect(1.4, 24 - 6.4, 21.2, 4.4, accent)
    cw = (21.2 - (cols - 1) * 0.7) / cols
    ch = (24 - 7.4 - 2.0 - (rows - 1) * 0.7) / rows
    cells = "".join(
        _rect(1.4 + c * (cw + 0.7), 2.0 + r * (ch + 0.7), cw, ch, "#CBCFD5")
        for r in range(rows) for c in range(cols))
    return cells + head


GLYPHS["cal_month"] = lambda a: _grid(7, 4, a)
GLYPHS["cal_year"] = lambda a: _grid(4, 3, a)


# ---- sequence, and the rest of the closed comparisons --------------------
for _i, _name in enumerate(("seq_1", "seq_2", "seq_3", "seq_4")):
    GLYPHS[_name] = (lambda k: lambda a: _strip(4, {k}, a))(_i)

GLYPHS["freq_sometimes"] = lambda a: _track(a, 2)
GLYPHS["q_full"] = lambda a: _glass(a, 1.0)
GLYPHS["q_empty"] = lambda a: _glass(a, 0.0)
GLYPHS["q_almost"] = lambda a: (_glass(a, 0.88)
                                + _line(3.5, 20, 20.5, 20, INK, 1.1, "1.5 1.5"))


# meilleur / pire are a step up and a step down from the grey reference. The
# first drawing put a 2-unit arrow above the blocks; at 26px it printed as a
# speck of dirt. Three bottom-aligned bars carry the direction on their own.
def _steps(a, hs):
    return "".join(
        (_rect if i else _box)(2 + i * 7.0, 3.5, 6.0, h, a) if i
        else _box(2, 3.5, 6.0, h, GREY, "none", 1.5)
        for i, h in enumerate(hs))


@_g("cmp_better")    # meilleur — each step taller than the grey reference
def _(a): return _steps(a, (7.5, 12.0, 17.0))


@_g("cmp_worse")     # pire — each step shorter than the grey reference
def _(a): return _steps(a, (17.0, 11.0, 5.5))


@_g("len_long")      # long — a bar running the full width of its grey rule
def _(a): return _line(2, 16.5, 22, 16.5, GREY, 1.1) + _rect(2, 8, 20, 5, a)


@_g("len_short")     # court — the same rule, a bar covering a quarter of it
def _(a): return _line(2, 16.5, 22, 16.5, GREY, 1.1) + _rect(2, 8, 5.5, 5, a)


# ---- duration, as a swept sector ----------------------------------------
# An hour card needs `une demi-heure` and `un quart d'heure`, which are spans,
# not instants — the dials above read as times of day and cannot say them. A
# swept sector on the same face keeps the family and states the span.
def _sector(minutes, accent):
    ang = math.radians(minutes * 6 - 90)
    x, y = 12 + 9.5 * math.cos(ang), 12 + 9.5 * math.sin(ang)
    large = 1 if minutes > 30 else 0
    wedge = (f'<path d="M12,12 L12,2.5 A9.5,9.5 0 {large},1 {x:.2f},{y:.2f} Z" '
             f'fill="{accent}"/>') if minutes else ""
    face = (f'<circle cx="12" cy="12" r="9.5" fill="none" stroke="{GREY}" '
            f'stroke-width="1.4"/>')
    return wedge + face + f'<circle cx="12" cy="12" r="1.5" fill="{GREY}"/>'


for _name, _m in (("dur_30", 30), ("dur_15", 15)):
    GLYPHS[_name] = (lambda m: lambda a: _sector(m, a))(_m)

def render(key, accent):
    fn = GLYPHS.get(key)
    return _svg(fn(accent)) if fn else None


if __name__ == "__main__":
    print("glyphs:", len(GLYPHS))
