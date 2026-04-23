"""TDS repositories."""

from app.repositories.tds.tds_section_repo import TDSSectionRepository
from app.repositories.tds.tds_entry_repo import TDSEntryRepository
from app.repositories.tds.tds_challan_repo import TDSChallanRepository
from app.repositories.tds.tds_return_repo import TDSReturnRepository

__all__ = [
    "TDSSectionRepository",
    "TDSEntryRepository",
    "TDSChallanRepository",
    "TDSReturnRepository",
]
