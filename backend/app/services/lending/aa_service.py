"""Account Aggregator service for consent management and data fetching."""

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID, uuid4

from sqlalchemy import select, func, and_, or_, update, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.lending.aa_consent import (
    AAConsent, AAFetchSession, AABankAccount, AABankTransaction, AAConsentLog
)
from app.models.lending.entity import Entity
from app.models.lending.application import LoanApplication
from app.models.lending.loan_account import LoanAccount
from app.models.lending.enums import (
    AAProvider, AAConsentStatus, AAConsentPurpose, AAConsentMode,
    AAFetchFrequency, AAFIType, AAFetchSessionStatus, AADataStatus
)
from app.models.core.integration_config import IntegrationConfig, IntegrationType
from app.schemas.lending.aa import (
    AAConsentCreate, AAConsentUpdate, AAConsentResponse, AAConsentListResponse,
    AAConsentDetailResponse, AAConsentRequestInitiate, AAConsentInitiateResponse,
    AAFetchDataRequest, AAFetchDataResponse, AAFetchSessionResponse,
    AAFetchSessionDetailResponse, AAFetchSessionListResponse,
    AABankAccountResponse, AABankAccountDetailResponse, AABankAccountListResponse,
    AABankTransactionResponse, AABankTransactionListResponse,
    AAConsentStatistics, AAFetchStatistics, AABankStatementAnalysis,
    AAConsentLogResponse, AAConsentLogListResponse,
)
from app.integrations.aa.factory import AAClientFactory
from app.integrations.aa.base import AAClientBase
from app.integrations.aa.schemas import AAConsentRequest, AAFetchRequest

logger = logging.getLogger(__name__)


class AAService:
    """Service for Account Aggregator consent and data management."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # Integration Config Helpers
    # =========================================================================

    async def _get_aa_client(
        self,
        organization_id: UUID,
        provider: AAProvider,
    ) -> Tuple[AAClientBase, IntegrationConfig]:
        """Get AA client for the organization and provider.

        Args:
            organization_id: Organization UUID
            provider: AA provider

        Returns:
            Tuple of AA client and integration config

        Raises:
            ValueError: If no active config found
        """
        # Find active integration config
        query = select(IntegrationConfig).where(
            and_(
                IntegrationConfig.organization_id == organization_id,
                IntegrationConfig.integration_type == IntegrationType.ACCOUNT_AGGREGATOR,
                IntegrationConfig.provider == provider.value,
                IntegrationConfig.is_active == True,
            )
        )
        result = await self.db.execute(query)
        config = result.scalar_one_or_none()

        if not config:
            raise ValueError(
                f"No active {provider.value} integration config found for organization"
            )

        # Create client
        client = AAClientFactory.create(
            provider.value,
            config.config_data,
            config.sandbox_mode,
        )

        return client, config

    # =========================================================================
    # Consent Management
    # =========================================================================

    async def initiate_consent(
        self,
        request: AAConsentRequestInitiate,
        created_by_id: Optional[UUID] = None,
    ) -> AAConsentInitiateResponse:
        """Initiate a new consent request.

        Args:
            request: Consent initiation request
            created_by_id: User initiating the consent

        Returns:
            Consent initiation response with URL
        """
        # Get AA client
        client, config = await self._get_aa_client(request.organization_id, request.provider)

        # Build AA consent request
        aa_request = AAConsentRequest(
            customer_vua=request.customer_id,
            purpose=request.purpose.value,
            purpose_description=f"Financial data for {request.purpose.value.lower()}",
            fi_types=[ft.value for ft in request.fi_types],
            consent_mode="VIEW",
            fetch_type="ONETIME",
            data_range_from=request.fi_data_from,
            data_range_to=request.fi_data_to,
            consent_validity_months=request.consent_validity_months,
            data_life_months=6,
            redirect_url=request.redirect_url or config.config_data.get("callback_url"),
            fiu_entity_id=config.config_data.get("entity_id", ""),
            customer_id=str(request.entity_id) if request.entity_id else None,
            loan_application_id=str(request.loan_application_id) if request.loan_application_id else None,
            loan_account_id=str(request.loan_account_id) if request.loan_account_id else None,
        )

        # Call AA provider
        aa_response = await client.create_consent(aa_request)

        if not aa_response.success:
            raise ValueError(aa_response.error_message or "Failed to create consent")

        # Create consent record
        consent_expiry = datetime.utcnow() + timedelta(days=request.consent_validity_months * 30)

        consent = AAConsent(
            organization_id=request.organization_id,
            entity_id=request.entity_id,
            loan_application_id=request.loan_application_id,
            loan_account_id=request.loan_account_id,
            customer_id=request.customer_id,
            customer_name=request.customer_name,
            customer_mobile=request.customer_mobile,
            customer_email=request.customer_email,
            provider=request.provider,
            consent_handle=aa_response.consent_handle,
            purpose=request.purpose,
            consent_mode=AAConsentMode.VIEW,
            fi_types=[ft.value for ft in request.fi_types],
            fi_data_from=request.fi_data_from,
            fi_data_to=request.fi_data_to,
            fetch_frequency=AAFetchFrequency.ONETIME,
            consent_expiry=consent_expiry,
            status=AAConsentStatus.PENDING,
            consent_url=aa_response.redirect_url,
            redirect_url=request.redirect_url,
            request_timestamp=datetime.utcnow(),
            aa_response=aa_response.raw_response,
            created_by_id=created_by_id,
        )
        self.db.add(consent)

        # Create log entry
        await self._create_consent_log(
            consent_id=consent.id,
            event_type="CREATED",
            new_status=AAConsentStatus.PENDING,
            source="USER",
            message="Consent request initiated",
            aa_response=aa_response.raw_response,
            created_by_id=created_by_id,
        )

        await self.db.commit()
        await self.db.refresh(consent)

        return AAConsentInitiateResponse(
            consent_id=consent.id,
            consent_handle=aa_response.consent_handle,
            consent_url=aa_response.redirect_url or "",
            status=AAConsentStatus.PENDING,
            message="Consent request initiated. Customer needs to approve via AA app.",
        )

    async def get_consent(self, consent_id: UUID) -> AAConsentDetailResponse:
        """Get consent by ID with details."""
        query = (
            select(AAConsent)
            .where(AAConsent.id == consent_id)
            .options(
                selectinload(AAConsent.entity),
                selectinload(AAConsent.fetch_sessions),
            )
        )
        result = await self.db.execute(query)
        consent = result.scalar_one_or_none()

        if not consent:
            raise ValueError(f"Consent {consent_id} not found")

        return self._to_consent_detail_response(consent)

    async def list_consents(
        self,
        organization_id: UUID,
        entity_id: Optional[UUID] = None,
        status: Optional[AAConsentStatus] = None,
        provider: Optional[AAProvider] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> AAConsentListResponse:
        """List consents with filters."""
        query = select(AAConsent).where(
            AAConsent.organization_id == organization_id
        ).order_by(desc(AAConsent.created_at))

        if entity_id:
            query = query.where(AAConsent.entity_id == entity_id)
        if status:
            query = query.where(AAConsent.status == status)
        if provider:
            query = query.where(AAConsent.provider == provider)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Apply pagination
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        consents = result.scalars().all()

        return AAConsentListResponse(
            items=[self._to_consent_response(c) for c in consents],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size,
        )

    async def check_consent_status(
        self,
        consent_id: UUID,
        sync_with_provider: bool = True,
    ) -> AAConsentResponse:
        """Check and update consent status.

        Args:
            consent_id: Consent UUID
            sync_with_provider: Whether to check with AA provider

        Returns:
            Updated consent response
        """
        consent = await self.db.get(AAConsent, consent_id)
        if not consent:
            raise ValueError(f"Consent {consent_id} not found")

        if sync_with_provider and consent.consent_handle:
            # Get AA client
            client, _ = await self._get_aa_client(consent.organization_id, consent.provider)

            # Check status with provider
            aa_response = await client.get_consent_status(consent.consent_handle)

            if aa_response.success:
                old_status = consent.status
                new_status = self._map_aa_status(aa_response.consent_status)

                if new_status != old_status:
                    consent.status = new_status
                    consent.status_updated_at = datetime.utcnow()

                    if new_status == AAConsentStatus.ACTIVE:
                        consent.consent_id = aa_response.consent_id
                        consent.approved_at = datetime.utcnow()
                    elif new_status == AAConsentStatus.REJECTED:
                        consent.rejected_at = datetime.utcnow()
                        consent.rejection_reason = aa_response.error_message

                    consent.aa_response = aa_response.raw_response

                    # Log status change
                    await self._create_consent_log(
                        consent_id=consent.id,
                        event_type="STATUS_CHANGE",
                        old_status=old_status,
                        new_status=new_status,
                        source="PROVIDER_SYNC",
                        aa_response=aa_response.raw_response,
                    )

                    await self.db.commit()

        return self._to_consent_response(consent)

    async def revoke_consent(
        self,
        consent_id: UUID,
        reason: Optional[str] = None,
        revoked_by_id: Optional[UUID] = None,
    ) -> AAConsentResponse:
        """Revoke an active consent."""
        consent = await self.db.get(AAConsent, consent_id)
        if not consent:
            raise ValueError(f"Consent {consent_id} not found")

        if consent.status not in [AAConsentStatus.ACTIVE, AAConsentStatus.APPROVED]:
            raise ValueError(f"Cannot revoke consent with status {consent.status}")

        # Call AA provider to revoke
        if consent.consent_id:
            client, _ = await self._get_aa_client(consent.organization_id, consent.provider)
            aa_response = await client.revoke_consent(consent.consent_id, reason)

            if not aa_response.success:
                logger.warning(f"Failed to revoke consent with provider: {aa_response.error_message}")

        # Update local status
        old_status = consent.status
        consent.status = AAConsentStatus.REVOKED
        consent.status_updated_at = datetime.utcnow()
        consent.revoked_at = datetime.utcnow()

        # Log
        await self._create_consent_log(
            consent_id=consent.id,
            event_type="REVOKED",
            old_status=old_status,
            new_status=AAConsentStatus.REVOKED,
            source="USER",
            message=reason,
            created_by_id=revoked_by_id,
        )

        await self.db.commit()
        return self._to_consent_response(consent)

    # =========================================================================
    # Data Fetching
    # =========================================================================

    async def initiate_data_fetch(
        self,
        request: AAFetchDataRequest,
    ) -> AAFetchDataResponse:
        """Initiate FI data fetch for an approved consent."""
        consent = await self.db.get(AAConsent, request.consent_id)
        if not consent:
            raise ValueError(f"Consent {request.consent_id} not found")

        if consent.status not in [AAConsentStatus.ACTIVE, AAConsentStatus.APPROVED]:
            raise ValueError(f"Consent is not active (status: {consent.status})")

        if not consent.consent_id:
            raise ValueError("Consent has not been approved yet (no consent_id)")

        # Get AA client
        client, _ = await self._get_aa_client(consent.organization_id, consent.provider)

        # Build fetch request
        fi_types = request.fi_types or consent.fi_types
        aa_request = AAFetchRequest(
            consent_id=consent.consent_id,
            fi_types=[ft.value if isinstance(ft, AAFIType) else ft for ft in fi_types],
            data_range_from=request.data_from or consent.fi_data_from,
            data_range_to=request.data_to or consent.fi_data_to,
        )

        # Initiate fetch
        aa_response = await client.initiate_fi_request(aa_request)

        if not aa_response.success:
            raise ValueError(aa_response.error_message or "Failed to initiate data fetch")

        # Create fetch session
        session = AAFetchSession(
            consent_id=consent.id,
            organization_id=consent.organization_id,
            session_id=aa_response.session_id,
            data_session_id=aa_response.data_session_id,
            fi_types_requested=aa_request.fi_types,
            data_from=aa_request.data_range_from,
            data_to=aa_request.data_range_to,
            status=AAFetchSessionStatus.INITIATED,
            initiated_at=datetime.utcnow(),
            aa_response=aa_response.raw_response,
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)

        return AAFetchDataResponse(
            fetch_session_id=session.id,
            session_id=aa_response.session_id or "",
            status=AAFetchSessionStatus.INITIATED,
            message="Data fetch initiated. Waiting for FIP response.",
        )

    async def fetch_session_data(
        self,
        session_id: UUID,
    ) -> AAFetchSessionDetailResponse:
        """Fetch actual data for a session (poll or after webhook)."""
        session = await self.db.get(AAFetchSession, session_id)
        if not session:
            raise ValueError(f"Fetch session {session_id} not found")

        consent = await self.db.get(AAConsent, session.consent_id)
        if not consent:
            raise ValueError("Associated consent not found")

        # Get AA client
        client, _ = await self._get_aa_client(consent.organization_id, consent.provider)

        # Fetch data
        aa_response = await client.fetch_fi_data(
            session.session_id,
            consent.consent_id,
        )

        if not aa_response.success:
            session.status = AAFetchSessionStatus.FAILED
            session.error_code = aa_response.error_code
            session.error_message = aa_response.error_message
            await self.db.commit()
            raise ValueError(aa_response.error_message or "Failed to fetch data")

        # Process FI data
        if aa_response.fi_data:
            session.data_received_at = datetime.utcnow()
            session.status = AAFetchSessionStatus.COMPLETED
            session.accounts_received = len(aa_response.fi_data)

            for fi_data in aa_response.fi_data:
                # Create bank account record
                bank_account = AABankAccount(
                    fetch_session_id=session.id,
                    organization_id=consent.organization_id,
                    entity_id=consent.entity_id,
                    fi_type=AAFIType(fi_data.fi_type) if fi_data.fi_type else AAFIType.DEPOSIT,
                    fip_id=fi_data.fip_id,
                    fip_name=fi_data.fip_id,  # Will be updated from profile
                    account_type=fi_data.account_type,
                    account_number_masked=fi_data.masked_account_number,
                    account_ref_number=fi_data.link_ref_number,
                    status=AADataStatus.RECEIVED,
                    raw_data=fi_data.raw_data,
                    profile_data=fi_data.profile,
                    summary_data=fi_data.summary,
                    data_fetched_at=datetime.utcnow(),
                    data_from=session.data_from,
                    data_to=session.data_to,
                )

                # Parse profile data
                if fi_data.profile:
                    profile = fi_data.profile
                    bank_account.holder_name = profile.get("name") or profile.get("holderName")
                    bank_account.holder_pan = profile.get("pan")
                    bank_account.holder_mobile = profile.get("mobile")
                    bank_account.holder_email = profile.get("email")
                    bank_account.ifsc_code = profile.get("ifsc") or profile.get("ifscCode")
                    bank_account.branch = profile.get("branch")

                # Parse summary data
                if fi_data.summary:
                    summary = fi_data.summary
                    bank_account.current_balance = Decimal(str(summary.get("currentBalance", 0)))
                    bank_account.available_balance = Decimal(str(summary.get("availableBalance", 0)))
                    if summary.get("balanceDateTime"):
                        try:
                            bank_account.balance_as_on = datetime.fromisoformat(
                                summary["balanceDateTime"].replace("Z", "+00:00")
                            )
                        except Exception:
                            pass

                self.db.add(bank_account)
                await self.db.flush()

                # Process transactions
                if fi_data.transactions:
                    for txn in fi_data.transactions:
                        transaction = AABankTransaction(
                            bank_account_id=bank_account.id,
                            organization_id=consent.organization_id,
                            txn_id=txn.get("txnId"),
                            txn_type=txn.get("type", "UNKNOWN"),
                            mode=txn.get("mode"),
                            amount=Decimal(str(txn.get("amount", 0))),
                            balance_after=Decimal(str(txn.get("currentBalance", 0))) if txn.get("currentBalance") else None,
                            transaction_date=datetime.strptime(
                                txn.get("transactionTimestamp", txn.get("valueDate", "1970-01-01"))[:10],
                                "%Y-%m-%d"
                            ).date(),
                            transaction_timestamp=datetime.fromisoformat(
                                txn.get("transactionTimestamp", "1970-01-01T00:00:00").replace("Z", "+00:00")
                            ) if txn.get("transactionTimestamp") else None,
                            narration=txn.get("narration"),
                            reference=txn.get("reference"),
                            counterparty_name=txn.get("counterpartyName"),
                            counterparty_account=txn.get("counterpartyAccount"),
                            counterparty_ifsc=txn.get("counterpartyIfsc"),
                            raw_data=txn,
                        )
                        self.db.add(transaction)

            session.completed_at = datetime.utcnow()

        session.aa_response = aa_response.raw_response
        await self.db.commit()

        # Reload with relationships
        query = (
            select(AAFetchSession)
            .where(AAFetchSession.id == session_id)
            .options(selectinload(AAFetchSession.bank_accounts))
        )
        result = await self.db.execute(query)
        session = result.scalar_one()

        return self._to_fetch_session_detail_response(session)

    async def get_fetch_session(self, session_id: UUID) -> AAFetchSessionDetailResponse:
        """Get fetch session by ID with accounts."""
        query = (
            select(AAFetchSession)
            .where(AAFetchSession.id == session_id)
            .options(
                selectinload(AAFetchSession.bank_accounts).selectinload(AABankAccount.transactions)
            )
        )
        result = await self.db.execute(query)
        session = result.scalar_one_or_none()

        if not session:
            raise ValueError(f"Fetch session {session_id} not found")

        return self._to_fetch_session_detail_response(session)

    async def list_fetch_sessions(
        self,
        consent_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> AAFetchSessionListResponse:
        """List fetch sessions for a consent."""
        query = (
            select(AAFetchSession)
            .where(AAFetchSession.consent_id == consent_id)
            .order_by(desc(AAFetchSession.created_at))
        )

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        sessions = result.scalars().all()

        return AAFetchSessionListResponse(
            items=[self._to_fetch_session_response(s) for s in sessions],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size,
        )

    # =========================================================================
    # Bank Account Data
    # =========================================================================

    async def get_bank_account(self, account_id: UUID) -> AABankAccountDetailResponse:
        """Get bank account by ID with transactions."""
        query = (
            select(AABankAccount)
            .where(AABankAccount.id == account_id)
            .options(selectinload(AABankAccount.transactions))
        )
        result = await self.db.execute(query)
        account = result.scalar_one_or_none()

        if not account:
            raise ValueError(f"Bank account {account_id} not found")

        return self._to_bank_account_detail_response(account)

    async def list_bank_accounts(
        self,
        organization_id: UUID,
        entity_id: Optional[UUID] = None,
        fi_type: Optional[AAFIType] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> AABankAccountListResponse:
        """List bank accounts with filters."""
        query = (
            select(AABankAccount)
            .where(AABankAccount.organization_id == organization_id)
            .order_by(desc(AABankAccount.created_at))
        )

        if entity_id:
            query = query.where(AABankAccount.entity_id == entity_id)
        if fi_type:
            query = query.where(AABankAccount.fi_type == fi_type)

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        accounts = result.scalars().all()

        return AABankAccountListResponse(
            items=[self._to_bank_account_response(a) for a in accounts],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size,
        )

    async def list_transactions(
        self,
        bank_account_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        txn_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> AABankTransactionListResponse:
        """List transactions for a bank account."""
        query = (
            select(AABankTransaction)
            .where(AABankTransaction.bank_account_id == bank_account_id)
            .order_by(desc(AABankTransaction.transaction_date))
        )

        if start_date:
            query = query.where(AABankTransaction.transaction_date >= start_date)
        if end_date:
            query = query.where(AABankTransaction.transaction_date <= end_date)
        if txn_type:
            query = query.where(AABankTransaction.txn_type == txn_type)

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        transactions = result.scalars().all()

        return AABankTransactionListResponse(
            items=[self._to_transaction_response(t) for t in transactions],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size,
        )

    # =========================================================================
    # Statistics & Analytics
    # =========================================================================

    async def get_consent_statistics(
        self,
        organization_id: UUID,
    ) -> AAConsentStatistics:
        """Get consent statistics for organization."""
        # Count by status
        status_query = (
            select(AAConsent.status, func.count())
            .where(AAConsent.organization_id == organization_id)
            .group_by(AAConsent.status)
        )
        status_result = await self.db.execute(status_query)
        status_counts = {row[0].value: row[1] for row in status_result}

        # Count by provider
        provider_query = (
            select(AAConsent.provider, func.count())
            .where(AAConsent.organization_id == organization_id)
            .group_by(AAConsent.provider)
        )
        provider_result = await self.db.execute(provider_query)
        provider_counts = {row[0].value: row[1] for row in provider_result}

        # Count by purpose
        purpose_query = (
            select(AAConsent.purpose, func.count())
            .where(AAConsent.organization_id == organization_id)
            .group_by(AAConsent.purpose)
        )
        purpose_result = await self.db.execute(purpose_query)
        purpose_counts = {row[0].value: row[1] for row in purpose_result}

        total = sum(status_counts.values())
        active = status_counts.get("ACTIVE", 0) + status_counts.get("APPROVED", 0)
        pending = status_counts.get("PENDING", 0)
        expired = status_counts.get("EXPIRED", 0)
        revoked = status_counts.get("REVOKED", 0)

        approval_rate = (active / total * 100) if total > 0 else 0

        return AAConsentStatistics(
            total_consents=total,
            active_consents=active,
            pending_consents=pending,
            expired_consents=expired,
            revoked_consents=revoked,
            approval_rate=approval_rate,
            provider_breakdown=provider_counts,
            purpose_breakdown=purpose_counts,
        )

    async def get_fetch_statistics(
        self,
        organization_id: UUID,
    ) -> AAFetchStatistics:
        """Get fetch statistics for organization."""
        # Fetch session counts
        session_query = (
            select(AAFetchSession.status, func.count())
            .join(AAConsent)
            .where(AAConsent.organization_id == organization_id)
            .group_by(AAFetchSession.status)
        )
        session_result = await self.db.execute(session_query)
        session_counts = {row[0].value: row[1] for row in session_result}

        # Account counts by FI type
        fi_type_query = (
            select(AABankAccount.fi_type, func.count())
            .where(AABankAccount.organization_id == organization_id)
            .group_by(AABankAccount.fi_type)
        )
        fi_type_result = await self.db.execute(fi_type_query)
        fi_type_counts = {row[0].value: row[1] for row in fi_type_result}

        # Total transactions
        txn_count_query = (
            select(func.count())
            .select_from(AABankTransaction)
            .where(AABankTransaction.organization_id == organization_id)
        )
        total_txn = (await self.db.execute(txn_count_query)).scalar() or 0

        total_sessions = sum(session_counts.values())
        successful = session_counts.get("COMPLETED", 0)
        failed = session_counts.get("FAILED", 0)
        total_accounts = sum(fi_type_counts.values())

        success_rate = (successful / total_sessions * 100) if total_sessions > 0 else 0
        avg_accounts = total_accounts / successful if successful > 0 else 0

        return AAFetchStatistics(
            total_fetch_sessions=total_sessions,
            successful_fetches=successful,
            failed_fetches=failed,
            total_accounts_fetched=total_accounts,
            total_transactions_fetched=total_txn,
            success_rate=success_rate,
            avg_accounts_per_fetch=avg_accounts,
            fi_type_breakdown=fi_type_counts,
        )

    # =========================================================================
    # Webhook Handlers
    # =========================================================================

    async def handle_consent_notification(
        self,
        consent_handle: str,
        consent_id: Optional[str],
        status: str,
        raw_payload: Dict[str, Any],
    ):
        """Handle consent status update from webhook."""
        # Find consent by handle
        query = select(AAConsent).where(AAConsent.consent_handle == consent_handle)
        result = await self.db.execute(query)
        consent = result.scalar_one_or_none()

        if not consent:
            logger.warning(f"Consent not found for handle: {consent_handle}")
            return

        old_status = consent.status
        new_status = self._map_aa_status(status)

        consent.status = new_status
        consent.status_updated_at = datetime.utcnow()

        if new_status == AAConsentStatus.ACTIVE and consent_id:
            consent.consent_id = consent_id
            consent.approved_at = datetime.utcnow()
        elif new_status == AAConsentStatus.REJECTED:
            consent.rejected_at = datetime.utcnow()
        elif new_status == AAConsentStatus.REVOKED:
            consent.revoked_at = datetime.utcnow()

        consent.aa_response = raw_payload

        # Log
        await self._create_consent_log(
            consent_id=consent.id,
            event_type="WEBHOOK_STATUS_UPDATE",
            old_status=old_status,
            new_status=new_status,
            source="WEBHOOK",
            aa_response=raw_payload,
        )

        await self.db.commit()

    async def handle_fi_notification(
        self,
        consent_id: str,
        session_id: str,
        status: str,
        fi_status_response: Optional[List[Dict[str, Any]]],
        raw_payload: Dict[str, Any],
    ):
        """Handle FI data notification from webhook."""
        # Find session
        query = select(AAFetchSession).where(AAFetchSession.session_id == session_id)
        result = await self.db.execute(query)
        session = result.scalar_one_or_none()

        if not session:
            logger.warning(f"Fetch session not found for session_id: {session_id}")
            return

        if status == "READY":
            session.status = AAFetchSessionStatus.PENDING
            session.data_requested_at = datetime.utcnow()
        elif status == "DENIED":
            session.status = AAFetchSessionStatus.FAILED
            session.error_message = "Data request denied by FIP"
        elif status == "TIMEOUT":
            session.status = AAFetchSessionStatus.EXPIRED
            session.error_message = "Data request timed out"

        session.aa_response = raw_payload
        await self.db.commit()

    # =========================================================================
    # Helpers
    # =========================================================================

    async def _create_consent_log(
        self,
        consent_id: UUID,
        event_type: str,
        old_status: Optional[AAConsentStatus] = None,
        new_status: Optional[AAConsentStatus] = None,
        source: Optional[str] = None,
        message: Optional[str] = None,
        aa_response: Optional[Dict[str, Any]] = None,
        created_by_id: Optional[UUID] = None,
    ):
        """Create a consent log entry."""
        log = AAConsentLog(
            consent_id=consent_id,
            event_type=event_type,
            old_status=old_status,
            new_status=new_status,
            source=source,
            message=message,
            aa_response=aa_response,
            created_by_id=created_by_id,
        )
        self.db.add(log)

    def _map_aa_status(self, status: str) -> AAConsentStatus:
        """Map AA provider status to internal status."""
        mapping = {
            "PENDING": AAConsentStatus.PENDING,
            "ACTIVE": AAConsentStatus.ACTIVE,
            "APPROVED": AAConsentStatus.APPROVED,
            "REJECTED": AAConsentStatus.REJECTED,
            "REVOKED": AAConsentStatus.REVOKED,
            "PAUSED": AAConsentStatus.PAUSED,
            "EXPIRED": AAConsentStatus.EXPIRED,
            "FAILED": AAConsentStatus.FAILED,
        }
        return mapping.get(status.upper(), AAConsentStatus.PENDING)

    def _to_consent_response(self, consent: AAConsent) -> AAConsentResponse:
        """Convert consent model to response."""
        return AAConsentResponse(
            id=consent.id,
            organization_id=consent.organization_id,
            entity_id=consent.entity_id,
            loan_application_id=consent.loan_application_id,
            loan_account_id=consent.loan_account_id,
            customer_id=consent.customer_id,
            customer_name=consent.customer_name,
            customer_mobile=consent.customer_mobile,
            customer_email=consent.customer_email,
            provider=consent.provider,
            consent_handle=consent.consent_handle,
            consent_id=consent.consent_id,
            consent_url=consent.consent_url,
            purpose=consent.purpose,
            purpose_description=consent.purpose_description,
            consent_mode=consent.consent_mode,
            fi_types=consent.fi_types or [],
            fi_data_from=consent.fi_data_from,
            fi_data_to=consent.fi_data_to,
            fetch_frequency=consent.fetch_frequency,
            fetch_frequency_value=consent.fetch_frequency_value,
            consent_start=consent.consent_start,
            consent_expiry=consent.consent_expiry,
            data_life_unit=consent.data_life_unit,
            data_life_value=consent.data_life_value,
            redirect_url=consent.redirect_url,
            status=consent.status,
            status_updated_at=consent.status_updated_at,
            request_timestamp=consent.request_timestamp,
            approved_at=consent.approved_at,
            rejected_at=consent.rejected_at,
            revoked_at=consent.revoked_at,
            rejection_reason=consent.rejection_reason,
            error_code=consent.error_code,
            error_message=consent.error_message,
            created_at=consent.created_at,
            updated_at=consent.updated_at,
        )

    def _to_consent_detail_response(self, consent: AAConsent) -> AAConsentDetailResponse:
        """Convert consent model to detailed response."""
        response = AAConsentDetailResponse(
            **self._to_consent_response(consent).model_dump()
        )
        response.fetch_sessions = [
            self._to_fetch_session_response(s) for s in (consent.fetch_sessions or [])
        ]
        if consent.entity:
            response.entity_name = consent.entity.name
        return response

    def _to_fetch_session_response(self, session: AAFetchSession) -> AAFetchSessionResponse:
        """Convert fetch session model to response."""
        return AAFetchSessionResponse(
            id=session.id,
            consent_id=session.consent_id,
            organization_id=session.organization_id,
            session_id=session.session_id,
            data_session_id=session.data_session_id,
            fi_types_requested=session.fi_types_requested or [],
            data_from=session.data_from,
            data_to=session.data_to,
            status=session.status,
            total_accounts_requested=session.total_accounts_requested,
            accounts_received=session.accounts_received,
            accounts_failed=session.accounts_failed,
            initiated_at=session.initiated_at,
            data_requested_at=session.data_requested_at,
            data_received_at=session.data_received_at,
            completed_at=session.completed_at,
            error_code=session.error_code,
            error_message=session.error_message,
            created_at=session.created_at,
        )

    def _to_fetch_session_detail_response(
        self, session: AAFetchSession
    ) -> AAFetchSessionDetailResponse:
        """Convert fetch session to detailed response."""
        response = AAFetchSessionDetailResponse(
            **self._to_fetch_session_response(session).model_dump()
        )
        response.bank_accounts = [
            self._to_bank_account_response(a) for a in (session.bank_accounts or [])
        ]
        return response

    def _to_bank_account_response(self, account: AABankAccount) -> AABankAccountResponse:
        """Convert bank account model to response."""
        return AABankAccountResponse(
            id=account.id,
            fetch_session_id=account.fetch_session_id,
            organization_id=account.organization_id,
            entity_id=account.entity_id,
            fi_type=account.fi_type,
            fip_id=account.fip_id,
            fip_name=account.fip_name,
            account_type=account.account_type,
            account_number_masked=account.account_number_masked,
            account_ref_number=account.account_ref_number,
            ifsc_code=account.ifsc_code,
            branch=account.branch,
            holder_name=account.holder_name,
            holder_pan=account.holder_pan,
            holder_mobile=account.holder_mobile,
            holder_email=account.holder_email,
            holder_dob=account.holder_dob,
            holder_type=account.holder_type,
            currency=account.currency,
            current_balance=account.current_balance,
            available_balance=account.available_balance,
            balance_as_on=account.balance_as_on,
            opening_date=account.opening_date,
            maturity_date=account.maturity_date,
            maturity_amount=account.maturity_amount,
            interest_rate=account.interest_rate,
            principal_amount=account.principal_amount,
            status=account.status,
            data_fetched_at=account.data_fetched_at,
            data_from=account.data_from,
            data_to=account.data_to,
            created_at=account.created_at,
        )

    def _to_bank_account_detail_response(
        self, account: AABankAccount
    ) -> AABankAccountDetailResponse:
        """Convert bank account to detailed response."""
        response = AABankAccountDetailResponse(
            **self._to_bank_account_response(account).model_dump()
        )
        response.transactions = [
            self._to_transaction_response(t) for t in (account.transactions or [])
        ]
        return response

    def _to_transaction_response(
        self, txn: AABankTransaction
    ) -> AABankTransactionResponse:
        """Convert transaction model to response."""
        return AABankTransactionResponse(
            id=txn.id,
            bank_account_id=txn.bank_account_id,
            organization_id=txn.organization_id,
            txn_id=txn.txn_id,
            txn_type=txn.txn_type,
            mode=txn.mode,
            amount=txn.amount,
            currency=txn.currency,
            balance_after=txn.balance_after,
            transaction_date=txn.transaction_date,
            transaction_timestamp=txn.transaction_timestamp,
            value_date=txn.value_date,
            narration=txn.narration,
            reference=txn.reference,
            counterparty_name=txn.counterparty_name,
            counterparty_account=txn.counterparty_account,
            counterparty_ifsc=txn.counterparty_ifsc,
            category=txn.category,
            sub_category=txn.sub_category,
            created_at=txn.created_at,
        )
