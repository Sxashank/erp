"""Portal Module Services.

Provides business logic for customer self-service portal.
"""

from app.services.portal.application_service import PortalApplicationService
from app.services.portal.auth_service import PortalAuthService
from app.services.portal.claim_service import PortalClaimService
from app.services.portal.dashboard_service import PortalDashboardService
from app.services.portal.document_service import PortalDocumentService
from app.services.portal.entity_access import (
    assert_application_access,
    assert_entity_access,
    assert_loan_access,
    get_accessible_entity_ids,
)
from app.services.portal.notification_service import PortalNotificationService
from app.services.portal.payment_service import PortalPaymentService
from app.services.portal.registration_service import PortalRegistrationService
from app.services.portal.service_request_service import PortalServiceRequestService

__all__ = [
    "PortalAuthService",
    "PortalDashboardService",
    "PortalPaymentService",
    "PortalDocumentService",
    "PortalServiceRequestService",
    "PortalNotificationService",
    "PortalRegistrationService",
    "PortalApplicationService",
    "PortalClaimService",
    "assert_application_access",
    "assert_entity_access",
    "assert_loan_access",
    "get_accessible_entity_ids",
]
