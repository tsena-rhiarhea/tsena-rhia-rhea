# fix_staff.py - Add staff sheet directly
import pandas as pd
from datetime import datetime
import os

EXCEL_FILE = "inventory.xlsx"

# Check if file exists
if not os.path.exists(EXCEL_FILE):
    print("Excel file not found. Please run the app first to create it.")
    exit()

# Read all existing sheets
try:
    existing_sheets = pd.ExcelFile(EXCEL_FILE).sheet_names
    print(f"Existing sheets: {existing_sheets}")
except Exception as e:
    print(f"Error reading file: {e}")
    exit()

# Create staff dataframe
staff_df = pd.DataFrame(columns=[
    'ID', 'Name', 'Position', 'Department', 'Phone', 'Email', 
    'Is_Supervisor', 'Supervisor_Of_Location', 'Is_Active', 'Notes', 'Created'
])

# Add default admin
default_admin = pd.DataFrame([{
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

staff_df = pd.concat([staff_df, default_admin], ignore_index=True)

# Write to Excel
with pd.ExcelWriter(EXCEL_FILE, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
    staff_df.to_excel(writer, sheet_name='staff', index=False)

print("✅ Added 'staff' sheet with ADMIN supervisor")
print(f"   Staff count: {len(staff_df)}")