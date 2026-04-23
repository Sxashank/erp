"""Base classes for communication providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID


class CommunicationChannel(str, Enum):
    """Communication channels."""
    SMS = "SMS"
    EMAIL = "EMAIL"
    PUSH = "PUSH"
    WHATSAPP = "WHATSAPP"


class MessageStatus(str, Enum):
    """Message delivery status."""
    PENDING = "PENDING"
    QUEUED = "QUEUED"
    SENT = "SENT"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
    REJECTED = "REJECTED"
    BOUNCED = "BOUNCED"
    OPENED = "OPENED"
    CLICKED = "CLICKED"


class MessagePriority(str, Enum):
    """Message priority levels."""
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class Recipient:
    """Message recipient."""
    identifier: str  # Phone number, email, or device token
    name: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Attachment:
    """Message attachment."""
    filename: str
    content: bytes
    content_type: str
    size_bytes: int


@dataclass
class CommunicationRequest:
    """Base communication request."""
    channel: CommunicationChannel
    recipients: List[Recipient]
    template_id: Optional[str] = None
    template_params: Dict[str, Any] = field(default_factory=dict)
    content: Optional[str] = None
    subject: Optional[str] = None  # For email
    attachments: List[Attachment] = field(default_factory=list)
    priority: MessagePriority = MessagePriority.NORMAL
    scheduled_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    # Tracking
    reference_id: Optional[str] = None
    organization_id: Optional[UUID] = None
    entity_type: Optional[str] = None  # e.g., "loan_account", "legal_case"
    entity_id: Optional[UUID] = None


@dataclass
class CommunicationResult:
    """Result of a communication attempt."""
    success: bool
    message_id: Optional[str] = None
    provider_message_id: Optional[str] = None
    status: MessageStatus = MessageStatus.PENDING
    recipient: Optional[str] = None
    channel: Optional[CommunicationChannel] = None
    cost: Optional[float] = None
    credits_used: Optional[int] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None


class CommunicationError(Exception):
    """Communication error."""

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        provider: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.code = code
        self.provider = provider
        self.details = details or {}


class CommunicationProvider(ABC):
    """Abstract base class for communication providers."""

    provider_name: str = "base"
    channel: CommunicationChannel

    def __init__(self, config: Dict[str, Any]):
        """Initialize provider with configuration."""
        self.config = config
        self._validate_config()

    @abstractmethod
    def _validate_config(self) -> None:
        """Validate provider configuration."""
        pass

    @abstractmethod
    async def send(self, request: CommunicationRequest) -> List[CommunicationResult]:
        """Send message to recipients."""
        pass

    @abstractmethod
    async def get_status(self, message_id: str) -> CommunicationResult:
        """Get delivery status of a message."""
        pass

    @abstractmethod
    async def get_balance(self) -> Dict[str, Any]:
        """Get account balance/credits."""
        pass

    async def validate_recipient(self, recipient: Recipient) -> bool:
        """Validate recipient identifier."""
        return True

    async def health_check(self) -> bool:
        """Check if provider is healthy."""
        try:
            await self.get_balance()
            return True
        except Exception:
            return False
