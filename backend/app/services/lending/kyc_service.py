"""KYC service for the lending module."""

from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lending.kyc import (
    KYCDocumentType,
    EntityKYCDocument,
    CKYCTransaction,
    BureauPull,
    BureauReport,
)
from app.models.lending.enums import (
    KYCDocCategory,
    KYCVerificationStatus,
    KYCVerificationMethod,
    CKYCTransactionType,
    BureauType,
    BureauPullStatus,
    EntityType,
)
from app.schemas.lending.kyc import (
    KYCDocumentTypeCreate,
    KYCDocumentTypeUpdate,
    EntityKYCDocumentCreate,
    EntityKYCDocumentUpdate,
    CKYCSearchRequest,
    CKYCDownloadRequest,
    BureauPullRequest,
)
from app.repositories.lending.kyc_repo import (
    KYCDocumentTypeRepository,
    EntityKYCDocumentRepository,
    CKYCTransactionRepository,
    BureauPullRepository,
    BureauReportRepository,
)
from app.repositories.lending.entity_repo import EntityRepository
from app.core.exceptions import NotFoundException, ConflictException, ValidationException


class KYCService:
    """Service for KYC operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.doc_type_repo = KYCDocumentTypeRepository(session)
        self.entity_kyc_repo = EntityKYCDocumentRepository(session)
        self.ckyc_repo = CKYCTransactionRepository(session)
        self.bureau_pull_repo = BureauPullRepository(session)
        self.bureau_report_repo = BureauReportRepository(session)
        self.entity_repo = EntityRepository(session)

    # =========================================================================
    # KYC Document Type Operations
    # =========================================================================

    async def create_document_type(
        self, data: KYCDocumentTypeCreate, created_by: UUID
    ) -> KYCDocumentType:
        """Create a new KYC document type."""
        existing = await self.doc_type_repo.get_by_code(data.code, data.organization_id)
        if existing:
            raise ConflictException(f"Document type with code '{data.code}' already exists")

        doc_type = KYCDocumentType(
            **data.model_dump(),
            created_by=created_by,
        )
        self.session.add(doc_type)
        await self.session.commit()
        await self.session.refresh(doc_type)
        return doc_type

    async def update_document_type(
        self, id: UUID, data: KYCDocumentTypeUpdate, updated_by: UUID
    ) -> KYCDocumentType:
        """Update a KYC document type."""
        doc_type = await self.doc_type_repo.get(id)
        if not doc_type:
            raise NotFoundException("Document type not found")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(doc_type, field, value)
        doc_type.updated_by = updated_by

        await self.session.commit()
        await self.session.refresh(doc_type)
        return doc_type

    async def get_document_type(self, id: UUID) -> KYCDocumentType:
        """Get KYC document type by ID."""
        doc_type = await self.doc_type_repo.get(id)
        if not doc_type:
            raise NotFoundException("Document type not found")
        return doc_type

    async def get_all_document_types(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
        category: Optional[KYCDocCategory] = None,
        entity_type: Optional[EntityType] = None,
    ) -> Tuple[List[KYCDocumentType], int]:
        """Get all KYC document types."""
        return await self.doc_type_repo.get_all_by_organization(
            organization_id=organization_id,
            skip=skip,
            limit=limit,
            include_inactive=include_inactive,
            category=category,
            entity_type=entity_type,
        )

    async def get_mandatory_document_types(
        self,
        organization_id: UUID,
        entity_type: Optional[EntityType] = None,
    ) -> List[KYCDocumentType]:
        """Get mandatory KYC document types."""
        return await self.doc_type_repo.get_mandatory_documents(
            organization_id, entity_type
        )

    # =========================================================================
    # Entity KYC Document Operations
    # =========================================================================

    async def upload_kyc_document(
        self, data: EntityKYCDocumentCreate, created_by: UUID
    ) -> EntityKYCDocument:
        """Upload a KYC document for an entity."""
        # Verify entity exists
        entity = await self.entity_repo.get(data.entity_id)
        if not entity:
            raise NotFoundException("Entity not found")

        # Verify document type exists
        doc_type = await self.doc_type_repo.get(data.document_type_id)
        if not doc_type:
            raise NotFoundException("Document type not found")

        kyc_doc = EntityKYCDocument(
            **data.model_dump(),
            created_by=created_by,
        )
        self.session.add(kyc_doc)
        await self.session.commit()
        await self.session.refresh(kyc_doc)
        return kyc_doc

    async def update_kyc_document(
        self, id: UUID, data: EntityKYCDocumentUpdate, updated_by: UUID
    ) -> EntityKYCDocument:
        """Update a KYC document."""
        kyc_doc = await self.entity_kyc_repo.get(id)
        if not kyc_doc:
            raise NotFoundException("KYC document not found")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(kyc_doc, field, value)
        kyc_doc.updated_by = updated_by

        await self.session.commit()
        await self.session.refresh(kyc_doc)
        return kyc_doc

    async def verify_kyc_document(
        self,
        id: UUID,
        verification_method: KYCVerificationMethod,
        verified_by: UUID,
        remarks: Optional[str] = None,
    ) -> EntityKYCDocument:
        """Verify a KYC document."""
        kyc_doc = await self.entity_kyc_repo.get(id)
        if not kyc_doc:
            raise NotFoundException("KYC document not found")

        kyc_doc.verification_status = KYCVerificationStatus.VERIFIED
        kyc_doc.verification_method = verification_method
        kyc_doc.verified_by_id = verified_by
        kyc_doc.verified_at = datetime.utcnow()
        kyc_doc.verification_remarks = remarks
        kyc_doc.updated_by = verified_by

        await self.session.commit()
        await self.session.refresh(kyc_doc)
        return kyc_doc

    async def reject_kyc_document(
        self,
        id: UUID,
        rejection_reason: str,
        rejected_by: UUID,
    ) -> EntityKYCDocument:
        """Reject a KYC document."""
        kyc_doc = await self.entity_kyc_repo.get(id)
        if not kyc_doc:
            raise NotFoundException("KYC document not found")

        kyc_doc.verification_status = KYCVerificationStatus.REJECTED
        kyc_doc.rejection_reason = rejection_reason
        kyc_doc.verified_by_id = rejected_by
        kyc_doc.verified_at = datetime.utcnow()
        kyc_doc.updated_by = rejected_by

        await self.session.commit()
        await self.session.refresh(kyc_doc)
        return kyc_doc

    async def get_entity_kyc_documents(
        self, entity_id: UUID, include_inactive: bool = False
    ) -> List[EntityKYCDocument]:
        """Get all KYC documents for an entity."""
        return await self.entity_kyc_repo.get_by_entity(entity_id, include_inactive)

    async def check_kyc_complete(
        self, entity_id: UUID, organization_id: UUID
    ) -> Dict[str, Any]:
        """Check KYC completion status for an entity."""
        entity = await self.entity_repo.get(entity_id)
        if not entity:
            raise NotFoundException("Entity not found")

        # Get mandatory document types for the entity type
        mandatory_types = await self.doc_type_repo.get_mandatory_documents(
            organization_id, entity.entity_type
        )

        # Get entity's KYC documents
        entity_docs = await self.entity_kyc_repo.get_by_entity(entity_id)

        # Check status
        mandatory_ids = {dt.id for dt in mandatory_types}
        verified_ids = {
            doc.document_type_id
            for doc in entity_docs
            if doc.verification_status == KYCVerificationStatus.VERIFIED
        }
        pending_ids = {
            doc.document_type_id
            for doc in entity_docs
            if doc.verification_status == KYCVerificationStatus.PENDING
        }

        missing_ids = mandatory_ids - (verified_ids | pending_ids)

        return {
            "is_complete": len(missing_ids) == 0 and len(pending_ids) == 0,
            "total_mandatory": len(mandatory_ids),
            "verified_count": len(verified_ids & mandatory_ids),
            "pending_count": len(pending_ids & mandatory_ids),
            "missing_count": len(missing_ids),
            "missing_documents": [
                dt for dt in mandatory_types if dt.id in missing_ids
            ],
        }

    # =========================================================================
    # CKYC Operations
    # =========================================================================

    async def search_ckyc(
        self, request: CKYCSearchRequest, initiated_by: UUID
    ) -> CKYCTransaction:
        """Search CKYC registry by PAN."""
        entity = await self.entity_repo.get(request.entity_id)
        if not entity:
            raise NotFoundException("Entity not found")

        # Create transaction record
        transaction = CKYCTransaction(
            entity_id=request.entity_id,
            transaction_type=CKYCTransactionType.SEARCH,
            search_pan=request.pan.upper(),
            search_dob=request.date_of_birth,
            search_mobile=request.mobile_number,
            status="INITIATED",
            initiated_by_id=initiated_by,
            initiated_at=datetime.utcnow(),
        )
        self.session.add(transaction)
        await self.session.flush()

        # TODO: Call actual CKYC API
        # For now, simulate a response
        transaction.status = "SUCCESS"
        transaction.completed_at = datetime.utcnow()
        transaction.response_payload = {
            "message": "CKYC search completed - integration pending"
        }

        await self.session.commit()
        await self.session.refresh(transaction)
        return transaction

    async def download_ckyc(
        self, request: CKYCDownloadRequest, initiated_by: UUID
    ) -> CKYCTransaction:
        """Download CKYC record."""
        entity = await self.entity_repo.get(request.entity_id)
        if not entity:
            raise NotFoundException("Entity not found")

        transaction = CKYCTransaction(
            entity_id=request.entity_id,
            transaction_type=CKYCTransactionType.DOWNLOAD,
            ckyc_number=request.ckyc_number,
            status="INITIATED",
            initiated_by_id=initiated_by,
            initiated_at=datetime.utcnow(),
        )
        self.session.add(transaction)
        await self.session.flush()

        # TODO: Call actual CKYC API
        transaction.status = "SUCCESS"
        transaction.completed_at = datetime.utcnow()
        transaction.response_payload = {
            "message": "CKYC download completed - integration pending"
        }

        # Update entity CKYC number
        entity.ckyc_number = request.ckyc_number

        await self.session.commit()
        await self.session.refresh(transaction)
        return transaction

    async def get_ckyc_transactions(
        self, entity_id: UUID
    ) -> List[CKYCTransaction]:
        """Get all CKYC transactions for an entity."""
        return await self.ckyc_repo.get_by_entity(entity_id)

    # =========================================================================
    # Credit Bureau Operations
    # =========================================================================

    async def initiate_bureau_pull(
        self, request: BureauPullRequest, initiated_by: UUID
    ) -> BureauPull:
        """Initiate credit bureau pull."""
        entity = await self.entity_repo.get(request.entity_id)
        if not entity:
            raise NotFoundException("Entity not found")

        # Check if we have a recent valid pull
        existing = await self.bureau_pull_repo.get_latest_by_bureau(
            request.entity_id, request.bureau_type
        )
        if existing and existing.report_valid_till and existing.report_valid_till >= date.today():
            raise ValidationException(
                f"A valid {request.bureau_type.value} report exists until {existing.report_valid_till}"
            )

        bureau_pull = BureauPull(
            entity_id=request.entity_id,
            bureau_type=request.bureau_type,
            consent_id=request.consent_id,
            consent_timestamp=request.consent_timestamp,
            request_payload={
                "pan": request.pan,
                "name": request.name,
                "dob": str(request.date_of_birth) if request.date_of_birth else None,
                "mobile": request.mobile,
                "email": request.email,
                "cin": request.cin,
                "purpose": request.purpose,
                "inquiry_amount": float(request.inquiry_amount) if request.inquiry_amount else None,
            },
            status=BureauPullStatus.INITIATED,
            initiated_by_id=initiated_by,
            initiated_at=datetime.utcnow(),
        )
        self.session.add(bureau_pull)
        await self.session.flush()

        # TODO: Call actual bureau API
        # For now, simulate a response
        bureau_pull.status = BureauPullStatus.SUCCESS
        bureau_pull.completed_at = datetime.utcnow()
        bureau_pull.pull_reference_number = f"{request.bureau_type.value}-{bureau_pull.id}"
        bureau_pull.report_valid_till = date.today().replace(
            month=date.today().month + 3 if date.today().month <= 9 else (date.today().month + 3) % 12,
            year=date.today().year if date.today().month <= 9 else date.today().year + 1,
        )

        # Create a sample bureau report
        bureau_report = BureauReport(
            bureau_pull_id=bureau_pull.id,
            report_reference_number=bureau_pull.pull_reference_number,
            report_date=date.today(),
            credit_score=750,  # Sample score
            total_accounts=5,
            active_accounts=3,
            closed_accounts=2,
            overdue_accounts=0,
            raw_report={"message": "Bureau integration pending - sample data"},
        )
        self.session.add(bureau_report)

        await self.session.commit()
        await self.session.refresh(bureau_pull)
        return bureau_pull

    async def get_bureau_pulls(
        self, entity_id: UUID, include_failed: bool = False
    ) -> List[BureauPull]:
        """Get all bureau pulls for an entity."""
        return await self.bureau_pull_repo.get_by_entity(entity_id, include_failed)

    async def get_bureau_report(
        self, bureau_pull_id: UUID
    ) -> Optional[BureauReport]:
        """Get bureau report for a pull."""
        return await self.bureau_report_repo.get_by_pull(bureau_pull_id)

    async def get_latest_credit_score(
        self,
        entity_id: UUID,
        bureau_type: Optional[BureauType] = None,
    ) -> Optional[int]:
        """Get latest credit score for an entity."""
        return await self.bureau_report_repo.get_latest_score(entity_id, bureau_type)
