"""
Doctor Discussion Guide PDF Generator.
Produces a clean, professional, one-page A4 PDF formatted for physician consultations.
Includes:
- Masked patient token / initials, age, date
- Current medication table (generic, brand, strength, duration)
- Top clinical conflicts and exact questions to ask
- Risk score summaries (ACB, Falls, CrCl)
- Space for physician's clinical notes
- Expiring QR code linking to digital read-only share view
- Standard decision-support disclaimer
"""
import io
import os
from typing import Any, Dict, List, Optional
import qrcode
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
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


def generate_qr_code_image(url: str) -> io.BytesIO:
    """Generates an in-memory QR code PNG image."""
    qr = qrcode.QRCode(
        version=1,
        box_size=3,
        border=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


def generate_doctor_guide_pdf(
    patient_info: Dict[str, Any],
    medications: List[Dict[str, Any]],
    alerts: List[Dict[str, Any]],
    risk_scores: Dict[str, Any],
    share_url: str = "http://localhost:8000/share/sample-token",
) -> bytes:
    """Generates the one-page Doctor Discussion Guide as PDF bytes."""
    buf = io.BytesIO()
    # A4: 595.27 x 841.89 points
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=32,
        bottomMargin=32,
    )

    styles = getSampleStyleSheet()

    # Custom typography styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#1d1d1f"),
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#515154"),
    )
    section_h_style = ParagraphStyle(
        "DocSecH",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#0071e3"),
    )
    body_style = ParagraphStyle(
        "DocBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#1d1d1f"),
    )
    table_cell_style = ParagraphStyle(
        "DocCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#1d1d1f"),
    )
    disclaimer_style = ParagraphStyle(
        "DocDisc",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=6.5,
        leading=8,
        textColor=colors.HexColor("#6e6e73"),
    )

    elements = []

    # 1. Header with QR Code
    qr_buf = generate_qr_code_image(share_url)
    qr_img = Image(qr_buf, width=54, height=54)

    pat_id_masked = patient_info.get("display_token", "PAT-XXXX")
    age = patient_info.get("age", 70)
    sex = patient_info.get("sex", "Unknown").title()
    date_str = patient_info.get("date", "2026-10-31")

    header_text = f"""<b>MedGuard Doctor Discussion Guide</b><br/>
    <font color="#515154">Patient Token: <b>{pat_id_masked}</b> | Age: {age} | Sex: {sex} | Generated: {date_str}</font><br/>
    <font color="#8a5a00"><b>Decision-Support Communication Aid — Not a Prescription or Medical Order</b></font>
    """
    header_table = Table(
        [[Paragraph(header_text, title_style), qr_img]],
        colWidths=[450, 65],
    )
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 8))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e5e5ea"), spaceAfter=8))

    # 2. Current Medications Table
    elements.append(Paragraph("1. Current Medication Picture (Confirmed)", section_h_style))
    elements.append(Spacer(1, 4))

    med_rows = [["Generic Ingredient(s)", "Brand / Preparation", "Strength", "Duration", "Source"]]
    for m in medications[:6]:  # Limit to 6 on 1-page summary
        ings = ", ".join([i["ingredient"].title() for i in m.get("ingredients", [])])
        brand = m.get("brand") or m.get("raw_text") or "-"
        strength = m.get("strength") or m.get("strength_text") or "-"
        duration = m.get("start_date") or "Ongoing"
        source = m.get("source", "Voice/App").title()
        med_rows.append([
            Paragraph(ings, table_cell_style),
            Paragraph(brand, table_cell_style),
            Paragraph(strength, table_cell_style),
            Paragraph(duration, table_cell_style),
            Paragraph(source, table_cell_style),
        ])

    med_table = Table(med_rows, colWidths=[140, 110, 80, 100, 85])
    med_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f5f5f7")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor("#1d1d1f")),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e5ea")),
    ]))
    elements.append(med_table)
    elements.append(Spacer(1, 10))

    # 3. Top Discussion Points / Conflicts
    elements.append(Paragraph("2. Top Clinical Considerations to Review", section_h_style))
    elements.append(Spacer(1, 4))

    top_alerts = alerts[:3]
    if not top_alerts:
        elements.append(Paragraph("No high-risk guideline conflicts identified across current regimen.", body_style))
    else:
        for idx, a in enumerate(top_alerts):
            sev = a.get("severity", "moderate").upper()
            color_hex = "#d70015" if sev == "CRITICAL" else ("#c93400" if sev == "HIGH" else "#8a5a00")
            point_text = f"""<b><font color="{color_hex}">[{sev}]</font> {a.get('type', '').replace('_', ' ').title()}</b>: {a.get('mechanism_summary', '')}<br/>
            &nbsp;&nbsp;&bull; <b>Suggested Doctor Question:</b> <i>\"{a.get('doctor_question', '')}\"</i>
            """
            elements.append(Paragraph(point_text, body_style))
            elements.append(Spacer(1, 3))

    elements.append(Spacer(1, 8))

    # 4. Risk Scores Summary (ACB, Falls, Renal)
    elements.append(Paragraph("3. Patient Vulnerability Metrics", section_h_style))
    elements.append(Spacer(1, 4))

    acb = risk_scores.get("acb", {})
    fall = risk_scores.get("fall_risk", {})
    renal = risk_scores.get("renal", {})

    acb_text = f"<b>Anticholinergic Burden:</b> {acb.get('score', 0)} ({acb.get('level', 'None')})"
    fall_text = f"<b>Fall-Risk Drugs:</b> {fall.get('band', 'Low')} ({fall.get('count', 0)} meds)"
    renal_val = f"{renal.get('value')} mL/min" if renal.get("available") else "Not provided"
    renal_text = f"<b>Est. Renal CrCl:</b> {renal_val}"

    scores_table = Table([[
        Paragraph(acb_text, body_style),
        Paragraph(fall_text, body_style),
        Paragraph(renal_text, body_style),
    ]], colWidths=[170, 170, 175])
    scores_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f5f5f7")),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e5ea")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(scores_table)
    elements.append(Spacer(1, 10))

    # 5. Doctor's Clinical Notes Box
    elements.append(Paragraph("4. Physician Notes & Treatment Decisions", section_h_style))
    elements.append(Spacer(1, 4))
    notes_box = Table([["\n\n\n\n"]], colWidths=[515])
    notes_box.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.75, colors.HexColor("#c7c7cc")),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#ffffff")),
    ]))
    elements.append(notes_box)
    elements.append(Spacer(1, 8))

    # 6. Footer Disclaimer
    disclaimer_text = (
        "<b>LEGAL & CLINICAL DISCLAIMER:</b> MedGuard is a clinical decision-support and communication aid grounded in "
        "published geriatric safety guidelines (AGS Beers, STOPP/START v3, FDA labels). It is not a certified medical device and does not "
        "diagnose, prescribe, or provide directive orders. Patients must never alter medication regimens without qualified medical consultation."
    )
    elements.append(Paragraph(disclaimer_text, disclaimer_style))

    doc.build(elements)
    pdf_bytes = buf.getvalue()
    buf.close()
    return pdf_bytes

