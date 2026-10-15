import os
import sys
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from dotenv import load_dotenv
load_dotenv()

mogo_uri = os.getenv("MONGOURL")

if not mogo_uri:
  print(
      "ERROR: MONGOURL environment variable is not set!", file=sys.stderr
  )
  sys.exit(1)

try:
  client = MongoClient(mogo_uri)
  print("Successfully connected to MongoDB!")

except ConnectionFailure as e:
  print(
      f"ERROR: Could not connect to MongoDB server: {e}",
      file=sys.stderr,
  )
  sys.exit(1)
except Exception as e:
  print(f"An unexpected error occurred during database setup: {e}", file=sys.stderr)
  sys.exit(1)


db = client["climate_analyzer"]
region_threshold_collection = db["threshold_cache"]
region_climate_collection = db["region_climate_cache"]
climate_trend_collection = db["climate_trend_cache"]