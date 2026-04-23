"""Integration configuration repository."""

from datetime import datetime, timezone
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.core.integration_config import (
    IntegrationConfig,
    IntegrationLog,
    IntegrationType,
    IntegrationProvider,
    HealthStatus,
)
from app.repositories.base import BaseRepository


class IntegrationConfigRepository(BaseRepository[IntegrationConfig]):
    """Repository for integration configuration management."""

    def __init__(self, session: AsyncSession):
        super().__init__(IntegrationConfig, session)

    async def get_by_org_and_type(
        self,
        organization_id: UUID,
        integration_type: IntegrationType,
        provider: Optional[IntegrationProvider] = None,
    ) -> Optional[IntegrationConfig]:
        """Get integration config by organization and type."""
        query = select(IntegrationConfig).where(
            and_(
                IntegrationConfig.organization_id == organization_id,
                IntegrationConfig.integration_type == integration_type,
                IntegrationConfig.is_active == True,
            )
        )
        if provider:
            query = query.where(IntegrationConfig.provider == provider)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_by_organization(
        self,
        organization_id: UUID,
        integration_type: Optional[IntegrationType] = None,
        include_inactive: bool = False,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[IntegrationConfig], int]:
        """List integration configs for an organization."""
        query = select(IntegrationConfig).where(
            IntegrationConfig.organization_id == organization_id
        )

        if not include_inactive:
            query = query.where(IntegrationConfig.is_active == True)

        if integration_type:
            query = query.where(IntegrationConfig.integration_type == integration_type)

        # Count query
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.session.execute(count_query)
        total_count = total.scalar() or 0

        # Apply pagination
        query = query.order_by(IntegrationConfig.integration_type).offset(skip).limit(limit)
        result = await self.session.execute(query)
        configs = list(result.scalars().all())

        return configs, total_count

    async def get_all_by_type(
        self,
        integration_type: IntegrationType,
        active_only: bool = True,
    ) -> List[IntegrationConfig]:
        """Get all configs of a specific type across all organizations."""
        query = select(IntegrationConfig).where(
            IntegrationConfig.integration_type == integration_type
        )
        if active_only:
            query = query.where(IntegrationConfig.is_active == True)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def exists_for_org(
        self,
        organization_id: UUID,
        integration_type: IntegrationType,
        provider: IntegrationProvider,
        exclude_id: Optional[UUID] = None,
    ) -> bool:
        """Check if config already exists for org/type/provider combination."""
        query = select(func.count(IntegrationConfig.id)).where(
            and_(
                IntegrationConfig.organization_id == organization_id,
                IntegrationConfig.integration_type == integration_type,
                IntegrationConfig.provider == provider,
            )
        )
        if exclude_id:
            query = query.where(IntegrationConfig.id != exclude_id)
        result = await self.session.execute(query)
        return (result.scalar() or 0) > 0

    async def update_health_status(
        self,
        config_id: UUID,
        status: HealthStatus,
        error_message: Optional[str] = None,
    ) -> Optional[IntegrationConfig]:
        """Update health status of an integration."""
        config = await self.get(config_id)
        if config:
            config.health_status = status
            config.last_health_check = datetime.now(timezone.utc)
            config.last_error_message = error_message
            await self.session.flush()
            await self.session.refresh(config)
        return config

    async def update_usage_stats(
        self,
        config_id: UUID,
        success: bool,
    ) -> Optional[IntegrationConfig]:
        """Update usage statistics for an integration."""
        config = await self.get(config_id)
        if config:
            config.last_used_at = datetime.now(timezone.utc)
            config.total_requests += 1
            if not success:
                config.failed_requests += 1
            await self.session.flush()
            await self.session.refresh(config)
        return config


class IntegrationLogRepository:
    """Repository for integration API logs."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        organization_id: UUID,
        integration_type: str,
        provider: str,
        request_id: Optional[str] = None,
        endpoint: Optional[str] = None,
        method: Optional[str] = None,
        request_payload: Optional[dict] = None,
        response_payload: Optional[dict] = None,
        http_status: Optional[int] = None,
        is_success: bool = False,
        error_message: Optional[str] = None,
        latency_ms: Optional[int] = None,
        triggered_by: Optional[UUID] = None,
        integration_config_id: Optional[UUID] = None,
    ) -> IntegrationLog:
        """Create a new integration log entry."""
        log = IntegrationLog(
            organization_id=organization_id,
            integration_config_id=integration_config_id,
            integration_type=integration_type,
            provider=provider,
            request_id=request_id,
            endpoint=endpoint,
            method=method,
            request_payload=request_payload,
            response_payload=response_payload,
            http_status=http_status,
            is_success=is_success,
            error_message=error_message,
            latency_ms=latency_ms,
            triggered_by=triggered_by,
        )
        self.session.add(log)
        await self.session.flush()
        await self.session.refresh(log)
        return log

    async def list_by_config(
        self,
        integration_config_id: UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[IntegrationLog], int]:
        """List logs for a specific integration config."""
        query = select(IntegrationLog).where(
            IntegrationLog.integration_config_id == integration_config_id
        )

        # Count
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.session.execute(count_query)
        total_count = total.scalar() or 0

        # Get logs
        query = query.order_by(IntegrationLog.created_at.desc()).offset(skip).limit(limit)
        result = await self.session.execute(query)
        logs = list(result.scalars().all())

        return logs, total_count

    async def list_by_organization(
        self,
        organization_id: UUID,
        integration_type: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        success_only: Optional[bool] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[IntegrationLog], int]:
        """List logs for an organization with filters."""
        query = select(IntegrationLog).where(
            IntegrationLog.organization_id == organization_id
        )

        if integration_type:
            query = query.where(IntegrationLog.integration_type == integration_type)
        if from_date:
            query = query.where(IntegrationLog.created_at >= from_date)
        if to_date:
            query = query.where(IntegrationLog.created_at <= to_date)
        if success_only is not None:
            query = query.where(IntegrationLog.is_success == success_only)

        # Count
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.session.execute(count_query)
        total_count = total.scalar() or 0

        # Get logs
        query = query.order_by(IntegrationLog.created_at.desc()).offset(skip).limit(limit)
        result = await self.session.execute(query)
        logs = list(result.scalars().all())

        return logs, total_count

    async def get_stats(
        self,
        organization_id: UUID,
        integration_type: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
    ) -> dict:
        """Get aggregate statistics for logs."""
        base_query = select(IntegrationLog).where(
            IntegrationLog.organization_id == organization_id
        )
        if integration_type:
            base_query = base_query.where(IntegrationLog.integration_type == integration_type)
        if from_date:
            base_query = base_query.where(IntegrationLog.created_at >= from_date)
        if to_date:
            base_query = base_query.where(IntegrationLog.created_at <= to_date)

        # Total count
        total_query = select(func.count()).select_from(base_query.subquery())
        total_result = await self.session.execute(total_query)
        total = total_result.scalar() or 0

        # Success count
        success_query = select(func.count()).select_from(
            base_query.where(IntegrationLog.is_success == True).subquery()
        )
        success_result = await self.session.execute(success_query)
        success = success_result.scalar() or 0

        # Average latency
        latency_query = select(func.avg(IntegrationLog.latency_ms)).select_from(
            base_query.where(IntegrationLog.latency_ms.isnot(None)).subquery()
        )
        latency_result = await self.session.execute(latency_query)
        avg_latency = latency_result.scalar()

        return {
            "total_requests": total,
            "successful_requests": success,
            "failed_requests": total - success,
            "success_rate": (success / total * 100) if total > 0 else 0,
            "average_latency_ms": round(avg_latency) if avg_latency else None,
        }
