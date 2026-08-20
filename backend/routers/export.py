from fastapi import APIRouter
from fastapi.responses import Response
from models.schemas import ExportRequest
from core.pdf_export import generate_pdf

router = APIRouter()


@router.post("/export-pdf")
async def export_pdf(req: ExportRequest):
    """Render the session Q&A history to a PDF and return it."""
    pdf_bytes = generate_pdf(req.session_history)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=session-export.pdf"},
    )
