"""Fetch uncertainty parameters from Qualer and store in database.

Uses the unified QualerClient interface to fetch uncertainty parameter data
for all measurement and uncertainty budget combinations in the system.
"""

from qualer_internal_sdk import QualerClient


def main():
    """Fetch and store uncertainty parameters for all measurements."""
    with QualerClient() as client:
        # Query database for measurement IDs and uncertainty budget IDs
        measurement_ids = [
            row[0]
            for row in client.uncertainty.api.run_sql(
                "SELECT measurementid FROM measurements LIMIT 10;"
            )
        ]
        budget_ids = [
            row[0]
            for row in client.uncertainty.api.run_sql(
                """SELECT "UncertaintyBudgetId" FROM uncertainty_budgets LIMIT 10;"""
            )
        ]

        print(
            f"Fetching uncertainty parameters for {len(measurement_ids)} measurements "
            f"and {len(budget_ids)} budgets..."
        )

        # Fetch parameters for all combinations
        results = client.uncertainty.parameters.fetch_for_measurements(
            measurement_ids, budget_ids, service_name="UncertaintyParameters"
        )

        successful = sum(1 for r in results.values() if "error" not in r)
        failed = len(results) - successful
        print(f"✓ Successfully fetched {successful} parameter sets")
        if failed > 0:
            print(f"⚠ Failed to fetch {failed} parameter sets")


if __name__ == "__main__":
    main()
