"""Portal Document Service.

Handles document access, generation, and requests.
"""

import secrets
from datetime import date, datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from uuid import UUID

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.portal.document import (
    PortalDocument,
    PortalDocumentRequest,
    PortalKYCVerification,
)
from app.models.portal.enums import (
    PortalDocumentType,
    DocumentRequestStatus,
    KYCType,
    KYCStatus,
)


class PortalDocumentService:
    """Portal document service."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # Document Access
    # =========================================================================

    async def get_documents(
        self,
        user_id: UUID,
        loan_account_id: Optional[UUID] = None,
        document_type: Optional[PortalDocumentType] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Get documents available to the user."""
        stmt = select(PortalDocument).where(
            and_(
                PortalDocument.user_id == user_id,
                PortalDocument.is_active == True,
            )
        )

        if loan_account_id:
            stmt = stmt.where(PortalDocument.loan_account_id == loan_account_id)

        if document_type:
            stmt = stmt.where(PortalDocument.document_type == document_type)

        # Check expiry
        stmt = stmt.where(
            or_(
                PortalDocument.expires_at.is_(None),
                PortalDocument.expires_at > datetime.utcnow(),
            )
        )

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar()

        # Get paginated results
        stmt = stmt.order_by(PortalDocument.created_at.desc())
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(stmt)
        documents = list(result.scalars().all())

        items = [
            {
                "id": str(doc.id),
                "document_type": doc.document_type.value,
                "document_name": doc.document_name,
                "description": doc.description,
                "file_name": doc.file_name,
                "file_type": doc.file_type,
                "file_size": doc.file_size,
                "document_date": doc.document_date.isoformat() if doc.document_date else None,
                "is_downloadable": doc.is_downloadable,
                "requires_otp": doc.requires_otp,
            }
            for doc in documents
        ]

        return items, total

    async def get_document(
        self,
        document_id: UUID,
        user_id: UUID,
    ) -> Optional[PortalDocument]:
        """Get a specific document."""
        stmt = select(PortalDocument).where(
            and_(
                PortalDocument.id == document_id,
                PortalDocument.user_id == user_id,
                PortalDocument.is_active == True,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def download_document(
        self,
        document_id: UUID,
        user_id: UUID,
    ) -> Optional[Dict[str, Any]]:
        """Get document download details."""
        document = await self.get_document(document_id, user_id)

        if not document:
            return None

        if not document.is_downloadable:
            return {"error": "Document is not downloadable"}

        # Update download tracking
        document.download_count += 1
        document.last_downloaded_at = datetime.utcnow()

        return {
            "file_path": document.file_path,
            "file_name": document.file_name,
            "file_type": document.file_type,
            "is_watermarked": document.is_watermarked,
        }

    async def record_view(
        self,
        document_id: UUID,
        user_id: UUID,
    ) -> bool:
        """Record document view."""
        document = await self.get_document(document_id, user_id)

        if document:
            document.view_count += 1
            document.last_viewed_at = datetime.utcnow()
            return True
        return False

    # =========================================================================
    # Document Generation
    # =========================================================================

    async def generate_account_statement(
        self,
        organization_id: UUID,
        user_id: UUID,
        loan_account_id: UUID,
        from_date: date,
        to_date: date,
    ) -> PortalDocument:
        """Generate account statement document."""
        # This would call the lending module to generate the statement
        # Placeholder implementation

        file_name = f"statement_{loan_account_id}_{from_date}_{to_date}.pdf"

        document = PortalDocument(
            organization_id=organization_id,
            user_id=user_id,
            loan_account_id=loan_account_id,
            document_type=PortalDocumentType.ACCOUNT_STATEMENT,
            document_name=f"Account Statement ({from_date} to {to_date})",
            file_name=file_name,
            file_type="application/pdf",
            file_size=0,  # Would be updated after generation
            file_path=f"/documents/statements/{file_name}",
            period_from=from_date,
            period_to=to_date,
            is_auto_generated=True,
            expires_at=datetime.utcnow() + timedelta(days=30),
        )
        self.db.add(document)

        # TODO: Generate actual PDF
        # pdf_content = await self._generate_statement_pdf(loan_account_id, from_date, to_date)
        # document.file_size = len(pdf_content)
        # await self._save_document_file(document.file_path, pdf_content)

        return document

    async def generate_interest_certificate(
        self,
        organization_id: UUID,
        user_id: UUID,
        loan_account_id: UUID,
        financial_year: str,
    ) -> PortalDocument:
        """Generate interest certificate for tax purposes."""
        file_name = f"interest_cert_{loan_account_id}_{financial_year}.pdf"

        document = PortalDocument(
            organization_id=organization_id,
            user_id=user_id,
            loan_account_id=loan_account_id,
            document_type=PortalDocumentType.INTEREST_CERTIFICATE,
            document_name=f"Interest Certificate FY {financial_year}",
            file_name=file_name,
            file_type="application/pdf",
            file_size=0,
            file_path=f"/documents/certificates/{file_name}",
            financial_year=financial_year,
            is_auto_generated=True,
            expires_at=datetime.utcnow() + timedelta(days=365),
        )
        self.db.add(document)

        return document

    async def generate_tds_certificate(
        self,
        organization_id: UUID,
        user_id: UUID,
        loan_account_id: UUID,
        financial_year: str,
        quarter: str,
    ) -> PortalDocument:
        """Generate TDS certificate (Form 16A)."""
        file_name = f"tds_cert_{loan_account_id}_{financial_year}_{quarter}.pdf"

        document = PortalDocument(
            organization_id=organization_id,
            user_id=user_id,
            loan_account_id=loan_account_id,
            document_type=PortalDocumentType.TDS_CERTIFICATE,
            document_name=f"TDS Certificate FY {financial_year} {quarter}",
            file_name=file_name,
            file_type="application/pdf",
            file_size=0,
            file_path=f"/documents/tds/{file_name}",
            financial_year=financial_year,
            is_auto_generated=True,
            expires_at=datetime.utcnow() + timedelta(days=365),
        )
        self.db.add(document)

        return document

    # =========================================================================
    # Document Requests
    # =========================================================================

    async def create_document_request(
        self,
        organization_id: UUID,
        user_id: UUID,
        loan_account_id: Optional[UUID],
        document_type: PortalDocumentType,
        reason: Optional[str] = None,
        delivery_mode: str = "DOWNLOAD",
        delivery_email: Optional[str] = None,
        delivery_address: Optional[str] = None,
        period_from: Optional[date] = None,
        period_to: Optional[date] = None,
        financial_year: Optional[str] = None,
    ) -> PortalDocumentRequest:
        """Create a document request."""
        request_number = self._generate_request_number()

        request = PortalDocumentRequest(
            organization_id=organization_id,
            user_id=user_id,
            loan_account_id=loan_account_id,
            request_number=request_number,
            document_type=document_type,
            request_reason=reason,
            delivery_mode=delivery_mode,
            delivery_email=delivery_email,
            delivery_address=delivery_address,
            period_from=period_from,
            period_to=period_to,
            financial_year=financial_year,
            status=DocumentRequestStatus.REQUESTED,
        )
        self.db.add(request)

        return request

    async def get_document_requests(
        self,
        user_id: UUID,
        status: Optional[DocumentRequestStatus] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Get document requests for a user."""
        stmt = select(PortalDocumentRequest).where(
            PortalDocumentRequest.user_id == user_id
        )

        if status:
            stmt = stmt.where(PortalDocumentRequest.status == status)

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar()

        # Get paginated results
        stmt = stmt.order_by(PortalDocumentRequest.created_at.desc())
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(stmt)
        requests = list(result.scalars().all())

        items = [
            {
                "id": str(req.id),
                "request_number": req.request_number,
                "document_type": req.document_type.value,
                "status": req.status.value,
                "status_message": req.status_message,
                "created_at": req.created_at.isoformat(),
                "fulfilled_at": req.fulfilled_at.isoformat() if req.fulfilled_at else None,
            }
            for req in requests
        ]

        return items, total

    async def get_document_request(
        self,
        request_id: UUID,
        user_id: UUID,
    ) -> Optional[PortalDocumentRequest]:
        """Get a specific document request."""
        stmt = select(PortalDocumentRequest).where(
            and_(
                PortalDocumentRequest.id == request_id,
                PortalDocumentRequest.user_id == user_id,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    # =========================================================================
    # KYC Verification
    # =========================================================================

    async def initiate_aadhaar_kyc(
        self,
        organization_id: UUID,
        user_id: UUID,
        customer_id: UUID,
        aadhaar_last4: str,
        consent_text: str,
        ip_address: Optional[str] = None,
        device_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Initiate Aadhaar eKYC."""
        reference_number = self._generate_kyc_reference()

        kyc = PortalKYCVerification(
            organization_id=organization_id,
            user_id=user_id,
            customer_id=customer_id,
            kyc_type=KYCType.AADHAAR_OTP,
            reference_number=reference_number,
            aadhaar_last4=aadhaar_last4,
            status=KYCStatus.INITIATED,
            ip_address=ip_address,
            device_id=device_id,
            consent_captured=True,
            consent_timestamp=datetime.utcnow(),
            consent_text=consent_text,
            expires_at=datetime.utcnow() + timedelta(minutes=10),
        )
        self.db.add(kyc)
        await self.db.flush()

        # Initiate Aadhaar OTP request via UIDAI
        # This would integrate with UIDAI or certified ASA
        otp_result = await self._request_aadhaar_otp(aadhaar_last4)

        if otp_result.get("success"):
            kyc.aadhaar_reference_id = otp_result.get("reference_id")
            kyc.otp_sent_at = datetime.utcnow()
            kyc.status = KYCStatus.IN_PROGRESS
            kyc.provider_name = otp_result.get("provider")
            kyc.provider_txn_id = otp_result.get("txn_id")

        return {
            "kyc_id": str(kyc.id),
            "reference_number": reference_number,
            "status": kyc.status.value,
            "otp_sent": otp_result.get("success", False),
            "expires_at": kyc.expires_at.isoformat(),
        }

    async def verify_aadhaar_otp(
        self,
        kyc_id: UUID,
        user_id: UUID,
        otp: str,
    ) -> Dict[str, Any]:
        """Verify Aadhaar OTP and complete eKYC."""
        stmt = select(PortalKYCVerification).where(
            and_(
                PortalKYCVerification.id == kyc_id,
                PortalKYCVerification.user_id == user_id,
                PortalKYCVerification.status == KYCStatus.IN_PROGRESS,
                PortalKYCVerification.expires_at > datetime.utcnow(),
            )
        )
        result = await self.db.execute(stmt)
        kyc = result.scalar_one_or_none()

        if not kyc:
            return {"success": False, "error": "KYC request not found or expired"}

        # Verify OTP with UIDAI
        verification = await self._verify_aadhaar_otp(
            kyc.aadhaar_reference_id, otp
        )

        if verification.get("success"):
            kyc.status = KYCStatus.COMPLETED
            kyc.otp_verified_at = datetime.utcnow()
            kyc.completed_at = datetime.utcnow()
            kyc.verified_name = verification.get("name")
            kyc.verified_dob = verification.get("dob")
            kyc.verified_gender = verification.get("gender")
            kyc.verified_address = verification.get("address")
            kyc.photo_match_score = verification.get("photo_match_score")

            return {
                "success": True,
                "kyc_id": str(kyc.id),
                "verified_data": {
                    "name": kyc.verified_name,
                    "dob": kyc.verified_dob.isoformat() if kyc.verified_dob else None,
                    "gender": kyc.verified_gender,
                },
            }
        else:
            kyc.status = KYCStatus.FAILED
            kyc.status_message = verification.get("error")
            return {"success": False, "error": verification.get("error")}

    async def initiate_pan_verification(
        self,
        organization_id: UUID,
        user_id: UUID,
        customer_id: UUID,
        pan_number: str,
        name_to_match: str,
    ) -> Dict[str, Any]:
        """Initiate PAN verification."""
        reference_number = self._generate_kyc_reference()

        kyc = PortalKYCVerification(
            organization_id=organization_id,
            user_id=user_id,
            customer_id=customer_id,
            kyc_type=KYCType.PAN_VERIFICATION,
            reference_number=reference_number,
            pan_number=pan_number,
            status=KYCStatus.INITIATED,
        )
        self.db.add(kyc)
        await self.db.flush()

        # Verify PAN via NSDL/ITD
        result = await self._verify_pan(pan_number, name_to_match)

        if result.get("verified"):
            kyc.status = KYCStatus.COMPLETED
            kyc.completed_at = datetime.utcnow()
            kyc.verified_name = result.get("name")
            kyc.provider_name = result.get("provider")
            kyc.provider_txn_id = result.get("txn_id")

            return {
                "success": True,
                "kyc_id": str(kyc.id),
                "verified": True,
                "name_match": result.get("name_match"),
                "pan_status": result.get("pan_status"),
            }
        else:
            kyc.status = KYCStatus.FAILED
            kyc.status_message = result.get("error")
            return {
                "success": False,
                "error": result.get("error"),
            }

    async def get_kyc_history(
        self,
        user_id: UUID,
        customer_id: UUID,
    ) -> List[Dict[str, Any]]:
        """Get KYC verification history."""
        stmt = (
            select(PortalKYCVerification)
            .where(
                and_(
                    PortalKYCVerification.user_id == user_id,
                    PortalKYCVerification.customer_id == customer_id,
                )
            )
            .order_by(PortalKYCVerification.created_at.desc())
        )
        result = await self.db.execute(stmt)
        verifications = list(result.scalars().all())

        return [
            {
                "id": str(v.id),
                "kyc_type": v.kyc_type.value,
                "reference_number": v.reference_number,
                "status": v.status.value,
                "initiated_at": v.initiated_at.isoformat(),
                "completed_at": v.completed_at.isoformat() if v.completed_at else None,
            }
            for v in verifications
        ]

    # =========================================================================
    # Private Methods
    # =========================================================================

    def _generate_request_number(self) -> str:
        """Generate unique document request number."""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        random_suffix = secrets.token_hex(3).upper()
        return f"DOC{timestamp}{random_suffix}"

    def _generate_kyc_reference(self) -> str:
        """Generate unique KYC reference number."""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        random_suffix = secrets.token_hex(4).upper()
        return f"KYC{timestamp}{random_suffix}"

    async def _request_aadhaar_otp(
        self,
        aadhaar_last4: str,
    ) -> Dict[str, Any]:
        """Request OTP from UIDAI."""
        # This would integrate with UIDAI via certified ASA
        # Placeholder implementation
        return {
            "success": True,
            "reference_id": f"UIDAI_{secrets.token_hex(8)}",
            "provider": "UIDAI",
            "txn_id": secrets.token_hex(16),
        }

    async def _verify_aadhaar_otp(
        self,
        reference_id: str,
        otp: str,
    ) -> Dict[str, Any]:
        """Verify OTP with UIDAI."""
        # This would verify OTP via UIDAI
        # Placeholder implementation
        return {
            "success": True,
            "name": "Test User",
            "dob": date(1990, 1, 1),
            "gender": "M",
            "address": "Test Address",
        }

    async def _verify_pan(
        self,
        pan_number: str,
        name_to_match: str,
    ) -> Dict[str, Any]:
        """Verify PAN via NSDL."""
        # This would verify PAN via NSDL/ITD
        # Placeholder implementation
        return {
            "verified": True,
            "name": name_to_match,
            "name_match": True,
            "pan_status": "ACTIVE",
            "provider": "NSDL",
            "txn_id": secrets.token_hex(16),
        }
