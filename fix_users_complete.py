# fix_users_complete.py - Completely rebuild users sheet with correct types
from excel_backend import ExcelBackend
import pandas as pd
import hashlib
from datetime import datetime

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

db = ExcelBackend()

# Delete the old users sheet by creating a new empty one
print("Rebuilding users sheet...")

# Create new users dataframe with correct types
new_users = pd.DataFrame({
    'ID': [1, 2, 3, 4],
    'Username': ['ADMIN', 'MANAGER', 'SUPERVISOR', 'CASHIER'],
    'Password': [
        hash_password('admin123'),
        hash_password('manager123'),
        hash_password('super123'),
        hash_password('cash123')
    ],
    'Full_Name': ['System Administrator', 'Store Manager', 'Shift Supervisor', 'Cashier'],
    'Role': ['ADMIN', 'MANAGER', 'SUPERVISOR', 'CASHIER'],
    'Is_Active': [True, True, True, True],
    'Created': [
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ],
    'Last_Login': [None, None, None, None]
})

# Save as string/object type for Last_Login
new_users['Last_Login'] = new_users['Last_Login'].astype(object)

db.save_sheet('users', new_users)
print("✅ Users sheet rebuilt with correct data types!")
print("\nDefault logins:")
print("   ADMIN / admin123")
print("   MANAGER / manager123")
print("   SUPERVISOR / super123")
print("   CASHIER / cash123")