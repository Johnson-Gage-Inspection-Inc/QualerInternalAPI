"""Fetch service groups from Qualer and store in database.

Uses the unified QualerClient interface to fetch service group data
for all service order items in the system.
"""

from qualer_internal_sdk import QualerClient


def main():
    """Fetch and store service groups for all work items."""
    with QualerClient() as client:
        # Query database for all work item IDs
        query = """SELECT workitemid FROM work_items;"""
        work_items = client.client_dashboard.api.run_sql(query)
        work_item_ids = [row[0] for row in work_items]

        print(f"Fetching service groups for {len(work_item_ids)} work items...")

        # Fetch service groups for all items
        results = client.service.service_groups.fetch_for_service_order_items(
            work_item_ids, service_name="GetServiceGroupsForExistingLevels"
        )

        successful = sum(1 for r in results.values() if "error" not in r)
        failed = len(results) - successful
        print(f"✓ Successfully fetched {successful} items")
        if failed > 0:
            print(f"⚠ Failed to fetch {failed} items")


if __name__ == "__main__":
    main()
