"""PDF generation for loan summary and payment schedule (Azerbaijani)."""
import calendar
import os
from datetime import date, datetime
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


_FONT_CANDIDATES = [
    ("DejaVuSans", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ("DejaVuSans-Bold", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
]

_FONT_REGULAR = "Helvetica"
_FONT_BOLD = "Helvetica-Bold"
_FONTS_REGISTERED = False


def _register_fonts():
    global _FONT_REGULAR, _FONT_BOLD, _FONTS_REGISTERED
    if _FONTS_REGISTERED:
        return
    try:
        for name, path in _FONT_CANDIDATES:
            if os.path.exists(path):
                pdfmetrics.registerFont(TTFont(name, path))
        if os.path.exists(_FONT_CANDIDATES[0][1]):
            _FONT_REGULAR = "DejaVuSans"
        if os.path.exists(_FONT_CANDIDATES[1][1]):
            _FONT_BOLD = "DejaVuSans-Bold"
    except Exception:
        pass
    _FONTS_REGISTERED = True


_AZ_MONTHS_FULL = {
    1: "Yanvar", 2: "Fevral", 3: "Mart", 4: "Aprel", 5: "May", 6: "İyun",
    7: "İyul", 8: "Avqust", 9: "Sentyabr", 10: "Oktyabr", 11: "Noyabr", 12: "Dekabr",
}


def _az_date(d):
    return f"{d.day} {_AZ_MONTHS_FULL[d.month]} {d.year}"


def _add_months(d, months):
    m = d.month - 1 + months
    y = d.year + m // 12
    m = m % 12 + 1
    day = min(d.day, calendar.monthrange(y, m)[1])
    return date(y, m, day)


def _term_label(months):
    if months % 12 == 0 and months >= 12:
        yrs = months // 12
        return f"{yrs} il"
    return f"{months} ay"


def build_loan_pdf(loan):
    """Return the PDF bytes for a loan summary."""
    _register_fonts()

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=f"Kredit Xülasəsi - {loan.loan_id or loan.pk}",
    )

    ink = colors.HexColor("#131b2e")
    header_bg = colors.HexColor("#283044")
    grid = colors.HexColor("#dae2fd")
    muted = colors.HexColor("#464555")
    zebra = colors.HexColor("#f2f3ff")

    styles = {
        "title": ParagraphStyle(
            "title", fontName=_FONT_BOLD, fontSize=22, leading=28,
            textColor=ink, spaceAfter=10,
        ),
        "section": ParagraphStyle(
            "section", fontName=_FONT_BOLD, fontSize=15, leading=20,
            textColor=ink, spaceBefore=14, spaceAfter=10,
        ),
        "footer": ParagraphStyle(
            "footer", fontName=_FONT_REGULAR, fontSize=9, leading=13,
            textColor=muted, alignment=1,
        ),
    }

    story = []

    # A slim indigo bar at the very top to echo the mock's header
    story.append(_top_bar())

    # Loan summary heading
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("Kredit Xülasəsi", styles["title"]))

    # Loan info key/value table
    customer_full = loan.customer.get_full_name() if loan.customer else ""
    given_name = loan.customer.name if loan.customer else ""
    surname = loan.customer.surname if loan.customer else ""
    start_date = loan.start.date() if loan.start else date.today()

    info_rows = [
        ["Ad", given_name or customer_full],
        ["Soyad", surname],
        ["Kredit ID", loan.loan_id or f"#{loan.pk}"],
        ["Kredit məbləği", f"{loan.amount:,} AZN".replace(",", " ")],
        ["Aylıq ödəniş", f"{loan.monthly_payment:,} AZN".replace(",", " ")],
        ["Kredit müddəti", _term_label(loan.term)],
        ["Başlanğıc tarixi", _az_date(start_date)],
    ]

    info_table = Table(info_rows, colWidths=[45 * mm, 120 * mm])
    info_table.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), _FONT_REGULAR, 10),
        ("FONT", (0, 0), (0, -1), _FONT_BOLD, 10),
        ("FONT", (1, 0), (1, -1), _FONT_BOLD, 10),
        ("TEXTCOLOR", (0, 0), (0, -1), muted),
        ("TEXTCOLOR", (1, 0), (1, -1), ink),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("LINEBELOW", (0, 0), (-1, -2), 0.5, grid),
    ]))
    story.append(info_table)

    # Payment schedule
    story.append(Paragraph("Ödəniş Cədvəli", styles["section"]))

    payments = list(loan.loan_payments.order_by("paid_at", "id"))
    header_row = ["Ödəniş №", "Ödəniş tarixi", "Aylıq ödəniş"]
    rows = [header_row]
    for month_num in range(1, loan.term + 1):
        due = _add_months(start_date, month_num)
        rows.append([
            str(month_num),
            _az_date(due),
            f"{loan.monthly_payment:,} AZN".replace(",", " "),
        ])

    schedule_table = Table(rows, colWidths=[45 * mm, 65 * mm, 55 * mm], repeatRows=1)
    schedule_style = [
        ("BACKGROUND", (0, 0), (-1, 0), header_bg),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONT", (0, 0), (-1, 0), _FONT_BOLD, 10),
        ("FONT", (0, 1), (-1, -1), _FONT_REGULAR, 10),
        ("TEXTCOLOR", (0, 1), (-1, -1), ink),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("LINEBELOW", (0, 1), (-1, -2), 0.4, grid),
        ("BOX", (0, 0), (-1, -1), 0.6, grid),
    ]
    for i in range(1, len(rows)):
        if i % 2 == 0:
            schedule_style.append(("BACKGROUND", (0, i), (-1, i), zebra))
    schedule_table.setStyle(TableStyle(schedule_style))
    story.append(schedule_table)

    # Footer
    story.append(Spacer(1, 10 * mm))
    today_az = _az_date(date.today())
    story.append(Paragraph(f"Sənəd {today_az} tarixində yaradılıb", styles["footer"]))
    story.append(Paragraph(
        "Bu sənəd təsdiqlənmiş kredit şərtləri və ödəniş cədvəlinin xülasəsidir.",
        styles["footer"],
    ))

    doc.build(story)
    return buf.getvalue()


def _top_bar():
    """A thin colored bar drawn as a 1-row table for the page header."""
    bar = Table([[""]], colWidths=[174 * mm], rowHeights=[3 * mm])
    bar.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#283044")),
        ("LINEBELOW", (0, 0), (-1, -1), 0, colors.HexColor("#283044")),
    ]))
    return bar
