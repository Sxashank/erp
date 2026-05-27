"""NPA (Non-Performing Asset) Management Service."""

import logging
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy import select, and_, or_, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lending import (
    LoanAccount,
    LoanSchedule,
    LoanReceipt,
    NPAClassification,
    NPAProvision,
    NPAHistory,
)

logger = logging.getLogger(__name__)


# NPA Classification thresholds (in days)
NPA_THRESHOLDS = {
    "standard": 0,
    "sma_0": 1,  # 1-30 days
    "sma_1": 31,  # 31-60 days
    "sma_2": 61,  # 61-90 days
    "substandard": 91,  # 91-365 days (NPA)
    "doubtful_1": 366,  # 1-2 years
    "doubtful_2": 731,  # 2-3 years
    "doubtful_3": 1096,  # > 3 years
    "loss": 1461,  # > 4 years or identified as loss
}

# Provisioning rates by classification
PROVISION_RATES = {
    "standard": Decimal("0.40"),  # 0.4%
    "sma_0": Decimal("0.40"),
    "sma_1": Decimal("0.40"),
    "sma_2": Decimal("0.40"),
    "substandard": Decimal("15.00"),  # 15%
    "substandard_secured": Decimal("15.00"),
    "substandard_unsecured": Decimal("25.00"),
    "doubtful_1": Decimal("25.00"),  # 25%
    "doubtful_2": Decimal("40.00"),  # 40%
    "doubtful_3": Decimal("100.00"),  # 100%
    "loss": Decimal("100.00"),  # 100%
}


class NPAService:
    """Service for NPA classification, provisioning, and management."""

    def __init__(self, db: AsyncSession):
        """Initialize NPA service."""
        self.db = db

    async def get_dpd(self, loan_account_id: UUID) -> int:
        """
        Calculate Days Past Due (DPD) for a loan account.

        Returns the number of days since the oldest unpaid EMI due date.
        """
        # Get oldest unpaid schedule entry
        result = await self.db.execute(
            select(LoanSchedule)
            .where(
                LoanSchedule.loan_account_id == loan_account_id,
                LoanSchedule.is_paid == False,
                LoanSchedule.due_date < date.today(),
            )
            .order_by(LoanSchedule.due_date)
            .limit(1)
        )
        oldest_unpaid = result.scalar_one_or_none()

        if not oldest_unpaid:
            return 0

        dpd = (date.today() - oldest_unpaid.due_date).days
        return max(0, dpd)

    async def _bucket_thresholds(
        self, organization_id: UUID
    ) -> list[tuple[str, int, Optional[int]]]:
        """Return ordered (classification_lower, min_dpd, max_dpd) thresholds.

        Reads from ``mst_npa_bucket`` for the org; falls back to the
        RBI baseline (the historical NPA_THRESHOLDS map) if the master
        is empty (tenant hasn't run the seed yet).
        """
        from datetime import date as _date

        from sqlalchemy import select

        from app.models.lending.masters import NpaBucket

        today = _date.today()
        stmt = (
            select(NpaBucket)
            .where(
                NpaBucket.organization_id == organization_id,
                NpaBucket.effective_from <= today,
            )
            .order_by(NpaBucket.sort_order)
        )
        rows = list((await self.db.execute(stmt)).scalars().all())
        if not rows:
            # Fallback — never let absence of masters break NPA classification.
            return [
                ("standard", 0, 0),
                ("sma_0", 1, 30),
                ("sma_1", 31, 60),
                ("sma_2", 61, 90),
                ("substandard", 91, 365),
                ("doubtful_1", 366, 730),
                ("doubtful_2", 731, 1095),
                ("doubtful_3", 1096, 1460),
                ("loss", 1461, None),
            ]
        # filter to currently-effective only
        active = [r for r in rows if r.effective_to is None or r.effective_to >= today]
        return [(r.asset_classification.lower(), r.min_dpd, r.max_dpd) for r in active]

    async def classify_loan(
        self,
        loan_account_id: UUID,
        dpd: Optional[int] = None,
    ) -> str:
        """
        Classify loan based on DPD.

        Buckets read from ``mst_npa_bucket`` (per-org overridable); falls
        back to RBI baseline if no master rows for the tenant.

        Returns classification: standard, sma_0, sma_1, sma_2, substandard,
        doubtful_1, doubtful_2, doubtful_3, or loss.
        """
        if dpd is None:
            dpd = await self.get_dpd(loan_account_id)

        # Resolve the loan's org_id to pick the right master set
        from app.models.lending.loan_account import LoanAccount

        loan = await self.db.get(LoanAccount, loan_account_id)
        organization_id = loan.organization_id if loan is not None else None

        if organization_id is not None:
            buckets = await self._bucket_thresholds(organization_id)
            # Iterate in descending min_dpd so first match (the worst bucket)
            # wins. open-ended max=None means "and above".
            for classification, min_dpd, max_dpd in sorted(buckets, key=lambda r: -r[1]):
                if dpd >= min_dpd and (max_dpd is None or dpd <= max_dpd):
                    return classification

        # Master-less fallback
        if dpd >= NPA_THRESHOLDS["loss"]:
            return "loss"
        elif dpd >= NPA_THRESHOLDS["doubtful_3"]:
            return "doubtful_3"
        elif dpd >= NPA_THRESHOLDS["doubtful_2"]:
            return "doubtful_2"
        elif dpd >= NPA_THRESHOLDS["doubtful_1"]:
            return "doubtful_1"
        elif dpd >= NPA_THRESHOLDS["substandard"]:
            return "substandard"
        elif dpd >= NPA_THRESHOLDS["sma_2"]:
            return "sma_2"
        elif dpd >= NPA_THRESHOLDS["sma_1"]:
            return "sma_1"
        elif dpd >= NPA_THRESHOLDS["sma_0"]:
            return "sma_0"
        else:
            return "standard"

    def is_npa(self, classification: str) -> bool:
        """Check if classification qualifies as NPA."""
        return classification in ["substandard", "doubtful_1", "doubtful_2", "doubtful_3", "loss"]

    async def calculate_provision(
        self,
        loan_account_id: UUID,
        classification: Optional[str] = None,
        is_secured: bool = True,
    ) -> Dict[str, Any]:
        """
        Calculate provisioning requirement for a loan.

        Returns:
            Dictionary with provision_rate, provision_amount, outstanding_amount
        """
        # Get loan account
        result = await self.db.execute(select(LoanAccount).where(LoanAccount.id == loan_account_id))
        loan = result.scalar_one_or_none()
        if not loan:
            raise ValueError(f"Loan account {loan_account_id} not found")

        if classification is None:
            classification = await self.classify_loan(loan_account_id)

        # Determine provision rate
        if classification == "substandard":
            provision_rate = (
                PROVISION_RATES["substandard_secured"]
                if is_secured
                else PROVISION_RATES["substandard_unsecured"]
            )
        else:
            provision_rate = PROVISION_RATES.get(classification, Decimal("0.40"))

        # Calculate provision amount
        outstanding = loan.principal_outstanding + loan.interest_outstanding
        provision_amount = (outstanding * provision_rate) / Decimal("100")

        return {
            "classification": classification,
            "provision_rate": provision_rate,
            "provision_amount": provision_amount,
            "outstanding_amount": outstanding,
            "is_npa": self.is_npa(classification),
        }

    async def run_npa_classification(
        self,
        organization_id: UUID,
        as_of_date: Optional[date] = None,
        user_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """
        Run NPA classification for all active loans in an organization.

        Returns summary of classification results.
        """
        if as_of_date is None:
            as_of_date = date.today()

        # Get all active loan accounts
        result = await self.db.execute(
            select(LoanAccount).where(
                LoanAccount.organization_id == organization_id,
                LoanAccount.status.in_(["active", "overdue"]),
                LoanAccount.is_active == True,
            )
        )
        loans = list(result.scalars().all())

        summary = {
            "total_loans": len(loans),
            "as_of_date": as_of_date.isoformat(),
            "classifications": {},
            "total_npa_amount": Decimal("0"),
            "total_provision_required": Decimal("0"),
            "processed": 0,
            "errors": 0,
        }

        for loan in loans:
            try:
                dpd = await self.get_dpd(loan.id)
                classification = await self.classify_loan(loan.id, dpd)
                provision_data = await self.calculate_provision(
                    loan.id,
                    classification,
                    loan.is_secured if hasattr(loan, "is_secured") else True,
                )

                # Update loan account classification
                loan.npa_classification = classification
                loan.dpd = dpd
                loan.is_npa = self.is_npa(classification)

                # Create or update NPA classification record
                await self._upsert_npa_classification(
                    loan_account_id=loan.id,
                    classification=classification,
                    dpd=dpd,
                    as_of_date=as_of_date,
                    provision_data=provision_data,
                    user_id=user_id,
                )

                # Update summary
                if classification not in summary["classifications"]:
                    summary["classifications"][classification] = {
                        "count": 0,
                        "outstanding": Decimal("0"),
                        "provision": Decimal("0"),
                    }
                summary["classifications"][classification]["count"] += 1
                summary["classifications"][classification]["outstanding"] += provision_data[
                    "outstanding_amount"
                ]
                summary["classifications"][classification]["provision"] += provision_data[
                    "provision_amount"
                ]

                if self.is_npa(classification):
                    summary["total_npa_amount"] += provision_data["outstanding_amount"]

                summary["total_provision_required"] += provision_data["provision_amount"]
                summary["processed"] += 1

            except Exception as e:
                logger.error(f"Error classifying loan {loan.id}: {e}")
                summary["errors"] += 1

        await self.db.flush()

        return summary

    async def _upsert_npa_classification(
        self,
        loan_account_id: UUID,
        classification: str,
        dpd: int,
        as_of_date: date,
        provision_data: Dict,
        user_id: Optional[UUID] = None,
    ) -> NPAClassification:
        """Create or update NPA classification record."""
        # Check for existing record
        result = await self.db.execute(
            select(NPAClassification).where(
                NPAClassification.loan_account_id == loan_account_id,
                NPAClassification.as_of_date == as_of_date,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            # Check if classification changed
            if existing.classification != classification:
                # Log history
                await self._log_classification_change(
                    loan_account_id=loan_account_id,
                    old_classification=existing.classification,
                    new_classification=classification,
                    reason="Automated NPA run",
                    user_id=user_id,
                )

            existing.classification = classification
            existing.dpd = dpd
            existing.outstanding_amount = provision_data["outstanding_amount"]
            existing.provision_rate = provision_data["provision_rate"]
            existing.provision_amount = provision_data["provision_amount"]
            existing.is_npa = provision_data["is_npa"]
            existing.updated_by = user_id
            return existing
        else:
            npa_record = NPAClassification(
                loan_account_id=loan_account_id,
                as_of_date=as_of_date,
                classification=classification,
                dpd=dpd,
                outstanding_amount=provision_data["outstanding_amount"],
                provision_rate=provision_data["provision_rate"],
                provision_amount=provision_data["provision_amount"],
                is_npa=provision_data["is_npa"],
                created_by=user_id,
            )
            self.db.add(npa_record)
            return npa_record

    async def _log_classification_change(
        self,
        loan_account_id: UUID,
        old_classification: str,
        new_classification: str,
        reason: str,
        user_id: Optional[UUID] = None,
    ) -> NPAHistory:
        """Log NPA classification change."""
        is_upgrade = self._is_upgrade(old_classification, new_classification)

        history = NPAHistory(
            loan_account_id=loan_account_id,
            old_classification=old_classification,
            new_classification=new_classification,
            change_date=date.today(),
            reason=reason,
            is_upgrade=is_upgrade,
            created_by=user_id,
        )
        self.db.add(history)
        return history

    def _is_upgrade(self, old_class: str, new_class: str) -> bool:
        """Check if classification change is an upgrade (improvement)."""
        class_order = [
            "loss",
            "doubtful_3",
            "doubtful_2",
            "doubtful_1",
            "substandard",
            "sma_2",
            "sma_1",
            "sma_0",
            "standard",
        ]
        old_idx = class_order.index(old_class) if old_class in class_order else 0
        new_idx = class_order.index(new_class) if new_class in class_order else 0
        return new_idx > old_idx

    async def upgrade_npa(
        self,
        loan_account_id: UUID,
        new_classification: str,
        reason: str,
        user_id: Optional[UUID] = None,
    ) -> bool:
        """
        Manually upgrade NPA classification (e.g., after recovery).

        Args:
            loan_account_id: Loan account ID
            new_classification: Target classification
            reason: Reason for upgrade
            user_id: User performing the action

        Returns:
            True if upgrade successful
        """
        result = await self.db.execute(select(LoanAccount).where(LoanAccount.id == loan_account_id))
        loan = result.scalar_one_or_none()
        if not loan:
            return False

        old_classification = loan.npa_classification or "standard"

        # Validate upgrade
        if not self._is_upgrade(old_classification, new_classification):
            raise ValueError("New classification must be better than current")

        # Log history
        await self._log_classification_change(
            loan_account_id=loan_account_id,
            old_classification=old_classification,
            new_classification=new_classification,
            reason=reason,
            user_id=user_id,
        )

        # Update loan
        loan.npa_classification = new_classification
        loan.is_npa = self.is_npa(new_classification)
        loan.updated_by = user_id

        await self.db.flush()
        return True

    async def write_off_loan(
        self,
        loan_account_id: UUID,
        write_off_amount: Decimal,
        reason: str,
        approved_by: UUID,
        user_id: Optional[UUID] = None,
    ) -> bool:
        """
        Write off a loan (mark as loss).

        Args:
            loan_account_id: Loan account ID
            write_off_amount: Amount being written off
            reason: Reason for write-off
            approved_by: Approver user ID
            user_id: User performing the action

        Returns:
            True if write-off successful
        """
        result = await self.db.execute(select(LoanAccount).where(LoanAccount.id == loan_account_id))
        loan = result.scalar_one_or_none()
        if not loan:
            return False

        old_classification = loan.npa_classification or "standard"

        # Log history
        await self._log_classification_change(
            loan_account_id=loan_account_id,
            old_classification=old_classification,
            new_classification="loss",
            reason=f"Write-off: {reason}",
            user_id=user_id,
        )

        # Update loan
        loan.npa_classification = "loss"
        loan.is_npa = True
        loan.status = "written_off"
        loan.write_off_amount = write_off_amount
        loan.write_off_date = date.today()
        loan.write_off_reason = reason
        loan.write_off_approved_by = approved_by
        loan.updated_by = user_id

        await self.db.flush()
        return True

    async def get_npa_summary(
        self,
        organization_id: UUID,
        as_of_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Get NPA summary for an organization.

        Returns summary statistics for NPA portfolio.
        """
        if as_of_date is None:
            as_of_date = date.today()

        result = await self.db.execute(
            select(
                LoanAccount.npa_classification,
                func.count(LoanAccount.id).label("count"),
                func.sum(
                    LoanAccount.principal_outstanding + LoanAccount.interest_outstanding
                ).label("outstanding"),
            )
            .where(
                LoanAccount.organization_id == organization_id,
                LoanAccount.status.in_(["active", "overdue"]),
                LoanAccount.is_active == True,
            )
            .group_by(LoanAccount.npa_classification)
        )

        rows = result.all()

        summary = {
            "as_of_date": as_of_date.isoformat(),
            "total_loans": 0,
            "total_outstanding": Decimal("0"),
            "npa_loans": 0,
            "npa_outstanding": Decimal("0"),
            "gnpa_ratio": Decimal("0"),
            "classifications": {},
        }

        for row in rows:
            classification = row.npa_classification or "standard"
            count = row.count
            outstanding = row.outstanding or Decimal("0")

            summary["classifications"][classification] = {
                "count": count,
                "outstanding": outstanding,
            }
            summary["total_loans"] += count
            summary["total_outstanding"] += outstanding

            if self.is_npa(classification):
                summary["npa_loans"] += count
                summary["npa_outstanding"] += outstanding

        # Calculate GNPA ratio
        if summary["total_outstanding"] > 0:
            summary["gnpa_ratio"] = (
                summary["npa_outstanding"] / summary["total_outstanding"]
            ) * 100

        return summary

    async def get_npa_movement(
        self,
        organization_id: UUID,
        from_date: date,
        to_date: date,
    ) -> Dict[str, Any]:
        """
        Get NPA movement report for a period.

        Shows loans moving in/out of NPA classification.
        """
        result = await self.db.execute(
            select(NPAHistory)
            .join(LoanAccount, NPAHistory.loan_account_id == LoanAccount.id)
            .where(
                LoanAccount.organization_id == organization_id,
                NPAHistory.change_date >= from_date,
                NPAHistory.change_date <= to_date,
            )
            .order_by(NPAHistory.change_date)
        )
        history = list(result.scalars().all())

        movement = {
            "period": {"from": from_date.isoformat(), "to": to_date.isoformat()},
            "slippage": [],  # Loans becoming NPA
            "upgrades": [],  # Loans moving out of NPA
            "write_offs": [],
            "total_slippage_count": 0,
            "total_upgrade_count": 0,
            "total_write_off_count": 0,
        }

        for entry in history:
            record = {
                "loan_account_id": str(entry.loan_account_id),
                "date": entry.change_date.isoformat(),
                "from": entry.old_classification,
                "to": entry.new_classification,
                "reason": entry.reason,
            }

            old_is_npa = self.is_npa(entry.old_classification)
            new_is_npa = self.is_npa(entry.new_classification)

            if not old_is_npa and new_is_npa:
                movement["slippage"].append(record)
                movement["total_slippage_count"] += 1
            elif old_is_npa and not new_is_npa:
                movement["upgrades"].append(record)
                movement["total_upgrade_count"] += 1

            if entry.new_classification == "loss":
                movement["write_offs"].append(record)
                movement["total_write_off_count"] += 1

        return movement
