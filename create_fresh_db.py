# create_fresh_db.py - Create brand new database with all sheets
import pandas as pd
from datetime import datetime
import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Create all sheets
with pd.ExcelWriter('inventory.xlsx', engine='openpyxl') as writer:
    
    # UOM sheet
    pd.DataFrame(columns=['ID', 'Name', 'Type', 'Base_Unit', 'Factor', 'Created']).to_excel(
        writer, sheet_name='uom', index=False)
    
    # Categories sheet
    pd.DataFrame(columns=['ID', 'Name', 'Parent_ID', 'Level', 'Created']).to_excel(
        writer, sheet_name='categories', index=False)
    
    # Locations sheet
    pd.DataFrame(columns=['ID', 'Name', 'Parent_ID', 'Level', 'Can_Hold_Stock', 'Supervisor_ID', 'Description', 'Created']).to_excel(
        writer, sheet_name='locations', index=False)
    
    # Colaborators sheet
    pd.DataFrame(columns=['ID', 'Name', 'Type', 'Phone', 'Location', 'Contact_Person', 'Balance', 'Is_Active', 'Notes', 'Created']).to_excel(
        writer, sheet_name='colaborators', index=False)
    
    # Products sheet
    pd.DataFrame(columns=['ID', 'Name', 'Category_ID', 'Base_UOM_ID', 'Location_ID', 'Primary_Supplier_ID', 'Current_Stock', 'Min_Stock_Alert', 'Selling_Price', 'Purchase_Cost', 'Color', 'Is_Active', 'Notes', 'Created']).to_excel(
        writer, sheet_name='products', index=False)
    
    # Product Packaging sheet
    pd.DataFrame(columns=['ID', 'Product_ID', 'UOM_ID', 'Is_Active']).to_excel(
        writer, sheet_name='product_packaging', index=False)
    
    # Packaging Breakdown sheet
    pd.DataFrame(columns=['ID', 'Product_ID', 'Location_ID', 'UOM_ID', 'Full_Units', 'Partial_Units', 'Loose_Pieces']).to_excel(
        writer, sheet_name='packaging_breakdown', index=False)
    
    # Stock Movements sheet
    pd.DataFrame(columns=['ID', 'Date', 'Type', 'Product_ID', 'From_Location', 'To_Location', 'Quantity', 'UOM_ID', 'Reference', 'User', 'Notes']).to_excel(
        writer, sheet_name='stock_movements', index=False)
    
    # Build Requests sheet
    pd.DataFrame(columns=['ID', 'Request_Date', 'Requested_By', 'Product_ID', 'Target_Packaging_UOM_ID', 'Quantity', 'Status', 'Approved_By', 'Approved_Date', 'Pulling_Plan', 'Notes']).to_excel(
        writer, sheet_name='build_requests', index=False)
    
    # Staff sheet
    pd.DataFrame(columns=['ID', 'Name', 'Position', 'Department', 'Phone', 'Email', 'Is_Supervisor', 'Supervisor_Of_Location', 'Is_Active', 'Notes', 'Created']).to_excel(
        writer, sheet_name='staff', index=False)
    
    # Users sheet (without Last_Login to avoid type errors)
    pd.DataFrame({
        'ID': [1, 2, 3, 4],
        'Username': ['ADMIN', 'MANAGER', 'SUPERVISOR', 'CASHIER'],
        'Password': [
            hash_password('admin123'),
            hash_password('manager123'),
            hash_password('super123'),
            hash_password('cash123')
        ],
        'Full_Name': ['System Administrator', 'Store Manager', 'Shift Supervisor', 'Cashier'],
        'Role': ['ADMIN', 'MANAGER', 'SUPERVISOR', 'CASHIER'],
        'Is_Active': [True, True, True, True],
        'Created': [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ]
    }).to_excel(writer, sheet_name='users', index=False)

print("=" * 50)
print("✅ Fresh database created: inventory.xlsx")
print("=" * 50)
print("\nDefault users created:")
print("   ADMIN     / admin123")
print("   MANAGER   / manager123")
print("   SUPERVISOR / super123")
print("   CASHIER   / cash123")
print("\nAll sheets created successfully!")