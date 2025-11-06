SOP Checklist Validator

What It Does
- Upload a SOP checklist and one or more input files (Stock, optional Master, optional GR) in the Streamlit app.
- For each SOP line in column `checks`, the router asks your Azure OpenAI model to select a single validation tool + arguments.
- The selected tool runs against the appropriate dataset(s) and returns pass/fail with details; all results are shown in the UI and exported to `results.xlsx`.

Quick Start
- Create and activate venv:
  - `python -m venv .venv`
  - Windows PowerShell: `.\.venv\Scripts\Activate.ps1`
- Install deps: `python -m pip install -r requirements.txt`
- Configure .env (no quotes; real values):
  - `base_url=https://YOUR_RESOURCE_NAME.openai.azure.com`
  - `LLMFOUNDRY_TOKEN=YOUR_AZURE_OPENAI_KEY`
  - `AZURE_API_VERSION=2025-01-01-preview`
  - `OPENAI_MODEL=gpt-4o-mini`  (Azure deployment name)
- Launch app: `python -m streamlit run streamlit_app.py`

Streamlit Usage
- Upload files in the sidebar:
  - SOP checklist (csv/xlsx with column `checks`)
  - Stock file (csv/xlsx; default sheet `Stock`)
  - Optional Master file (default sheet `Master`)
  - Optional Goods Receipt file (GR, default sheet `GR`)
- Click `Run Validation`.
- Review the table; click `Download results.xlsx` to save the output.

End-to-End Flow
1) UI reads SOP and data into pandas DataFrames.
2) For each SOP `checks` line, the LangGraph workflow (src/graph/app.py) runs two nodes:
   - `route`: sends the free-text check to the LLM router (src/validator/router.py) and expects strict JSON `{"tool": ..., "args": {...}}`.
   - `act`: executes that tool via the runner (src/validator/runner.py) on the right DataFrame(s).
3) Each tool returns `{passed: bool, info: {...}}`.
4) The app aggregates all results into a table and writes `results.xlsx`.

LLM Router (Azure OpenAI)
- File: `src/validator/router.py`
- Client: `AzureOpenAI(api_key=LLMFOUNDRY_TOKEN, azure_endpoint=base_url, api_version=AZURE_API_VERSION)`.
- System prompt (summary): “Choose exactly one tool and args. Return strict JSON only. Datasets: stock/master/gr. Use GR for MB51/receipt checks; for manufacturing date vs documentation, join stock to master on keys ['Material Code','Batch'] and compare 'Date of Manufacturing'.”
- Tools exposed to LLM:
  - `column_exists({column})`
  - `duplicates_check({columns, allowed, dataset})` where `dataset` ? {`stock`,`gr`}
  - `value_in_master({column, master_column})`
  - `row_condition({expr})`
  - `date_not_future({column})`
  - `value_range({column, min_val, max_val, inclusive})`
  - `regex_match({column, pattern, mode})`
  - `match_master_on_keys({keys, column})`
- If the LLM returns non-JSON, the router extracts the first `{...}` object from the reply and parses it.
- `has_llm()` in the UI indicates if the client was initialized.

Runner
- File: `src/validator/runner.py`
- Chooses dataset based on intent:
  - `duplicates_check` ? uses GR DataFrame when `args.dataset == "gr"`; otherwise Stock.
  - `match_master_on_keys` ? joins Stock to Master on `args.keys` and compares the specified column (date-safe).
- Returns result rows `{check, tool, passed, details}`.

Tools
- File: `src/validator/tools.py`
- Key tools implemented:
  - `duplicates_check(df, columns, allowed)` ? counts duplicate rows on `columns`; returns examples.
  - `match_master_on_keys(df, master, keys, column)` ? left-join on `keys`, parse dates, report mismatches.
  - Plus generics: `column_exists`, `value_in_master`, `row_condition`, `date_not_future`, `value_range`, `regex_match`.
- Date parsing uses pandas/dateutil; numeric parsing handles thousands separators like `45,000`.

Detailed Example: Duplicate Receipt in MB51 (GR)
- SOP row (checks): `Ensure no duplicate receipt exists in MB51`.
- Route node builds messages:
  - system: describes tools + datasets and asks for strict JSON.
  - user: `Ensure no duplicate receipt exists in MB51`.
- Expected LLM output JSON:
  ```json
  {"tool": "duplicates_check", "args": {"columns": ["Material Document"], "dataset": "gr", "allowed": false}}
  ```
- Act node passes GR DataFrame to `duplicates_check` with `columns=['Material Document']`.
- Tool computes duplicates and returns e.g.:
  ```json
  {"passed": false, "info": {"duplicate_count": 2, "examples": [{"Material Document": 5000000011, "Posting Date": "11/04/2025", "Plant": "HYD1"}, {"Material Document": 5000000011, "Posting Date": "11/04/2025", "Plant": "HYD1"}]}}
  ```
- Result row in table:
  - `check`: Ensure no duplicate receipt exists in MB51
  - `tool`: duplicates_check
  - `passed`: false
  - `details`: duplicate_count=2, examples=[...]

Detailed Example: Confirm Manufacturing Date Against Documentation
- SOP row (checks): `Confirm manufacturing date against documentation`.
- Expected LLM output JSON:
  ```json
  {"tool": "match_master_on_keys", "args": {"keys": ["Material Code", "Batch"], "column": "Date of Manufacturing"}}
  ```
- Act node runs `match_master_on_keys(stock_df, master_df, keys, column)`.
- Tool joins Stock?Master on `Material Code`+`Batch`, parses dates, and flags mismatches or missing master records:
  - If all match: `passed=true, info={"mismatch_count": 0}`.
  - If discrepancies: `passed=false, info={"mismatch_count": N, "examples": [<up to 5 mismatched rows>]}`.

Output
- UI table shows every SOP check with the LLM-selected tool and pass/fail.
- Download `results.xlsx` (sheet `results`) with the same content.

Troubleshooting
- App caption says `LLM routing: Inactive`:
  - Fix `.env`: ensure non-empty values (no quotes) for `base_url`, `LLMFOUNDRY_TOKEN`, `AZURE_API_VERSION`, `OPENAI_MODEL`.
  - Restart the app.
- Table shows `tool=None` and `Unable to route check`:
  - Run `from src.validator.router import has_llm, route_check, last_router_error` in Python to inspect `has_llm()` and `last_router_error()`.
  - If `has_llm=False`, client init failed (endpoint/key/version). If `last_router_error` shows `llm_error`, share the string and adjust prompt/tool list or Azure settings.
- GR duplicates not detected:
  - Ensure GR file uses column `Material Document` (or adjust SOP wording to include the exact key you want checked).
- Manufacturing date mismatches not detected:
  - Ensure Stock and Master have aligned `Material Code` and `Batch` keys and the date column is `Date of Manufacturing`.
