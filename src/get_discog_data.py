# Get Discogs data

import requests
import pandas as pd
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import os
from dotenv import load_dotenv

load_dotenv()

def get_discogs_data():
    api_key = os.getenv("DISCOGS_TOKEN")
    url = f"https://api.discogs.com/artists/1?callback={api_key}"
    response = requests.get(url)
    data = response.json()
    return data

if __name__ == "__main__":
    data = get_discogs_data()
    print(data)