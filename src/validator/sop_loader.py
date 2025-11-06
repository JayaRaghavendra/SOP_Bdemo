from typing import Tuple
import pandas as pd

REQUIRED_SOP_COL = "checks"

def load_sop(path: str) -> pd.DataFrame:
    df = pd.read_excel(path) if path.lower().endswith((".xlsx", ".xls")) else pd.read_csv(path)
    if REQUIRED_SOP_COL not in df.columns:
        raise ValueError(f"SOP file must contain a column '{REQUIRED_SOP_COL}'")
    return df
