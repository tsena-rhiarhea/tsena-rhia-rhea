# fix_purchases_sheets.py
from excel_backend import ExcelBackend

db = ExcelBackend()

# This will create the sheets automatically
purchases_df = db.get_sheet('purchases')
purchase_items_df = db.get_sheet('purchase_items')

print("✅ Purchases sheets ready!")
print(f"   Purchases: {len(purchases_df)} records")
print(f"   Purchase Items: {len(purchase_items_df)} records")