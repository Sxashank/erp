"""TDS services."""

from app.services.tds.tds_section_service import TDSSectionService
from app.services.tds.tds_entry_service import TDSEntryService
from app.services.tds.tds_challan_service import TDSChallanService
from app.services.tds.tds_return_service import TDSReturnService
from app.services.tds.form16a_service import Form16AService

__all__ = [
    "TDSSectionService",
    "TDSEntryService",
    "TDSChallanService",
    "TDSReturnService",
    "Form16AService",
]
