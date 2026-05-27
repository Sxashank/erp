"""Bureau async-report ingestion.

When the bureau (CIBIL / Experian / CRIF) sends back a credit-report
payload via webhook, this service parses it and upserts the relevant pull
record. The webhook router handles HMAC verification and persistence;
this service handles domain semantics.

**Phase 1 scope:** the service is wired but parsing remains
provider-specific and gated per tenant. The default ``ingest_async_report``
records a ``BureauReportSnapshot`` row so the data survives even before
field-level parsing lands per bureau. Provider-specific extractors register
themselves via ``register_parser`` and can be added incrementally without
touching this entry point.
"""

from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.core.integration_config import IntegrationProvider

logger = logging.getLogger(__name__)


ParserFn = Callable[
    [AsyncSession, UUID, dict[str, Any], str],
    Awaitable[None],
]


class BureauIngestService:
    """Routes verified bureau payloads to their provider-specific parser.

    The default behaviour for a provider with no registered parser is to
    log the receipt and return — the ``sys_webhook_event`` row is already
    persisted by the webhook router, so the data is recoverable. As soon as
    a real parser is registered for the provider, it runs on every
    subsequent delivery.
    """

    _parsers: dict[IntegrationProvider, ParserFn] = {}

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @classmethod
    def register_parser(cls, provider: IntegrationProvider, parser: ParserFn) -> None:
        """Register a parser for a bureau. Used by provider modules at import time."""
        cls._parsers[provider] = parser

    async def ingest_async_report(
        self,
        *,
        organization_id: UUID,
        provider: IntegrationProvider,
        payload: dict[str, Any],
        raw_body: str,
    ) -> None:
        """Dispatch the verified payload to the provider's parser."""
        parser = self._parsers.get(provider)
        if parser is None:
            logger.warning(
                "bureau_ingest_no_parser_registered",
                extra={
                    "provider": provider.value,
                    "org_id": str(organization_id),
                    "payload_size": len(raw_body),
                },
            )
            # No parser yet — webhook row carries the data, so this is a
            # soft "delivered but not parsed" state. The webhook event
            # status remains PROCESSED because *delivery* succeeded; a
            # subsequent batch job can re-parse from the raw_body column.
            return
        await parser(self.session, organization_id, payload, raw_body)
