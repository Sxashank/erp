"""Legal Module models for case management, recovery, and compliance.

This module provides comprehensive legal management including:
- Law Firm & Advocate Management
- Legal Notice Generation & Tracking
- Document Management with Versioning
- Legal Expense Management
- Statutory Period Calculations
- Court/Forum Management
"""

from app.models.legal.advocate import (
    LawFirm,
    Advocate,
    AdvocateSpecialization,
    AdvocateAssignment,
    AdvocatePerformance,
)
from app.models.legal.notice import (
    NoticeTemplate,
    LegalNotice,
    NoticeDelivery,
    NoticeResponse,
)
from app.models.legal.document import (
    LegalDocumentType,
    LegalDocument,
    DocumentVersion,
    LegalDocumentChecklist as DocumentChecklist,
)
from app.models.legal.expense import (
    ExpenseCategory,
    LegalExpense,
    ExpenseRecovery,
    AdvocateFee,
)
from app.models.legal.statutory_period import (
    StatutoryPeriod,
    PeriodTracking,
    LimitationAlert,
)
from app.models.legal.court import (
    Court,
    CourtBench,
    CourtFeeSlab,
)
from app.models.legal.enums import (
    NoticeType,
    NoticeStatus,
    DeliveryMode,
    DeliveryStatus,
    DocumentCategory,
    ExpenseCategoryType,
    ExpenseStatus,
    RecoveryType,
    FeeStructureType,
    AdvocateRole,
    SpecializationType,
    CourtType,
    AlertPriority,
)

__all__ = [
    # Advocate
    "LawFirm",
    "Advocate",
    "AdvocateSpecialization",
    "AdvocateAssignment",
    "AdvocatePerformance",
    # Notice
    "NoticeTemplate",
    "LegalNotice",
    "NoticeDelivery",
    "NoticeResponse",
    # Document
    "LegalDocumentType",
    "LegalDocument",
    "DocumentVersion",
    "DocumentChecklist",
    # Expense
    "ExpenseCategory",
    "LegalExpense",
    "ExpenseRecovery",
    "AdvocateFee",
    # Statutory Period
    "StatutoryPeriod",
    "PeriodTracking",
    "LimitationAlert",
    # Court
    "Court",
    "CourtBench",
    "CourtFeeSlab",
    # Enums
    "NoticeType",
    "NoticeStatus",
    "DeliveryMode",
    "DeliveryStatus",
    "DocumentCategory",
    "ExpenseCategoryType",
    "ExpenseStatus",
    "RecoveryType",
    "FeeStructureType",
    "AdvocateRole",
    "SpecializationType",
    "CourtType",
    "AlertPriority",
]
