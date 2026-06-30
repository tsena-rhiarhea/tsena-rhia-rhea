# fix_excel.py - Add missing sheets to existing Excel file
import pandas as pd
from excel_backend import ExcelBackend

# This will automatically add any missing sheets
db = ExcelBackend()
print("Checking and fixing Excel file...")

# Test each sheet
sheets = ['uom', 'categories', 'products', 'customers', 'suppliers', 'users']
for sheet in sheets:
    df = db.get_sheet(sheet)
    print(f"✅ {sheet}: {len(df)} rows")

print("\nAll sheets are now available!")