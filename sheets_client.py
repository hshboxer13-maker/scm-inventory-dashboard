import os

import gspread
import pandas as pd
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials

load_dotenv()

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]


def get_client() -> gspread.Client:
    creds_path = os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
    creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
    return gspread.authorize(creds)


def load_inventory_df() -> pd.DataFrame:
    client = get_client()
    spreadsheet_id = os.environ["SPREADSHEET_ID"]
    sheet_name = os.environ["SHEET_NAME"]

    worksheet = client.open_by_key(spreadsheet_id).worksheet(sheet_name)
    records = worksheet.get_all_records()
    return pd.DataFrame(records)


if __name__ == "__main__":
    df = load_inventory_df()
    print(f"rows: {len(df)}, columns: {list(df.columns)}")
    print(df.head())
