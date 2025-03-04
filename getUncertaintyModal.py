from my_qualer_utils import QualerAPIFetcher
from tqdm import tqdm

with QualerAPIFetcher() as api:
    query = """SELECT
        m.measurementid,
        ms.batchid
    FROM measurements m
    JOIN measurement_points mp ON m.measurementid = mp.measurementid
    JOIN measurement_sets ms ON mp.measurementsetid = ms.measurementsetid
    LIMIT 10;
"""
    queryResult = api.run_sql(query)
    for (measurementID, batchId) in tqdm(queryResult):
        url = (
            "https://jgiquality.qualer.com/work/Uncertainties/UncertaintyModal?"
            f"measurementId={measurementID}&MeasurementBatchId={batchId}"
        )
        try:
            api.fetch_and_store(url, "UncertaintyModal")
        except Exception as e:
            print(f"Error fetching {url}: {e}")
