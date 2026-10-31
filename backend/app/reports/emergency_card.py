"""
Emergency Medication Card Generator.
Produces a compact wallet-sized / lock-screen printable card:
- Masked name / initials
- Age, sex, emergency contact
- Active medications with generic names and strengths
- Critical clinical hazard flags (e.g., 'ON A BLOOD THINNER', 'FALL RISK')
- Expiring QR link for paramedics / emergency physicians
"""
import io
from typing import Any, Dict, List
import qrcode
from reportlab.lib import colors
from reportlab.lib.pagesizes import A6  # Compact wallet/card size (105 x 148 mm)
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    HRFlowable,
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def generate_emergency_card_pdf(
    patient_info: Dict[str, Any],
    medications: List[Dict[str, Any]],
    critical_flags: List[str],
    share_url: str = "http://localhost:8000/share/sample-emergency-token",
) -> bytes:
    """Generates a compact A6 emergency card PDF."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A6,
        rightMargin=16,
        leftMargin=16,
        topMargin=16,
        bottomMargin=16,
    )

    styles = getSampleStyleSheet()

    header_style = ParagraphStyle(
        "EmergHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#d70015"),
    )
    title_style = ParagraphStyle(
        "EmergTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=11,
        textColor=colors.HexColor("#1d1d1f"),
    )
    cell_style = ParagraphStyle(
        "EmergCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=9,
        textColor=colors.HexColor("#1d1d1f"),
    )
    flag_style = ParagraphStyle(
        "EmergFlag",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#d70015"),
    )

    elements = []

    # 1. Header with Medical Alert Banner
    elements.append(Paragraph("MEDGUARD EMERGENCY CARD", header_style))
    elements.append(Spacer(1, 4))

    # Masked Patient Details
    pat_token = patient_info.get("display_token", "PAT-XXXX")
    age = patient_info.get("age", 70)
    sex = patient_info.get("sex", "Unknown").title()

    info_text = f"<b>Patient:</b> {pat_token} | <b>Age:</b> {age} | <b>Sex:</b> {sex}"
    elements.append(Paragraph(info_text, title_style))
    elements.append(Spacer(1, 4))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#d70015"), spaceAfter=6))

    # 2. Critical Safety Flags (e.g., Blood Thinner)
    if critical_flags:
        flags_text = "<b>CRITICAL ALERTS:</b> " + " | ".join(critical_flags)
        elements.append(Paragraph(flags_text, flag_style))
        elements.append(Spacer(1, 6))

    # 3. Medications Table
    elements.append(Paragraph("<b>Active Medications:</b>", title_style))
    elements.append(Spacer(1, 3))

    rows = [["Ingredient", "Brand", "Strength"]]
    for m in medications[:5]:
        ings = ", ".join([i["ingredient"].title() for i in m.get("ingredients", [])])
        brand = m.get("brand") or "-"
        strength = m.get("strength") or m.get("strength_text") or "-"
        rows.append([
            Paragraph(ings, cell_style),
            Paragraph(brand, cell_style),
            Paragraph(strength, cell_style),
        ])

    table = Table(rows, colWidths=[120, 80, 60])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f5f5f7")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e5ea")),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 8))

    # 4. QR Code linking to full live digital summary
    qr = qrcode.QRCode(version=1, box_size=2, border=1)
    qr.add_data(share_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    qr_buf = io.BytesIO()
    img.save(qr_buf, format="PNG")
    qr_buf.seek(0)
    qr_img = Image(qr_buf, width=45, height=45)

    qr_table = Table([[
        qr_img,
        Paragraph("Scan QR for full clinical profile, allergies, and emergency discussion guide.", cell_style),
    ]], colWidths=[55, 205])
    qr_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(qr_table)

    doc.build(elements)
    pdf_bytes = buf.getvalue()
    buf.close()
    return pdf_bytes

