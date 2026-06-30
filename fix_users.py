# fix_users.py - Fix the users sheet data types
from excel_backend import ExcelBackend
import pandas as pd

db = ExcelBackend()

users_df = db.get_sheet('users')

if not users_df.empty:
    # Convert Last_Login to string/object type
    if 'Last_Login' in users_df.columns:
        users_df['Last_Login'] = users_df['Last_Login'].astype(object)
    
    # Save back
    db.save_sheet('users', users_df)
    print("✅ Fixed users sheet - Last_Login column type corrected")
else:
    print("Users sheet is empty, will be created on next login")

print("Done!")