"""GSTN Portal Integration Pydantic schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import Field
from app.schemas.base import CamelSchema

from app.models.gst.gstn_models import (
    GSTReturnType,
    GSTReturnStatus,
    GSTNSessionStatus,
    ITCMismatchType,
    ITCMismatchResolution,
    GSTR1Section,
)


# =============================================================================
# GSTN Session Schemas
# =============================================================================

class GSTNSessionBase(CamelSchema):
    """Base schema for GSTN session."""
    gstin: str = Field(..., min_length=15, max_length=15, description="GSTIN")


class GSTNOTPRequest(GSTNSessionBase):
    """Request to initiate GSTN OTP."""
    username: Optional[str] = Field(
        default=None,
        description="GSTN portal username; optional while external GSTN integration is disabled",
    )


class GSTNOTPVerify(GSTNSessionBase):
    """Request to verify GSTN OTP."""
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit OTP")
    otp_reference: Optional[str] = Field(
        default=None,
        description="OTP reference from request; optional while external GSTN integration is disabled",
    )


class GSTNSessionResponse(CamelSchema):
    """Response for GSTN session."""

    id: UUID
    gstin: str
    status: GSTNSessionStatus
    token_expires_at: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime

    @property
    def is_valid(self) -> bool:
        if self.status != GSTNSessionStatus.ACTIVE:
            return False
        if not self.token_expires_at:
            return False
        return datetime.utcnow() < self.token_expires_at.replace(tzinfo=None)


class GSTNSessionCreate(CamelSchema):
    """Create new GSTN session after OTP verification."""
    gst_registration_id: UUID
    auth_token: str
    sek_key: str
    token_expires_at: datetime


# =============================================================================
# GST Return Filing Schemas
# =============================================================================

class GSTReturnFilingBase(CamelSchema):
    """Base schema for GST return filing."""
    return_type: GSTReturnType
    return_period: str = Field(..., pattern=r"^\d{2}\d{4}$", description="MMYYYY format")
    financial_year: str = Field(..., pattern=r"^\d{4}-\d{2}$", description="e.g., 2024-25")


class GSTReturnFilingCreate(GSTReturnFilingBase):
    """Create new GST return filing."""
    gst_registration_id: UUID


class GSTReturnFilingUpdate(CamelSchema):
    """Update GST return filing."""
    status: Optional[GSTReturnStatus] = None
    summary_data: Optional[Dict[str, Any]] = None
    section_wise_data: Optional[Dict[str, Any]] = None


class GSTReturnSummary(CamelSchema):
    """Summary data for GST return."""
    total_taxable_value: Decimal = Field(default=Decimal("0"))
    total_igst: Decimal = Field(default=Decimal("0"))
    total_cgst: Decimal = Field(default=Decimal("0"))
    total_sgst: Decimal = Field(default=Decimal("0"))
    total_cess: Decimal = Field(default=Decimal("0"))
    total_tax_liability: Decimal = Field(default=Decimal("0"))
    total_itc_claimed: Decimal = Field(default=Decimal("0"))
    cash_payment: Decimal = Field(default=Decimal("0"))
    invoice_count: int = 0
    b2b_invoice_count: int = 0
    b2c_invoice_count: int = 0
    cdn_count: int = 0


class GSTReturnFilingResponse(GSTReturnFilingBase):
    """Response for GST return filing."""

    id: UUID
    organization_id: UUID
    gst_registration_id: UUID
    gstin: str
    status: GSTReturnStatus
    arn: Optional[str] = None
    filing_date: Optional[date] = None
    due_date: Optional[date] = None
    total_taxable_value: Optional[Decimal] = None
    total_igst: Optional[Decimal] = None
    total_cgst: Optional[Decimal] = None
    total_sgst: Optional[Decimal] = None
    total_cess: Optional[Decimal] = None
    total_tax_liability: Optional[Decimal] = None
    total_itc_claimed: Optional[Decimal] = None
    cash_payment: Optional[Decimal] = None
    invoice_count: int = 0
    b2b_invoice_count: int = 0
    b2c_invoice_count: int = 0
    cdn_count: int = 0
    late_fee: Optional[Decimal] = None
    interest: Optional[Decimal] = None
    validated_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    filed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class GSTReturnFilingDetail(GSTReturnFilingResponse):
    """Detailed response with section data."""
    summary_data: Optional[Dict[str, Any]] = None
    section_wise_data: Optional[Dict[str, Any]] = None
    error_details: Optional[Dict[str, Any]] = None


class GSTReturnFilingListResponse(CamelSchema):
    """Paginated list of GST return filings."""
    items: List[GSTReturnFilingResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# =============================================================================
# GSTR-1 Specific Schemas
# =============================================================================

class GSTR1B2BInvoice(CamelSchema):
    """B2B invoice for GSTR-1."""
    invoice_number: str
    invoice_date: date
    customer_gstin: str
    customer_name: Optional[str] = None
    place_of_supply: str
    reverse_charge: bool = False
    invoice_type: str = "R"  # R=Regular, SEZWP=SEZ with payment, etc.
    taxable_value: Decimal
    igst: Decimal = Field(default=Decimal("0"))
    cgst: Decimal = Field(default=Decimal("0"))
    sgst: Decimal = Field(default=Decimal("0"))
    cess: Decimal = Field(default=Decimal("0"))
    rate: Decimal


class GSTR1B2CInvoice(CamelSchema):
    """B2C invoice for GSTR-1."""
    place_of_supply: str
    rate: Decimal
    taxable_value: Decimal
    igst: Decimal = Field(default=Decimal("0"))
    cgst: Decimal = Field(default=Decimal("0"))
    sgst: Decimal = Field(default=Decimal("0"))
    cess: Decimal = Field(default=Decimal("0"))


class GSTR1HSNSummary(CamelSchema):
    """HSN-wise summary for GSTR-1."""
    hsn_code: str
    description: Optional[str] = None
    uqc: str  # Unit quantity code
    total_quantity: Decimal
    total_taxable_value: Decimal
    total_igst: Decimal = Field(default=Decimal("0"))
    total_cgst: Decimal = Field(default=Decimal("0"))
    total_sgst: Decimal = Field(default=Decimal("0"))
    total_cess: Decimal = Field(default=Decimal("0"))


class GSTR1DocumentSummary(CamelSchema):
    """Document summary for GSTR-1."""
    document_type: str  # Invoices, Debit Notes, Credit Notes
    from_serial: str
    to_serial: str
    total_number: int
    cancelled: int = 0


class GSTR1Data(CamelSchema):
    """Complete GSTR-1 data structure."""
    gstin: str
    return_period: str
    b2b_invoices: List[GSTR1B2BInvoice] = []
    b2cl_invoices: List[GSTR1B2BInvoice] = []  # B2C Large (>2.5L inter-state)
    b2cs_data: List[GSTR1B2CInvoice] = []  # B2C Small
    cdn_registered: List[GSTR1B2BInvoice] = []  # Credit/Debit notes to registered
    cdn_unregistered: List[GSTR1B2BInvoice] = []  # Credit/Debit notes to unregistered
    export_invoices: List[GSTR1B2BInvoice] = []
    hsn_summary: List[GSTR1HSNSummary] = []
    document_summary: List[GSTR1DocumentSummary] = []
    nil_rated: Optional[Dict[str, Any]] = None


# =============================================================================
# GSTR-3B Specific Schemas
# =============================================================================

class GSTR3BOutwardSupplies(CamelSchema):
    """3.1 - Outward taxable supplies."""
    taxable_value: Decimal
    igst: Decimal = Field(default=Decimal("0"))
    cgst: Decimal = Field(default=Decimal("0"))
    sgst: Decimal = Field(default=Decimal("0"))
    cess: Decimal = Field(default=Decimal("0"))


class GSTR3BITCDetails(CamelSchema):
    """4 - Eligible ITC."""
    igst: Decimal = Field(default=Decimal("0"))
    cgst: Decimal = Field(default=Decimal("0"))
    sgst: Decimal = Field(default=Decimal("0"))
    cess: Decimal = Field(default=Decimal("0"))


class GSTR3BData(CamelSchema):
    """Complete GSTR-3B data structure."""
    gstin: str
    return_period: str
    # 3.1 - Outward supplies
    outward_taxable_supplies: GSTR3BOutwardSupplies
    outward_taxable_zero_rated: GSTR3BOutwardSupplies
    outward_nil_rated_exempt: GSTR3BOutwardSupplies
    outward_non_gst: GSTR3BOutwardSupplies
    # 3.2 - Inward supplies attracting reverse charge
    inward_reverse_charge: GSTR3BOutwardSupplies
    # 4 - Eligible ITC
    itc_available: GSTR3BITCDetails
    itc_reversed: GSTR3BITCDetails
    itc_net: GSTR3BITCDetails
    itc_ineligible: GSTR3BITCDetails
    # 5 - Exempt, nil-rated and non-GST
    inter_state_supplies_unregistered: Decimal = Field(default=Decimal("0"))
    inter_state_supplies_composition: Decimal = Field(default=Decimal("0"))
    intra_state_supplies_unregistered: Decimal = Field(default=Decimal("0"))
    intra_state_supplies_composition: Decimal = Field(default=Decimal("0"))
    # 6 - Payment of tax
    tax_payable_igst: Decimal = Field(default=Decimal("0"))
    tax_payable_cgst: Decimal = Field(default=Decimal("0"))
    tax_payable_sgst: Decimal = Field(default=Decimal("0"))
    tax_payable_cess: Decimal = Field(default=Decimal("0"))
    tax_paid_igst: Decimal = Field(default=Decimal("0"))
    tax_paid_cgst: Decimal = Field(default=Decimal("0"))
    tax_paid_sgst: Decimal = Field(default=Decimal("0"))
    tax_paid_cess: Decimal = Field(default=Decimal("0"))
    cash_paid_igst: Decimal = Field(default=Decimal("0"))
    cash_paid_cgst: Decimal = Field(default=Decimal("0"))
    cash_paid_sgst: Decimal = Field(default=Decimal("0"))
    cash_paid_cess: Decimal = Field(default=Decimal("0"))
    interest: Decimal = Field(default=Decimal("0"))
    late_fee: Decimal = Field(default=Decimal("0"))


# =============================================================================
# ITC Reconciliation Schemas
# =============================================================================

class ITCMismatchBase(CamelSchema):
    """Base schema for ITC mismatch."""
    return_period: str
    supplier_gstin: str
    invoice_number: str
    invoice_date: Optional[date] = None
    mismatch_type: ITCMismatchType


class ITCMismatchCreate(ITCMismatchBase):
    """Create ITC mismatch record."""
    gst_registration_id: UUID
    supplier_name: Optional[str] = None
    books_taxable_value: Optional[Decimal] = None
    books_igst: Optional[Decimal] = None
    books_cgst: Optional[Decimal] = None
    books_sgst: Optional[Decimal] = None
    books_cess: Optional[Decimal] = None
    gstr2b_taxable_value: Optional[Decimal] = None
    gstr2b_igst: Optional[Decimal] = None
    gstr2b_cgst: Optional[Decimal] = None
    gstr2b_sgst: Optional[Decimal] = None
    gstr2b_cess: Optional[Decimal] = None
    purchase_bill_id: Optional[UUID] = None


class ITCMismatchResolve(CamelSchema):
    """Resolve ITC mismatch."""
    resolution_status: ITCMismatchResolution
    resolution_notes: Optional[str] = None


class ITCMismatchResponse(ITCMismatchBase):
    """Response for ITC mismatch."""

    id: UUID
    organization_id: UUID
    gst_registration_id: UUID
    supplier_name: Optional[str] = None
    books_taxable_value: Optional[Decimal] = None
    books_igst: Optional[Decimal] = None
    books_cgst: Optional[Decimal] = None
    books_sgst: Optional[Decimal] = None
    books_cess: Optional[Decimal] = None
    books_total_tax: Optional[Decimal] = None
    gstr2b_taxable_value: Optional[Decimal] = None
    gstr2b_igst: Optional[Decimal] = None
    gstr2b_cgst: Optional[Decimal] = None
    gstr2b_sgst: Optional[Decimal] = None
    gstr2b_cess: Optional[Decimal] = None
    gstr2b_total_tax: Optional[Decimal] = None
    variance_taxable: Optional[Decimal] = None
    variance_total: Optional[Decimal] = None
    resolution_status: ITCMismatchResolution
    resolution_notes: Optional[str] = None
    resolved_at: Optional[datetime] = None
    purchase_bill_id: Optional[UUID] = None
    created_at: datetime


class ITCMismatchListResponse(CamelSchema):
    """Paginated list of ITC mismatches."""
    items: List[ITCMismatchResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ITCReconciliationSummary(CamelSchema):
    """Summary of ITC reconciliation."""
    return_period: str
    total_invoices_in_books: int
    total_invoices_in_2b: int
    matched_invoices: int
    mismatched_invoices: int
    missing_in_2b: int
    missing_in_books: int
    amount_mismatch: int
    # Tax amounts
    books_total_itc: Decimal
    gstr2b_total_itc: Decimal
    matched_itc: Decimal
    variance_itc: Decimal
    # Resolution status
    pending_resolution: int
    resolved: int


# =============================================================================
# GSTR-2B Data Schemas
# =============================================================================

class GSTR2BInvoiceResponse(CamelSchema):
    """Response for GSTR-2B invoice data."""

    id: UUID
    return_period: str
    supplier_gstin: str
    supplier_name: Optional[str] = None
    supplier_filing_status: Optional[str] = None
    invoice_number: str
    invoice_date: date
    invoice_type: str
    place_of_supply: Optional[str] = None
    reverse_charge: bool
    taxable_value: Decimal
    igst: Decimal
    cgst: Decimal
    sgst: Decimal
    cess: Decimal
    itc_eligible: bool
    itc_claimed: bool
    is_matched: bool
    matched_purchase_bill_id: Optional[UUID] = None
    source_section: Optional[str] = None
    fetched_at: datetime


class GSTR2BListResponse(CamelSchema):
    """Paginated list of GSTR-2B invoices."""
    items: List[GSTR2BInvoiceResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class GSTR2BSummary(CamelSchema):
    """Summary of GSTR-2B data."""
    return_period: str
    total_invoices: int
    total_suppliers: int
    total_taxable_value: Decimal
    total_igst: Decimal
    total_cgst: Decimal
    total_sgst: Decimal
    total_cess: Decimal
    eligible_itc: Decimal
    ineligible_itc: Decimal
    reverse_charge_itc: Decimal
    matched_count: int
    unmatched_count: int


# =============================================================================
# Statistics Schemas
# =============================================================================

class GSTNFilingStatistics(CamelSchema):
    """Statistics for GSTN filings."""
    total_returns: int
    filed_on_time: int
    filed_late: int
    pending: int
    # By return type
    gstr1_count: int
    gstr3b_count: int
    # Tax statistics
    total_tax_liability: Decimal
    total_itc_claimed: Decimal
    total_cash_paid: Decimal
    total_late_fee: Decimal


class ITCReconciliationStatistics(CamelSchema):
    """Statistics for ITC reconciliation."""
    total_mismatches: int
    pending_resolution: int
    resolved: int
    # By type
    missing_in_2b: int
    missing_in_books: int
    amount_mismatch: int
    # Variance
    total_variance: Decimal


# =============================================================================
# Request Schemas for API Operations
# =============================================================================

class GenerateGSTR1Request(CamelSchema):
    """Request to generate GSTR-1 from sales data."""
    gst_registration_id: UUID
    return_period: str = Field(..., pattern=r"^\d{2}\d{4}$")
    financial_year: str = Field(..., pattern=r"^\d{4}-\d{2}$")


class GenerateGSTR3BRequest(CamelSchema):
    """Request to generate GSTR-3B summary."""
    gst_registration_id: UUID
    return_period: str = Field(..., pattern=r"^\d{2}\d{4}$")
    financial_year: str = Field(..., pattern=r"^\d{4}-\d{2}$")


class FetchGSTR2BRequest(CamelSchema):
    """Request to fetch GSTR-2B from GSTN."""
    gst_registration_id: UUID
    return_period: str = Field(..., pattern=r"^\d{2}\d{4}$")


class RunITCReconciliationRequest(CamelSchema):
    """Request to run ITC reconciliation."""
    gst_registration_id: UUID
    return_period: str = Field(..., pattern=r"^\d{2}\d{4}$")
    auto_match_threshold: Decimal = Field(
        default=Decimal("0.01"),
        description="Threshold for auto-matching (difference allowed)"
    )


class SubmitReturnRequest(CamelSchema):
    """Request to submit return to GSTN."""
    return_id: UUID
    gstn_session_id: UUID


class FileReturnRequest(CamelSchema):
    """Request to file return with DSC/EVC."""
    return_id: UUID
    gstn_session_id: UUID
    filing_mode: str = Field(..., pattern="^(DSC|EVC)$")
    pan: str = Field(..., min_length=10, max_length=10)
    otp: Optional[str] = None  # Required for EVC
