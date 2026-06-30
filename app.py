# app.py - Main Navigation with Purchases Module
import streamlit as st
from excel_backend import ExcelBackend
from auth import login, init_users, get_current_user
import pandas as pd
import numpy as np
import os
import sys
import traceback

# ========== ERROR HANDLING WRAPPER ==========
def safe_exec_module(module_path, module_name):
    """Safely execute a module with error handling"""
    try:
        # Create a new namespace for the module
        module_globals = {
            '__name__': module_name,
            '__file__': module_path,
            'st': st,
            'pd': pd,
            'np': np,
            'ExcelBackend': ExcelBackend,
            'get_current_user': get_current_user,
            'user': get_current_user(),
            'db': db
        }
        
        with open(module_path, 'r', encoding='utf-8') as f:
            code = f.read()
        
        # Execute the module code
        exec(code, module_globals)
        return True
        
    except Exception as e:
        st.error(f"❌ Error loading module: {module_name}")
        st.error(f"Error details: {str(e)}")
        
        # Show full traceback for debugging
        with st.expander("🔍 Full Error Details"):
            st.code(traceback.format_exc(), language="python")
            
            # Show the specific error line if possible
            st.markdown("### Error Analysis")
            st.write(f"**Error Type:** {type(e).__name__}")
            st.write(f"**Error Message:** {str(e)}")
            
            if "Invalid value '' for dtype 'float64'" in str(e):
                st.warning("""
                ⚠️ **Common Fix:** Empty strings ('') are being assigned to a float column.
                
                **Solutions:**
                1. Replace empty strings with NaN: `df.replace('', np.nan)`
                2. Use nullable float dtype: `df['column'].astype('Float64')`
                3. Clean data before assignment: Use `safe_float_conversion()`
                """)
            
            st.info("💡 Check the module's code for direct assignment of empty strings to numeric columns.")
        
        return False

# ========== DATA CLEANING UTILITIES ==========
def clean_float_value(value):
    """Clean a value for float assignment"""
    if value is None or value == '' or pd.isna(value):
        return np.nan
    try:
        return float(value)
    except (ValueError, TypeError):
        return np.nan

def clean_dataframe_for_export(df):
    """Clean DataFrame before saving to Excel"""
    df = df.copy()
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].replace('', 'Unknown')
            df[col] = df[col].fillna('Unknown')
        elif pd.api.types.is_float_dtype(df[col]):
            df[col] = df[col].fillna(np.nan)
    return df

def safe_read_excel(file_path, sheet_name):
    """Safely read Excel with cleaning"""
    try:
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        
        # Clean all columns
        for col in df.columns:
            # Convert empty strings to NaN for numeric columns
            if df[col].dtype == 'object':
                # Try to convert to numeric where possible
                try:
                    df[col] = pd.to_numeric(df[col], errors='ignore')
                except:
                    pass
            
            # Replace empty strings with NaN for float columns
            if pd.api.types.is_float_dtype(df[col]):
                df[col] = df[col].replace('', np.nan)
                df[col] = df[col].astype('Float64')  # Nullable float
            elif df[col].dtype == 'object':
                df[col] = df[col].replace('', 'Unknown')
                
        return df
    except Exception as e:
        st.error(f"Error reading {sheet_name}: {str(e)}")
        return pd.DataFrame()

# ========== INITIALIZATION ==========
init_users()

st.set_page_config(
    page_title="TSENA RHIA-RHEA",
    page_icon="📦",
    layout="wide"
)

# ========== LOGIN ==========
is_logged_in = login()

if not is_logged_in:
    st.title("📦 TSENA RHIA-RHEA")
    st.caption("Inventory & Directory System")
    st.markdown("---")
    st.info("👈 Please login using the sidebar to access the system")
    st.stop()

user = get_current_user()
st.title("📦 TSENA RHIA-RHEA")
st.caption(f"Inventory & Directory System - Welcome, {user['full_name']} ({user['role']})")

db = ExcelBackend()

# ========== SIDEBAR - BACKUP SECTION ==========
st.sidebar.markdown("---")
if user['role'] in ['MANAGER', 'ADMIN']:
    st.sidebar.subheader("💾 Database")
    
    if st.sidebar.button("Create Backup", use_container_width=True):
        with st.spinner("Creating backup..."):
            backup_name = db.create_backup()
            if backup_name:
                st.sidebar.success(f"✅ Backup saved: {backup_name}")
            else:
                st.sidebar.error("❌ Backup failed")
    
    backup_folder = "backups"
    if os.path.exists(backup_folder):
        backups = [f for f in os.listdir(backup_folder) if f.endswith('.xlsx')]
        if backups:
            backups.sort(reverse=True)
            st.sidebar.caption(f"Last backup: {backups[0][:20]}...")
        else:
            st.sidebar.caption("No backups yet")
    else:
        st.sidebar.caption("No backups folder")

st.sidebar.markdown("---")

# ========== NAVIGATION ==========
st.sidebar.subheader("📋 NAVIGATION")

if 'current_page' not in st.session_state:
    st.session_state.current_page = "Dashboard"

def navigate_to(page):
    st.session_state.current_page = page
    st.rerun()

if st.sidebar.button("📊 DASHBOARD", use_container_width=True):
    navigate_to("Dashboard")

st.sidebar.markdown("---")

# DIRECTORY section
st.sidebar.markdown("### 📁 DIRECTORY")
if st.sidebar.button("👥 INTERNAL", use_container_width=True):
    navigate_to("Internal")
if st.sidebar.button("🔗 CONNECTIONS", use_container_width=True):
    navigate_to("Connections")

st.sidebar.markdown("---")

# PRODUCTS & SERVICES section
st.sidebar.markdown("### 📦 PRODUCTS & SERVICES")
if st.sidebar.button("📦 Products", use_container_width=True):
    navigate_to("Products")
if st.sidebar.button("📁 Categories", use_container_width=True):
    navigate_to("Categories")
if st.sidebar.button("📏 UOM", use_container_width=True):
    navigate_to("UOM")
if st.sidebar.button("📍 Locations", use_container_width=True):
    navigate_to("Locations")
if st.sidebar.button("🔄 Stock Transfer", use_container_width=True):
    navigate_to("StockTransfer")
if st.sidebar.button("🏗️ Build Requests", use_container_width=True):
    navigate_to("BuildRequests")

st.sidebar.markdown("---")

# PURCHASES & SALES section
st.sidebar.markdown("### 💰 PURCHASES & SALES")
if st.sidebar.button("🛒 Purchases", use_container_width=True):
    navigate_to("Purchases")

st.sidebar.markdown("---")
st.sidebar.caption(f"Logged in as: {user['full_name']}")
st.sidebar.caption(f"Role: {user['role']}")

# ========== MAIN CONTENT AREA ==========

# Global try-catch for main content
try:
    if st.session_state.current_page == "Dashboard":
        st.markdown("""
        ## Welcome to TSENA RHIA-RHEA

        Select a module from the sidebar to get started.

        ### Available Modules:

        #### 📁 DIRECTORY
        - **👥 INTERNAL** - Manage users and staff (linked together)
        - **🔗 CONNECTIONS** - Manage suppliers, customers, and prospects

        #### 📦 PRODUCTS & SERVICES
        - **📦 Products** - Manage products with packaging and pricing
        - **📁 Categories** - Hierarchical product categories
        - **📏 UOM** - Units of Measure (base and packaging units)
        - **📍 Locations** - Storage locations with supervisor assignment
        - **🔄 Stock Transfer** - Transfer stock between locations
        - **🏗️ Build Requests** - Request packaging builds (Supervisor+)

        #### 💰 PURCHASES & SALES
        - **🛒 Purchases** - Record stock purchases from suppliers

        ### Planned Modules:
        - 📊 Global Dashboard
        - 💵 Sales (POS system)
        - 📈 Statistics and Reports
        """)
        
        st.markdown("---")
        st.subheader("📊 Current Data Status")
        
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
        # Safe data loading with error handling
        try:
            uom_data = db.get_sheet('uom')
            col1.metric("UOM", len(uom_data) if not uom_data.empty else 0)
        except:
            col1.metric("UOM", "⚠️ Error")
            
        try:
            cat_data = db.get_sheet('categories')
            col2.metric("Categories", len(cat_data) if not cat_data.empty else 0)
        except:
            col2.metric("Categories", "⚠️ Error")
            
        try:
            loc_data = db.get_sheet('locations')
            col3.metric("Locations", len(loc_data) if not loc_data.empty else 0)
        except:
            col3.metric("Locations", "⚠️ Error")
            
        try:
            colab_data = db.get_sheet('colaborators')
            col4.metric("Connections", len(colab_data) if not colab_data.empty else 0)
        except:
            col4.metric("Connections", "⚠️ Error")
            
        try:
            prod_data = db.get_sheet('products')
            col5.metric("Products", len(prod_data) if not prod_data.empty else 0)
        except:
            col5.metric("Products", "⚠️ Error")
            
        try:
            purch_data = db.get_sheet('purchases')
            col6.metric("Purchases", len(purch_data) if not purch_data.empty else 0)
        except:
            col6.metric("Purchases", "⚠️ Error")

    elif st.session_state.current_page == "Internal":
        module_success = safe_exec_module('modules/internal.py', 'internal_module')
        if not module_success:
            st.error("Failed to load Internal module. Please check the module code.")

    elif st.session_state.current_page == "Connections":
        module_success = safe_exec_module('modules/connections.py', 'connections_module')
        if not module_success:
            st.error("Failed to load Connections module. Please check the module code.")

    elif st.session_state.current_page == "Products":
        module_success = safe_exec_module('modules/products.py', 'products_module')
        if not module_success:
            st.error("Failed to load Products module. Please check the module code.")

    elif st.session_state.current_page == "Categories":
        module_success = safe_exec_module('modules/categories.py', 'categories_module')
        if not module_success:
            st.error("Failed to load Categories module. Please check the module code.")

    elif st.session_state.current_page == "UOM":
        module_success = safe_exec_module('modules/uom.py', 'uom_module')
        if not module_success:
            st.error("Failed to load UOM module. Please check the module code.")

    elif st.session_state.current_page == "Locations":
        module_success = safe_exec_module('modules/locations.py', 'locations_module')
        if not module_success:
            st.error("Failed to load Locations module. Please check the module code.")

    elif st.session_state.current_page == "StockTransfer":
        module_success = safe_exec_module('modules/stock_transfer.py', 'stock_transfer_module')
        if not module_success:
            st.error("Failed to load Stock Transfer module. Please check the module code.")

    elif st.session_state.current_page == "BuildRequests":
        module_success = safe_exec_module('modules/build_requests.py', 'build_requests_module')
        if not module_success:
            st.error("Failed to load Build Requests module. Please check the module code.")

    elif st.session_state.current_page == "Purchases":
        module_success = safe_exec_module('modules/purchases.py', 'purchases_module')
        if not module_success:
            st.error("Failed to load Purchases module. Please check the module code.")

except Exception as e:
    st.error(f"❌ Unexpected error in main application: {str(e)}")
    with st.expander("🔍 Full Error Details"):
        st.code(traceback.format_exc(), language="python")
    
    st.warning("""
    ### Quick Fix for Common Issues:
    
    1. **Empty String in Float Column**: 
       - Open the module file and replace any `''` assignment with `np.nan`
       - Use `pd.NA` or `np.nan` instead of empty strings
       
    2. **Excel File Issues**:
       - Check if the Excel file is not corrupted
       - Ensure columns have correct data types
       
    3. **Module Import Issues**:
       - Make sure all module files exist in the `modules/` folder
       - Check for syntax errors in module files
    """)