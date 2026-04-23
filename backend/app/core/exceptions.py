"""Custom application exceptions."""

from typing import Any, Dict, Optional

from fastapi import HTTPException, status


class AppException(HTTPException):
    """Base application exception."""

    def __init__(
        self,
        status_code: int,
        detail: str,
        headers: Optional[Dict[str, str]] = None,
        error_code: Optional[str] = None,
    ) -> None:
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.error_code = error_code


class NotFoundException(AppException):
    """Resource not found exception."""

    def __init__(
        self,
        detail: str = "Resource not found",
        error_code: str = "NOT_FOUND",
    ) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_code=error_code,
        )


class UnauthorizedException(AppException):
    """Unauthorized access exception."""

    def __init__(
        self,
        detail: str = "Could not validate credentials",
        error_code: str = "UNAUTHORIZED",
    ) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
            error_code=error_code,
        )


class ForbiddenException(AppException):
    """Forbidden access exception."""

    def __init__(
        self,
        detail: str = "Not enough permissions",
        error_code: str = "FORBIDDEN",
    ) -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code=error_code,
        )


class BadRequestException(AppException):
    """Bad request exception."""

    def __init__(
        self,
        detail: str = "Bad request",
        error_code: str = "BAD_REQUEST",
    ) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code=error_code,
        )


class ConflictException(AppException):
    """Conflict exception (e.g., duplicate resource)."""

    def __init__(
        self,
        detail: str = "Resource already exists",
        error_code: str = "CONFLICT",
    ) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
            error_code=error_code,
        )


class ConcurrencyConflictError(ConflictException):
    """Raised when optimistic lock detects concurrent modification.

    This exception indicates that another user has modified the record
    since it was last read. The client should refresh and retry.
    """

    def __init__(
        self,
        entity: str,
        entity_id: str,
    ) -> None:
        self.entity = entity
        self.entity_id = entity_id
        super().__init__(
            detail=f"{entity} was modified by another user. Please refresh and try again.",
            error_code="CONCURRENCY_CONFLICT",
        )


class ValidationException(AppException):
    """Validation error exception."""

    def __init__(
        self,
        detail: str = "Validation error",
        errors: Optional[list[Dict[str, Any]]] = None,
        error_code: str = "VALIDATION_ERROR",
    ) -> None:
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            error_code=error_code,
        )
        self.errors = errors or []


class AccountLockedException(AppException):
    """Account locked exception."""

    def __init__(
        self,
        detail: str = "Account is locked due to too many failed login attempts",
        error_code: str = "ACCOUNT_LOCKED",
    ) -> None:
        super().__init__(
            status_code=status.HTTP_423_LOCKED,
            detail=detail,
            error_code=error_code,
        )


class PasswordExpiredException(AppException):
    """Password expired exception."""

    def __init__(
        self,
        detail: str = "Password has expired. Please reset your password.",
        error_code: str = "PASSWORD_EXPIRED",
    ) -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code=error_code,
        )


# ============================================
# Fixed Assets Module Exceptions
# ============================================

class AssetNotFoundError(AppException):
    """Fixed asset not found."""

    def __init__(
        self,
        asset_id: Optional[str] = None,
        detail: Optional[str] = None,
    ) -> None:
        message = detail or f"Asset not found: {asset_id}" if asset_id else "Asset not found"
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=message,
            error_code="ASSET_NOT_FOUND",
        )


class ClosedPeriodError(AppException):
    """Transaction in closed financial period."""

    def __init__(
        self,
        period: Optional[str] = None,
        detail: Optional[str] = None,
    ) -> None:
        message = detail or f"Cannot post to closed period: {period}" if period else "Cannot post to closed period"
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
            error_code="CLOSED_PERIOD",
        )


class GLPostingFailedError(AppException):
    """GL posting failed."""

    def __init__(
        self,
        detail: str = "GL posting failed",
        voucher_id: Optional[str] = None,
    ) -> None:
        message = f"{detail}. Voucher: {voucher_id}" if voucher_id else detail
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=message,
            error_code="GL_POSTING_FAILED",
        )


class ApprovalRequiredError(AppException):
    """Action requires approval."""

    def __init__(
        self,
        workflow_type: Optional[str] = None,
        detail: Optional[str] = None,
    ) -> None:
        message = detail or f"Approval required for: {workflow_type}" if workflow_type else "Approval required"
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=message,
            error_code="APPROVAL_REQUIRED",
        )


class InsufficientApprovalError(AppException):
    """Insufficient approval level."""

    def __init__(
        self,
        required_level: Optional[int] = None,
        current_level: Optional[int] = None,
        detail: Optional[str] = None,
    ) -> None:
        if detail:
            message = detail
        elif required_level and current_level:
            message = f"Insufficient approval: current level {current_level}, required {required_level}"
        else:
            message = "Insufficient approval"
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=message,
            error_code="INSUFFICIENT_APPROVAL",
        )


class ConcurrentModificationError(AppException):
    """Record modified by another user."""

    def __init__(
        self,
        detail: str = "Record was modified by another user. Please refresh and try again.",
    ) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
            error_code="CONCURRENT_MODIFICATION",
        )


class DepreciationAlreadyRunError(AppException):
    """Depreciation already run for period."""

    def __init__(
        self,
        period: Optional[str] = None,
        detail: Optional[str] = None,
    ) -> None:
        message = detail or f"Depreciation already run for period: {period}" if period else "Depreciation already run"
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
            error_code="DEPRECIATION_ALREADY_RUN",
        )


class InvalidAssetStatusError(AppException):
    """Invalid asset status for operation."""

    def __init__(
        self,
        current_status: Optional[str] = None,
        required_status: Optional[str] = None,
        detail: Optional[str] = None,
    ) -> None:
        if detail:
            message = detail
        elif current_status and required_status:
            message = f"Invalid status: {current_status}. Required: {required_status}"
        else:
            message = "Invalid asset status for this operation"
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
            error_code="INVALID_ASSET_STATUS",
        )


class LeaseAccountingError(AppException):
    """Lease accounting error."""

    def __init__(
        self,
        detail: str = "Lease accounting error",
        lease_id: Optional[str] = None,
    ) -> None:
        message = f"{detail}. Lease: {lease_id}" if lease_id else detail
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
            error_code="LEASE_ACCOUNTING_ERROR",
        )


class InsuranceClaimError(AppException):
    """Insurance claim processing error."""

    def __init__(
        self,
        detail: str = "Insurance claim error",
        claim_id: Optional[str] = None,
    ) -> None:
        message = f"{detail}. Claim: {claim_id}" if claim_id else detail
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
            error_code="INSURANCE_CLAIM_ERROR",
        )
