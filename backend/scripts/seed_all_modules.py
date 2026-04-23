"""
Master seed script that runs all module-specific seed scripts.
This script will seed data for all new modules in the correct order.

Usage:
    cd /Users/balakrishnavundavalli/working/talentfino/erp/backend
    source venv/bin/activate
    python scripts/seed_all_modules.py
"""

import asyncio
import subprocess
import sys
import os

# List of seed scripts to run in order
SEED_SCRIPTS = [
    "seed_inventory_data.py",
    "seed_hr_training_data.py",
    "seed_treasury_data.py",
    "seed_procurement_data.py",
    "seed_kyc_data.py",
    "seed_legal_data_direct.py",
    "seed_ess_masters.py",
]


def run_seed_script(script_name: str) -> bool:
    """Run a single seed script and return success status."""
    script_path = os.path.join(os.path.dirname(__file__), script_name)

    if not os.path.exists(script_path):
        print(f"⚠ Script not found: {script_name}")
        return True  # Continue with other scripts

    print(f"\n{'='*60}")
    print(f"Running: {script_name}")
    print(f"{'='*60}")

    try:
        result = subprocess.run(
            [sys.executable, script_path],
            cwd=os.path.dirname(os.path.dirname(__file__)),
            capture_output=False,
        )
        return result.returncode == 0
    except Exception as e:
        print(f"✗ Error running {script_name}: {e}")
        return False


def main():
    """Run all seed scripts."""
    print("=" * 70)
    print("NBFC ERP - Master Seed Data Script")
    print("=" * 70)
    print("\nThis script will seed data for the following modules:")
    for i, script in enumerate(SEED_SCRIPTS, 1):
        module_name = script.replace("seed_", "").replace("_data.py", "").replace("_direct.py", "").replace("_masters.py", "").replace("_", " ").title()
        print(f"  {i}. {module_name}")

    print("\n" + "-" * 70)

    success_count = 0
    failure_count = 0

    for script in SEED_SCRIPTS:
        if run_seed_script(script):
            success_count += 1
        else:
            failure_count += 1

    print("\n" + "=" * 70)
    print("SEED DATA SUMMARY")
    print("=" * 70)
    print(f"  ✓ Successful: {success_count}")
    print(f"  ✗ Failed: {failure_count}")
    print(f"  Total: {len(SEED_SCRIPTS)}")
    print("=" * 70)

    if failure_count > 0:
        print("\n⚠ Some seed scripts failed. Please check the logs above.")
        sys.exit(1)
    else:
        print("\n✓ All seed scripts completed successfully!")
        sys.exit(0)


if __name__ == "__main__":
    main()
