import pandas as pd
from datetime import date

# Stock data as per screenshot
stock_rows = [
    {"Material Code": "MAT-001", "Material Description": "API Raw Material", "Plant": "HYD1", "Storage Location": "RM01", "Batch": "BATCH-2025A", "Date of Manufacturing": "10/15/2025", "Current Stock": "1,200", "UoM": "KG", "Valuation Type": "Standard", "Last Update": "11/4/2025"},
    {"Material Code": "MAT-002", "Material Description": "Packaging Cartons", "Plant": "HYD1", "Storage Location": "PKG01", "Batch": "BATCH-2025B", "Date of Manufacturing": "10/20/2025", "Current Stock": "8,500", "UoM": "PCS", "Valuation Type": "Standard", "Last Update": "11/4/2025"},
    {"Material Code": "MAT-003", "Material Description": "Glass Vials", "Plant": "HYD2", "Storage Location": "PKG02", "Batch": "BATCH-2025C", "Date of Manufacturing": "10/18/2025", "Current Stock": "45,000", "UoM": "PCS", "Valuation Type": "Standard", "Last Update": "11/4/2025"},
    {"Material Code": "MAT-004", "Material Description": "Labels", "Plant": "HYD1", "Storage Location": "PKG03", "Batch": "BATCH-2025D", "Date of Manufacturing": "10/22/2025", "Current Stock": "12,000", "UoM": "PCS", "Valuation Type": "Standard", "Last Update": "11/4/2025"},
    {"Material Code": "MAT-005", "Material Description": "Solvent Ethanol", "Plant": "HYD2", "Storage Location": "RM02", "Batch": "BATCH-2025E", "Date of Manufacturing": "10/10/2025", "Current Stock": "3,500", "UoM": "L", "Valuation Type": "Standard", "Last Update": "11/4/2025"},
    {"Material Code": "MAT-006", "Material Description": "Plastic Caps", "Plant": "HYD1", "Storage Location": "PKG04", "Batch": "BATCH-2025F", "Date of Manufacturing": "10/25/2025", "Current Stock": "28,000", "UoM": "PCS", "Valuation Type": "Standard", "Last Update": "11/4/2025"},
    {"Material Code": "MAT-007", "Material Description": "Aluminum Foil", "Plant": "HYD2", "Storage Location": "PKG05", "Batch": "BATCH-2025G", "Date of Manufacturing": "10/12/2025", "Current Stock": "1,200", "UoM": "KG", "Valuation Type": "Standard", "Last Update": "11/4/2025"},
    {"Material Code": "MAT-008", "Material Description": "Secondary Packaging", "Plant": "HYD1", "Storage Location": "PKG06", "Batch": "BATCH-2025H", "Date of Manufacturing": "10/28/2025", "Current Stock": "6,000", "UoM": "PCS", "Valuation Type": "Standard", "Last Update": "11/4/2025"},
    {"Material Code": "MAT-009", "Material Description": "API Intermediate", "Plant": "HYD2", "Storage Location": "RM03", "Batch": "BATCH-2025I", "Date of Manufacturing": "10/14/2025", "Current Stock": "750", "UoM": "KG", "Valuation Type": "Standard", "Last Update": "11/4/2025"},
    {"Material Code": "MAT-010", "Material Description": "Rubber Stoppers", "Plant": "HYD1", "Storage Location": "PKG07", "Batch": "BATCH-2025J", "Date of Manufacturing": "10/30/2025", "Current Stock": "20,000", "UoM": "PCS", "Valuation Type": "Standard", "Last Update": "11/4/2025"},
]
stock_df = pd.DataFrame(stock_rows)

# Master data mirrors the valid codes/batches
master_df = stock_df[["Material Code", "Material Description", "Plant", "Storage Location", "Batch", "Date of Manufacturing"]].copy()

# SOP checks
sop_checks = pd.DataFrame({
    "id": [1,2,3,4,5,6,7,8,9,10],
    "severity": ["H","M","M","M","M","H","H","H","M","M"],
    "checks": [
        "Column 'Material Code' must exist",
        "Column 'Material Description' must exist",
        "Column 'Plant' must exist",
        "Column 'Storage Location' must exist",
        "Column 'Batch' must exist",
        "Date of Manufacturing not in future",
        "Column 'Current Stock' must be > 0",
        "Column 'Material Code' must be in master",
        "Column 'Batch' must be in master",
        "No duplicates in 'Material Code' and 'Batch'",
    ]
})

with pd.ExcelWriter('stock.xlsx', engine='openpyxl') as xw:
    stock_df.to_excel(xw, index=False, sheet_name='Stock')

with pd.ExcelWriter('master.xlsx', engine='openpyxl') as xw:
    master_df.to_excel(xw, index=False, sheet_name='Master')

with pd.ExcelWriter('sop.xlsx', engine='openpyxl') as xw:
    sop_checks.to_excel(xw, index=False, sheet_name='SOP')

print('Generated stock.xlsx, master.xlsx, sop.xlsx')
