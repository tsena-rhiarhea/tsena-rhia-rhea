# simple_create.py - Create fresh database
import openpyxl
from openpyxl import Workbook
from datetime import datetime
import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Create new workbook
wb = Workbook()

# Remove default sheet
wb.remove(wb.active)

# Create all sheets
sheets = ['uom', 'categories', 'locations', 'colaborators', 'products', 
          'product_packaging', 'packaging_breakdown', 'stock_movements', 
          'build_requests', 'staff', 'users']

for sheet_name in sheets:
    wb.create_sheet(sheet_name)

# Add headers to each sheet
# UOM
ws = wb['uom']
ws.append(['ID', 'Name', 'Type', 'Base_Unit', 'Factor', 'Created'])

# Categories
ws = wb['categories']
ws.append(['ID', 'Name', 'Parent_ID', 'Level', 'Created'])

# Locations
ws = wb['locations']
ws.append(['ID', 'Name', 'Parent_ID', 'Level', 'Can_Hold_Stock', 'Supervisor_ID', 'Description', 'Created'])

# Colaborators
ws = wb['colaborators']
ws.append(['ID', 'Name', 'Type', 'Phone', 'Location', 'Contact_Person', 'Balance', 'Is_Active', 'Notes', 'Created'])

# Products
ws = wb['products']
ws.append(['ID', 'Name', 'Category_ID', 'Base_UOM_ID', 'Location_ID', 'Primary_Supplier_ID', 'Current_Stock', 'Min_Stock_Alert', 'Selling_Price', 'Purchase_Cost', 'Color', 'Is_Active', 'Notes', 'Created'])

# Product Packaging
ws = wb['product_packaging']
ws.append(['ID', 'Product_ID', 'UOM_ID', 'Is_Active'])

# Packaging Breakdown
ws = wb['packaging_breakdown']
ws.append(['ID', 'Product_ID', 'Location_ID', 'UOM_ID', 'Full_Units', 'Partial_Units', 'Loose_Pieces'])

# Stock Movements
ws = wb['stock_movements']
ws.append(['ID', 'Date', 'Type', 'Product_ID', 'From_Location', 'To_Location', 'Quantity', 'UOM_ID', 'Reference', 'User', 'Notes'])

# Build Requests
ws = wb['build_requests']
ws.append(['ID', 'Request_Date', 'Requested_By', 'Product_ID', 'Target_Packaging_UOM_ID', 'Quantity', 'Status', 'Approved_By', 'Approved_Date', 'Pulling_Plan', 'Notes'])

# Staff
ws = wb['staff']
ws.append(['ID', 'Name', 'Position', 'Department', 'Phone', 'Email', 'Is_Supervisor', 'Supervisor_Of_Location', 'Is_Active', 'Notes', 'Created'])

# Users
ws = wb['users']
ws.append(['ID', 'Username', 'Password', 'Full_Name', 'Role', 'Is_Active', 'Created'])
ws.append([1, 'ADMIN', hash_password('admin123'), 'System Administrator', 'ADMIN', True, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
ws.append([2, 'MANAGER', hash_password('manager123'), 'Store Manager', 'MANAGER', True, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
ws.append([3, 'SUPERVISOR', hash_password('super123'), 'Shift Supervisor', 'SUPERVISOR', True, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
ws.append([4, 'CASHIER', hash_password('cash123'), 'Cashier', 'CASHIER', True, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])

# Save the workbook
wb.save('inventory.xlsx')
print("=" * 50)
print("✅ Fresh database created: inventory.xlsx")
print("=" * 50)
print("\nDefault users:")
print("   ADMIN     / admin123")
print("   MANAGER   / manager123")
print("   SUPERVISOR / super123")
print("   CASHIER   / cash123")
print("\nAll 11 sheets created successfully!")