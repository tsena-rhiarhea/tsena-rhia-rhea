# fix_products_final.py
from excel_backend import ExcelBackend
import pandas as pd

db = ExcelBackend()

# Fix products sheet
products_df = db.get_sheet('products')

if not products_df.empty:
    # Convert all numeric columns to float
    for col in ['Current_Stock', 'Min_Stock_Alert', 'Selling_Price', 'Purchase_Cost']:
        if col in products_df.columns:
            products_df[col] = pd.to_numeric(products_df[col], errors='coerce').fillna(0.0)
    
    db.save_sheet('products', products_df)
    print("✅ Fixed products sheet")

print("Done! Now run: streamlit run products_app.py")