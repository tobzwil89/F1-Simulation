# Copyright (c) 2023 Team Analytics
# All rights reserved.

def get_race_data():

    # imports
    import os
    from pathlib import Path
    from dotenv import load_dotenv
    import requests
    from requests.auth import HTTPBasicAuth
    import pandas as pd
    from io import StringIO

    # Zugangsdaten kommen aus der Datei .env neben diesem Skript
    load_dotenv(Path(__file__).with_name('.env'))
    username = os.environ.get('F1_USERNAME', '')
    password = os.environ.get('F1_PASSWORD', '')
    if not username or not password:
        raise RuntimeError('F1_USERNAME und F1_PASSWORD fehlen. Bitte in .env eintragen.')

    file_url = 'https://team-analytics.com/f1/datacenter/remote/export_race_data.php'

    # make a GET request with HTTP basic authentication
    response = requests.get(file_url, auth=HTTPBasicAuth(username, password), stream=True, allow_redirects=False)

    # check if the request was successful and return data
    if response.status_code == 200:
        content = StringIO(response.text)
        df = pd.read_csv(content)
        return df
    else:
        return None