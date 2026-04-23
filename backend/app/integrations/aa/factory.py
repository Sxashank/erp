"""Factory for creating Account Aggregator clients."""

import logging
from typing import Any, Dict, List, Type

from app.integrations.aa.base import AAClientBase
from app.integrations.aa.finvu import FinvuAAClient
from app.integrations.aa.setu import SetuAAClient
from app.integrations.aa.onemoney import OneMoneyAAClient

logger = logging.getLogger(__name__)


class AAClientFactory:
    """Factory for creating AA clients based on provider."""

    CLIENTS: Dict[str, Type[AAClientBase]] = {
        "FINVU": FinvuAAClient,
        "SETU": SetuAAClient,
        "ONEMONEY": OneMoneyAAClient,
        # Future providers
        # "NADL": NADLAAClient,
        # "CAMS_FINSERV": CamsFinservAAClient,
        # "PERFIOS": PerfiosAAClient,
    }

    @classmethod
    def create(
        cls,
        provider: str,
        config: Dict[str, Any],
        sandbox_mode: bool = True,
    ) -> AAClientBase:
        """Create an AA client for the given provider.

        Args:
            provider: Provider identifier (FINVU, SETU, ONEMONEY, etc.)
            config: Provider-specific configuration
            sandbox_mode: Whether to use sandbox environment

        Returns:
            AAClientBase implementation

        Raises:
            ValueError: If provider is not supported
        """
        provider_upper = provider.upper()
        client_class = cls.CLIENTS.get(provider_upper)

        if not client_class:
            raise ValueError(
                f"Unsupported AA provider: {provider}. "
                f"Supported providers: {', '.join(cls.CLIENTS.keys())}"
            )

        logger.info(f"Creating AA client for provider: {provider}")
        return client_class(config, sandbox_mode)

    @classmethod
    def get_supported_providers(cls) -> List[str]:
        """Get list of supported AA providers."""
        return list(cls.CLIENTS.keys())

    @classmethod
    def is_supported(cls, provider: str) -> bool:
        """Check if a provider is supported.

        Args:
            provider: Provider identifier

        Returns:
            True if provider is supported
        """
        return provider.upper() in cls.CLIENTS

    @classmethod
    def get_provider_config_schema(cls, provider: str) -> Dict[str, Any]:
        """Get the expected configuration schema for a provider.

        Args:
            provider: Provider identifier

        Returns:
            Dict describing required configuration fields
        """
        # Common fields for all providers
        common_schema = {
            "client_id": {
                "type": "string",
                "required": True,
                "description": "FIU client ID provided by AA",
            },
            "client_secret": {
                "type": "string",
                "required": True,
                "secret": True,
                "description": "FIU client secret",
            },
            "entity_id": {
                "type": "string",
                "required": True,
                "description": "FIU entity ID registered with AA",
            },
            "callback_url": {
                "type": "string",
                "required": True,
                "description": "Webhook callback URL for consent/FI notifications",
            },
            "webhook_secret": {
                "type": "string",
                "required": False,
                "secret": True,
                "description": "Secret for webhook signature verification",
            },
        }

        provider_upper = provider.upper()

        # Provider-specific fields
        if provider_upper == "FINVU":
            return {
                **common_schema,
                "sandbox_url": {
                    "type": "string",
                    "required": False,
                    "default": "https://fiu-uat.finvu.in/api",
                    "description": "Finvu sandbox API URL",
                },
                "api_base_url": {
                    "type": "string",
                    "required": False,
                    "default": "https://fiu.finvu.in/api",
                    "description": "Finvu production API URL",
                },
            }

        elif provider_upper == "SETU":
            return {
                **common_schema,
                "product_instance_id": {
                    "type": "string",
                    "required": True,
                    "description": "Setu product instance ID",
                },
                "sandbox_url": {
                    "type": "string",
                    "required": False,
                    "default": "https://fiu-sandbox.setu.co",
                    "description": "Setu sandbox API URL",
                },
                "api_base_url": {
                    "type": "string",
                    "required": False,
                    "default": "https://fiu.setu.co",
                    "description": "Setu production API URL",
                },
            }

        elif provider_upper == "ONEMONEY":
            return {
                **common_schema,
                "sandbox_url": {
                    "type": "string",
                    "required": False,
                    "default": "https://sandbox.onemoney.in/v2",
                    "description": "OneMoney sandbox API URL",
                },
                "api_base_url": {
                    "type": "string",
                    "required": False,
                    "default": "https://api.onemoney.in/v2",
                    "description": "OneMoney production API URL",
                },
            }

        return common_schema
