# add_staff_sheet.py
import pandas as pd
from datetime import datetime

# This will automatically add any missing sheets including 'staff'
from excel_backend import ExcelBackend

print("Checking and adding missing sheets...")
db = ExcelBackend()

# Check if staff sheet exists
staff_df = db.get_sheet('staff')
if staff_df.empty:
    print("Adding default staff...")
    default_staff = pd.DataFrame([{
        'ID': 1,
        'Name': 'ADMIN',
        'Position': 'System Administrator',
        'Department': 'Management',
        'Phone': '',
        'Email': '',
        'Is_Supervisor': True,
        'Supervisor_Of_Location': None,
        'Is_Active': True,
        'Notes': 'Default administrator',
        'Created': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }])
    db.save_sheet('staff', default_staff)
    print("✅ Staff sheet created with ADMIN supervisor")
else:
    print(f"✅ Staff sheet already exists with {len(staff_df)} entries")

# List all sheets
import openpyxl
wb = openpyxl.load_workbook('inventory.xlsx')
print(f"\nAll sheets in inventory.xlsx: {wb.sheetnames}")