# fix_products_types.py
from excel_backend import ExcelBackend
import pandas as pd

db = ExcelBackend()

# Fix products sheet data types
products_df = db.get_sheet('products')

if not products_df.empty:
    # Convert numeric columns to float
    numeric_cols = ['Current_Stock', 'Min_Stock_Alert', 'Selling_Price', 'Purchase_Cost']
    for col in numeric_cols:
        if col in products_df.columns:
            products_df[col] = pd.to_numeric(products_df[col], errors='coerce').fillna(0)
    
    # Convert boolean column
    if 'Is_Active' in products_df.columns:
        products_df['Is_Active'] = products_df['Is_Active'].fillna(True)
    
    db.save_sheet('products', products_df)
    print("✅ Fixed products sheet data types")

print("All fixed!")