"""Form 16A certificate generation service."""

from datetime import date
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID
import hashlib

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tds.tds_entry import TDSEntry
from app.repositories.tds.tds_entry_repo import TDSEntryRepository
from app.repositories.tds.tds_section_repo import TDSSectionRepository
from app.core.constants import TDSChallanStatus
from app.core.exceptions import NotFoundException, ValidationException


class Form16ACertificate:
    """Form 16A certificate data structure."""

    def __init__(
        self,
        certificate_number: str,
        deductor_tan: str,
        deductor_name: str,
        deductor_address: str,
        deductee_pan: str,
        deductee_name: str,
        deductee_address: str,
        financial_year: str,
        assessment_year: str,
        period_from: date,
        period_to: date,
        tds_section_code: str,
        tds_section_name: str,
        total_amount_paid: Decimal,
        total_tds_deducted: Decimal,
        total_tds_deposited: Decimal,
        transactions: List[dict],
        challans: List[dict],
        generated_date: date,
    ):
        self.certificate_number = certificate_number
        self.deductor_tan = deductor_tan
        self.deductor_name = deductor_name
        self.deductor_address = deductor_address
        self.deductee_pan = deductee_pan
        self.deductee_name = deductee_name
        self.deductee_address = deductee_address
        self.financial_year = financial_year
        self.assessment_year = assessment_year
        self.period_from = period_from
        self.period_to = period_to
        self.tds_section_code = tds_section_code
        self.tds_section_name = tds_section_name
        self.total_amount_paid = total_amount_paid
        self.total_tds_deducted = total_tds_deducted
        self.total_tds_deposited = total_tds_deposited
        self.transactions = transactions
        self.challans = challans
        self.generated_date = generated_date


class Form16AService:
    """Service for generating Form 16A certificates."""

    WORKING_SUMMARY_STATUS = "GENERATED_SUMMARY"
    LEGAL_STATUS = "NOT_TRACES_ISSUED"
    SOURCE = "SYSTEM_GENERATED_SUMMARY"
    COMPLIANCE_NOTE = (
        "System-generated working summary. Use TRACES-issued Form 16A as the legal certificate."
    )

    def __init__(self, session: AsyncSession):
        self.session = session
        self.entry_repo = TDSEntryRepository(session)
        self.section_repo = TDSSectionRepository(session)

    def _get_assessment_year(self, financial_year: str) -> str:
        """Get assessment year from financial year."""
        year_start = int(financial_year.split("-")[0])
        return f"{year_start + 1}-{str(year_start + 2)[-2:]}"

    def _get_quarter_dates(self, financial_year: str, quarter: str) -> Tuple[date, date]:
        """Get start and end dates for a quarter."""
        year_start = int(financial_year.split("-")[0])

        quarter_dates = {
            "Q1": (date(year_start, 4, 1), date(year_start, 6, 30)),
            "Q2": (date(year_start, 7, 1), date(year_start, 9, 30)),
            "Q3": (date(year_start, 10, 1), date(year_start, 12, 31)),
            "Q4": (date(year_start + 1, 1, 1), date(year_start + 1, 3, 31)),
        }
        return quarter_dates.get(quarter, (None, None))

    def _generate_certificate_number(
        self,
        organization_id: UUID,
        deductee_pan: str,
        financial_year: str,
        quarter: str,
        sequence: int,
    ) -> str:
        """Generate unique certificate number."""
        # Format: TAN-PAN-FY-Q-SEQ
        hash_input = f"{organization_id}-{deductee_pan}-{financial_year}-{quarter}-{sequence}"
        short_hash = hashlib.md5(hash_input.encode()).hexdigest()[:6].upper()
        return f"16A-{financial_year.replace('-', '')}-{quarter}-{short_hash}"

    async def get_deductees_for_certificates(
        self,
        organization_id: UUID,
        financial_year: str,
        quarter: str,
    ) -> List[dict]:
        """Get list of deductees eligible for Form 16A in a quarter."""
        period_from, period_to = self._get_quarter_dates(financial_year, quarter)
        if not period_from:
            raise ValidationException(f"Invalid quarter: {quarter}")

        # Get unique deductees with aggregated TDS
        query = (
            select(
                TDSEntry.deductee_pan,
                TDSEntry.deductee_name,
                TDSEntry.tds_section_id,
                func.sum(TDSEntry.base_amount).label("total_amount_paid"),
                func.sum(TDSEntry.total_tds).label("total_tds_deducted"),
                func.count(TDSEntry.id).label("transaction_count"),
            )
            .where(
                and_(
                    TDSEntry.organization_id == organization_id,
                    TDSEntry.deduction_date >= period_from,
                    TDSEntry.deduction_date <= period_to,
                    TDSEntry.is_active == True,
                    TDSEntry.challan_status.in_([TDSChallanStatus.PAID, TDSChallanStatus.VERIFIED]),
                )
            )
            .group_by(
                TDSEntry.deductee_pan,
                TDSEntry.deductee_name,
                TDSEntry.tds_section_id,
            )
            .order_by(TDSEntry.deductee_name)
        )

        result = await self.session.execute(query)
        rows = result.all()

        deductees = []
        for row in rows:
            section = await self.section_repo.get(row.tds_section_id)
            deductees.append(
                {
                    "deductee_pan": row.deductee_pan,
                    "deductee_name": row.deductee_name,
                    "tds_section_id": row.tds_section_id,
                    "tds_section_code": section.section_code if section else None,
                    "tds_section_name": section.section_name if section else None,
                    "total_amount_paid": row.total_amount_paid,
                    "total_tds_deducted": row.total_tds_deducted,
                    "transaction_count": row.transaction_count,
                }
            )

        return deductees

    async def generate_certificate(
        self,
        organization_id: UUID,
        deductee_pan: str,
        tds_section_id: UUID,
        financial_year: str,
        quarter: str,
    ) -> Form16ACertificate:
        """Generate Form 16A certificate for a deductee."""
        period_from, period_to = self._get_quarter_dates(financial_year, quarter)
        if not period_from:
            raise ValidationException(f"Invalid quarter: {quarter}")

        # Get TDS section
        section = await self.section_repo.get(tds_section_id)
        if not section:
            raise NotFoundException("TDS section not found")

        # Get all entries for this deductee in the period
        query = (
            select(TDSEntry)
            .where(
                and_(
                    TDSEntry.organization_id == organization_id,
                    TDSEntry.deductee_pan == deductee_pan,
                    TDSEntry.tds_section_id == tds_section_id,
                    TDSEntry.deduction_date >= period_from,
                    TDSEntry.deduction_date <= period_to,
                    TDSEntry.is_active == True,
                    TDSEntry.challan_status.in_([TDSChallanStatus.PAID, TDSChallanStatus.VERIFIED]),
                )
            )
            .order_by(TDSEntry.deduction_date)
        )
        result = await self.session.execute(query)
        entries = list(result.scalars().all())

        if not entries:
            raise NotFoundException(
                f"No TDS entries found for {deductee_pan} in {quarter} {financial_year}"
            )

        # Get organization details
        first_entry = entries[0]
        org = first_entry.organization

        # Build transactions list
        transactions = []
        for entry in entries:
            transactions.append(
                {
                    "date": entry.deduction_date,
                    "amount_paid": float(entry.base_amount),
                    "tds_deducted": float(entry.tds_amount),
                    "surcharge": float(entry.surcharge),
                    "cess": float(entry.cess),
                    "total_tds": float(entry.total_tds),
                    "rate": float(entry.tds_rate),
                }
            )

        # Build challans list (unique challans)
        challans = {}
        for entry in entries:
            if entry.challan_number and entry.challan_number not in challans:
                challans[entry.challan_number] = {
                    "challan_number": entry.challan_number,
                    "bsr_code": entry.bsr_code,
                    "date": entry.challan_date,
                    "bank_name": entry.bank_name,
                }

        # Calculate totals
        total_amount_paid = sum(e.base_amount for e in entries)
        total_tds_deducted = sum(e.total_tds for e in entries)

        # Generate certificate number
        certificate_number = self._generate_certificate_number(
            organization_id,
            deductee_pan,
            financial_year,
            quarter,
            1,
        )

        # Update entries with certificate info
        for entry in entries:
            entry.certificate_number = certificate_number
            entry.certificate_date = date.today()

        await self.session.flush()

        return Form16ACertificate(
            certificate_number=certificate_number,
            deductor_tan=getattr(org, "tan", "") or "",
            deductor_name=org.name,
            deductor_address=getattr(org, "reg_address_line1", "") or "",
            deductee_pan=deductee_pan,
            deductee_name=first_entry.deductee_name,
            deductee_address=first_entry.deductee_address or "",
            financial_year=financial_year,
            assessment_year=self._get_assessment_year(financial_year),
            period_from=period_from,
            period_to=period_to,
            tds_section_code=section.section_code,
            tds_section_name=section.section_name,
            total_amount_paid=total_amount_paid,
            total_tds_deducted=total_tds_deducted,
            total_tds_deposited=total_tds_deducted,  # Assuming deposited = deducted
            transactions=transactions,
            challans=list(challans.values()),
            generated_date=date.today(),
        )

    async def generate_bulk_certificates(
        self,
        organization_id: UUID,
        financial_year: str,
        quarter: str,
    ) -> List[Form16ACertificate]:
        """Generate Form 16A certificates for all eligible deductees."""
        deductees = await self.get_deductees_for_certificates(
            organization_id,
            financial_year,
            quarter,
        )

        certificates = []
        for deductee in deductees:
            if deductee["deductee_pan"]:  # Only if PAN is available
                try:
                    cert = await self.generate_certificate(
                        organization_id,
                        deductee["deductee_pan"],
                        deductee["tds_section_id"],
                        financial_year,
                        quarter,
                    )
                    certificates.append(cert)
                except Exception:
                    # Log error but continue with other certificates
                    pass

        return certificates

    def generate_certificate_html(self, certificate: Form16ACertificate) -> str:
        """Generate HTML representation of Form 16A certificate."""
        transactions_html = ""
        for txn in certificate.transactions:
            transactions_html += f"""
            <tr>
                <td>{txn['date']}</td>
                <td style="text-align: right;">{txn['amount_paid']:,.2f}</td>
                <td style="text-align: right;">{txn['tds_deducted']:,.2f}</td>
                <td style="text-align: right;">{txn['surcharge']:,.2f}</td>
                <td style="text-align: right;">{txn['cess']:,.2f}</td>
                <td style="text-align: right;">{txn['total_tds']:,.2f}</td>
            </tr>
            """

        challans_html = ""
        for challan in certificate.challans:
            challans_html += f"""
            <tr>
                <td>{challan['challan_number']}</td>
                <td>{challan['bsr_code']}</td>
                <td>{challan['date']}</td>
                <td>{challan['bank_name']}</td>
            </tr>
            """

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Form 16A - TDS Certificate</title>
    <style>
        body {{ font-family: Arial, sans-serif; font-size: 12px; margin: 20px; }}
        .header {{ text-align: center; margin-bottom: 20px; }}
        .title {{ font-size: 18px; font-weight: bold; }}
        .subtitle {{ font-size: 14px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        th, td {{ border: 1px solid #000; padding: 5px; }}
        th {{ background-color: #f0f0f0; }}
        .section {{ margin: 15px 0; }}
        .section-title {{ font-weight: bold; margin-bottom: 5px; }}
        .totals {{ font-weight: bold; }}
        .footer {{ margin-top: 30px; text-align: center; font-size: 10px; }}
    </style>
</head>
<body>
    <div class="header">
        <div class="title">FORM NO. 16A</div>
        <div class="subtitle">Certificate under section 203 of the Income-tax Act, 1961</div>
        <div class="subtitle">for tax deducted at source</div>
    </div>

    <div class="section">
        <table>
            <tr>
                <td width="50%">
                    <strong>Certificate No:</strong> {certificate.certificate_number}<br>
                    <strong>Date:</strong> {certificate.generated_date}
                </td>
                <td width="50%">
                    <strong>Financial Year:</strong> {certificate.financial_year}<br>
                    <strong>Assessment Year:</strong> {certificate.assessment_year}
                </td>
            </tr>
        </table>
    </div>

    <div class="section">
        <div class="section-title">PART A - Details of Deductor and Deductee</div>
        <table>
            <tr>
                <td width="50%">
                    <strong>Deductor Details:</strong><br>
                    TAN: {certificate.deductor_tan}<br>
                    Name: {certificate.deductor_name}<br>
                    Address: {certificate.deductor_address}
                </td>
                <td width="50%">
                    <strong>Deductee Details:</strong><br>
                    PAN: {certificate.deductee_pan}<br>
                    Name: {certificate.deductee_name}<br>
                    Address: {certificate.deductee_address}
                </td>
            </tr>
        </table>
    </div>

    <div class="section">
        <div class="section-title">PART B - Details of Tax Deducted and Deposited</div>
        <p><strong>Section:</strong> {certificate.tds_section_code} - {certificate.tds_section_name}</p>
        <p><strong>Period:</strong> {certificate.period_from} to {certificate.period_to}</p>

        <table>
            <thead>
                <tr>
                    <th>Date of Payment/Credit</th>
                    <th>Amount Paid/Credited (Rs.)</th>
                    <th>TDS Deducted (Rs.)</th>
                    <th>Surcharge (Rs.)</th>
                    <th>Cess (Rs.)</th>
                    <th>Total TDS (Rs.)</th>
                </tr>
            </thead>
            <tbody>
                {transactions_html}
                <tr class="totals">
                    <td><strong>TOTAL</strong></td>
                    <td style="text-align: right;"><strong>{float(certificate.total_amount_paid):,.2f}</strong></td>
                    <td colspan="4" style="text-align: right;"><strong>{float(certificate.total_tds_deducted):,.2f}</strong></td>
                </tr>
            </tbody>
        </table>
    </div>

    <div class="section">
        <div class="section-title">Challan Details</div>
        <table>
            <thead>
                <tr>
                    <th>Challan No.</th>
                    <th>BSR Code</th>
                    <th>Date</th>
                    <th>Bank Name</th>
                </tr>
            </thead>
            <tbody>
                {challans_html}
            </tbody>
        </table>
    </div>

    <div class="section">
        <p><strong>Total Tax Deducted:</strong> Rs. {float(certificate.total_tds_deducted):,.2f}</p>
        <p><strong>Total Tax Deposited:</strong> Rs. {float(certificate.total_tds_deposited):,.2f}</p>
    </div>

    <div class="section" style="margin-top: 40px;">
        <p>I, _________________________, son/daughter of _________________________</p>
        <p>working as _________________________ (designation) certify that a sum of</p>
        <p>Rs. {float(certificate.total_tds_deducted):,.2f} (Rupees _________________________ only)</p>
        <p>has been deducted at source and paid to the credit of the Central Government.</p>
        <br><br>
        <p style="text-align: right;">
            Signature of the person responsible for deducting tax at source<br>
            Name: _________________________<br>
            Designation: _________________________<br>
            Date: _________________________
        </p>
    </div>

    <div class="footer">
        <p>This is a computer-generated certificate.</p>
        <p>Generated on: {certificate.generated_date}</p>
    </div>
</body>
</html>
        """
        return html

    async def get_certificate_by_number(
        self,
        organization_id: UUID,
        certificate_number: str,
    ) -> Optional[dict]:
        """Get certificate details by certificate number."""
        query = (
            select(TDSEntry)
            .where(
                and_(
                    TDSEntry.organization_id == organization_id,
                    TDSEntry.certificate_number == certificate_number,
                    TDSEntry.is_active == True,
                )
            )
            .order_by(TDSEntry.deduction_date)
        )
        result = await self.session.execute(query)
        entries = list(result.scalars().all())

        if not entries:
            return None

        first_entry = entries[0]
        section = await self.section_repo.get(first_entry.tds_section_id)

        return {
            "certificate_number": certificate_number,
            "certificate_date": first_entry.certificate_date,
            "deductee_pan": first_entry.deductee_pan,
            "deductee_name": first_entry.deductee_name,
            "tds_section_code": section.section_code if section else None,
            "total_amount_paid": sum(e.base_amount for e in entries),
            "total_tds_deducted": sum(e.total_tds for e in entries),
            "entry_count": len(entries),
            "artifact_status": self.WORKING_SUMMARY_STATUS,
            "legal_status": self.LEGAL_STATUS,
            "source": self.SOURCE,
            "compliance_note": self.COMPLIANCE_NOTE,
        }

    async def get_generated_certificates(
        self,
        organization_id: UUID,
        financial_year: str,
        quarter: Optional[str] = None,
    ) -> List[dict]:
        """Get list of generated certificates."""
        period_from, period_to = None, None
        if quarter:
            period_from, period_to = self._get_quarter_dates(financial_year, quarter)

        conditions = [
            TDSEntry.organization_id == organization_id,
            TDSEntry.certificate_number.isnot(None),
            TDSEntry.is_active == True,
        ]

        if period_from and period_to:
            conditions.extend(
                [
                    TDSEntry.deduction_date >= period_from,
                    TDSEntry.deduction_date <= period_to,
                ]
            )

        query = (
            select(
                TDSEntry.certificate_number,
                TDSEntry.certificate_date,
                TDSEntry.deductee_pan,
                TDSEntry.deductee_name,
                TDSEntry.tds_section_id,
                func.sum(TDSEntry.base_amount).label("total_amount_paid"),
                func.sum(TDSEntry.total_tds).label("total_tds_deducted"),
                func.count(TDSEntry.id).label("entry_count"),
            )
            .where(and_(*conditions))
            .group_by(
                TDSEntry.certificate_number,
                TDSEntry.certificate_date,
                TDSEntry.deductee_pan,
                TDSEntry.deductee_name,
                TDSEntry.tds_section_id,
            )
            .order_by(TDSEntry.certificate_date.desc())
        )

        result = await self.session.execute(query)
        rows = result.all()

        certificates = []
        for row in rows:
            section = await self.section_repo.get(row.tds_section_id)
            certificates.append(
                {
                    "certificate_number": row.certificate_number,
                    "certificate_date": row.certificate_date,
                    "deductee_pan": row.deductee_pan,
                    "deductee_name": row.deductee_name,
                    "tds_section_code": section.section_code if section else None,
                    "tds_section_name": section.section_name if section else None,
                    "total_amount_paid": row.total_amount_paid,
                    "total_tds_deducted": row.total_tds_deducted,
                    "entry_count": row.entry_count,
                    "artifact_status": self.WORKING_SUMMARY_STATUS,
                    "legal_status": self.LEGAL_STATUS,
                    "source": self.SOURCE,
                    "compliance_note": self.COMPLIANCE_NOTE,
                }
            )

        return certificates
