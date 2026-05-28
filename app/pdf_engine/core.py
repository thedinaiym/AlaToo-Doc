from __future__ import annotations

import enum
import io
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.pdfbase.ttfonts import TTFont
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
