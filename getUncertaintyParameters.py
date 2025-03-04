from my_qualer_utils import QualerAPIFetcher
from tqdm import tqdm

with QualerAPIFetcher() as api:
    measurementIDs = api.run_sql("SELECT measurementid FROM measurements LIMIT 10;")
    uncertaintyBudgetIDs = api.run_sql(
        """SELECT "UncertaintyBudgetId" FROM uncertainty_budgets LIMIT 10;"""
    )
    for measurementID in tqdm(measurementIDs):
        for uncertaintyBudgetID in uncertaintyBudgetIDs:
            url = (
                "https://jgiquality.qualer.com/work/Uncertainties/UncertaintyParameters?"
                f"measurementId={measurementID[0]}&uncertaintyBudgetId={uncertaintyBudgetID[0]}"
            )
            try:
                api.fetch_and_store(url, "UncertaintyParameters")
            except Exception as e:
                print(f"Error fetching {url}: {e}")
