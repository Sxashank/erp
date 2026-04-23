"""CommunicationService tests (STAGE-6-PENDING-communication-service closure)."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.core import feature_flags
from app.services.notification.communication_service import (
    Channel,
    CommunicationService,
    DispatchResult,
    DispatchStatus,
    Recipient,
)


@pytest.fixture(autouse=True)
def _reset_flags():
    feature_flags.reset_flags()
    yield
    feature_flags.reset_flags()


def test_recipient_resolves_target_per_channel() -> None:
    r = Recipient(
        user_id="u1",
        email="a@b.com",
        phone="+919876543210",
        device_token="fcm-token",
    )
    assert r.target_for(Channel.EMAIL) == "a@b.com"
    assert r.target_for(Channel.SMS) == "+919876543210"
    assert r.target_for(Channel.PUSH) == "fcm-token"
    assert r.target_for(Channel.IN_APP) == "u1"


@pytest.mark.asyncio
async def test_send_returns_failed_when_target_missing() -> None:
    svc = CommunicationService()
    feature_flags.set_flag("sms_live", "mock")
    r = Recipient(user_id="u1")  # no phone
    result = await svc.send(
        channel=Channel.SMS,
        recipient=r,
        template_code="OTP_LOGIN",
    )
    assert result.status == DispatchStatus.FAILED
    assert "no target" in (result.error or "")


@pytest.mark.asyncio
async def test_send_disabled_when_flag_off() -> None:
    svc = CommunicationService()
    feature_flags.set_flag("sms_live", "off")
    r = Recipient(user_id="u1", phone="+919876543210")
    result = await svc.send(
        channel=Channel.SMS, recipient=r, template_code="OTP_LOGIN"
    )
    assert result.status == DispatchStatus.DISABLED
    assert result.provider_message_id is None


@pytest.mark.asyncio
async def test_send_mocks_when_flag_mock() -> None:
    svc = CommunicationService()
    feature_flags.set_flag("sms_live", "mock")
    r = Recipient(user_id="u1", phone="+919876543210")
    result = await svc.send(
        channel=Channel.SMS, recipient=r, template_code="OTP_LOGIN"
    )
    assert result.status == DispatchStatus.MOCKED
    assert result.provider_message_id == "mock-OTP_LOGIN"


@pytest.mark.asyncio
async def test_send_calls_registered_provider_when_live() -> None:
    svc = CommunicationService()
    feature_flags.set_flag("sms_live", "on")

    fake_provider = AsyncMock()
    fake_provider.send = AsyncMock(
        return_value=DispatchResult(
            channel=Channel.SMS,
            status=DispatchStatus.SENT,
            provider_message_id="msg-12345",
        )
    )
    svc.register_provider(Channel.SMS, fake_provider)

    r = Recipient(user_id="u1", phone="+919876543210")
    result = await svc.send(
        channel=Channel.SMS,
        recipient=r,
        template_code="OTP_LOGIN",
        context={"otp": "123456"},
    )
    assert result.status == DispatchStatus.SENT
    assert result.provider_message_id == "msg-12345"
    fake_provider.send.assert_awaited_once()


@pytest.mark.asyncio
async def test_send_falls_back_to_mock_when_live_but_no_provider_registered() -> None:
    svc = CommunicationService()
    feature_flags.set_flag("sms_live", "on")  # live, but no provider installed
    r = Recipient(user_id="u1", phone="+919876543210")
    result = await svc.send(
        channel=Channel.SMS, recipient=r, template_code="OTP_LOGIN"
    )
    assert result.status == DispatchStatus.MOCKED


@pytest.mark.asyncio
async def test_send_captures_provider_exception_as_failed() -> None:
    svc = CommunicationService()
    feature_flags.set_flag("sms_live", "on")

    class _Explode:
        async def send(self, **kwargs):
            raise RuntimeError("gateway timeout")

    svc.register_provider(Channel.SMS, _Explode())
    r = Recipient(user_id="u1", phone="+919876543210")
    result = await svc.send(
        channel=Channel.SMS, recipient=r, template_code="OTP_LOGIN"
    )
    assert result.status == DispatchStatus.FAILED
    assert "gateway timeout" in (result.error or "")


@pytest.mark.asyncio
async def test_fanout_returns_one_result_per_recipient() -> None:
    svc = CommunicationService()
    feature_flags.set_flag("sms_live", "mock")
    recipients = [
        Recipient(user_id="u1", phone="+919876543210"),
        Recipient(user_id="u2", phone="+918888888888"),
        Recipient(user_id="u3"),  # no phone — fails
    ]
    results = await svc.fanout(
        channel=Channel.SMS,
        recipients=recipients,
        template_code="PAYMENT_DUE",
    )
    assert len(results) == 3
    assert results[0].status == DispatchStatus.MOCKED
    assert results[1].status == DispatchStatus.MOCKED
    assert results[2].status == DispatchStatus.FAILED


@pytest.mark.asyncio
async def test_fanout_continues_past_individual_provider_failures() -> None:
    svc = CommunicationService()
    feature_flags.set_flag("sms_live", "on")

    calls = {"n": 0}

    class _HalfDown:
        async def send(self, **kwargs):
            calls["n"] += 1
            if calls["n"] == 2:
                raise RuntimeError("rate limit")
            return DispatchResult(
                channel=Channel.SMS,
                status=DispatchStatus.SENT,
                provider_message_id=f"m{calls['n']}",
            )

    svc.register_provider(Channel.SMS, _HalfDown())
    recipients = [
        Recipient(user_id=f"u{i}", phone=f"+9199999999{i:02}") for i in range(3)
    ]
    results = await svc.fanout(
        channel=Channel.SMS,
        recipients=recipients,
        template_code="PAYMENT_DUE",
    )
    assert [r.status for r in results] == [
        DispatchStatus.SENT,
        DispatchStatus.FAILED,
        DispatchStatus.SENT,
    ]
