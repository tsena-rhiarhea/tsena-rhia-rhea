# fix_purchases.py
from excel_backend import ExcelBackend

db = ExcelBackend()

# This will create the sheets automatically
purchases_df = db.get_sheet('purchases')
purchase_items_df = db.get_sheet('purchase_items')

print("✅ Purchases sheets ready!")