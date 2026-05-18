from app.models.lending.enums import ApplicationStage, ApplicationStatus, EntityType
from app.services.portal.scheme_rules import (
    derive_scheme_application_status,
    is_scheme_eligible_entity_type,
)


def test_only_institutional_entity_types_are_scheme_eligible():
    assert is_scheme_eligible_entity_type(EntityType.CORPORATE) is True
    assert is_scheme_eligible_entity_type(EntityType.LLP) is True
    assert is_scheme_eligible_entity_type(EntityType.PARTNERSHIP) is True
    assert is_scheme_eligible_entity_type(EntityType.TRUST) is True
    assert is_scheme_eligible_entity_type(EntityType.SOCIETY) is True
    assert is_scheme_eligible_entity_type(EntityType.INDIVIDUAL) is False
    assert is_scheme_eligible_entity_type(EntityType.HUF) is False
    assert is_scheme_eligible_entity_type(EntityType.PROPRIETORSHIP) is False


def test_scheme_status_mapping_prefers_borrower_facing_milestones():
    assert (
        derive_scheme_application_status(
            ApplicationStatus.DRAFT,
            ApplicationStage.LEAD,
        )
        == "DRAFT"
    )
    assert (
        derive_scheme_application_status(
            ApplicationStatus.SUBMITTED,
            ApplicationStage.APPLICATION,
        )
        == "LENDER_REVIEW"
    )
    assert (
        derive_scheme_application_status(
            ApplicationStatus.UNDER_REVIEW,
            ApplicationStage.APPRAISAL,
        )
        == "SMFCL_APPRAISAL"
    )
    assert (
        derive_scheme_application_status(
            ApplicationStatus.ADDITIONAL_INFO_REQUIRED,
            ApplicationStage.APPLICATION,
        )
        == "QUERY_PENDING"
    )
    assert (
        derive_scheme_application_status(
            ApplicationStatus.SANCTIONED,
            ApplicationStage.POST_SANCTION,
        )
        == "SANCTION_ISSUED"
    )
