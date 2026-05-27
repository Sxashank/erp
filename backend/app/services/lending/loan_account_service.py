"""Services for Phase 2 Loan Accounting."""

from datetime import UTC, date, datetime, time, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lending.enums import (
    AccrualCategory,
    AccrualStatus,
    AdjustmentType,
    AllocationComponent,
    ApplicationStage,
    ApplicationStatus,
    AssetClassification,
    DisbursementStatus,
    InstallmentStatus,
    LoanAccountStatus,
    MandateStatus,
    ReceiptType,
    ProvisioningCategory,
    ReceiptStatus,
    ScheduleType,
    SanctionStatus,
)
from app.models.lending.application import LoanApplication
from app.models.lending.entity import Entity
from app.models.lending.loan_account import (
    AssetClassificationHistory,
    Disbursement,
    LoanAccount,
    LoanAccrual,
    LoanAdjustment,
    LoanMandate,
    LoanProvision,
    LoanReceipt,
    RepaymentSchedule,
    ScheduleInstallment,
)
from app.models.lending.product import LoanProduct
from app.models.lending.sanction import LoanSanction
from app.repositories.lending.application_repo import LoanApplicationRepository
from app.repositories.lending.entity_repo import EntityRepository
from app.repositories.lending.loan_account_repo import (
    AssetClassificationHistoryRepository,
    DisbursementRepository,
    LoanAccountRepository,
    LoanAccrualRepository,
    LoanAdjustmentRepository,
    LoanMandateRepository,
    LoanProvisionRepository,
    LoanReceiptRepository,
    ReceiptAllocationRepository,
    RepaymentScheduleRepository,
    ScheduleInstallmentRepository,
)
from app.repositories.lending.product_repo import LoanProductRepository
from app.repositories.lending.sanction_repo import LoanSanctionRepository
from app.schemas.lending.loan_account import (
    DisbursementApproval,
    DisbursementCreate,
    DisbursementProcess,
    HistoricalLoanOnboardingCreate,
    HistoricalLoanOnboardingResult,
    LoanAccountCreate,
    LoanAccountUpdate,
    LoanAdjustmentCreate,
    LoanMandateCreate,
    LoanReceiptCreate,
    MandateCancelRequest,
    MandateRegisterRequest,
    ReceiptBounceRequest,
    RepaymentScheduleCreate,
)


class LoanAccountService:
    """Service for loan account operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.loan_account_repo = LoanAccountRepository(db)
        self.disbursement_repo = DisbursementRepository(db)
        self.schedule_repo = RepaymentScheduleRepository(db)
        self.installment_repo = ScheduleInstallmentRepository(db)
        self.accrual_repo = LoanAccrualRepository(db)
        self.receipt_repo = LoanReceiptRepository(db)
        self.allocation_repo = ReceiptAllocationRepository(db)
        self.mandate_repo = LoanMandateRepository(db)
        self.classification_repo = AssetClassificationHistoryRepository(db)
        self.provision_repo = LoanProvisionRepository(db)
        self.adjustment_repo = LoanAdjustmentRepository(db)
        self.sanction_repo = LoanSanctionRepository(db)
        self.application_repo = LoanApplicationRepository(db)
        self.entity_repo = EntityRepository(db)
        self.product_repo = LoanProductRepository(db)

    # =========================================================================
    # Loan Account Operations
    # =========================================================================

    @staticmethod
    def _add_months(base_date: date, months: int) -> date:
        """Add calendar months without introducing an external dependency."""
        month_index = base_date.month - 1 + months
        year = base_date.year + month_index // 12
        month = month_index % 12 + 1
        month_lengths = [
            31,
            29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,
            31,
            30,
            31,
            30,
            31,
            31,
            30,
            31,
            30,
            31,
        ]
        day = min(base_date.day, month_lengths[month - 1])
        return date(year, month, day)

    async def create_loan_account(
        self,
        data: LoanAccountCreate,
        user_id: UUID,
    ) -> LoanAccount:
        """Create a new loan account from sanction."""
        # Validate sanction exists and is accepted
        sanction = await self.sanction_repo.get(data.sanction_id)
        if not sanction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sanction not found",
            )
        if sanction.status not in [SanctionStatus.ACCEPTED, SanctionStatus.ACTIVE]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sanction must be accepted before creating loan account",
            )

        # Check if loan account already exists for this sanction
        existing = await self.loan_account_repo.get_by_sanction(data.sanction_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Loan account already exists for this sanction",
            )

        account_open_date = data.account_open_date or date.today()
        moratorium_months = sanction.moratorium_months or 0
        maturity_date = self._add_months(account_open_date, sanction.tenure_months)
        moratorium_end_date = (
            self._add_months(account_open_date, moratorium_months)
            if moratorium_months > 0
            else None
        )

        # Generate account number
        account_number = await self.loan_account_repo.generate_account_number(
            sanction.organization_id
        )

        # Create loan account
        loan_account_data = {
            "organization_id": sanction.organization_id,
            "sanction_id": sanction.id,
            "entity_id": sanction.entity_id,
            "product_id": sanction.product_id,
            "loan_account_number": account_number,
            "loan_reference_number": data.loan_reference_number,
            "account_open_date": account_open_date,
            "repayment_start_date": sanction.repayment_start_date,
            "maturity_date": maturity_date,
            "sanctioned_amount": sanction.sanctioned_amount,
            "tenure_months": sanction.tenure_months,
            "moratorium_months": moratorium_months,
            "moratorium_end_date": moratorium_end_date,
            "interest_type": sanction.interest_type,
            "base_rate_id": sanction.base_rate_id,
            "current_base_rate": sanction.base_rate_at_sanction,
            "spread_bps": sanction.spread_bps,
            "current_interest_rate": sanction.effective_rate,
            "rate_reset_frequency": sanction.rate_reset_frequency,
            "penal_interest_rate": sanction.penal_interest_rate,
            "repayment_frequency": sanction.repayment_frequency,
            "repayment_mode": sanction.repayment_mode,
            "day_count_convention": data.day_count_convention or sanction.day_count_convention,
            "installment_day": data.installment_day,
            "prepayment_penalty_rate": sanction.prepayment_penalty_rate,
            "foreclosure_penalty_rate": sanction.foreclosure_penalty_rate,
            "allocation_priority": data.allocation_priority,
            "allocation_order": data.allocation_order,
            "undisbursed_amount": sanction.sanctioned_amount,
            "status": LoanAccountStatus.CREATED,
            "remarks": data.remarks,
            "created_by": user_id,
        }

        loan_account = await self.loan_account_repo.create(loan_account_data)
        await self.db.flush()
        await self.db.refresh(loan_account)

        return loan_account

    def _derive_installment_status(
        self,
        *,
        due_date: date,
        cutover_date: date,
        principal_amount: Decimal,
        interest_amount: Decimal,
        penal_interest_due: Decimal,
        principal_paid: Decimal,
        interest_paid: Decimal,
        penal_interest_paid: Decimal,
        explicit_status: InstallmentStatus | None,
    ) -> InstallmentStatus:
        """Classify one imported instalment without relying on today's date."""
        if explicit_status is not None:
            return explicit_status

        total_due = principal_amount + interest_amount + penal_interest_due
        total_paid = principal_paid + interest_paid + penal_interest_paid
        if total_due <= 0:
            return InstallmentStatus.PAID
        if total_paid >= total_due:
            return InstallmentStatus.PAID
        if total_paid > 0:
            return InstallmentStatus.PARTIALLY_PAID
        if due_date < cutover_date:
            return InstallmentStatus.OVERDUE
        if due_date == cutover_date:
            return InstallmentStatus.DUE
        return InstallmentStatus.NOT_DUE

    def _derive_asset_classification(self, dpd: int) -> AssetClassification:
        if dpd <= 0:
            return AssetClassification.STANDARD
        if dpd <= 30:
            return AssetClassification.SMA_0
        if dpd <= 60:
            return AssetClassification.SMA_1
        if dpd <= 90:
            return AssetClassification.SMA_2
        return AssetClassification.NPA

    async def _resolve_historical_entity(
        self,
        data: HistoricalLoanOnboardingCreate,
        organization_id: UUID,
    ) -> Entity:
        if data.entity_id is not None:
            entity = await self.entity_repo.get(data.entity_id)
            if entity and entity.organization_id == organization_id:
                return entity
        elif data.entity_code:
            entity = await self.entity_repo.get_by_code(data.entity_code, organization_id)
            if entity:
                return entity
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Historical onboarding entity was not found in this tenant",
        )

    async def _resolve_historical_product(
        self,
        data: HistoricalLoanOnboardingCreate,
        organization_id: UUID,
    ) -> LoanProduct:
        if data.product_id is not None:
            product = await self.product_repo.get_for_organization(data.product_id, organization_id)
            if product:
                return product
        elif data.product_code:
            product = await self.product_repo.get_by_code(data.product_code, organization_id)
            if product:
                return product
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Historical onboarding product was not found in this tenant",
        )

    async def validate_historical_onboarding(
        self,
        data: HistoricalLoanOnboardingCreate,
        organization_id: UUID,
    ) -> HistoricalLoanOnboardingResult:
        """Validate a legacy loan import without creating records."""
        warnings: list[str] = []
        entity = await self._resolve_historical_entity(data, organization_id)
        product = await self._resolve_historical_product(data, organization_id)

        account_number = data.loan_account_number
        if account_number:
            existing = await self.loan_account_repo.get_by_account_number(account_number)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Loan account number already exists: {account_number}",
                )

        if data.post_historical_accounting:
            warnings.append(
                "postHistoricalAccounting is not enabled in this manual-first release; "
                "legacy EMI rows are imported as operational history and accounting starts "
                "from the cutover balances."
            )

        if not data.installments:
            warnings.append(
                "No installment rows were supplied; the loan will retain balances but will not "
                "show historical EMI history until schedule rows are imported."
            )

        return HistoricalLoanOnboardingResult(
            loan_account_number=account_number,
            imported_installments=len(data.installments),
            dry_run=True,
            warnings=[
                f"Resolved entity {entity.entity_code}",
                f"Resolved product {product.code}",
                *warnings,
            ],
        )

    async def onboard_historical_loan(
        self,
        data: HistoricalLoanOnboardingCreate,
        organization_id: UUID,
        user_id: UUID,
        *,
        dry_run: bool = False,
    ) -> HistoricalLoanOnboardingResult:
        """Create a legacy loan account with historical schedule and EMI receipts.

        This path is for onboarding pre-existing corporate/project loans from a
        client Excel register. It deliberately avoids re-running historical
        accounting. Historical receipts are stored as LMS operational history;
        finance carries the cutover outstanding through opening balances.
        """
        validation = await self.validate_historical_onboarding(data, organization_id)
        if dry_run:
            return validation

        entity = await self._resolve_historical_entity(data, organization_id)
        product = await self._resolve_historical_product(data, organization_id)

        application_number = await self.application_repo.generate_application_number(
            organization_id, product.code
        )
        sanction_number = await self.sanction_repo.generate_sanction_number(
            organization_id, product.code
        )
        loan_account_number = (
            data.loan_account_number
            or await self.loan_account_repo.generate_account_number(organization_id)
        )
        existing = await self.loan_account_repo.get_by_account_number(loan_account_number)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Loan account number already exists: {loan_account_number}",
            )

        application = await self.application_repo.create(
            {
                "organization_id": organization_id,
                "application_number": application_number,
                "entity_id": entity.id,
                "product_id": product.id,
                "requested_amount": data.sanctioned_amount,
                "requested_tenure_months": data.tenure_months,
                "purpose": data.purpose,
                "detailed_purpose": data.remarks,
                "is_project_finance": bool(data.project_name),
                "project_name": data.project_name,
                "project_cost": data.sanctioned_amount,
                "preferred_interest_type": data.interest_type,
                "preferred_repayment_frequency": data.repayment_frequency,
                "preferred_repayment_mode": data.repayment_mode,
                "requested_moratorium_months": data.moratorium_months,
                "stage": ApplicationStage.DISBURSED,
                "status": ApplicationStatus.SANCTIONED,
                "application_date": data.application_date,
                "submission_date": data.application_date,
                "decision_date": data.sanction_date,
                "source_channel": "MIGRATION",
                "source_reference": data.legacy_loan_number,
                "remarks": data.remarks,
                "extra_data": {
                    "legacyOnboarding": True,
                    "legacyLoanNumber": data.legacy_loan_number,
                    "cutoverDate": data.cutover_date.isoformat(),
                },
                "created_by": user_id,
            }
        )

        validity_date = max(
            data.account_open_date,
            data.sanction_date + timedelta(days=90),
        )
        sanction = await self.sanction_repo.create(
            {
                "organization_id": organization_id,
                "application_id": application.id,
                "entity_id": entity.id,
                "product_id": product.id,
                "sanction_number": sanction_number,
                "sanction_letter_number": data.legacy_loan_number,
                "sanction_date": data.sanction_date,
                "validity_date": validity_date,
                "sanctioned_amount": data.sanctioned_amount,
                "requested_amount": data.sanctioned_amount,
                "approved_project_cost": data.sanctioned_amount,
                "tenure_months": data.tenure_months,
                "moratorium_months": data.moratorium_months,
                "interest_type": data.interest_type,
                "effective_rate": data.current_interest_rate,
                "penal_interest_rate": data.penal_interest_rate,
                "repayment_frequency": data.repayment_frequency,
                "repayment_mode": data.repayment_mode,
                "repayment_start_date": data.repayment_start_date,
                "day_count_convention": data.day_count_convention,
                "disbursement_type": "LEGACY",
                "max_tranches": 1,
                "status": SanctionStatus.ACCEPTED,
                "acceptance_required": False,
                "accepted_at": datetime.combine(data.sanction_date, time.min, tzinfo=UTC),
                "special_terms": "Imported from pre-go-live loan register.",
                "remarks": data.remarks,
                "created_by": user_id,
            }
        )

        sorted_installments = sorted(data.installments, key=lambda row: row.installment_number)
        oldest_unpaid_due_date: date | None = None
        calculated_principal_overdue = Decimal("0")
        calculated_interest_overdue = Decimal("0")
        total_principal_received = Decimal("0")
        total_interest_received = Decimal("0")
        total_penal_received = Decimal("0")
        imported_receipts = 0

        for row in sorted_installments:
            status_value = self._derive_installment_status(
                due_date=row.due_date,
                cutover_date=data.cutover_date,
                principal_amount=row.principal_amount,
                interest_amount=row.interest_amount,
                penal_interest_due=row.penal_interest_due,
                principal_paid=row.principal_paid,
                interest_paid=row.interest_paid,
                penal_interest_paid=row.penal_interest_paid,
                explicit_status=row.status,
            )
            unpaid_principal = row.principal_amount - row.principal_paid
            unpaid_interest = row.interest_amount - row.interest_paid
            if (
                status_value
                in {
                    InstallmentStatus.DUE,
                    InstallmentStatus.PARTIALLY_PAID,
                    InstallmentStatus.OVERDUE,
                }
                and row.due_date <= data.cutover_date
            ):
                calculated_principal_overdue += max(unpaid_principal, Decimal("0"))
                calculated_interest_overdue += max(unpaid_interest, Decimal("0"))
                if oldest_unpaid_due_date is None or row.due_date < oldest_unpaid_due_date:
                    oldest_unpaid_due_date = row.due_date

            total_principal_received += row.principal_paid
            total_interest_received += row.interest_paid
            total_penal_received += row.penal_interest_paid
            if data.create_historical_receipts:
                paid_total = row.principal_paid + row.interest_paid + row.penal_interest_paid
                if paid_total > 0:
                    imported_receipts += 1

        days_past_due = (
            data.days_past_due
            if data.days_past_due is not None
            else (
                max((data.cutover_date - oldest_unpaid_due_date).days, 0)
                if oldest_unpaid_due_date
                else 0
            )
        )
        asset_classification = data.asset_classification or self._derive_asset_classification(
            days_past_due
        )
        principal_overdue = (
            data.principal_overdue
            if data.principal_overdue is not None
            else calculated_principal_overdue
        )
        interest_overdue = (
            data.interest_overdue
            if data.interest_overdue is not None
            else calculated_interest_overdue
        )
        total_outstanding = data.total_outstanding or (
            data.principal_outstanding
            + data.interest_outstanding
            + interest_overdue
            + data.penal_interest_outstanding
            + data.charges_outstanding
        )
        status_value = (
            LoanAccountStatus.CLOSED if total_outstanding <= 0 else LoanAccountStatus.ACTIVE
        )
        current_emi_amount = data.current_emi_amount
        if current_emi_amount is None and sorted_installments:
            next_open = next(
                (
                    row.emi_amount
                    for row in sorted_installments
                    if row.due_date >= data.cutover_date
                ),
                sorted_installments[-1].emi_amount,
            )
            current_emi_amount = next_open

        loan_account = await self.loan_account_repo.create(
            {
                "organization_id": organization_id,
                "sanction_id": sanction.id,
                "entity_id": entity.id,
                "product_id": product.id,
                "loan_account_number": loan_account_number,
                "loan_reference_number": data.loan_reference_number or data.legacy_loan_number,
                "account_open_date": data.account_open_date,
                "first_disbursement_date": data.first_disbursement_date,
                "last_disbursement_date": data.last_disbursement_date
                or data.first_disbursement_date,
                "repayment_start_date": data.repayment_start_date
                or (sorted_installments[0].due_date if sorted_installments else None),
                "maturity_date": data.maturity_date
                or (sorted_installments[-1].due_date if sorted_installments else None),
                "sanctioned_amount": data.sanctioned_amount,
                "tenure_months": data.tenure_months,
                "moratorium_months": data.moratorium_months,
                "interest_type": data.interest_type,
                "current_interest_rate": data.current_interest_rate,
                "penal_interest_rate": data.penal_interest_rate,
                "repayment_frequency": data.repayment_frequency,
                "repayment_mode": data.repayment_mode,
                "day_count_convention": data.day_count_convention,
                "current_emi_amount": current_emi_amount,
                "total_disbursed_amount": data.total_disbursed_amount,
                "undisbursed_amount": max(
                    data.sanctioned_amount - data.total_disbursed_amount, Decimal("0")
                ),
                "principal_outstanding": data.principal_outstanding,
                "interest_outstanding": data.interest_outstanding,
                "interest_overdue": interest_overdue,
                "principal_overdue": principal_overdue,
                "penal_interest_outstanding": data.penal_interest_outstanding,
                "charges_outstanding": data.charges_outstanding,
                "total_outstanding": total_outstanding,
                "total_principal_received": total_principal_received,
                "total_interest_received": total_interest_received,
                "total_penal_interest_received": total_penal_received,
                "days_past_due": days_past_due,
                "oldest_due_date": oldest_unpaid_due_date,
                "asset_classification": asset_classification,
                "npa_date": data.npa_date,
                "status": status_value,
                "remarks": (
                    f"Legacy onboarding as of {data.cutover_date.isoformat()}."
                    + (f" {data.remarks}" if data.remarks else "")
                ),
                "created_by": user_id,
            }
        )

        schedule: RepaymentSchedule | None = None
        if sorted_installments:
            for existing_schedule in await self.schedule_repo.get_all_schedules(loan_account.id):
                existing_schedule.is_current = False
                existing_schedule.superseded_date = data.cutover_date

            schedule = await self.schedule_repo.create(
                {
                    "loan_account_id": loan_account.id,
                    "schedule_number": 1,
                    "schedule_type": ScheduleType.ORIGINAL,
                    "principal_amount": data.total_disbursed_amount,
                    "interest_rate": data.current_interest_rate,
                    "tenure_months": len(sorted_installments),
                    "emi_amount": current_emi_amount,
                    "effective_date": data.account_open_date,
                    "first_installment_date": sorted_installments[0].due_date,
                    "last_installment_date": sorted_installments[-1].due_date,
                    "total_installments": len(sorted_installments),
                    "total_principal": sum(
                        (row.principal_amount for row in sorted_installments), Decimal("0")
                    ),
                    "total_interest": sum(
                        (row.interest_amount for row in sorted_installments), Decimal("0")
                    ),
                    "is_current": True,
                    "change_reason": "LEGACY_ONBOARDING",
                    "remarks": f"Imported schedule as of cutover date {data.cutover_date.isoformat()}",
                    "created_by": user_id,
                }
            )

            for row in sorted_installments:
                status_value = self._derive_installment_status(
                    due_date=row.due_date,
                    cutover_date=data.cutover_date,
                    principal_amount=row.principal_amount,
                    interest_amount=row.interest_amount,
                    penal_interest_due=row.penal_interest_due,
                    principal_paid=row.principal_paid,
                    interest_paid=row.interest_paid,
                    penal_interest_paid=row.penal_interest_paid,
                    explicit_status=row.status,
                )
                unpaid_principal = max(row.principal_amount - row.principal_paid, Decimal("0"))
                unpaid_interest = max(row.interest_amount - row.interest_paid, Decimal("0"))
                installment = await self.installment_repo.create(
                    {
                        "schedule_id": schedule.id,
                        "installment_number": row.installment_number,
                        "due_date": row.due_date,
                        "principal_amount": row.principal_amount,
                        "interest_amount": row.interest_amount,
                        "emi_amount": row.emi_amount,
                        "opening_balance": row.opening_balance,
                        "closing_balance": row.closing_balance,
                        "principal_paid": row.principal_paid,
                        "interest_paid": row.interest_paid,
                        "penal_interest_due": row.penal_interest_due,
                        "penal_interest_paid": row.penal_interest_paid,
                        "principal_overdue": (
                            unpaid_principal
                            if row.due_date <= data.cutover_date
                            and status_value
                            in {
                                InstallmentStatus.DUE,
                                InstallmentStatus.PARTIALLY_PAID,
                                InstallmentStatus.OVERDUE,
                            }
                            else Decimal("0")
                        ),
                        "interest_overdue": (
                            unpaid_interest
                            if row.due_date <= data.cutover_date
                            and status_value
                            in {
                                InstallmentStatus.DUE,
                                InstallmentStatus.PARTIALLY_PAID,
                                InstallmentStatus.OVERDUE,
                            }
                            else Decimal("0")
                        ),
                        "status": status_value,
                        "paid_date": (
                            row.paid_date if status_value == InstallmentStatus.PAID else None
                        ),
                        "created_by": user_id,
                    }
                )

                if data.create_historical_receipts:
                    paid_total = row.principal_paid + row.interest_paid + row.penal_interest_paid
                    if paid_total <= 0:
                        continue
                    receipt_number = (
                        f"LEG-{loan_account_number[-18:].replace('/', '-')}-"
                        f"{row.installment_number:05d}"
                    )[:50]
                    receipt = await self.receipt_repo.create(
                        {
                            "organization_id": organization_id,
                            "loan_account_id": loan_account.id,
                            "receipt_number": receipt_number,
                            "receipt_date": row.paid_date or row.due_date,
                            "value_date": row.paid_date or row.due_date,
                            "receipt_amount": paid_total,
                            "receipt_type": ReceiptType.REGULAR,
                            "receipt_mode": row.receipt_mode,
                            "instrument_number": row.receipt_reference,
                            "allocated_amount": paid_total,
                            "unallocated_amount": Decimal("0"),
                            "principal_allocated": row.principal_paid,
                            "interest_allocated": row.interest_paid,
                            "penal_interest_allocated": row.penal_interest_paid,
                            "charges_allocated": Decimal("0"),
                            "status": ReceiptStatus.ALLOCATED,
                            "processed_by_id": user_id,
                            "processed_at": datetime.combine(
                                row.paid_date or row.due_date, time.min, tzinfo=UTC
                            ),
                            "remarks": "Imported historical EMI receipt.",
                            "created_by": user_id,
                        }
                    )
                    sequence = 0
                    for component, amount in (
                        (AllocationComponent.PENAL_INTEREST, row.penal_interest_paid),
                        (AllocationComponent.INTEREST, row.interest_paid),
                        (AllocationComponent.PRINCIPAL, row.principal_paid),
                    ):
                        if amount <= 0:
                            continue
                        sequence += 1
                        await self.allocation_repo.create(
                            {
                                "receipt_id": receipt.id,
                                "installment_id": installment.id,
                                "allocation_component": component,
                                "allocated_amount": amount,
                                "allocation_sequence": sequence,
                                "remarks": "Imported historical allocation.",
                                "created_by": user_id,
                            }
                        )

        await self.db.flush()
        await self.db.refresh(loan_account)

        warnings = [
            *validation.warnings,
            (
                "Historical EMI receipts are LMS operational history only; "
                "GL accounting should be opened from the cutover outstanding balances."
            ),
        ]
        return HistoricalLoanOnboardingResult(
            loan_account_id=loan_account.id,
            loan_account_number=loan_account.loan_account_number,
            application_id=application.id,
            sanction_id=sanction.id,
            schedule_id=schedule.id if schedule else None,
            imported_installments=len(sorted_installments),
            imported_receipts=imported_receipts,
            dry_run=False,
            warnings=warnings,
        )

    async def get_loan_account(self, loan_account_id: UUID) -> LoanAccount:
        """Get loan account by ID."""
        loan_account = await self.loan_account_repo.get(loan_account_id)
        if not loan_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Loan account not found",
            )
        return loan_account

    async def get_loan_account_with_relations(self, loan_account_id: UUID) -> LoanAccount:
        """Get loan account with entity + product eagerly loaded.

        Lighter than `get_loan_account_with_details` (which loads schedules,
        receipts, etc.) — just enough for the view page header to surface
        entity_name, product_name, product_code without N+1.
        """
        from sqlalchemy import select as _select
        from sqlalchemy.orm import selectinload

        result = await self.db.execute(
            _select(LoanAccount)
            .where(LoanAccount.id == loan_account_id)
            .options(
                selectinload(LoanAccount.entity),
                selectinload(LoanAccount.product),
            )
        )
        loan_account = result.scalar_one_or_none()
        if not loan_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Loan account not found",
            )
        return loan_account

    async def get_loan_account_with_relations(self, loan_account_id: UUID) -> LoanAccount:
        """Get loan account with entity + product eagerly loaded.

        Lighter than `get_loan_account_with_details` (which loads schedules,
        receipts, etc.) — just enough for the view page header to surface
        entity_name, product_name, product_code without N+1.
        """
        from sqlalchemy import select as _select
        from sqlalchemy.orm import selectinload

        result = await self.db.execute(
            _select(LoanAccount)
            .where(LoanAccount.id == loan_account_id)
            .options(
                selectinload(LoanAccount.entity),
                selectinload(LoanAccount.product),
            )
        )
        loan_account = result.scalar_one_or_none()
        if not loan_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Loan account not found",
            )
        return loan_account

    async def get_loan_account_with_details(self, loan_account_id: UUID) -> LoanAccount:
        """Get loan account with all related data."""
        loan_account = await self.loan_account_repo.get_with_details(loan_account_id)
        if not loan_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Loan account not found",
            )
        return loan_account

    async def get_all_loan_accounts(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 50,
        include_inactive: bool = False,
        search: str | None = None,
        entity_id: UUID | None = None,
        product_id: UUID | None = None,
        loan_status: LoanAccountStatus | None = None,
        asset_classification: AssetClassification | None = None,
        min_dpd: int | None = None,
        max_dpd: int | None = None,
    ) -> tuple[list[LoanAccount], int]:
        """Get paginated list of loan accounts."""
        return await self.loan_account_repo.get_all_accounts(
            organization_id=organization_id,
            skip=skip,
            limit=limit,
            include_inactive=include_inactive,
            search=search,
            entity_id=entity_id,
            product_id=product_id,
            status=loan_status,
            asset_classification=asset_classification,
            min_dpd=min_dpd,
            max_dpd=max_dpd,
        )

    async def update_loan_account(
        self,
        loan_account_id: UUID,
        data: LoanAccountUpdate,
        user_id: UUID,
    ) -> LoanAccount:
        """Update loan account."""
        loan_account = await self.get_loan_account(loan_account_id)

        update_data = data.model_dump(exclude_unset=True)
        update_data["updated_by"] = user_id

        loan_account = await self.loan_account_repo.update(loan_account, update_data)
        await self.db.flush()
        await self.db.refresh(loan_account)

        return loan_account

    async def activate_loan_account(
        self,
        loan_account_id: UUID,
        user_id: UUID,
    ) -> LoanAccount:
        """Activate loan account after first disbursement."""
        loan_account = await self.get_loan_account(loan_account_id)

        if loan_account.status != LoanAccountStatus.CREATED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Loan account must be in CREATED status to activate",
            )

        if loan_account.total_disbursed_amount <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one disbursement required to activate",
            )

        update_data = {
            "status": LoanAccountStatus.ACTIVE,
            "updated_by": user_id,
        }

        loan_account = await self.loan_account_repo.update(loan_account, update_data)
        await self.db.flush()
        await self.db.refresh(loan_account)

        return loan_account

    # =========================================================================
    # Disbursement Operations
    # =========================================================================

    async def create_disbursement(
        self,
        data: DisbursementCreate,
        user_id: UUID,
    ) -> Disbursement:
        """Create a new disbursement request."""
        loan_account = await self.get_loan_account(data.loan_account_id)

        # Validate amount
        if data.requested_amount > loan_account.undisbursed_amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Requested amount exceeds undisbursed amount: {loan_account.undisbursed_amount}",
            )

        # Generate reference
        disb_number = await self.disbursement_repo.get_next_disbursement_number(
            data.loan_account_id
        )
        reference = f"{loan_account.loan_account_number}/D{disb_number:02d}"

        disbursement_data = data.model_dump()
        disbursement_data["disbursement_number"] = disb_number
        disbursement_data["disbursement_reference"] = reference
        disbursement_data["status"] = DisbursementStatus.PENDING
        disbursement_data["created_by"] = user_id

        disbursement = await self.disbursement_repo.create(disbursement_data)
        await self.db.flush()
        await self.db.refresh(disbursement)

        return disbursement

    async def approve_disbursement(
        self,
        disbursement_id: UUID,
        approval: DisbursementApproval,
        user_id: UUID,
    ) -> Disbursement:
        """Approve a disbursement request."""
        disbursement = await self.disbursement_repo.get(disbursement_id)
        if not disbursement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Disbursement not found",
            )

        if disbursement.status != DisbursementStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only pending disbursements can be approved",
            )

        update_data = {
            "approved_amount": approval.approved_amount,
            "approval_date": date.today(),
            "approved_by_id": user_id,
            "approved_at": date.today(),
            "status": DisbursementStatus.APPROVED,
            "updated_by": user_id,
        }

        disbursement = await self.disbursement_repo.update(disbursement, update_data)
        await self.db.flush()
        await self.db.refresh(disbursement)

        return disbursement

    async def process_disbursement(
        self,
        disbursement_id: UUID,
        process_data: DisbursementProcess,
        user_id: UUID,
    ) -> Disbursement:
        """Process an approved disbursement."""
        disbursement = await self.disbursement_repo.get(disbursement_id)
        if not disbursement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Disbursement not found",
            )

        if disbursement.status != DisbursementStatus.APPROVED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only approved disbursements can be processed",
            )

        loan_account = await self.get_loan_account(disbursement.loan_account_id)

        # Calculate net disbursement
        disbursed_amount = disbursement.approved_amount
        net_disbursement = disbursed_amount - disbursement.disbursement_charges

        # Update disbursement
        disb_update = {
            "disbursed_amount": disbursed_amount,
            "net_disbursement": net_disbursement,
            "disbursement_date": process_data.disbursement_date,
            "value_date": process_data.value_date,
            "utr_number": process_data.utr_number,
            "cheque_number": process_data.cheque_number,
            "processed_by_id": user_id,
            "processed_at": date.today(),
            "status": DisbursementStatus.PROCESSED,
            "updated_by": user_id,
        }

        disbursement = await self.disbursement_repo.update(disbursement, disb_update)

        # Update loan account balances
        is_first = loan_account.first_disbursement_date is None
        account_update = {
            "total_disbursed_amount": loan_account.total_disbursed_amount + disbursed_amount,
            "undisbursed_amount": loan_account.undisbursed_amount - disbursed_amount,
            "principal_outstanding": loan_account.principal_outstanding + disbursed_amount,
            "total_outstanding": loan_account.total_outstanding + disbursed_amount,
            "last_disbursement_date": process_data.disbursement_date,
            "updated_by": user_id,
        }

        if is_first:
            account_update["first_disbursement_date"] = process_data.disbursement_date

        await self.loan_account_repo.update(loan_account, account_update)
        await self.db.flush()
        await self.db.refresh(disbursement)

        return disbursement

    async def get_loan_disbursements(
        self,
        loan_account_id: UUID,
        include_inactive: bool = False,
    ) -> list[Disbursement]:
        """Get all disbursements for a loan account."""
        return await self.disbursement_repo.get_loan_disbursements(
            loan_account_id, include_inactive
        )

    # =========================================================================
    # Repayment Schedule Operations
    # =========================================================================

    async def generate_schedule(
        self,
        data: RepaymentScheduleCreate,
        user_id: UUID,
    ) -> RepaymentSchedule:
        """Generate repayment schedule for a loan account."""
        loan_account = await self.get_loan_account(data.loan_account_id)

        # Calculate EMI
        emi = self._calculate_emi(
            principal=data.principal_amount,
            rate=data.interest_rate,
            tenure=data.tenure_months,
        )

        # Get next schedule number
        schedule_number = await self.schedule_repo.get_next_schedule_number(data.loan_account_id)

        # Supersede current schedule if exists
        if schedule_number > 1:
            current = await self.schedule_repo.get_current_schedule(data.loan_account_id)
            if current:
                await self.schedule_repo.supersede_current_schedule(
                    data.loan_account_id,
                    None,  # Will update after creating new schedule
                    data.effective_date,
                )

        # Calculate last installment date
        last_date = self._add_months(data.first_installment_date, data.tenure_months - 1)

        # Create schedule
        schedule_data = data.model_dump()
        schedule_data["schedule_number"] = schedule_number
        schedule_data["emi_amount"] = emi
        schedule_data["last_installment_date"] = last_date
        schedule_data["total_installments"] = data.tenure_months
        schedule_data["total_principal"] = data.principal_amount
        schedule_data["total_interest"] = (emi * data.tenure_months) - data.principal_amount
        schedule_data["is_current"] = True
        schedule_data["created_by"] = user_id

        schedule = await self.schedule_repo.create(schedule_data)

        # Generate installments
        await self._generate_installments(
            schedule_id=schedule.id,
            principal=data.principal_amount,
            interest_rate=data.interest_rate,
            tenure=data.tenure_months,
            emi=emi,
            first_date=data.first_installment_date,
            user_id=user_id,
        )

        # Update loan account
        await self.loan_account_repo.update(
            loan_account,
            {
                "current_emi_amount": emi,
                "repayment_start_date": data.first_installment_date,
                "maturity_date": last_date,
                "updated_by": user_id,
            },
        )

        await self.db.flush()
        await self.db.refresh(schedule)

        return schedule

    async def _generate_installments(
        self,
        schedule_id: UUID,
        principal: Decimal,
        interest_rate: Decimal,
        tenure: int,
        emi: Decimal,
        first_date: date,
        user_id: UUID,
    ) -> None:
        """Generate installment records for a schedule."""
        balance = principal
        monthly_rate = interest_rate / Decimal("1200")

        for i in range(tenure):
            due_date = self._add_months(first_date, i)
            interest_amount = (balance * monthly_rate).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

            if i == tenure - 1:
                # Last installment - adjust for rounding
                principal_amount = balance
                installment_emi = principal_amount + interest_amount
            else:
                principal_amount = emi - interest_amount
                installment_emi = emi

            closing_balance = balance - principal_amount

            installment_data = {
                "schedule_id": schedule_id,
                "installment_number": i + 1,
                "due_date": due_date,
                "principal_amount": principal_amount,
                "interest_amount": interest_amount,
                "emi_amount": installment_emi,
                "opening_balance": balance,
                "closing_balance": closing_balance,
                "status": InstallmentStatus.NOT_DUE,
                "created_by": user_id,
            }

            await self.installment_repo.create(installment_data)
            balance = closing_balance

    def _calculate_emi(
        self,
        principal: Decimal,
        rate: Decimal,
        tenure: int,
    ) -> Decimal:
        """Calculate EMI using standard formula."""
        if rate == 0:
            return (principal / tenure).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        monthly_rate = rate / Decimal("1200")
        factor = (1 + monthly_rate) ** tenure
        emi = principal * monthly_rate * factor / (factor - 1)
        return emi.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def _add_months(self, start_date: date, months: int) -> date:
        """Add months to a date."""
        month = start_date.month - 1 + months
        year = start_date.year + month // 12
        month = month % 12 + 1
        day = min(
            start_date.day,
            [31, 29 if year % 4 == 0 else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1],
        )
        return date(year, month, day)

    async def get_current_schedule(
        self,
        loan_account_id: UUID,
    ) -> RepaymentSchedule | None:
        """Get current repayment schedule."""
        return await self.schedule_repo.get_current_schedule(loan_account_id)

    async def get_due_installments(
        self,
        loan_account_id: UUID,
        as_of_date: date | None = None,
    ) -> list[ScheduleInstallment]:
        """Get due installments for a loan account."""
        schedule = await self.schedule_repo.get_current_schedule(loan_account_id)
        if not schedule:
            return []

        return await self.installment_repo.get_due_installments(
            schedule.id,
            as_of_date or date.today(),
        )

    # =========================================================================
    # Receipt Operations
    # =========================================================================

    async def create_receipt(
        self,
        data: LoanReceiptCreate,
        user_id: UUID,
    ) -> LoanReceipt:
        """Create a new loan receipt."""
        if data.loan_account_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Loan account is required",
            )
        loan_account = await self.get_loan_account(data.loan_account_id)

        # Generate receipt number
        receipt_number = await self.receipt_repo.generate_receipt_number(
            loan_account.organization_id
        )

        receipt_data = data.model_dump(exclude_none=True)
        receipt_data["organization_id"] = loan_account.organization_id
        receipt_data["value_date"] = data.value_date or data.receipt_date
        receipt_data["receipt_number"] = receipt_number
        receipt_data["unallocated_amount"] = data.receipt_amount
        receipt_data["status"] = ReceiptStatus.PENDING
        receipt_data["created_by"] = user_id

        receipt = await self.receipt_repo.create(receipt_data)
        await self.db.flush()
        await self.db.refresh(receipt)

        return receipt

    async def allocate_receipt(
        self,
        receipt_id: UUID,
        user_id: UUID,
    ) -> LoanReceipt:
        """Allocate receipt to loan dues using FIFO."""
        receipt = await self.receipt_repo.get_with_allocations(receipt_id)
        if not receipt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Receipt not found",
            )

        if receipt.status != ReceiptStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only pending receipts can be allocated",
            )

        loan_account = await self.get_loan_account(receipt.loan_account_id)
        schedule = await self.schedule_repo.get_current_schedule(loan_account.id)

        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No repayment schedule found",
            )

        remaining = receipt.receipt_amount
        allocation_seq = 0

        # Get due installments in FIFO order (oldest due_date first).
        due_installments = await self.installment_repo.get_due_installments(
            schedule.id, date.today()
        )

        principal_allocated = Decimal("0")
        interest_allocated = Decimal("0")
        penal_interest_allocated = Decimal("0")

        # Receipt allocation — CROSS-INSTALLMENT PRIORITY per CLAUDE.md §4.8.
        # The priority is:
        #   penal (all overdue) → interest (all overdue) → principal (all overdue)
        # i.e. ALL penal interest across every overdue installment is cleared
        # before ANY current interest is touched, and ALL interest is cleared
        # before ANY principal. Charges are not yet modelled on the
        # installment row; when they are added they slot between penal and
        # interest per the spec.
        #
        # The previous implementation did per-installment priority (penal →
        # int → prin inside each installment, moving to the next installment
        # before revisiting any bucket). That was a material deviation from
        # the RBI spec; see .stubs-approved.md entry
        # ALLOCATION-PRIORITY-2026-04-23 for the closure rationale.

        async def _allocate_component(
            component_attr_due: str,
            component_attr_paid: str,
            component: AllocationComponent,
        ) -> Decimal:
            nonlocal remaining, allocation_seq
            total_allocated = Decimal("0")
            for installment in due_installments:
                if remaining <= 0:
                    break
                due_amount = getattr(installment, component_attr_due)
                paid_amount = getattr(installment, component_attr_paid)
                outstanding = due_amount - paid_amount
                if outstanding <= 0:
                    continue
                alloc = min(remaining, outstanding)
                allocation_seq += 1
                await self.allocation_repo.create(
                    {
                        "receipt_id": receipt_id,
                        "installment_id": installment.id,
                        "allocation_component": component,
                        "allocated_amount": alloc,
                        "allocation_sequence": allocation_seq,
                        "created_by": user_id,
                    }
                )
                remaining -= alloc
                total_allocated += alloc
                new_paid = paid_amount + alloc
                # Update the in-memory row AND persist so the next pass sees
                # the new paid amount when it computes outstanding.
                setattr(installment, component_attr_paid, new_paid)
                await self.installment_repo.update(installment, {component_attr_paid: new_paid})
            return total_allocated

        # Pass 1 — penal interest across all overdue installments.
        penal_interest_allocated = await _allocate_component(
            "penal_interest_due", "penal_interest_paid", AllocationComponent.PENAL_INTEREST
        )
        # Pass 2 — interest across all overdue installments.
        interest_allocated = await _allocate_component(
            "interest_amount", "interest_paid", AllocationComponent.INTEREST
        )
        # Pass 3 — principal across all overdue installments.
        principal_allocated = await _allocate_component(
            "principal_amount", "principal_paid", AllocationComponent.PRINCIPAL
        )

        # Update installment statuses after all three passes so we can read
        # the final totals per installment.
        for installment in due_installments:
            total_paid = (
                installment.principal_paid
                + installment.interest_paid
                + installment.penal_interest_paid
            )
            total_due = installment.emi_amount + installment.penal_interest_due
            if total_paid >= total_due:
                await self.installment_repo.update(
                    installment,
                    {
                        "status": InstallmentStatus.PAID,
                        "paid_date": receipt.value_date,
                    },
                )
            elif total_paid > 0:
                await self.installment_repo.update(
                    installment, {"status": InstallmentStatus.PARTIALLY_PAID}
                )

        # Update receipt
        allocated = receipt.receipt_amount - remaining
        receipt_update = {
            "allocated_amount": allocated,
            "unallocated_amount": remaining,
            "principal_allocated": principal_allocated,
            "interest_allocated": interest_allocated,
            "penal_interest_allocated": penal_interest_allocated,
            "status": ReceiptStatus.ALLOCATED,
            "processed_by_id": user_id,
            "processed_at": date.today(),
            "updated_by": user_id,
        }

        receipt = await self.receipt_repo.update(receipt, receipt_update)

        # Update loan account balances
        await self.loan_account_repo.update(
            loan_account,
            {
                "principal_outstanding": loan_account.principal_outstanding - principal_allocated,
                "total_outstanding": loan_account.total_outstanding - allocated,
                "total_principal_received": loan_account.total_principal_received
                + principal_allocated,
                "total_interest_received": loan_account.total_interest_received
                + interest_allocated,
                "total_penal_interest_received": loan_account.total_penal_interest_received
                + penal_interest_allocated,
                "updated_by": user_id,
            },
        )

        await self.db.flush()
        await self.db.refresh(receipt)

        return receipt

    async def mark_receipt_bounced(
        self,
        receipt_id: UUID,
        bounce_data: ReceiptBounceRequest,
        user_id: UUID,
    ) -> LoanReceipt:
        """Mark a receipt as bounced."""
        receipt = await self.receipt_repo.get(receipt_id)
        if not receipt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Receipt not found",
            )

        # Reverse the receipt's allocations and roll back the loan-account
        # balances. A bounced receipt must not leave behind the principal /
        # interest / penal credits it originally booked — otherwise the
        # outstanding balance is understated and the next demand looks
        # already paid.
        from sqlalchemy import select

        from app.models.lending.loan_account import LoanAccount
        from app.models.lending.receipt import LoanReceiptAllocation

        # 1. Sum the original component allocations
        alloc_result = await self.db.execute(
            select(LoanReceiptAllocation).where(LoanReceiptAllocation.receipt_id == receipt_id)
        )
        allocations = list(alloc_result.scalars().all())

        principal_rev = sum(
            (a.amount or 0)
            for a in allocations
            if str(a.component).upper() in {"PRINCIPAL", "OVERDUE_PRINCIPAL"}
        )
        interest_rev = sum(
            (a.amount or 0)
            for a in allocations
            if str(a.component).upper() in {"INTEREST", "OVERDUE_INTEREST"}
        )
        penal_rev = sum(
            (a.amount or 0)
            for a in allocations
            if str(a.component).upper() in {"PENAL_INTEREST", "PENAL"}
        )
        charges_rev = sum(
            (a.amount or 0)
            for a in allocations
            if str(a.component).upper() in {"CHARGES", "OTHER_CHARGES"}
        )

        # 2. Roll back the loan-account outstanding columns
        loan = await self.db.get(LoanAccount, receipt.loan_account_id)
        if loan is not None:
            loan.principal_outstanding = (loan.principal_outstanding or 0) + principal_rev
            loan.interest_outstanding = (loan.interest_outstanding or 0) + interest_rev
            if hasattr(loan, "penal_interest_outstanding"):
                loan.penal_interest_outstanding = (loan.penal_interest_outstanding or 0) + penal_rev
            if hasattr(loan, "charges_outstanding"):
                loan.charges_outstanding = (loan.charges_outstanding or 0) + charges_rev
            if hasattr(loan, "total_received"):
                loan.total_received = (loan.total_received or 0) - (receipt.receipt_amount or 0)

        # 3. Mark allocations as reversed (soft) so audit trail is clear
        for a in allocations:
            if hasattr(a, "is_reversed"):
                a.is_reversed = True
            if hasattr(a, "reversed_at"):
                from datetime import datetime, timezone

                a.reversed_at = datetime.now(timezone.utc)

        update_data = {
            "bounced": True,
            "bounce_date": bounce_data.bounce_date,
            "bounce_reason": bounce_data.bounce_reason,
            "bounce_charges": bounce_data.bounce_charges,
            "status": ReceiptStatus.BOUNCED,
            "updated_by": user_id,
        }

        receipt = await self.receipt_repo.update(receipt, update_data)
        await self.db.flush()
        await self.db.refresh(receipt)

        from app.models.lending.lifecycle_event import (
            LifecycleActorKind,
            LifecycleSubjectType,
        )
        from app.services.lending.lifecycle_service import LifecycleService

        await LifecycleService(self.db).record_event(
            organization_id=(
                receipt.organization_id
                if hasattr(receipt, "organization_id")
                else loan.organization_id if "loan" in dir() else None
            ),
            subject_type=LifecycleSubjectType.RECEIPT,
            subject_id=receipt.id,
            event_type="RECEIPT_BOUNCED",
            actor_kind=LifecycleActorKind.LENDER,
            actor_user_id=user_id,
            business_number=getattr(receipt, "receipt_number", None),
            state_to="BOUNCED",
            reason_text=bounce_data.bounce_reason,
            payload={
                "bounce_date": (
                    bounce_data.bounce_date.isoformat()
                    if hasattr(bounce_data, "bounce_date") and bounce_data.bounce_date
                    else None
                ),
                "bounce_charges": (
                    float(bounce_data.bounce_charges or 0)
                    if hasattr(bounce_data, "bounce_charges")
                    else None
                ),
                "principal_reversed": float(principal_rev),
                "interest_reversed": float(interest_rev),
                "penal_reversed": float(penal_rev),
                "charges_reversed": float(charges_rev),
                "receipt_amount": float(receipt.receipt_amount or 0),
                "loan_account_id": str(receipt.loan_account_id),
            },
        )
        # Mirror on the loan-account timeline
        await LifecycleService(self.db).record_event(
            organization_id=(
                receipt.organization_id if hasattr(receipt, "organization_id") else None
            ),
            subject_type=LifecycleSubjectType.LOAN_ACCOUNT,
            subject_id=receipt.loan_account_id,
            event_type="RECEIPT_BOUNCED",
            actor_kind=LifecycleActorKind.LENDER,
            actor_user_id=user_id,
            business_number=getattr(receipt, "receipt_number", None),
            payload={
                "receipt_id": str(receipt.id),
                "receipt_amount": float(receipt.receipt_amount or 0),
                "bounce_reason": bounce_data.bounce_reason,
            },
        )

        return receipt

    async def get_loan_receipts(
        self,
        loan_account_id: UUID,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> list[LoanReceipt]:
        """Get all receipts for a loan account."""
        return await self.receipt_repo.get_loan_receipts(
            loan_account_id,
            from_date=from_date,
            to_date=to_date,
        )

    # =========================================================================
    # Mandate Operations
    # =========================================================================

    async def create_mandate(
        self,
        data: LoanMandateCreate,
        user_id: UUID,
    ) -> LoanMandate:
        """Create a new NACH mandate."""
        loan_account = await self.get_loan_account(data.loan_account_id)

        # Generate mandate reference
        reference = f"{loan_account.loan_account_number}/M{date.today().strftime('%Y%m%d')}"

        mandate_data = data.model_dump()
        mandate_data["mandate_reference"] = reference
        mandate_data["status"] = MandateStatus.INITIATED
        mandate_data["created_by"] = user_id

        mandate = await self.mandate_repo.create(mandate_data)
        await self.db.flush()
        await self.db.refresh(mandate)

        return mandate

    async def register_mandate(
        self,
        mandate_id: UUID,
        register_data: MandateRegisterRequest,
        user_id: UUID,
    ) -> LoanMandate:
        """Register mandate with UMRN."""
        mandate = await self.mandate_repo.get(mandate_id)
        if not mandate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mandate not found",
            )

        update_data = {
            "umrn": register_data.umrn,
            "registration_date": register_data.registration_date,
            "status": MandateStatus.ACTIVE,
            "updated_by": user_id,
        }

        mandate = await self.mandate_repo.update(mandate, update_data)
        await self.db.flush()
        await self.db.refresh(mandate)

        return mandate

    async def cancel_mandate(
        self,
        mandate_id: UUID,
        cancel_data: MandateCancelRequest,
        user_id: UUID,
    ) -> LoanMandate:
        """Cancel a mandate."""
        mandate = await self.mandate_repo.get(mandate_id)
        if not mandate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mandate not found",
            )

        update_data = {
            "cancellation_date": cancel_data.cancellation_date,
            "cancellation_reason": cancel_data.cancellation_reason,
            "status": MandateStatus.CANCELLED,
            "updated_by": user_id,
        }

        mandate = await self.mandate_repo.update(mandate, update_data)
        await self.db.flush()
        await self.db.refresh(mandate)

        return mandate

    async def get_loan_mandates(
        self,
        loan_account_id: UUID,
    ) -> list[LoanMandate]:
        """Get all mandates for a loan account."""
        return await self.mandate_repo.get_loan_mandates(loan_account_id)

    # =========================================================================
    # Asset Classification Operations
    # =========================================================================

    async def update_asset_classification(
        self,
        loan_account_id: UUID,
        user_id: UUID,
    ) -> LoanAccount:
        """Update asset classification based on DPD."""
        loan_account = await self.get_loan_account(loan_account_id)

        # Get oldest due date
        schedule = await self.schedule_repo.get_current_schedule(loan_account_id)
        if not schedule:
            return loan_account

        oldest_due = await self.installment_repo.get_oldest_unpaid_date(schedule.id)
        if not oldest_due:
            # No dues, classification is STANDARD
            new_classification = AssetClassification.STANDARD
            dpd = 0
        else:
            dpd = (date.today() - oldest_due).days
            new_classification = self._get_classification_from_dpd(dpd)

        # Check if classification changed
        if new_classification != loan_account.asset_classification:
            # Record history
            await self.classification_repo.create(
                {
                    "loan_account_id": loan_account_id,
                    "effective_date": date.today(),
                    "previous_classification": loan_account.asset_classification,
                    "new_classification": new_classification,
                    "days_past_due": dpd,
                    "principal_outstanding": loan_account.principal_outstanding,
                    "total_outstanding": loan_account.total_outstanding,
                    "change_reason": "SYSTEM_AUTO",
                    "created_by": user_id,
                }
            )

            # Determine if accrual should be suspended
            is_npa = new_classification in [
                AssetClassification.NPA,
                AssetClassification.SUBSTANDARD,
                AssetClassification.DOUBTFUL_1,
                AssetClassification.DOUBTFUL_2,
                AssetClassification.DOUBTFUL_3,
                AssetClassification.LOSS,
            ]

            update_data = {
                "days_past_due": dpd,
                "oldest_due_date": oldest_due,
                "asset_classification": new_classification,
                "updated_by": user_id,
            }

            if is_npa and not loan_account.accrual_suspended:
                update_data["accrual_suspended"] = True
                update_data["accrual_suspension_date"] = date.today()
                update_data["npa_date"] = date.today()
                update_data["npa_amount"] = loan_account.total_outstanding

            loan_account = await self.loan_account_repo.update(loan_account, update_data)

        await self.db.flush()
        await self.db.refresh(loan_account)

        return loan_account

    def _get_classification_from_dpd(self, dpd: int) -> AssetClassification:
        """Get asset classification from DPD."""
        if dpd <= 0:
            return AssetClassification.STANDARD
        elif dpd <= 30:
            return AssetClassification.SMA_0
        elif dpd <= 60:
            return AssetClassification.SMA_1
        elif dpd <= 90:
            return AssetClassification.SMA_2
        else:
            return AssetClassification.NPA

    async def get_classification_history(
        self,
        loan_account_id: UUID,
    ) -> list[AssetClassificationHistory]:
        """Get asset classification history."""
        return await self.classification_repo.get_loan_history(loan_account_id)

    # =========================================================================
    # Accrual Operations
    # =========================================================================

    async def run_daily_accrual(
        self,
        loan_account_id: UUID,
        accrual_date: date,
        user_id: UUID,
    ) -> LoanAccrual | None:
        """Run daily interest accrual for a loan account."""
        loan_account = await self.get_loan_account(loan_account_id)

        if loan_account.status != LoanAccountStatus.ACTIVE:
            return None

        if loan_account.principal_outstanding <= 0:
            return None

        # Check if already accrued
        existing = await self.accrual_repo.get_accrual_for_date(
            loan_account_id, accrual_date, AccrualCategory.INTEREST
        )
        if existing:
            return existing

        # Calculate daily interest
        daily_rate = loan_account.current_interest_rate / Decimal("36500")
        accrued = loan_account.principal_outstanding * daily_rate

        # Get cumulative
        total_accrued = await self.accrual_repo.get_total_accrued(loan_account_id)

        accrual_data = {
            "loan_account_id": loan_account_id,
            "accrual_date": accrual_date,
            "accrual_category": AccrualCategory.INTEREST,
            "principal_balance": loan_account.principal_outstanding,
            "interest_rate": loan_account.current_interest_rate,
            "day_count_basis": 365,
            "accrued_amount": accrued,
            "cumulative_accrued": total_accrued + accrued,
            "status": (
                AccrualStatus.ACCRUED
                if not loan_account.accrual_suspended
                else AccrualStatus.SUSPENDED
            ),
            "moved_to_suspense": loan_account.accrual_suspended,
            "suspense_date": date.today() if loan_account.accrual_suspended else None,
            "created_by": user_id,
        }

        accrual = await self.accrual_repo.create(accrual_data)

        # Update loan account
        if loan_account.accrual_suspended:
            await self.loan_account_repo.update(
                loan_account,
                {
                    "suspended_interest": loan_account.suspended_interest + accrued,
                    "last_accrual_date": accrual_date,
                    "updated_by": user_id,
                },
            )
        else:
            await self.loan_account_repo.update(
                loan_account,
                {
                    "interest_accrued_not_due": loan_account.interest_accrued_not_due + accrued,
                    "interest_outstanding": loan_account.interest_outstanding + accrued,
                    "total_outstanding": loan_account.total_outstanding + accrued,
                    "last_accrual_date": accrual_date,
                    "updated_by": user_id,
                },
            )

        await self.db.flush()
        await self.db.refresh(accrual)

        return accrual

    # =========================================================================
    # Provision Operations
    # =========================================================================

    async def calculate_provision(
        self,
        loan_account_id: UUID,
        provision_date: date,
        user_id: UUID,
    ) -> LoanProvision:
        """Calculate and create provision for a loan account."""
        loan_account = await self.get_loan_account(loan_account_id)

        # Determine whether the loan is secured by querying the sanction's
        # security roster. A loan is "secured" for provisioning purposes if
        # it has at least one ACTIVE LoanSecurity row of category PRIMARY or
        # COLLATERAL (per CLAUDE.md §4.8 — RBI secured/unsecured table).
        has_security = False
        try:
            from sqlalchemy import select

            from app.models.lending.sanction import LoanSecurity
            from app.models.lending.enums import (
                SecurityCategory,
                SecurityStatus,
            )

            security_result = await self.db.execute(
                select(LoanSecurity.id)
                .where(
                    LoanSecurity.sanction_id == loan_account.sanction_id,
                    LoanSecurity.security_category.in_(
                        [SecurityCategory.PRIMARY, SecurityCategory.COLLATERAL]
                    ),
                    LoanSecurity.status.notin_(
                        [SecurityStatus.RELEASED, SecurityStatus.SUBSTITUTED]
                    ),
                )
                .limit(1)
            )
            has_security = security_result.scalar_one_or_none() is not None
        except Exception:  # noqa: BLE001 — keep provisioning available even
            # if the security check fails. Conservative fallback is True (i.e.
            # treat as secured / lower provision); however, for safety we
            # actually want UN-secured (higher provision) as the conservative
            # default in lending. Use False on failure.
            has_security = False

        prov_category, prov_pct = self._get_provision_rate(
            loan_account.asset_classification,
            has_security=has_security,
        )

        provision_required = (loan_account.total_outstanding * prov_pct / Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        # Get previous provision
        last_provision = await self.provision_repo.get_latest_provision(loan_account_id)
        provision_held = last_provision.provision_required if last_provision else Decimal("0")
        provision_movement = provision_required - provision_held

        provision_data = {
            "organization_id": loan_account.organization_id,
            "loan_account_id": loan_account_id,
            "provision_date": provision_date,
            "asset_classification": loan_account.asset_classification,
            "provisioning_category": prov_category,
            "principal_outstanding": loan_account.principal_outstanding,
            "total_outstanding": loan_account.total_outstanding,
            "provision_percentage": prov_pct,
            "provision_required": provision_required,
            "provision_held": provision_held,
            "provision_movement": provision_movement,
            "created_by": user_id,
        }

        provision = await self.provision_repo.create(provision_data)

        # Update loan account
        await self.loan_account_repo.update(
            loan_account,
            {
                "provision_percentage": prov_pct,
                "provision_amount": provision_required,
                "provision_held": provision_required,
                "updated_by": user_id,
            },
        )

        await self.db.flush()
        await self.db.refresh(provision)

        return provision

    def _get_provision_rate(
        self,
        classification: AssetClassification,
        has_security: bool,
    ) -> tuple[ProvisioningCategory, Decimal]:
        """Get provision rate based on classification."""
        rates = {
            AssetClassification.STANDARD: (ProvisioningCategory.STANDARD, Decimal("0.40")),
            AssetClassification.SMA_0: (ProvisioningCategory.STANDARD, Decimal("0.40")),
            AssetClassification.SMA_1: (ProvisioningCategory.STANDARD, Decimal("0.40")),
            AssetClassification.SMA_2: (ProvisioningCategory.STANDARD, Decimal("0.40")),
            AssetClassification.NPA: (
                (
                    ProvisioningCategory.SUBSTANDARD_SECURED
                    if has_security
                    else ProvisioningCategory.SUBSTANDARD_UNSECURED
                ),
                Decimal("15") if has_security else Decimal("25"),
            ),
            AssetClassification.SUBSTANDARD: (
                (
                    ProvisioningCategory.SUBSTANDARD_SECURED
                    if has_security
                    else ProvisioningCategory.SUBSTANDARD_UNSECURED
                ),
                Decimal("15") if has_security else Decimal("25"),
            ),
            AssetClassification.DOUBTFUL_1: (ProvisioningCategory.DOUBTFUL_1, Decimal("25")),
            AssetClassification.DOUBTFUL_2: (ProvisioningCategory.DOUBTFUL_2, Decimal("40")),
            AssetClassification.DOUBTFUL_3: (ProvisioningCategory.DOUBTFUL_3, Decimal("100")),
            AssetClassification.LOSS: (ProvisioningCategory.LOSS, Decimal("100")),
        }
        return rates.get(classification, (ProvisioningCategory.STANDARD, Decimal("0.40")))

    # =========================================================================
    # Adjustment Operations
    # =========================================================================

    async def create_adjustment(
        self,
        data: LoanAdjustmentCreate,
        user_id: UUID,
    ) -> LoanAdjustment:
        """Create a loan adjustment (rate change, waiver, etc.)."""
        loan_account = await self.get_loan_account(data.loan_account_id)

        # Generate reference
        reference = await self.adjustment_repo.generate_adjustment_reference(data.loan_account_id)

        adjustment_data = data.model_dump()
        adjustment_data["adjustment_reference"] = reference
        adjustment_data["previous_interest_rate"] = loan_account.current_interest_rate
        adjustment_data["previous_emi"] = loan_account.current_emi_amount
        adjustment_data["previous_maturity_date"] = loan_account.maturity_date
        adjustment_data["created_by"] = user_id

        adjustment = await self.adjustment_repo.create(adjustment_data)

        # Apply adjustment to loan account
        if data.adjustment_type == AdjustmentType.RATE_CHANGE and data.new_interest_rate:
            await self.loan_account_repo.update(
                loan_account,
                {
                    "current_interest_rate": data.new_interest_rate,
                    "updated_by": user_id,
                },
            )

        await self.db.flush()
        await self.db.refresh(adjustment)

        return adjustment

    async def get_loan_adjustments(
        self,
        loan_account_id: UUID,
    ) -> list[LoanAdjustment]:
        """Get all adjustments for a loan account."""
        return await self.adjustment_repo.get_loan_adjustments(loan_account_id)

    # =========================================================================
    # Summary/Report Operations
    # =========================================================================

    async def get_portfolio_summary(
        self,
        organization_id: UUID,
    ) -> dict[str, Any]:
        """Get portfolio summary for organization."""
        accounts, total = await self.loan_account_repo.get_all_accounts(
            organization_id=organization_id,
            limit=10000,
        )

        total_sanctioned = sum(a.sanctioned_amount for a in accounts)
        total_disbursed = sum(a.total_disbursed_amount for a in accounts)
        total_outstanding = sum(a.total_outstanding for a in accounts)
        total_overdue = sum(a.principal_overdue + a.interest_overdue for a in accounts)
        total_npa = sum(
            a.total_outstanding
            for a in accounts
            if a.asset_classification
            in [
                AssetClassification.NPA,
                AssetClassification.SUBSTANDARD,
                AssetClassification.DOUBTFUL_1,
                AssetClassification.DOUBTFUL_2,
                AssetClassification.DOUBTFUL_3,
                AssetClassification.LOSS,
            ]
        )

        standard_count = len(
            [a for a in accounts if a.asset_classification == AssetClassification.STANDARD]
        )
        sma_count = len(
            [
                a
                for a in accounts
                if a.asset_classification
                in [AssetClassification.SMA_0, AssetClassification.SMA_1, AssetClassification.SMA_2]
            ]
        )
        npa_count = len(
            [
                a
                for a in accounts
                if a.asset_classification
                in [
                    AssetClassification.NPA,
                    AssetClassification.SUBSTANDARD,
                    AssetClassification.DOUBTFUL_1,
                    AssetClassification.DOUBTFUL_2,
                    AssetClassification.DOUBTFUL_3,
                    AssetClassification.LOSS,
                ]
            ]
        )

        return {
            "total_accounts": total,
            "total_sanctioned": total_sanctioned,
            "total_disbursed": total_disbursed,
            "total_outstanding": total_outstanding,
            "total_overdue": total_overdue,
            "total_npa_amount": total_npa,
            "standard_count": standard_count,
            "sma_count": sma_count,
            "npa_count": npa_count,
        }

    async def get_dpd_buckets(
        self,
        organization_id: UUID,
    ) -> list[dict[str, Any]]:
        """Get DPD bucket wise analysis."""
        accounts, _ = await self.loan_account_repo.get_all_accounts(
            organization_id=organization_id,
            limit=10000,
        )

        buckets = {
            "0": {"count": 0, "principal": Decimal("0"), "total": Decimal("0")},
            "1-30": {"count": 0, "principal": Decimal("0"), "total": Decimal("0")},
            "31-60": {"count": 0, "principal": Decimal("0"), "total": Decimal("0")},
            "61-90": {"count": 0, "principal": Decimal("0"), "total": Decimal("0")},
            "91-180": {"count": 0, "principal": Decimal("0"), "total": Decimal("0")},
            "181-365": {"count": 0, "principal": Decimal("0"), "total": Decimal("0")},
            ">365": {"count": 0, "principal": Decimal("0"), "total": Decimal("0")},
        }

        for account in accounts:
            dpd = account.days_past_due
            if dpd == 0:
                bucket = "0"
            elif dpd <= 30:
                bucket = "1-30"
            elif dpd <= 60:
                bucket = "31-60"
            elif dpd <= 90:
                bucket = "61-90"
            elif dpd <= 180:
                bucket = "91-180"
            elif dpd <= 365:
                bucket = "181-365"
            else:
                bucket = ">365"

            buckets[bucket]["count"] += 1
            buckets[bucket]["principal"] += account.principal_outstanding
            buckets[bucket]["total"] += account.total_outstanding

        return [
            {
                "bucket": k,
                "count": v["count"],
                "principal_outstanding": v["principal"],
                "total_outstanding": v["total"],
            }
            for k, v in buckets.items()
        ]
