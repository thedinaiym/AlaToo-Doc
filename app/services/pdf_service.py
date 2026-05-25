from html import escape
from pathlib import Path

from xhtml2pdf import pisa


def generate_document_pdf(title: str, text: str, output_path: str) -> None:
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    safe_title = escape(title)
    safe_text = "<br />".join(escape(text).splitlines())

    html = f"""
    <!doctype html>
    <html>
      <head>
        <meta charset="utf-8" />
        <style>
          @page {{
            size: A4;
            margin: 2.2cm 2cm;
          }}

          body {{
            color: #111827;
            font-family: Arial, Helvetica, sans-serif;
            font-size: 12pt;
            line-height: 1.55;
          }}

          .document {{
            width: 100%;
          }}

          .header {{
            border-bottom: 1px solid #d1d5db;
            margin-bottom: 28px;
            padding-bottom: 14px;
            text-align: center;
          }}

          .university {{
            font-size: 11pt;
            font-weight: bold;
            letter-spacing: 0.4px;
            text-transform: uppercase;
          }}

          h1 {{
            font-size: 18pt;
            margin: 26px 0 22px;
            text-align: center;
          }}

          .content {{
            font-size: 12pt;
            margin-top: 24px;
            text-align: justify;
          }}

          .footer {{
            margin-top: 56px;
          }}

          .signature-row {{
            margin-top: 34px;
            width: 100%;
          }}

          .signature-label {{
            display: inline-block;
            width: 130px;
          }}
        </style>
      </head>
      <body>
        <div class="document">
          <div class="header">
            <div class="university">Ala-Too International University</div>
            <div>Official document management system</div>
          </div>

          <h1>{safe_title}</h1>

          <div class="content">{safe_text}</div>

          <div class="footer">
            <div class="signature-row">
              <span class="signature-label">Signature:</span>
              ______________________________
            </div>
            <div class="signature-row">
              <span class="signature-label">Date:</span>
              ______________________________
            </div>
          </div>
        </div>
      </body>
    </html>
    """

    with output_file.open("wb") as pdf_file:
        result = pisa.CreatePDF(html, dest=pdf_file, encoding="utf-8")

    if result.err:
        raise RuntimeError("Failed to generate document PDF")
