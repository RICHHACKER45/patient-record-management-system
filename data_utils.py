# ----------------------------
# FILE: data_utils.py
# Data handling using pandas. Encapsulated functions.
# ----------------------------
import pandas as pd

def db_to_dataframe(db_path: str = 'patients.db') -> pd.DataFrame:
    import sqlite3
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query('SELECT * FROM patients', conn)
    conn.close()
    return df

def dataframe_summary(df: pd.DataFrame) -> str:
    # simple textual summary used in reports
    return df.describe(include='all').to_string()

def save_dataframe_csv(df: pd.DataFrame, path: str = 'patients_df.csv') -> None:
    df.to_csv(path, index=False)