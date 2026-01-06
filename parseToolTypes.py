import pandas as pd
from sqlalchemy import create_engine
import json

# Connect to your Postgres DB (adjust connection string as needed)
from dotenv import load_dotenv
import os

load_dotenv()
DB_URL = os.getenv("DB_URL")
if not DB_URL:
    raise EnvironmentError("DB_URL environment variable is not set")
engine = create_engine(DB_URL)

file = "C:/Users/JGI/Jeff H/Escape Dantes Inferno/QualerInternalAPI/ToolTypes.json"
with open(file, "r") as f:
    data = json.load(f)

df = pd.DataFrame(data)
df.to_sql("tool_types", engine, if_exists="append", index=False)

# # Then, run this SQL:
# ALTER TABLE IF EXISTS public.tool_types DROP COLUMN IF EXISTS "Selected";

# ALTER TABLE IF EXISTS public.tool_types
#     ALTER COLUMN "Text" SET NOT NULL;

# ALTER TABLE IF EXISTS public.tool_types
#     ALTER COLUMN "Value" SET NOT NULL;
# ALTER TABLE IF EXISTS public.tool_types
#     ADD PRIMARY KEY ("Value");

# ALTER TABLE IF EXISTS public.tool_types
#     RENAME "Text" TO name;

# ALTER TABLE IF EXISTS public.tool_types
#     RENAME "Value" TO id;
