"""SLA Monitor Background Worker.

Monitors and enforces SLAs for:
- Legal case processing
- Service request turnaround
- Document processing
- Escalation management
"""

import asyncio
import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select, and_, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.common.background_job import BackgroundJob, JobType, JobStatus
from app.services.common.job_service import BackgroundJobRunner

logger = logging.getLogger(__name__)


# SLA Definitions (in business hours/days)
SLA_DEFINITIONS = {
    "LEGAL_CASE": {
        "SARFAESI_13_2_NOTICE": {"target_days": 3, "warning_days": 2},
        "POSSESSION_NOTICE": {"target_days": 5, "warning_days": 3},
        "HEARING_PREPARATION": {"target_days": 7, "warning_days": 5},
        "DOCUMENT_FILING": {"target_days": 3, "warning_days": 2},
    },
    "SERVICE_REQUEST": {
        "PREPAYMENT": {"target_days": 3, "warning_days": 2},
        "FORECLOSURE": {"target_days": 5, "warning_days": 3},
        "NOC_REQUEST": {"target_days": 7, "warning_days": 5},
        "STATEMENT_REQUEST": {"target_days": 1, "warning_days": 1},
        "EMI_DATE_CHANGE": {"target_days": 5, "warning_days": 3},
        "ADDRESS_CHANGE": {"target_days": 3, "warning_days": 2},
    },
    "DOCUMENT_PROCESSING": {
        "KYC_VERIFICATION": {"target_days": 2, "warning_days": 1},
        "DOCUMENT_UPLOAD": {"target_days": 1, "warning_days": 1},
        "AGREEMENT_GENERATION": {"target_days": 3, "warning_days": 2},
    },
}


async def process_sla_monitoring(
    job: BackgroundJob,
    runner: BackgroundJobRunner,
) -> Dict[str, Any]:
    """
    Process SLA monitoring and trigger escalations.

    This job:
    1. Checks SLA compliance for all tracked items
    2. Generates SLA breach alerts
    3. Triggers escalation workflows
    4. Updates SLA metrics
    """
    from app.database import async_session_maker

    input_data = job.input_data or {}
    sla_type = input_data.get("sla_type", "all")

    metrics = {
        "total_items_checked": 0,
        "sla_compliant": 0,
        "sla_warning": 0,
        "sla_breached": 0,
        "escalations_triggered": 0,
    }
    errors: List[Dict] = []

    async with async_session_maker() as session:
        try:
            if sla_type in ["all", "legal_case"]:
                legal_metrics = await _check_legal_case_sla(session, job.organization_id)
                _merge_metrics(metrics, legal_metrics)

            if sla_type in ["all", "service_request"]:
                sr_metrics = await _check_service_request_sla(session, job.organization_id)
                _merge_metrics(metrics, sr_metrics)

            if sla_type in ["all", "document"]:
                doc_metrics = await _check_document_processing_sla(session, job.organization_id)
                _merge_metrics(metrics, doc_metrics)

            await session.commit()

            await runner.update_progress(
                job,
                processed=metrics["total_items_checked"],
                successful=metrics["sla_compliant"],
                failed=metrics["sla_breached"],
            )

            return {
                "metrics": metrics,
                "errors": errors,
            }

        except Exception as e:
            logger.error(f"Error in SLA monitoring: {e}")
            errors.append({"error": str(e)})
            return {
                "metrics": metrics,
                "errors": errors,
            }


async def _check_legal_case_sla(
    session: AsyncSession,
    organization_id: UUID,
) -> Dict[str, int]:
    """Check SLA compliance for legal cases."""
    from app.models.lending.collections import LegalCase

    metrics = {
        "total_items_checked": 0,
        "sla_compliant": 0,
        "sla_warning": 0,
        "sla_breached": 0,
        "escalations_triggered": 0,
    }

    today = date.today()

    # Query active legal cases
    query = select(LegalCase).where(
        and_(
            LegalCase.organization_id == organization_id,
            LegalCase.case_status.in_(["INITIATED", "IN_PROGRESS", "PENDING_HEARING"]),
        )
    )

    result = await session.execute(query)
    cases = result.scalars().all()

    for case in cases:
        metrics["total_items_checked"] += 1

        # Calculate SLA based on case stage
        sla_status = _calculate_case_sla_status(case, today)

        if sla_status == "COMPLIANT":
            metrics["sla_compliant"] += 1
        elif sla_status == "WARNING":
            metrics["sla_warning"] += 1
            # Send warning notification
            await _send_sla_warning(session, "LEGAL_CASE", case.id, case.assigned_to_id)
        else:
            metrics["sla_breached"] += 1
            # Trigger escalation
            escalated = await _trigger_escalation(
                session,
                escalation_type="LEGAL_CASE_SLA_BREACH",
                entity_id=case.id,
                entity_type="LegalCase",
                organization_id=organization_id,
            )
            if escalated:
                metrics["escalations_triggered"] += 1

    return metrics


async def _check_service_request_sla(
    session: AsyncSession,
    organization_id: UUID,
) -> Dict[str, int]:
    """Check SLA compliance for service requests."""
    from app.models.portal.service_request import PortalServiceRequest
    from app.models.portal.enums import ServiceRequestStatus

    metrics = {
        "total_items_checked": 0,
        "sla_compliant": 0,
        "sla_warning": 0,
        "sla_breached": 0,
        "escalations_triggered": 0,
    }

    today = datetime.utcnow()

    # Query pending service requests
    query = select(PortalServiceRequest).where(
        and_(
            PortalServiceRequest.organization_id == organization_id,
            PortalServiceRequest.status.in_([
                ServiceRequestStatus.SUBMITTED,
                ServiceRequestStatus.UNDER_REVIEW,
                ServiceRequestStatus.PENDING_DOCUMENTS,
            ]),
        )
    )

    result = await session.execute(query)
    requests = result.scalars().all()

    for request in requests:
        metrics["total_items_checked"] += 1

        # Get SLA definition for request type
        sla_def = SLA_DEFINITIONS.get("SERVICE_REQUEST", {}).get(
            request.request_type.value,
            {"target_days": 5, "warning_days": 3}
        )

        # Calculate age in business days
        age_days = (today - request.created_at).days

        if age_days <= sla_def["warning_days"]:
            metrics["sla_compliant"] += 1
        elif age_days <= sla_def["target_days"]:
            metrics["sla_warning"] += 1
            await _send_sla_warning(
                session,
                "SERVICE_REQUEST",
                request.id,
                request.assigned_to_id,
            )
        else:
            metrics["sla_breached"] += 1
            escalated = await _trigger_escalation(
                session,
                escalation_type="SERVICE_REQUEST_SLA_BREACH",
                entity_id=request.id,
                entity_type="PortalServiceRequest",
                organization_id=organization_id,
                metadata={
                    "request_type": request.request_type.value,
                    "age_days": age_days,
                    "target_days": sla_def["target_days"],
                }
            )
            if escalated:
                metrics["escalations_triggered"] += 1

    return metrics


async def _check_document_processing_sla(
    session: AsyncSession,
    organization_id: UUID,
) -> Dict[str, int]:
    """Check SLA compliance for document processing."""
    from app.models.portal.document import PortalDocumentRequest
    from app.models.portal.enums import DocumentRequestStatus

    metrics = {
        "total_items_checked": 0,
        "sla_compliant": 0,
        "sla_warning": 0,
        "sla_breached": 0,
        "escalations_triggered": 0,
    }

    today = datetime.utcnow()

    # Query pending document requests
    query = select(PortalDocumentRequest).where(
        and_(
            PortalDocumentRequest.organization_id == organization_id,
            PortalDocumentRequest.status.in_([
                DocumentRequestStatus.PENDING,
                DocumentRequestStatus.IN_REVIEW,
            ]),
        )
    )

    result = await session.execute(query)
    requests = result.scalars().all()

    for request in requests:
        metrics["total_items_checked"] += 1

        sla_def = SLA_DEFINITIONS.get("DOCUMENT_PROCESSING", {}).get(
            request.document_type.value if request.document_type else "DEFAULT",
            {"target_days": 3, "warning_days": 2}
        )

        age_days = (today - request.created_at).days

        if age_days <= sla_def["warning_days"]:
            metrics["sla_compliant"] += 1
        elif age_days <= sla_def["target_days"]:
            metrics["sla_warning"] += 1
        else:
            metrics["sla_breached"] += 1
            await _trigger_escalation(
                session,
                escalation_type="DOCUMENT_SLA_BREACH",
                entity_id=request.id,
                entity_type="PortalDocumentRequest",
                organization_id=organization_id,
            )
            metrics["escalations_triggered"] += 1

    return metrics


def _calculate_case_sla_status(case: Any, today: date) -> str:
    """Calculate SLA status for a legal case based on its stage."""
    # Simplified SLA calculation
    # In production, this would consider:
    # - Case type and current stage
    # - Last action date
    # - Expected completion date for current stage

    case_age = (today - case.created_at.date()).days

    if case.case_type == "SARFAESI":
        # SARFAESI has specific statutory timelines
        if case_age > 90:
            return "BREACHED"
        elif case_age > 60:
            return "WARNING"
        else:
            return "COMPLIANT"
    else:
        # Generic case SLA
        if case_age > 30:
            return "BREACHED"
        elif case_age > 20:
            return "WARNING"
        else:
            return "COMPLIANT"


async def _send_sla_warning(
    session: AsyncSession,
    sla_type: str,
    entity_id: UUID,
    assigned_to_id: Optional[UUID],
) -> None:
    """Send SLA warning notification."""
    # from app.integrations.communication import CommunicationService

    logger.warning(
        f"SLA warning for {sla_type}: {entity_id}, assigned to: {assigned_to_id}"
    )

    # In production:
    # - Get user email/phone for assigned_to_id
    # - Send email notification
    # - Create in-app notification


async def _trigger_escalation(
    session: AsyncSession,
    escalation_type: str,
    entity_id: UUID,
    entity_type: str,
    organization_id: UUID,
    metadata: Optional[Dict[str, Any]] = None,
) -> bool:
    """Trigger escalation workflow for SLA breach."""
    logger.error(
        f"SLA BREACH - Triggering escalation: {escalation_type} "
        f"for {entity_type}:{entity_id}"
    )

    # In production:
    # 1. Create escalation record
    # 2. Notify supervisor/manager
    # 3. Update entity status
    # 4. Create audit trail

    # from app.models.workflow.escalation import Escalation
    # escalation = Escalation(
    #     organization_id=organization_id,
    #     escalation_type=escalation_type,
    #     entity_type=entity_type,
    #     entity_id=entity_id,
    #     status="ACTIVE",
    #     escalation_level=1,
    #     metadata=metadata,
    # )
    # session.add(escalation)

    return True


def _merge_metrics(target: Dict[str, int], source: Dict[str, int]) -> None:
    """Merge metrics dictionaries."""
    for key, value in source.items():
        target[key] = target.get(key, 0) + value


# Scheduled task functions

async def run_sla_monitoring():
    """Run SLA monitoring job."""
    from app.database import async_session_maker
    from app.services.common.job_service import JobService, BackgroundJobRunner

    logger.info("Starting SLA monitoring job")

    async with async_session_maker() as session:
        job_service = JobService(session)

        organization_id = UUID("00000000-0000-0000-0000-000000000000")

        job = await job_service.create_job(
            organization_id=organization_id,
            job_type=JobType.SLA_MONITORING,
            job_name="SLA Monitoring",
            created_by=organization_id,
            input_data={"sla_type": "all"},
        )

        runner = BackgroundJobRunner(session)
        result = await process_sla_monitoring(job, runner)

        logger.info(f"SLA monitoring completed: {result}")


async def run_escalation_review():
    """Review and process active escalations."""
    logger.info("Running escalation review")
    # Process active escalations
    # - Check if resolved
    # - Escalate to next level if not resolved
    # - Send reminder notifications
    pass


# SLA Report generation

async def generate_sla_report(
    session: AsyncSession,
    organization_id: UUID,
    from_date: date,
    to_date: date,
) -> Dict[str, Any]:
    """Generate SLA compliance report."""
    report = {
        "period": {
            "from": from_date.isoformat(),
            "to": to_date.isoformat(),
        },
        "legal_cases": {
            "total": 0,
            "compliant": 0,
            "breached": 0,
            "compliance_rate": 0.0,
        },
        "service_requests": {
            "total": 0,
            "compliant": 0,
            "breached": 0,
            "compliance_rate": 0.0,
            "avg_resolution_time_hours": 0,
        },
        "document_processing": {
            "total": 0,
            "compliant": 0,
            "breached": 0,
            "compliance_rate": 0.0,
        },
        "escalations": {
            "total": 0,
            "resolved": 0,
            "pending": 0,
            "avg_resolution_time_hours": 0,
        },
    }

    # TODO: Query and populate actual metrics

    return report
