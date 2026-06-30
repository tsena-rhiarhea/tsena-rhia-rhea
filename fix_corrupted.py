# fix_corrupted.py - Fix or recreate corrupted Excel file
import os
import pandas as pd
from datetime import datetime

EXCEL_FILE = "inventory.xlsx"

# Backup the corrupted file if it exists
if os.path.exists(EXCEL_FILE):
    backup_name = f"corrupted_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    os.rename(EXCEL_FILE, backup_name)
    print(f"✅ Corrupted file backed up as: {backup_name}")

# Create a fresh Excel file
print("Creating fresh inventory.xlsx...")

from excel_backend import ExcelBackend

# This will create a brand new file
db = ExcelBackend()

print("✅ Fresh inventory.xlsx created!")

# Verify all sheets were created
sheets_to_check = ['uom', 'categories', 'locations', 'colaborators', 'products', 'users']
for sheet in sheets_to_check:
    df = db.get_sheet(sheet)
    print(f"  ✓ {sheet}: {len(df)} rows")

print("\n✅ Your Excel file is now fixed and ready to use!")