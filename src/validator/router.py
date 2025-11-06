import json
import os
import re
from typing import Any, Dict, Optional
from dotenv import load_dotenv

try:
    from openai import AzureOpenAI
except Exception:
    AzureOpenAI = None  # type: ignore

TOOLS = [
    {
        "name": "column_exists",
        "args": {"type": "object", "properties": {"column": {"type": "string"}}, "required": ["column"]},
        "description": "Verify that a column exists in the target dataset.",
    },
    {
        "name": "duplicates_check",
        "args": {"type": "object", "properties": {"columns": {"type": "array", "items": {"type": "string"}}, "allowed": {"type": "boolean"}, "dataset": {"type": "string", "enum": ["stock", "gr"]}}, "required": ["columns"]},
        "description": "Check duplicate rows based on key columns. Optional dataset 'gr' for GR formats.",
    },
    {
        "name": "value_in_master",
        "args": {"type": "object", "properties": {"column": {"type": "string"}, "master_column": {"type": "string"}}, "required": ["column", "master_column"]},
        "description": "Validate that values of a stock column exist in master column.",
    },
    {
        "name": "row_condition",
        "args": {"type": "object", "properties": {"expr": {"type": "string"}}, "required": ["expr"]},
        "description": "Evaluate a pandas boolean expression across rows (e.g., `Current Stock > 0`).",
    },
    {
        "name": "date_not_future",
        "args": {"type": "object", "properties": {"column": {"type": "string"}}, "required": ["column"]},
        "description": "Ensure all dates in column are not in the future.",
    },
    {
        "name": "value_range",
        "args": {"type": "object", "properties": {"column": {"type": "string"}, "min_val": {"type": "number"}, "max_val": {"type": "number"}, "inclusive": {"type": "boolean"}}, "required": ["column"]},
        "description": "Numeric range validation. Use thousands separators compatible values.",
    },
    {
        "name": "regex_match",
        "args": {"type": "object", "properties": {"column": {"type": "string"}, "pattern": {"type": "string"}, "mode": {"type": "string", "enum": ["all", "any"]}}, "required": ["column", "pattern"]},
        "description": "Regex validation if the SOP explicitly defines a pattern to match.",
    },
    {
        "name": "match_master_on_keys",
        "args": {"type": "object", "properties": {"keys": {"type": "array", "items": {"type": "string"}}, "column": {"type": "string"}}, "required": ["keys", "column"]},
        "description": "Join stock to master on keys and compare a column (dates supported).",
    },
]

SYSTEM_PROMPT = (
    "You are a precise SOP check intent router. Given one check line, choose exactly one tool and arguments. "
    "Return strict JSON only: {\"tool\": <name>, \"args\": {..}}. If ambiguous, infer the most likely intent. "
    "Datasets available: stock, master, gr (Goods Receipt). Common columns: stock/master -> Material Code, Batch, Date of Manufacturing; gr -> Material Document. "
    "When check mentions MB51/GR, use dataset 'gr'. For manufacturing date vs documentation, compare stock vs master on keys ['Material Code','Batch'] and column 'Date of Manufacturing'. "
)

_last_error: Optional[str] = None


def _client_from_env():
    load_dotenv(override=True)
    key = os.getenv("LLMFOUNDRY_TOKEN") or os.getenv("OPENAI_API_KEY")
    endpoint = os.getenv("base_url") or os.getenv("OPENAI_BASE_URL")
    api_version = os.getenv("AZURE_API_VERSION") or os.getenv("OPENAI_API_VERSION")
    model = os.getenv("OPENAI_MODEL") or "gpt-4o-mini"
    if AzureOpenAI is None or not key or not endpoint or not api_version:
        return None, None, None, None
    try:
        client = AzureOpenAI(api_key=key, azure_endpoint=endpoint, api_version=api_version)
        return client, model, endpoint, api_version
    except Exception as e:
        global _last_error
        _last_error = f"client_init_error: {e}"
        return None, None, None, None


def route_check(text: str) -> Optional[Dict[str, Any]]:
    client, model, _, _ = _client_from_env()
    if client is None:
        return None
    tools_desc = [{"name": t["name"], "args": t["args"], "description": t["description"]} for t in TOOLS]
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT + " Tools:" + json.dumps(tools_desc)},
        {"role": "user", "content": text},
    ]
    try:
        resp = client.chat.completions.create(model=model, messages=messages, temperature=0)
        content = resp.choices[0].message.content if resp.choices else None
        if not content:
            return None
        # Try JSON parse directly; if fails, attempt to extract JSON object substring
        try:
            data = json.loads(content)
        except Exception:
            m = re.search(r"\{[\s\S]*\}", content)
            if not m:
                return None
            data = json.loads(m.group(0))
        if isinstance(data, dict) and "tool" in data and "args" in data:
            return data
        return None
    except Exception as e:
        global _last_error
        _last_error = f"llm_error: {e}"
        return None


def has_llm() -> bool:
    client, _, _, _ = _client_from_env()
    return client is not None

# Optional helper to introspect last router error (for debugging UI)
def last_router_error() -> Optional[str]:
    return _last_error
