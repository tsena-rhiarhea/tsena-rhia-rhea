# add_sheets.py - Add all new sheets
from excel_backend import ExcelBackend
import pandas as pd

db = ExcelBackend()

# List of sheets to ensure exist
sheets = [
    'uom', 'categories', 'locations', 'colaborators', 'products',
    'product_packaging', 'packaging_breakdown', 'stock_movements',
    'build_requests', 'staff', 'users'
]

for sheet in sheets:
    df = db.get_sheet(sheet)
    print(f"{sheet}: {len(df)} rows")

print("\nAll sheets ready!")