"""PDF generation helpers for portal documents.

Phase-2 fix: replaces the 0-byte placeholder in
``services/portal/document_service.py::generate_account_statement``.

Reportlab is the chosen library — pure-Python, no headless-browser
dependency, and the only PDF generator already pulled into the platform
(via ``requirements.txt``).
"""

from __future__ import annotations

import io
from datetime import date
from decimal import Decimal
from typing import Iterable, Sequence
from uuid import UUID

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def _fmt_amount(value: Decimal | float | int | None) -> str:
    if value is None:
        return "—"
    return f"₹ {Decimal(value):,.2f}"


def _fmt_date(value: date | None) -> str:
    if value is None:
        return "—"
    return value.strftime("%d %b %Y")


def render_account_statement_pdf(
    *,
    organization_name: str,
    organization_address: str | None,
    borrower_name: str,
    loan_account_number: str,
    loan_account_id: UUID,
    from_date: date,
    to_date: date,
    opening_balance: Decimal,
    closing_balance: Decimal,
    transactions: Sequence[dict],
) -> bytes:
    """Render a borrower-facing loan account statement PDF.

    ``transactions`` items are dicts with keys: date, particulars, debit,
    credit, balance, reference.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=18 * mm,
        title=f"Account Statement - {loan_account_number}",
        author=organization_name,
    )

    styles = getSampleStyleSheet()
    style_title = ParagraphStyle(
        "Title",
        parent=styles["Heading1"],
        fontSize=18,
        spaceAfter=4,
    )
    style_subtitle = ParagraphStyle(
        "Subtitle",
        parent=styles["Heading2"],
        fontSize=11,
        textColor=colors.HexColor("#475569"),
        spaceAfter=12,
    )
    style_label = ParagraphStyle(
        "Label",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#64748b"),
    )
    style_value = ParagraphStyle(
        "Value",
        parent=styles["Normal"],
        fontSize=10,
    )

    flow = []

    flow.append(Paragraph(organization_name, style_title))
    if organization_address:
        flow.append(Paragraph(organization_address, style_subtitle))

    flow.append(Paragraph("<b>Account Statement</b>", styles["Heading2"]))
    flow.append(
        Paragraph(
            f"Period: {_fmt_date(from_date)} — {_fmt_date(to_date)}",
            style_subtitle,
        )
    )

    # Borrower / account block
    info_table = Table(
        [
            [
                Paragraph("Borrower", style_label),
                Paragraph(borrower_name, style_value),
                Paragraph("Loan A/c", style_label),
                Paragraph(loan_account_number, style_value),
            ],
            [
                Paragraph("Opening balance", style_label),
                Paragraph(_fmt_amount(opening_balance), style_value),
                Paragraph("Closing balance", style_label),
                Paragraph(_fmt_amount(closing_balance), style_value),
            ],
        ],
        colWidths=[28 * mm, 60 * mm, 28 * mm, 60 * mm],
    )
    info_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#e2e8f0")),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    flow.append(info_table)
    flow.append(Spacer(1, 8 * mm))

    # Transactions table
    header = ["Date", "Particulars", "Debit", "Credit", "Balance", "Reference"]
    rows: list[list[str]] = [header]
    for tx in transactions:
        rows.append(
            [
                _fmt_date(tx.get("date")),
                str(tx.get("particulars") or "—"),
                _fmt_amount(tx.get("debit")) if tx.get("debit") else "—",
                _fmt_amount(tx.get("credit")) if tx.get("credit") else "—",
                _fmt_amount(tx.get("balance")),
                str(tx.get("reference") or ""),
            ]
        )

    if not transactions:
        rows.append(["—", "No transactions in this period", "—", "—", "—", ""])

    txn_table = Table(
        rows,
        colWidths=[22 * mm, 60 * mm, 25 * mm, 25 * mm, 28 * mm, 26 * mm],
        repeatRows=1,
    )
    txn_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTSIZE", (0, 0), (-1, 0), 9),
                ("FONTSIZE", (0, 1), (-1, -1), 8.5),
                ("ALIGN", (2, 1), (4, -1), "RIGHT"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#e2e8f0")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    flow.append(txn_table)
    flow.append(Spacer(1, 10 * mm))

    flow.append(
        Paragraph(
            "<i>This is a system-generated statement and does not require a "
            "signature. For queries, please contact your relationship manager.</i>",
            style_subtitle,
        )
    )

    doc.build(flow)
    return buffer.getvalue()


def render_interest_certificate_pdf(
    *,
    organization_name: str,
    organization_address: str | None,
    borrower_name: str,
    borrower_pan: str | None,
    loan_account_number: str,
    financial_year: str,
    interest_paid: Decimal,
    principal_repaid: Decimal,
    closing_balance: Decimal,
    issued_on: date,
) -> bytes:
    """Render an income-tax interest certificate (24B) PDF."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=18 * mm,
        bottomMargin=20 * mm,
        title=f"Interest Certificate - {loan_account_number} FY{financial_year}",
        author=organization_name,
    )
    styles = getSampleStyleSheet()
    flow = []
    flow.append(Paragraph(organization_name, styles["Title"]))
    if organization_address:
        flow.append(Paragraph(organization_address, styles["Normal"]))
    flow.append(Spacer(1, 6 * mm))
    flow.append(Paragraph("<b>INTEREST CERTIFICATE</b>", styles["Heading2"]))
    flow.append(
        Paragraph(
            f"Financial Year {financial_year} (Section 24(b) of the Income Tax Act, 1961)",
            styles["Normal"],
        )
    )
    flow.append(Spacer(1, 8 * mm))

    rows = [
        ["Borrower name", borrower_name],
        ["PAN", borrower_pan or "—"],
        ["Loan account number", loan_account_number],
        ["Financial year", financial_year],
        ["Interest paid", _fmt_amount(interest_paid)],
        ["Principal repaid", _fmt_amount(principal_repaid)],
        ["Closing balance as on 31-Mar", _fmt_amount(closing_balance)],
        ["Issued on", _fmt_date(issued_on)],
    ]
    info = Table(rows, colWidths=[60 * mm, 100 * mm])
    info.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#e2e8f0")),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f1f5f9")),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    flow.append(info)
    flow.append(Spacer(1, 10 * mm))
    flow.append(
        Paragraph(
            "<i>This certificate is issued for tax-filing purposes and is a "
            "system-generated document. No signature required.</i>",
            styles["Normal"],
        )
    )

    doc.build(flow)
    return buffer.getvalue()


# ============================================================================
# Phase C — template-driven renderers
# ============================================================================
#
# These renderers read the template body from ``mst_document_template`` (a
# CertificateService method provides the body+merge fields) and render a
# polished A4 PDF. They share one generic engine + thin wrappers per
# certificate type so the visual identity stays consistent.
# ============================================================================


import re as _re


def _expand_merge_fields(body: str, merge_data: dict) -> str:
    """Replace ``{{key}}`` placeholders with values from merge_data.

    Markdown-aware: leaves any unmatched placeholders intact so the
    template-author can see what was missed at preview time.
    """

    def replace(match: "_re.Match[str]") -> str:
        key = match.group(1).strip()
        value = merge_data.get(key)
        if value is None:
            return match.group(0)
        if isinstance(value, Decimal):
            return _fmt_amount(value)
        if isinstance(value, date):
            return _fmt_date(value)
        return str(value)

    return _re.sub(r"\{\{\s*([a-zA-Z0-9_\.]+)\s*\}\}", replace, body)


def render_template_pdf(
    *,
    organization_name: str,
    organization_address: str | None,
    title: str,
    body_markdown: str,
    merge_data: dict,
    summary_table: list[tuple[str, str]] | None = None,
    footer_note: str | None = None,
    certificate_number: str | None = None,
) -> bytes:
    """Generic template-driven PDF renderer.

    Args:
        organization_name: NBFC name in the header.
        organization_address: Optional address line.
        title: Bold heading printed under the org name.
        body_markdown: Template body (Markdown). ``{{merge_fields}}`` get
            expanded from merge_data. Headings (``# ``, ``## ``) and bold
            (``**…**``) translate to platypus paragraphs.
        merge_data: Dict of values to substitute.
        summary_table: Optional key/value table printed below the body
            (e.g. amount breakup, dates, identifiers).
        footer_note: Optional italic line printed at the bottom.
        certificate_number: Optional id printed top-right.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=18 * mm,
        bottomMargin=20 * mm,
        title=title,
        author=organization_name,
    )
    styles = getSampleStyleSheet()
    style_title = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontSize=18,
        spaceAfter=4,
    )
    style_subtitle = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Heading2"],
        fontSize=11,
        textColor=colors.HexColor("#475569"),
        spaceAfter=12,
    )

    flow: list = []

    # Header: org name + (optional) certificate number row
    flow.append(Paragraph(organization_name, style_title))
    if organization_address:
        flow.append(Paragraph(organization_address, style_subtitle))
    if certificate_number:
        flow.append(
            Paragraph(
                f"<i>Certificate no.: {certificate_number}</i>",
                styles["Normal"],
            )
        )
    flow.append(Spacer(1, 4 * mm))
    flow.append(Paragraph(f"<b>{title}</b>", styles["Heading2"]))
    flow.append(Spacer(1, 6 * mm))

    # Body — expand merge fields then translate basic Markdown
    expanded = _expand_merge_fields(body_markdown or "", merge_data)
    for line in expanded.splitlines():
        if not line.strip():
            flow.append(Spacer(1, 3 * mm))
            continue
        if line.startswith("## "):
            flow.append(Paragraph(f"<b>{line[3:].strip()}</b>", styles["Heading3"]))
        elif line.startswith("# "):
            flow.append(Paragraph(f"<b>{line[2:].strip()}</b>", styles["Heading2"]))
        else:
            # Bold **…** → <b>…</b>
            html = _re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", line)
            flow.append(Paragraph(html, styles["Normal"]))

    flow.append(Spacer(1, 6 * mm))

    if summary_table:
        info = Table(summary_table, colWidths=[60 * mm, 110 * mm])
        info.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#e2e8f0")),
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f1f5f9")),
                    ("FONTSIZE", (0, 0), (-1, -1), 9.5),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        flow.append(info)
        flow.append(Spacer(1, 6 * mm))

    if footer_note:
        flow.append(Paragraph(f"<i>{footer_note}</i>", styles["Normal"]))

    doc.build(flow)
    return buffer.getvalue()


def render_kfs_pdf(
    *,
    organization_name: str,
    organization_address: str | None,
    body_markdown: str,
    merge_data: dict,
    certificate_number: str,
    summary: dict,
) -> bytes:
    """Key Facts Statement (RBI Annex A — Oct-2024 mandate)."""
    summary_table = [
        ["Borrower", str(summary.get("borrower_name", "—"))],
        ["Loan amount", _fmt_amount(summary.get("loan_amount"))],
        ["Tenure (months)", str(summary.get("tenure_months", "—"))],
        ["Interest rate", f"{summary.get('interest_rate', '—')} %"],
        ["Rate type", str(summary.get("rate_type", "—"))],
        ["EMI / instalment", _fmt_amount(summary.get("instalment_amount"))],
        ["APR (computed)", f"{summary.get('apr', '—')} %"],
        ["Total interest payable", _fmt_amount(summary.get("total_interest"))],
        ["Total amount payable", _fmt_amount(summary.get("total_payable"))],
        ["Cooling-off period (days)", str(summary.get("cooling_off_days", 3))],
    ]
    return render_template_pdf(
        organization_name=organization_name,
        organization_address=organization_address,
        title="KEY FACTS STATEMENT",
        body_markdown=body_markdown,
        merge_data=merge_data,
        summary_table=summary_table,
        footer_note=(
            "Issued per RBI Master Direction on Key Facts Statement for Loans "
            "& Advances dated 15-Apr-2024. Please review carefully and "
            "acknowledge on the portal before accepting the sanction."
        ),
        certificate_number=certificate_number,
    )


def render_no_dues_certificate_pdf(
    *,
    organization_name: str,
    organization_address: str | None,
    body_markdown: str,
    merge_data: dict,
    certificate_number: str,
    borrower_name: str,
    loan_account_number: str,
    closure_date: date,
    period_start: date,
) -> bytes:
    """No-Dues Certificate issued at closure."""
    summary_table = [
        ["Borrower", borrower_name],
        ["Loan account", loan_account_number],
        ["Relationship period", f"{_fmt_date(period_start)} – {_fmt_date(closure_date)}"],
        ["Status", "FULLY SETTLED"],
        ["Closure date", _fmt_date(closure_date)],
    ]
    return render_template_pdf(
        organization_name=organization_name,
        organization_address=organization_address,
        title="NO-DUES CERTIFICATE",
        body_markdown=body_markdown,
        merge_data=merge_data,
        summary_table=summary_table,
        footer_note=(
            "This is a system-generated certificate confirming that no "
            "amounts remain outstanding on the above loan account as on the "
            "date stated."
        ),
        certificate_number=certificate_number,
    )


def render_foreclosure_letter_pdf(
    *,
    organization_name: str,
    organization_address: str | None,
    body_markdown: str,
    merge_data: dict,
    certificate_number: str,
    borrower_name: str,
    loan_account_number: str,
    as_of_date: date,
    valid_till: date,
    principal_outstanding: Decimal,
    interest_accrued: Decimal,
    foreclosure_fee: Decimal,
    other_charges: Decimal,
    payment_account_details: str,
) -> bytes:
    total = (
        (principal_outstanding or Decimal("0"))
        + (interest_accrued or Decimal("0"))
        + (foreclosure_fee or Decimal("0"))
        + (other_charges or Decimal("0"))
    )
    summary_table = [
        ["Borrower", borrower_name],
        ["Loan account", loan_account_number],
        ["As of date", _fmt_date(as_of_date)],
        ["Principal outstanding", _fmt_amount(principal_outstanding)],
        ["Interest accrued", _fmt_amount(interest_accrued)],
        ["Foreclosure fee", _fmt_amount(foreclosure_fee)],
        ["Other charges", _fmt_amount(other_charges)],
        ["TOTAL PAYABLE", _fmt_amount(total)],
        ["Valid till", _fmt_date(valid_till)],
        ["Payment to", payment_account_details],
    ]
    return render_template_pdf(
        organization_name=organization_name,
        organization_address=organization_address,
        title="FORECLOSURE LETTER",
        body_markdown=body_markdown,
        merge_data=merge_data,
        summary_table=summary_table,
        footer_note=(
            "Once the total amount is received, all charges on the secured "
            "assets will be released and the loan account closed. Original "
            "documents will be released within 30 days per RBI directive "
            "(Sep 2023). For any assistance, please contact your relationship "
            "manager."
        ),
        certificate_number=certificate_number,
    )


def render_balance_confirmation_pdf(
    *,
    organization_name: str,
    organization_address: str | None,
    body_markdown: str,
    merge_data: dict,
    certificate_number: str,
    borrower_name: str,
    loan_account_number: str,
    as_of_date: date,
    principal_outstanding: Decimal,
    interest_outstanding: Decimal,
    total_outstanding: Decimal,
) -> bytes:
    summary_table = [
        ["Borrower", borrower_name],
        ["Loan account", loan_account_number],
        ["As of date", _fmt_date(as_of_date)],
        ["Principal outstanding", _fmt_amount(principal_outstanding)],
        ["Interest outstanding", _fmt_amount(interest_outstanding)],
        ["Total outstanding", _fmt_amount(total_outstanding)],
    ]
    return render_template_pdf(
        organization_name=organization_name,
        organization_address=organization_address,
        title="BALANCE CONFIRMATION",
        body_markdown=body_markdown,
        merge_data=merge_data,
        summary_table=summary_table,
        certificate_number=certificate_number,
    )


def render_charge_release_letter_pdf(
    *,
    organization_name: str,
    organization_address: str | None,
    body_markdown: str,
    merge_data: dict,
    certificate_number: str,
    borrower_name: str,
    loan_account_number: str,
    closure_date: date,
    securities_released: list[str],
) -> bytes:
    summary_table = [
        ["Borrower", borrower_name],
        ["Loan account", loan_account_number],
        ["Closed on", _fmt_date(closure_date)],
        ["Securities released", "; ".join(securities_released) if securities_released else "—"],
    ]
    return render_template_pdf(
        organization_name=organization_name,
        organization_address=organization_address,
        title="CHARGE RELEASE LETTER",
        body_markdown=body_markdown,
        merge_data=merge_data,
        summary_table=summary_table,
        footer_note=(
            "We confirm that the charges created on the above-listed "
            "securities have been released. CERSAI / ROC / NeSL satisfaction "
            "filings have been initiated."
        ),
        certificate_number=certificate_number,
    )


def render_rate_revision_intimation_pdf(
    *,
    organization_name: str,
    organization_address: str | None,
    body_markdown: str,
    merge_data: dict,
    certificate_number: str,
    borrower_name: str,
    loan_account_number: str,
    benchmark_code: str,
    old_rate_percent: Decimal,
    new_rate_percent: Decimal,
    effective_from: date,
    new_emi: Decimal | None,
    new_tenure_months: int | None,
) -> bytes:
    summary_table = [
        ["Borrower", borrower_name],
        ["Loan account", loan_account_number],
        ["Benchmark", benchmark_code],
        ["Previous rate", f"{old_rate_percent}%"],
        ["New rate", f"{new_rate_percent}%"],
        ["Effective from", _fmt_date(effective_from)],
    ]
    if new_emi is not None:
        summary_table.append(["New EMI", _fmt_amount(new_emi)])
    if new_tenure_months is not None:
        summary_table.append(["New tenure (months)", str(new_tenure_months)])
    return render_template_pdf(
        organization_name=organization_name,
        organization_address=organization_address,
        title="RATE REVISION INTIMATION",
        body_markdown=body_markdown,
        merge_data=merge_data,
        summary_table=summary_table,
        footer_note=(
            "Per RBI's EMI-Reset circular, you may elect to (a) increase the "
            "EMI, (b) extend the tenure, or (c) switch to a fixed rate. "
            "Please log in to the portal to record your choice."
        ),
        certificate_number=certificate_number,
    )


def render_demand_notice_pdf(
    *,
    organization_name: str,
    organization_address: str | None,
    body_markdown: str,
    merge_data: dict,
    certificate_number: str,
    borrower_name: str,
    loan_account_number: str,
    overdue_amount: Decimal,
    overdue_since: date,
    cure_period_days: int,
) -> bytes:
    summary_table = [
        ["Borrower", borrower_name],
        ["Loan account", loan_account_number],
        ["Overdue amount", _fmt_amount(overdue_amount)],
        ["Overdue since", _fmt_date(overdue_since)],
        ["Cure period", f"{cure_period_days} days"],
    ]
    return render_template_pdf(
        organization_name=organization_name,
        organization_address=organization_address,
        title="DEMAND NOTICE",
        body_markdown=body_markdown,
        merge_data=merge_data,
        summary_table=summary_table,
        footer_note=(
            "Please regularise the overdue within the cure period stated "
            "above. Failure to do so will lead to further action, including "
            "but not limited to legal proceedings under applicable laws."
        ),
        certificate_number=certificate_number,
    )


def render_principal_paid_certificate_pdf(
    *,
    organization_name: str,
    organization_address: str | None,
    body_markdown: str,
    merge_data: dict,
    certificate_number: str,
    borrower_name: str,
    loan_account_number: str,
    financial_year: str,
    principal_paid: Decimal,
) -> bytes:
    summary_table = [
        ["Borrower", borrower_name],
        ["Loan account", loan_account_number],
        ["Financial year", financial_year],
        ["Principal repaid", _fmt_amount(principal_paid)],
    ]
    return render_template_pdf(
        organization_name=organization_name,
        organization_address=organization_address,
        title="PRINCIPAL REPAYMENT CERTIFICATE",
        body_markdown=body_markdown,
        merge_data=merge_data,
        summary_table=summary_table,
        footer_note="System-generated. No signature required.",
        certificate_number=certificate_number,
    )


def render_provisional_interest_certificate_pdf(
    *,
    organization_name: str,
    organization_address: str | None,
    body_markdown: str,
    merge_data: dict,
    certificate_number: str,
    borrower_name: str,
    loan_account_number: str,
    financial_year: str,
    projected_interest: Decimal,
    projected_principal: Decimal,
) -> bytes:
    summary_table = [
        ["Borrower", borrower_name],
        ["Loan account", loan_account_number],
        ["Financial year (projected)", financial_year],
        ["Projected interest", _fmt_amount(projected_interest)],
        ["Projected principal repayment", _fmt_amount(projected_principal)],
    ]
    return render_template_pdf(
        organization_name=organization_name,
        organization_address=organization_address,
        title="PROVISIONAL INTEREST CERTIFICATE",
        body_markdown=body_markdown,
        merge_data=merge_data,
        summary_table=summary_table,
        footer_note=(
            "Projected figures based on the current EMI schedule. "
            "A final certificate with actual paid amounts will be issued "
            "after the financial year ends."
        ),
        certificate_number=certificate_number,
    )
