"""Entity/Borrower API endpoints."""

from datetime import date
from pathlib import Path
from typing import Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequirePermissions
from app.core.exceptions import ValidationException
from app.database import get_db
from app.models.auth.user import User
from app.models.lending.enums import (
    EntityStatus,
    EntityType,
    KYCVerificationMethod,
    RiskCategory,
)
from app.schemas.base import CamelSchema, PaginatedResponse
from app.schemas.lending.entity import (
    EntityAddressCreate,
    EntityAddressResponse,
    EntityAddressUpdate,
    EntityBankAccountCreate,
    EntityBankAccountResponse,
    EntityBankAccountUpdate,
    EntityContactCreate,
    EntityContactResponse,
    EntityContactUpdate,
    EntityCreate,
    EntityDetailResponse,
    EntityFinancialCreate,
    EntityFinancialResponse,
    EntityFinancialUpdate,
    EntityListResponse,
    EntityResponse,
    EntityUpdate,
)
from app.schemas.lending.kyc import EntityKYCDocumentCreate, EntityKYCDocumentResponse
from app.services.lending.entity_service import EntityService
from app.services.lending.kyc_service import KYCService

router = APIRouter()


class EntityKYCVerificationRequest(CamelSchema):
    """Manual KYC verification action payload."""

    status: Literal["VERIFIED", "REJECTED"]
    remarks: str | None = None


# =============================================================================
# Entity CRUD Endpoints
# =============================================================================


@router.get(
    "",
    response_model=PaginatedResponse[EntityListResponse],
    response_model_by_alias=True,
)
async def list_entities(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    include_inactive: bool = Query(False),
    search: str | None = Query(None, description="Search in code, name, PAN, GSTIN"),
    entity_type: EntityType | None = Query(None),
    status: EntityStatus | None = Query(None),
    risk_category: RiskCategory | None = Query(None),
    relationship_manager_id: UUID | None = Query(None),
    current_user: User = Depends(RequirePermissions("LOS_ENTITY_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated list of entities for an organization."""
    service = EntityService(db)
    skip = (page - 1) * page_size
    entities, total = await service.get_all_entities(
        organization_id=current_user.organization_id,
        skip=skip,
        limit=page_size,
        include_inactive=include_inactive,
        search=search,
        entity_type=entity_type,
        status=status,
        risk_category=risk_category,
        relationship_manager_id=relationship_manager_id,
    )
    items = [EntityListResponse.model_validate(e) for e in entities]
    return PaginatedResponse.create(items, total, page, page_size)


@router.get(
    "/active",
    response_model=list[EntityListResponse],
    response_model_by_alias=True,
)
async def list_active_entities(
    entity_type: EntityType | None = Query(None),
    current_user: User = Depends(RequirePermissions("LOS_ENTITY_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """Get active entities for dropdown lists."""
    service = EntityService(db)
    entities = await service.get_active_entities(current_user.organization_id, entity_type)
    return [EntityListResponse.model_validate(e) for e in entities]


@router.post("", response_model=EntityResponse, response_model_by_alias=True)
async def create_entity(
    data: EntityCreate,
    current_user: User = Depends(RequirePermissions("LOS_ENTITY_CREATE")),
    db: AsyncSession = Depends(get_db),
):
    """Create a new entity/borrower."""
    service = EntityService(db)
    data.organization_id = current_user.organization_id
    entity = await service.create_entity(data, current_user.id)
    return EntityResponse.model_validate(entity)


@router.get("/{entity_id}", response_model=EntityResponse, response_model_by_alias=True)
async def get_entity(
    entity_id: UUID,
    current_user: User = Depends(RequirePermissions("LOS_ENTITY_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """Get entity by ID."""
    service = EntityService(db)
    entity = await service.get_entity(entity_id)
    return EntityResponse.model_validate(entity)


@router.get(
    "/{entity_id}/details", response_model=EntityDetailResponse, response_model_by_alias=True
)
async def get_entity_details(
    entity_id: UUID,
    current_user: User = Depends(RequirePermissions("LOS_ENTITY_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """Get entity with all related data."""
    service = EntityService(db)
    entity = await service.get_entity_with_details(entity_id)
    return EntityDetailResponse.model_validate(entity)


@router.put("/{entity_id}", response_model=EntityResponse, response_model_by_alias=True)
async def update_entity(
    entity_id: UUID,
    data: EntityUpdate,
    current_user: User = Depends(RequirePermissions("LOS_ENTITY_UPDATE")),
    db: AsyncSession = Depends(get_db),
):
    """Update an entity."""
    service = EntityService(db)
    entity = await service.update_entity(entity_id, data, current_user.id)
    return EntityResponse.model_validate(entity)


@router.delete("/{entity_id}")
async def delete_entity(
    entity_id: UUID,
    current_user: User = Depends(RequirePermissions("LOS_ENTITY_DELETE")),
    db: AsyncSession = Depends(get_db),
):
    """Soft delete an entity."""
    service = EntityService(db)
    await service.delete_entity(entity_id, current_user.id)
    return {"message": "Entity deleted successfully"}


# =============================================================================
# Entity Contact Endpoints
# =============================================================================


@router.get(
    "/{entity_id}/contacts",
    response_model=list[EntityContactResponse],
    response_model_by_alias=True,
)
async def list_entity_contacts(
    entity_id: UUID,
    include_inactive: bool = Query(False),
    current_user: User = Depends(RequirePermissions("LOS_ENTITY_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """Get all contacts for an entity."""
    service = EntityService(db)
    contacts = await service.get_entity_contacts(entity_id, include_inactive)
    return [EntityContactResponse.model_validate(c) for c in contacts]


@router.post(
    "/{entity_id}/contacts", response_model=EntityContactResponse, response_model_by_alias=True
)
async def add_entity_contact(
    entity_id: UUID,
    data: EntityContactCreate,
    current_user: User = Depends(RequirePermissions("LOS_ENTITY_UPDATE")),
    db: AsyncSession = Depends(get_db),
):
    """Add a contact to an entity."""
    data.entity_id = entity_id
    service = EntityService(db)
    contact = await service.add_contact(data, current_user.id)
    return EntityContactResponse.model_validate(contact)


@router.put(
    "/contacts/{contact_id}", response_model=EntityContactResponse, response_model_by_alias=True
)
async def update_entity_contact(
    contact_id: UUID,
    data: EntityContactUpdate,
    current_user: User = Depends(RequirePermissions("LOS_ENTITY_UPDATE")),
    db: AsyncSession = Depends(get_db),
):
    """Update an entity contact."""
    service = EntityService(db)
    contact = await service.update_contact(contact_id, data, current_user.id)
    return EntityContactResponse.model_validate(contact)


@router.delete("/contacts/{contact_id}")
async def delete_entity_contact(
    contact_id: UUID,
    current_user: User = Depends(RequirePermissions("LOS_ENTITY_DELETE")),
    db: AsyncSession = Depends(get_db),
):
    """Delete an entity contact."""
    service = EntityService(db)
    await service.delete_contact(contact_id, current_user.id)
    return {"message": "Contact deleted successfully"}


# =============================================================================
# Entity Address Endpoints
# =============================================================================


@router.get(
    "/{entity_id}/addresses",
    response_model=list[EntityAddressResponse],
    response_model_by_alias=True,
)
async def list_entity_addresses(
    entity_id: UUID,
    include_inactive: bool = Query(False),
    current_user: User = Depends(RequirePermissions("LOS_ENTITY_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """Get all addresses for an entity."""
    service = EntityService(db)
    addresses = await service.get_entity_addresses(entity_id, include_inactive)
    return [EntityAddressResponse.model_validate(a) for a in addresses]


@router.post(
    "/{entity_id}/addresses", response_model=EntityAddressResponse, response_model_by_alias=True
)
async def add_entity_address(
    entity_id: UUID,
    data: EntityAddressCreate,
    current_user: User = Depends(RequirePermissions("LOS_ENTITY_UPDATE")),
    db: AsyncSession = Depends(get_db),
):
    """Add an address to an entity."""
    data.entity_id = entity_id
    service = EntityService(db)
    address = await service.add_address(data, current_user.id)
    return EntityAddressResponse.model_validate(address)


@router.put(
    "/addresses/{address_id}", response_model=EntityAddressResponse, response_model_by_alias=True
)
async def update_entity_address(
    address_id: UUID,
    data: EntityAddressUpdate,
    current_user: User = Depends(RequirePermissions("LOS_ENTITY_UPDATE")),
    db: AsyncSession = Depends(get_db),
):
    """Update an entity address."""
    service = EntityService(db)
    address = await service.update_address(address_id, data, current_user.id)
    return EntityAddressResponse.model_validate(address)


@router.delete("/addresses/{address_id}")
async def delete_entity_address(
    address_id: UUID,
    current_user: User = Depends(RequirePermissions("LOS_ENTITY_DELETE")),
    db: AsyncSession = Depends(get_db),
):
    """Delete an entity address."""
    service = EntityService(db)
    await service.delete_address(address_id, current_user.id)
    return {"message": "Address deleted successfully"}


# =============================================================================
# Entity Bank Account Endpoints
# =============================================================================


@router.get(
    "/{entity_id}/bank-accounts",
    response_model=list[EntityBankAccountResponse],
    response_model_by_alias=True,
)
async def list_entity_bank_accounts(
    entity_id: UUID,
    include_inactive: bool = Query(False),
    current_user: User = Depends(RequirePermissions("LOS_ENTITY_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """Get all bank accounts for an entity."""
    service = EntityService(db)
    accounts = await service.get_entity_bank_accounts(entity_id, include_inactive)
    return [EntityBankAccountResponse.model_validate(a) for a in accounts]


@router.post(
    "/{entity_id}/bank-accounts",
    response_model=EntityBankAccountResponse,
    response_model_by_alias=True,
)
async def add_entity_bank_account(
    entity_id: UUID,
    data: EntityBankAccountCreate,
    current_user: User = Depends(RequirePermissions("LOS_ENTITY_UPDATE")),
    db: AsyncSession = Depends(get_db),
):
    """Add a bank account to an entity."""
    data.entity_id = entity_id
    service = EntityService(db)
    account = await service.add_bank_account(data, current_user.id)
    return EntityBankAccountResponse.model_validate(account)


@router.put(
    "/bank-accounts/{account_id}",
    response_model=EntityBankAccountResponse,
    response_model_by_alias=True,
)
async def update_entity_bank_account(
    account_id: UUID,
    data: EntityBankAccountUpdate,
    current_user: User = Depends(RequirePermissions("LOS_ENTITY_UPDATE")),
    db: AsyncSession = Depends(get_db),
):
    """Update an entity bank account."""
    service = EntityService(db)
    account = await service.update_bank_account(account_id, data, current_user.id)
    return EntityBankAccountResponse.model_validate(account)


@router.delete("/bank-accounts/{account_id}")
async def delete_entity_bank_account(
    account_id: UUID,
    current_user: User = Depends(RequirePermissions("LOS_ENTITY_DELETE")),
    db: AsyncSession = Depends(get_db),
):
    """Delete an entity bank account."""
    service = EntityService(db)
    await service.delete_bank_account(account_id, current_user.id)
    return {"message": "Bank account deleted successfully"}


# =============================================================================
# Entity Financial Endpoints
# =============================================================================


@router.get(
    "/{entity_id}/financials",
    response_model=list[EntityFinancialResponse],
    response_model_by_alias=True,
)
async def list_entity_financials(
    entity_id: UUID,
    include_inactive: bool = Query(False),
    current_user: User = Depends(RequirePermissions("LOS_ENTITY_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """Get all financial data for an entity."""
    service = EntityService(db)
    financials = await service.get_entity_financials(entity_id, include_inactive)
    return [EntityFinancialResponse.model_validate(f) for f in financials]


@router.get(
    "/{entity_id}/financials/latest",
    response_model=EntityFinancialResponse,
    response_model_by_alias=True,
)
async def get_latest_financial(
    entity_id: UUID,
    current_user: User = Depends(RequirePermissions("LOS_ENTITY_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """Get latest financial data for an entity."""
    service = EntityService(db)
    financial = await service.get_latest_financial(entity_id)
    if not financial:
        return None
    return EntityFinancialResponse.model_validate(financial)


@router.post(
    "/{entity_id}/financials", response_model=EntityFinancialResponse, response_model_by_alias=True
)
async def add_entity_financial(
    entity_id: UUID,
    data: EntityFinancialCreate,
    current_user: User = Depends(RequirePermissions("LOS_ENTITY_UPDATE")),
    db: AsyncSession = Depends(get_db),
):
    """Add financial data for an entity."""
    data.entity_id = entity_id
    service = EntityService(db)
    financial = await service.add_financial(data, current_user.id)
    return EntityFinancialResponse.model_validate(financial)


@router.put(
    "/financials/{financial_id}",
    response_model=EntityFinancialResponse,
    response_model_by_alias=True,
)
async def update_entity_financial(
    financial_id: UUID,
    data: EntityFinancialUpdate,
    current_user: User = Depends(RequirePermissions("LOS_ENTITY_UPDATE")),
    db: AsyncSession = Depends(get_db),
):
    """Update entity financial data."""
    service = EntityService(db)
    financial = await service.update_financial(financial_id, data, current_user.id)
    return EntityFinancialResponse.model_validate(financial)


@router.delete("/financials/{financial_id}")
async def delete_entity_financial(
    financial_id: UUID,
    current_user: User = Depends(RequirePermissions("LOS_ENTITY_DELETE")),
    db: AsyncSession = Depends(get_db),
):
    """Delete entity financial data."""
    service = EntityService(db)
    await service.delete_financial(financial_id, current_user.id)
    return {"message": "Financial data deleted successfully"}


# --------------------------------------------------------------------------
# Entity KYC documents
# --------------------------------------------------------------------------


@router.get(
    "/{entity_id}/kyc-documents",
    response_model=list[EntityKYCDocumentResponse],
    response_model_by_alias=True,
)
async def list_entity_kyc_documents(
    entity_id: UUID,
    include_inactive: bool = Query(False),
    current_user: User = Depends(RequirePermissions("LOS_ENTITY_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """Get all KYC documents for an entity."""
    service = KYCService(db)
    docs = await service.get_entity_kyc_documents(entity_id, include_inactive)
    return [EntityKYCDocumentResponse.model_validate(d) for d in docs]


@router.post(
    "/{entity_id}/kyc-documents",
    response_model=EntityKYCDocumentResponse,
    response_model_by_alias=True,
)
async def upload_entity_kyc_document(
    entity_id: UUID,
    file: UploadFile = File(...),
    document_type: str = Form(...),
    document_number: str | None = Form(None),
    issue_date: date | None = Form(None),
    expiry_date: date | None = Form(None),
    current_user: User = Depends(RequirePermissions("LOS_ENTITY_UPDATE")),
    db: AsyncSession = Depends(get_db),
):
    """Upload a manually collected KYC document for an entity."""
    service = KYCService(db)
    entity = await service.entity_repo.get(entity_id)
    if not entity:
        raise ValidationException("Entity not found")

    doc_type = await service.doc_type_repo.get_by_code(
        document_type,
        current_user.organization_id,
    )
    if not doc_type:
        raise ValidationException(f"KYC document type '{document_type}' is not configured")

    original_filename = file.filename or f"{document_type}.bin"
    suffix = Path(original_filename).suffix.lower()
    allowed_suffixes = {".pdf", ".jpg", ".jpeg", ".png"}
    if suffix not in allowed_suffixes:
        raise ValidationException("KYC file must be PDF, JPG, JPEG, or PNG")

    contents = await file.read()
    max_size_bytes = 10 * 1024 * 1024
    if len(contents) > max_size_bytes:
        raise ValidationException("KYC file must not exceed 10 MB")

    storage_dir = (
        Path("uploads")
        / "lending"
        / "entities"
        / str(current_user.organization_id)
        / str(entity_id)
        / "kyc"
    )
    storage_dir.mkdir(parents=True, exist_ok=True)
    stored_filename = f"{uuid4()}{suffix}"
    storage_path = storage_dir / stored_filename
    storage_path.write_bytes(contents)

    data = EntityKYCDocumentCreate(
        entity_id=entity_id,
        document_type_id=doc_type.id,
        document_number=document_number,
        document_name=doc_type.name,
        issue_date=issue_date,
        expiry_date=expiry_date,
        file_path=str(storage_path),
        file_name=original_filename,
        file_size_bytes=len(contents),
        file_mime_type=file.content_type,
    )
    document = await service.upload_kyc_document(data, current_user.id)
    return EntityKYCDocumentResponse.model_validate(document)


@router.post(
    "/{entity_id}/kyc-documents/{document_id}/verify",
    response_model=EntityKYCDocumentResponse,
    response_model_by_alias=True,
)
async def verify_entity_kyc_document(
    entity_id: UUID,
    document_id: UUID,
    data: EntityKYCVerificationRequest,
    current_user: User = Depends(RequirePermissions("LOS_ENTITY_UPDATE")),
    db: AsyncSession = Depends(get_db),
):
    """Verify or reject an entity KYC document manually."""
    service = KYCService(db)
    document = await service.entity_kyc_repo.get(document_id)
    if not document or document.entity_id != entity_id:
        raise ValidationException("KYC document not found for this entity")

    if data.status == "VERIFIED":
        updated = await service.verify_kyc_document(
            document_id,
            KYCVerificationMethod.MANUAL,
            current_user.id,
            data.remarks,
        )
    else:
        updated = await service.reject_kyc_document(
            document_id,
            data.remarks or "Rejected during manual review",
            current_user.id,
        )
    return EntityKYCDocumentResponse.model_validate(updated)


@router.delete("/{entity_id}/kyc-documents/{document_id}")
async def delete_entity_kyc_document(
    entity_id: UUID,
    document_id: UUID,
    current_user: User = Depends(RequirePermissions("LOS_ENTITY_DELETE")),
    db: AsyncSession = Depends(get_db),
):
    """Soft delete an entity KYC document."""
    service = KYCService(db)
    document = await service.entity_kyc_repo.get(document_id)
    if not document or document.entity_id != entity_id:
        raise ValidationException("KYC document not found for this entity")
    await service.delete_kyc_document(document_id, current_user.id)
    return {"message": "KYC document deleted successfully"}
