"""ESS IT Declaration Service (Indian Income Tax)."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.ess.it_declaration import (
    ITDeclarationMaster,
    ITDeclaration,
    ITDeclarationItem,
    HRAReceipt,
    AttendanceRegularization,
)
from app.models.ess.enums import ITDeclarationStatus, RegularizationStatus


class ESSITDeclarationService:
    """Service for ESS IT Declaration management."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ==================== Section Masters ====================

    async def get_declaration_sections(
        self,
        organization_id: UUID,
        tax_regime: str = "OLD",
        active_only: bool = True,
    ) -> List[ITDeclarationMaster]:
        """Get IT declaration sections applicable for a regime."""
        query = select(ITDeclarationMaster).where(
            ITDeclarationMaster.organization_id == organization_id
        )

        if tax_regime == "OLD":
            query = query.where(ITDeclarationMaster.applicable_in_old_regime == True)
        else:
            query = query.where(ITDeclarationMaster.applicable_in_new_regime == True)

        if active_only:
            query = query.where(ITDeclarationMaster.is_active == True)

        query = query.order_by(ITDeclarationMaster.display_order)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_section_by_code(
        self,
        organization_id: UUID,
        section_code: str,
    ) -> Optional[ITDeclarationMaster]:
        """Get section by code."""
        query = select(ITDeclarationMaster).where(
            and_(
                ITDeclarationMaster.organization_id == organization_id,
                ITDeclarationMaster.section_code == section_code,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    # ==================== Declaration Management ====================

    async def get_or_create_declaration(
        self,
        organization_id: UUID,
        ess_user_id: UUID,
        employee_id: UUID,
        financial_year: str,
        tax_regime: str = "OLD",
    ) -> ITDeclaration:
        """Get existing or create new declaration for the financial year."""
        # Check for existing declaration
        query = select(ITDeclaration).where(
            and_(
                ITDeclaration.organization_id == organization_id,
                ITDeclaration.employee_id == employee_id,
                ITDeclaration.financial_year == financial_year,
                ITDeclaration.is_latest == True,
            )
        ).options(
            selectinload(ITDeclaration.items),
            selectinload(ITDeclaration.hra_receipts),
        )
        result = await self.session.execute(query)
        existing = result.scalar_one_or_none()

        if existing:
            return existing

        # Create new declaration
        declaration = ITDeclaration(
            organization_id=organization_id,
            ess_user_id=ess_user_id,
            employee_id=employee_id,
            financial_year=financial_year,
            tax_regime=tax_regime,
            total_declared_amount=Decimal("0"),
            total_verified_amount=Decimal("0"),
            total_approved_amount=Decimal("0"),
            status=ITDeclarationStatus.DRAFT,
            version=1,
            is_latest=True,
        )
        self.session.add(declaration)
        await self.session.flush()
        return declaration

    async def get_declaration_by_id(
        self,
        declaration_id: UUID,
    ) -> Optional[ITDeclaration]:
        """Get declaration by ID with items."""
        query = select(ITDeclaration).where(
            ITDeclaration.id == declaration_id
        ).options(
            selectinload(ITDeclaration.items),
            selectinload(ITDeclaration.hra_receipts),
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_declarations_by_employee(
        self,
        employee_id: UUID,
        limit: int = 5,
    ) -> List[ITDeclaration]:
        """Get all declarations for an employee."""
        query = select(ITDeclaration).where(
            and_(
                ITDeclaration.employee_id == employee_id,
                ITDeclaration.is_latest == True,
            )
        ).order_by(ITDeclaration.financial_year.desc()).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_tax_regime(
        self,
        declaration_id: UUID,
        tax_regime: str,
    ) -> Optional[ITDeclaration]:
        """Update tax regime for a declaration."""
        declaration = await self.get_declaration_by_id(declaration_id)
        if not declaration:
            return None

        if declaration.status not in [ITDeclarationStatus.DRAFT]:
            raise ValueError("Cannot change regime after submission")

        declaration.tax_regime = tax_regime
        await self.session.flush()
        return declaration

    # ==================== Declaration Items ====================

    async def add_declaration_item(
        self,
        declaration_id: UUID,
        section_code: str,
        particular: str,
        declared_amount: Decimal,
        description: Optional[str] = None,
        investment_date: Optional[date] = None,
        policy_number: Optional[str] = None,
        institution_name: Optional[str] = None,
        proof_url: Optional[str] = None,
        proof_type: Optional[str] = None,
    ) -> ITDeclarationItem:
        """Add a declaration item."""
        declaration = await self.get_declaration_by_id(declaration_id)
        if not declaration:
            raise ValueError("Declaration not found")

        if declaration.status not in [ITDeclarationStatus.DRAFT, ITDeclarationStatus.PROOF_PENDING]:
            raise ValueError("Cannot modify submitted declaration")

        # Get section for validation
        section = await self.get_section_by_code(
            declaration.organization_id, section_code
        )

        # Check section limit
        if section:
            existing_for_section = sum(
                item.declared_amount
                for item in declaration.items
                if item.section_code == section_code
            )
            if existing_for_section + declared_amount > section.max_limit:
                raise ValueError(
                    f"Amount exceeds section limit of {section.max_limit}"
                )

        item = ITDeclarationItem(
            declaration_id=declaration_id,
            section_id=section.id if section else None,
            section_code=section_code,
            particular=particular,
            description=description,
            declared_amount=declared_amount,
            investment_date=investment_date,
            policy_number=policy_number,
            institution_name=institution_name,
            proof_submitted=proof_url is not None,
            proof_url=proof_url,
            proof_type=proof_type,
        )
        self.session.add(item)

        # Update total
        declaration.total_declared_amount += declared_amount

        await self.session.flush()
        return item

    async def update_declaration_item(
        self,
        item_id: UUID,
        **kwargs
    ) -> Optional[ITDeclarationItem]:
        """Update a declaration item."""
        query = select(ITDeclarationItem).where(
            ITDeclarationItem.id == item_id
        )
        result = await self.session.execute(query)
        item = result.scalar_one_or_none()

        if not item:
            return None

        # Get declaration to check status
        declaration = await self.get_declaration_by_id(item.declaration_id)
        if declaration.status not in [ITDeclarationStatus.DRAFT, ITDeclarationStatus.PROOF_PENDING]:
            raise ValueError("Cannot modify submitted declaration")

        old_amount = item.declared_amount
        new_amount = kwargs.get('declared_amount', old_amount)

        for key, value in kwargs.items():
            if hasattr(item, key) and key not in ['id', 'declaration_id']:
                setattr(item, key, value)

        # Update proof status
        if kwargs.get('proof_url'):
            item.proof_submitted = True

        # Update declaration total if amount changed
        if new_amount != old_amount:
            declaration.total_declared_amount = (
                declaration.total_declared_amount - old_amount + new_amount
            )

        await self.session.flush()
        return item

    async def delete_declaration_item(
        self,
        item_id: UUID,
    ) -> bool:
        """Delete a declaration item."""
        query = select(ITDeclarationItem).where(
            ITDeclarationItem.id == item_id
        )
        result = await self.session.execute(query)
        item = result.scalar_one_or_none()

        if not item:
            return False

        # Get declaration
        declaration = await self.get_declaration_by_id(item.declaration_id)
        if declaration.status not in [ITDeclarationStatus.DRAFT]:
            raise ValueError("Cannot delete from submitted declaration")

        # Update total
        declaration.total_declared_amount -= item.declared_amount

        await self.session.delete(item)
        await self.session.flush()
        return True

    # ==================== HRA ====================

    async def update_hra_details(
        self,
        declaration_id: UUID,
        rent_paid_monthly: Decimal,
        landlord_name: str,
        landlord_pan: Optional[str] = None,
        landlord_address: Optional[str] = None,
        metro_city: bool = False,
    ) -> ITDeclaration:
        """Update HRA details in declaration."""
        declaration = await self.get_declaration_by_id(declaration_id)
        if not declaration:
            raise ValueError("Declaration not found")

        if declaration.status not in [ITDeclarationStatus.DRAFT, ITDeclarationStatus.PROOF_PENDING]:
            raise ValueError("Cannot modify submitted declaration")

        declaration.rent_paid_monthly = rent_paid_monthly
        declaration.landlord_name = landlord_name
        declaration.landlord_pan = landlord_pan
        declaration.landlord_address = landlord_address
        declaration.metro_city = metro_city

        # Calculate annual HRA
        declaration.hra_declared = rent_paid_monthly * 12

        await self.session.flush()
        return declaration

    async def add_hra_receipt(
        self,
        declaration_id: UUID,
        month: str,
        rent_amount: Decimal,
        receipt_number: Optional[str] = None,
        receipt_url: Optional[str] = None,
    ) -> HRAReceipt:
        """Add monthly HRA receipt."""
        receipt = HRAReceipt(
            declaration_id=declaration_id,
            month=month,
            rent_amount=rent_amount,
            receipt_number=receipt_number,
            receipt_url=receipt_url,
            receipt_uploaded=receipt_url is not None,
        )
        self.session.add(receipt)
        await self.session.flush()
        return receipt

    # ==================== Home Loan ====================

    async def update_home_loan_details(
        self,
        declaration_id: UUID,
        home_loan_interest: Decimal,
        home_loan_principal: Optional[Decimal] = None,
        loan_sanctioned_date: Optional[date] = None,
        lender_name: Optional[str] = None,
        lender_pan: Optional[str] = None,
        property_type: str = "SELF_OCCUPIED",
    ) -> ITDeclaration:
        """Update home loan details in declaration."""
        declaration = await self.get_declaration_by_id(declaration_id)
        if not declaration:
            raise ValueError("Declaration not found")

        if declaration.status not in [ITDeclarationStatus.DRAFT, ITDeclarationStatus.PROOF_PENDING]:
            raise ValueError("Cannot modify submitted declaration")

        declaration.home_loan_interest = home_loan_interest
        declaration.home_loan_principal = home_loan_principal
        declaration.loan_sanctioned_date = loan_sanctioned_date
        declaration.lender_name = lender_name
        declaration.lender_pan = lender_pan
        declaration.property_type = property_type

        await self.session.flush()
        return declaration

    # ==================== Submission & Approval ====================

    async def submit_declaration(
        self,
        declaration_id: UUID,
    ) -> ITDeclaration:
        """Submit declaration for verification."""
        declaration = await self.get_declaration_by_id(declaration_id)
        if not declaration:
            raise ValueError("Declaration not found")

        if declaration.status != ITDeclarationStatus.DRAFT:
            raise ValueError("Only draft declarations can be submitted")

        declaration.status = ITDeclarationStatus.SUBMITTED
        declaration.submitted_date = datetime.utcnow()

        await self.session.flush()
        return declaration

    async def submit_proofs(
        self,
        declaration_id: UUID,
    ) -> ITDeclaration:
        """Mark proofs as submitted."""
        declaration = await self.get_declaration_by_id(declaration_id)
        if not declaration:
            raise ValueError("Declaration not found")

        if declaration.status != ITDeclarationStatus.PROOF_PENDING:
            raise ValueError("Declaration not in proof pending status")

        # Check if all required proofs are uploaded
        items_without_proof = [
            item for item in declaration.items
            if not item.proof_submitted
        ]
        if items_without_proof:
            raise ValueError(f"{len(items_without_proof)} items still missing proofs")

        declaration.status = ITDeclarationStatus.PROOF_SUBMITTED
        declaration.proof_submitted_date = datetime.utcnow()

        await self.session.flush()
        return declaration

    async def verify_declaration(
        self,
        declaration_id: UUID,
        verifier_id: UUID,
        verified_amounts: dict,  # {item_id: verified_amount}
        remarks: Optional[str] = None,
    ) -> ITDeclaration:
        """Verify declaration and set verified amounts."""
        declaration = await self.get_declaration_by_id(declaration_id)
        if not declaration:
            raise ValueError("Declaration not found")

        if declaration.status not in [ITDeclarationStatus.SUBMITTED, ITDeclarationStatus.PROOF_SUBMITTED]:
            raise ValueError("Declaration not ready for verification")

        total_verified = Decimal("0")

        # Update each item
        for item in declaration.items:
            if str(item.id) in verified_amounts:
                item.verified_amount = Decimal(str(verified_amounts[str(item.id)]))
                item.is_verified = True
                total_verified += item.verified_amount
            else:
                # Default to declared if not in verified_amounts
                item.verified_amount = item.declared_amount
                item.is_verified = True
                total_verified += item.declared_amount

        declaration.total_verified_amount = total_verified
        declaration.status = ITDeclarationStatus.VERIFIED
        declaration.verified_by = verifier_id
        declaration.verified_date = datetime.utcnow()
        declaration.verification_remarks = remarks

        await self.session.flush()
        return declaration

    async def approve_declaration(
        self,
        declaration_id: UUID,
        approver_id: UUID,
        approved_amounts: Optional[dict] = None,
        remarks: Optional[str] = None,
    ) -> ITDeclaration:
        """Final approval of declaration."""
        declaration = await self.get_declaration_by_id(declaration_id)
        if not declaration:
            raise ValueError("Declaration not found")

        if declaration.status != ITDeclarationStatus.VERIFIED:
            raise ValueError("Declaration must be verified before approval")

        total_approved = Decimal("0")

        # Update each item
        for item in declaration.items:
            if approved_amounts and str(item.id) in approved_amounts:
                item.approved_amount = Decimal(str(approved_amounts[str(item.id)]))
            else:
                # Default to verified amount
                item.approved_amount = item.verified_amount
            total_approved += item.approved_amount

        declaration.total_approved_amount = total_approved
        declaration.status = ITDeclarationStatus.APPROVED

        await self.session.flush()
        return declaration

    async def request_proof_resubmission(
        self,
        declaration_id: UUID,
        item_ids: List[UUID],
        remarks: str,
    ) -> ITDeclaration:
        """Request proof resubmission for specific items."""
        declaration = await self.get_declaration_by_id(declaration_id)
        if not declaration:
            raise ValueError("Declaration not found")

        # Mark items for resubmission
        for item in declaration.items:
            if item.id in item_ids:
                item.is_verified = False
                item.verification_remarks = remarks

        declaration.status = ITDeclarationStatus.PROOF_PENDING

        await self.session.flush()
        return declaration

    # ==================== Tax Calculation ====================

    async def calculate_tax_liability(
        self,
        declaration_id: UUID,
        gross_salary: Decimal,
        other_income: Decimal = Decimal("0"),
    ) -> dict:
        """Calculate estimated tax liability."""
        declaration = await self.get_declaration_by_id(declaration_id)
        if not declaration:
            raise ValueError("Declaration not found")

        # Get applicable deductions based on regime
        if declaration.tax_regime == "OLD":
            total_deductions = declaration.total_declared_amount
            # Add HRA if declared
            if declaration.hra_declared:
                total_deductions += declaration.hra_declared
            # Add home loan interest (Section 24b)
            if declaration.home_loan_interest:
                # Max 2 lakh for self-occupied
                max_interest = Decimal("200000") if declaration.property_type == "SELF_OCCUPIED" else declaration.home_loan_interest
                total_deductions += min(declaration.home_loan_interest, max_interest)

            # Standard deduction (Rs. 50,000)
            standard_deduction = Decimal("50000")
            total_deductions += standard_deduction

            taxable_income = gross_salary + other_income - total_deductions
        else:
            # New regime - only standard deduction
            standard_deduction = Decimal("75000")  # Updated for FY 2024-25
            taxable_income = gross_salary + other_income - standard_deduction
            total_deductions = standard_deduction

        # Calculate tax based on slab
        tax = self._calculate_tax_by_slab(taxable_income, declaration.tax_regime)

        # Add surcharge and cess
        surcharge = self._calculate_surcharge(taxable_income, tax)
        cess = (tax + surcharge) * Decimal("0.04")  # 4% cess

        total_tax = tax + surcharge + cess

        # Monthly TDS
        remaining_months = 12 - (datetime.now().month if datetime.now().month >= 4 else datetime.now().month + 12 - 4)
        monthly_tds = total_tax / max(remaining_months, 1)

        # Update declaration
        declaration.estimated_taxable_income = taxable_income
        declaration.estimated_tax_liability = total_tax
        declaration.monthly_tds = monthly_tds
        await self.session.flush()

        return {
            "gross_salary": float(gross_salary),
            "other_income": float(other_income),
            "total_deductions": float(total_deductions),
            "taxable_income": float(max(taxable_income, Decimal("0"))),
            "tax_on_income": float(tax),
            "surcharge": float(surcharge),
            "cess": float(cess),
            "total_tax": float(total_tax),
            "monthly_tds": float(monthly_tds),
            "tax_regime": declaration.tax_regime,
        }

    def _calculate_tax_by_slab(self, taxable_income: Decimal, regime: str) -> Decimal:
        """Calculate tax based on income slabs."""
        if taxable_income <= 0:
            return Decimal("0")

        if regime == "NEW":
            # New regime slabs (FY 2024-25)
            slabs = [
                (300000, Decimal("0")),
                (700000, Decimal("0.05")),
                (1000000, Decimal("0.10")),
                (1200000, Decimal("0.15")),
                (1500000, Decimal("0.20")),
                (float("inf"), Decimal("0.30")),
            ]
        else:
            # Old regime slabs
            slabs = [
                (250000, Decimal("0")),
                (500000, Decimal("0.05")),
                (1000000, Decimal("0.20")),
                (float("inf"), Decimal("0.30")),
            ]

        tax = Decimal("0")
        prev_limit = Decimal("0")

        for limit, rate in slabs:
            if taxable_income <= prev_limit:
                break
            taxable_in_slab = min(taxable_income, Decimal(str(limit))) - prev_limit
            tax += taxable_in_slab * rate
            prev_limit = Decimal(str(limit))

        # Rebate u/s 87A (if applicable)
        if regime == "NEW" and taxable_income <= 700000:
            tax = max(tax - Decimal("25000"), Decimal("0"))
        elif regime == "OLD" and taxable_income <= 500000:
            tax = max(tax - Decimal("12500"), Decimal("0"))

        return tax

    def _calculate_surcharge(self, taxable_income: Decimal, tax: Decimal) -> Decimal:
        """Calculate surcharge based on income."""
        if taxable_income <= 5000000:
            return Decimal("0")
        elif taxable_income <= 10000000:
            return tax * Decimal("0.10")
        elif taxable_income <= 20000000:
            return tax * Decimal("0.15")
        elif taxable_income <= 50000000:
            return tax * Decimal("0.25")
        else:
            return tax * Decimal("0.37")

    # ==================== Attendance Regularization ====================

    async def generate_regularization_number(self, organization_id: UUID) -> str:
        """Generate unique regularization request number."""
        today = date.today()
        prefix = f"REG{today.strftime('%Y%m')}"

        query = select(func.count()).select_from(AttendanceRegularization).where(
            and_(
                AttendanceRegularization.organization_id == organization_id,
                AttendanceRegularization.request_number.like(f"{prefix}%")
            )
        )
        result = await self.session.execute(query)
        count = result.scalar() or 0

        return f"{prefix}{count + 1:04d}"

    async def create_regularization_request(
        self,
        organization_id: UUID,
        employee_id: UUID,
        attendance_date: date,
        regularization_type: str,
        reason: str,
        requested_in_time: Optional[str] = None,
        requested_out_time: Optional[str] = None,
        supporting_document: Optional[str] = None,
    ) -> AttendanceRegularization:
        """Create attendance regularization request."""
        request_number = await self.generate_regularization_number(organization_id)

        request = AttendanceRegularization(
            organization_id=organization_id,
            employee_id=employee_id,
            request_number=request_number,
            attendance_date=attendance_date,
            regularization_type=regularization_type,
            requested_in_time=requested_in_time,
            requested_out_time=requested_out_time,
            reason=reason,
            supporting_document=supporting_document,
            status=RegularizationStatus.PENDING.value,
        )
        self.session.add(request)
        await self.session.flush()
        return request

    async def get_regularization_requests(
        self,
        employee_id: UUID,
        status: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[AttendanceRegularization], int]:
        """Get regularization requests for an employee."""
        query = select(AttendanceRegularization).where(
            AttendanceRegularization.employee_id == employee_id
        )

        if status:
            query = query.where(AttendanceRegularization.status == status)
        if from_date:
            query = query.where(AttendanceRegularization.attendance_date >= from_date)
        if to_date:
            query = query.where(AttendanceRegularization.attendance_date <= to_date)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        # Apply pagination
        query = query.order_by(AttendanceRegularization.created_at.desc())
        query = query.offset(offset).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all()), total

    async def cancel_regularization_request(
        self,
        employee_id: UUID,
        request_id: UUID,
    ) -> bool:
        """Cancel a pending regularization request owned by an employee."""
        query = select(AttendanceRegularization).where(
            and_(
                AttendanceRegularization.id == request_id,
                AttendanceRegularization.employee_id == employee_id,
            )
        )
        result = await self.session.execute(query)
        regularization = result.scalar_one_or_none()
        if not regularization:
            return False

        if regularization.status != RegularizationStatus.PENDING.value:
            raise ValueError("Only pending regularization requests can be cancelled")

        regularization.status = RegularizationStatus.CANCELLED.value
        await self.session.flush()
        return True
