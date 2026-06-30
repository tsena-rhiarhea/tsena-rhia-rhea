# fix_users_remove_column.py
from excel_backend import ExcelBackend
import pandas as pd

db = ExcelBackend()

users_df = db.get_sheet('users')

if not users_df.empty:
    # Remove Last_Login column if it exists
    if 'Last_Login' in users_df.columns:
        users_df = users_df.drop(columns=['Last_Login'])
        print("✅ Removed Last_Login column")
    
    db.save_sheet('users', users_df)
    print("✅ Users sheet fixed!")

# Also update excel_backend.py to remove Last_Login from new workbooks
print("\nDone!")