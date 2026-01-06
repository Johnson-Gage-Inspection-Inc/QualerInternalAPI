from my_qualer_utils import QualerAPIFetcher
from tqdm import tqdm

with QualerAPIFetcher() as api:
    query = """SELECT workitemid FROM work_items;"""
    queryResult = api.run_sql(query)
    for (workitemid) in tqdm(queryResult, dynamic_ncols=True):
        url = (
            "https://jgiquality.qualer.com/work/TaskDetails/GetServiceGroupsForExistingLevels?"
            f"serviceOrderItemId={workitemid[0]}"
        )
        try:
            api.fetch_and_store(url, "GetServiceGroupsForExistingLevels")
        except Exception as e:
            print(f"Error fetching {url}: {e}")
