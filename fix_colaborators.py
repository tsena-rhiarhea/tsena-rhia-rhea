# fix_colaborators.py
from excel_backend import ExcelBackend

print("Adding colaborators sheet...")

db = ExcelBackend()
colaborators_df = db.get_sheet('colaborators')

if colaborators_df.empty:
    import pandas as pd
    colaborators_df = pd.DataFrame(columns=[
        'ID', 'Name', 'Type', 'Phone', 'Location', 'Contact_Person',
        'Balance', 'Is_Active', 'Notes', 'Created'
    ])
    db.save_sheet('colaborators', colaborators_df)
    print("✅ Created colaborators sheet")

print(f"Colaborators sheet ready with {len(colaborators_df)} entries")