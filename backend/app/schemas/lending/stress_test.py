"""Stress test schemas (parametric v1).

Four standard scenarios — rate shock ±200 bps, NPA shock +5%, combined macro.
v1 is parametric: no Monte Carlo, no portfolio revaluation. CLAUDE.md §1
quality bar applies — outputs are honest computations over real portfolio
aggregates, not fabricated numbers.

Wire shape is camelCase (CamelSchema) so the React page can consume the
fields without a per-field mapper.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any, Literal

from pydantic import Field

from app.schemas.base import CamelSchema

ScenarioId = Literal[
    "RATE_SHOCK_PLUS_200",
    "RATE_SHOCK_MINUS_200",
    "NPA_SHOCK_PLUS_5",
    "COMBINED_MACRO",
]

ScenarioStatus = Literal["PASS", "WARN", "FAIL"]


class ScenarioMetadata(CamelSchema):
    """Static metadata for a stress scenario.

    Returned by `GET /lending/stress-test/scenarios` so the UI can render
    a description / chip set without first running the scenario.
    """

    scenario_id: ScenarioId
    name: str
    description: str
    category: Literal["RATE", "CREDIT", "COMBINED"]
    shock_bps: int | None = Field(
        None, description="Parallel rate shock in basis points (rate scenarios only)"
    )
    npa_migration_pct: Decimal | None = Field(
        None,
        description=(
            "Fraction of standard portfolio that migrates to substandard" " (credit scenarios only)"
        ),
    )


class ScenarioInputs(CamelSchema):
    """Snapshot of inputs that drove the computation.

    Captured per-run so the result is reproducible / auditable.
    """

    as_of_date: date
    shock_bps: int | None = None
    npa_migration_pct: Decimal | None = None

    # Portfolio aggregates (Decimals serialised as strings — never floats for ₹)
    total_principal_outstanding: Decimal = Field(default=Decimal("0"))
    secured_principal: Decimal = Field(default=Decimal("0"))
    unsecured_principal: Decimal = Field(default=Decimal("0"))
    rate_sensitive_liabilities: Decimal = Field(default=Decimal("0"))
    rate_sensitive_assets: Decimal = Field(default=Decimal("0"))

    # Capital snapshot
    tier1_capital: Decimal = Field(default=Decimal("0"))
    tier2_capital: Decimal = Field(default=Decimal("0"))
    total_capital: Decimal = Field(default=Decimal("0"))
    total_rwa: Decimal = Field(default=Decimal("0"))

    # Provisioning rates used (per CLAUDE.md §4.8 — never hardcoded in math)
    standard_secured_rate: Decimal = Field(default=Decimal("0"))
    substandard_secured_rate: Decimal = Field(default=Decimal("0"))
    standard_unsecured_rate: Decimal = Field(default=Decimal("0"))
    substandard_unsecured_rate: Decimal = Field(default=Decimal("0"))
    provisioning_rate_source: Literal["mst_provisioning_rate", "rbi_default"] = "rbi_default"


class ScenarioOutputs(CamelSchema):
    """Computed impact of a single scenario."""

    # NII / earnings impact
    nii_impact: Decimal = Field(default=Decimal("0"))
    nii_impact_percent: Decimal = Field(default=Decimal("0"))

    # Credit impact
    provision_impact: Decimal = Field(default=Decimal("0"))

    # CRAR impact
    pre_stress_crar: Decimal = Field(default=Decimal("0"))
    post_stress_crar: Decimal = Field(default=Decimal("0"))
    crar_delta_bps: int = 0

    # NPA ratio impact
    pre_stress_npa_ratio: Decimal = Field(default=Decimal("0"))
    post_stress_npa_ratio: Decimal = Field(default=Decimal("0"))

    # Regulatory breach flag
    minimum_crar_required: Decimal = Field(default=Decimal("15"))
    breach_minimum_crar: bool = False


class ScenarioResult(CamelSchema):
    """Full result for one scenario."""

    scenario_id: ScenarioId
    name: str
    description: str
    inputs: ScenarioInputs
    outputs: ScenarioOutputs
    status: ScenarioStatus
    warnings: list[str] = Field(default_factory=list)


class StressTestRunRequest(CamelSchema):
    """Body for `POST /lending/stress-test/run`."""

    scenario_id: ScenarioId
    as_of_date: date | None = None


class StressTestRunAllRequest(CamelSchema):
    """Body for `POST /lending/stress-test/run-all`."""

    as_of_date: date | None = None


class StressTestRunResponse(CamelSchema):
    """Envelope returned by `run` / `run-all`.

    `results` always carries the list (length 1 for `run`, length 4 for
    `run-all`) so the UI can render a uniform set of cards.
    """

    as_of_date: date
    results: list[ScenarioResult]
    summary: dict[str, Any] = Field(default_factory=dict)
