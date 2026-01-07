"""Fetch uncertainty modals from Qualer and store in database.

Uses the unified QualerClient interface to fetch uncertainty modal data
for all measurement and batch combinations in the system.
"""

from qualer_internal_sdk import QualerClient


def main():
    """Fetch and store uncertainty modals for all measurement batches."""
    with QualerClient() as client:
        # Query database for measurement and batch combinations
        query = """SELECT
            m.measurementid,
            ms.batchid
        FROM measurements m
        JOIN measurement_points mp ON m.measurementid = mp.measurementid
        JOIN measurement_sets ms ON mp.measurementsetid = ms.measurementsetid
        LIMIT 10;
    """
        measurement_batches = [(row[0], row[1]) for row in client.uncertainty.api.run_sql(query)]

        print(f"Fetching uncertainty modals for {len(measurement_batches)} measurement batches...")

        # Fetch modals for all combinations
        results = client.uncertainty.modal.fetch_for_measurements(
            measurement_batches, service_name="UncertaintyModal"
        )

        successful = sum(1 for r in results.values() if "error" not in r)
        failed = len(results) - successful
        print(f"✓ Successfully fetched {successful} modals")
        if failed > 0:
            print(f"⚠ Failed to fetch {failed} modals")


if __name__ == "__main__":
    main()
