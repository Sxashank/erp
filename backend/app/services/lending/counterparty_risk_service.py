"""Counterparty Risk analytics service.

Aggregates exposures across active loans, treasury investments and
borrowings to produce the analytics the Counterparty Risk page renders:

* per-counterparty ranked exposures with utilisation vs single-borrower
  limit (15% of Tier-1, 20% for infrastructure entities per CLAUDE.md §4.9 /
  RBI SBR);
* sector concentration;
* internal rating distribution (sourced from ``Entity.internal_rating``);
* limit breaches (utilisation >= 80%, sorted desc).

Multi-tenant per CLAUDE.md §3.4: every query filters on
``organization_id`` (RLS also enforces this).

Money columns are ``Decimal`` per CLAUDE.md §6.2 — never floats.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lending.entity import Entity
from app.models.lending.enums import (
    BorrowingStatus,
    IndustrySector,
    LoanAccountStatus,
)
from app.models.lending.loan_account import LoanAccount
from app.models.lending.treasury import Borrowing, Lender
from app.models.lending.treasury_investment import TreasuryInvestment

# Single-borrower limit per RBI Scale-Based Regulation. CLAUDE.md §4.9.
SINGLE_BORROWER_LIMIT_PERCENT = Decimal("15")
SINGLE_BORROWER_LIMIT_PERCENT_INFRA = Decimal("20")
GROUP_LIMIT_PERCENT = Decimal("25")

# Utilisation thresholds — match the FE pill colours.
NEAR_LIMIT_THRESHOLD = Decimal("80")
BREACHED_THRESHOLD = Decimal("100")

# TODO(STAGE-4-counterparty-risk-tier1): the regulatory CRAR service exposes
# `_get_tier1_capital` as a private helper that itself returns a hardcoded
# ₹10 Cr value. Until the regulatory team wires the real capital-fund
# computation, we mirror that placeholder here so the math is at least
# consistent across the two surfaces. Approved in `.stubs-approved.md`.
_TIER1_CAPITAL_PLACEHOLDER = Decimal("100000000")  # ₹10 Cr


def _quantize_money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"))


def _quantize_percent(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.0001"))


def _classify_status(utilization_percent: Decimal) -> str:
    if utilization_percent >= BREACHED_THRESHOLD:
        return "BREACHED"
    if utilization_percent >= NEAR_LIMIT_THRESHOLD:
        return "NEAR_LIMIT"
    return "WITHIN_LIMIT"


def _breach_severity(utilization_percent: Decimal) -> str:
    """How bad is the breach? FE colour-codes by severity."""
    if utilization_percent >= Decimal("125"):
        return "CRITICAL"
    if utilization_percent >= BREACHED_THRESHOLD:
        return "BREACH"
    return "WARNING"  # 80–100 band — heading toward breach


class CounterpartyRiskService:
    """Read-only analytics; safe to call from list endpoints."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------ helpers

    async def _get_tier1_capital(self, organization_id: UUID) -> Decimal:
        """Read Tier-1 capital for the organisation.

        Right now this is a placeholder tracked at module level.
        When ``RegulatoryReportService._get_tier1_capital`` becomes a real
        computation, swap it in here.
        """
        return _TIER1_CAPITAL_PLACEHOLDER

    # ------------------------------------------------------------------ loans

    async def _loan_exposures_by_entity(self, organization_id: UUID) -> dict[UUID, Decimal]:
        """Sum of `principal_outstanding` across active loans, by entity."""
        stmt = (
            select(
                LoanAccount.entity_id,
                func.coalesce(func.sum(LoanAccount.principal_outstanding), Decimal("0")).label(
                    "exposure"
                ),
            )
            .where(
                LoanAccount.organization_id == organization_id,
                LoanAccount.status.in_(
                    [
                        LoanAccountStatus.ACTIVE,
                        LoanAccountStatus.CREATED,
                        LoanAccountStatus.DORMANT,
                        LoanAccountStatus.FROZEN,
                        LoanAccountStatus.RECALLED,
                    ]
                ),
            )
            .group_by(LoanAccount.entity_id)
        )
        result = await self.db.execute(stmt)
        return {row.entity_id: Decimal(row.exposure or 0) for row in result.all()}

    # ------------------------------------------------------------------ invest

    async def _investment_exposures_by_issuer(self, organization_id: UUID) -> dict[str, Decimal]:
        """Sum of investment exposure grouped by issuer name.

        Exposure = current_value if available, else purchase_price * units.
        Only ACTIVE investments count (matured / sold positions excluded).
        """
        stmt = select(
            TreasuryInvestment.issuer,
            TreasuryInvestment.purchase_price,
            TreasuryInvestment.units,
            TreasuryInvestment.current_value,
        ).where(
            TreasuryInvestment.organization_id == organization_id,
            TreasuryInvestment.status == "ACTIVE",
        )
        result = await self.db.execute(stmt)

        exposures: dict[str, Decimal] = {}
        for row in result.all():
            if row.current_value is not None:
                exposure = Decimal(row.current_value)
            else:
                exposure = Decimal(row.purchase_price) * Decimal(row.units)
            exposures[row.issuer] = exposures.get(row.issuer, Decimal("0")) + exposure
        return exposures

    # ------------------------------------------------------------------ borrows

    async def _borrowing_exposures_by_lender(self, organization_id: UUID) -> list[dict[str, Any]]:
        """Sum of borrowing principal outstanding grouped by lender.

        This is "lender concentration" (whose money we owe); included on the
        page separately because counterparty risk in the strict sense (the
        risk that *they* default to *us*) doesn't apply, but tenor / refi
        concentration on the funding side matters.
        """
        stmt = (
            select(
                Borrowing.lender_id,
                Lender.lender_name,
                func.coalesce(func.sum(Borrowing.principal_outstanding), Decimal("0")).label(
                    "exposure"
                ),
            )
            .join(Lender, Lender.id == Borrowing.lender_id)
            .where(
                Borrowing.organization_id == organization_id,
                # Borrowing.status is a String column; compare by enum value.
                Borrowing.status.in_(
                    [
                        BorrowingStatus.ACTIVE.value,
                        BorrowingStatus.SANCTIONED.value,
                        BorrowingStatus.FULLY_DRAWN.value,
                        BorrowingStatus.REPAYING.value,
                    ]
                ),
            )
            .group_by(Borrowing.lender_id, Lender.lender_name)
        )
        result = await self.db.execute(stmt)
        return [
            {
                "lender_id": row.lender_id,
                "lender_name": row.lender_name,
                "exposure": Decimal(row.exposure or 0),
            }
            for row in result.all()
        ]

    # ------------------------------------------------------------------ entities

    async def _entities_by_id(
        self, organization_id: UUID, entity_ids: list[UUID]
    ) -> dict[UUID, Entity]:
        if not entity_ids:
            return {}
        stmt = select(Entity).where(
            Entity.organization_id == organization_id,
            Entity.id.in_(entity_ids),
        )
        result = await self.db.execute(stmt)
        return {entity.id: entity for entity in result.scalars().all()}

    # ============================================================== public API

    async def get_counterparty_exposures(
        self, organization_id: UUID, top_n: int = 50
    ) -> dict[str, Any]:
        """Ranked list of counterparties by total exposure.

        Three counterparty buckets are merged:
        * ENTITY  — sum of active loans (borrowers).
        * ISSUER  — sum of active investment holdings (we are the lender).
        * LENDER  — sum of active borrowing principal_outstanding (we are the
          borrower) — included for lender-side concentration visibility.
        """
        tier1 = await self._get_tier1_capital(organization_id)
        single_limit = tier1 * (SINGLE_BORROWER_LIMIT_PERCENT / Decimal("100"))
        infra_limit = tier1 * (SINGLE_BORROWER_LIMIT_PERCENT_INFRA / Decimal("100"))

        loan_map = await self._loan_exposures_by_entity(organization_id)
        investment_map = await self._investment_exposures_by_issuer(organization_id)
        borrowing_rows = await self._borrowing_exposures_by_lender(organization_id)
        entities = await self._entities_by_id(organization_id, list(loan_map.keys()))

        items: list[dict[str, Any]] = []

        # --- ENTITY (borrowers) ----------------------------------------------
        for entity_id, loan_exposure in loan_map.items():
            entity = entities.get(entity_id)
            if entity is None:
                continue
            is_infra = entity.industry_sector == IndustrySector.INFRASTRUCTURE
            limit_amount = infra_limit if is_infra else single_limit
            total_exposure = loan_exposure
            utilization = (
                (total_exposure / limit_amount * Decimal("100"))
                if limit_amount > 0
                else Decimal("0")
            )
            items.append(
                {
                    "counterparty_id": str(entity.id),
                    "counterparty_name": entity.legal_name,
                    "counterparty_type": "ENTITY",
                    "loan_exposure": _quantize_money(loan_exposure),
                    "investment_exposure": Decimal("0.00"),
                    "borrowing_exposure": Decimal("0.00"),
                    "total_exposure": _quantize_money(total_exposure),
                    "tier1_capital": _quantize_money(tier1),
                    "limit_amount": _quantize_money(limit_amount),
                    "utilization_percent": _quantize_percent(utilization),
                    "status": _classify_status(utilization),
                    "rating": entity.internal_rating,
                    "sector": entity.industry_sector.value if entity.industry_sector else None,
                    "is_infrastructure": is_infra,
                }
            )

        # --- ISSUER (investments) --------------------------------------------
        for issuer, exposure in investment_map.items():
            limit_amount = single_limit  # issuers don't carry infra carve-out here
            utilization = (
                (exposure / limit_amount * Decimal("100")) if limit_amount > 0 else Decimal("0")
            )
            items.append(
                {
                    "counterparty_id": f"issuer:{issuer}",
                    "counterparty_name": issuer,
                    "counterparty_type": "ISSUER",
                    "loan_exposure": Decimal("0.00"),
                    "investment_exposure": _quantize_money(exposure),
                    "borrowing_exposure": Decimal("0.00"),
                    "total_exposure": _quantize_money(exposure),
                    "tier1_capital": _quantize_money(tier1),
                    "limit_amount": _quantize_money(limit_amount),
                    "utilization_percent": _quantize_percent(utilization),
                    "status": _classify_status(utilization),
                    "rating": None,
                    "sector": None,
                    "is_infrastructure": False,
                }
            )

        # --- LENDER (borrowings) ---------------------------------------------
        for row in borrowing_rows:
            exposure = row["exposure"]
            limit_amount = single_limit
            utilization = (
                (exposure / limit_amount * Decimal("100")) if limit_amount > 0 else Decimal("0")
            )
            items.append(
                {
                    "counterparty_id": str(row["lender_id"]),
                    "counterparty_name": row["lender_name"],
                    "counterparty_type": "LENDER",
                    "loan_exposure": Decimal("0.00"),
                    "investment_exposure": Decimal("0.00"),
                    "borrowing_exposure": _quantize_money(exposure),
                    "total_exposure": _quantize_money(exposure),
                    "tier1_capital": _quantize_money(tier1),
                    "limit_amount": _quantize_money(limit_amount),
                    "utilization_percent": _quantize_percent(utilization),
                    "status": _classify_status(utilization),
                    "rating": None,
                    "sector": None,
                    "is_infrastructure": False,
                }
            )

        items.sort(key=lambda x: x["total_exposure"], reverse=True)
        capped = items[:top_n]

        total_counterparties = len(items)
        total_exposure = sum((i["total_exposure"] for i in items), Decimal("0"))
        near_limit_count = sum(1 for i in items if i["status"] == "NEAR_LIMIT")
        breached_count = sum(1 for i in items if i["status"] == "BREACHED")

        return {
            "items": capped,
            "total_counterparties": total_counterparties,
            "total_exposure": _quantize_money(total_exposure),
            "near_limit_count": near_limit_count,
            "breached_count": breached_count,
            "tier1_capital": _quantize_money(tier1),
            "single_borrower_limit_percent": SINGLE_BORROWER_LIMIT_PERCENT,
            "infra_limit_percent": SINGLE_BORROWER_LIMIT_PERCENT_INFRA,
        }

    # ------------------------------------------------------------------ sectors

    async def get_sector_concentration(self, organization_id: UUID) -> dict[str, Any]:
        """Group loan exposure by ``entity.industry_sector``."""
        stmt = (
            select(
                Entity.industry_sector,
                func.coalesce(func.sum(LoanAccount.principal_outstanding), Decimal("0")).label(
                    "exposure"
                ),
                func.count(func.distinct(LoanAccount.id)).label("count"),
            )
            .join(Entity, Entity.id == LoanAccount.entity_id)
            .where(
                LoanAccount.organization_id == organization_id,
                LoanAccount.status.in_(
                    [
                        LoanAccountStatus.ACTIVE,
                        LoanAccountStatus.CREATED,
                        LoanAccountStatus.DORMANT,
                        LoanAccountStatus.FROZEN,
                        LoanAccountStatus.RECALLED,
                    ]
                ),
            )
            .group_by(Entity.industry_sector)
        )
        result = await self.db.execute(stmt)
        rows = result.all()
        total = sum((Decimal(r.exposure or 0) for r in rows), Decimal("0"))

        items: list[dict[str, Any]] = []
        for row in rows:
            exposure = Decimal(row.exposure or 0)
            percent = (exposure / total * Decimal("100")) if total > 0 else Decimal("0")
            items.append(
                {
                    "sector": (
                        row.industry_sector.value
                        if row.industry_sector is not None
                        else "UNCLASSIFIED"
                    ),
                    "exposure": _quantize_money(exposure),
                    "count": int(row.count or 0),
                    "percent_of_portfolio": _quantize_percent(percent),
                }
            )

        items.sort(key=lambda x: x["exposure"], reverse=True)
        return {
            "items": items,
            "total_exposure": _quantize_money(total),
        }

    # ------------------------------------------------------------------ ratings

    async def get_rating_distribution(self, organization_id: UUID) -> dict[str, Any]:
        """Group loan exposure by ``entity.internal_rating``."""
        stmt = (
            select(
                Entity.internal_rating,
                func.coalesce(func.sum(LoanAccount.principal_outstanding), Decimal("0")).label(
                    "exposure"
                ),
                func.count(func.distinct(LoanAccount.id)).label("count"),
            )
            .join(Entity, Entity.id == LoanAccount.entity_id)
            .where(
                LoanAccount.organization_id == organization_id,
                LoanAccount.status.in_(
                    [
                        LoanAccountStatus.ACTIVE,
                        LoanAccountStatus.CREATED,
                        LoanAccountStatus.DORMANT,
                        LoanAccountStatus.FROZEN,
                        LoanAccountStatus.RECALLED,
                    ]
                ),
            )
            .group_by(Entity.internal_rating)
        )
        result = await self.db.execute(stmt)
        rows = result.all()
        total = sum((Decimal(r.exposure or 0) for r in rows), Decimal("0"))

        items: list[dict[str, Any]] = []
        for row in rows:
            exposure = Decimal(row.exposure or 0)
            percent = (exposure / total * Decimal("100")) if total > 0 else Decimal("0")
            items.append(
                {
                    "rating": row.internal_rating or "UNRATED",
                    "exposure": _quantize_money(exposure),
                    "count": int(row.count or 0),
                    "percent_of_portfolio": _quantize_percent(percent),
                }
            )

        items.sort(key=lambda x: x["exposure"], reverse=True)
        return {
            "items": items,
            "total_exposure": _quantize_money(total),
        }

    # ------------------------------------------------------------------ breaches

    async def get_limit_breaches(self, organization_id: UUID) -> dict[str, Any]:
        """Counterparties at >= 80% utilisation, sorted descending."""
        exposures = await self.get_counterparty_exposures(organization_id, top_n=10_000)

        breaches: list[dict[str, Any]] = []
        for item in exposures["items"]:
            if item["utilization_percent"] >= NEAR_LIMIT_THRESHOLD:
                breaches.append(
                    {
                        "counterparty_id": item["counterparty_id"],
                        "counterparty_name": item["counterparty_name"],
                        "counterparty_type": item["counterparty_type"],
                        "total_exposure": item["total_exposure"],
                        "limit_amount": item["limit_amount"],
                        "utilization_percent": item["utilization_percent"],
                        "status": item["status"],
                        "severity": _breach_severity(item["utilization_percent"]),
                        "is_infrastructure": item["is_infrastructure"],
                    }
                )

        breaches.sort(key=lambda x: x["utilization_percent"], reverse=True)
        return {
            "items": breaches,
            "near_limit_count": sum(1 for b in breaches if b["status"] == "NEAR_LIMIT"),
            "breached_count": sum(1 for b in breaches if b["status"] == "BREACHED"),
        }
