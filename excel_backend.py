# excel_backend.py - Complete version with all sheets
import pandas as pd
import os
import shutil
from datetime import datetime

class ExcelBackend:
    def __init__(self, filename="inventory.xlsx"):
        self.filename = filename
        self.backup_folder = "backups"
        
        if not os.path.exists(self.backup_folder):
            os.makedirs(self.backup_folder)
        
        if not os.path.exists(filename):
            self.create_new_workbook()
        else:
            self.ensure_all_sheets_exist()
    
    def create_backup(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}.xlsx"
        backup_path = os.path.join(self.backup_folder, backup_name)
        
        try:
            shutil.copy2(self.filename, backup_path)
            return backup_name
        except Exception as e:
            print(f"Backup failed: {e}")
            return None
    
    def create_new_workbook(self):
        with pd.ExcelWriter(self.filename, engine='openpyxl') as writer:
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
            pd.DataFrame(columns=[
                'ID', 'Name', 'Category_ID', 'Base_UOM_ID', 'Location_ID', 
                'Primary_Supplier_ID', 'Current_Stock', 'Min_Stock_Alert', 
                'Selling_Price', 'Purchase_Cost', 'Color', 'Is_Active', 'Notes', 'Created'
            ]).to_excel(writer, sheet_name='products', index=False)
            
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
            
            # Users sheet
            pd.DataFrame(columns=['ID', 'Username', 'Password', 'Full_Name', 'Role', 'Is_Active', 'Created']).to_excel(
                writer, sheet_name='users', index=False)
            
            # Purchases sheet
            pd.DataFrame(columns=[
                'ID', 'PO_Number', 'Date', 'Supplier_ID', 'Supplier_Name',
                'Total_Amount', 'Status', 'Notes', 'Created_By', 'Created_At'
            ]).to_excel(writer, sheet_name='purchases', index=False)
            
            # Purchase Items sheet
            pd.DataFrame(columns=[
                'ID', 'Purchase_ID', 'Product_ID', 'Product_Name', 'UOM_ID', 'UOM_Name',
                'Quantity', 'Unit_Cost', 'Total_Cost'
            ]).to_excel(writer, sheet_name='purchase_items', index=False)
    
    def ensure_all_sheets_exist(self):
        required_sheets = [
            'uom', 'categories', 'locations', 'colaborators', 'products', 
            'product_packaging', 'packaging_breakdown', 'stock_movements', 
            'build_requests', 'staff', 'users', 'purchases', 'purchase_items'
        ]
        
        try:
            existing_sheets = pd.ExcelFile(self.filename).sheet_names
            
            for sheet in required_sheets:
                if sheet not in existing_sheets:
                    with pd.ExcelWriter(self.filename, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                        if sheet == 'uom':
                            pd.DataFrame(columns=['ID', 'Name', 'Type', 'Base_Unit', 'Factor', 'Created']).to_excel(writer, sheet_name=sheet, index=False)
                        elif sheet == 'categories':
                            pd.DataFrame(columns=['ID', 'Name', 'Parent_ID', 'Level', 'Created']).to_excel(writer, sheet_name=sheet, index=False)
                        elif sheet == 'locations':
                            pd.DataFrame(columns=['ID', 'Name', 'Parent_ID', 'Level', 'Can_Hold_Stock', 'Supervisor_ID', 'Description', 'Created']).to_excel(writer, sheet_name=sheet, index=False)
                        elif sheet == 'colaborators':
                            pd.DataFrame(columns=['ID', 'Name', 'Type', 'Phone', 'Location', 'Contact_Person', 'Balance', 'Is_Active', 'Notes', 'Created']).to_excel(writer, sheet_name=sheet, index=False)
                        elif sheet == 'products':
                            pd.DataFrame(columns=[
                                'ID', 'Name', 'Category_ID', 'Base_UOM_ID', 'Location_ID', 
                                'Primary_Supplier_ID', 'Current_Stock', 'Min_Stock_Alert', 
                                'Selling_Price', 'Purchase_Cost', 'Color', 'Is_Active', 'Notes', 'Created'
                            ]).to_excel(writer, sheet_name=sheet, index=False)
                        elif sheet == 'product_packaging':
                            pd.DataFrame(columns=['ID', 'Product_ID', 'UOM_ID', 'Is_Active']).to_excel(writer, sheet_name=sheet, index=False)
                        elif sheet == 'packaging_breakdown':
                            pd.DataFrame(columns=['ID', 'Product_ID', 'Location_ID', 'UOM_ID', 'Full_Units', 'Partial_Units', 'Loose_Pieces']).to_excel(writer, sheet_name=sheet, index=False)
                        elif sheet == 'stock_movements':
                            pd.DataFrame(columns=['ID', 'Date', 'Type', 'Product_ID', 'From_Location', 'To_Location', 'Quantity', 'UOM_ID', 'Reference', 'User', 'Notes']).to_excel(writer, sheet_name=sheet, index=False)
                        elif sheet == 'build_requests':
                            pd.DataFrame(columns=['ID', 'Request_Date', 'Requested_By', 'Product_ID', 'Target_Packaging_UOM_ID', 'Quantity', 'Status', 'Approved_By', 'Approved_Date', 'Pulling_Plan', 'Notes']).to_excel(writer, sheet_name=sheet, index=False)
                        elif sheet == 'staff':
                            pd.DataFrame(columns=['ID', 'Name', 'Position', 'Department', 'Phone', 'Email', 'Is_Supervisor', 'Supervisor_Of_Location', 'Is_Active', 'Notes', 'Created']).to_excel(writer, sheet_name=sheet, index=False)
                        elif sheet == 'users':
                            pd.DataFrame(columns=['ID', 'Username', 'Password', 'Full_Name', 'Role', 'Is_Active', 'Created']).to_excel(writer, sheet_name=sheet, index=False)
                        elif sheet == 'purchases':
                            pd.DataFrame(columns=[
                                'ID', 'PO_Number', 'Date', 'Supplier_ID', 'Supplier_Name',
                                'Total_Amount', 'Status', 'Notes', 'Created_By', 'Created_At'
                            ]).to_excel(writer, sheet_name=sheet, index=False)
                        elif sheet == 'purchase_items':
                            pd.DataFrame(columns=[
                                'ID', 'Purchase_ID', 'Product_ID', 'Product_Name', 'UOM_ID', 'UOM_Name',
                                'Quantity', 'Unit_Cost', 'Total_Cost'
                            ]).to_excel(writer, sheet_name=sheet, index=False)
                    print(f"Added missing sheet: {sheet}")
        
        except Exception as e:
            print(f"Error ensuring sheets: {e}")
            self.create_new_workbook()
    
    def get_sheet(self, sheet_name):
        try:
            return pd.read_excel(self.filename, sheet_name=sheet_name)
        except ValueError:
            self.ensure_all_sheets_exist()
            return pd.read_excel(self.filename, sheet_name=sheet_name)
        except Exception as e:
            print(f"Error reading sheet {sheet_name}: {e}")
            return pd.DataFrame()
    
    def save_sheet(self, sheet_name, dataframe):
        try:
            excel_file = pd.ExcelFile(self.filename)
            sheets = {}
            for sheet in excel_file.sheet_names:
                sheets[sheet] = pd.read_excel(self.filename, sheet_name=sheet)
            
            sheets[sheet_name] = dataframe
            
            with pd.ExcelWriter(self.filename, engine='openpyxl') as writer:
                for sheet_name, df in sheets.items():
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
        except Exception as e:
            print(f"Error saving sheet {sheet_name}: {e}")
            if not os.path.exists(self.filename):
                self.create_new_workbook()
            else:
                try:
                    with pd.ExcelWriter(self.filename, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                        dataframe.to_excel(writer, sheet_name=sheet_name, index=False)
                except:
                    self.create_new_workbook()
                    with pd.ExcelWriter(self.filename, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                        dataframe.to_excel(writer, sheet_name=sheet_name, index=False)
    
    def get_next_id(self, sheet_name):
        df = self.get_sheet(sheet_name)
        if df.empty:
            return 1
        if 'ID' not in df.columns:
            return 1
        return df['ID'].max() + 1 if not df.empty else 1