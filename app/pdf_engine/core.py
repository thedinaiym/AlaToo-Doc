from __future__ import annotations

import enum
import io
from html import escape
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from xhtml2pdf import pisa
from xhtml2pdf.default import DEFAULT_FONT


class DocumentType(str, enum.Enum):
    change_of_grade = "change_of_grade"
    academic_leave = "academic_leave"
    late_enrollment = "late_enrollment"
    student_complaint = "student_complaint"


TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
PUBLIC_DIR = PROJECT_ROOT / "frontend" / "public"
FONT_FAMILY = "UniversitySerif"
DEFAULT_LOGO_PATH = PUBLIC_DIR / "logo.png"


def _candidate_font_paths() -> tuple[Path, ...]:
    return (
        Path("C:/Windows/Fonts/times.ttf"),
        Path("C:/Windows/Fonts/timesnewroman.ttf"),
        Path("/usr/share/fonts/truetype/liberation2/LiberationSerif-Regular.ttf"),
        Path("/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"),
        Path("/usr/share/fonts/truetype/msttcorefonts/Times_New_Roman.ttf"),
        Path("/Library/Fonts/Times New Roman.ttf"),
        Path("/System/Library/Fonts/Supplemental/Times New Roman.ttf"),
    )


def _candidate_bold_font_paths() -> tuple[Path, ...]:
    return (
        Path("C:/Windows/Fonts/timesbd.ttf"),
        Path("/usr/share/fonts/truetype/liberation2/LiberationSerif-Bold.ttf"),
        Path("/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"),
        Path("/Library/Fonts/Times New Roman Bold.ttf"),
        Path("/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf"),
    )


def _resolve_existing_font(font_paths: tuple[Path, ...]) -> Path | None:
    for font_path in font_paths:
        if font_path.exists():
            return font_path
    return None


def _resolve_cyrillic_font() -> Path:
    font_path = _resolve_existing_font(_candidate_font_paths())
    if font_path is not None:
        return font_path

    raise RuntimeError(
        "No Cyrillic-capable serif font found. Install Times New Roman or Liberation Serif."
    )


CYRILLIC_FONT_PATH = _resolve_cyrillic_font()
BOLD_CYRILLIC_FONT_PATH = _resolve_existing_font(_candidate_bold_font_paths()) or CYRILLIC_FONT_PATH
pdfmetrics.registerFont(TTFont(FONT_FAMILY, str(CYRILLIC_FONT_PATH)))
pdfmetrics.registerFont(TTFont(f"{FONT_FAMILY}-Bold", str(BOLD_CYRILLIC_FONT_PATH)))
registerFontFamily(
    FONT_FAMILY,
    normal=FONT_FAMILY,
    bold=f"{FONT_FAMILY}-Bold",
    italic=FONT_FAMILY,
    boldItalic=f"{FONT_FAMILY}-Bold",
)
DEFAULT_FONT.update(
    {
        FONT_FAMILY.lower(): FONT_FAMILY,
        "times new roman": FONT_FAMILY,
        "times": FONT_FAMILY,
        "times-roman": FONT_FAMILY,
        "serif": FONT_FAMILY,
    }
)


env = Environment(
    loader=FileSystemLoader(str(TEMPLATE_DIR)),
    autoescape=select_autoescape(("html", "xml")),
    trim_blocks=True,
    lstrip_blocks=True,
)


def _link_callback(uri: str, _rel: str) -> str:
    if uri == "cyrillic-font.ttf":
        return str(CYRILLIC_FONT_PATH)
    if uri in {"/public/logo.png", "public/logo.png", "logo.png"}:
        return str(DEFAULT_LOGO_PATH)
    path = Path(uri)
    if path.is_absolute() and path.exists():
        return str(path)
    project_path = PROJECT_ROOT / uri.lstrip("/")
    if project_path.exists():
        return str(project_path)
    return uri


def render_document_to_pdf(doc_type: str, context: dict[str, Any]) -> bytes:
    try:
        document_type = DocumentType(doc_type)
    except ValueError as exc:
        allowed = ", ".join(item.value for item in DocumentType)
        raise ValueError(f"Unsupported document type '{doc_type}'. Allowed: {allowed}") from exc

    return _render_with_reportlab(document_type, context)


def _paragraphs_from_text(text: str) -> list[str]:
    paragraphs = [line.strip() for line in text.splitlines() if line.strip()]
    return paragraphs or [text.strip()]


def _render_with_reportlab(_document_type: DocumentType, context: dict[str, Any]) -> bytes:
    output = io.BytesIO()
    document = SimpleDocTemplate(
        output,
        pagesize=A4,
        leftMargin=30 * mm,
        rightMargin=10 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    normal_style = ParagraphStyle(
        "UniversityNormal",
        fontName=FONT_FAMILY,
        fontSize=12,
        leading=15,
        alignment=TA_LEFT,
        spaceAfter=0,
    )
    header_style = ParagraphStyle(
        "UniversityHeader",
        parent=normal_style,
        leading=14,
    )
    title_style = ParagraphStyle(
        "UniversityTitle",
        parent=normal_style,
        fontName=f"{FONT_FAMILY}-Bold",
        alignment=TA_CENTER,
        leading=14,
    )
    body_style = ParagraphStyle(
        "UniversityBody",
        parent=normal_style,
        alignment=TA_JUSTIFY,
        firstLineIndent=12.5 * mm,
        leading=15,
        spaceAfter=3 * mm,
    )
    signature_style = ParagraphStyle(
        "UniversitySignature",
        parent=normal_style,
        fontName=f"{FONT_FAMILY}-Bold",
        fontSize=10,
        leading=12,
        alignment=TA_CENTER,
    )

    story: list[Any] = []
    logo_path = Path(str(context.get("logo_path") or DEFAULT_LOGO_PATH))
    if not logo_path.is_absolute():
        logo_path = PROJECT_ROOT / logo_path
    if logo_path.exists():
        logo = Image(str(logo_path), width=22 * mm, height=22 * mm, kind="proportional")
        logo.hAlign = "CENTER"
        story.extend([logo, Spacer(1, 6 * mm)])

    from_student_label = str(context.get("from_student_label") or "от студента")
    group_label = str(context.get("group_label") or "Группа")
    registration_label = str(context.get("registration_label") or "Регистрационный №")
    signed_label = str(context.get("signed_label") or "ПОДПИСАНО ЭП")

    recipient_lines = [
        str(context.get("recipient_title") or ""),
        str(context.get("recipient_name") or ""),
        f"{from_student_label} {context.get('student_name') or ''}",
        f"ID: {context.get('student_id') or ''}",
        f"{group_label}: {context.get('group_or_faculty') or context.get('faculty') or ''}",
    ]
    recipient_block = "<br/>".join(escape(line) for line in recipient_lines if line)
    header_table = Table(
        [["", Paragraph(recipient_block, header_style)]],
        colWidths=[85 * mm, 75 * mm],
    )
    header_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    story.extend([header_table, Spacer(1, 14 * mm)])

    story.append(
        Paragraph(escape(str(context.get("application_title") or "ЗАЯВЛЕНИЕ")), title_style)
    )
    story.append(
        Paragraph(
            f"{registration_label} {escape(str(context.get('doc_number') or ''))}",
            normal_style.clone("DocumentNumber", alignment=TA_CENTER, leading=14),
        )
    )
    story.append(Spacer(1, 12 * mm))

    for paragraph in _paragraphs_from_text(str(context.get("final_text") or "")):
        story.append(Paragraph(escape(paragraph), body_style))

    story.append(Spacer(1, 18 * mm))
    signature_table = Table(
        [
            [
                Paragraph(escape(str(context.get("date") or "")), normal_style),
                Paragraph(escape(signed_label), signature_style),
            ]
        ],
        colWidths=[80 * mm, 80 * mm],
    )
    signature_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                ("BOX", (1, 0), (1, 0), 1, colors.black),
                ("LEFTPADDING", (0, 0), (0, 0), 0),
                ("RIGHTPADDING", (0, 0), (0, 0), 0),
                ("TOPPADDING", (1, 0), (1, 0), 6 * mm),
                ("BOTTOMPADDING", (1, 0), (1, 0), 6 * mm),
            ]
        )
    )
    story.append(signature_table)

    document.build(story)
    return output.getvalue()


def render_document_to_pdf_with_xhtml2pdf(doc_type: str, context: dict[str, Any]) -> bytes:
    try:
        document_type = DocumentType(doc_type)
    except ValueError as exc:
        allowed = ", ".join(item.value for item in DocumentType)
        raise ValueError(f"Unsupported document type '{doc_type}'. Allowed: {allowed}") from exc

    template = env.get_template(f"{document_type.value}.html")
    template_context = {
        **context,
        "font_family": FONT_FAMILY,
        "doc_type": document_type.value,
        "logo_path": str(context.get("logo_path") or DEFAULT_LOGO_PATH),
    }
    html = template.render(
        **template_context,
    )

    output = io.BytesIO()
    result = pisa.CreatePDF(
        src=html,
        dest=output,
        encoding="utf-8",
        link_callback=_link_callback,
    )

    if result.err:
        raise RuntimeError("Failed to render PDF document")

    return output.getvalue()
