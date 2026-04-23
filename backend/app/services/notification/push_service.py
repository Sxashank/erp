"""Push notification service for mobile and web push notifications."""

import logging
from typing import Optional, List
from uuid import UUID

from app.config import settings

logger = logging.getLogger(__name__)


class PushService:
    """Service for sending push notifications."""

    def __init__(self):
        """Initialize push notification service."""
        self.enabled = getattr(settings, 'PUSH_ENABLED', False)
        self.provider = getattr(settings, 'PUSH_PROVIDER', 'firebase')
        self.fcm_server_key = getattr(settings, 'FCM_SERVER_KEY', '')
        self.fcm_project_id = getattr(settings, 'FCM_PROJECT_ID', '')

    async def send_push(
        self,
        user_id: UUID,
        title: str,
        body: str,
        data: Optional[dict] = None,
        image_url: Optional[str] = None,
        action_url: Optional[str] = None,
    ) -> bool:
        """
        Send push notification to a user.

        Args:
            user_id: Target user ID
            title: Notification title
            body: Notification body
            data: Additional data payload
            image_url: Optional image URL
            action_url: URL to open when notification is clicked

        Returns:
            True if notification was sent successfully
        """
        if not self.enabled:
            logger.info(
                f"Push notification disabled. Would have sent to user {user_id}: {title}"
            )
            return True

        # Get user's device tokens
        tokens = await self._get_user_tokens(user_id)
        if not tokens:
            logger.warning(f"No device tokens found for user {user_id}")
            return False

        try:
            if self.provider == 'firebase':
                return await self._send_via_fcm(tokens, title, body, data, image_url)
            else:
                logger.error(f"Unknown push provider: {self.provider}")
                return False

        except Exception as e:
            logger.error(f"Error sending push notification: {e}")
            return False

    async def _send_via_fcm(
        self,
        tokens: List[str],
        title: str,
        body: str,
        data: Optional[dict],
        image_url: Optional[str],
    ) -> bool:
        """Send push notification via Firebase Cloud Messaging."""
        try:
            import httpx

            url = "https://fcm.googleapis.com/fcm/send"
            headers = {
                "Authorization": f"key={self.fcm_server_key}",
                "Content-Type": "application/json",
            }

            notification_payload = {
                "title": title,
                "body": body,
            }
            if image_url:
                notification_payload["image"] = image_url

            # Send to each token
            for token in tokens:
                payload = {
                    "to": token,
                    "notification": notification_payload,
                    "data": data or {},
                }

                async with httpx.AsyncClient() as client:
                    response = await client.post(url, json=payload, headers=headers)
                    response.raise_for_status()

            logger.info(f"FCM push sent to {len(tokens)} devices: {title}")
            return True

        except Exception as e:
            logger.error(f"FCM push error: {e}")
            return False

    async def send_to_tokens(
        self,
        tokens: List[str],
        title: str,
        body: str,
        data: Optional[dict] = None,
        image_url: Optional[str] = None,
    ) -> dict:
        """
        Send push notification to specific device tokens.

        Args:
            tokens: List of device tokens
            title: Notification title
            body: Notification body
            data: Additional data payload
            image_url: Optional image URL

        Returns:
            Dict with success/failed counts
        """
        if not self.enabled:
            logger.info(f"Push disabled. Would have sent to {len(tokens)} tokens")
            return {"success": len(tokens), "failed": 0}

        results = {"success": 0, "failed": 0, "errors": []}

        if self.provider == 'firebase':
            # FCM supports multicast
            success = await self._send_via_fcm(tokens, title, body, data, image_url)
            if success:
                results["success"] = len(tokens)
            else:
                results["failed"] = len(tokens)

        return results

    async def send_to_topic(
        self,
        topic: str,
        title: str,
        body: str,
        data: Optional[dict] = None,
        image_url: Optional[str] = None,
    ) -> bool:
        """
        Send push notification to a topic (FCM topic messaging).

        Args:
            topic: Topic name (e.g., "announcements", "org_123")
            title: Notification title
            body: Notification body
            data: Additional data payload
            image_url: Optional image URL

        Returns:
            True if notification was sent successfully
        """
        if not self.enabled:
            logger.info(f"Push disabled. Would have sent to topic {topic}: {title}")
            return True

        if self.provider != 'firebase':
            logger.error("Topic messaging only supported with Firebase")
            return False

        try:
            import httpx

            url = "https://fcm.googleapis.com/fcm/send"
            headers = {
                "Authorization": f"key={self.fcm_server_key}",
                "Content-Type": "application/json",
            }

            notification_payload = {
                "title": title,
                "body": body,
            }
            if image_url:
                notification_payload["image"] = image_url

            payload = {
                "to": f"/topics/{topic}",
                "notification": notification_payload,
                "data": data or {},
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()

            logger.info(f"FCM topic push sent to {topic}: {title}")
            return True

        except Exception as e:
            logger.error(f"FCM topic push error: {e}")
            return False

    async def _get_user_tokens(self, user_id: UUID) -> List[str]:
        """
        Get device tokens for a user.

        This would typically query a database table storing device registrations.
        For now, returns empty list as placeholder.
        """
        # TODO: Implement device token retrieval from database
        # Example:
        # result = await self.db.execute(
        #     select(DeviceToken.token).where(
        #         DeviceToken.user_id == user_id,
        #         DeviceToken.is_active == True,
        #     )
        # )
        # return [row[0] for row in result.all()]
        return []

    async def register_device(
        self,
        user_id: UUID,
        token: str,
        device_type: str,
        device_name: Optional[str] = None,
    ) -> bool:
        """
        Register a device token for push notifications.

        Args:
            user_id: User ID
            token: Device token (FCM token)
            device_type: Device type (ios, android, web)
            device_name: Optional device name

        Returns:
            True if registration successful
        """
        # TODO: Store device token in database
        logger.info(f"Device registered for user {user_id}: {device_type}")
        return True

    async def unregister_device(
        self,
        user_id: UUID,
        token: str,
    ) -> bool:
        """
        Unregister a device token.

        Args:
            user_id: User ID
            token: Device token to remove

        Returns:
            True if unregistration successful
        """
        # TODO: Remove device token from database
        logger.info(f"Device unregistered for user {user_id}")
        return True

    async def subscribe_to_topic(
        self,
        tokens: List[str],
        topic: str,
    ) -> bool:
        """
        Subscribe device tokens to a topic.

        Args:
            tokens: List of device tokens
            topic: Topic to subscribe to

        Returns:
            True if subscription successful
        """
        if not self.enabled or self.provider != 'firebase':
            return True

        try:
            import httpx

            url = f"https://iid.googleapis.com/iid/v1:batchAdd"
            headers = {
                "Authorization": f"key={self.fcm_server_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "to": f"/topics/{topic}",
                "registration_tokens": tokens,
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()

            logger.info(f"Subscribed {len(tokens)} devices to topic {topic}")
            return True

        except Exception as e:
            logger.error(f"FCM topic subscription error: {e}")
            return False

    async def unsubscribe_from_topic(
        self,
        tokens: List[str],
        topic: str,
    ) -> bool:
        """
        Unsubscribe device tokens from a topic.

        Args:
            tokens: List of device tokens
            topic: Topic to unsubscribe from

        Returns:
            True if unsubscription successful
        """
        if not self.enabled or self.provider != 'firebase':
            return True

        try:
            import httpx

            url = f"https://iid.googleapis.com/iid/v1:batchRemove"
            headers = {
                "Authorization": f"key={self.fcm_server_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "to": f"/topics/{topic}",
                "registration_tokens": tokens,
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()

            logger.info(f"Unsubscribed {len(tokens)} devices from topic {topic}")
            return True

        except Exception as e:
            logger.error(f"FCM topic unsubscription error: {e}")
            return False


# Singleton instance
push_service = PushService()
