# recover_data.py - Try to recover data from corrupted file
import pandas as pd
import os
from datetime import datetime

corrupted_file = "inventory.xlsx"
recovered_data = {}

if os.path.exists(corrupted_file):
    print("Attempting to recover data from corrupted file...")
    
    # Try to read each sheet individually using different engines
    sheets = ['uom', 'categories', 'locations', 'colaborators', 'products', 'users']
    
    for sheet in sheets:
        try:
            # Try with openpyxl first
            df = pd.read_excel(corrupted_file, sheet_name=sheet, engine='openpyxl')
            if not df.empty:
                recovered_data[sheet] = df
                print(f"✅ Recovered {sheet}: {len(df)} rows")
        except:
            try:
                # Try with calamine engine (if available)
                df = pd.read_excel(corrupted_file, sheet_name=sheet, engine='calamine')
                if not df.empty:
                    recovered_data[sheet] = df
                    print(f"✅ Recovered {sheet}: {len(df)} rows (using calamine)")
            except:
                try:
                    # Try reading without specifying sheet
                    df = pd.read_excel(corrupted_file, engine='openpyxl')
                    print(f"⚠️ Could not read sheet {sheet} separately")
                except Exception as e:
                    print(f"❌ Could not recover {sheet}: {e}")
    
    # Create new file with recovered data
    if recovered_data:
        print("\nCreating new file with recovered data...")
        from excel_backend import ExcelBackend
        
        db = ExcelBackend()
        
        for sheet_name, df in recovered_data.items():
            db.save_sheet(sheet_name, df)
            print(f"  ✓ Restored {sheet_name}")
        
        print("\n✅ Data recovery complete!")
    else:
        print("\n❌ No data could be recovered. Starting fresh.")
        from excel_backend import ExcelBackend
        db = ExcelBackend()
        print("✅ Fresh file created.")
else:
    print("No corrupted file found. Creating fresh file...")
    from excel_backend import ExcelBackend
    db = ExcelBackend()
    print("✅ Fresh file created.")