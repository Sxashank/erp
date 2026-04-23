"""ESS Portal Models package.

This module provides models for the Employee Self-Service Portal including:
- ESS User Management (authentication, sessions, devices)
- Reimbursement Claims
- Helpdesk Tickets (HR/IT)
- IT Declaration (Tax computation)
- Attendance Regularization
- Profile Update Requests
"""

from app.models.ess.enums import (
    ESSUserStatus,
    ClaimType,
    ClaimStatus,
    TicketCategory,
    TicketPriority,
    TicketStatus,
    ITDeclarationStatus,
    ITDeclarationSection,
    RegularizationType,
    RegularizationStatus,
    ProfileUpdateType,
    ProfileUpdateStatus,
)

from app.models.ess.ess_user import (
    ESSUser,
    ESSSession,
    ESSDevice,
    ESSOTP,
    ProfileUpdateRequest,
)

from app.models.ess.reimbursement import (
    ReimbursementCategory,
    ReimbursementClaim,
    ReimbursementLineItem,
    ReimbursementApproval,
)

from app.models.ess.helpdesk import (
    TicketCategoryMaster,
    HelpdeskTicket,
    TicketComment,
    TicketHistory,
)

from app.models.ess.it_declaration import (
    ITDeclarationMaster,
    ITDeclaration,
    ITDeclarationItem,
    HRAReceipt,
    AttendanceRegularization,
)

__all__ = [
    # Enums
    "ESSUserStatus",
    "ClaimType",
    "ClaimStatus",
    "TicketCategory",
    "TicketPriority",
    "TicketStatus",
    "ITDeclarationStatus",
    "ITDeclarationSection",
    "RegularizationType",
    "RegularizationStatus",
    "ProfileUpdateType",
    "ProfileUpdateStatus",
    # ESS User
    "ESSUser",
    "ESSSession",
    "ESSDevice",
    "ESSOTP",
    "ProfileUpdateRequest",
    # Reimbursement
    "ReimbursementCategory",
    "ReimbursementClaim",
    "ReimbursementLineItem",
    "ReimbursementApproval",
    # Helpdesk
    "TicketCategoryMaster",
    "HelpdeskTicket",
    "TicketComment",
    "TicketHistory",
    # IT Declaration
    "ITDeclarationMaster",
    "ITDeclaration",
    "ITDeclarationItem",
    "HRAReceipt",
    "AttendanceRegularization",
]
