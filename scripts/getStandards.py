"""
Extract standards (specifications) from Qualer API via Standard_Read.

Run:
    python scripts/getStandards.py

Outputs:
    - standards_page1.json (first page)
    - standards_page1.csv (first page)
"""

import json
import pandas as pd
from utils.auth import QualerAPIFetcher
from qualer_internal_sdk.endpoints.specifications import (
    get_standards_page,
)


def main():
    page_size = 50
    page_number = 1

    with QualerAPIFetcher() as fetcher:
        standards_page = get_standards_page(
            fetcher=fetcher,
            page=page_number,
            page_size=page_size,
            standard_filter="All",
            search="",
            product_id="",
            area_id=None,  # Sends "NaN" as observed in UI
        )

        print(
            f"Fetched {len(standards_page.items)} standards "
            f"(page {page_number}, total reported {standards_page.total})"
        )

        records = [vars(item) for item in standards_page.items]

        json_output = "standards_page1.json"
        with open(json_output, "w") as f:
            json.dump(records, f, indent=2)
        print(f"Saved {json_output}")

        csv_output = "standards_page1.csv"
        df = pd.json_normalize(records)
        df.to_csv(csv_output, index=False)
        print(f"Saved {csv_output}")

        # To fetch more pages, adjust `page` or loop with get_standards_page()
        # To fetch all (potentially large), use get_all_standards() with a max_pages limit.


if __name__ == "__main__":
    main()
