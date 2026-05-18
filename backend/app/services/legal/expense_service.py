"""Legal Expense Management Service.

Provides business logic for managing legal expenses,
court fees, and expense recovery tracking.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.legal.court import CourtFeeSlab
from app.models.legal.enums import (
    ExpenseCategoryType,
    ExpenseStatus,
    RecoveryType,
)
from app.models.legal.expense import (
    ExpenseCategory,
    ExpenseRecovery,
    LegalExpense,
)
from app.models.lending.enums import LegalForumType


class LegalExpenseService:
    """Service for managing legal expenses."""

    # Standard TDS rates for legal services
    TDS_RATES = {
        "194J": Decimal("10.00"),  # Professional services
        "194C": Decimal("2.00"),  # Contractors
    }

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # Category Management
    # =========================================================================

    async def create_category(
        self,
        organization_id: UUID,
        category_code: str,
        category_name: str,
        category_type: ExpenseCategoryType,
        gl_account_id: UUID | None = None,
        tds_applicable: bool = False,
        tds_section: str | None = None,
        tds_rate: Decimal | None = None,
        gst_applicable: bool = False,
        gst_rate: Decimal | None = None,
        hsn_sac_code: str | None = None,
        recoverable_from_borrower: bool = True,
        recovery_priority: int = 0,
        created_by: UUID | None = None,
    ) -> ExpenseCategory:
        """Create a new expense category."""
        category = ExpenseCategory(
            organization_id=organization_id,
            category_code=category_code,
            category_name=category_name,
            category_type=category_type,
            gl_account_id=gl_account_id,
            tds_applicable=tds_applicable,
            tds_section=tds_section,
            tds_rate=tds_rate,
            gst_applicable=gst_applicable,
            gst_rate=gst_rate,
            hsn_sac_code=hsn_sac_code,
            recoverable_from_borrower=recoverable_from_borrower,
            recovery_priority=recovery_priority,
            created_by=created_by,
        )
        self.db.add(category)
        await self.db.flush()
        return category

    async def list_categories(self, organization_id: UUID) -> list[ExpenseCategory]:
        """List all expense categories."""
        result = await self.db.execute(
            select(ExpenseCategory)
            .where(
                and_(
                    ExpenseCategory.organization_id == organization_id,
                    ExpenseCategory.is_active == True,
                )
            )
            .order_by(ExpenseCategory.display_order)
        )
        return list(result.scalars().all())

    # =========================================================================
    # Expense Recording
    # =========================================================================

    async def record_expense(
        self,
        organization_id: UUID,
        legal_case_id: UUID,
        category_id: UUID,
        expense_date: date,
        description: str,
        base_amount: Decimal,
        payee_name: str,
        advocate_id: UUID | None = None,
        payee_pan: str | None = None,
        payee_gstin: str | None = None,
        invoice_number: str | None = None,
        invoice_date: date | None = None,
        invoice_document_path: str | None = None,
        gst_state: str | None = None,  # For CGST/SGST vs IGST
        is_recoverable: bool = True,
        created_by: UUID | None = None,
    ) -> LegalExpense:
        """Record a new legal expense."""
        # Get category for tax treatment
        category_result = await self.db.execute(
            select(ExpenseCategory).where(ExpenseCategory.id == category_id)
        )
        category = category_result.scalar_one_or_none()
        if not category:
            raise ValueError(f"Category {category_id} not found")

        # Calculate GST
        cgst_amount = Decimal("0")
        sgst_amount = Decimal("0")
        igst_amount = Decimal("0")
        total_gst = Decimal("0")

        if category.gst_applicable and category.gst_rate:
            total_gst = base_amount * category.gst_rate / 100
            if gst_state == "INTRA":  # Same state
                cgst_amount = total_gst / 2
                sgst_amount = total_gst / 2
            else:  # Inter-state
                igst_amount = total_gst

        # Calculate TDS
        tds_amount = Decimal("0")
        if category.tds_applicable and category.tds_rate and payee_pan:
            # TDS is on base amount, not GST
            tds_amount = base_amount * category.tds_rate / 100

        # Calculate net amounts
        gross_amount = base_amount + total_gst
        net_payable = gross_amount - tds_amount

        # Generate expense reference
        expense_reference = await self._generate_expense_reference(organization_id)

        expense = LegalExpense(
            organization_id=organization_id,
            legal_case_id=legal_case_id,
            category_id=category_id,
            advocate_id=advocate_id,
            expense_reference=expense_reference,
            expense_date=expense_date,
            description=description,
            status=ExpenseStatus.PENDING,
            base_amount=base_amount,
            gst_applicable=category.gst_applicable,
            cgst_rate=(
                category.gst_rate / 2 if category.gst_applicable and gst_state == "INTRA" else None
            ),
            cgst_amount=cgst_amount if gst_state == "INTRA" else None,
            sgst_rate=(
                category.gst_rate / 2 if category.gst_applicable and gst_state == "INTRA" else None
            ),
            sgst_amount=sgst_amount if gst_state == "INTRA" else None,
            igst_rate=(
                category.gst_rate if category.gst_applicable and gst_state != "INTRA" else None
            ),
            igst_amount=igst_amount if gst_state != "INTRA" else None,
            total_gst=total_gst,
            tds_applicable=category.tds_applicable,
            tds_section=category.tds_section,
            tds_rate=category.tds_rate,
            tds_amount=tds_amount,
            gross_amount=gross_amount,
            net_payable=net_payable,
            payee_name=payee_name,
            payee_pan=payee_pan,
            payee_gstin=payee_gstin,
            invoice_number=invoice_number,
            invoice_date=invoice_date,
            invoice_document_path=invoice_document_path,
            is_recoverable=is_recoverable and category.recoverable_from_borrower,
            created_by=created_by,
        )
        self.db.add(expense)
        await self.db.flush()
        return expense

    async def approve_expense(
        self,
        expense_id: UUID,
        approved_by_id: UUID,
        approved_by_name: str,
    ) -> LegalExpense:
        """Approve an expense."""
        result = await self.db.execute(select(LegalExpense).where(LegalExpense.id == expense_id))
        expense = result.scalar_one_or_none()
        if not expense:
            raise ValueError(f"Expense {expense_id} not found")

        if expense.status != ExpenseStatus.PENDING:
            raise ValueError(f"Expense cannot be approved in {expense.status} status")

        expense.status = ExpenseStatus.APPROVED
        expense.approved_by_id = approved_by_id
        expense.approved_by_name = approved_by_name
        expense.approval_date = datetime.utcnow()

        await self.db.flush()
        return expense

    async def reject_expense(
        self,
        expense_id: UUID,
        rejection_reason: str,
        updated_by: UUID | None = None,
    ) -> LegalExpense:
        """Reject an expense."""
        result = await self.db.execute(select(LegalExpense).where(LegalExpense.id == expense_id))
        expense = result.scalar_one_or_none()
        if not expense:
            raise ValueError(f"Expense {expense_id} not found")

        expense.status = ExpenseStatus.REJECTED
        expense.rejection_reason = rejection_reason
        expense.updated_by = updated_by

        await self.db.flush()
        return expense

    async def record_payment(
        self,
        expense_id: UUID,
        payment_date: date,
        payment_mode: str,
        payment_reference: str,
        voucher_id: UUID | None = None,
        updated_by: UUID | None = None,
    ) -> LegalExpense:
        """Record payment for an expense."""
        result = await self.db.execute(select(LegalExpense).where(LegalExpense.id == expense_id))
        expense = result.scalar_one_or_none()
        if not expense:
            raise ValueError(f"Expense {expense_id} not found")

        if expense.status != ExpenseStatus.APPROVED:
            raise ValueError("Expense must be approved before payment")

        expense.status = ExpenseStatus.PAID
        expense.payment_date = payment_date
        expense.payment_mode = payment_mode
        expense.payment_reference = payment_reference
        expense.voucher_id = voucher_id
        expense.updated_by = updated_by

        await self.db.flush()
        return expense

    # =========================================================================
    # Recovery Tracking
    # =========================================================================

    async def record_recovery(
        self,
        expense_id: UUID,
        recovery_type: RecoveryType,
        recovery_date: date,
        amount_recovered: Decimal,
        source_reference: str | None = None,
        source_transaction_id: UUID | None = None,
        auction_id: UUID | None = None,
        ots_id: UUID | None = None,
        remarks: str | None = None,
        created_by: UUID | None = None,
    ) -> ExpenseRecovery:
        """Record recovery of expense amount."""
        result = await self.db.execute(select(LegalExpense).where(LegalExpense.id == expense_id))
        expense = result.scalar_one_or_none()
        if not expense:
            raise ValueError(f"Expense {expense_id} not found")

        recovery = ExpenseRecovery(
            legal_expense_id=expense_id,
            recovery_type=recovery_type,
            recovery_date=recovery_date,
            amount_recovered=amount_recovered,
            source_reference=source_reference,
            source_transaction_id=source_transaction_id,
            auction_id=auction_id,
            ots_id=ots_id,
            remarks=remarks,
            created_by=created_by,
        )
        self.db.add(recovery)

        # Update expense recovery status
        expense.amount_recovered += amount_recovered
        if expense.amount_recovered >= expense.gross_amount:
            expense.recovery_status = "FULLY_RECOVERED"
            expense.status = ExpenseStatus.FULLY_RECOVERED
        else:
            expense.recovery_status = "PARTIALLY_RECOVERED"
            expense.status = ExpenseStatus.PARTIALLY_RECOVERED

        await self.db.flush()
        return recovery

    # =========================================================================
    # Court Fee Calculation
    # =========================================================================

    async def calculate_court_fee(
        self,
        claim_amount: Decimal,
        court_id: UUID | None = None,
        court_type: LegalForumType | None = None,
        fee_type: str = "FILING",
    ) -> Decimal:
        """Calculate court fee based on claim amount."""
        query = select(CourtFeeSlab).where(
            and_(
                CourtFeeSlab.fee_type == fee_type,
                CourtFeeSlab.is_active == True,
                CourtFeeSlab.min_claim_amount <= claim_amount,
                or_(
                    CourtFeeSlab.max_claim_amount.is_(None),
                    CourtFeeSlab.max_claim_amount >= claim_amount,
                ),
                CourtFeeSlab.effective_from <= date.today(),
                or_(
                    CourtFeeSlab.effective_to.is_(None),
                    CourtFeeSlab.effective_to >= date.today(),
                ),
            )
        )

        if court_id:
            query = query.where(CourtFeeSlab.court_id == court_id)
        elif court_type:
            query = query.where(CourtFeeSlab.court_type == court_type)

        result = await self.db.execute(query)
        slab = result.scalar_one_or_none()

        if slab:
            return slab.calculate_fee(claim_amount)

        # Default calculation if no slab found
        return self._default_court_fee(claim_amount, court_type, fee_type)

    def _default_court_fee(
        self,
        claim_amount: Decimal,
        court_type: LegalForumType | None,
        fee_type: str,
    ) -> Decimal:
        """Calculate default court fee when no slab is defined."""
        # DRT filing fee
        if court_type == LegalForumType.DRT:
            # DRT fee: 1% of claim amount, min Rs 12,000, max Rs 1,50,000
            fee = claim_amount * Decimal("0.01")
            return max(min(fee, Decimal("150000")), Decimal("12000"))

        # NCLT fee
        if court_type == LegalForumType.NCLT:
            # Flat fee for IBC applications
            return Decimal("25000")

        # Default: 1% with minimum
        fee = claim_amount * Decimal("0.01")
        return max(fee, Decimal("1000"))

    # =========================================================================
    # Queries
    # =========================================================================

    async def get_expense(self, expense_id: UUID) -> LegalExpense | None:
        """Get expense by ID with related data."""
        result = await self.db.execute(
            select(LegalExpense)
            .options(
                selectinload(LegalExpense.category),
                selectinload(LegalExpense.recoveries),
            )
            .where(LegalExpense.id == expense_id)
        )
        return result.scalar_one_or_none()

    async def list_expenses(
        self,
        organization_id: UUID,
        legal_case_id: UUID | None = None,
        category_id: UUID | None = None,
        expense_category: Any | None = None,
        status: ExpenseStatus | None = None,
        expense_status: ExpenseStatus | None = None,
        is_paid: bool | None = None,
        is_recovered: bool | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[LegalExpense], int]:
        """List expenses with filtering and pagination."""
        query = select(LegalExpense).where(
            and_(
                LegalExpense.organization_id == organization_id,
                LegalExpense.is_active == True,
            )
        )

        if legal_case_id:
            query = query.where(LegalExpense.legal_case_id == legal_case_id)
        if category_id:
            query = query.where(LegalExpense.category_id == category_id)
        effective_status = status or expense_status
        if effective_status:
            query = query.where(LegalExpense.status == effective_status)
        if is_paid is not None:
            query = query.where(
                LegalExpense.payment_date.is_not(None)
                if is_paid
                else LegalExpense.payment_date.is_(None)
            )
        if is_recovered is not None:
            query = query.where(
                LegalExpense.amount_recovered > 0
                if is_recovered
                else LegalExpense.amount_recovered <= 0
            )
        if from_date:
            query = query.where(LegalExpense.expense_date >= from_date)
        if to_date:
            query = query.where(LegalExpense.expense_date <= to_date)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Apply pagination and ordering
        query = query.order_by(LegalExpense.expense_date.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def get_case_expense_summary(self, legal_case_id: UUID) -> dict[str, Any]:
        """Get expense summary for a case."""
        result = await self.db.execute(
            select(LegalExpense).where(
                and_(
                    LegalExpense.legal_case_id == legal_case_id,
                    LegalExpense.is_active == True,
                )
            )
        )
        expenses = list(result.scalars().all())

        summary = {
            "total_expenses": len(expenses),
            "total_amount": Decimal("0"),
            "total_gst": Decimal("0"),
            "total_tds": Decimal("0"),
            "total_paid": Decimal("0"),
            "total_recovered": Decimal("0"),
            "pending_recovery": Decimal("0"),
            "by_category": {},
            "by_status": {},
        }

        for expense in expenses:
            summary["total_amount"] += expense.gross_amount
            summary["total_gst"] += expense.total_gst
            summary["total_tds"] += expense.tds_amount

            if expense.status == ExpenseStatus.PAID:
                summary["total_paid"] += expense.gross_amount

            summary["total_recovered"] += expense.amount_recovered

            # By status
            status_key = expense.status.value if expense.status else "UNKNOWN"
            if status_key not in summary["by_status"]:
                summary["by_status"][status_key] = {"count": 0, "amount": Decimal("0")}
            summary["by_status"][status_key]["count"] += 1
            summary["by_status"][status_key]["amount"] += expense.gross_amount

        summary["pending_recovery"] = summary["total_amount"] - summary["total_recovered"]

        return summary

    # =========================================================================
    # Helper Methods
    # =========================================================================

    async def _generate_expense_reference(self, organization_id: UUID) -> str:
        """Generate unique expense reference."""
        today = date.today()
        prefix = f"EXP/{today.strftime('%Y%m')}"

        count_query = select(func.count()).where(
            and_(
                LegalExpense.organization_id == organization_id,
                LegalExpense.expense_reference.like(f"{prefix}%"),
            )
        )
        count = (await self.db.execute(count_query)).scalar() or 0

        return f"{prefix}/{count + 1:04d}"


# Helper for SQL OR condition
def or_(*conditions):
    from sqlalchemy import or_ as sql_or

    return sql_or(*conditions)
