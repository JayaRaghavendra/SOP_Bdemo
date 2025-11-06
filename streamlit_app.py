import io
import os
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from src.graph.app import build_graph
from src.validator.router import has_llm

st.set_page_config(page_title="SOP Validator", layout="wide")
st.title("SOP Checklist Validator")

load_dotenv(override=True)

with st.sidebar:
    st.header("Upload Files")
    sop_file = st.file_uploader("SOP checklist (csv/xlsx)", type=["csv", "xlsx", "xls"])
    stock_file = st.file_uploader("Stock file (csv/xlsx)", type=["csv", "xlsx", "xls"])
    stock_sheet = st.text_input("Stock sheet name (xlsx)", value="Stock")
    master_file = st.file_uploader("Master file (optional, csv/xlsx)", type=["csv", "xlsx", "xls"])
    master_sheet = st.text_input("Master sheet name (xlsx)", value="Master")
    gr_file = st.file_uploader("GR file (optional, csv/xlsx)", type=["csv", "xlsx", "xls"])
    gr_sheet = st.text_input("GR sheet name (xlsx)", value="GR")
    run_btn = st.button("Run Validation")

# Helpers to read uploaded files to DataFrames

def _read_df(upload, sheet_name=None):
    if upload is None:
        return None
    name = upload.name.lower()
    data = upload.read()
    bio = io.BytesIO(data)
    if name.endswith(".csv"):
        # Try utf-8 then fallback
        try:
            return pd.read_csv(io.BytesIO(data))
        except Exception:
            return pd.read_csv(io.BytesIO(data), encoding="latin1")
    else:
        return pd.read_excel(bio, sheet_name=sheet_name) if sheet_name else pd.read_excel(bio)

results_df = None

if run_btn:
    # Load SOP
    sop_df = _read_df(sop_file)
    if sop_df is None or "checks" not in sop_df.columns:
        st.error("SOP file must have a column named 'checks'.")
    else:
        # Load stock/master/gr
        stock_df = _read_df(stock_file, sheet_name=stock_sheet)
        if stock_df is None:
            st.error("Please upload a stock file.")
        else:
            master_df = _read_df(master_file, sheet_name=master_sheet)
            gr_df = _read_df(gr_file, sheet_name=gr_sheet)
            # Build graph and run each SOP check
            wf = build_graph(stock_df, master_df, gr_df)
            results = []
            for _, row in sop_df.iterrows():
                check_text = str(row["checks"]) 
                out = wf.invoke({"check": check_text})
                res = out.get("result", {})
                # propagate id/severity if present
                for extra in ("id", "severity"):
                    if extra in sop_df.columns:
                        res[extra] = row.get(extra)
                results.append(res)

            results_df = pd.DataFrame(results)
            st.subheader("Results")
            st.dataframe(results_df, use_container_width=True)

            # Offer a downloadable Excel
            with io.BytesIO() as bio:
                with pd.ExcelWriter(bio, engine="openpyxl") as xw:
                    results_df.to_excel(xw, index=False, sheet_name="results")
                bio.seek(0)
                st.download_button(
                    label="Download results.xlsx",
                    data=bio.read(),
                    file_name="results.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

status = "LLM routing: Active" if has_llm() else "LLM routing: Inactive (set .env: OPENAI_API_KEY/base_url/AZURE_API_VERSION/OPENAI_MODEL)"
st.caption(status)
