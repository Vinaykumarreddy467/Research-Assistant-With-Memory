from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch


def generate_pdf(session_history: list[dict]) -> bytes:
    """Render session Q&A history to a PDF."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5 * inch, bottomMargin=0.5 * inch)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle("Title2", parent=styles["Title"], fontSize=18, spaceAfter=20)
    q_style = ParagraphStyle("Question", parent=styles["Normal"], fontSize=12, textColor="#2563eb", spaceAfter=6)
    a_style = ParagraphStyle("Answer", parent=styles["Normal"], fontSize=11, spaceAfter=4)
    cite_style = ParagraphStyle("Citation", parent=styles["Normal"], fontSize=9, textColor="#6b7280", leftIndent=20, spaceAfter=12)

    story = [Paragraph("Research Assistant — Session Export", title_style), Spacer(1, 12)]

    for i, exchange in enumerate(session_history, 1):
        question = exchange.get("question", "")
        answer = exchange.get("answer", "")
        citations = exchange.get("citations", [])

        story.append(Paragraph(f"<b>Q{i}:</b> {question}", q_style))
        story.append(Paragraph(answer, a_style))

        if citations:
            for cite in citations:
                story.append(Paragraph(f"Source: {cite.get('url', 'N/A')}", cite_style))

        story.append(Spacer(1, 12))

    doc.build(story)
    return buffer.getvalue()
