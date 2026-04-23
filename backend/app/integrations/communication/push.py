"""Push notification provider implementations."""

import json
from abc import ABC
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx

from app.integrations.communication.base import (
    CommunicationChannel,
    CommunicationError,
    CommunicationProvider,
    CommunicationRequest,
    CommunicationResult,
    MessageStatus,
    Recipient,
)


class PushProvider(CommunicationProvider, ABC):
    """Base class for push notification providers."""

    channel = CommunicationChannel.PUSH


class FirebasePushProvider(PushProvider):
    """Firebase Cloud Messaging (FCM) push notification provider."""

    provider_name = "firebase_fcm"

    def _validate_config(self) -> None:
        """Validate Firebase configuration."""
        # Either use server key (legacy) or service account (v1 API)
        if "server_key" not in self.config and "service_account" not in self.config:
            raise CommunicationError(
                "Missing required config: server_key or service_account",
                code="CONFIG_ERROR",
                provider=self.provider_name,
            )

    def _get_access_token(self) -> str:
        """Get OAuth 2.0 access token for FCM v1 API."""
        if "server_key" in self.config:
            return self.config["server_key"]

        # For service account, use google-auth library
        # from google.oauth2 import service_account
        # credentials = service_account.Credentials.from_service_account_info(...)
        # credentials.refresh(Request())
        # return credentials.token

        return ""

    async def send(self, request: CommunicationRequest) -> List[CommunicationResult]:
        """Send push notification via FCM."""
        results = []
        use_legacy = "server_key" in self.config

        if use_legacy:
            return await self._send_legacy(request)
        else:
            return await self._send_v1(request)

    async def _send_legacy(
        self, request: CommunicationRequest
    ) -> List[CommunicationResult]:
        """Send using legacy FCM HTTP API."""
        results = []
        server_key = self.config["server_key"]
        base_url = "https://fcm.googleapis.com/fcm"

        # Build notification payload
        notification = {
            "title": request.subject or "Notification",
            "body": request.content or "",
        }

        # Add custom data
        data = request.template_params.copy() if request.template_params else {}
        if request.metadata:
            data.update(request.metadata)

        # Determine if multicast or single
        device_tokens = [r.identifier for r in request.recipients]

        if len(device_tokens) == 1:
            payload = {
                "to": device_tokens[0],
                "notification": notification,
                "data": data,
            }
        else:
            payload = {
                "registration_ids": device_tokens,
                "notification": notification,
                "data": data,
            }

        # Add priority
        if request.priority:
            priority_map = {
                "LOW": "normal",
                "NORMAL": "normal",
                "HIGH": "high",
                "CRITICAL": "high",
            }
            payload["priority"] = priority_map.get(request.priority.value, "normal")

        headers = {
            "Authorization": f"key={server_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{base_url}/send",
                    json=payload,
                    headers=headers,
                    timeout=30.0,
                )

                data = response.json()

                if response.status_code == 200:
                    if data.get("success", 0) > 0:
                        # Process individual results
                        fcm_results = data.get("results", [])
                        for i, recipient in enumerate(request.recipients):
                            if i < len(fcm_results):
                                fcm_result = fcm_results[i]
                                if "message_id" in fcm_result:
                                    results.append(
                                        CommunicationResult(
                                            success=True,
                                            message_id=fcm_result.get("message_id"),
                                            provider_message_id=data.get("multicast_id"),
                                            status=MessageStatus.SENT,
                                            recipient=recipient.identifier,
                                            channel=self.channel,
                                            sent_at=datetime.utcnow(),
                                        )
                                    )
                                else:
                                    results.append(
                                        CommunicationResult(
                                            success=False,
                                            status=MessageStatus.FAILED,
                                            recipient=recipient.identifier,
                                            channel=self.channel,
                                            error_code=fcm_result.get("error"),
                                            error_message=fcm_result.get("error"),
                                        )
                                    )
                    else:
                        for recipient in request.recipients:
                            results.append(
                                CommunicationResult(
                                    success=False,
                                    status=MessageStatus.FAILED,
                                    recipient=recipient.identifier,
                                    channel=self.channel,
                                    error_message="FCM send failed",
                                )
                            )
                else:
                    for recipient in request.recipients:
                        results.append(
                            CommunicationResult(
                                success=False,
                                status=MessageStatus.FAILED,
                                recipient=recipient.identifier,
                                channel=self.channel,
                                error_code=str(response.status_code),
                                error_message=str(data),
                            )
                        )

        except Exception as e:
            raise CommunicationError(
                f"FCM error: {str(e)}",
                code="PROVIDER_ERROR",
                provider=self.provider_name,
            )

        return results

    async def _send_v1(self, request: CommunicationRequest) -> List[CommunicationResult]:
        """Send using FCM v1 HTTP API."""
        results = []
        project_id = self.config.get("project_id", "")
        base_url = f"https://fcm.googleapis.com/v1/projects/{project_id}/messages:send"

        # Get access token (would use google-auth in production)
        access_token = self._get_access_token()

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        for recipient in request.recipients:
            # Build v1 message
            message = {
                "message": {
                    "token": recipient.identifier,
                    "notification": {
                        "title": request.subject or "Notification",
                        "body": request.content or "",
                    },
                }
            }

            # Add data payload
            if request.template_params or request.metadata:
                data = {}
                if request.template_params:
                    data.update(request.template_params)
                if request.metadata:
                    data.update(request.metadata)
                # FCM v1 requires all data values to be strings
                message["message"]["data"] = {
                    k: str(v) for k, v in data.items()
                }

            # Add Android-specific config
            message["message"]["android"] = {
                "priority": "high" if request.priority and request.priority.value in ["HIGH", "CRITICAL"] else "normal",
            }

            # Add iOS-specific config (APNs)
            message["message"]["apns"] = {
                "payload": {
                    "aps": {
                        "sound": "default",
                    }
                }
            }

            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        base_url,
                        json=message,
                        headers=headers,
                        timeout=30.0,
                    )

                    data = response.json()

                    if response.status_code == 200:
                        results.append(
                            CommunicationResult(
                                success=True,
                                message_id=data.get("name"),
                                provider_message_id=data.get("name"),
                                status=MessageStatus.SENT,
                                recipient=recipient.identifier,
                                channel=self.channel,
                                sent_at=datetime.utcnow(),
                            )
                        )
                    else:
                        results.append(
                            CommunicationResult(
                                success=False,
                                status=MessageStatus.FAILED,
                                recipient=recipient.identifier,
                                channel=self.channel,
                                error_code=str(data.get("error", {}).get("code")),
                                error_message=data.get("error", {}).get("message"),
                            )
                        )

            except Exception as e:
                results.append(
                    CommunicationResult(
                        success=False,
                        status=MessageStatus.FAILED,
                        recipient=recipient.identifier,
                        channel=self.channel,
                        error_message=str(e),
                    )
                )

        return results

    async def get_status(self, message_id: str) -> CommunicationResult:
        """FCM doesn't provide message status API - use delivery receipts."""
        return CommunicationResult(
            success=True,
            message_id=message_id,
            status=MessageStatus.SENT,
            metadata={
                "note": "FCM does not provide delivery status API. Use delivery receipts."
            },
        )

    async def get_balance(self) -> Dict[str, Any]:
        """FCM is free - no balance concept."""
        return {
            "provider": self.provider_name,
            "note": "FCM is free with no message limits",
        }

    async def validate_token(self, token: str) -> bool:
        """Validate if a device token is valid."""
        # Send a dry_run message to validate token
        if "server_key" in self.config:
            server_key = self.config["server_key"]
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        "https://fcm.googleapis.com/fcm/send",
                        json={
                            "to": token,
                            "dry_run": True,
                        },
                        headers={
                            "Authorization": f"key={server_key}",
                            "Content-Type": "application/json",
                        },
                        timeout=10.0,
                    )
                    data = response.json()
                    return data.get("success", 0) > 0
            except Exception:
                return False
        return True

    async def subscribe_to_topic(
        self, tokens: List[str], topic: str
    ) -> Dict[str, Any]:
        """Subscribe device tokens to a topic."""
        server_key = self.config.get("server_key", "")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://iid.googleapis.com/iid/v1:batchAdd",
                    json={
                        "to": f"/topics/{topic}",
                        "registration_tokens": tokens,
                    },
                    headers={
                        "Authorization": f"key={server_key}",
                        "Content-Type": "application/json",
                    },
                    timeout=30.0,
                )
                return response.json()
        except Exception as e:
            raise CommunicationError(
                f"Failed to subscribe to topic: {str(e)}",
                code="TOPIC_ERROR",
                provider=self.provider_name,
            )

    async def unsubscribe_from_topic(
        self, tokens: List[str], topic: str
    ) -> Dict[str, Any]:
        """Unsubscribe device tokens from a topic."""
        server_key = self.config.get("server_key", "")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://iid.googleapis.com/iid/v1:batchRemove",
                    json={
                        "to": f"/topics/{topic}",
                        "registration_tokens": tokens,
                    },
                    headers={
                        "Authorization": f"key={server_key}",
                        "Content-Type": "application/json",
                    },
                    timeout=30.0,
                )
                return response.json()
        except Exception as e:
            raise CommunicationError(
                f"Failed to unsubscribe from topic: {str(e)}",
                code="TOPIC_ERROR",
                provider=self.provider_name,
            )
