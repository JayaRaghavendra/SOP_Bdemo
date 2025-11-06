from typing import Dict, Any, Optional
import pandas as pd

from .tools import (
    ToolResult,
    column_exists,
    duplicates_check,
    value_in_master,
    row_condition,
    date_not_future,
    value_range,
    regex_match,
    match_master_on_keys,
)
from .router import route_check

TOOLS = {
    "column_exists": column_exists,
    "duplicates_check": duplicates_check,
    "value_in_master": value_in_master,
    "row_condition": row_condition,
    "date_not_future": date_not_future,
    "value_range": value_range,
    "regex_match": regex_match,
    "match_master_on_keys": match_master_on_keys,
}


def run_check(check_text: str, stock_df: pd.DataFrame, master_df: Optional[pd.DataFrame], gr_df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
    intent = route_check(check_text)
    if not intent:
        return {"check": check_text, "tool": None, "passed": False, "details": {"error": "Unable to route check"}}
    tool_name = intent["tool"]
    print("############## Running tool:", tool_name)
    args = intent.get("args", {})
    print("With args:", args)

    fn = TOOLS.get(tool_name)
    if not fn:
        return {"check": check_text, "tool": tool_name, "passed": False, "details": {"error": "Unknown tool"}}

    try:
        if tool_name == "value_in_master":
            if master_df is None:
                return {"check": check_text, "tool": tool_name, "passed": False, "details": {"error": "Master data required"}}
            res: ToolResult = fn(stock_df, master_df, args["column"], args["master_column"])  # type: ignore
        elif tool_name == "duplicates_check":
            dataset = args.get("dataset")
            target_df = gr_df if dataset == "gr" and gr_df is not None else stock_df
            res = fn(target_df, args["columns"], args.get("allowed", False))  # type: ignore
        elif tool_name == "column_exists":
            res = fn(stock_df, args["column"])  # type: ignore
        elif tool_name == "row_condition":
            res = fn(stock_df, args["expr"])  # type: ignore
        elif tool_name == "date_not_future":
            res = fn(stock_df, args["column"])  # type: ignore
        elif tool_name == "value_range":
            res = fn(stock_df, args["column"], args.get("min_val"), args.get("max_val"), args.get("inclusive", True))  # type: ignore
        elif tool_name == "regex_match":
            res = fn(stock_df, args["column"], args["pattern"], args.get("mode", "all"))  # type: ignore
        elif tool_name == "match_master_on_keys":
            if master_df is None:
                return {"check": check_text, "tool": tool_name, "passed": False, "details": {"error": "Master data required"}}
            res = fn(stock_df, master_df, args["keys"], args["column"])  # type: ignore
        else:
            return {"check": check_text, "tool": tool_name, "passed": False, "details": {"error": "Unhandled tool"}}
    except Exception as e:
        return {"check": check_text, "tool": tool_name, "passed": False, "details": {"error": str(e), "args": args}}

    return {"check": check_text, "tool": tool_name, "passed": res.passed, "details": res.info}
