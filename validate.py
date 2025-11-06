import argparse
import pandas as pd
from src.validator.sop_loader import load_sop
from src.validator.runner import run_check


def main():
    ap = argparse.ArgumentParser(description="SOP Checklist Validator")
    ap.add_argument("--sop", required=True, help="Path to SOP checklist (xlsx/csv) with column 'checks'")
    ap.add_argument("--input", required=True, help="Path to stock Excel/CSV")
    ap.add_argument("--meta", help="Path to master Excel/CSV (optional)")
    ap.add_argument("--sheet", help="Sheet name for stock file (optional)")
    ap.add_argument("--meta-sheet", help="Sheet name for master file (optional)")
    ap.add_argument("--out", default="results.xlsx", help="Output results file (xlsx/csv)")

    args = ap.parse_args()

    sop_df = load_sop(args.sop)

    # Load stock
    if args.input.lower().endswith((".xlsx", ".xls")):
        stock_df = pd.read_excel(args.input, sheet_name=args.sheet) if args.sheet else pd.read_excel(args.input)
    else:
        stock_df = pd.read_csv(args.input)

    # Load master (optional)
    master_df = None
    if args.meta:
        if args.meta.lower().endswith((".xlsx", ".xls")):
            master_df = pd.read_excel(args.meta, sheet_name=args.meta_sheet) if args.meta_sheet else pd.read_excel(args.meta)
        else:
            master_df = pd.read_csv(args.meta)

    results = []
    for _, row in sop_df.iterrows():
        check_text = str(row["checks"])  # required column
        res = run_check(check_text, stock_df, master_df)
        # propagate optional metadata like id/severity
        out = {
            "check": res["check"],
            "tool": res["tool"],
            "passed": res["passed"],
            "details": res["details"],
        }
        for extra in ("id", "severity"):
            if extra in sop_df.columns:
                out[extra] = row.get(extra)
        results.append(out)

    results_df = pd.DataFrame(results)

    if args.out.lower().endswith((".xlsx", ".xls")):
        with pd.ExcelWriter(args.out, engine="openpyxl") as xw:
            results_df.to_excel(xw, index=False, sheet_name="results")
    else:
        results_df.to_csv(args.out, index=False)

    # Basic console report
    total = len(results_df)
    passed = int(results_df["passed"].sum())
    print(f"Checks passed: {passed}/{total}")
    # show first few failed details
    failed = results_df[~results_df["passed"].astype(bool)]
    if not failed.empty:
        print("Failed checks (top 5):")
        for _, r in failed.head(5).iterrows():
            print("-", r["check"], "->", r["details"])


if __name__ == "__main__":
    main()
