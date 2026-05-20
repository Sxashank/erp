"""Small dependency-free export helpers.

These helpers intentionally use only the Python standard library. They are
for operational reports where we need a real downloadable PDF/XLSX without
adding renderer dependencies to the backend image.
"""

from __future__ import annotations

import html
import io
import textwrap
import zipfile
from collections.abc import Iterable, Sequence


def _xml(text: object) -> str:
    return html.escape("" if text is None else str(text), quote=True)


def build_xlsx(rows: Sequence[Sequence[object]], sheet_name: str = "Report") -> bytes:
    """Build a minimal XLSX workbook with one inline-string worksheet."""
    sheet_rows: list[str] = []
    for row_index, row in enumerate(rows, start=1):
        cells: list[str] = []
        for col_index, value in enumerate(row, start=1):
            cell_ref = f"{_column_name(col_index)}{row_index}"
            cells.append(
                f'<c r="{cell_ref}" t="inlineStr"><is><t>{_xml(value)}</t></is></c>'
            )
        sheet_rows.append(f'<row r="{row_index}">{"".join(cells)}</row>')

    safe_sheet_name = _xml(sheet_name[:31] or "Report")
    sheet_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        "<sheetData>"
        f"{''.join(sheet_rows)}"
        "</sheetData>"
        "</worksheet>"
    )
    workbook_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f'<sheets><sheet name="{safe_sheet_name}" sheetId="1" r:id="rId1"/></sheets>'
        "</workbook>"
    )
    rels_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="xl/workbook.xml"/>'
        "</Relationships>"
    )
    workbook_rels_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
        'Target="worksheets/sheet1.xml"/>'
        "</Relationships>"
    )
    content_types_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/worksheets/sheet1.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        "</Types>"
    )

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types_xml)
        archive.writestr("_rels/.rels", rels_xml)
        archive.writestr("xl/workbook.xml", workbook_xml)
        archive.writestr("xl/_rels/workbook.xml.rels", workbook_rels_xml)
        archive.writestr("xl/worksheets/sheet1.xml", sheet_xml)
    return buffer.getvalue()


def build_text_pdf(title: str, lines: Iterable[object]) -> bytes:
    """Build a simple text PDF with A4 pages and a standard Helvetica font."""
    page_lines: list[list[str]] = []
    current: list[str] = []
    wrapped_lines: list[str] = []
    for raw_line in lines:
        text = "" if raw_line is None else str(raw_line)
        wrapped = textwrap.wrap(text, width=96) or [""]
        wrapped_lines.extend(wrapped)

    for line in wrapped_lines:
        if len(current) >= 46:
            page_lines.append(current)
            current = []
        current.append(line)
    if current or not page_lines:
        page_lines.append(current)

    objects: list[bytes] = []
    page_object_ids: list[int] = []
    content_object_ids: list[int] = []
    font_object_id = 3 + (len(page_lines) * 2)

    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    kids = " ".join(f"{3 + index * 2} 0 R" for index in range(len(page_lines)))
    objects.append(f"<< /Type /Pages /Kids [{kids}] /Count {len(page_lines)} >>".encode())

    for page_index, lines_for_page in enumerate(page_lines):
        page_id = 3 + page_index * 2
        content_id = page_id + 1
        page_object_ids.append(page_id)
        content_object_ids.append(content_id)
        content = _pdf_page_content(title, lines_for_page, page_index + 1, len(page_lines))
        objects.append(
            (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
                f"/Resources << /Font << /F1 {font_object_id} 0 R >> >> "
                f"/Contents {content_id} 0 R >>"
            ).encode()
        )
        objects.append(
            f"<< /Length {len(content)} >>\nstream\n".encode() + content + b"\nendstream"
        )

    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for object_number, body in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{object_number} 0 obj\n".encode())
        pdf.extend(body)
        pdf.extend(b"\nendobj\n")

    xref_start = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode())
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode())
    pdf.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_start}\n%%EOF\n"
        ).encode()
    )
    return bytes(pdf)


def _column_name(index: int) -> str:
    name = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        name = chr(65 + remainder) + name
    return name


def _pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _pdf_page_content(title: str, lines: Sequence[str], page: int, total_pages: int) -> bytes:
    commands = ["BT", "/F1 14 Tf", "50 800 Td", f"({_pdf_escape(title)}) Tj"]
    commands.extend(["/F1 9 Tf", "0 -22 Td"])
    for line in lines:
        commands.append(f"({_pdf_escape(line)}) Tj")
        commands.append("0 -14 Td")
    commands.extend(["/F1 8 Tf", "0 -18 Td", f"(Page {page} of {total_pages}) Tj", "ET"])
    return "\n".join(commands).encode("latin-1", errors="replace")
