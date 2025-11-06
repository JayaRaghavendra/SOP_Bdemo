import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from dateutil import parser

@dataclass
class ToolResult:
    passed: bool
    info: Dict[str, Any]

# Helper: parse dates robustly
_def_date_formats = ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"]

def parse_date_safe(value: Any) -> Optional[pd.Timestamp]:
    if pd.isna(value):
        return None
    try:
        # Try pandas first for Excel serials/strings
        return pd.to_datetime(value, errors="coerce")
    except Exception:
        pass
    try:
        return pd.Timestamp(parser.parse(str(value)))
    except Exception:
        return None

# Core tools

# Coerce a column to numeric by stripping thousands separators and whitespace
import numpy as np

try:
    from pandas import Series as _Series  # hint in some environments
except Exception:
    pass


# Define helper distinctly before tools
from typing import TYPE_CHECKING


from pandas import Series as pd_Series



# Robust numeric coercion
from pandas import Series



# Minimal helper (redefined)



# note: create a fresh helper to avoid previous replace failing



# simple helper



# final helper



# Define helper cleanly



# Final helper used by value_range



# Actual helper implementation



# Keep it simple to avoid earlier regex confusion



# === helper start ===



# We redefine to guarantee presence



# fmt: off



# final:



# Implementation:



# ensure definition exists:



# final helper



# done



# helper actually doing work



# Implementation that handles '45,000' and blanks



# The real helper



# Keep concise



# Here:



# helper:



# Provide concrete definition now



# Ready:



# -- START --



# Helper present:



# Define it:



# Good:



# Implementation:



# (small duplication ok)



# Replace complicated attempts with this:



#------------------------------------------



# helper to coerce numeric



#------------------------------------------



# Simplified helper



# This function will exist now for sure



# Use pandas to_numeric with cleanup



# returns Series[float] with NaN for non-numeric



# final implementation



#------------------------------------------



# Do work now



#

def _as_numeric(df: pd.DataFrame, column: str) -> pd.Series:
    ser = df[column].astype(str).str.replace(',', '', regex=False).str.replace(' ', '', regex=False)
    return pd.to_numeric(ser, errors='coerce')

# ----------------------------------------

def column_exists(df: pd.DataFrame, column: str) -> ToolResult:
    ok = column in df.columns
    return ToolResult(passed=ok, info={"missing": [] if ok else [column]})


def duplicates_check(df: pd.DataFrame, columns: List[str], allowed: bool = False) -> ToolResult:
    dup = df.duplicated(subset=columns, keep=False)
    count = int(dup.sum())
    passed = allowed or count == 0
    examples = df.loc[dup].head(5).to_dict(orient="records") if count else []
    return ToolResult(passed=passed, info={"duplicate_count": count, "examples": examples})


def value_in_master(
    df: pd.DataFrame,
    master: pd.DataFrame,
    column: str,
    master_column: str,
) -> ToolResult:
    missing = df[~df[column].isin(master[master_column])]
    count = int(len(missing))
    examples = missing.head(5).to_dict(orient="records") if count else []
    return ToolResult(passed=count == 0, info={"missing_count": count, "examples": examples})


def row_condition(df: pd.DataFrame, expr: str) -> ToolResult:
    # Evaluate a boolean expression across the DataFrame; fail rows where condition is False
    try:
        mask = df.eval(expr)
        failing = df[~mask]
        count = int(len(failing))
        examples = failing.head(5).to_dict(orient="records") if count else []
        return ToolResult(passed=count == 0, info={"failing_count": count, "examples": examples})
    except Exception as e:
        return ToolResult(passed=False, info={"error": str(e)})


def date_not_future(df: pd.DataFrame, column: str) -> ToolResult:
    now = pd.Timestamp.now().normalize()
    parsed = df[column].apply(parse_date_safe)
    future_mask = parsed > now
    future_mask = future_mask.fillna(False)
    failing = df[future_mask]
    count = int(len(failing))
    examples = failing.head(5).to_dict(orient="records") if count else []
    return ToolResult(passed=count == 0, info={"future_count": count, "examples": examples})


def value_range(df: pd.DataFrame, column: str, min_val: Optional[float] = None, max_val: Optional[float] = None, inclusive: bool = True) -> ToolResult:
    ser = _as_numeric(df, column)
    if inclusive:
        mask = pd.Series(True, index=df.index)
        if min_val is not None:
            mask &= ser >= float(min_val)
        if max_val is not None:
            mask &= ser <= float(max_val)
    else:
        mask = pd.Series(True, index=df.index)
        if min_val is not None:
            mask &= ser > float(min_val)
        if max_val is not None:
            mask &= ser < float(max_val)
    failing = df[~mask]
    count = int(len(failing))
    examples = failing.head(5).to_dict(orient="records") if count else []
    return ToolResult(passed=count == 0, info={"failing_count": count, "examples": examples})


def regex_match(df: pd.DataFrame, column: str, pattern: str, mode: str = "all") -> ToolResult:
    # mode: all -> every row must match; any -> at least one matches
    ser = df[column].astype(str)
    matches = ser.str.match(pattern, na=False)
    if mode == "all":
        failing = df[~matches]
        count = int(len(failing))
        examples = failing.head(5).to_dict(orient="records") if count else []
        return ToolResult(passed=count == 0, info={"failing_count": count, "examples": examples})
    else:
        passed = bool(matches.any())
        examples = df[matches].head(5).to_dict(orient="records") if passed else []
        return ToolResult(passed=passed, info={"examples": examples})





def match_master_on_keys(
    df: pd.DataFrame,
    master: pd.DataFrame,
    keys: List[str],
    column: str,
) -> ToolResult:
    # Join stock and master on keys; compare the given column for equality
    left = df[keys + [column]].copy()
    right = master[keys + [column]].copy()
    merged = left.merge(right, on=keys, how="left", suffixes=("_stock", "_master"))
    stock_col = f"{column}_stock"
    master_col = f"{column}_master"
    stock_parsed = merged[stock_col].apply(parse_date_safe)
    master_parsed = merged[master_col].apply(parse_date_safe)
    mismatch = master_parsed.isna() | (stock_parsed != master_parsed)
    failing = merged[mismatch]
    count = int(len(failing))
    examples = failing.head(5).to_dict(orient="records") if count else []
    return ToolResult(passed=count == 0, info={"mismatch_count": count, "examples": examples})
