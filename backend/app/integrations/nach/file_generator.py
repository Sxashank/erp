"""NACH ACH file generator for NPCI format."""

import hashlib
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import List, Optional, Tuple
from uuid import UUID

from app.integrations.nach.schemas import (
    NachDebitRecord,
    NachHeaderRecord,
    NachTrailerRecord,
    NachResponseRecord,
)
from app.models.lending.enums import NachFileFormat


class NachFileGenerator:
    """Generator for NACH ACH format files."""

    def __init__(
        self,
        sponsor_bank_ifsc: str,
        utility_code: str,
        output_directory: str = "/tmp/nach_files",
    ):
        """Initialize the NACH file generator.

        Args:
            sponsor_bank_ifsc: IFSC code of the sponsor bank
            utility_code: Utility code assigned by NPCI
            output_directory: Directory to store generated files
        """
        self.sponsor_bank_ifsc = sponsor_bank_ifsc
        self.utility_code = utility_code
        self.output_directory = Path(output_directory)
        self.output_directory.mkdir(parents=True, exist_ok=True)

    def generate_debit_file(
        self,
        batch_reference: str,
        debit_date: date,
        transactions: List[dict],
    ) -> Tuple[str, str, str, int, Decimal]:
        """Generate NACH debit file.

        Args:
            batch_reference: Unique batch reference
            debit_date: Date of debit
            transactions: List of transaction dictionaries with keys:
                - transaction_reference
                - umrn
                - account_number
                - ifsc_code
                - account_holder_name
                - bank_name (optional)
                - amount
                - narration (optional)

        Returns:
            Tuple of (file_name, file_path, checksum, total_count, total_amount)
        """
        # Create header record
        now = datetime.now()
        total_amount = Decimal("0")
        debit_records = []

        # Process transactions
        for txn in transactions:
            amount = Decimal(str(txn["amount"]))
            total_amount += amount

            record = NachDebitRecord(
                transaction_reference=txn["transaction_reference"],
                umrn=txn["umrn"],
                account_number=txn["account_number"],
                ifsc_code=txn["ifsc_code"],
                account_holder_name=txn["account_holder_name"],
                bank_name=txn.get("bank_name"),
                amount=amount,
                debit_date=debit_date,
                sponsor_bank_ifsc=self.sponsor_bank_ifsc,
                utility_code=self.utility_code,
                narration=txn.get("narration", "EMI DEBIT"),
            )
            debit_records.append(record)

        # Create header
        header = NachHeaderRecord(
            file_creation_date=now.date(),
            file_creation_time=now.strftime("%H:%M"),
            sponsor_bank_ifsc=self.sponsor_bank_ifsc,
            utility_code=self.utility_code,
            batch_reference=batch_reference,
            debit_date=debit_date,
            total_count=len(debit_records),
            total_amount=total_amount,
        )

        # Create trailer
        trailer = NachTrailerRecord(
            total_count=len(debit_records),
            total_amount=total_amount,
        )

        # Generate file content
        lines = [header.to_ach_line()]
        for record in debit_records:
            lines.append(record.to_ach_line())
        lines.append(trailer.to_ach_line())

        content = "\n".join(lines)

        # Generate file name
        file_name = f"NACH_DR_{batch_reference}_{debit_date.strftime('%Y%m%d')}.txt"
        file_path = self.output_directory / file_name

        # Write file
        with open(file_path, "w") as f:
            f.write(content)

        # Calculate checksum
        checksum = hashlib.sha256(content.encode()).hexdigest()

        return file_name, str(file_path), checksum, len(debit_records), total_amount

    def parse_response_file(
        self,
        file_path: str,
    ) -> Tuple[List[NachResponseRecord], List[str]]:
        """Parse NACH response file.

        Args:
            file_path: Path to the response file

        Returns:
            Tuple of (records, errors)
        """
        records = []
        errors = []

        with open(file_path, "r") as f:
            lines = f.readlines()

        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            # Skip header and trailer
            if line[0] in ("H", "T"):
                continue

            try:
                record = NachResponseRecord.from_ach_line(line)
                records.append(record)
            except Exception as e:
                errors.append(f"Line {i + 1}: {str(e)}")

        return records, errors

    def generate_mandate_registration_file(
        self,
        batch_reference: str,
        mandates: List[dict],
    ) -> Tuple[str, str, str]:
        """Generate mandate registration file.

        Args:
            batch_reference: Unique batch reference
            mandates: List of mandate dictionaries

        Returns:
            Tuple of (file_name, file_path, checksum)
        """
        # Mandate registration format varies by provider
        # This is a simplified implementation
        lines = []

        for mandate in mandates:
            line_parts = [
                "M",  # Mandate record
                mandate["mandate_reference"].ljust(30),
                mandate["account_number"].ljust(35),
                mandate["ifsc_code"].ljust(11),
                mandate["account_holder_name"].ljust(40)[:40],
                mandate["start_date"].strftime("%d%m%Y"),
                mandate["end_date"].strftime("%d%m%Y"),
                str(int(mandate["max_amount"] * 100)).zfill(13),
                mandate.get("frequency", "M").ljust(1),
                self.utility_code.ljust(18),
                self.sponsor_bank_ifsc.ljust(11),
            ]
            lines.append("".join(line_parts))

        content = "\n".join(lines)

        file_name = f"NACH_MANDATE_{batch_reference}_{datetime.now().strftime('%Y%m%d%H%M%S')}.txt"
        file_path = self.output_directory / file_name

        with open(file_path, "w") as f:
            f.write(content)

        checksum = hashlib.sha256(content.encode()).hexdigest()

        return file_name, str(file_path), checksum


class NachFileValidator:
    """Validator for NACH files."""

    @staticmethod
    def validate_account_number(account_number: str) -> bool:
        """Validate bank account number format."""
        # Account number should be alphanumeric, 9-18 digits
        if not account_number:
            return False
        clean = account_number.strip()
        return len(clean) >= 9 and len(clean) <= 18 and clean.replace(" ", "").isalnum()

    @staticmethod
    def validate_ifsc(ifsc: str) -> bool:
        """Validate IFSC code format."""
        # IFSC: 4 letters + 0 + 6 alphanumeric
        if not ifsc or len(ifsc) != 11:
            return False
        return ifsc[:4].isalpha() and ifsc[4] == "0" and ifsc[5:].isalnum()

    @staticmethod
    def validate_umrn(umrn: str) -> bool:
        """Validate UMRN format."""
        # UMRN format varies, generally 10-20 characters
        if not umrn:
            return False
        return len(umrn) >= 10 and len(umrn) <= 20

    @staticmethod
    def validate_amount(amount: Decimal, max_amount: Decimal) -> Tuple[bool, Optional[str]]:
        """Validate debit amount against mandate limit."""
        if amount <= 0:
            return False, "Amount must be positive"
        if amount > max_amount:
            return False, f"Amount {amount} exceeds mandate limit {max_amount}"
        return True, None

    @classmethod
    def validate_transaction(cls, transaction: dict, mandate_max_amount: Decimal) -> Tuple[bool, List[str]]:
        """Validate a complete transaction record."""
        errors = []

        if not cls.validate_account_number(transaction.get("account_number", "")):
            errors.append("Invalid account number")

        if not cls.validate_ifsc(transaction.get("ifsc_code", "")):
            errors.append("Invalid IFSC code")

        if not cls.validate_umrn(transaction.get("umrn", "")):
            errors.append("Invalid UMRN")

        amount = transaction.get("amount", Decimal("0"))
        valid, msg = cls.validate_amount(amount, mandate_max_amount)
        if not valid:
            errors.append(msg)

        return len(errors) == 0, errors
