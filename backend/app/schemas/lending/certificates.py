"""Schemas for LoanCertificate API — camelCase wire."""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from app.models.lending.loan_certificate import CertificateType
from app.schemas.base import CamelSchema


class CertificateResponse(CamelSchema):
    id: UUID
    loan_account_id: Optional[UUID] = None
    application_id: Optional[UUID] = None
    sanction_id: Optional[UUID] = None
    certificate_type: CertificateType
    certificate_number: str
    dms_document_id: Optional[UUID] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    issued_at: datetime
    issued_by_id: Optional[UUID] = None
    issued_to_portal_user_id: Optional[UUID] = None
    period_from: Optional[date] = None
    period_to: Optional[date] = None
    financial_year: Optional[str] = None
    requires_acknowledgement: bool
    is_acknowledged: bool
    acknowledged_at: Optional[datetime] = None
    template_code: Optional[str] = None
    template_version: Optional[int] = None
    remarks: Optional[str] = None


class CertificateListResponse(CamelSchema):
    items: list[CertificateResponse]
    total: int


class IssueNdcRequest(CamelSchema):
    closure_date: date
    period_start: date


class IssueForeclosureLetterRequest(CamelSchema):
    as_of_date: date
    valid_till: date
    principal_outstanding: str
    interest_accrued: str
    foreclosure_fee: str
    other_charges: str
    payment_account_details: str
