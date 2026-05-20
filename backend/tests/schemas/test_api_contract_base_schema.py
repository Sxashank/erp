"""Contract tests for frontend-facing schema serialization."""

from datetime import datetime, timezone
from uuid import uuid4

from app.schemas.base import AuditSchema, BaseSchema, PaginatedResponse


class SampleContractSchema(BaseSchema):
    organization_id: str
    created_by_user_id: str


def test_base_schema_serializes_camel_case_aliases() -> None:
    payload = SampleContractSchema(
        organization_id="org-1",
        created_by_user_id="user-1",
    ).model_dump(by_alias=True)

    assert payload == {
        "organizationId": "org-1",
        "createdByUserId": "user-1",
    }
    assert "organization_id" not in payload
    assert "created_by_user_id" not in payload


def test_audit_schema_inherits_camel_case_contract() -> None:
    payload = AuditSchema(
        created_at=datetime(2026, 5, 20, tzinfo=timezone.utc),
        updated_at=None,
        created_by=uuid4(),
        updated_by=None,
        is_active=True,
        version=1,
    ).model_dump(by_alias=True)

    assert "createdAt" in payload
    assert "createdBy" in payload
    assert "isActive" in payload
    assert "created_at" not in payload
    assert "created_by" not in payload
    assert "is_active" not in payload


def test_paginated_response_uses_camel_case_pagination_fields() -> None:
    payload = PaginatedResponse.create(
        items=[SampleContractSchema(organization_id="org-1", created_by_user_id="user-1")],
        total=25,
        page=2,
        page_size=10,
    ).model_dump(by_alias=True)

    assert payload["pageSize"] == 10
    assert payload["totalPages"] == 3
    assert payload["items"][0]["organizationId"] == "org-1"
    assert "page_size" not in payload
    assert "total_pages" not in payload
