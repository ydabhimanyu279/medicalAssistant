import io
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle, ListFlowable, ListItem
from reportlab.lib.enums import TA_CENTER
from datetime import datetime

def generate_discharge_pdf(session, transcript_text: str, discharge_content: dict) -> bytes:
    """Generate a discharge summary PDF and return it as bytes."""

    buffer = io.BytesIO()
    doc    = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
    )

    styles  = getSampleStyleSheet()
    content = []

    # Custom styles
    title_style = ParagraphStyle(
        "Title",
        parent=styles["Heading1"],
        fontSize=22,
        textColor=colors.HexColor("#0f172a"),
        alignment=TA_CENTER,
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#64748b"),
        alignment=TA_CENTER,
        spaceAfter=20,
    )
    section_style = ParagraphStyle(
        "Section",
        parent=styles["Heading2"],
        fontSize=13,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=16,
        spaceAfter=8,
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#334155"),
        leading=16,
    )
    footer_style = ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.HexColor("#94a3b8"),
        alignment=TA_CENTER,
    )

    # Header
    content.append(Paragraph("MedAssist", title_style))
    content.append(Paragraph("Patient Discharge Summary", subtitle_style))
    content.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e2e8f0")))
    content.append(Spacer(1, 12))

    # Session info table
    content.append(Paragraph("Consultation Details", section_style))
    discharge_date = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    created        = datetime.fromisoformat(str(session.created_at)).strftime("%B %d, %Y at %I:%M %p")
    info_data = [
        ["Session Title",   session.title],
        ["Session ID",      str(session.id)],
        ["Consultation Date", created],
        ["Discharge Date",  discharge_date],
    ]
    info_table = Table(info_data, colWidths=[4.5*cm, 12.5*cm])
    info_table.setStyle(TableStyle([
        ("FONTSIZE",      (0, 0), (-1, -1), 10),
        ("TEXTCOLOR",     (0, 0), (0, -1), colors.HexColor("#64748b")),
        ("TEXTCOLOR",     (1, 0), (1, -1), colors.HexColor("#1e293b")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    content.append(info_table)
    content.append(Spacer(1, 8))
    content.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e2e8f0")))

    # Possible cause
    content.append(Paragraph("Possible Cause", section_style))
    content.append(Paragraph(
        discharge_content.get("possible_cause", "Not determined."),
        body_style
    ))
    content.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e2e8f0")))

    # Prescribed drugs
    content.append(Paragraph("Prescribed Drugs and Dosages", section_style))
    drugs = discharge_content.get("prescribed_drugs", [])
    if drugs:
        items = [ListItem(Paragraph(d, body_style), bulletColor=colors.HexColor("#3b82f6")) for d in drugs]
        content.append(ListFlowable(items, bulletType="bullet"))
    else:
        content.append(Paragraph("No drugs prescribed.", body_style))
    content.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e2e8f0")))

    # Follow up tests
    content.append(Paragraph("Recommended Follow-Up Tests", section_style))
    tests = discharge_content.get("followup_tests", [])
    if tests:
        items = [ListItem(Paragraph(t, body_style), bulletColor=colors.HexColor("#3b82f6")) for t in tests]
        content.append(ListFlowable(items, bulletType="bullet"))
    else:
        content.append(Paragraph("No follow-up tests recommended.", body_style))
    content.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e2e8f0")))

    # Follow up instructions
    content.append(Paragraph("Follow-Up Instructions", section_style))
    instructions = discharge_content.get("followup_instructions", [])
    if instructions:
        items = [ListItem(Paragraph(i, body_style), bulletColor=colors.HexColor("#3b82f6")) for i in instructions]
        content.append(ListFlowable(items, bulletType="bullet"))
    else:
        content.append(Paragraph("No specific instructions provided.", body_style))

    # Footer
    content.append(Spacer(1, 24))
    content.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e2e8f0")))
    content.append(Spacer(1, 6))
    content.append(Paragraph(
        "Generated by MedAssist — for clinical reference only. Doctor review and approval required before patient discharge.",
        footer_style
    ))

    doc.build(content)
    buffer.seek(0)
    return buffer.read()