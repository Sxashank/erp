"""Payment File service for NEFT/RTGS file generation."""

import hashlib
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ap_ar.payment_file import PaymentFile, PaymentFileTransaction
from app.repositories.ap_ar.payment_file_repo import (
    PaymentFileRepository,
    PaymentFileTransactionRepository,
)
from app.repositories.ap_ar.payment_repo import PaymentRepository
from app.repositories.masters.organization_bank_account_repo import OrganizationBankAccountRepository
from app.schemas.ap_ar.payment_file import (
    PaymentFileFormat,
    PaymentFileStatus,
    PaymentTransactionStatus,
    PaymentFileGenerateRequest,
    PaymentFileResponse,
    PaymentFileDetailResponse,
    PaymentFileSummary,
    BankFormatConfig,
)


class PaymentFileService:
    """Service for Payment File operations."""

    # Default bank format configurations
    DEFAULT_BANK_CONFIGS = {
        "HDFC": BankFormatConfig(
            bank_code="HDFC",
            bank_name="HDFC Bank",
            neft_format="HDFC_H2H",
            rtgs_format="HDFC_H2H",
            delimiter="|",
            date_format="%d/%m/%Y",
            amount_format="decimal",
        ),
        "ICICI": BankFormatConfig(
            bank_code="ICIC",
            bank_name="ICICI Bank",
            neft_format="ICICI_CIB",
            rtgs_format="ICICI_CIB",
            delimiter=",",
            date_format="%d-%m-%Y",
            amount_format="decimal",
        ),
        "AXIS": BankFormatConfig(
            bank_code="UTIB",
            bank_name="Axis Bank",
            neft_format="AXIS_CORP",
            rtgs_format="AXIS_CORP",
            delimiter="|",
            date_format="%d/%m/%Y",
            amount_format="decimal",
        ),
        "SBI": BankFormatConfig(
            bank_code="SBIN",
            bank_name="State Bank of India",
            neft_format="SBI_CINB",
            rtgs_format="SBI_CINB",
            delimiter="|",
            date_format="%d-%m-%Y",
            amount_format="paise",
        ),
        "DEFAULT": BankFormatConfig(
            bank_code="XXXX",
            bank_name="Standard Format",
            neft_format="NPCI_STANDARD",
            rtgs_format="NPCI_STANDARD",
            delimiter="|",
            date_format="%d/%m/%Y",
            amount_format="decimal",
        ),
    }

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = PaymentFileRepository(session)
        self.transaction_repository = PaymentFileTransactionRepository(session)
        self.payment_repository = PaymentRepository(session)
        self.bank_account_repository = OrganizationBankAccountRepository(session)

    async def generate_file(
        self,
        data: PaymentFileGenerateRequest,
        created_by: Optional[UUID] = None,
    ) -> PaymentFile:
        """Generate a payment file from selected payments."""
        # Validate bank account
        bank_account = await self.bank_account_repository.get(data.organization_bank_account_id)
        if not bank_account:
            raise ValueError("Bank account not found")
        if bank_account.organization_id != data.organization_id:
            raise ValueError("Bank account belongs to different organization")

        # Check for payments already in files
        already_in_file = await self.repository.get_payments_in_files(
            data.payment_ids,
            exclude_status=["FAILED", "CANCELLED"],
        )
        if already_in_file:
            raise ValueError(
                f"{len(already_in_file)} payment(s) are already included in other files"
            )

        # Get payments and validate
        payments = []
        for payment_id in data.payment_ids:
            payment = await self.payment_repository.get_with_details(payment_id)
            if not payment:
                raise ValueError(f"Payment {payment_id} not found")
            if payment.organization_id != data.organization_id:
                raise ValueError(f"Payment {payment_id} belongs to different organization")
            if payment.status != "APPROVED":
                raise ValueError(f"Payment {payment_id} is not approved")
            if not payment.payment_mode or payment.payment_mode.upper() not in ["NEFT", "RTGS", "IMPS"]:
                raise ValueError(f"Payment {payment_id} payment mode is not compatible")
            payments.append(payment)

        # Generate file reference
        prefix = f"{data.file_format.value}_"
        file_reference = await self.repository.get_next_reference(
            data.organization_id, prefix
        )

        # Create payment file
        payment_file = PaymentFile(
            organization_id=data.organization_id,
            organization_bank_account_id=data.organization_bank_account_id,
            file_reference=file_reference,
            file_format=data.file_format.value,
            payment_date=data.payment_date,
            status=PaymentFileStatus.DRAFT.value,
            description=data.description,
            created_by=created_by,
        )
        payment_file = await self.repository.create(payment_file)

        # Create transactions
        total_amount = Decimal("0.00")
        for seq, payment in enumerate(payments, start=1):
            # Get vendor bank details
            vendor_bank = None
            if hasattr(payment, 'vendor') and payment.vendor:
                vendor_bank = getattr(payment.vendor, 'bank_accounts', [])
                if vendor_bank:
                    vendor_bank = vendor_bank[0]  # Primary bank account

            txn = PaymentFileTransaction(
                payment_file_id=payment_file.id,
                payment_id=payment.id,
                sequence_number=seq,
                beneficiary_name=payment.payee_name or (payment.vendor.name if payment.vendor else ""),
                beneficiary_account_number=vendor_bank.account_number if vendor_bank else "",
                beneficiary_ifsc=vendor_bank.ifsc_code if vendor_bank else "",
                beneficiary_bank_name=vendor_bank.bank_name if vendor_bank else "",
                amount=payment.amount,
                narration=f"Payment for {payment.reference_number}",
                status=PaymentTransactionStatus.PENDING.value,
            )
            await self.transaction_repository.create(txn)
            total_amount += payment.amount

        # Update aggregates
        await self.repository.update(
            payment_file.id,
            {
                "total_transactions": len(payments),
                "total_amount": total_amount,
            }
        )

        # Generate file content
        file_content = await self._generate_file_content(
            payment_file.id,
            data.file_format,
            bank_account,
        )

        # Calculate checksum
        checksum = hashlib.sha256(file_content.encode()).hexdigest()

        # Update with file content and status
        payment_file = await self.repository.update(
            payment_file.id,
            {
                "file_content": file_content,
                "checksum": checksum,
                "status": PaymentFileStatus.GENERATED.value,
                "file_generated_at": datetime.utcnow(),
            }
        )

        return await self.repository.get_with_details(payment_file.id)

    async def _generate_file_content(
        self,
        payment_file_id: UUID,
        file_format: PaymentFileFormat,
        bank_account,
    ) -> str:
        """Generate file content based on format."""
        transactions = await self.transaction_repository.get_by_payment_file(payment_file_id)

        # Get bank config
        ifsc_prefix = bank_account.ifsc_code[:4] if bank_account.ifsc_code else "XXXX"
        config = self.DEFAULT_BANK_CONFIGS.get(
            {
                "HDFC": "HDFC",
                "ICIC": "ICICI",
                "UTIB": "AXIS",
                "SBIN": "SBI",
            }.get(ifsc_prefix, "DEFAULT"),
            self.DEFAULT_BANK_CONFIGS["DEFAULT"]
        )

        if file_format == PaymentFileFormat.NEFT:
            return self._generate_neft_file(transactions, bank_account, config)
        elif file_format == PaymentFileFormat.RTGS:
            return self._generate_rtgs_file(transactions, bank_account, config)
        else:
            return self._generate_generic_file(transactions, bank_account, config)

    def _generate_neft_file(
        self,
        transactions: List[PaymentFileTransaction],
        bank_account,
        config: BankFormatConfig,
    ) -> str:
        """Generate NEFT file in NPCI/bank-specific format."""
        lines = []
        delimiter = config.delimiter
        date_str = date.today().strftime(config.date_format)

        # Header record
        total_amount = sum(t.amount for t in transactions)
        header = delimiter.join([
            "H",  # Record type
            bank_account.account_number,  # Remitter account
            bank_account.ifsc_code,  # Remitter IFSC
            date_str,  # File date
            str(len(transactions)),  # Transaction count
            self._format_amount(total_amount, config),  # Total amount
            "NEFT",  # File type
        ])
        lines.append(header)

        # Transaction records
        for txn in transactions:
            record = delimiter.join([
                "D",  # Record type (Detail)
                str(txn.sequence_number),  # Serial number
                txn.beneficiary_ifsc,  # Beneficiary IFSC
                txn.beneficiary_account_number,  # Beneficiary account
                self._clean_name(txn.beneficiary_name, 40),  # Beneficiary name
                self._format_amount(txn.amount, config),  # Amount
                bank_account.account_number,  # Remitter account
                self._clean_name(bank_account.account_holder_name or "", 40),  # Remitter name
                "IFT",  # Payment type
                self._clean_narration(txn.narration or "", 30),  # Narration
                txn.email or "",  # Email
                txn.mobile or "",  # Mobile
            ])
            lines.append(record)

        # Trailer record
        trailer = delimiter.join([
            "T",  # Record type
            str(len(transactions)),  # Transaction count
            self._format_amount(total_amount, config),  # Total amount
        ])
        lines.append(trailer)

        return "\n".join(lines)

    def _generate_rtgs_file(
        self,
        transactions: List[PaymentFileTransaction],
        bank_account,
        config: BankFormatConfig,
    ) -> str:
        """Generate RTGS file format."""
        lines = []
        delimiter = config.delimiter
        date_str = date.today().strftime(config.date_format)

        # Header record
        total_amount = sum(t.amount for t in transactions)
        header = delimiter.join([
            "H",  # Record type
            bank_account.account_number,  # Remitter account
            bank_account.ifsc_code,  # Remitter IFSC
            date_str,  # File date
            str(len(transactions)),  # Transaction count
            self._format_amount(total_amount, config),  # Total amount
            "RTGS",  # File type
        ])
        lines.append(header)

        # Transaction records
        for txn in transactions:
            record = delimiter.join([
                "D",  # Record type (Detail)
                str(txn.sequence_number),  # Serial number
                txn.beneficiary_ifsc,  # Beneficiary IFSC
                txn.beneficiary_account_number,  # Beneficiary account
                self._clean_name(txn.beneficiary_name, 35),  # Beneficiary name (RTGS has shorter limit)
                self._format_amount(txn.amount, config),  # Amount
                bank_account.account_number,  # Remitter account
                self._clean_name(bank_account.account_holder_name or "", 35),  # Remitter name
                "RTG",  # Payment type
                self._clean_narration(txn.narration or "", 35),  # Sender to receiver info
            ])
            lines.append(record)

        # Trailer record
        trailer = delimiter.join([
            "T",  # Record type
            str(len(transactions)),  # Transaction count
            self._format_amount(total_amount, config),  # Total amount
        ])
        lines.append(trailer)

        return "\n".join(lines)

    def _generate_generic_file(
        self,
        transactions: List[PaymentFileTransaction],
        bank_account,
        config: BankFormatConfig,
    ) -> str:
        """Generate generic payment file (CSV-like)."""
        lines = []
        delimiter = config.delimiter

        # Header row
        header = delimiter.join([
            "Sr No",
            "Beneficiary Name",
            "Beneficiary Account",
            "Beneficiary IFSC",
            "Amount",
            "Narration",
        ])
        lines.append(header)

        # Data rows
        for txn in transactions:
            record = delimiter.join([
                str(txn.sequence_number),
                txn.beneficiary_name,
                txn.beneficiary_account_number,
                txn.beneficiary_ifsc,
                str(txn.amount),
                txn.narration or "",
            ])
            lines.append(record)

        return "\n".join(lines)

    def _format_amount(self, amount: Decimal, config: BankFormatConfig) -> str:
        """Format amount based on bank configuration."""
        if config.amount_format == "paise":
            return str(int(amount * 100))
        return f"{amount:.2f}"

    def _clean_name(self, name: str, max_length: int) -> str:
        """Clean and truncate name for file format."""
        # Remove special characters that might cause issues
        clean = "".join(c for c in name if c.isalnum() or c in " .-")
        return clean[:max_length].strip()

    def _clean_narration(self, narration: str, max_length: int) -> str:
        """Clean and truncate narration."""
        clean = "".join(c for c in narration if c.isalnum() or c in " .-/")
        return clean[:max_length].strip()

    async def get(self, id: UUID) -> Optional[PaymentFile]:
        """Get payment file by ID."""
        return await self.repository.get_with_details(id)

    async def get_by_reference(self, file_reference: str) -> Optional[PaymentFile]:
        """Get payment file by reference."""
        return await self.repository.get_by_reference(file_reference)

    async def get_by_organization(
        self,
        organization_id: UUID,
        status: Optional[str] = None,
        file_format: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[PaymentFile], int]:
        """Get payment files for an organization."""
        return await self.repository.get_by_organization(
            organization_id=organization_id,
            status=status,
            file_format=file_format,
            from_date=from_date,
            to_date=to_date,
            skip=skip,
            limit=limit,
        )

    async def mark_downloaded(self, id: UUID) -> Optional[PaymentFile]:
        """Mark file as downloaded."""
        return await self.repository.update_file_status(
            id,
            PaymentFileStatus.DOWNLOADED.value,
            "file_downloaded_at",
        )

    async def mark_uploaded(self, id: UUID) -> Optional[PaymentFile]:
        """Mark file as uploaded to bank."""
        return await self.repository.update_file_status(
            id,
            PaymentFileStatus.UPLOADED.value,
            "file_uploaded_at",
        )

    async def start_processing(self, id: UUID) -> Optional[PaymentFile]:
        """Mark file as processing started."""
        return await self.repository.update_file_status(
            id,
            PaymentFileStatus.PROCESSING.value,
            "processing_started_at",
        )

    async def update_processing_results(
        self,
        id: UUID,
        results: List[dict],
    ) -> PaymentFile:
        """Update transaction statuses from bank response."""
        payment_file = await self.repository.get_with_details(id)
        if not payment_file:
            raise ValueError("Payment file not found")

        # Update each transaction
        for result in results:
            txn_id = result.get("transaction_id")
            status = result.get("status", "FAILED")
            bank_reference = result.get("bank_reference")
            failure_reason = result.get("failure_reason")

            await self.transaction_repository.update_status(
                txn_id,
                status,
                bank_reference,
                failure_reason,
            )

        # Recalculate aggregates
        await self.repository.update_aggregates(id)

        # Determine final status
        updated_file = await self.repository.get_with_details(id)
        if updated_file.failed_count == 0:
            final_status = PaymentFileStatus.COMPLETED.value
        elif updated_file.successful_count == 0:
            final_status = PaymentFileStatus.FAILED.value
        else:
            final_status = PaymentFileStatus.PARTIALLY_COMPLETED.value

        return await self.repository.update(
            id,
            {
                "status": final_status,
                "processing_completed_at": datetime.utcnow(),
            }
        )

    async def get_file_content(self, id: UUID) -> Optional[str]:
        """Get file content for download."""
        payment_file = await self.repository.get(id)
        if not payment_file:
            return None
        return payment_file.file_content

    async def get_payment_summary(
        self,
        organization_id: UUID,
        payment_ids: List[UUID],
    ) -> PaymentFileSummary:
        """Get summary of payments for file generation."""
        # Check which payments are already in files
        already_in_file = await self.repository.get_payments_in_files(
            payment_ids,
            exclude_status=["FAILED", "CANCELLED"],
        )

        # Get payment details
        total_amount = Decimal("0.00")
        by_format = {
            "NEFT": {"count": 0, "amount": Decimal("0.00")},
            "RTGS": {"count": 0, "amount": Decimal("0.00")},
        }

        for payment_id in payment_ids:
            if payment_id in already_in_file:
                continue

            payment = await self.payment_repository.get(payment_id)
            if payment and payment.status == "APPROVED":
                total_amount += payment.amount
                mode = payment.payment_mode.upper() if payment.payment_mode else "NEFT"
                if mode in by_format:
                    by_format[mode]["count"] += 1
                    by_format[mode]["amount"] += payment.amount

        return PaymentFileSummary(
            total_payments=len(payment_ids),
            total_amount=total_amount,
            by_format=by_format,
            eligible_for_generation=len(payment_ids) - len(already_in_file),
            already_in_file=len(already_in_file),
        )

    async def cancel_file(self, id: UUID) -> Optional[PaymentFile]:
        """Cancel a payment file (only if not yet uploaded)."""
        payment_file = await self.repository.get(id)
        if not payment_file:
            return None

        if payment_file.status in ["UPLOADED", "PROCESSING", "COMPLETED", "PARTIALLY_COMPLETED"]:
            raise ValueError("Cannot cancel file that is already uploaded or processed")

        return await self.repository.update(
            id,
            {
                "status": "CANCELLED",
                "is_active": False,
            }
        )

    def to_response(self, payment_file: PaymentFile) -> PaymentFileResponse:
        """Convert to response schema."""
        return PaymentFileResponse(
            id=payment_file.id,
            organization_id=payment_file.organization_id,
            organization_bank_account_id=payment_file.organization_bank_account_id,
            file_reference=payment_file.file_reference,
            file_format=PaymentFileFormat(payment_file.file_format),
            payment_date=payment_file.payment_date,
            status=PaymentFileStatus(payment_file.status),
            total_transactions=payment_file.total_transactions,
            total_amount=payment_file.total_amount,
            successful_count=payment_file.successful_count,
            failed_count=payment_file.failed_count,
            file_generated_at=payment_file.file_generated_at,
            file_downloaded_at=payment_file.file_downloaded_at,
            file_uploaded_at=payment_file.file_uploaded_at,
            processing_started_at=payment_file.processing_started_at,
            processing_completed_at=payment_file.processing_completed_at,
            description=payment_file.description,
            created_at=payment_file.created_at,
            created_by=payment_file.created_by,
        )
