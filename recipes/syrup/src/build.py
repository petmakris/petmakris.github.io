import os
import sys

import qrcode
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, PageBreak, Image, Flowable)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, 'fonts')
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'siropi-sokolatas-pralina-GR.pdf')

pdfmetrics.registerFont(TTFont('Roboto', os.path.join(FONTS, 'Roboto-Regular.ttf')))
pdfmetrics.registerFont(TTFont('Roboto-Md', os.path.join(FONTS, 'Roboto-Medium.ttf')))
pdfmetrics.registerFont(TTFont('Roboto-Bd', os.path.join(FONTS, 'Roboto-Bold.ttf')))
pdfmetrics.registerFont(TTFont('Roboto-It', os.path.join(FONTS, 'Roboto-RegularItalic.ttf')))
pdfmetrics.registerFontFamily('Roboto', normal='Roboto', bold='Roboto-Bd', italic='Roboto-It')

R, RM, RB = 'Roboto', 'Roboto-Md', 'Roboto-Bd'

PRIMARY = colors.HexColor("#1565C0")
PRIM_DK = colors.HexColor("#0D47A1")
PRIM_LT = colors.HexColor("#E3F2FD")
ON_SURF = colors.HexColor("#111111")
SECOND = colors.HexColor("#4A4A4A")
FRENCH = colors.HexColor("#00695C")   # Teal 800 — reserved for French shelf words
DIVIDER = colors.HexColor("#CFD8DC")
SURF_V = colors.HexColor("#F5F5F5")
WARN_BG = colors.HexColor("#FFF8E1")
WARN_FG = colors.HexColor("#B26500")
WARN_BD = colors.HexColor("#F57C00")
ERR_FG = colors.HexColor("#C62828")
GREEN = colors.HexColor("#2E7D32")
WHITE = colors.white

CONTENT_W = 182 * mm


def ps(name, **kw):
    return ParagraphStyle(name, **kw)


S = {
    'h1': ps('h1', fontName=RB, fontSize=19, leading=22, textColor=WHITE),
    'h1sub': ps('h1sub', fontName=R, fontSize=9.2, leading=12, textColor=colors.HexColor("#D6E4F7")),
    'over': ps('over', fontName=RB, fontSize=8, leading=10, textColor=PRIMARY),
    'h2': ps('h2', fontName=RB, fontSize=12.5, leading=15, textColor=ON_SURF),
    'h3': ps('h3', fontName=RB, fontSize=8.6, leading=11, textColor=PRIMARY),
    'body': ps('body', fontName=R, fontSize=8.6, leading=11.4, textColor=ON_SURF),
    'bodyS': ps('bodyS', fontName=R, fontSize=7.7, leading=9.9, textColor=SECOND),
    'lbl': ps('lbl', fontName=RM, fontSize=6.5, leading=8, textColor=SECOND),
    'val': ps('val', fontName=RB, fontSize=9.5, leading=11.5, textColor=ON_SURF),
    'stept': ps('stept', fontName=RB, fontSize=9.2, leading=11.5, textColor=ON_SURF),
    'time': ps('time', fontName=RM, fontSize=7.4, leading=9, textColor=PRIMARY),
    'th': ps('th', fontName=RB, fontSize=7, leading=9, textColor=WHITE),
    'item': ps('item', fontName=RM, fontSize=8.8, leading=11, textColor=ON_SURF),
    'sub': ps('sub', fontName=R, fontSize=7.4, leading=9.5, textColor=SECOND),
    'qrcap': ps('qrcap', fontName=RM, fontSize=5.4, leading=7, textColor=PRIMARY, alignment=1),
}


def fr(t):
    """French shelf-word, colour-coded so it stands out in the store."""
    return f"<font color='#00695C'><b>{t}</b></font>"


class Badge(Flowable):
    def __init__(self, n, d=6.4 * mm):
        Flowable.__init__(self)
        self.n, self.d = str(n), d
        self.width = self.height = d

    def draw(self):
        c = self.canv
        r = self.d / 2.0
        c.setFillColor(PRIMARY)
        c.circle(r, r, r, stroke=0, fill=1)
        c.setFillColor(WHITE)
        c.setFont(RB, 9)
        c.drawCentredString(r, r - 3.2, self.n)


class CheckBox(Flowable):
    def __init__(self, s=3.6 * mm):
        Flowable.__init__(self)
        self.s = s
        self.width = self.height = s

    def draw(self):
        c = self.canv
        c.setStrokeColor(colors.HexColor("#5F6368"))
        c.setLineWidth(1.0)
        c.setFillColor(WHITE)
        c.roundRect(0, 0, self.s, self.s, 0.6 * mm, stroke=1, fill=1)


def card(content, width=CONTENT_W, bg=WHITE, border=DIVIDER, pad=9, radius=8, accent=None):
    t = Table([[content]], colWidths=[width])
    style = [
        ('BACKGROUND', (0, 0), (-1, -1), bg),
        ('BOX', (0, 0), (-1, -1), 0.7, border),
        ('ROUNDEDCORNERS', [radius, radius, radius, radius]),
        ('LEFTPADDING', (0, 0), (-1, -1), pad + (4 if accent else 0)),
        ('RIGHTPADDING', (0, 0), (-1, -1), pad),
        ('TOPPADDING', (0, 0), (-1, -1), pad),
        ('BOTTOMPADDING', (0, 0), (-1, -1), pad),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]
    if accent:
        style.append(('LINEBEFORE', (0, 0), (0, -1), 3.2, accent))
    t.setStyle(TableStyle(style))
    return t


def chip(label, value, w):
    inner = Table([[Paragraph(label.upper(), S['lbl'])], [Paragraph(value, S['val'])]],
                  colWidths=[w - 12])
    inner.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (0, 0), 0), ('BOTTOMPADDING', (0, 0), (0, 0), 1),
        ('TOPPADDING', (0, 1), (0, 1), 0), ('BOTTOMPADDING', (0, 1), (0, 1), 0),
    ]))
    t = Table([[inner]], colWidths=[w])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), PRIM_LT),
        ('BOX', (0, 0), (-1, -1), 0.6, colors.HexColor("#BBDEFB")),
        ('ROUNDEDCORNERS', [6, 6, 6, 6]),
        ('LEFTPADDING', (0, 0), (-1, -1), 6), ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6), ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    return t


def section_head(over, title):
    t = Table([[Paragraph(over, S['over'])], [Paragraph(title, S['h2'])]], colWidths=[CONTENT_W])
    t.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (0, 0), 0), ('BOTTOMPADDING', (0, 0), (0, 0), 1),
        ('TOPPADDING', (0, 1), (0, 1), 0), ('BOTTOMPADDING', (0, 1), (0, 1), 4),
    ]))
    return t


QRDIR = os.path.join(HERE, '.qr-cache')
os.makedirs(QRDIR, exist_ok=True)


def qr_img(url, key, size=16 * mm):
    path = os.path.join(QRDIR, f'{key}.png')
    if not os.path.exists(path):
        q = qrcode.QRCode(box_size=10, border=1,
                          error_correction=qrcode.constants.ERROR_CORRECT_M)
        q.add_data(url)
        q.make(fit=True)
        q.make_image(fill_color="#111111", back_color="white").save(path)
    return Image(path, width=size, height=size)


story = []

# =========================== ΣΕΛΙΔΑ 1 ===========================
appbar = Table([[
    [Paragraph("Σιρόπι Σοκολάτας με Πραλίνα Φουντουκιού", S['h1']),
     Paragraph("Τόπινγκ σχεδόν μηδενικών θερμίδων για γιαούρτι 2% &nbsp;&middot;&nbsp; "
               "Στα παρενθετικά, τα γαλλικά ονόματα για το σούπερ μάρκετ", S['h1sub'])]
]], colWidths=[CONTENT_W])
appbar.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, -1), PRIMARY),
    ('ROUNDEDCORNERS', [8, 8, 8, 8]),
    ('LEFTPADDING', (0, 0), (-1, -1), 14), ('RIGHTPADDING', (0, 0), (-1, -1), 14),
    ('TOPPADDING', (0, 0), (-1, -1), 11), ('BOTTOMPADDING', (0, 0), (-1, -1), 11),
]))
story.append(appbar)
story.append(Spacer(1, 9))

cw = (CONTENT_W - 4 * 5) / 5.0
chips = Table([[chip("Ποσότητα", "250 ml", cw), '', chip("Μερίδες", "8 &times; 2 κ.σ.", cw), '',
                chip("Ανά μερίδα", "33 kcal", cw), '', chip("Χρόνος", "25 λεπτά", cw), '',
                chip("Διατηρείται", "10 ημέρες", cw)]],
              colWidths=[cw, 5, cw, 5, cw, 5, cw, 5, cw])
chips.setStyle(TableStyle([('LEFTPADDING', (0, 0), (-1, -1), 0),
                           ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                           ('TOPPADDING', (0, 0), (-1, -1), 0),
                           ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                           ('VALIGN', (0, 0), (-1, -1), 'TOP')]))
story.append(chips)
story.append(Spacer(1, 8))

story.append(section_head("ΒΗΜΑ 1", "Υλικά"))


def ing_rows(rows, w):
    data = [[Paragraph(f"<b>{a}</b>", S['body']), Paragraph(b, S['body'])] for a, b in rows]
    t = Table(data, colWidths=[w * 0.28, w * 0.72])
    t.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 2),
        ('TOPPADDING', (0, 0), (-1, -1), 1.8), ('BOTTOMPADDING', (0, 0), (-1, -1), 1.8),
        ('LINEBELOW', (0, 0), (-1, -2), 0.4, colors.HexColor("#ECEFF1")),
    ]))
    return t


CW_HALF = (CONTENT_W - 6) / 2.0
inner_w = CW_HALF - 22

praline = [
    ("25 g", f"φουντούκια ωμά, ολόκληρα<br/>({fr('noisettes entières')})"),
    ("5 g", f"λευκή ζάχαρη ({fr('sucre blanc')})<br/><font color='#2E7D32' size='7.3'>20 kcal συνολικά &middot; δεν είναι στη λίστα ψωνιών</font>"),
    ("1 πρέζα", f"ψιλό θαλασσινό αλάτι<br/>({fr('sel de mer fin')})"),
]

syrup = [
    ("240 ml", f"γάλα αμυγδάλου χωρίς ζάχαρη<br/>({fr('boisson d’amande sans sucre')})"),
    ("20 g", f"κακάο σκόνη, αλκαλιωμένο<br/>({fr('cacao en poudre')})"),
    ("25 g", f"ερυθριτόλη ({fr('érythritol')})"),
    ("10 στγ.", f"Assugrin υγρό ({fr('Assugrin liquide')})"),
    ("&#189; κ.γ.", f"στιγμιαίος εσπρέσο<br/>({fr('café soluble espresso')})"),
    ("&#188; κ.γ.", f"ψιλό θαλασσινό αλάτι ({fr('sel fin')})"),
    ("&#188; κ.γ.", f"εκχύλισμα βανίλιας<br/>({fr('extrait de vanille')})"),
    ("&#8539; κ.γ.", f"πιπέρι καγιέν ({fr('poivre de Cayenne')})"),
    ("&#188; κ.γ.", f"ξανθάνη ({fr('gomme de xanthane')})"),
    ("1 κ.γ.", f"λάδι φουντουκιού ({fr('huile de noisette')})<br/><font size='7.3'>προαιρετικό</font>"),
]

c1 = card([Paragraph("ΓΙΑ ΤΗΝ ΠΡΑΛΙΝΑ", S['h3']), Spacer(1, 4), ing_rows(praline, inner_w)],
          width=CW_HALF, pad=11)
c2 = card([Paragraph("ΓΙΑ ΤΟ ΣΙΡΟΠΙ", S['h3']), Spacer(1, 4), ing_rows(syrup, inner_w)],
          width=CW_HALF, pad=11)

warn = [
    Paragraph("ΠΡΟΣΟΧΗ", ps('w', fontName=RB, fontSize=8, leading=10, textColor=WARN_FG)),
    Spacer(1, 4),
    Paragraph(
        "<b>Η ερυθριτόλη είναι το βασικό ρίσκο.</b> Διάλυσέ την τελείως όσο το μείγμα είναι ζεστό και κράτα την "
        "ποσότητα χαμηλά — αλλιώς θα «τρίζει» πάνω στο κρύο γιαούρτι. Άσε το Assugrin να κάνει τη γλύκα.<br/><br/>"
        "<b>Το καγιέν</b> πρέπει να δίνει ζέστη στον λαιμό, όχι κάψα. Αν το νιώθεις πικάντικο, μείωσέ το στο μισό."
        "<br/><br/>"
        "<b>Υφή:</b> αν μείνει πολύ αραιό μετά την ψύξη, πρόσθεσε άλλη μια πρέζα ξανθάνη· αν γίνει κολλώδες, αραίωσέ το με λίγο γάλα αμυγδάλου.",
        S['bodyS'])
]
warn_card = card(warn, width=CW_HALF, bg=WARN_BG, border=colors.HexColor("#FFE082"),
                 accent=WARN_BD, pad=10)

grid = Table([[[c1, Spacer(1, 6), warn_card], '', c2]], colWidths=[CW_HALF, 6, CW_HALF])
grid.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'),
                          ('LEFTPADDING', (0, 0), (-1, -1), 0),
                          ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                          ('TOPPADDING', (0, 0), (-1, -1), 0),
                          ('BOTTOMPADDING', (0, 0), (-1, -1), 0)]))
story.append(grid)
story.append(Spacer(1, 8))

story.append(section_head("ΒΗΜΑ 2", "Εκτέλεση"))

steps = [
    ("Καβούρδισμα φουντουκιών", "7 λεπτά",
     "Σε στεγνό τηγάνι, μέτρια φωτιά, ανακινώντας συχνά, μέχρι να μυρίσουν και να ροδίσουν ως μέσα. "
     "Το ακαβούρδιστο φουντούκι δεν έχει γεύση — εδώ φτιάχνεται το μεγαλύτερο μέρος του αρώματος."),
    ("Καραμέλωμα", "2–3 λεπτά",
     "Ρίξε τη ζάχαρη και μια πρέζα αλάτι κατευθείαν στο καυτό τηγάνι με τα φουντούκια. Ανακάτευε συνεχώς "
     "μέχρι να λιώσει, να πάρει κεχριμπαρένιο χρώμα και να τα καλύψει. Κατέβασέ το μόλις μυρίσει καραμέλα."),
    ("Κρύωμα και άλεσμα", "15 λεπτά",
     "Άπλωσέ το λεπτό σε λαδόκολλα και άφησέ το να στερεοποιηθεί εντελώς. Σπάσε το και χτύπησέ το σε μικρό "
     "μύλο μέχρι να γίνει από άμμος μια ρευστή πάστα."),
    ("Άνοιγμα του κακάο", "3 λεπτά",
     "Ζέστανε το γάλα αμυγδάλου μέχρι να αχνίζει, όχι να βράσει. Χτύπησε μέσα κακάο, εσπρέσο, αλάτι και "
     "καγιέν. Συνέχισε σε χαμηλή φωτιά — το κακάο θέλει θερμότητα και χρόνο για ν’ ανοίξει."),
    ("Γλύκανση", "2 λεπτά",
     "Εκτός φωτιάς, ανακάτεψε ερυθριτόλη, Assugrin και την πάστα πραλίνας. Ανακάτευε μέχρι η ερυθριτόλη να "
     "<b>διαλυθεί εντελώς</b>. Δοκίμασε και άφησέ το λίγο πιο γλυκό απ’ όσο θέλεις — κρύο θα γευτεί πιο πικρό."),
    ("Πύκνωση", "30 δευτ.",
     "Στο μπλέντερ: βάλ’ το πρώτα να δουλεύει και μετά ρίξε τη ξανθάνη σιγά-σιγά από το καπάκι. Ποτέ σε ακίνητο "
     "υγρό. Θα φαίνεται πολύ αραιό — έτσι πρέπει."),
    ("Ολοκλήρωση και ψύξη", "45 λεπτά",
     "Χτύπησε μέσα τη βανίλια και το λάδι φουντουκιού. Σε βάζο ή μπουκάλι και στο ψυγείο. Θα πήξει αρκετά "
     "καθώς ενυδατώνεται η ξανθάνη."),
]

rows = []
for i, (t, tm, d) in enumerate(steps, 1):
    head = Table([[Paragraph(t, S['stept']), Paragraph(tm, S['time'])]],
                 colWidths=[CONTENT_W - 40 - 62, 62])
    head.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0), ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'), ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
    ]))
    rows.append([Badge(i), [head, Paragraph(d, S['bodyS'])]])

st = Table(rows, colWidths=[10 * mm, CONTENT_W - 10 * mm])
st.setStyle(TableStyle([
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (1, 0), (1, -1), 4),
    ('TOPPADDING', (0, 0), (-1, -1), 2.6), ('BOTTOMPADDING', (0, 0), (-1, -1), 2.6),
    ('LINEBELOW', (0, 0), (-1, -2), 0.4, colors.HexColor("#ECEFF1")),
]))
story.append(st)
story.append(Spacer(1, 7))

story.append(card(
    Paragraph("<b>ΕΞΟΠΛΙΣΜΟΣ</b> &nbsp; κατσαρολάκι &middot; μπλέντερ ή ραβδομπλέντερ &middot; μύλος μπαχαρικών "
              "&middot; βάζο ή μπουκάλι με στόμιο", S['bodyS']),
    bg=SURF_V, border=DIVIDER, pad=8))

# =========================== ΣΕΛΙΔΑ 2 ===========================
story.append(PageBreak())

bar2 = Table([[
    [Paragraph("Λίστα για τα Ψώνια", S['h1']),
     Paragraph("Σκάναρε τον κωδικό για να δεις το ακριβές προϊόν — φωτογραφία, τιμή και διαθεσιμότητα στο κατάστημα",
               S['h1sub'])]
]], colWidths=[CONTENT_W])
bar2.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, -1), PRIMARY),
    ('ROUNDEDCORNERS', [8, 8, 8, 8]),
    ('LEFTPADDING', (0, 0), (-1, -1), 14), ('RIGHTPADDING', (0, 0), (-1, -1), 14),
    ('TOPPADDING', (0, 0), (-1, -1), 11), ('BOTTOMPADDING', (0, 0), (-1, -1), 11),
]))
story.append(bar2)
story.append(Spacer(1, 8))

story.append(card(
    Paragraph("Το <b>Migros La Sallaz</b> (Rte de Berne 1) και το <b>Coop</b> ακριβώς απέναντι καλύπτουν όλη τη λίστα. "
              f"Τίποτα δεν χρειάζεται παραγγελία online. Με {fr('πράσινο')} είναι οι γαλλικές λέξεις που θα δεις στη "
              "συσκευασία ή στην ταμπέλα του ραφιού.", S['bodyS']),
    bg=PRIM_LT, border=colors.HexColor("#BBDEFB"), accent=PRIMARY, pad=9))
story.append(Spacer(1, 9))

story.append(section_head("ΣΚΑΝΑΡΕ ΓΙΑ ΝΑ ΔΕΙΣ ΤΗ ΣΥΣΚΕΥΑΣΙΑ", "Τα τέσσερα που μπερδεύονται εύκολα"))

QW = 16 * mm
prods = [
    ("Alnatura Bio Drink Amande, sans sucre",
     f"Migros &middot; 1 L &middot; ράφι φυτικών ροφημάτων ({fr('boissons végétales')})",
     f"Πράσινο-λευκό χάρτινο κουτί Alnatura. Πρέπει να γράφει {fr('sans sucre ajouté')}. Το απλό δίπλα του είναι ζαχαρωμένο.",
     "https://www.migros.ch/fr/product/204030800000", "almond", "MIGROS"),
    ("M-Classic Erythrit",
     f"Migros &middot; ράφι ζάχαρης ({fr('sucre &amp; édulcorants')})",
     "Αν είσαι στο Coop, πάρε το <b>Coop Erythrit 500 g</b>. Είναι το ίδιο πράγμα.",
     "https://www.migros.ch/de/product/mo/10552122", "eryth", "MIGROS"),
    ("Assugrin Liquid Sweetener, 200 ml",
     f"Coop &middot; ράφι ζάχαρης ({fr('sucre &amp; édulcorants')})",
     "Μικρό μπουκαλάκι με σταγονόμετρο — <b>όχι</b> τα χάπια ούτε η σκόνη 300 g. Δέκα σταγόνες γλυκαίνουν σαν ένα κουταλάκι ζάχαρη.",
     "https://www.coop.ch/en/food/pantry/staples/flour-sugar/sweeteners/assugrin-liquid-sweetener/p/3452258", "assu", "COOP"),
    ("Betty Bossi Xanthan Gum, 3 &times; 8 g",
     f"Coop &middot; ράφι ζαχαροπλαστικής ({fr('pâtisserie')})",
     "Τρία μικρά φακελάκια σε χάρτινο κουτάκι. Στο Migros κρύβεται στο τμήμα χωρίς γλουτένη.",
     "https://www.coop.ch/en/food/pantry/baking-ingredients/classic-baking-ingredients/baking-staples/betty-bossi-xanthan-gum-3-x-8-g/p/6879062", "xanthan", "COOP"),
]

prows = []
for name, where, note, url, key, store in prods:
    tag_col = GREEN if store == "MIGROS" else PRIMARY
    tag = Table([[Paragraph(store, ps('tag', fontName=RB, fontSize=6, leading=7.5,
                                      textColor=WHITE, alignment=1))]], colWidths=[15 * mm])
    tag.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), tag_col),
        ('ROUNDEDCORNERS', [4, 4, 4, 4]),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5), ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    body = [Paragraph(name, S['item']), Spacer(1, 1.5),
            Paragraph(where, S['sub']), Spacer(1, 3),
            Paragraph(note, S['bodyS'])]
    prows.append([CheckBox(), tag, body, [qr_img(url, key, QW), Paragraph("scan", S['qrcap'])]])

pt = Table(prows, colWidths=[8 * mm, 17 * mm, CONTENT_W - 8 * mm - 17 * mm - QW - 12 * mm, QW + 10 * mm])
pt.setStyle(TableStyle([
    ('VALIGN', (0, 0), (2, -1), 'TOP'),
    ('VALIGN', (3, 0), (3, -1), 'MIDDLE'), ('ALIGN', (3, 0), (3, -1), 'CENTER'),
    ('LEFTPADDING', (0, 0), (-1, -1), 0),
    ('RIGHTPADDING', (1, 0), (1, -1), 6), ('RIGHTPADDING', (2, 0), (2, -1), 8),
    ('TOPPADDING', (0, 0), (-1, -1), 4.5), ('BOTTOMPADDING', (0, 0), (-1, -1), 4.5),
    ('LINEBELOW', (0, 0), (-1, -2), 0.5, DIVIDER),
]))
story.append(card(pt, pad=10))
story.append(Spacer(1, 9))

story.append(section_head("ΧΩΡΙΣ ΣΚΑΝΑΡΙΣΜΑ", "Όλα τα υπόλοιπα"))

rest = [
    ("Κακάο σκόνη, χωρίς ζάχαρη", f"{fr('cacao en poudre non sucré')}", "250 g",
     f"{fr('Pâtisserie')}",
     f"Διάβασε τα συστατικά: πρέπει να γράφει {fr('carbonate de potassium')} — αυτό σημαίνει αλκαλιωμένο."),
    ("Φουντούκια ωμά, ολόκληρα", f"{fr('noisettes entières')}", "100 g",
     f"{fr('Fruits secs')}",
     "Ωμά και ολόκληρα. Όχι καβουρδισμένα, όχι σπασμένα, όχι φιλέ."),
    ("Στιγμιαίος καφές εσπρέσο", f"{fr('café soluble espresso')}", "1 βάζο",
     f"{fr('Café')}", "Οποιαδήποτε μάρκα. Η συνταγή θέλει μισό κουταλάκι."),
    ("Εκχύλισμα βανίλιας", f"{fr('extrait de vanille')}", "1 μπουκ.",
     f"{fr('Pâtisserie')}",
     f"Απόφυγε το {fr('sucre vanillé')} στο ίδιο ράφι — είναι κυρίως ζάχαρη."),
    ("Πιπέρι καγιέν", f"{fr('poivre de Cayenne')}", "1 βάζο",
     f"{fr('Épices')}", "Σε σκόνη, όχι νιφάδες τσίλι."),
    ("Ψιλό θαλασσινό αλάτι", f"{fr('sel de mer fin')}", "1",
     f"{fr('Épices')}", "Μάλλον το έχεις ήδη στο σπίτι."),
    ("Λάδι φουντουκιού", f"{fr('huile de noisette')}", "1 μπουκ.",
     f"{fr('Huiles')} (Coop)",
     "<font color='#4A4A4A'>Προαιρετικό.</font> Δίνει πλούσια γεύση για ~5 kcal τη μερίδα."),
]

data = [[Paragraph("", S['th']), Paragraph("ΥΛΙΚΟ / ΓΑΛΛΙΚΑ", S['th']), Paragraph("ΠΟΣΟ", S['th']),
         Paragraph("ΡΑΦΙ", S['th']), Paragraph("ΤΙ ΝΑ ΠΡΟΣΕΞΕΙΣ", S['th'])]]
for gr_name, fr_name, qty, aisle, look in rest:
    cell = [Paragraph(gr_name, S['item']), Paragraph(fr_name, S['sub'])]
    data.append([CheckBox(), cell, Paragraph(qty, S['bodyS']),
                 Paragraph(aisle, S['sub']), Paragraph(look, S['bodyS'])])

rt = Table(data, colWidths=[8 * mm, 48 * mm, 14 * mm, 30 * mm, 82 * mm], repeatRows=1)
rt.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), PRIM_DK),
    ('ROUNDEDCORNERS', [8, 8, 8, 8]),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ('LEFTPADDING', (0, 0), (-1, -1), 7), ('RIGHTPADDING', (0, 0), (-1, -1), 7),
    ('LEFTPADDING', (0, 0), (0, -1), 10),
    ('LINEBELOW', (0, 1), (-1, -2), 0.5, DIVIDER),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, SURF_V]),
    ('BOX', (0, 0), (-1, -1), 0.7, DIVIDER),
]))
story.append(rt)


def furniture(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(DIVIDER)
    canvas.setLineWidth(0.6)
    canvas.line(14 * mm, 14 * mm, 196 * mm, 14 * mm)
    canvas.setFont(R, 7.2)
    canvas.setFillColor(SECOND)
    canvas.drawString(14 * mm, 10 * mm, "Σιρόπι Σοκολάτας με Πραλίνα Φουντουκιού")
    lbl = "Συνταγή" if doc.page == 1 else "Λίστα Ψωνιών"
    canvas.setFont(RM, 7.2)
    canvas.setFillColor(PRIMARY)
    canvas.drawRightString(196 * mm, 10 * mm, f"{lbl}   {doc.page} / 2")
    canvas.restoreState()


doc = SimpleDocTemplate(OUT,
                        pagesize=A4,
                        leftMargin=14 * mm, rightMargin=14 * mm,
                        topMargin=14 * mm, bottomMargin=18 * mm,
                        title="Σιρόπι Σοκολάτας με Πραλίνα Φουντουκιού",
                        author="Συνταγή + λίστα ψωνιών")
doc.build(story, onFirstPage=furniture, onLaterPages=furniture)
print(f"built -> {OUT}")
