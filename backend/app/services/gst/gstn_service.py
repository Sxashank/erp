"""GSTN Portal Service.

Business logic for GST return filing operations including:
- Session management with OTP authentication
- GSTR-1 generation from sales invoices
- GSTR-3B summary generation
- GSTR-2B fetch and ITC reconciliation
"""

import logging
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.gst.gstn_models import (
    GSTNSession,
    GSTReturnFiling,
    GSTItcMismatch,
    GSTR2BData,
    GSTNSessionStatus,
    GSTReturnType,
    GSTReturnStatus,
    ITCMismatchType,
    ITCMismatchResolution,
)
from app.models.gst.gst_registration import GSTRegistration
from app.models.core.integration_config import IntegrationConfig, IntegrationType
from app.integrations.gstn import GSTNClient, GSTNAuthManager
from app.core.encryption import decrypt_value
from app.schemas.gst.gstn import (
    GSTReturnFilingResponse,
    GSTReturnFilingListResponse,
    GSTR1Data,
    GSTR3BData,
    ITCMismatchResponse,
    ITCMismatchListResponse,
    ITCReconciliationSummary,
    GSTR2BInvoiceResponse,
    GSTR2BListResponse,
)

logger = logging.getLogger(__name__)


class GSTNService:
    """Service for GSTN portal operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # Session Management
    # =========================================================================

    async def _get_integration_config(
        self,
        organization_id: UUID,
    ) -> Optional[IntegrationConfig]:
        """Get GSTN integration configuration for organization."""
        query = select(IntegrationConfig).where(
            and_(
                IntegrationConfig.organization_id == organization_id,
                IntegrationConfig.integration_type == IntegrationType.GSTN,
                IntegrationConfig.is_active == True,
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def _get_auth_manager(
        self,
        config: IntegrationConfig,
    ) -> GSTNAuthManager:
        """Create GSTN auth manager from config."""
        config_data = config.config_data
        return GSTNAuthManager(
            asp_id=config_data.get("asp_id"),
            asp_secret=decrypt_value(config_data.get("asp_secret_encrypted")),
            asp_userid=config_data.get("asp_userid"),
            public_key_pem=config_data.get("public_key"),
            sandbox_mode=config.sandbox_mode,
        )

    async def request_otp(
        self,
        organization_id: UUID,
        gst_registration_id: UUID,
        username: str,
        initiated_by: UUID,
    ) -> Dict[str, Any]:
        """Request OTP for GSTN authentication.

        Args:
            organization_id: Organization ID
            gst_registration_id: GST registration ID
            username: GSTN portal username
            initiated_by: User ID initiating the request

        Returns:
            OTP request result with session ID
        """
        # Get GST registration
        gst_reg = await self.db.get(GSTRegistration, gst_registration_id)
        if not gst_reg:
            raise ValueError("GST registration not found")

        # Get integration config
        config = await self._get_integration_config(organization_id)
        if not config:
            raise ValueError("GSTN integration not configured")

        # Create auth manager
        auth_manager = await self._get_auth_manager(config)

        try:
            # Request OTP
            result = await auth_manager.request_otp(gst_reg.gstin, username)

            if result["success"]:
                # Create session record
                session = GSTNSession(
                    organization_id=organization_id,
                    gst_registration_id=gst_registration_id,
                    gstin=gst_reg.gstin,
                    status=GSTNSessionStatus.OTP_PENDING,
                    otp_requested_at=datetime.utcnow(),
                    otp_reference=result.get("otp_reference"),
                    initiated_by=initiated_by,
                )
                self.db.add(session)
                await self.db.commit()
                await self.db.refresh(session)

                return {
                    "success": True,
                    "session_id": str(session.id),
                    "otp_reference": result.get("otp_reference"),
                    "app_key": result.get("raw_app_key"),
                    "message": "OTP sent successfully",
                }
            else:
                return result

        finally:
            await auth_manager.close()

    async def verify_otp(
        self,
        session_id: UUID,
        username: str,
        otp: str,
        app_key: str,
    ) -> Dict[str, Any]:
        """Verify OTP and establish authenticated session.

        Args:
            session_id: Session ID from OTP request
            username: GSTN portal username
            otp: OTP entered by user
            app_key: Application key from OTP request

        Returns:
            Verification result with session details
        """
        # Get session
        session = await self.db.get(GSTNSession, session_id)
        if not session:
            raise ValueError("Session not found")

        if session.status != GSTNSessionStatus.OTP_PENDING:
            raise ValueError("Invalid session state")

        # Get integration config
        config = await self._get_integration_config(session.organization_id)
        if not config:
            raise ValueError("GSTN integration not configured")

        # Create auth manager
        auth_manager = await self._get_auth_manager(config)

        try:
            # Verify OTP
            result = await auth_manager.verify_otp(
                gstin=session.gstin,
                username=username,
                otp=otp,
                otp_reference=session.otp_reference,
                app_key_b64=app_key,
            )

            if result["success"]:
                # Update session with tokens
                session.status = GSTNSessionStatus.ACTIVE
                session.auth_token = result["auth_token"]
                session.sek_key = result["sek"]
                session.token_expires_at = result["token_expires_at"]
                session.last_activity = datetime.utcnow()
                await self.db.commit()

                return {
                    "success": True,
                    "session_id": str(session.id),
                    "expires_at": result["token_expires_at"].isoformat(),
                    "message": "Authentication successful",
                }
            else:
                session.status = GSTNSessionStatus.INVALID
                session.error_message = result.get("message")
                await self.db.commit()
                return result

        finally:
            await auth_manager.close()

    async def get_active_session(
        self,
        organization_id: UUID,
        gstin: str,
    ) -> Optional[GSTNSession]:
        """Get active GSTN session for GSTIN."""
        query = select(GSTNSession).where(
            and_(
                GSTNSession.organization_id == organization_id,
                GSTNSession.gstin == gstin,
                GSTNSession.status == GSTNSessionStatus.ACTIVE,
                GSTNSession.token_expires_at > datetime.utcnow(),
            )
        ).order_by(GSTNSession.created_at.desc())

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def _get_gstn_client(
        self,
        session: GSTNSession,
    ) -> GSTNClient:
        """Create GSTN client from session."""
        config = await self._get_integration_config(session.organization_id)
        if not config:
            raise ValueError("GSTN integration not configured")

        auth_manager = await self._get_auth_manager(config)

        return GSTNClient(
            auth_manager=auth_manager,
            auth_token=session.auth_token,
            sek_b64=session.sek_key,
            gstin=session.gstin,
        )

    # =========================================================================
    # Return Filing Management
    # =========================================================================

    async def get_or_create_return(
        self,
        organization_id: UUID,
        gst_registration_id: UUID,
        return_type: GSTReturnType,
        return_period: str,
        financial_year: str,
    ) -> GSTReturnFiling:
        """Get or create a return filing record."""
        gst_reg = await self.db.get(GSTRegistration, gst_registration_id)
        if not gst_reg:
            raise ValueError("GST registration not found")

        # Check for existing
        query = select(GSTReturnFiling).where(
            and_(
                GSTReturnFiling.organization_id == organization_id,
                GSTReturnFiling.gstin == gst_reg.gstin,
                GSTReturnFiling.return_type == return_type,
                GSTReturnFiling.return_period == return_period,
            )
        )
        result = await self.db.execute(query)
        existing = result.scalar_one_or_none()

        if existing:
            return existing

        # Create new
        filing = GSTReturnFiling(
            organization_id=organization_id,
            gst_registration_id=gst_registration_id,
            gstin=gst_reg.gstin,
            return_type=return_type,
            return_period=return_period,
            financial_year=financial_year,
            status=GSTReturnStatus.NOT_STARTED,
        )
        self.db.add(filing)
        await self.db.commit()
        await self.db.refresh(filing)
        return filing

    async def list_returns(
        self,
        organization_id: UUID,
        gst_registration_id: Optional[UUID] = None,
        return_type: Optional[GSTReturnType] = None,
        financial_year: Optional[str] = None,
        status: Optional[GSTReturnStatus] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> GSTReturnFilingListResponse:
        """List GST return filings."""
        query = select(GSTReturnFiling).where(
            GSTReturnFiling.organization_id == organization_id
        )

        if gst_registration_id:
            query = query.where(GSTReturnFiling.gst_registration_id == gst_registration_id)
        if return_type:
            query = query.where(GSTReturnFiling.return_type == return_type)
        if financial_year:
            query = query.where(GSTReturnFiling.financial_year == financial_year)
        if status:
            query = query.where(GSTReturnFiling.status == status)

        # Count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Paginate
        query = query.order_by(GSTReturnFiling.return_period.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        items = result.scalars().all()

        return GSTReturnFilingListResponse(
            items=[GSTReturnFilingResponse.model_validate(f) for f in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size,
        )

    async def generate_gstr1(
        self,
        organization_id: UUID,
        gst_registration_id: UUID,
        return_period: str,
        financial_year: str,
        prepared_by: UUID,
    ) -> GSTReturnFiling:
        """Generate GSTR-1 from sales invoices.

        Args:
            organization_id: Organization ID
            gst_registration_id: GST registration ID
            return_period: Period in MMYYYY format
            financial_year: e.g., "2024-25"
            prepared_by: User preparing the return

        Returns:
            Updated return filing record
        """
        # Get or create return record
        filing = await self.get_or_create_return(
            organization_id=organization_id,
            gst_registration_id=gst_registration_id,
            return_type=GSTReturnType.GSTR1,
            return_period=return_period,
            financial_year=financial_year,
        )

        # Parse period to get date range
        month = int(return_period[:2])
        year = int(return_period[2:])
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)

        # Fetch sales invoices for the period
        # This would query the sales_invoice table
        # For now, initialize with empty structure
        section_data = {
            "b2b": [],
            "b2cl": [],
            "b2cs": [],
            "cdnr": [],
            "cdnur": [],
            "exp": [],
            "hsn": [],
            "doc": [],
        }

        # TODO: Implement actual invoice fetching and transformation
        # from app.models.ap_ar.sales_invoice import SalesInvoice
        # query = select(SalesInvoice).where(...)

        # Calculate totals
        total_taxable = Decimal("0")
        total_igst = Decimal("0")
        total_cgst = Decimal("0")
        total_sgst = Decimal("0")
        total_cess = Decimal("0")
        b2b_count = 0
        b2c_count = 0
        cdn_count = 0

        # Update filing record
        filing.status = GSTReturnStatus.DRAFT
        filing.section_wise_data = section_data
        filing.total_taxable_value = total_taxable
        filing.total_igst = total_igst
        filing.total_cgst = total_cgst
        filing.total_sgst = total_sgst
        filing.total_cess = total_cess
        filing.total_tax_liability = total_igst + total_cgst + total_sgst + total_cess
        filing.b2b_invoice_count = b2b_count
        filing.b2c_invoice_count = b2c_count
        filing.cdn_count = cdn_count
        filing.invoice_count = b2b_count + b2c_count
        filing.prepared_by = prepared_by

        await self.db.commit()
        await self.db.refresh(filing)

        logger.info(f"Generated GSTR-1 for {filing.gstin}, period {return_period}")
        return filing

    async def generate_gstr3b(
        self,
        organization_id: UUID,
        gst_registration_id: UUID,
        return_period: str,
        financial_year: str,
        prepared_by: UUID,
    ) -> GSTReturnFiling:
        """Generate GSTR-3B summary.

        Args:
            organization_id: Organization ID
            gst_registration_id: GST registration ID
            return_period: Period in MMYYYY format
            financial_year: e.g., "2024-25"
            prepared_by: User preparing the return

        Returns:
            Updated return filing record
        """
        # Get or create return record
        filing = await self.get_or_create_return(
            organization_id=organization_id,
            gst_registration_id=gst_registration_id,
            return_type=GSTReturnType.GSTR3B,
            return_period=return_period,
            financial_year=financial_year,
        )

        # Calculate GSTR-3B summary from vouchers and invoices
        # This aggregates data from:
        # 1. Sales invoices (output tax)
        # 2. Purchase bills (input tax/ITC)
        # 3. Credit/debit notes

        summary_data = {
            "3.1": {  # Outward taxable supplies
                "osup_det": {"txval": 0, "iamt": 0, "camt": 0, "samt": 0, "csamt": 0},
                "osup_zero": {"txval": 0, "iamt": 0, "camt": 0, "samt": 0, "csamt": 0},
                "osup_nil_exmp": {"txval": 0},
                "osup_nongst": {"txval": 0},
            },
            "3.2": {  # Inward supplies attracting reverse charge
                "isup_rev": {"txval": 0, "iamt": 0, "camt": 0, "samt": 0, "csamt": 0},
            },
            "4": {  # Eligible ITC
                "itc_avl": {"iamt": 0, "camt": 0, "samt": 0, "csamt": 0},
                "itc_rev": {"iamt": 0, "camt": 0, "samt": 0, "csamt": 0},
                "itc_net": {"iamt": 0, "camt": 0, "samt": 0, "csamt": 0},
                "itc_inelg": {"iamt": 0, "camt": 0, "samt": 0, "csamt": 0},
            },
            "5": {  # Exempt, nil rated
                "inter_sply_unregd": 0,
                "inter_sply_comp": 0,
                "intra_sply_unregd": 0,
                "intra_sply_comp": 0,
            },
            "6": {  # Payment of tax
                "tax_pbl": {"iamt": 0, "camt": 0, "samt": 0, "csamt": 0},
                "tax_pd_itc": {"iamt": 0, "camt": 0, "samt": 0, "csamt": 0},
                "tax_pd_cash": {"iamt": 0, "camt": 0, "samt": 0, "csamt": 0},
                "interest": 0,
                "late_fee": 0,
            },
        }

        # TODO: Implement actual calculation from invoices

        # Update filing
        filing.status = GSTReturnStatus.DRAFT
        filing.summary_data = summary_data
        filing.total_taxable_value = Decimal("0")
        filing.total_igst = Decimal("0")
        filing.total_cgst = Decimal("0")
        filing.total_sgst = Decimal("0")
        filing.total_cess = Decimal("0")
        filing.total_tax_liability = Decimal("0")
        filing.total_itc_claimed = Decimal("0")
        filing.prepared_by = prepared_by

        await self.db.commit()
        await self.db.refresh(filing)

        logger.info(f"Generated GSTR-3B for {filing.gstin}, period {return_period}")
        return filing

    # =========================================================================
    # GSTR-2B and ITC Reconciliation
    # =========================================================================

    async def fetch_gstr2b(
        self,
        organization_id: UUID,
        gst_registration_id: UUID,
        return_period: str,
        session_id: UUID,
    ) -> Dict[str, Any]:
        """Fetch GSTR-2B data from GSTN.

        Args:
            organization_id: Organization ID
            gst_registration_id: GST registration ID
            return_period: Period in MMYYYY format
            session_id: Active GSTN session ID

        Returns:
            Fetch result with summary
        """
        # Get session
        session = await self.db.get(GSTNSession, session_id)
        if not session or session.status != GSTNSessionStatus.ACTIVE:
            raise ValueError("Invalid or expired session")

        gst_reg = await self.db.get(GSTRegistration, gst_registration_id)
        if not gst_reg:
            raise ValueError("GST registration not found")

        # Get GSTN client
        client = await self._get_gstn_client(session)

        try:
            # Fetch GSTR-2B
            result = await client.get_gstr2b(return_period)

            if not result["success"]:
                return result

            data = result.get("data", {})
            invoices = data.get("docdata", {}).get("b2b", [])

            # Store fetched data
            stored_count = 0
            for supplier in invoices:
                supplier_gstin = supplier.get("ctin")
                supplier_name = supplier.get("trdnm")
                filing_status = supplier.get("cfs")

                for inv in supplier.get("inv", []):
                    # Create or update GSTR2B record
                    gstr2b_record = GSTR2BData(
                        organization_id=organization_id,
                        gst_registration_id=gst_registration_id,
                        return_period=return_period,
                        supplier_gstin=supplier_gstin,
                        supplier_name=supplier_name,
                        supplier_filing_status=filing_status,
                        invoice_number=inv.get("inum"),
                        invoice_date=datetime.strptime(inv.get("dt"), "%d-%m-%Y").date(),
                        invoice_type=inv.get("inv_typ", "R"),
                        place_of_supply=inv.get("pos"),
                        reverse_charge=inv.get("rchrg") == "Y",
                        taxable_value=Decimal(str(inv.get("val", 0))),
                        igst=Decimal(str(inv.get("itms", [{}])[0].get("itm_det", {}).get("iamt", 0))),
                        cgst=Decimal(str(inv.get("itms", [{}])[0].get("itm_det", {}).get("camt", 0))),
                        sgst=Decimal(str(inv.get("itms", [{}])[0].get("itm_det", {}).get("samt", 0))),
                        cess=Decimal(str(inv.get("itms", [{}])[0].get("itm_det", {}).get("csamt", 0))),
                        raw_data=inv,
                    )

                    # Merge (upsert)
                    await self.db.merge(gstr2b_record)
                    stored_count += 1

            await self.db.commit()

            return {
                "success": True,
                "invoices_fetched": stored_count,
                "message": f"Fetched {stored_count} invoices from GSTR-2B",
            }

        finally:
            await client.close()

    async def run_itc_reconciliation(
        self,
        organization_id: UUID,
        gst_registration_id: UUID,
        return_period: str,
        auto_match_threshold: Decimal = Decimal("0.01"),
    ) -> ITCReconciliationSummary:
        """Run ITC reconciliation between books and GSTR-2B.

        Args:
            organization_id: Organization ID
            gst_registration_id: GST registration ID
            return_period: Period in MMYYYY format
            auto_match_threshold: Threshold for auto-matching

        Returns:
            Reconciliation summary
        """
        gst_reg = await self.db.get(GSTRegistration, gst_registration_id)
        if not gst_reg:
            raise ValueError("GST registration not found")

        # Get GSTR-2B data
        gstr2b_query = select(GSTR2BData).where(
            and_(
                GSTR2BData.organization_id == organization_id,
                GSTR2BData.gst_registration_id == gst_registration_id,
                GSTR2BData.return_period == return_period,
            )
        )
        gstr2b_result = await self.db.execute(gstr2b_query)
        gstr2b_records = {
            (r.supplier_gstin, r.invoice_number): r
            for r in gstr2b_result.scalars().all()
        }

        # Get purchase bills from books for the period
        # TODO: Implement actual purchase bill query
        # For now, simulate with empty dict
        books_records: Dict[Tuple[str, str], Any] = {}

        # Clear existing mismatches for this period
        await self.db.execute(
            GSTItcMismatch.__table__.delete().where(
                and_(
                    GSTItcMismatch.organization_id == organization_id,
                    GSTItcMismatch.gst_registration_id == gst_registration_id,
                    GSTItcMismatch.return_period == return_period,
                )
            )
        )

        mismatches_created = 0
        matched_count = 0

        # Check for mismatches
        all_keys = set(gstr2b_records.keys()) | set(books_records.keys())

        for key in all_keys:
            supplier_gstin, invoice_number = key
            gstr2b = gstr2b_records.get(key)
            books = books_records.get(key)

            if gstr2b and books:
                # Both exist - check for amount mismatch
                variance = abs(gstr2b.taxable_value - books.get("taxable_value", 0))
                if variance > auto_match_threshold:
                    # Create mismatch record
                    mismatch = GSTItcMismatch(
                        organization_id=organization_id,
                        gst_registration_id=gst_registration_id,
                        return_period=return_period,
                        supplier_gstin=supplier_gstin,
                        supplier_name=gstr2b.supplier_name,
                        invoice_number=invoice_number,
                        invoice_date=gstr2b.invoice_date,
                        mismatch_type=ITCMismatchType.AMOUNT_MISMATCH,
                        gstr2b_taxable_value=gstr2b.taxable_value,
                        gstr2b_igst=gstr2b.igst,
                        gstr2b_cgst=gstr2b.cgst,
                        gstr2b_sgst=gstr2b.sgst,
                        gstr2b_cess=gstr2b.cess,
                        gstr2b_total_tax=gstr2b.igst + gstr2b.cgst + gstr2b.sgst,
                        books_taxable_value=books.get("taxable_value"),
                        books_igst=books.get("igst"),
                        books_cgst=books.get("cgst"),
                        books_sgst=books.get("sgst"),
                        books_total_tax=books.get("total_tax"),
                        variance_taxable=variance,
                        variance_total=variance,
                    )
                    self.db.add(mismatch)
                    mismatches_created += 1
                else:
                    # Match - update GSTR2B record
                    gstr2b.is_matched = True
                    gstr2b.matched_purchase_bill_id = books.get("purchase_bill_id")
                    matched_count += 1

            elif gstr2b and not books:
                # In 2B but not in books
                mismatch = GSTItcMismatch(
                    organization_id=organization_id,
                    gst_registration_id=gst_registration_id,
                    return_period=return_period,
                    supplier_gstin=supplier_gstin,
                    supplier_name=gstr2b.supplier_name,
                    invoice_number=invoice_number,
                    invoice_date=gstr2b.invoice_date,
                    mismatch_type=ITCMismatchType.MISSING_IN_BOOKS,
                    gstr2b_taxable_value=gstr2b.taxable_value,
                    gstr2b_igst=gstr2b.igst,
                    gstr2b_cgst=gstr2b.cgst,
                    gstr2b_sgst=gstr2b.sgst,
                    gstr2b_cess=gstr2b.cess,
                    gstr2b_total_tax=gstr2b.igst + gstr2b.cgst + gstr2b.sgst,
                )
                self.db.add(mismatch)
                mismatches_created += 1

            elif books and not gstr2b:
                # In books but not in 2B
                mismatch = GSTItcMismatch(
                    organization_id=organization_id,
                    gst_registration_id=gst_registration_id,
                    return_period=return_period,
                    supplier_gstin=supplier_gstin,
                    invoice_number=invoice_number,
                    mismatch_type=ITCMismatchType.MISSING_IN_2B,
                    books_taxable_value=books.get("taxable_value"),
                    books_igst=books.get("igst"),
                    books_cgst=books.get("cgst"),
                    books_sgst=books.get("sgst"),
                    books_total_tax=books.get("total_tax"),
                    purchase_bill_id=books.get("purchase_bill_id"),
                )
                self.db.add(mismatch)
                mismatches_created += 1

        await self.db.commit()

        # Calculate summary
        return ITCReconciliationSummary(
            return_period=return_period,
            total_invoices_in_books=len(books_records),
            total_invoices_in_2b=len(gstr2b_records),
            matched_invoices=matched_count,
            mismatched_invoices=mismatches_created,
            missing_in_2b=sum(1 for k in books_records if k not in gstr2b_records),
            missing_in_books=sum(1 for k in gstr2b_records if k not in books_records),
            amount_mismatch=mismatches_created - sum(1 for k in books_records if k not in gstr2b_records) - sum(1 for k in gstr2b_records if k not in books_records),
            books_total_itc=sum(Decimal(str(b.get("total_tax", 0))) for b in books_records.values()),
            gstr2b_total_itc=sum(r.igst + r.cgst + r.sgst for r in gstr2b_records.values()),
            matched_itc=Decimal("0"),  # TODO: Calculate
            variance_itc=Decimal("0"),  # TODO: Calculate
            pending_resolution=mismatches_created,
            resolved=0,
        )

    async def list_itc_mismatches(
        self,
        organization_id: UUID,
        gst_registration_id: Optional[UUID] = None,
        return_period: Optional[str] = None,
        mismatch_type: Optional[ITCMismatchType] = None,
        resolution_status: Optional[ITCMismatchResolution] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> ITCMismatchListResponse:
        """List ITC mismatches."""
        query = select(GSTItcMismatch).where(
            GSTItcMismatch.organization_id == organization_id
        )

        if gst_registration_id:
            query = query.where(GSTItcMismatch.gst_registration_id == gst_registration_id)
        if return_period:
            query = query.where(GSTItcMismatch.return_period == return_period)
        if mismatch_type:
            query = query.where(GSTItcMismatch.mismatch_type == mismatch_type)
        if resolution_status:
            query = query.where(GSTItcMismatch.resolution_status == resolution_status)

        # Count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Paginate
        query = query.order_by(GSTItcMismatch.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        items = result.scalars().all()

        return ITCMismatchListResponse(
            items=[ITCMismatchResponse.model_validate(m) for m in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size,
        )

    async def resolve_mismatch(
        self,
        mismatch_id: UUID,
        resolution_status: ITCMismatchResolution,
        resolution_notes: Optional[str],
        resolved_by: UUID,
    ) -> GSTItcMismatch:
        """Resolve an ITC mismatch."""
        mismatch = await self.db.get(GSTItcMismatch, mismatch_id)
        if not mismatch:
            raise ValueError("Mismatch not found")

        mismatch.resolution_status = resolution_status
        mismatch.resolution_notes = resolution_notes
        mismatch.resolved_at = datetime.utcnow()
        mismatch.resolved_by = resolved_by

        await self.db.commit()
        await self.db.refresh(mismatch)
        return mismatch

    # =========================================================================
    # GSTR-1 Filing Operations
    # =========================================================================

    async def validate_gstr1(
        self,
        return_id: UUID,
        session_id: UUID,
        validated_by: UUID,
    ) -> GSTReturnFiling:
        """Validate GSTR-1 data with GSTN.

        Args:
            return_id: Return filing ID
            session_id: Active GSTN session ID
            validated_by: User performing validation

        Returns:
            Updated return filing record
        """
        # Get return filing
        filing = await self.db.get(GSTReturnFiling, return_id)
        if not filing:
            raise ValueError("Return filing not found")

        if filing.return_type != GSTReturnType.GSTR1:
            raise ValueError("Not a GSTR-1 return")

        if filing.status not in [GSTReturnStatus.DRAFT, GSTReturnStatus.ERROR]:
            raise ValueError(f"Cannot validate return in {filing.status} status")

        # Get session
        session = await self.db.get(GSTNSession, session_id)
        if not session or session.status != GSTNSessionStatus.ACTIVE:
            raise ValueError("Invalid or expired session")

        # Get GSTN client
        client = await self._get_gstn_client(session)

        try:
            # Save each section to GSTN for validation
            section_data = filing.section_wise_data or {}
            errors = []

            for section, data in section_data.items():
                if data:
                    result = await client.save_gstr1(
                        return_period=filing.return_period,
                        section=section.upper(),
                        data=data,
                    )
                    if not result["success"]:
                        errors.append({
                            "section": section,
                            "error_code": result.get("error_code"),
                            "error_message": result.get("error_message"),
                        })

            if errors:
                filing.status = GSTReturnStatus.ERROR
                filing.error_details = {"validation_errors": errors}
                await self.db.commit()
                await self.db.refresh(filing)
                raise ValueError(f"Validation failed: {errors}")

            # Update filing status
            filing.status = GSTReturnStatus.VALIDATED
            filing.validated_at = datetime.utcnow()
            filing.gstn_session_id = session_id
            filing.error_details = None

            await self.db.commit()
            await self.db.refresh(filing)

            logger.info(f"Validated GSTR-1 for {filing.gstin}, period {filing.return_period}")
            return filing

        finally:
            await client.close()

    async def submit_gstr1(
        self,
        return_id: UUID,
        session_id: UUID,
        submitted_by: UUID,
    ) -> GSTReturnFiling:
        """Submit GSTR-1 to GSTN.

        Args:
            return_id: Return filing ID
            session_id: Active GSTN session ID
            submitted_by: User submitting the return

        Returns:
            Updated return filing record
        """
        # Get return filing
        filing = await self.db.get(GSTReturnFiling, return_id)
        if not filing:
            raise ValueError("Return filing not found")

        if filing.return_type != GSTReturnType.GSTR1:
            raise ValueError("Not a GSTR-1 return")

        if filing.status != GSTReturnStatus.VALIDATED:
            raise ValueError(f"Return must be validated before submission. Current status: {filing.status}")

        # Get session
        session = await self.db.get(GSTNSession, session_id)
        if not session or session.status != GSTNSessionStatus.ACTIVE:
            raise ValueError("Invalid or expired session")

        # Get GSTN client
        client = await self._get_gstn_client(session)

        try:
            # Submit GSTR-1
            result = await client.submit_gstr1(filing.return_period)

            if not result["success"]:
                filing.status = GSTReturnStatus.ERROR
                filing.error_details = {
                    "submission_error": {
                        "error_code": result.get("error_code"),
                        "error_message": result.get("error_message"),
                    }
                }
                await self.db.commit()
                raise ValueError(f"Submission failed: {result.get('error_message')}")

            # Update filing status
            filing.status = GSTReturnStatus.SUBMITTED
            filing.submitted_at = datetime.utcnow()
            filing.submitted_by = submitted_by
            filing.gstn_session_id = session_id
            filing.error_details = None

            await self.db.commit()
            await self.db.refresh(filing)

            logger.info(f"Submitted GSTR-1 for {filing.gstin}, period {filing.return_period}")
            return filing

        finally:
            await client.close()

    async def file_gstr1(
        self,
        return_id: UUID,
        session_id: UUID,
        pan: str,
        otp: str,
        filed_by: UUID,
    ) -> GSTReturnFiling:
        """File GSTR-1 with EVC.

        Args:
            return_id: Return filing ID
            session_id: Active GSTN session ID
            pan: PAN of authorized signatory
            otp: OTP for EVC
            filed_by: User filing the return

        Returns:
            Updated return filing record with ARN
        """
        # Get return filing
        filing = await self.db.get(GSTReturnFiling, return_id)
        if not filing:
            raise ValueError("Return filing not found")

        if filing.return_type != GSTReturnType.GSTR1:
            raise ValueError("Not a GSTR-1 return")

        if filing.status != GSTReturnStatus.SUBMITTED:
            raise ValueError(f"Return must be submitted before filing. Current status: {filing.status}")

        # Get session
        session = await self.db.get(GSTNSession, session_id)
        if not session or session.status != GSTNSessionStatus.ACTIVE:
            raise ValueError("Invalid or expired session")

        # Get GSTN client
        client = await self._get_gstn_client(session)

        try:
            # File GSTR-1 with EVC
            result = await client.file_gstr1_with_evc(
                return_period=filing.return_period,
                pan=pan,
                otp=otp,
            )

            if not result["success"]:
                filing.status = GSTReturnStatus.ERROR
                filing.error_details = {
                    "filing_error": {
                        "error_code": result.get("error_code"),
                        "error_message": result.get("error_message"),
                    }
                }
                await self.db.commit()
                raise ValueError(f"Filing failed: {result.get('error_message')}")

            # Extract ARN from response
            data = result.get("data", {})
            arn = data.get("arn") or data.get("reference_id")

            # Update filing status
            filing.status = GSTReturnStatus.FILED
            filing.filed_at = datetime.utcnow()
            filing.filing_date = date.today()
            filing.arn = arn
            filing.submitted_by = filed_by
            filing.gstn_session_id = session_id
            filing.error_details = None

            await self.db.commit()
            await self.db.refresh(filing)

            logger.info(f"Filed GSTR-1 for {filing.gstin}, period {filing.return_period}, ARN: {arn}")
            return filing

        finally:
            await client.close()

    # =========================================================================
    # GSTR-3B Filing Operations
    # =========================================================================

    async def validate_gstr3b(
        self,
        return_id: UUID,
        session_id: UUID,
        validated_by: UUID,
    ) -> GSTReturnFiling:
        """Validate GSTR-3B data with GSTN.

        Args:
            return_id: Return filing ID
            session_id: Active GSTN session ID
            validated_by: User performing validation

        Returns:
            Updated return filing record
        """
        # Get return filing
        filing = await self.db.get(GSTReturnFiling, return_id)
        if not filing:
            raise ValueError("Return filing not found")

        if filing.return_type != GSTReturnType.GSTR3B:
            raise ValueError("Not a GSTR-3B return")

        if filing.status not in [GSTReturnStatus.DRAFT, GSTReturnStatus.ERROR]:
            raise ValueError(f"Cannot validate return in {filing.status} status")

        # Get session
        session = await self.db.get(GSTNSession, session_id)
        if not session or session.status != GSTNSessionStatus.ACTIVE:
            raise ValueError("Invalid or expired session")

        # Get GSTN client
        client = await self._get_gstn_client(session)

        try:
            # Save GSTR-3B data to GSTN for validation
            summary_data = filing.summary_data or {}
            result = await client.save_gstr3b(
                return_period=filing.return_period,
                data=summary_data,
            )

            if not result["success"]:
                filing.status = GSTReturnStatus.ERROR
                filing.error_details = {
                    "validation_error": {
                        "error_code": result.get("error_code"),
                        "error_message": result.get("error_message"),
                    }
                }
                await self.db.commit()
                raise ValueError(f"Validation failed: {result.get('error_message')}")

            # Update filing status
            filing.status = GSTReturnStatus.VALIDATED
            filing.validated_at = datetime.utcnow()
            filing.gstn_session_id = session_id
            filing.error_details = None

            await self.db.commit()
            await self.db.refresh(filing)

            logger.info(f"Validated GSTR-3B for {filing.gstin}, period {filing.return_period}")
            return filing

        finally:
            await client.close()

    async def submit_gstr3b(
        self,
        return_id: UUID,
        session_id: UUID,
        submitted_by: UUID,
    ) -> GSTReturnFiling:
        """Submit GSTR-3B to GSTN.

        Args:
            return_id: Return filing ID
            session_id: Active GSTN session ID
            submitted_by: User submitting the return

        Returns:
            Updated return filing record
        """
        # Get return filing
        filing = await self.db.get(GSTReturnFiling, return_id)
        if not filing:
            raise ValueError("Return filing not found")

        if filing.return_type != GSTReturnType.GSTR3B:
            raise ValueError("Not a GSTR-3B return")

        if filing.status != GSTReturnStatus.VALIDATED:
            raise ValueError(f"Return must be validated before submission. Current status: {filing.status}")

        # Get session
        session = await self.db.get(GSTNSession, session_id)
        if not session or session.status != GSTNSessionStatus.ACTIVE:
            raise ValueError("Invalid or expired session")

        # Get GSTN client
        client = await self._get_gstn_client(session)

        try:
            # Submit GSTR-3B
            result = await client.submit_gstr3b(filing.return_period)

            if not result["success"]:
                filing.status = GSTReturnStatus.ERROR
                filing.error_details = {
                    "submission_error": {
                        "error_code": result.get("error_code"),
                        "error_message": result.get("error_message"),
                    }
                }
                await self.db.commit()
                raise ValueError(f"Submission failed: {result.get('error_message')}")

            # Update filing status
            filing.status = GSTReturnStatus.SUBMITTED
            filing.submitted_at = datetime.utcnow()
            filing.submitted_by = submitted_by
            filing.gstn_session_id = session_id
            filing.error_details = None

            await self.db.commit()
            await self.db.refresh(filing)

            logger.info(f"Submitted GSTR-3B for {filing.gstin}, period {filing.return_period}")
            return filing

        finally:
            await client.close()

    async def file_gstr3b(
        self,
        return_id: UUID,
        session_id: UUID,
        pan: str,
        otp: str,
        filed_by: UUID,
    ) -> GSTReturnFiling:
        """File GSTR-3B with EVC.

        Args:
            return_id: Return filing ID
            session_id: Active GSTN session ID
            pan: PAN of authorized signatory
            otp: OTP for EVC
            filed_by: User filing the return

        Returns:
            Updated return filing record with ARN
        """
        # Get return filing
        filing = await self.db.get(GSTReturnFiling, return_id)
        if not filing:
            raise ValueError("Return filing not found")

        if filing.return_type != GSTReturnType.GSTR3B:
            raise ValueError("Not a GSTR-3B return")

        if filing.status != GSTReturnStatus.SUBMITTED:
            raise ValueError(f"Return must be submitted before filing. Current status: {filing.status}")

        # Get session
        session = await self.db.get(GSTNSession, session_id)
        if not session or session.status != GSTNSessionStatus.ACTIVE:
            raise ValueError("Invalid or expired session")

        # Get GSTN client
        client = await self._get_gstn_client(session)

        try:
            # File GSTR-3B with EVC
            result = await client.file_gstr3b_with_evc(
                return_period=filing.return_period,
                pan=pan,
                otp=otp,
            )

            if not result["success"]:
                filing.status = GSTReturnStatus.ERROR
                filing.error_details = {
                    "filing_error": {
                        "error_code": result.get("error_code"),
                        "error_message": result.get("error_message"),
                    }
                }
                await self.db.commit()
                raise ValueError(f"Filing failed: {result.get('error_message')}")

            # Extract ARN from response
            data = result.get("data", {})
            arn = data.get("arn") or data.get("reference_id")

            # Update filing status
            filing.status = GSTReturnStatus.FILED
            filing.filed_at = datetime.utcnow()
            filing.filing_date = date.today()
            filing.arn = arn
            filing.submitted_by = filed_by
            filing.gstn_session_id = session_id
            filing.error_details = None

            await self.db.commit()
            await self.db.refresh(filing)

            logger.info(f"Filed GSTR-3B for {filing.gstin}, period {filing.return_period}, ARN: {arn}")
            return filing

        finally:
            await client.close()

    # =========================================================================
    # Filing Utilities
    # =========================================================================

    async def request_filing_otp(
        self,
        session_id: UUID,
        pan: str,
    ) -> Dict[str, Any]:
        """Request OTP for filing return with EVC.

        Args:
            session_id: Active GSTN session ID
            pan: PAN of authorized signatory

        Returns:
            OTP request result
        """
        # Get session
        session = await self.db.get(GSTNSession, session_id)
        if not session or session.status != GSTNSessionStatus.ACTIVE:
            raise ValueError("Invalid or expired session")

        # Get GSTN client
        client = await self._get_gstn_client(session)

        try:
            result = await client.request_otp_for_filing(pan)

            if not result["success"]:
                raise ValueError(f"OTP request failed: {result.get('error_message')}")

            return {
                "success": True,
                "message": "OTP sent to registered mobile/email",
                "otp_reference": result.get("data", {}).get("ref_id"),
            }

        finally:
            await client.close()

    async def get_return_status_from_gstn(
        self,
        return_id: UUID,
        session_id: UUID,
    ) -> Dict[str, Any]:
        """Get return filing status from GSTN.

        Args:
            return_id: Return filing ID
            session_id: Active GSTN session ID

        Returns:
            Filing status from GSTN
        """
        # Get return filing
        filing = await self.db.get(GSTReturnFiling, return_id)
        if not filing:
            raise ValueError("Return filing not found")

        # Get session
        session = await self.db.get(GSTNSession, session_id)
        if not session or session.status != GSTNSessionStatus.ACTIVE:
            raise ValueError("Invalid or expired session")

        # Get GSTN client
        client = await self._get_gstn_client(session)

        try:
            result = await client.get_return_status(
                return_period=filing.return_period,
                return_type=filing.return_type.value,
            )

            if result["success"]:
                data = result.get("data", {})
                # Update local record if ARN is present
                if data.get("arn") and not filing.arn:
                    filing.arn = data["arn"]
                    filing.status = GSTReturnStatus.FILED
                    filing.filed_at = datetime.utcnow()
                    await self.db.commit()

                return {
                    "success": True,
                    "status": data.get("status"),
                    "arn": data.get("arn"),
                    "filing_date": data.get("filing_date"),
                    "valid": data.get("valid"),
                }
            else:
                return result

        finally:
            await client.close()
