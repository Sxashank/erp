"""Portal Service Request Service.

Handles service requests like prepayment, foreclosure, EMI date change, etc.
"""

import secrets
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional, Dict, Any, List, Tuple
from uuid import UUID

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.portal.service_request import (
    PortalServiceRequest,
    PortalServiceRequestDocument,
    PortalServiceRequestHistory,
)
from app.models.portal.enums import (
    ServiceRequestType,
    ServiceRequestStatus,
)


class PortalServiceRequestService:
    """Portal service request service."""

    # SLA days by request type
    SLA_DAYS = {
        ServiceRequestType.PREPAYMENT: 3,
        ServiceRequestType.FORECLOSURE: 7,
        ServiceRequestType.EMI_DATE_CHANGE: 5,
        ServiceRequestType.ADDRESS_CHANGE: 3,
        ServiceRequestType.CONTACT_UPDATE: 1,
        ServiceRequestType.NOC_REQUEST: 7,
        ServiceRequestType.STATEMENT_REQUEST: 2,
        ServiceRequestType.CERTIFICATE_REQUEST: 5,
        ServiceRequestType.INSURANCE_CLAIM: 15,
        ServiceRequestType.LOAN_RESTRUCTURE: 15,
        ServiceRequestType.MORATORIUM: 7,
        ServiceRequestType.DISPUTE_RESOLUTION: 15,
    }

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # Create Service Request
    # =========================================================================

    async def create_request(
        self,
        organization_id: UUID,
        user_id: UUID,
        loan_account_id: UUID,
        request_type: ServiceRequestType,
        subject: str,
        description: Optional[str] = None,
        **kwargs,
    ) -> PortalServiceRequest:
        """Create a new service request."""
        request_number = self._generate_request_number()

        request = PortalServiceRequest(
            organization_id=organization_id,
            user_id=user_id,
            loan_account_id=loan_account_id,
            request_number=request_number,
            request_type=request_type,
            subject=subject,
            description=description,
            status=ServiceRequestStatus.DRAFT,
            sla_due_at=datetime.utcnow() + timedelta(days=self.SLA_DAYS.get(request_type, 7)),
        )

        # Set type-specific fields
        if request_type == ServiceRequestType.PREPAYMENT:
            request.requested_amount = kwargs.get("prepayment_amount")
        elif request_type == ServiceRequestType.FORECLOSURE:
            request.requested_amount = kwargs.get("foreclosure_amount")
        elif request_type == ServiceRequestType.EMI_DATE_CHANGE:
            request.current_emi_date = kwargs.get("current_emi_date")
            request.requested_emi_date = kwargs.get("new_emi_date")
            request.effective_from = kwargs.get("effective_from")
        elif request_type in [ServiceRequestType.ADDRESS_CHANGE, ServiceRequestType.CONTACT_UPDATE]:
            request.change_details = str(kwargs.get("change_details", {}))

        self.db.add(request)
        await self.db.flush()

        # Add initial history
        await self._add_history(
            request.id,
            None,
            ServiceRequestStatus.DRAFT,
            "CUSTOMER",
            user_id,
            "Request created",
        )

        return request

    async def submit_request(
        self,
        request_id: UUID,
        user_id: UUID,
    ) -> PortalServiceRequest:
        """Submit a draft request."""
        request = await self._get_request(request_id, user_id)
        if not request:
            raise ValueError("Request not found")

        if request.status != ServiceRequestStatus.DRAFT:
            raise ValueError("Only draft requests can be submitted")

        old_status = request.status
        request.status = ServiceRequestStatus.SUBMITTED

        await self._add_history(
            request_id,
            old_status,
            ServiceRequestStatus.SUBMITTED,
            "CUSTOMER",
            user_id,
            "Request submitted",
        )

        return request

    # =========================================================================
    # Prepayment Request
    # =========================================================================

    async def create_prepayment_request(
        self,
        organization_id: UUID,
        user_id: UUID,
        loan_account_id: UUID,
        prepayment_amount: Decimal,
        prepayment_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """Create a prepayment request with quote."""
        # Get prepayment quote from dashboard service
        # This would calculate charges, interest adjustment, etc.
        quote = await self._get_prepayment_quote(
            loan_account_id, prepayment_amount, prepayment_date
        )

        request = await self.create_request(
            organization_id=organization_id,
            user_id=user_id,
            loan_account_id=loan_account_id,
            request_type=ServiceRequestType.PREPAYMENT,
            subject=f"Prepayment Request - ₹{prepayment_amount:,.2f}",
            prepayment_amount=prepayment_amount,
        )

        request.quote_amount = Decimal(str(quote.get("total_payable", 0)))
        request.quote_valid_until = datetime.fromisoformat(quote.get("valid_until"))
        request.quote_breakdown = str(quote)

        # Auto-submit prepayment requests
        request.status = ServiceRequestStatus.SUBMITTED

        await self._add_history(
            request.id,
            ServiceRequestStatus.DRAFT,
            ServiceRequestStatus.SUBMITTED,
            "SYSTEM",
            None,
            "Auto-submitted prepayment request",
        )

        return {
            "request_id": str(request.id),
            "request_number": request.request_number,
            "quote": quote,
            "status": request.status.value,
        }

    # =========================================================================
    # Foreclosure Request
    # =========================================================================

    async def create_foreclosure_request(
        self,
        organization_id: UUID,
        user_id: UUID,
        loan_account_id: UUID,
        foreclosure_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """Create a foreclosure request with quote."""
        # Get foreclosure quote
        quote = await self._get_foreclosure_quote(loan_account_id, foreclosure_date)

        request = await self.create_request(
            organization_id=organization_id,
            user_id=user_id,
            loan_account_id=loan_account_id,
            request_type=ServiceRequestType.FORECLOSURE,
            subject="Loan Foreclosure Request",
            foreclosure_amount=Decimal(str(quote.get("total_payable", 0))),
        )

        request.quote_amount = Decimal(str(quote.get("total_payable", 0)))
        request.quote_valid_until = datetime.fromisoformat(quote.get("valid_until"))
        request.quote_breakdown = str(quote)

        # Auto-submit foreclosure requests
        request.status = ServiceRequestStatus.SUBMITTED

        await self._add_history(
            request.id,
            ServiceRequestStatus.DRAFT,
            ServiceRequestStatus.SUBMITTED,
            "SYSTEM",
            None,
            "Auto-submitted foreclosure request",
        )

        return {
            "request_id": str(request.id),
            "request_number": request.request_number,
            "quote": quote,
            "status": request.status.value,
        }

    # =========================================================================
    # EMI Date Change
    # =========================================================================

    async def create_emi_date_change_request(
        self,
        organization_id: UUID,
        user_id: UUID,
        loan_account_id: UUID,
        current_emi_date: int,
        new_emi_date: int,
        effective_from: date,
        reason: Optional[str] = None,
    ) -> PortalServiceRequest:
        """Create EMI date change request."""
        if new_emi_date < 1 or new_emi_date > 28:
            raise ValueError("EMI date must be between 1 and 28")

        request = await self.create_request(
            organization_id=organization_id,
            user_id=user_id,
            loan_account_id=loan_account_id,
            request_type=ServiceRequestType.EMI_DATE_CHANGE,
            subject=f"EMI Date Change Request - Day {current_emi_date} to Day {new_emi_date}",
            description=reason,
            current_emi_date=current_emi_date,
            new_emi_date=new_emi_date,
            effective_from=effective_from,
        )

        return request

    # =========================================================================
    # Get Requests
    # =========================================================================

    async def get_requests(
        self,
        user_id: UUID,
        loan_account_id: Optional[UUID] = None,
        request_type: Optional[ServiceRequestType] = None,
        status: Optional[ServiceRequestStatus] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Get service requests for a user."""
        stmt = select(PortalServiceRequest).where(
            PortalServiceRequest.user_id == user_id
        )

        if loan_account_id:
            stmt = stmt.where(PortalServiceRequest.loan_account_id == loan_account_id)

        if request_type:
            stmt = stmt.where(PortalServiceRequest.request_type == request_type)

        if status:
            stmt = stmt.where(PortalServiceRequest.status == status)

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar()

        # Get paginated results
        stmt = stmt.order_by(PortalServiceRequest.created_at.desc())
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(stmt)
        requests = list(result.scalars().all())

        items = [
            {
                "id": str(req.id),
                "request_number": req.request_number,
                "request_type": req.request_type.value,
                "subject": req.subject,
                "status": req.status.value,
                "status_message": req.status_message,
                "created_at": req.created_at.isoformat(),
                "sla_due_at": req.sla_due_at.isoformat() if req.sla_due_at else None,
                "is_sla_breached": req.is_sla_breached,
            }
            for req in requests
        ]

        return items, total

    async def get_request_details(
        self,
        request_id: UUID,
        user_id: UUID,
    ) -> Optional[Dict[str, Any]]:
        """Get detailed service request information."""
        stmt = (
            select(PortalServiceRequest)
            .options(
                selectinload(PortalServiceRequest.documents),
                selectinload(PortalServiceRequest.history),
            )
            .where(
                and_(
                    PortalServiceRequest.id == request_id,
                    PortalServiceRequest.user_id == user_id,
                )
            )
        )
        result = await self.db.execute(stmt)
        request = result.scalar_one_or_none()

        if not request:
            return None

        return {
            "id": str(request.id),
            "request_number": request.request_number,
            "request_type": request.request_type.value,
            "subject": request.subject,
            "description": request.description,
            "status": request.status.value,
            "status_message": request.status_message,
            "created_at": request.created_at.isoformat(),
            "sla_due_at": request.sla_due_at.isoformat() if request.sla_due_at else None,
            "is_sla_breached": request.is_sla_breached,
            # Type-specific fields
            "requested_amount": float(request.requested_amount) if request.requested_amount else None,
            "quote_amount": float(request.quote_amount) if request.quote_amount else None,
            "quote_valid_until": request.quote_valid_until.isoformat() if request.quote_valid_until else None,
            "current_emi_date": request.current_emi_date,
            "requested_emi_date": request.requested_emi_date,
            # Documents
            "documents": [
                {
                    "id": str(doc.id),
                    "document_name": doc.document_name,
                    "document_type": doc.document_type,
                    "is_verified": doc.is_verified,
                }
                for doc in request.documents
            ],
            # History
            "history": [
                {
                    "from_status": h.from_status.value if h.from_status else None,
                    "to_status": h.to_status.value,
                    "change_reason": h.change_reason,
                    "remarks": h.remarks,
                    "changed_by_type": h.changed_by_type,
                    "changed_at": h.changed_at.isoformat(),
                }
                for h in sorted(request.history, key=lambda x: x.changed_at)
            ],
        }

    # =========================================================================
    # Document Upload
    # =========================================================================

    async def upload_document(
        self,
        request_id: UUID,
        user_id: UUID,
        document_name: str,
        document_type: str,
        file_name: str,
        file_type: str,
        file_size: int,
        file_path: str,
        file_hash: Optional[str] = None,
    ) -> PortalServiceRequestDocument:
        """Upload a document for a service request."""
        request = await self._get_request(request_id, user_id)
        if not request:
            raise ValueError("Request not found")

        if request.status not in [
            ServiceRequestStatus.DRAFT,
            ServiceRequestStatus.PENDING_DOCUMENTS,
        ]:
            raise ValueError("Cannot upload documents to this request")

        document = PortalServiceRequestDocument(
            service_request_id=request_id,
            document_name=document_name,
            document_type=document_type,
            file_name=file_name,
            file_type=file_type,
            file_size=file_size,
            file_path=file_path,
            file_hash=file_hash,
            uploaded_by="CUSTOMER",
        )
        self.db.add(document)

        return document

    # =========================================================================
    # Cancel Request
    # =========================================================================

    async def cancel_request(
        self,
        request_id: UUID,
        user_id: UUID,
        reason: str,
    ) -> bool:
        """Cancel a service request."""
        request = await self._get_request(request_id, user_id)
        if not request:
            return False

        # Can only cancel requests in certain statuses
        cancellable_statuses = [
            ServiceRequestStatus.DRAFT,
            ServiceRequestStatus.SUBMITTED,
            ServiceRequestStatus.UNDER_REVIEW,
            ServiceRequestStatus.PENDING_DOCUMENTS,
            ServiceRequestStatus.PENDING_PAYMENT,
        ]

        if request.status not in cancellable_statuses:
            return False

        old_status = request.status
        request.status = ServiceRequestStatus.CANCELLED
        request.cancelled_at = datetime.utcnow()
        request.cancelled_by = user_id
        request.cancellation_reason = reason

        await self._add_history(
            request_id,
            old_status,
            ServiceRequestStatus.CANCELLED,
            "CUSTOMER",
            user_id,
            f"Cancelled: {reason}",
        )

        return True

    # =========================================================================
    # Feedback
    # =========================================================================

    async def submit_feedback(
        self,
        request_id: UUID,
        user_id: UUID,
        rating: int,
        feedback: Optional[str] = None,
    ) -> bool:
        """Submit feedback for a completed request."""
        if rating < 1 or rating > 5:
            raise ValueError("Rating must be between 1 and 5")

        request = await self._get_request(request_id, user_id)
        if not request:
            return False

        if request.status != ServiceRequestStatus.COMPLETED:
            return False

        request.customer_rating = rating
        request.customer_feedback = feedback
        request.feedback_at = datetime.utcnow()

        return True

    # =========================================================================
    # Private Methods
    # =========================================================================

    def _generate_request_number(self) -> str:
        """Generate unique request number."""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        random_suffix = secrets.token_hex(3).upper()
        return f"SR{timestamp}{random_suffix}"

    async def _get_request(
        self,
        request_id: UUID,
        user_id: UUID,
    ) -> Optional[PortalServiceRequest]:
        """Get a service request."""
        stmt = select(PortalServiceRequest).where(
            and_(
                PortalServiceRequest.id == request_id,
                PortalServiceRequest.user_id == user_id,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _add_history(
        self,
        request_id: UUID,
        from_status: Optional[ServiceRequestStatus],
        to_status: ServiceRequestStatus,
        changed_by_type: str,
        changed_by_id: Optional[UUID],
        remarks: Optional[str] = None,
        ip_address: Optional[str] = None,
    ):
        """Add status change to history."""
        history = PortalServiceRequestHistory(
            service_request_id=request_id,
            from_status=from_status,
            to_status=to_status,
            changed_by_type=changed_by_type,
            changed_by_id=changed_by_id,
            remarks=remarks,
            ip_address=ip_address,
        )
        self.db.add(history)

    async def _get_prepayment_quote(
        self,
        loan_account_id: UUID,
        amount: Decimal,
        prepayment_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """Get prepayment quote from lending module."""
        # This would call the dashboard service or lending module
        if not prepayment_date:
            prepayment_date = date.today()

        return {
            "prepayment_amount": float(amount),
            "prepayment_charges": 0,
            "interest_till_date": 0,
            "total_payable": float(amount),
            "valid_until": (datetime.utcnow() + timedelta(days=1)).isoformat(),
        }

    async def _get_foreclosure_quote(
        self,
        loan_account_id: UUID,
        foreclosure_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """Get foreclosure quote from lending module."""
        if not foreclosure_date:
            foreclosure_date = date.today()

        return {
            "principal_outstanding": 0,
            "interest_till_date": 0,
            "foreclosure_charges": 0,
            "other_charges": 0,
            "total_payable": 0,
            "valid_until": (datetime.utcnow() + timedelta(days=1)).isoformat(),
        }
