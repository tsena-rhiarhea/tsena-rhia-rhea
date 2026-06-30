# fix_purchase_items.py
from excel_backend import ExcelBackend

db = ExcelBackend()

items_df = db.get_sheet('purchase_items')

# Add new columns if they don't exist
if 'Ordered_Quantity' not in items_df.columns:
    # Rename existing 'Quantity' to 'Ordered_Quantity'
    if 'Quantity' in items_df.columns:
        items_df = items_df.rename(columns={'Quantity': 'Ordered_Quantity'})
    else:
        items_df['Ordered_Quantity'] = 0

if 'Received_Quantity' not in items_df.columns:
    items_df['Received_Quantity'] = 0

db.save_sheet('purchase_items', items_df)
print("✅ Updated purchase_items sheet")