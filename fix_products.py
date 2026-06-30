# fix_products.py
from excel_backend import ExcelBackend

db = ExcelBackend()

# Get products sheet
products_df = db.get_sheet('products')

# Add missing columns if they don't exist
if 'Category_ID' not in products_df.columns:
    products_df['Category_ID'] = None
    print("✅ Added Category_ID column")

if 'Base_UOM_ID' not in products_df.columns:
    products_df['Base_UOM_ID'] = None
    print("✅ Added Base_UOM_ID column")

# Save back
db.save_sheet('products', products_df)
print("✅ Products sheet updated!")