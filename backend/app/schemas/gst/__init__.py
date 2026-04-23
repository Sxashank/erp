"""GST schemas."""

from app.schemas.gst.gst_rate import (
    GSTRateCreate,
    GSTRateUpdate,
    GSTRateResponse,
)
from app.schemas.gst.hsn_sac import (
    HSNSACCreate,
    HSNSACUpdate,
    HSNSACResponse,
)
from app.schemas.gst.gst_registration import (
    GSTRegistrationCreate,
    GSTRegistrationUpdate,
    GSTRegistrationResponse,
)
from app.schemas.gst.gstn import (
    # GSTN Session
    GSTNOTPRequest,
    GSTNOTPVerify,
    GSTNSessionResponse,
    GSTNSessionCreate,
    # Return Filing
    GSTReturnFilingCreate,
    GSTReturnFilingUpdate,
    GSTReturnFilingResponse,
    GSTReturnFilingDetail,
    GSTReturnFilingListResponse,
    GSTReturnSummary,
    # GSTR-1
    GSTR1B2BInvoice,
    GSTR1B2CInvoice,
    GSTR1HSNSummary,
    GSTR1DocumentSummary,
    GSTR1Data,
    # GSTR-3B
    GSTR3BOutwardSupplies,
    GSTR3BITCDetails,
    GSTR3BData,
    # ITC Reconciliation
    ITCMismatchCreate,
    ITCMismatchResolve,
    ITCMismatchResponse,
    ITCMismatchListResponse,
    ITCReconciliationSummary,
    # GSTR-2B
    GSTR2BInvoiceResponse,
    GSTR2BListResponse,
    GSTR2BSummary,
    # Statistics
    GSTNFilingStatistics,
    ITCReconciliationStatistics,
    # Requests
    GenerateGSTR1Request,
    GenerateGSTR3BRequest,
    FetchGSTR2BRequest,
    RunITCReconciliationRequest,
    SubmitReturnRequest,
    FileReturnRequest,
)

__all__ = [
    # Existing
    "GSTRateCreate",
    "GSTRateUpdate",
    "GSTRateResponse",
    "HSNSACCreate",
    "HSNSACUpdate",
    "HSNSACResponse",
    "GSTRegistrationCreate",
    "GSTRegistrationUpdate",
    "GSTRegistrationResponse",
    # GSTN Session
    "GSTNOTPRequest",
    "GSTNOTPVerify",
    "GSTNSessionResponse",
    "GSTNSessionCreate",
    # Return Filing
    "GSTReturnFilingCreate",
    "GSTReturnFilingUpdate",
    "GSTReturnFilingResponse",
    "GSTReturnFilingDetail",
    "GSTReturnFilingListResponse",
    "GSTReturnSummary",
    # GSTR-1
    "GSTR1B2BInvoice",
    "GSTR1B2CInvoice",
    "GSTR1HSNSummary",
    "GSTR1DocumentSummary",
    "GSTR1Data",
    # GSTR-3B
    "GSTR3BOutwardSupplies",
    "GSTR3BITCDetails",
    "GSTR3BData",
    # ITC Reconciliation
    "ITCMismatchCreate",
    "ITCMismatchResolve",
    "ITCMismatchResponse",
    "ITCMismatchListResponse",
    "ITCReconciliationSummary",
    # GSTR-2B
    "GSTR2BInvoiceResponse",
    "GSTR2BListResponse",
    "GSTR2BSummary",
    # Statistics
    "GSTNFilingStatistics",
    "ITCReconciliationStatistics",
    # Requests
    "GenerateGSTR1Request",
    "GenerateGSTR3BRequest",
    "FetchGSTR2BRequest",
    "RunITCReconciliationRequest",
    "SubmitReturnRequest",
    "FileReturnRequest",
]
