"""Service for managing voucher templates."""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.finance.voucher_template import VoucherTemplate
from app.models.finance.voucher import Voucher, VoucherLine
from app.models.finance.voucher_type import VoucherType
from app.models.finance.financial_year import FinancialYear, FinancialPeriod
from app.models.finance.account import Account
from app.core.constants import VoucherStatus
from app.schemas.finance.voucher_template import (
    VoucherTemplateCreate,
    VoucherTemplateUpdate,
    VoucherTemplateResponse,
    VoucherTemplateListItem,
    VoucherTemplateListResponse,
    VoucherTemplateLineResponse,
    UseTemplateResponse,
    TemplateCategory,
    VoucherTemplateStats,
)


class VoucherTemplateService:
    """Service for managing voucher templates."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        data: VoucherTemplateCreate,
        user_id: UUID,
    ) -> VoucherTemplate:
        """Create a new voucher template."""
        # Calculate total amount
        total_amount = sum(line.debit_amount for line in data.lines)

        # Prepare template data
        template_data = [
            {
                "account_id": str(line.account_id),
                "debit_amount": str(line.debit_amount),
                "credit_amount": str(line.credit_amount),
                "narration": line.narration,
                "cost_center_id": str(line.cost_center_id) if line.cost_center_id else None,
            }
            for line in data.lines
        ]

        template = VoucherTemplate(
            organization_id=data.organization_id,
            voucher_type_id=data.voucher_type_id,
            template_name=data.template_name,
            description=data.description,
            default_narration=data.default_narration,
            total_amount=total_amount,
            template_data=template_data,
            category=data.category,
            is_favorite=data.is_favorite,
            created_by=user_id,
        )

        self.db.add(template)
        await self.db.flush()
        await self.db.refresh(template)

        return template

    async def update(
        self,
        template_id: UUID,
        data: VoucherTemplateUpdate,
        user_id: UUID,
    ) -> VoucherTemplate:
        """Update an existing voucher template."""
        stmt = select(VoucherTemplate).where(VoucherTemplate.id == template_id)
        result = await self.db.execute(stmt)
        template = result.scalar_one_or_none()

        if not template:
            raise ValueError(f"Voucher template {template_id} not found")

        update_data = data.model_dump(exclude_unset=True)

        if "lines" in update_data and update_data["lines"]:
            lines = data.lines
            total_amount = sum(line.debit_amount for line in lines)
            template_data = [
                {
                    "account_id": str(line.account_id),
                    "debit_amount": str(line.debit_amount),
                    "credit_amount": str(line.credit_amount),
                    "narration": line.narration,
                    "cost_center_id": str(line.cost_center_id) if line.cost_center_id else None,
                }
                for line in lines
            ]
            template.total_amount = total_amount
            template.template_data = template_data
            del update_data["lines"]

        for key, value in update_data.items():
            setattr(template, key, value)

        template.modified_by = user_id

        await self.db.flush()
        await self.db.refresh(template)

        return template

    async def get(self, template_id: UUID) -> Optional[VoucherTemplate]:
        """Get a voucher template by ID."""
        stmt = select(VoucherTemplate).where(
            and_(
                VoucherTemplate.id == template_id,
                VoucherTemplate.is_deleted == False,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list(
        self,
        organization_id: UUID,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_favorite: Optional[bool] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> VoucherTemplateListResponse:
        """List voucher templates with pagination."""
        stmt = (
            select(VoucherTemplate)
            .where(VoucherTemplate.organization_id == organization_id)
            .where(VoucherTemplate.is_deleted == False)
        )

        if category:
            stmt = stmt.where(VoucherTemplate.category == category)
        if is_active is not None:
            stmt = stmt.where(VoucherTemplate.is_active == is_active)
        if is_favorite is not None:
            stmt = stmt.where(VoucherTemplate.is_favorite == is_favorite)
        if search:
            stmt = stmt.where(VoucherTemplate.template_name.ilike(f"%{search}%"))

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.db.execute(count_stmt)).scalar() or 0

        # Get paginated results
        stmt = stmt.order_by(
            VoucherTemplate.is_favorite.desc(),
            VoucherTemplate.usage_count.desc(),
            VoucherTemplate.template_name.asc(),
        )
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(stmt)
        items = result.scalars().all()

        return VoucherTemplateListResponse(
            items=[
                VoucherTemplateListItem(
                    id=str(t.id),
                    template_name=t.template_name,
                    voucher_type_name=t.voucher_type.name if t.voucher_type else "",
                    voucher_type_code=t.voucher_type.code if t.voucher_type else "",
                    total_amount=t.total_amount,
                    category=t.category,
                    is_active=t.is_active,
                    is_favorite=t.is_favorite,
                    usage_count=t.usage_count,
                    last_used_at=t.last_used_at,
                )
                for t in items
            ],
            total=total,
            page=page,
            page_size=page_size,
            pages=(total + page_size - 1) // page_size,
        )

    async def get_with_lines(self, template_id: UUID) -> Optional[VoucherTemplateResponse]:
        """Get voucher template with full line details."""
        template = await self.get(template_id)
        if not template:
            return None

        # Get account details for lines
        account_ids = [UUID(line["account_id"]) for line in template.template_data]
        stmt = select(Account).where(Account.id.in_(account_ids))
        result = await self.db.execute(stmt)
        accounts = {str(a.id): a for a in result.scalars().all()}

        lines = []
        for line_data in template.template_data:
            account = accounts.get(line_data["account_id"])
            lines.append(
                VoucherTemplateLineResponse(
                    account_id=line_data["account_id"],
                    account_code=account.code if account else "",
                    account_name=account.name if account else "",
                    debit_amount=Decimal(line_data["debit_amount"]),
                    credit_amount=Decimal(line_data["credit_amount"]),
                    narration=line_data.get("narration"),
                    cost_center_id=line_data.get("cost_center_id"),
                )
            )

        return VoucherTemplateResponse(
            id=str(template.id),
            organization_id=str(template.organization_id),
            organization_name=template.organization.name if template.organization else "",
            voucher_type_id=str(template.voucher_type_id),
            voucher_type_name=template.voucher_type.name if template.voucher_type else "",
            voucher_type_code=template.voucher_type.code if template.voucher_type else "",
            template_name=template.template_name,
            description=template.description,
            default_narration=template.default_narration,
            total_amount=template.total_amount,
            lines=lines,
            is_active=template.is_active,
            is_favorite=template.is_favorite,
            category=template.category,
            usage_count=template.usage_count,
            last_used_at=template.last_used_at,
            created_at=template.created_at,
            updated_at=template.modified_at,
        )

    async def toggle_favorite(
        self,
        template_id: UUID,
        user_id: UUID,
    ) -> VoucherTemplate:
        """Toggle favorite status of a template."""
        template = await self.get(template_id)
        if not template:
            raise ValueError(f"Voucher template {template_id} not found")

        template.is_favorite = not template.is_favorite
        template.modified_by = user_id

        await self.db.flush()
        return template

    async def use_template(
        self,
        template_id: UUID,
        user_id: UUID,
        voucher_date: date,
        narration_override: Optional[str] = None,
        amount_multiplier: Optional[Decimal] = None,
    ) -> UseTemplateResponse:
        """Create a voucher from template."""
        template = await self.get(template_id)
        if not template:
            return UseTemplateResponse(
                success=False,
                message=f"Voucher template {template_id} not found",
            )

        if not template.is_active:
            return UseTemplateResponse(
                success=False,
                message="Cannot use an inactive template",
            )

        # Get active financial year and period
        fy_stmt = select(FinancialYear).where(
            and_(
                FinancialYear.organization_id == template.organization_id,
                FinancialYear.start_date <= voucher_date,
                FinancialYear.end_date >= voucher_date,
                FinancialYear.is_closed == False,
            )
        )
        fy_result = await self.db.execute(fy_stmt)
        financial_year = fy_result.scalar_one_or_none()

        if not financial_year:
            return UseTemplateResponse(
                success=False,
                message=f"No active financial year found for date {voucher_date}",
            )

        # Get period
        period_stmt = select(FinancialPeriod).where(
            and_(
                FinancialPeriod.financial_year_id == financial_year.id,
                FinancialPeriod.start_date <= voucher_date,
                FinancialPeriod.end_date >= voucher_date,
                FinancialPeriod.is_locked == False,
            )
        )
        period_result = await self.db.execute(period_stmt)
        period = period_result.scalar_one_or_none()

        if not period:
            return UseTemplateResponse(
                success=False,
                message=f"No open period found for date {voucher_date}",
            )

        # Generate voucher number
        voucher_type = template.voucher_type
        prefix = voucher_type.prefix or "V"
        count_stmt = select(func.count()).where(
            and_(
                Voucher.voucher_type_id == template.voucher_type_id,
                Voucher.financial_year_id == financial_year.id,
            )
        )
        count = (await self.db.execute(count_stmt)).scalar() or 0
        voucher_number = f"{prefix}/{financial_year.code}/{count + 1:06d}"

        # Build narration
        narration = narration_override or template.default_narration

        # Calculate amounts with optional multiplier
        multiplier = amount_multiplier or Decimal("1.00")
        total_amount = template.total_amount * multiplier

        # Create voucher
        voucher = Voucher(
            voucher_type_id=template.voucher_type_id,
            voucher_number=voucher_number,
            voucher_date=voucher_date,
            financial_year_id=financial_year.id,
            period_id=period.id,
            narration=narration,
            total_debit=total_amount,
            total_credit=total_amount,
            status=VoucherStatus.DRAFT,
            organization_id=template.organization_id,
            created_by=user_id,
        )

        self.db.add(voucher)
        await self.db.flush()

        # Create voucher lines
        for i, line_data in enumerate(template.template_data, start=1):
            debit = Decimal(line_data["debit_amount"]) * multiplier
            credit = Decimal(line_data["credit_amount"]) * multiplier
            voucher_line = VoucherLine(
                voucher_id=voucher.id,
                line_number=i,
                account_id=UUID(line_data["account_id"]),
                debit_amount=debit,
                credit_amount=credit,
                narration=line_data.get("narration"),
                cost_center_id=UUID(line_data["cost_center_id"]) if line_data.get("cost_center_id") else None,
            )
            self.db.add(voucher_line)

        # Update template usage stats
        template.usage_count += 1
        template.last_used_at = datetime.utcnow()

        await self.db.flush()
        await self.db.refresh(voucher)

        return UseTemplateResponse(
            success=True,
            message=f"Voucher {voucher.voucher_number} created successfully",
            voucher_id=str(voucher.id),
            voucher_number=voucher.voucher_number,
        )

    async def get_categories(self, organization_id: UUID) -> List[TemplateCategory]:
        """Get all unique categories with counts."""
        stmt = (
            select(
                VoucherTemplate.category,
                func.count().label("count"),
            )
            .where(
                and_(
                    VoucherTemplate.organization_id == organization_id,
                    VoucherTemplate.is_deleted == False,
                    VoucherTemplate.category.isnot(None),
                )
            )
            .group_by(VoucherTemplate.category)
            .order_by(func.count().desc())
        )

        result = await self.db.execute(stmt)
        rows = result.all()

        return [
            TemplateCategory(category=row.category, count=row.count)
            for row in rows
        ]

    async def get_stats(self, organization_id: UUID) -> VoucherTemplateStats:
        """Get statistics for voucher templates."""
        # Total templates
        total_stmt = select(func.count()).where(
            and_(
                VoucherTemplate.organization_id == organization_id,
                VoucherTemplate.is_deleted == False,
            )
        )
        total = (await self.db.execute(total_stmt)).scalar() or 0

        # Active templates
        active_stmt = select(func.count()).where(
            and_(
                VoucherTemplate.organization_id == organization_id,
                VoucherTemplate.is_deleted == False,
                VoucherTemplate.is_active == True,
            )
        )
        active = (await self.db.execute(active_stmt)).scalar() or 0

        # Favorite templates
        favorite_stmt = select(func.count()).where(
            and_(
                VoucherTemplate.organization_id == organization_id,
                VoucherTemplate.is_deleted == False,
                VoucherTemplate.is_favorite == True,
            )
        )
        favorite = (await self.db.execute(favorite_stmt)).scalar() or 0

        # Categories
        categories = await self.get_categories(organization_id)

        # Most used
        most_used_stmt = (
            select(VoucherTemplate)
            .where(
                and_(
                    VoucherTemplate.organization_id == organization_id,
                    VoucherTemplate.is_deleted == False,
                    VoucherTemplate.usage_count > 0,
                )
            )
            .order_by(VoucherTemplate.usage_count.desc())
            .limit(5)
        )
        most_used_result = await self.db.execute(most_used_stmt)
        most_used_items = most_used_result.scalars().all()

        return VoucherTemplateStats(
            total_templates=total,
            active_templates=active,
            favorite_templates=favorite,
            categories=categories,
            most_used=[
                VoucherTemplateListItem(
                    id=str(t.id),
                    template_name=t.template_name,
                    voucher_type_name=t.voucher_type.name if t.voucher_type else "",
                    voucher_type_code=t.voucher_type.code if t.voucher_type else "",
                    total_amount=t.total_amount,
                    category=t.category,
                    is_active=t.is_active,
                    is_favorite=t.is_favorite,
                    usage_count=t.usage_count,
                    last_used_at=t.last_used_at,
                )
                for t in most_used_items
            ],
        )

    async def delete(self, template_id: UUID, user_id: UUID) -> bool:
        """Soft delete a voucher template."""
        template = await self.get(template_id)
        if not template:
            return False

        template.is_deleted = True
        template.is_active = False
        template.modified_by = user_id

        await self.db.flush()
        return True

    async def duplicate(
        self,
        template_id: UUID,
        user_id: UUID,
        new_name: Optional[str] = None,
    ) -> VoucherTemplate:
        """Duplicate an existing template."""
        original = await self.get(template_id)
        if not original:
            raise ValueError(f"Voucher template {template_id} not found")

        duplicate = VoucherTemplate(
            organization_id=original.organization_id,
            voucher_type_id=original.voucher_type_id,
            template_name=new_name or f"{original.template_name} (Copy)",
            description=original.description,
            default_narration=original.default_narration,
            total_amount=original.total_amount,
            template_data=original.template_data.copy(),
            category=original.category,
            is_favorite=False,
            created_by=user_id,
        )

        self.db.add(duplicate)
        await self.db.flush()
        await self.db.refresh(duplicate)

        return duplicate
