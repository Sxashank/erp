"""TDS schemas."""

from app.schemas.tds.tds_section import (
    TDSSectionCreate,
    TDSSectionUpdate,
    TDSSectionResponse,
)
from app.schemas.tds.tds_entry import (
    TDSEntryCreate,
    TDSEntryUpdate,
    TDSEntryResponse,
)
from app.schemas.tds.tds_challan import (
    TDSChallanCreate,
    TDSChallanUpdate,
    TDSChallanResponse,
    TDSChallanListResponse,
    TDSChallanPaymentUpdate,
    TDSChallanOLTASUpdate,
    AddEntriesToChallanRequest,
    RemoveEntriesFromChallanRequest,
    ChallanAggregationRequest,
    ChallanSummary,
    ChallanDueReport,
)
from app.schemas.tds.tds_return import (
    TDSReturnCreate,
    TDSReturnUpdate,
    TDSReturnResponse,
    TDSReturnListResponse,
    FilingDetailsUpdate,
    ReturnValidationResult,
    ReturnFileGenerationRequest,
    ReturnFileResponse,
    RevisionRequest,
    DeducteeSummary,
)

__all__ = [
    "TDSSectionCreate",
    "TDSSectionUpdate",
    "TDSSectionResponse",
    "TDSEntryCreate",
    "TDSEntryUpdate",
    "TDSEntryResponse",
    "TDSChallanCreate",
    "TDSChallanUpdate",
    "TDSChallanResponse",
    "TDSChallanListResponse",
    "TDSChallanPaymentUpdate",
    "TDSChallanOLTASUpdate",
    "AddEntriesToChallanRequest",
    "RemoveEntriesFromChallanRequest",
    "ChallanAggregationRequest",
    "ChallanSummary",
    "ChallanDueReport",
    "TDSReturnCreate",
    "TDSReturnUpdate",
    "TDSReturnResponse",
    "TDSReturnListResponse",
    "FilingDetailsUpdate",
    "ReturnValidationResult",
    "ReturnFileGenerationRequest",
    "ReturnFileResponse",
    "RevisionRequest",
    "DeducteeSummary",
]
