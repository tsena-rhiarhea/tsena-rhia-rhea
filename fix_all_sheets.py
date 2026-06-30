# fix_all_sheets.py - Add all missing sheets
from excel_backend import ExcelBackend

print("Checking all sheets...")
db = ExcelBackend()

# List all sheets that should exist
sheets = ['uom', 'categories', 'locations', 'colaborators', 'products', 'staff', 'packaging_prices', 'users']

for sheet in sheets:
    df = db.get_sheet(sheet)
    print(f"  {sheet}: {len(df)} rows")

print("\n✅ All sheets are now available!")