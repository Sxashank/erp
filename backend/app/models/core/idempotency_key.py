"""Idempotency-key store for safe replay of financial mutations.

See CLAUDE.md §6.3 / §8.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class IdempotencyKey(Base):
    """Persisted idempotency-key -> response record.

    A client-supplied `Idempotency-Key` header on any mutating financial
    endpoint causes the server to store (key, user_id, request_hash,
    response_status, response_body) here for 24h. A second call with the
    same key and the same request hash returns the cached response; a call
    with the same key and a DIFFERENT hash is rejected 422.

    We keep this table lean and outside the audit/soft-delete machinery:
    it is a system-owned table, not tenant data.
    """

    __tablename__ = "idempotency_key"
    __table_args__ = (
        Index("ix_idempotency_key_user_key", "user_id", "key", unique=True),
        Index("ix_idempotency_key_expires_at", "expires_at"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    key: Mapped[str] = mapped_column(String(255), nullable=False)
    user_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    method: Mapped[str] = mapped_column(String(10), nullable=False)
    path: Mapped[str] = mapped_column(String(500), nullable=False)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    response_status: Mapped[int] = mapped_column(Integer, nullable=False)
    response_body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Use portable JSON type that renders as JSONB on Postgres and JSON on
    # SQLite (for unit-test compatibility). Behavioural semantics are the
    # same; only the physical column type differs.
    response_headers: Mapped[Optional[dict]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="When this idempotency record becomes safe to delete",
    )

    def __repr__(self) -> str:
        return f"<IdempotencyKey key={self.key} user_id={self.user_id}>"
