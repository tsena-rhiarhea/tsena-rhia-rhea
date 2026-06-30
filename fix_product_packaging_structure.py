# fix_product_packaging_structure.py
from excel_backend import ExcelBackend
import pandas as pd

db = ExcelBackend()

# Update product_packaging sheet structure
pp_df = db.get_sheet('product_packaging')

# New columns
new_columns = ['ID', 'Product_ID', 'UOM_ID', 'Selling_Price', 'Purchase_Price', 'Is_Active']

# Check if old columns exist and migrate
if not pp_df.empty:
    # If old structure (without price columns), migrate
    if 'Selling_Price' not in pp_df.columns:
        pp_df['Selling_Price'] = 0.0
    if 'Purchase_Price' not in pp_df.columns:
        pp_df['Purchase_Price'] = 0.0
    
    # Keep only needed columns
    pp_df = pp_df[[c for c in new_columns if c in pp_df.columns]]
else:
    pp_df = pd.DataFrame(columns=new_columns)

db.save_sheet('product_packaging', pp_df)
print("✅ Updated product_packaging sheet structure")