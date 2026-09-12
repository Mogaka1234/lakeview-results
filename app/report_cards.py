"""
Branded PDF report cards for Lakeview Junior School.
Clean layout with header band, performance table, chart, comments and signatures.
"""
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    KeepTogether, HRFlowable, Flowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Circle
from reportlab.graphics.charts.barcharts import VerticalBarChart
from datetime import datetime
from . import grading

SCHOOL_NAME = "Lakeview Junior School"
SCHOOL_MOTTO = "Excellence Through Competence"
SCHOOL_TAGLINE = "Junior Secondary  •  Grades 7 – 9"


# Brand colours
NAVY = colors.Color(0.05, 0.18, 0.38)
NAVY_LIGHT = colors.Color(0.12, 0.28, 0.52)
GOLD = colors.Color(0.75, 0.58, 0.15)
LIGHT_BG = colors.Color(0.94, 0.96, 0.99)
ROW_ALT = colors.Color(0.96, 0.97, 0.99)


def _level_color(level: str):
    return {
        "EE1": colors.Color(0.05, 0.45, 0.22),
        "EE2": colors.Color(0.12, 0.55, 0.30),
        "ME1": colors.Color(0.15, 0.40, 0.65),
        "ME2": colors.Color(0.25, 0.48, 0.70),
        "AE1": colors.Color(0.80, 0.50, 0.08),
        "AE2": colors.Color(0.85, 0.55, 0.12),
        "BE1": colors.Color(0.75, 0.22, 0.18),
        "BE2": colors.Color(0.65, 0.12, 0.12),
    }.get(level, colors.grey)


class HeaderBand(Flowable):
    """Full-width coloured header with school name."""
    def __init__(self, width, height=28*mm):
        Flowable.__init__(self)
        self.width = width
        self.height = height

    def draw(self):
        self.canv.setFillColor(NAVY)
        self.canv.rect(0, 0, self.width, self.height, fill=1, stroke=0)
        # Gold accent line
        self.canv.setFillColor(GOLD)
        self.canv.rect(0, 0, self.width, 2.2*mm, fill=1, stroke=0)
        # School name
        self.canv.setFillColor(colors.white)
        self.canv.setFont("Helvetica-Bold", 16)
        self.canv.drawCentredString(self.width/2, self.height - 11*mm, SCHOOL_NAME.upper())
        self.canv.setFont("Helvetica", 8)
        self.canv.setFillColor(colors.Color(0.85, 0.88, 0.95))
        self.canv.drawCentredString(self.width/2, self.height - 16.5*mm, SCHOOL_MOTTO)
        self.canv.setFont("Helvetica", 7.5)
        self.canv.drawCentredString(self.width/2, self.height - 21*mm, SCHOOL_TAGLINE)


def _make_performance_chart(subject_scores, width=480, height=155):
    if not subject_scores:
        d = Drawing(width, 30)
        d.add(String(width/2, 12, "No performance data available", textAnchor="middle",
                     fontSize=8, fillColor=colors.grey))
        return d

    names = [s[0][:14] for s in subject_scores]
    data = [[s[1] for s in subject_scores]]

    d = Drawing(width, height)
    # Background panel
    d.add(Rect(0, 0, width, height, fillColor=LIGHT_BG, strokeColor=colors.Color(0.8, 0.84, 0.9), strokeWidth=0.5))

    chart = VerticalBarChart()
    chart.x = 38
    chart.y = 28
    chart.height = height - 50
    chart.width = width - 55
    chart.data = data
    chart.valueAxis.valueMin = 0
    chart.valueAxis.valueMax = 100
    chart.valueAxis.valueStep = 25
    chart.valueAxis.labels.fontSize = 7
    chart.valueAxis.labels.fillColor = colors.Color(0.3, 0.35, 0.4)
    chart.categoryAxis.labels.boxAnchor = "ne"
    chart.categoryAxis.labels.dx = -1
    chart.categoryAxis.labels.dy = -1
    chart.categoryAxis.labels.angle = 40
    chart.categoryAxis.labels.fontSize = 6.5
    chart.categoryAxis.categoryNames = names
    chart.bars[0].fillColor = NAVY_LIGHT
    chart.bars[0].strokeColor = NAVY
    chart.bars[0].strokeWidth = 0.4
    d.add(chart)

    d.add(String(width/2, height - 12, "Performance by Subject (%)", textAnchor="middle",
                 fontSize=9, fillColor=NAVY, fontName="Helvetica-Bold"))
    return d


def generate_report_card(
    learner, term, subject_results,
    class_teacher_comment="", dos_comment="", principal_comment="",
    overall_level="", overall_average=0.0,
) -> bytes:
    buffer = BytesIO()
    page_width = A4[0]
    left_margin = 12*mm
    right_margin = 12*mm
    content_width = page_width - left_margin - right_margin

    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=left_margin, rightMargin=right_margin,
        topMargin=8*mm, bottomMargin=10*mm,
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="ReportTitle", fontSize=11, alignment=TA_CENTER,
                              textColor=NAVY, fontName="Helvetica-Bold", spaceBefore=3, spaceAfter=2))
    styles.add(ParagraphStyle(name="Section", fontSize=9, fontName="Helvetica-Bold",
                              textColor=NAVY, spaceBefore=6, spaceAfter=3))
    styles.add(ParagraphStyle(name="Body", fontSize=8, leading=11))
    styles.add(ParagraphStyle(name="Small", fontSize=7.5, leading=10))
    styles.add(ParagraphStyle(name="Comment", fontSize=7.5, leading=10, leftIndent=2))
    styles.add(ParagraphStyle(name="Footer", fontSize=6.5, alignment=TA_CENTER, textColor=colors.grey))
    styles.add(ParagraphStyle(name="CenterSmall", fontSize=7.5, alignment=TA_CENTER))

    story = []

    # ===== Header band =====
    story.append(HeaderBand(content_width))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("LEARNER PROGRESS REPORT", styles["ReportTitle"]))
    story.append(HRFlowable(width="100%", thickness=0.8, color=GOLD, spaceBefore=1, spaceAfter=3*mm))

    # ===== Learner info box =====
    year = term.academic_year.year if getattr(term, "academic_year", None) else datetime.now().year
    info_style = styles["Small"]
    info_data = [
        [Paragraph(f"<b>Name</b><br/>{learner.first_name} {learner.last_name}", info_style),
         Paragraph(f"<b>Admission No.</b><br/>{learner.admission_no}", info_style),
         Paragraph(f"<b>Stream</b><br/>{learner.stream.name if learner.stream else '—'}", info_style)],
        [Paragraph(f"<b>Gender</b><br/>{learner.gender or '—'}", info_style),
         Paragraph(f"<b>Term</b><br/>{term.name}", info_style),
         Paragraph(f"<b>Academic Year</b><br/>{year}", info_style)],
    ]
    info_table = Table(info_data, colWidths=[content_width/3]*3)
    info_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
        ("BOX", (0, 0), (-1, -1), 0.6, NAVY_LIGHT),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.Color(0.75, 0.8, 0.88)),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 4*mm))

    # ===== Subject performance table =====
    story.append(Paragraph("SUBJECT PERFORMANCE", styles["Section"]))

    header = [
        Paragraph("<b>Subject</b>", styles["Small"]),
        Paragraph("<b>Score %</b>", styles["Small"]),
        Paragraph("<b>Level</b>", styles["Small"]),
        Paragraph("<b>Description</b>", styles["Small"]),
        Paragraph("<b>Teacher Comment</b>", styles["Small"]),
    ]
    rows = [header]
    for r in subject_results:
        level = r.get("level", "")
        desc = grading.get_level_description(level).split("(")[0].strip()
        rows.append([
            Paragraph(r.get("subject", ""), styles["Small"]),
            Paragraph(f"{r.get('score', 0):.1f}", styles["Small"]),
            Paragraph(f"<b>{level}</b>", styles["Small"]),
            Paragraph(desc, styles["Small"]),
            Paragraph(r.get("comment") or "—", styles["Small"]),
        ])

    col_w = [42*mm, 18*mm, 16*mm, 48*mm, content_width - 42*mm - 18*mm - 16*mm - 48*mm]
    t = Table(rows, colWidths=col_w, repeatRows=1)
    cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (1, 0), (2, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.Color(0.7, 0.75, 0.82)),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ROW_ALT]),
    ]
    for i, r in enumerate(subject_results, start=1):
        cmds.append(("TEXTCOLOR", (2, i), (2, i), _level_color(r.get("level", ""))))
    t.setStyle(TableStyle(cmds))
    story.append(t)
    story.append(Spacer(1, 3.5*mm))

    # ===== Overall box =====
    story.append(Paragraph("OVERALL PERFORMANCE", styles["Section"]))
    overall_data = [[
        Paragraph(f"<b>Average Score</b><br/><font size='12'><b>{overall_average:.1f}%</b></font>", styles["CenterSmall"]),
        Paragraph(f"<b>Overall Level</b><br/><font size='11' color='#{_level_color(overall_level).hexval()[2:]}'><b>{overall_level}</b></font>", styles["CenterSmall"]),
        Paragraph(f"<b>Description</b><br/>{grading.get_level_description(overall_level).split('(')[0].strip()}", styles["CenterSmall"]),
    ]]
    ot = Table(overall_data, colWidths=[content_width/3]*3)
    ot.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
        ("BOX", (0, 0), (-1, -1), 1, NAVY),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, NAVY_LIGHT),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))
    story.append(ot)
    story.append(Spacer(1, 3*mm))

    # ===== Graph =====
    chart_data = [(r["subject"], r["score"]) for r in subject_results]
    story.append(_make_performance_chart(chart_data, width=content_width))
    story.append(Spacer(1, 3.5*mm))

    # ===== Comments =====
    story.append(Paragraph("COMMENTS", styles["Section"]))
    def comment_block(title, text):
        return [
            Paragraph(f"<b>{title}</b>", styles["Small"]),
            Paragraph(text or "………………………………………………………………………………………", styles["Comment"]),
            Spacer(1, 2*mm),
        ]
    for title, text in [
        ("Class Teacher", class_teacher_comment),
        ("Director of Studies", dos_comment),
        ("Principal", principal_comment),
    ]:
        story.extend(comment_block(title, text))

    story.append(Spacer(1, 3*mm))

    # ===== Signatures =====
    sig = [
        [Paragraph("_______________________", styles["CenterSmall"]),
         Paragraph("_______________________", styles["CenterSmall"]),
         Paragraph("_______________________", styles["CenterSmall"])],
        [Paragraph("<b>Class Teacher</b>", styles["CenterSmall"]),
         Paragraph("<b>Director of Studies</b>", styles["CenterSmall"]),
         Paragraph("<b>Principal</b>", styles["CenterSmall"])],
        [Paragraph("Date: _______________", styles["CenterSmall"]),
         Paragraph("Date: _______________", styles["CenterSmall"]),
         Paragraph("Date: _______________", styles["CenterSmall"])],
    ]
    sig_t = Table(sig, colWidths=[content_width/3]*3)
    sig_t.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
    ]))
    story.append(sig_t)
    story.append(Spacer(1, 4*mm))

    # ===== Footer / Key =====
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.Color(0.7, 0.75, 0.8)))
    legend = (
        "<b>Performance Key:</b>  EE1 (90–100%) &nbsp; EE2 (75–89%) &nbsp; ME1 (65–74%) &nbsp; ME2 (50–64%) &nbsp; "
        "AE1 (35–49%) &nbsp; AE2 (20–34%) &nbsp; BE1 (10–19%) &nbsp; BE2 (0–9%)"
    )
    story.append(Paragraph(legend, styles["Footer"]))
    story.append(Paragraph(
        f"Generated on {datetime.now().strftime('%d %B %Y at %H:%M')}  •  {SCHOOL_NAME}  •  results.lakeviewjunior.ac.ke",
        styles["Footer"]
    ))

    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf
