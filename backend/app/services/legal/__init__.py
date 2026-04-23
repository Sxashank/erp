"""Legal Module services.

Provides business logic for legal case management including:
- Advocate Management
- Notice Generation & Tracking
- Statutory Period Calculations
- Legal Expense Management
- SARFAESI Workflow
- Legal Analytics
"""

from app.services.legal.advocate_service import AdvocateService
from app.services.legal.notice_service import NoticeService
from app.services.legal.statutory_service import StatutoryService
from app.services.legal.expense_service import LegalExpenseService
from app.services.legal.sarfaesi_service import SARFAESIService
from app.services.legal.analytics_service import LegalAnalyticsService

__all__ = [
    "AdvocateService",
    "NoticeService",
    "StatutoryService",
    "LegalExpenseService",
    "SARFAESIService",
    "LegalAnalyticsService",
]
