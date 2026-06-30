# fix_packaging_prices.py
from excel_backend import ExcelBackend

db = ExcelBackend()
prices_df = db.get_sheet('packaging_prices')

if prices_df.empty:
    import pandas as pd
    prices_df = pd.DataFrame(columns=['ID', 'Product_ID', 'UOM_ID', 'Selling_Price', 'Purchase_Price', 'Is_Active'])
    db.save_sheet('packaging_prices', prices_df)
    print("✅ Added packaging_prices sheet")
else:
    print("packaging_prices sheet already exists")