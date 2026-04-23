"""Credit rating models for the lending module."""

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Optional, List
from uuid import UUID

from sqlalchemy import (
    Boolean, Date, Enum, ForeignKey, Integer,
    Numeric, String, Text, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.lending.enums import (
    RiskCategoryType, RatingGrade, RatingType, RatingStatus
)


if TYPE_CHECKING:
    from app.models.masters.organization import Organization
    from app.models.lending.entity import Entity
    from app.models.workflow import WorkflowInstance


class RiskCategory(BaseModel):
    """Risk categories for credit scoring model."""

    __tablename__ = "los_risk_category"

    # Organization scope
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Organization this category belongs to",
    )

    # Category identification
    code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Category code e.g., 'FINANCIAL', 'SPONSOR'",
    )
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Category name",
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Category description",
    )
    category_type: Mapped[RiskCategoryType] = mapped_column(
        Enum(RiskCategoryType),
        nullable=False,
        index=True,
        comment="Type - SPONSOR, PROJECT, FINANCIAL, INDUSTRY, etc.",
    )

    # Weighting
    weight_percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        comment="Weight of this category in overall score (total should be 100)",
    )
    max_score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=100,
        comment="Maximum possible score in this category",
    )

    # Display
    display_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Display order",
    )

    # Applicability
    applicable_entity_types: Mapped[Optional[list]] = mapped_column(
        JSONB,
        nullable=True,
        comment="List of entity types where this applies",
    )
    applicable_product_categories: Mapped[Optional[list]] = mapped_column(
        JSONB,
        nullable=True,
        comment="List of product categories where this applies",
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        lazy="selectin",
    )
    parameters: Mapped[List["RiskParameter"]] = relationship(
        "RiskParameter",
        back_populates="category",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="RiskParameter.display_order",
    )

    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_risk_category_org_code"),
        Index("ix_los_risk_category_org_type", "organization_id", "category_type"),
    )

    def __repr__(self) -> str:
        return f"<RiskCategory(code={self.code}, weight={self.weight_percentage}%)>"


class RiskParameter(BaseModel):
    """Individual risk parameters within a category."""

    __tablename__ = "los_risk_parameter"

    # Parent category
    category_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("los_risk_category.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent risk category",
    )

    # Parameter identification
    code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Parameter code e.g., 'CURRENT_RATIO', 'DEBT_EQUITY'",
    )
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Parameter name",
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Parameter description",
    )

    # Scoring configuration
    max_score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=10,
        comment="Maximum score for this parameter",
    )
    weight_in_category: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("100"),
        comment="Weight within category (total should be 100)",
    )

    # Value type and bounds
    value_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="NUMERIC",
        comment="Value type - NUMERIC, PERCENTAGE, CATEGORICAL, BOOLEAN",
    )
    min_value: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 4),
        nullable=True,
        comment="Minimum allowed value (for numeric)",
    )
    max_value: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 4),
        nullable=True,
        comment="Maximum allowed value (for numeric)",
    )

    # Scoring slabs (for numeric values)
    scoring_slabs: Mapped[Optional[list]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Scoring slabs e.g., [{'min': 1.5, 'max': 2.0, 'score': 8}]",
    )

    # Categorical options (for categorical values)
    categorical_options: Mapped[Optional[list]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Options for categorical e.g., [{'value': 'AAA', 'score': 10}]",
    )

    # Auto-calculation
    is_auto_calculated: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Can be auto-calculated from financial data?",
    )
    calculation_formula: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Formula for auto-calculation (Python expression)",
    )
    data_source_field: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Field name in EntityFinancial for auto-fetch",
    )

    # Display
    display_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Display order within category",
    )
    is_mandatory: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Is this parameter mandatory?",
    )

    # Remarks template
    default_remarks: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Default remarks template",
    )

    # Relationships
    category: Mapped["RiskCategory"] = relationship(
        "RiskCategory",
        back_populates="parameters",
    )

    __table_args__ = (
        UniqueConstraint("category_id", "code", name="uq_risk_param_category_code"),
        Index("ix_los_risk_parameter_code", "code"),
    )

    def calculate_score(self, value: any) -> int:
        """Calculate score for a given value."""
        if value is None:
            return 0

        if self.value_type == "BOOLEAN":
            return self.max_score if value else 0

        if self.value_type == "CATEGORICAL" and self.categorical_options:
            for option in self.categorical_options:
                if option.get("value") == value:
                    return option.get("score", 0)
            return 0

        if self.value_type in ("NUMERIC", "PERCENTAGE") and self.scoring_slabs:
            numeric_value = Decimal(str(value))
            for slab in self.scoring_slabs:
                min_val = Decimal(str(slab.get("min", "-999999999")))
                max_val = Decimal(str(slab.get("max", "999999999")))
                if min_val <= numeric_value <= max_val:
                    return slab.get("score", 0)
            return 0

        return 0

    def __repr__(self) -> str:
        return f"<RiskParameter(code={self.code}, max_score={self.max_score})>"


class RatingMatrix(BaseModel):
    """Rating grade matrix - maps scores to rating grades."""

    __tablename__ = "los_rating_matrix"

    # Organization scope
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Organization",
    )

    # Rating grade
    grade: Mapped[RatingGrade] = mapped_column(
        Enum(RatingGrade),
        nullable=False,
        index=True,
        comment="Rating grade - AAA, AA+, AA, etc.",
    )
    grade_description: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Description of the grade",
    )

    # Score range
    min_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        comment="Minimum score for this grade",
    )
    max_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        comment="Maximum score for this grade",
    )

    # Risk implications
    risk_weight: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("100"),
        comment="Risk weight for capital calculation",
    )
    provisioning_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0"),
        comment="Provisioning rate percentage",
    )
    pricing_spread_bps: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Minimum spread over base rate (basis points)",
    )

    # Policy
    max_exposure_pct: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        comment="Max exposure as % of total portfolio",
    )
    requires_collateral: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Collateral mandatory for this grade?",
    )
    min_collateral_coverage: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        comment="Minimum collateral coverage ratio",
    )

    # Approval authority
    approval_authority: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Approval authority designation",
    )
    max_sanction_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Maximum sanction amount for this grade",
    )

    # Display
    display_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Display order (AAA first)",
    )
    color_code: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        comment="Color code for UI (hex)",
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint("organization_id", "grade", name="uq_rating_matrix_org_grade"),
        Index("ix_los_rating_matrix_org_score", "organization_id", "min_score", "max_score"),
    )

    def __repr__(self) -> str:
        return f"<RatingMatrix(grade={self.grade}, score_range={self.min_score}-{self.max_score})>"


class EntityRating(BaseModel):
    """Credit rating assigned to an entity."""

    __tablename__ = "los_entity_rating"

    # Organization scope
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Organization",
    )

    # Entity reference
    entity_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("los_entity.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Rated entity",
    )

    # Rating identification
    rating_reference: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Rating reference number e.g., 'RAT/2025/00001'",
    )
    rating_type: Mapped[RatingType] = mapped_column(
        Enum(RatingType),
        nullable=False,
        index=True,
        comment="Type - INITIAL, REVIEW, ANNUAL, EVENT_BASED",
    )

    # Rating date
    rating_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Date of rating",
    )
    effective_from: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Rating effective from",
    )
    valid_until: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Rating valid until",
    )

    # Previous rating (for review/annual)
    previous_rating_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("los_entity_rating.id", ondelete="SET NULL"),
        nullable=True,
        comment="Previous rating if this is a review",
    )
    previous_grade: Mapped[Optional[RatingGrade]] = mapped_column(
        Enum(RatingGrade),
        nullable=True,
        comment="Previous rating grade",
    )

    # Scores
    total_score: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="Total weighted score",
    )
    max_possible_score: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("100"),
        comment="Maximum possible score",
    )
    score_percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        comment="Score as percentage of max",
    )

    # Final grade
    calculated_grade: Mapped[RatingGrade] = mapped_column(
        Enum(RatingGrade),
        nullable=False,
        comment="Grade based on score calculation",
    )
    final_grade: Mapped[RatingGrade] = mapped_column(
        Enum(RatingGrade),
        nullable=False,
        index=True,
        comment="Final assigned grade (may be overridden)",
    )
    grade_overridden: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Was grade overridden from calculated?",
    )
    override_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Reason for grade override",
    )

    # Category-wise scores (stored as JSON)
    category_scores: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        comment="Category-wise scores",
    )

    # Parameter-wise scores (stored as JSON)
    parameter_scores: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        comment="Parameter-wise scores with values",
    )

    # Financial data used
    financial_year_used: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        comment="Financial year data used for rating",
    )

    # Status and workflow
    status: Mapped[RatingStatus] = mapped_column(
        Enum(RatingStatus),
        nullable=False,
        default=RatingStatus.DRAFT,
        index=True,
        comment="Status - DRAFT, PENDING_APPROVAL, APPROVED, REJECTED",
    )
    workflow_instance_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("wf_workflow_instance.id", ondelete="SET NULL"),
        nullable=True,
        comment="Approval workflow instance",
    )

    # Approval
    approved_by_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
        comment="Approved by user",
    )
    approved_at: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Approval date",
    )
    approval_remarks: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Approval remarks",
    )

    # Rating analyst
    rated_by_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="RESTRICT"),
        nullable=False,
        comment="Rating analyst",
    )

    # Summary and remarks
    rating_summary: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Rating summary/executive summary",
    )
    strengths: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Key strengths identified",
    )
    weaknesses: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Key weaknesses/concerns identified",
    )
    recommendations: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Recommendations",
    )

    # Attachments
    supporting_documents: Mapped[Optional[list]] = mapped_column(
        JSONB,
        nullable=True,
        comment="List of supporting document paths",
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        lazy="selectin",
    )
    entity: Mapped["Entity"] = relationship(
        "Entity",
        back_populates="ratings",
    )
    previous_rating: Mapped[Optional["EntityRating"]] = relationship(
        "EntityRating",
        remote_side="EntityRating.id",
        lazy="selectin",
    )
    workflow_instance: Mapped[Optional["WorkflowInstance"]] = relationship(
        "WorkflowInstance",
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint("organization_id", "rating_reference", name="uq_entity_rating_ref"),
        Index("ix_los_entity_rating_entity_date", "entity_id", "rating_date"),
        Index("ix_los_entity_rating_org_status", "organization_id", "status"),
        Index("ix_los_entity_rating_org_grade", "organization_id", "final_grade"),
    )

    def __repr__(self) -> str:
        return f"<EntityRating(entity={self.entity_id}, grade={self.final_grade}, status={self.status})>"


class RatingScoreDetail(BaseModel):
    """Individual parameter scores for a rating."""

    __tablename__ = "los_rating_score_detail"

    # Parent rating
    rating_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("los_entity_rating.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent rating",
    )

    # Category and parameter
    category_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("los_risk_category.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="Risk category",
    )
    parameter_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("los_risk_parameter.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="Risk parameter",
    )

    # Value and score
    input_value: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Input value (string representation)",
    )
    numeric_value: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 4),
        nullable=True,
        comment="Numeric value if applicable",
    )
    score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Score assigned",
    )
    max_score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Maximum possible score",
    )
    weighted_score: Mapped[Decimal] = mapped_column(
        Numeric(10, 4),
        nullable=False,
        comment="Weighted score contribution",
    )

    # Source
    is_auto_calculated: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Was value auto-calculated?",
    )
    data_source: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Source of data e.g., 'EntityFinancial.2024-25'",
    )

    # Override
    is_overridden: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Was score overridden?",
    )
    original_score: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Original score before override",
    )
    override_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Reason for override",
    )

    # Remarks
    remarks: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Parameter-specific remarks",
    )

    # Relationships
    rating: Mapped["EntityRating"] = relationship(
        "EntityRating",
        lazy="selectin",
    )
    category: Mapped["RiskCategory"] = relationship(
        "RiskCategory",
        lazy="selectin",
    )
    parameter: Mapped["RiskParameter"] = relationship(
        "RiskParameter",
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint("rating_id", "parameter_id", name="uq_rating_score_param"),
        Index("ix_los_rating_score_rating_cat", "rating_id", "category_id"),
    )

    def __repr__(self) -> str:
        return f"<RatingScoreDetail(rating={self.rating_id}, score={self.score}/{self.max_score})>"
