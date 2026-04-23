"""Collateral/Security Management Service."""

import logging
from datetime import datetime, date
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy import select, and_, or_, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lending import (
    LoanSanction,
    LoanSecurity,
    SecurityCategory,
    SecurityType,
    ChargeType,
    SecurityStatus,
)
from app.models.lending.loan_account import LoanAccount

logger = logging.getLogger(__name__)


class CollateralService:
    """Service for managing loan collaterals/securities."""

    def __init__(self, db: AsyncSession):
        """Initialize collateral service."""
        self.db = db

    async def create_security(
        self,
        sanction_id: UUID,
        security_category: str,
        security_type: str,
        description: str,
        acceptable_value: Decimal,
        margin_percentage: Decimal = Decimal("25"),
        charge_type: str = "FIRST",
        property_details: Optional[Dict[str, Any]] = None,
        owner_details: Optional[Dict[str, Any]] = None,
        valuation_details: Optional[Dict[str, Any]] = None,
        user_id: Optional[UUID] = None,
    ) -> LoanSecurity:
        """
        Create a new security/collateral for a sanction.

        Args:
            sanction_id: Parent sanction ID
            security_category: PRIMARY, COLLATERAL, GUARANTEE
            security_type: IMMOVABLE_PROPERTY, MOVABLE_ASSET, etc.
            description: Security description
            acceptable_value: Value acceptable for coverage
            margin_percentage: Margin/haircut percentage
            charge_type: FIRST, SECOND, PARI_PASSU
            property_details: Property-specific details
            owner_details: Owner information
            valuation_details: Valuation information
            user_id: User creating the security

        Returns:
            Created LoanSecurity object
        """
        # Get next security number
        result = await self.db.execute(
            select(func.coalesce(func.max(LoanSecurity.security_number), 0))
            .where(LoanSecurity.sanction_id == sanction_id)
        )
        next_number = result.scalar() + 1

        # Calculate net value
        net_value = (acceptable_value * (Decimal("100") - margin_percentage) / Decimal("100")).quantize(
            Decimal("0.01"), ROUND_HALF_UP
        )

        security = LoanSecurity(
            sanction_id=sanction_id,
            security_number=next_number,
            security_category=SecurityCategory[security_category],
            security_type=SecurityType[security_type],
            charge_type=ChargeType[charge_type],
            description=description,
            acceptable_value=acceptable_value,
            margin_percentage=margin_percentage,
            net_value=net_value,
            created_by=user_id,
        )

        # Add property details if provided
        if property_details:
            security.property_address = property_details.get("address")
            security.property_area_sqft = property_details.get("area_sqft")
            security.survey_number = property_details.get("survey_number")
            security.property_type = property_details.get("type")
            security.detailed_description = property_details.get("detailed_description")

        # Add owner details if provided
        if owner_details:
            security.owner_name = owner_details.get("name")
            security.owner_relationship = owner_details.get("relationship")
            security.is_third_party = owner_details.get("is_third_party", False)
            security.third_party_entity_id = owner_details.get("entity_id")

        # Add valuation details if provided
        if valuation_details:
            security.declared_value = valuation_details.get("declared_value")
            security.market_value = valuation_details.get("market_value")
            security.forced_sale_value = valuation_details.get("forced_sale_value")
            security.valuation_date = valuation_details.get("valuation_date")
            security.valuer_name = valuation_details.get("valuer_name")
            security.valuer_firm = valuation_details.get("valuer_firm")
            security.valuation_report_path = valuation_details.get("report_path")

        self.db.add(security)
        await self.db.commit()
        await self.db.refresh(security)

        return security

    async def update_valuation(
        self,
        security_id: UUID,
        market_value: Decimal,
        forced_sale_value: Optional[Decimal] = None,
        acceptable_value: Optional[Decimal] = None,
        valuation_date: Optional[date] = None,
        valuer_name: Optional[str] = None,
        valuer_firm: Optional[str] = None,
        report_path: Optional[str] = None,
        next_valuation_date: Optional[date] = None,
        user_id: Optional[UUID] = None,
    ) -> LoanSecurity:
        """
        Update security valuation.

        Args:
            security_id: Security ID
            market_value: New market value
            forced_sale_value: Forced sale value
            acceptable_value: New acceptable value (if different from market)
            valuation_date: Date of valuation
            valuer_name: Valuer name
            valuer_firm: Valuation firm
            report_path: Path to valuation report
            next_valuation_date: Next valuation due date
            user_id: User performing update

        Returns:
            Updated LoanSecurity
        """
        result = await self.db.execute(
            select(LoanSecurity).where(LoanSecurity.id == security_id)
        )
        security = result.scalar_one_or_none()
        if not security:
            raise ValueError(f"Security {security_id} not found")

        # Update valuation
        security.market_value = market_value
        if forced_sale_value:
            security.forced_sale_value = forced_sale_value
        if acceptable_value:
            security.acceptable_value = acceptable_value
            # Recalculate net value
            security.net_value = (
                acceptable_value * (Decimal("100") - security.margin_percentage) / Decimal("100")
            ).quantize(Decimal("0.01"), ROUND_HALF_UP)

        security.valuation_date = valuation_date or date.today()
        security.valuer_name = valuer_name
        security.valuer_firm = valuer_firm
        if report_path:
            security.valuation_report_path = report_path
        if next_valuation_date:
            security.next_valuation_date = next_valuation_date

        security.updated_by = user_id

        await self.db.commit()
        await self.db.refresh(security)

        return security

    async def release_security(
        self,
        security_id: UUID,
        release_reason: str,
        release_date: Optional[date] = None,
        release_to: Optional[str] = None,
        user_id: Optional[UUID] = None,
    ) -> LoanSecurity:
        """
        Release a security/collateral.

        Args:
            security_id: Security ID
            release_reason: Reason for release
            release_date: Release date
            release_to: Released to whom
            user_id: User performing release

        Returns:
            Updated LoanSecurity
        """
        result = await self.db.execute(
            select(LoanSecurity).where(LoanSecurity.id == security_id)
        )
        security = result.scalar_one_or_none()
        if not security:
            raise ValueError(f"Security {security_id} not found")

        # Check if loan is closed or security can be released
        sanction_result = await self.db.execute(
            select(LoanSanction).where(LoanSanction.id == security.sanction_id)
        )
        sanction = sanction_result.scalar_one_or_none()

        # Check if there's an active loan account
        if sanction:
            loan_result = await self.db.execute(
                select(LoanAccount).where(
                    LoanAccount.sanction_id == sanction.id,
                    LoanAccount.status.not_in(["CLOSED", "WRITTEN_OFF"]),
                )
            )
            active_loan = loan_result.scalar_one_or_none()
            if active_loan:
                # Verify outstanding is zero or release is approved
                if active_loan.total_outstanding > Decimal("0"):
                    logger.warning(
                        f"Releasing security {security_id} while loan {active_loan.id} "
                        f"has outstanding {active_loan.total_outstanding}"
                    )

        # Update security status
        security.status = SecurityStatus.RELEASED
        security.release_date = release_date or date.today()
        security.release_reason = release_reason
        security.released_to = release_to
        security.updated_by = user_id

        await self.db.commit()
        await self.db.refresh(security)

        return security

    async def substitute_security(
        self,
        old_security_id: UUID,
        new_security_data: Dict[str, Any],
        substitution_reason: str,
        user_id: Optional[UUID] = None,
    ) -> Dict[str, LoanSecurity]:
        """
        Substitute one security with another.

        Args:
            old_security_id: ID of security to replace
            new_security_data: Data for new security
            substitution_reason: Reason for substitution
            user_id: User performing substitution

        Returns:
            Dictionary with old and new security objects
        """
        # Get old security
        result = await self.db.execute(
            select(LoanSecurity).where(LoanSecurity.id == old_security_id)
        )
        old_security = result.scalar_one_or_none()
        if not old_security:
            raise ValueError(f"Security {old_security_id} not found")

        # Create new security
        new_security = await self.create_security(
            sanction_id=old_security.sanction_id,
            security_category=new_security_data.get("category", old_security.security_category.name),
            security_type=new_security_data.get("type", old_security.security_type.name),
            description=new_security_data["description"],
            acceptable_value=new_security_data["acceptable_value"],
            margin_percentage=new_security_data.get("margin_percentage", old_security.margin_percentage),
            charge_type=new_security_data.get("charge_type", old_security.charge_type.name),
            property_details=new_security_data.get("property_details"),
            owner_details=new_security_data.get("owner_details"),
            valuation_details=new_security_data.get("valuation_details"),
            user_id=user_id,
        )

        # Link substitution
        new_security.substitutes_security_id = old_security_id
        new_security.substitution_reason = substitution_reason

        # Release old security
        old_security.status = SecurityStatus.SUBSTITUTED
        old_security.substituted_by_id = new_security.id
        old_security.release_date = date.today()
        old_security.release_reason = f"Substituted: {substitution_reason}"
        old_security.updated_by = user_id

        await self.db.commit()
        await self.db.refresh(old_security)
        await self.db.refresh(new_security)

        return {
            "old_security": old_security,
            "new_security": new_security,
        }

    async def get_security_coverage(
        self,
        sanction_id: UUID,
        include_released: bool = False,
    ) -> Dict[str, Any]:
        """
        Calculate security coverage for a sanction.

        Args:
            sanction_id: Sanction ID
            include_released: Include released securities

        Returns:
            Coverage calculation details
        """
        conditions = [LoanSecurity.sanction_id == sanction_id]
        if not include_released:
            conditions.append(
                LoanSecurity.status.in_([SecurityStatus.ACTIVE, SecurityStatus.PENDING])
            )

        result = await self.db.execute(
            select(LoanSecurity).where(and_(*conditions))
        )
        securities = list(result.scalars().all())

        # Get sanction amount
        sanction_result = await self.db.execute(
            select(LoanSanction).where(LoanSanction.id == sanction_id)
        )
        sanction = sanction_result.scalar_one_or_none()

        if not sanction:
            raise ValueError(f"Sanction {sanction_id} not found")

        # Calculate totals by category
        totals = {
            "PRIMARY": {"count": 0, "acceptable_value": Decimal("0"), "net_value": Decimal("0")},
            "COLLATERAL": {"count": 0, "acceptable_value": Decimal("0"), "net_value": Decimal("0")},
            "GUARANTEE": {"count": 0, "acceptable_value": Decimal("0"), "net_value": Decimal("0")},
        }

        for security in securities:
            category = security.security_category.name
            if category in totals:
                totals[category]["count"] += 1
                totals[category]["acceptable_value"] += security.acceptable_value
                totals[category]["net_value"] += security.net_value

        total_acceptable = sum(t["acceptable_value"] for t in totals.values())
        total_net = sum(t["net_value"] for t in totals.values())

        # Calculate coverage ratio
        loan_amount = sanction.sanctioned_amount
        coverage_ratio = (
            (total_net / loan_amount * Decimal("100")).quantize(Decimal("0.01"), ROUND_HALF_UP)
            if loan_amount > 0 else Decimal("0")
        )

        return {
            "sanction_id": sanction_id,
            "loan_amount": loan_amount,
            "securities": [
                {
                    "id": str(s.id),
                    "category": s.security_category.name,
                    "type": s.security_type.name,
                    "description": s.description,
                    "acceptable_value": s.acceptable_value,
                    "margin": s.margin_percentage,
                    "net_value": s.net_value,
                    "status": s.status.name if hasattr(s, 'status') and s.status else "ACTIVE",
                }
                for s in securities
            ],
            "category_totals": totals,
            "total_acceptable_value": total_acceptable,
            "total_net_value": total_net,
            "coverage_ratio": coverage_ratio,
            "is_fully_secured": coverage_ratio >= Decimal("100"),
        }

    async def get_securities_due_for_valuation(
        self,
        organization_id: UUID,
        as_of_date: Optional[date] = None,
        days_ahead: int = 30,
    ) -> List[Dict[str, Any]]:
        """
        Get securities due for revaluation.

        Args:
            organization_id: Organization ID
            as_of_date: Reference date
            days_ahead: Days to look ahead

        Returns:
            List of securities due for valuation
        """
        if as_of_date is None:
            as_of_date = date.today()

        from datetime import timedelta
        due_date_threshold = as_of_date + timedelta(days=days_ahead)

        # Join with sanction to filter by organization
        result = await self.db.execute(
            select(LoanSecurity)
            .join(LoanSanction, LoanSecurity.sanction_id == LoanSanction.id)
            .where(
                LoanSanction.organization_id == organization_id,
                LoanSecurity.next_valuation_date <= due_date_threshold,
                LoanSecurity.status == SecurityStatus.ACTIVE,
            )
            .order_by(LoanSecurity.next_valuation_date)
        )
        securities = list(result.scalars().all())

        return [
            {
                "security_id": str(s.id),
                "sanction_id": str(s.sanction_id),
                "security_type": s.security_type.name,
                "description": s.description,
                "last_valuation_date": s.valuation_date,
                "next_valuation_date": s.next_valuation_date,
                "current_market_value": s.market_value,
                "acceptable_value": s.acceptable_value,
                "days_until_due": (s.next_valuation_date - as_of_date).days if s.next_valuation_date else None,
            }
            for s in securities
        ]

    async def get_securities_by_loan(
        self,
        loan_account_id: UUID,
    ) -> List[LoanSecurity]:
        """
        Get all securities for a loan account.

        Args:
            loan_account_id: Loan account ID

        Returns:
            List of securities
        """
        # Get sanction ID from loan account
        result = await self.db.execute(
            select(LoanAccount).where(LoanAccount.id == loan_account_id)
        )
        loan = result.scalar_one_or_none()
        if not loan:
            raise ValueError(f"Loan account {loan_account_id} not found")

        security_result = await self.db.execute(
            select(LoanSecurity)
            .where(
                LoanSecurity.sanction_id == loan.sanction_id,
                LoanSecurity.status == SecurityStatus.ACTIVE,
            )
            .order_by(LoanSecurity.security_category, LoanSecurity.security_number)
        )
        return list(security_result.scalars().all())

    async def add_encumbrance(
        self,
        security_id: UUID,
        charge_holder: str,
        charge_amount: Decimal,
        charge_date: Optional[date] = None,
        charge_reference: Optional[str] = None,
        user_id: Optional[UUID] = None,
    ) -> LoanSecurity:
        """
        Add existing encumbrance information to security.

        Args:
            security_id: Security ID
            charge_holder: Existing charge holder name
            charge_amount: Existing charge amount
            charge_date: Date of existing charge
            charge_reference: Reference number of existing charge
            user_id: User adding encumbrance

        Returns:
            Updated LoanSecurity
        """
        result = await self.db.execute(
            select(LoanSecurity).where(LoanSecurity.id == security_id)
        )
        security = result.scalar_one_or_none()
        if not security:
            raise ValueError(f"Security {security_id} not found")

        security.has_existing_charge = True
        security.existing_charge_holder = charge_holder
        security.existing_charge_amount = charge_amount
        security.existing_charge_date = charge_date
        security.existing_charge_reference = charge_reference
        security.updated_by = user_id

        await self.db.commit()
        await self.db.refresh(security)

        return security

    async def record_charge_creation(
        self,
        security_id: UUID,
        charge_creation_date: date,
        charge_id: Optional[str] = None,
        roc_filing_date: Optional[date] = None,
        roc_filing_srn: Optional[str] = None,
        cersai_registration_date: Optional[date] = None,
        cersai_transaction_id: Optional[str] = None,
        user_id: Optional[UUID] = None,
    ) -> LoanSecurity:
        """
        Record charge creation/registration details.

        Args:
            security_id: Security ID
            charge_creation_date: Date of charge creation
            charge_id: Charge ID from registry
            roc_filing_date: ROC filing date
            roc_filing_srn: ROC filing SRN
            cersai_registration_date: CERSAI registration date
            cersai_transaction_id: CERSAI transaction ID
            user_id: User recording charge

        Returns:
            Updated LoanSecurity
        """
        result = await self.db.execute(
            select(LoanSecurity).where(LoanSecurity.id == security_id)
        )
        security = result.scalar_one_or_none()
        if not security:
            raise ValueError(f"Security {security_id} not found")

        security.charge_created = True
        security.charge_creation_date = charge_creation_date
        security.charge_id = charge_id
        security.roc_filing_date = roc_filing_date
        security.roc_filing_srn = roc_filing_srn
        security.cersai_registration_date = cersai_registration_date
        security.cersai_transaction_id = cersai_transaction_id
        security.status = SecurityStatus.ACTIVE
        security.updated_by = user_id

        await self.db.commit()
        await self.db.refresh(security)

        return security

    async def get_collateral_summary(
        self,
        organization_id: UUID,
        as_of_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Get collateral summary for organization.

        Args:
            organization_id: Organization ID
            as_of_date: Reference date

        Returns:
            Summary statistics
        """
        if as_of_date is None:
            as_of_date = date.today()

        # Get all active securities for organization
        result = await self.db.execute(
            select(LoanSecurity)
            .join(LoanSanction, LoanSecurity.sanction_id == LoanSanction.id)
            .where(
                LoanSanction.organization_id == organization_id,
                LoanSecurity.status == SecurityStatus.ACTIVE,
            )
        )
        securities = list(result.scalars().all())

        # Calculate summaries by type
        by_type = {}
        by_category = {}
        total_acceptable = Decimal("0")
        total_net = Decimal("0")

        for security in securities:
            type_name = security.security_type.name
            category_name = security.security_category.name

            if type_name not in by_type:
                by_type[type_name] = {"count": 0, "acceptable_value": Decimal("0"), "net_value": Decimal("0")}
            by_type[type_name]["count"] += 1
            by_type[type_name]["acceptable_value"] += security.acceptable_value
            by_type[type_name]["net_value"] += security.net_value

            if category_name not in by_category:
                by_category[category_name] = {"count": 0, "acceptable_value": Decimal("0"), "net_value": Decimal("0")}
            by_category[category_name]["count"] += 1
            by_category[category_name]["acceptable_value"] += security.acceptable_value
            by_category[category_name]["net_value"] += security.net_value

            total_acceptable += security.acceptable_value
            total_net += security.net_value

        # Securities pending valuation
        pending_valuation = [
            s for s in securities
            if s.next_valuation_date and s.next_valuation_date <= as_of_date
        ]

        return {
            "total_securities": len(securities),
            "total_acceptable_value": total_acceptable,
            "total_net_value": total_net,
            "by_type": by_type,
            "by_category": by_category,
            "pending_valuation_count": len(pending_valuation),
            "as_of_date": as_of_date,
        }
