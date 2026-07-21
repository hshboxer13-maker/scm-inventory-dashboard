import os

import gspread
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials

load_dotenv()

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]


def _secret_or_env(key: str) -> str:
    """Streamlit Cloud에 배포되면 st.secrets, 로컬에서는 .env 값을 사용."""
    try:
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.environ[key]


def get_client() -> gspread.Client:
    try:
        if "gcp_service_account" in st.secrets:
            creds = Credentials.from_service_account_info(
                dict(st.secrets["gcp_service_account"]), scopes=SCOPES
            )
            return gspread.authorize(creds)
    except Exception:
        pass

    creds_path = os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
    creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
    return gspread.authorize(creds)


def load_inventory_df() -> pd.DataFrame:
    client = get_client()
    spreadsheet_id = _secret_or_env("SPREADSHEET_ID")
    sheet_name = _secret_or_env("SHEET_NAME")

    worksheet = client.open_by_key(spreadsheet_id).worksheet(sheet_name)
    records = worksheet.get_all_records()
    return pd.DataFrame(records)


if __name__ == "__main__":
    df = load_inventory_df()
    print(f"rows: {len(df)}, columns: {list(df.columns)}")
    print(df.head())
