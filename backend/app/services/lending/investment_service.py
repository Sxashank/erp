"""Treasury investment portfolio service.

Owns the transaction boundary for investment lifecycle operations
(CLAUDE.md §3.2). Money is ``Decimal``; never ``float`` (CLAUDE.md §6.2).
"""

from __future__ import annotations

from collections import OrderedDict, defaultdict
from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, NotFoundException
from app.models.auth.user import User
from app.models.lending.treasury_investment import TreasuryInvestment
from app.repositories.lending.investment_repo import InvestmentRepository
from app.schemas.lending.investment import (
    CategoryBreakdown,
    InvestmentCreateRequest,
    InvestmentMatureRequest,
    InvestmentMaturityResponse,
    MaturityBucket,
    MaturityBucketItem,
    PortfolioSummaryResponse,
)


def _add_months(d: date, months: int) -> date:
    """Naive month-end-safe date offset. Used only for bucket boundaries."""
    year = d.year + (d.month - 1 + months) // 12
    month = (d.month - 1 + months) % 12 + 1
    # Clamp day to month-end if needed (28 covers all months).
    day = min(d.day, 28)
    return date(year, month, day)


class InvestmentService:
    """Service for treasury investment portfolio operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = InvestmentRepository(session)

    # =========================================================================
    # Create
    # =========================================================================

    async def create_investment(
        self,
        data: InvestmentCreateRequest,
        current_user: User,
    ) -> TreasuryInvestment:
        """Create a new investment record for the current user's org.

        Generates a deterministic per-tenant investment number
        ``INV/<YYYY>/<NNNNN>``, computes the initial book value as
        ``purchase_price * units`` and stamps the audit fields.

        The caller (route) owns the outer transaction (``db.begin()``);
        this method only flushes so the row + generated columns are
        visible inside the same transaction.
        """
        if current_user.organization_id is None:
            raise BadRequestException(
                "Current user has no organization context",
                error_code="MISSING_ORG_CONTEXT",
            )
        org_id: UUID = current_user.organization_id

        # Maturity-date guard: when present must be on or after purchase.
        if data.maturity_date is not None and data.maturity_date < data.purchase_date:
            raise BadRequestException(
                "Maturity date cannot precede purchase date",
                error_code="INVALID_MATURITY_DATE",
            )

        # Generate business number scoped to (org, year).
        year = date.today().year
        existing = await self.repo.count_by_year(org_id, year)
        investment_number = f"INV/{year}/{existing + 1:05d}"

        # Defence in depth — extremely unlikely collision but worth checking.
        if await self.repo.get_by_number(org_id, investment_number):
            investment_number = f"INV/{year}/{existing + 2:05d}"

        # Initial book value used as the first MTM snapshot. Decimal stays
        # Decimal — never float.
        initial_value: Decimal = data.purchase_price * data.units

        investment = TreasuryInvestment(
            organization_id=org_id,
            investment_number=investment_number,
            type=data.type,
            category=data.category,
            issuer=data.issuer,
            description=data.description,
            isin=data.isin,
            face_value=data.face_value,
            purchase_price=data.purchase_price,
            units=data.units,
            coupon_rate=data.coupon_rate,
            ytm=data.ytm,
            coupon_frequency=data.coupon_frequency,
            purchase_date=data.purchase_date,
            maturity_date=data.maturity_date,
            broker=data.broker,
            remarks=data.remarks,
            status="ACTIVE",
            current_value=initial_value,
            accrued_interest=Decimal("0"),
            created_by=current_user.id,
        )
        self.session.add(investment)
        await self.session.flush()
        await self.session.refresh(investment)
        return investment

    # =========================================================================
    # Read
    # =========================================================================

    async def list_investments(
        self,
        organization_id: UUID,
        status: str | None = None,
        category: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[TreasuryInvestment], int]:
        """Paginated list. Caps limit at 200 per CLAUDE.md §6.5 (route enforces)."""
        return await self.repo.list_by_org(
            organization_id=organization_id,
            status=status,
            category=category,
            skip=skip,
            limit=limit,
        )

    async def get_investment(
        self, organization_id: UUID, investment_id: UUID
    ) -> TreasuryInvestment:
        """Get a single investment, enforcing tenant scope at the service tier.

        RLS also enforces org isolation at the DB layer (CLAUDE.md §3.4); this
        check turns a silent zero-row result into an explicit 404.
        """
        inv = await self.repo.get(investment_id)
        if not inv or inv.organization_id != organization_id:
            raise NotFoundException("Investment not found", error_code="INVESTMENT_NOT_FOUND")
        return inv

    # =========================================================================
    # Portfolio summary
    # =========================================================================

    async def get_portfolio_summary(self, organization_id: UUID) -> PortfolioSummaryResponse:
        """Aggregate metrics across all active investments for the org."""
        rows = await self.repo.list_all_active(organization_id)

        total_face = Decimal("0")
        total_purchase = Decimal("0")
        total_current = Decimal("0")
        active_count = 0
        weighted_ytm_numer = Decimal("0")  # ytm * purchase_value
        weighted_ytm_denom = Decimal("0")  # purchase_value

        by_category: dict[str, dict[str, Decimal | int]] = defaultdict(
            lambda: {
                "count": 0,
                "face_value": Decimal("0"),
                "purchase_value": Decimal("0"),
                "current_value": Decimal("0"),
            }
        )
        by_type: dict[str, dict[str, Decimal | int]] = defaultdict(
            lambda: {
                "count": 0,
                "face_value": Decimal("0"),
                "purchase_value": Decimal("0"),
                "current_value": Decimal("0"),
            }
        )

        for inv in rows:
            face = inv.face_value * inv.units
            purchase = inv.purchase_price * inv.units
            current = inv.current_value if inv.current_value is not None else purchase
            total_face += face
            total_purchase += purchase
            total_current += current

            if inv.status == "ACTIVE":
                active_count += 1

            if purchase > 0:
                weighted_ytm_numer += inv.ytm * purchase
                weighted_ytm_denom += purchase

            for bucket, key in ((by_category, inv.category), (by_type, inv.type)):
                bucket[key]["count"] = int(bucket[key]["count"]) + 1
                bucket[key]["face_value"] = Decimal(bucket[key]["face_value"]) + face
                bucket[key]["purchase_value"] = Decimal(bucket[key]["purchase_value"]) + purchase
                bucket[key]["current_value"] = Decimal(bucket[key]["current_value"]) + current

        weighted_ytm: Decimal | None = None
        if weighted_ytm_denom > 0:
            weighted_ytm = (weighted_ytm_numer / weighted_ytm_denom).quantize(Decimal("0.0001"))

        return PortfolioSummaryResponse(
            total_count=len(rows),
            active_count=active_count,
            total_face_value=total_face,
            total_purchase_value=total_purchase,
            total_current_value=total_current,
            unrealized_gain_loss=total_current - total_purchase,
            weighted_avg_ytm=weighted_ytm,
            by_category=[
                CategoryBreakdown(
                    key=k,
                    count=int(v["count"]),
                    face_value=Decimal(v["face_value"]),
                    purchase_value=Decimal(v["purchase_value"]),
                    current_value=Decimal(v["current_value"]),
                )
                for k, v in by_category.items()
            ],
            by_type=[
                CategoryBreakdown(
                    key=k,
                    count=int(v["count"]),
                    face_value=Decimal(v["face_value"]),
                    purchase_value=Decimal(v["purchase_value"]),
                    current_value=Decimal(v["current_value"]),
                )
                for k, v in by_type.items()
            ],
        )

    # =========================================================================
    # Maturity schedule
    # =========================================================================

    async def get_maturity_schedule(
        self, organization_id: UUID, months_ahead: int = 12
    ) -> InvestmentMaturityResponse:
        """Investments maturing in the next ``months_ahead`` months.

        Groups results into month-wide buckets (e.g. ``Jan 2026``,
        ``Feb 2026`` …) so the maturity-ladder UI can render directly.

        Caller bounds ``months_ahead`` (route uses 1..120).
        """
        today = date.today()
        end = _add_months(today, months_ahead)
        thirty_days_end = today + timedelta(days=30)
        ninety_days_end = today + timedelta(days=90)

        rows = await self.repo.list_maturing(organization_id, today, end)

        # Month-keyed ordered dict so buckets come out chronologically.
        buckets: OrderedDict[tuple[int, int], list[TreasuryInvestment]] = OrderedDict()
        # Pre-seed each month in the window so empty months still render.
        cursor = date(today.year, today.month, 1)
        while cursor <= end:
            buckets[(cursor.year, cursor.month)] = []
            cursor = _add_months(cursor, 1)
            cursor = date(cursor.year, cursor.month, 1)

        total_30d = Decimal("0")
        total_90d = Decimal("0")
        total_period = Decimal("0")
        upcoming_30d: list[MaturityBucketItem] = []

        for inv in rows:
            assert inv.maturity_date is not None  # filtered in repo
            key = (inv.maturity_date.year, inv.maturity_date.month)
            buckets.setdefault(key, []).append(inv)
            face = inv.face_value * inv.units
            total_period += face
            if inv.maturity_date <= thirty_days_end:
                total_30d += face
                upcoming_30d.append(MaturityBucketItem.model_validate(inv))
            if inv.maturity_date <= ninety_days_end:
                total_90d += face

        bucket_models: list[MaturityBucket] = []
        month_names = [
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec",
        ]
        for (year, month), invs in buckets.items():
            period_start = date(year, month, 1)
            # Period end = day before next month start; safe across years.
            nxt = _add_months(period_start, 1)
            period_end = date(nxt.year, nxt.month, 1) - timedelta(days=1)
            face_sum = sum((i.face_value * i.units for i in invs), start=Decimal("0"))
            bucket_models.append(
                MaturityBucket(
                    label=f"{month_names[month - 1]} {year}",
                    period_start=period_start,
                    period_end=period_end,
                    total_face_value=face_sum,
                    investment_count=len(invs),
                    investments=[MaturityBucketItem.model_validate(inv) for inv in invs],
                )
            )

        return InvestmentMaturityResponse(
            months_ahead=months_ahead,
            as_of_date=today,
            upcoming_30d=upcoming_30d,
            total_maturing_30d=total_30d,
            total_maturing_90d=total_90d,
            total_maturing_period=total_period,
            buckets=bucket_models,
        )

    # =========================================================================
    # Mark matured
    # =========================================================================

    async def mark_matured(
        self,
        organization_id: UUID,
        investment_id: UUID,
        data: InvestmentMatureRequest,
        current_user: User,
    ) -> TreasuryInvestment:
        """Mark an investment as MATURED (or SOLD when ``sale_value`` is given).

        Computes ``realized_gain_loss = proceeds - purchase_value`` where
        ``proceeds`` is the explicit sale value when provided, otherwise
        ``face_value * units`` (assumes redemption at par).

        TODO(STAGE-X): post the GL entries — book the receipt to the bank
        account and recognise gain/loss against the investment income /
        loss accounts. Tracked in `.stubs-approved.md` once the GL service
        contract is wired up for treasury.
        """
        inv = await self.get_investment(organization_id, investment_id)

        if inv.status != "ACTIVE":
            raise BadRequestException(
                f"Investment is already {inv.status.lower()}; cannot mature again",
                error_code="INVESTMENT_NOT_ACTIVE",
            )

        purchase_value = inv.purchase_price * inv.units
        if data.sale_value is not None:
            proceeds = data.sale_value
            new_status = "SOLD"
        else:
            proceeds = inv.face_value * inv.units
            new_status = "MATURED"

        inv.sale_value = proceeds
        inv.sale_date = data.sale_date or date.today()
        inv.realized_gain_loss = proceeds - purchase_value
        inv.current_value = proceeds
        inv.status = new_status
        if data.remarks:
            inv.remarks = f"{inv.remarks}\n{data.remarks}" if inv.remarks else data.remarks
        inv.updated_by = current_user.id

        await self.session.flush()
        await self.session.refresh(inv)
        return inv
