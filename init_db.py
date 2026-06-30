# init_db.py - Run this once to initialize the database
from excel_backend import ExcelBackend
from auth import init_users

print("Initializing database...")
db = ExcelBackend()
init_users()
print("\nDatabase initialized successfully!")
print("\nDefault logins:")
print("  ADMIN / admin123")
print("  MANAGER / manager123")
print("  SUPERVISOR / super123")
print("  CASHIER / cash123")