# fix_locations.py - Add locations sheet to existing Excel file
from excel_backend import ExcelBackend

print("Adding locations sheet to your Excel file...")

db = ExcelBackend()

# This will automatically create the locations sheet
locations_df = db.get_sheet('locations')

# Add default main location if empty
if locations_df.empty:
    import pandas as pd
    from datetime import datetime
    
    default_location = pd.DataFrame([{
        'ID': 1,
        'Name': 'TSENA RHIA-RHEA',
        'Parent_ID': None,
        'Level': 0,
        'Can_Hold_Stock': False,
        'Description': 'Main headquarters - Cannot hold stock directly',
        'Created': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }])
    db.save_sheet('locations', default_location)
    print("✅ Added default main location")

print(f"✅ Locations sheet has {len(locations_df)} rows")
print("\nAll sheets are now available!")