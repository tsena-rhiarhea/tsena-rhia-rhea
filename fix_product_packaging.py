# fix_product_packaging.py
from excel_backend import ExcelBackend

db = ExcelBackend()

# Add product_packaging sheet if missing
product_packaging_df = db.get_sheet('product_packaging')
if product_packaging_df.empty:
    import pandas as pd
    product_packaging_df = pd.DataFrame(columns=['ID', 'Product_ID', 'UOM_ID', 'Is_Active'])
    db.save_sheet('product_packaging', product_packaging_df)
    print("✅ Added product_packaging sheet")
else:
    print("product_packaging sheet already exists")