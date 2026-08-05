from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)
from datetime import datetime
import io
import html

from models.sentiment import VideoAnalysis


def generate_pdf_report(room_id: str, transcript: str, sentiment: VideoAnalysis | None) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=20 * mm, bottomMargin=20 * mm)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle("TitleStyle", parent=styles["Title"], fontSize=18, spaceAfter=10)
    heading_style = ParagraphStyle("HeadingStyle", parent=styles["Heading2"], spaceBefore=14, spaceAfter=6)
    body_style = styles["BodyText"]
    flag_style = ParagraphStyle("FlagStyle", parent=styles["BodyText"], textColor=colors.red, fontName="Helvetica-Bold")
    warning_style = ParagraphStyle("WarningStyle", parent=styles["BodyText"], textColor=colors.HexColor("#b8860b"), fontName="Helvetica-Oblique")

    elements = []

    elements.append(Paragraph("Video KYC Verification Report", title_style))
    elements.append(Paragraph(f"Room ID: {html.escape(room_id)}", body_style))
    elements.append(Paragraph(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", body_style))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph("Sentiment & Behavioral Analysis", heading_style))

    if sentiment is not None:
        summary_data = [
            ["Overall Sentiment", sentiment.overall_sentiment.capitalize()],
            ["Sentiment Score", f"{sentiment.sentiment_score:.2f}"],
            ["Engagement Level", sentiment.engagement_level.capitalize()],
            ["Confidence", f"{sentiment.confidence:.2f}"],
        ]
        table = Table(summary_data, colWidths=[150, 300])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f0f0f0")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 10))

        elements.append(Paragraph("Facial Expression Summary", heading_style))
        elements.append(Paragraph(html.escape(sentiment.facial_expression_summary), body_style))

        elements.append(Paragraph("Inferred Intention", heading_style))
        elements.append(Paragraph(html.escape(sentiment.inferred_intention), body_style))

        if sentiment.stress_indicators:
            elements.append(Paragraph("Stress Indicators", heading_style))
            for s in sentiment.stress_indicators:
                elements.append(Paragraph(f"• {html.escape(s)}", body_style))

        if sentiment.key_moments:
            elements.append(Paragraph("Key Moments", heading_style))
            moment_data = [["Timestamp", "Observation"]] + [
                [m.approx_timestamp, html.escape(m.observation)] for m in sentiment.key_moments
            ]
            moment_table = Table(moment_data, colWidths=[80, 370])
            moment_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dddddd")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]))
            elements.append(moment_table)

        elements.append(Spacer(1, 10))
        risk_text = "⚠ DECEPTION RISK FLAGGED" if sentiment.deception_risk_flag else "No deception risk flagged"
        elements.append(Paragraph(risk_text, flag_style if sentiment.deception_risk_flag else body_style))

    else:
        elements.append(Paragraph(
            "Sentiment analysis is unavailable for this session (analysis service error). "
            "Only the call transcript is included below.",
            warning_style
        ))
        elements.append(Spacer(1, 10))

    elements.append(PageBreak())
    elements.append(Paragraph("Call Transcript", heading_style))
    if transcript:
        for line in transcript.split("\n"):
            if line.strip():
                elements.append(Paragraph(html.escape(line), body_style))
                elements.append(Spacer(1, 4))
    else:
        elements.append(Paragraph("Transcript not available.", body_style))

    doc.build(elements)
    return buffer.getvalue()