"""
Direct database seed script for HR Training & Performance Module master data.
Inserts data directly into the database without requiring API authentication.

Usage:
    cd /Users/balakrishnavundavalli/working/talentfino/erp/backend
    source venv/bin/activate
    python scripts/seed_hr_training_data.py
"""

import asyncio
from datetime import date, timedelta
from decimal import Decimal
import os

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# Get database URL from environment or use default
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://smfc:smfc_secret@localhost:5432/smfc_erp"
)

# Import models
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# =============================================================================
# TRAINING PROGRAMS DATA
# =============================================================================

TRAINING_PROGRAMS = [
    # Compliance Training
    {
        "program_code": "TRN-COMP-001",
        "program_name": "Anti-Money Laundering (AML) Basics",
        "description": "Comprehensive training on AML regulations, KYC requirements, and suspicious transaction reporting for NBFC employees",
        "category": "COMPLIANCE",
        "training_type": "MANDATORY",
        "duration_hours": 8,
        "max_participants": 50,
        "min_participants": 10,
        "cost_per_participant": Decimal("1500.00"),
        "certification_required": True,
        "validity_months": 12,
        "is_active": True,
    },
    {
        "program_code": "TRN-COMP-002",
        "program_name": "Fair Practice Code Training",
        "description": "Training on RBI Fair Practice Code guidelines for lending institutions",
        "category": "COMPLIANCE",
        "training_type": "MANDATORY",
        "duration_hours": 4,
        "max_participants": 100,
        "min_participants": 20,
        "cost_per_participant": Decimal("750.00"),
        "certification_required": True,
        "validity_months": 12,
        "is_active": True,
    },
    {
        "program_code": "TRN-COMP-003",
        "program_name": "Data Privacy & DPDP Act",
        "description": "Training on Digital Personal Data Protection Act compliance for financial services",
        "category": "COMPLIANCE",
        "training_type": "MANDATORY",
        "duration_hours": 6,
        "max_participants": 100,
        "min_participants": 15,
        "cost_per_participant": Decimal("1200.00"),
        "certification_required": True,
        "validity_months": 24,
        "is_active": True,
    },
    {
        "program_code": "TRN-COMP-004",
        "program_name": "POSH - Prevention of Sexual Harassment",
        "description": "Mandatory POSH awareness training for all employees",
        "category": "COMPLIANCE",
        "training_type": "MANDATORY",
        "duration_hours": 4,
        "max_participants": 100,
        "min_participants": 20,
        "cost_per_participant": Decimal("500.00"),
        "certification_required": True,
        "validity_months": 12,
        "is_active": True,
    },
    # Technical Training
    {
        "program_code": "TRN-TECH-001",
        "program_name": "Credit Appraisal Fundamentals",
        "description": "Fundamentals of credit appraisal including financial analysis, risk assessment, and documentation",
        "category": "TECHNICAL",
        "training_type": "SKILL_BASED",
        "duration_hours": 16,
        "max_participants": 30,
        "min_participants": 10,
        "cost_per_participant": Decimal("3500.00"),
        "certification_required": True,
        "validity_months": 36,
        "is_active": True,
    },
    {
        "program_code": "TRN-TECH-002",
        "program_name": "Advanced Credit Analysis",
        "description": "Advanced techniques in credit analysis including ratio analysis, cash flow analysis, and industry assessment",
        "category": "TECHNICAL",
        "training_type": "SKILL_BASED",
        "duration_hours": 24,
        "max_participants": 25,
        "min_participants": 8,
        "cost_per_participant": Decimal("5000.00"),
        "certification_required": True,
        "validity_months": 36,
        "is_active": True,
    },
    {
        "program_code": "TRN-TECH-003",
        "program_name": "Collections & Recovery Management",
        "description": "Best practices in collections, negotiation skills, and legal recovery procedures",
        "category": "TECHNICAL",
        "training_type": "SKILL_BASED",
        "duration_hours": 12,
        "max_participants": 40,
        "min_participants": 15,
        "cost_per_participant": Decimal("2500.00"),
        "certification_required": False,
        "validity_months": 24,
        "is_active": True,
    },
    {
        "program_code": "TRN-TECH-004",
        "program_name": "SARFAESI Act & Legal Recovery",
        "description": "Comprehensive training on SARFAESI procedures, DRT filing, and legal recovery mechanisms",
        "category": "TECHNICAL",
        "training_type": "SKILL_BASED",
        "duration_hours": 16,
        "max_participants": 30,
        "min_participants": 10,
        "cost_per_participant": Decimal("4000.00"),
        "certification_required": True,
        "validity_months": 24,
        "is_active": True,
    },
    {
        "program_code": "TRN-TECH-005",
        "program_name": "Property Valuation Basics",
        "description": "Understanding property valuation methods, documentation, and market analysis",
        "category": "TECHNICAL",
        "training_type": "SKILL_BASED",
        "duration_hours": 12,
        "max_participants": 25,
        "min_participants": 8,
        "cost_per_participant": Decimal("3000.00"),
        "certification_required": True,
        "validity_months": 36,
        "is_active": True,
    },
    # Soft Skills
    {
        "program_code": "TRN-SOFT-001",
        "program_name": "Effective Communication Skills",
        "description": "Developing verbal and written communication skills for professional excellence",
        "category": "SOFT_SKILLS",
        "training_type": "DEVELOPMENT",
        "duration_hours": 8,
        "max_participants": 30,
        "min_participants": 10,
        "cost_per_participant": Decimal("2000.00"),
        "certification_required": False,
        "validity_months": None,
        "is_active": True,
    },
    {
        "program_code": "TRN-SOFT-002",
        "program_name": "Customer Service Excellence",
        "description": "Building customer-centric mindset and handling difficult customer situations",
        "category": "SOFT_SKILLS",
        "training_type": "DEVELOPMENT",
        "duration_hours": 8,
        "max_participants": 40,
        "min_participants": 15,
        "cost_per_participant": Decimal("1800.00"),
        "certification_required": False,
        "validity_months": None,
        "is_active": True,
    },
    {
        "program_code": "TRN-SOFT-003",
        "program_name": "Negotiation Skills",
        "description": "Effective negotiation techniques for sales, collections, and vendor management",
        "category": "SOFT_SKILLS",
        "training_type": "DEVELOPMENT",
        "duration_hours": 12,
        "max_participants": 25,
        "min_participants": 10,
        "cost_per_participant": Decimal("2500.00"),
        "certification_required": False,
        "validity_months": None,
        "is_active": True,
    },
    # Leadership Training
    {
        "program_code": "TRN-LEAD-001",
        "program_name": "First Time Manager Program",
        "description": "Transition program for individual contributors becoming managers",
        "category": "LEADERSHIP",
        "training_type": "DEVELOPMENT",
        "duration_hours": 24,
        "max_participants": 20,
        "min_participants": 8,
        "cost_per_participant": Decimal("8000.00"),
        "certification_required": True,
        "validity_months": None,
        "is_active": True,
    },
    {
        "program_code": "TRN-LEAD-002",
        "program_name": "Leadership Excellence Program",
        "description": "Advanced leadership program for senior managers",
        "category": "LEADERSHIP",
        "training_type": "DEVELOPMENT",
        "duration_hours": 40,
        "max_participants": 15,
        "min_participants": 5,
        "cost_per_participant": Decimal("25000.00"),
        "certification_required": True,
        "validity_months": None,
        "is_active": True,
    },
    {
        "program_code": "TRN-LEAD-003",
        "program_name": "Performance Management Workshop",
        "description": "Effective performance management, goal setting, and feedback techniques",
        "category": "LEADERSHIP",
        "training_type": "DEVELOPMENT",
        "duration_hours": 8,
        "max_participants": 25,
        "min_participants": 10,
        "cost_per_participant": Decimal("3000.00"),
        "certification_required": False,
        "validity_months": None,
        "is_active": True,
    },
    # IT & Digital
    {
        "program_code": "TRN-IT-001",
        "program_name": "MS Excel Advanced",
        "description": "Advanced Excel including macros, VBA, and data analysis",
        "category": "IT_SKILLS",
        "training_type": "SKILL_BASED",
        "duration_hours": 16,
        "max_participants": 25,
        "min_participants": 10,
        "cost_per_participant": Decimal("2500.00"),
        "certification_required": True,
        "validity_months": None,
        "is_active": True,
    },
    {
        "program_code": "TRN-IT-002",
        "program_name": "Cyber Security Awareness",
        "description": "Cyber security best practices, phishing awareness, and data protection",
        "category": "IT_SKILLS",
        "training_type": "MANDATORY",
        "duration_hours": 4,
        "max_participants": 100,
        "min_participants": 20,
        "cost_per_participant": Decimal("500.00"),
        "certification_required": True,
        "validity_months": 12,
        "is_active": True,
    },
    {
        "program_code": "TRN-IT-003",
        "program_name": "ERP System Training",
        "description": "Training on organization's ERP system modules and workflows",
        "category": "IT_SKILLS",
        "training_type": "ONBOARDING",
        "duration_hours": 16,
        "max_participants": 20,
        "min_participants": 5,
        "cost_per_participant": Decimal("0.00"),
        "certification_required": False,
        "validity_months": None,
        "is_active": True,
    },
    # Onboarding
    {
        "program_code": "TRN-ONB-001",
        "program_name": "New Employee Orientation",
        "description": "Comprehensive orientation covering company policies, culture, and systems",
        "category": "ONBOARDING",
        "training_type": "ONBOARDING",
        "duration_hours": 8,
        "max_participants": 30,
        "min_participants": 5,
        "cost_per_participant": Decimal("0.00"),
        "certification_required": False,
        "validity_months": None,
        "is_active": True,
    },
    {
        "program_code": "TRN-ONB-002",
        "program_name": "Product Knowledge Training",
        "description": "In-depth training on all loan products, features, and eligibility criteria",
        "category": "ONBOARDING",
        "training_type": "ONBOARDING",
        "duration_hours": 16,
        "max_participants": 25,
        "min_participants": 5,
        "cost_per_participant": Decimal("0.00"),
        "certification_required": True,
        "validity_months": 24,
        "is_active": True,
    },
]


# =============================================================================
# APPRAISAL CYCLES DATA
# =============================================================================

current_year = date.today().year

APPRAISAL_CYCLES = [
    {
        "cycle_code": f"APR-{current_year}-H1",
        "cycle_name": f"H1 {current_year} Performance Review",
        "description": f"Half-yearly performance review for April-September {current_year}",
        "cycle_type": "HALF_YEARLY",
        "start_date": date(current_year, 4, 1),
        "end_date": date(current_year, 9, 30),
        "goal_setting_start": date(current_year, 4, 1),
        "goal_setting_end": date(current_year, 4, 15),
        "self_appraisal_start": date(current_year, 9, 15),
        "self_appraisal_end": date(current_year, 9, 25),
        "manager_review_start": date(current_year, 9, 26),
        "manager_review_end": date(current_year, 10, 10),
        "calibration_start": date(current_year, 10, 11),
        "calibration_end": date(current_year, 10, 20),
        "status": "ACTIVE",
        "is_active": True,
    },
    {
        "cycle_code": f"APR-{current_year}-H2",
        "cycle_name": f"H2 {current_year} Performance Review",
        "description": f"Half-yearly performance review for October {current_year} - March {current_year + 1}",
        "cycle_type": "HALF_YEARLY",
        "start_date": date(current_year, 10, 1),
        "end_date": date(current_year + 1, 3, 31),
        "goal_setting_start": date(current_year, 10, 1),
        "goal_setting_end": date(current_year, 10, 15),
        "self_appraisal_start": date(current_year + 1, 3, 15),
        "self_appraisal_end": date(current_year + 1, 3, 25),
        "manager_review_start": date(current_year + 1, 3, 26),
        "manager_review_end": date(current_year + 1, 4, 10),
        "calibration_start": date(current_year + 1, 4, 11),
        "calibration_end": date(current_year + 1, 4, 20),
        "status": "DRAFT",
        "is_active": True,
    },
    {
        "cycle_code": f"APR-{current_year}-ANNUAL",
        "cycle_name": f"Annual Performance Review FY{current_year}-{str(current_year + 1)[-2:]}",
        "description": f"Annual performance review for FY {current_year}-{current_year + 1}",
        "cycle_type": "ANNUAL",
        "start_date": date(current_year, 4, 1),
        "end_date": date(current_year + 1, 3, 31),
        "goal_setting_start": date(current_year, 4, 1),
        "goal_setting_end": date(current_year, 4, 30),
        "self_appraisal_start": date(current_year + 1, 3, 1),
        "self_appraisal_end": date(current_year + 1, 3, 15),
        "manager_review_start": date(current_year + 1, 3, 16),
        "manager_review_end": date(current_year + 1, 3, 31),
        "calibration_start": date(current_year + 1, 4, 1),
        "calibration_end": date(current_year + 1, 4, 15),
        "status": "ACTIVE",
        "is_active": True,
    },
    {
        "cycle_code": f"APR-{current_year}-PROB",
        "cycle_name": f"Probation Review {current_year}",
        "description": "Ongoing probation confirmation reviews",
        "cycle_type": "PROBATION",
        "start_date": date(current_year, 1, 1),
        "end_date": date(current_year, 12, 31),
        "goal_setting_start": None,
        "goal_setting_end": None,
        "self_appraisal_start": None,
        "self_appraisal_end": None,
        "manager_review_start": None,
        "manager_review_end": None,
        "calibration_start": None,
        "calibration_end": None,
        "status": "ACTIVE",
        "is_active": True,
    },
]


# =============================================================================
# GOAL CATEGORIES DATA
# =============================================================================

GOAL_CATEGORIES = [
    {
        "category_code": "GOAL-BUS",
        "category_name": "Business Goals",
        "description": "Revenue, targets, and business growth objectives",
        "weightage": Decimal("40.00"),
        "is_active": True,
    },
    {
        "category_code": "GOAL-OPS",
        "category_name": "Operational Excellence",
        "description": "Process improvement, efficiency, and quality objectives",
        "weightage": Decimal("25.00"),
        "is_active": True,
    },
    {
        "category_code": "GOAL-PPL",
        "category_name": "People & Team",
        "description": "Team development, collaboration, and leadership objectives",
        "weightage": Decimal("15.00"),
        "is_active": True,
    },
    {
        "category_code": "GOAL-LRN",
        "category_name": "Learning & Development",
        "description": "Skill development and certification objectives",
        "weightage": Decimal("10.00"),
        "is_active": True,
    },
    {
        "category_code": "GOAL-INN",
        "category_name": "Innovation & Initiative",
        "description": "Process innovation and special project objectives",
        "weightage": Decimal("10.00"),
        "is_active": True,
    },
]


# =============================================================================
# RATING SCALES DATA
# =============================================================================

RATING_SCALES = [
    {
        "scale_code": "RATING-5",
        "scale_name": "5-Point Rating Scale",
        "description": "Standard 5-point performance rating scale",
        "min_rating": 1,
        "max_rating": 5,
        "is_default": True,
        "is_active": True,
        "ratings": [
            {"value": 5, "label": "Outstanding", "description": "Exceptional performance that far exceeds expectations"},
            {"value": 4, "label": "Exceeds Expectations", "description": "Performance that consistently exceeds expectations"},
            {"value": 3, "label": "Meets Expectations", "description": "Solid performance that meets all expectations"},
            {"value": 2, "label": "Needs Improvement", "description": "Performance that partially meets expectations"},
            {"value": 1, "label": "Unsatisfactory", "description": "Performance that does not meet expectations"},
        ],
    },
]


# =============================================================================
# COMPETENCIES DATA
# =============================================================================

COMPETENCIES = [
    # Core Competencies
    {
        "competency_code": "COMP-CUST",
        "competency_name": "Customer Focus",
        "description": "Understanding and meeting customer needs, building relationships",
        "category": "CORE",
        "is_active": True,
    },
    {
        "competency_code": "COMP-INTG",
        "competency_name": "Integrity & Ethics",
        "description": "Acting with honesty, maintaining ethical standards",
        "category": "CORE",
        "is_active": True,
    },
    {
        "competency_code": "COMP-TEAM",
        "competency_name": "Teamwork & Collaboration",
        "description": "Working effectively with others, contributing to team success",
        "category": "CORE",
        "is_active": True,
    },
    {
        "competency_code": "COMP-COMM",
        "competency_name": "Communication",
        "description": "Expressing ideas clearly, listening actively",
        "category": "CORE",
        "is_active": True,
    },
    {
        "competency_code": "COMP-RSLT",
        "competency_name": "Results Orientation",
        "description": "Focus on achieving goals and delivering quality outcomes",
        "category": "CORE",
        "is_active": True,
    },
    # Functional Competencies
    {
        "competency_code": "COMP-ANLYT",
        "competency_name": "Analytical Thinking",
        "description": "Ability to analyze data, identify patterns, and make informed decisions",
        "category": "FUNCTIONAL",
        "is_active": True,
    },
    {
        "competency_code": "COMP-PROB",
        "competency_name": "Problem Solving",
        "description": "Identifying issues and developing effective solutions",
        "category": "FUNCTIONAL",
        "is_active": True,
    },
    {
        "competency_code": "COMP-PLAN",
        "competency_name": "Planning & Organization",
        "description": "Setting priorities, managing time, and organizing resources",
        "category": "FUNCTIONAL",
        "is_active": True,
    },
    # Leadership Competencies
    {
        "competency_code": "COMP-LEAD",
        "competency_name": "Leadership",
        "description": "Inspiring and guiding others toward common goals",
        "category": "LEADERSHIP",
        "is_active": True,
    },
    {
        "competency_code": "COMP-DECN",
        "competency_name": "Decision Making",
        "description": "Making timely and effective decisions",
        "category": "LEADERSHIP",
        "is_active": True,
    },
    {
        "competency_code": "COMP-CHNG",
        "competency_name": "Change Management",
        "description": "Adapting to change and helping others through transitions",
        "category": "LEADERSHIP",
        "is_active": True,
    },
    {
        "competency_code": "COMP-DEVP",
        "competency_name": "Developing Others",
        "description": "Coaching, mentoring, and developing team members",
        "category": "LEADERSHIP",
        "is_active": True,
    },
]


# =============================================================================
# MAIN EXECUTION
# =============================================================================

async def main():
    """Main execution function."""
    print("=" * 60)
    print("HR Training & Performance Module Direct Seed Script")
    print("=" * 60)

    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            # Get organization ID
            result = await session.execute(text("SELECT id FROM mst_organization LIMIT 1"))
            org_row = result.fetchone()
            if not org_row:
                print("✗ No organization found. Please run seed_data.py first.")
                return
            org_id = org_row[0]
            print(f"✓ Using organization: {org_id}")

            # Get user ID for created_by
            result = await session.execute(text("SELECT id FROM mst_user WHERE is_active = true LIMIT 1"))
            user_row = result.fetchone()
            user_id = user_row[0] if user_row else None

            # Seed Training Programs
            print("\n--- Seeding Training Programs ---")
            count = 0
            for prog_data in TRAINING_PROGRAMS:
                # Check if exists
                result = await session.execute(
                    text("SELECT id FROM mst_training_program WHERE organization_id = :org_id AND program_code = :code"),
                    {"org_id": org_id, "code": prog_data["program_code"]}
                )
                if result.fetchone():
                    print(f"  - Skipped (exists): {prog_data['program_code']}")
                    continue

                # Insert training program
                await session.execute(
                    text("""
                        INSERT INTO mst_training_program (
                            organization_id, program_code, program_name, description,
                            category, training_type, duration_hours, max_participants,
                            min_participants, cost_per_participant, certification_required,
                            validity_months, is_active, created_by_id
                        ) VALUES (
                            :org_id, :program_code, :program_name, :description,
                            :category, :training_type, :duration_hours, :max_participants,
                            :min_participants, :cost_per_participant, :certification_required,
                            :validity_months, :is_active, :user_id
                        )
                    """),
                    {
                        "org_id": org_id,
                        "program_code": prog_data["program_code"],
                        "program_name": prog_data["program_name"],
                        "description": prog_data["description"],
                        "category": prog_data["category"],
                        "training_type": prog_data["training_type"],
                        "duration_hours": prog_data["duration_hours"],
                        "max_participants": prog_data["max_participants"],
                        "min_participants": prog_data["min_participants"],
                        "cost_per_participant": prog_data["cost_per_participant"],
                        "certification_required": prog_data["certification_required"],
                        "validity_months": prog_data["validity_months"],
                        "is_active": prog_data["is_active"],
                        "user_id": user_id,
                    }
                )
                count += 1
            await session.commit()
            print(f"  ✓ Created {count} training programs")

            # Seed Appraisal Cycles
            print("\n--- Seeding Appraisal Cycles ---")
            count = 0
            for cycle_data in APPRAISAL_CYCLES:
                # Check if exists
                result = await session.execute(
                    text("SELECT id FROM mst_appraisal_cycle WHERE organization_id = :org_id AND cycle_code = :code"),
                    {"org_id": org_id, "code": cycle_data["cycle_code"]}
                )
                if result.fetchone():
                    print(f"  - Skipped (exists): {cycle_data['cycle_code']}")
                    continue

                # Insert appraisal cycle
                await session.execute(
                    text("""
                        INSERT INTO mst_appraisal_cycle (
                            organization_id, cycle_code, cycle_name, description,
                            cycle_type, start_date, end_date,
                            goal_setting_start, goal_setting_end,
                            self_appraisal_start, self_appraisal_end,
                            manager_review_start, manager_review_end,
                            calibration_start, calibration_end,
                            status, is_active, created_by_id
                        ) VALUES (
                            :org_id, :cycle_code, :cycle_name, :description,
                            :cycle_type, :start_date, :end_date,
                            :goal_setting_start, :goal_setting_end,
                            :self_appraisal_start, :self_appraisal_end,
                            :manager_review_start, :manager_review_end,
                            :calibration_start, :calibration_end,
                            :status, :is_active, :user_id
                        )
                    """),
                    {
                        "org_id": org_id,
                        "cycle_code": cycle_data["cycle_code"],
                        "cycle_name": cycle_data["cycle_name"],
                        "description": cycle_data["description"],
                        "cycle_type": cycle_data["cycle_type"],
                        "start_date": cycle_data["start_date"],
                        "end_date": cycle_data["end_date"],
                        "goal_setting_start": cycle_data["goal_setting_start"],
                        "goal_setting_end": cycle_data["goal_setting_end"],
                        "self_appraisal_start": cycle_data["self_appraisal_start"],
                        "self_appraisal_end": cycle_data["self_appraisal_end"],
                        "manager_review_start": cycle_data["manager_review_start"],
                        "manager_review_end": cycle_data["manager_review_end"],
                        "calibration_start": cycle_data["calibration_start"],
                        "calibration_end": cycle_data["calibration_end"],
                        "status": cycle_data["status"],
                        "is_active": cycle_data["is_active"],
                        "user_id": user_id,
                    }
                )
                count += 1
            await session.commit()
            print(f"  ✓ Created {count} appraisal cycles")

            print("\n" + "=" * 60)
            print("✓ HR Training & Performance seed data created successfully!")
            print("=" * 60)

        except Exception as e:
            await session.rollback()
            print(f"\n✗ Error: {e}")
            import traceback
            traceback.print_exc()
            raise
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
