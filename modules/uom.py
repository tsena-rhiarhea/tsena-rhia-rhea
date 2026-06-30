# modules/uom.py - UOM Management with Conditional Form
import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from excel_backend import ExcelBackend
from auth import get_current_user

user = get_current_user()
if not user:
    st.error("Please login first")
    st.stop()

st.title("📏 Units of Measure Management")
st.caption("Manage Base Units and Packaging Units")

db = ExcelBackend()

# Initialize session state
if 'show_add_form' not in st.session_state:
    st.session_state.show_add_form = False
if 'edit_uom_id' not in st.session_state:
    st.session_state.edit_uom_id = None
if 'uom_added' not in st.session_state:
    st.session_state.uom_added = False
if 'last_added_uom' not in st.session_state:
    st.session_state.last_added_uom = None

def init_uom():
    uom_df = db.get_sheet('uom')
    if uom_df.empty:
        uom_df = pd.DataFrame(columns=['ID', 'Name', 'Type', 'Base_Unit', 'Factor', 'Created'])
        db.save_sheet('uom', uom_df)
    return uom_df

def get_product_count_by_uom(uom_id):
    products_df = db.get_sheet('products')
    if products_df.empty:
        return 0
    return len(products_df[products_df['Base_UOM_ID'] == uom_id])

# Show success message
if st.session_state.uom_added:
    st.balloons()
    st.success(f"✅ UOM '{st.session_state.last_added_uom}' added successfully!")
    st.session_state.uom_added = False
    st.rerun()

# ========== ADD/EDIT FORM ==========
if st.session_state.show_add_form or st.session_state.edit_uom_id:
    
    if st.button("← Back to UOM List", use_container_width=True):
        st.session_state.show_add_form = False
        st.session_state.edit_uom_id = None
        st.rerun()
    
    st.markdown("---")
    
    if st.session_state.edit_uom_id:
        st.subheader("✏️ Edit UOM")
        uom_df = init_uom()
        uom = uom_df[uom_df['ID'] == st.session_state.edit_uom_id].iloc[0]
        is_edit = True
    else:
        st.subheader("➕ Add New UOM")
        is_edit = False
    
    with st.form(key="uom_form"):
        if is_edit:
            name = st.text_input("UOM Name", value=uom['Name'])
        else:
            name = st.text_input("UOM Name", placeholder="Example: PC, KG, DOZEN, BOX")
        
        if is_edit:
            uom_type = st.selectbox("Type", ["BASE", "PACKAGING"], index=0 if uom['Type'] == 'BASE' else 1)
        else:
            uom_type = st.selectbox("Type", ["BASE", "PACKAGING"])
        
        if uom_type == "PACKAGING":
            uom_df = init_uom()
            base_units = uom_df[uom_df['Type'] == 'BASE']['Name'].tolist()
            if base_units:
                if is_edit:
                    default_index = base_units.index(uom['Base_Unit']) if uom['Base_Unit'] in base_units else 0
                    base_unit = st.selectbox("Base Unit", base_units, index=default_index)
                else:
                    base_unit = st.selectbox("Base Unit", base_units)
                
                if is_edit:
                    factor = st.number_input("Conversion Factor (1 Packaging = ? Base Units)", min_value=0.1, step=1.0, value=float(uom['Factor']))
                else:
                    factor = st.number_input("Conversion Factor (1 Packaging = ? Base Units)", min_value=0.1, step=1.0, value=1.0)
            else:
                st.error("No base units found. Please add a BASE unit first.")
                base_unit = None
                factor = 1.0
        else:
            base_unit = None
            factor = 1.0
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.form_submit_button("Cancel", use_container_width=True):
                st.session_state.show_add_form = False
                st.session_state.edit_uom_id = None
                st.rerun()
        with col_btn2:
            if st.form_submit_button("Save UOM", type="primary", use_container_width=True):
                if not name:
                    st.error("Name is required!")
                elif uom_type == "PACKAGING" and not base_unit:
                    st.error("Please select a base unit!")
                else:
                    uom_df = init_uom()
                    
                    if is_edit:
                        uom_df.loc[uom_df['ID'] == st.session_state.edit_uom_id, 'Name'] = name.upper()
                        uom_df.loc[uom_df['ID'] == st.session_state.edit_uom_id, 'Type'] = uom_type
                        if uom_type == "PACKAGING":
                            uom_df.loc[uom_df['ID'] == st.session_state.edit_uom_id, 'Base_Unit'] = base_unit
                            uom_df.loc[uom_df['ID'] == st.session_state.edit_uom_id, 'Factor'] = factor
                        else:
                            uom_df.loc[uom_df['ID'] == st.session_state.edit_uom_id, 'Base_Unit'] = '-'
                            uom_df.loc[uom_df['ID'] == st.session_state.edit_uom_id, 'Factor'] = 1.0
                        db.save_sheet('uom', uom_df)
                        st.session_state.edit_uom_id = None
                        st.success(f"UOM '{name}' updated!")
                        st.rerun()
                    else:
                        if name.upper() in uom_df['Name'].str.upper().values:
                            st.error(f"UOM '{name}' already exists!")
                        else:
                            new_id = db.get_next_id('uom')
                            new_row = pd.DataFrame([{
                                'ID': new_id, 'Name': name.upper(), 'Type': uom_type,
                                'Base_Unit': base_unit if uom_type == "PACKAGING" else '-',
                                'Factor': factor, 'Created': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            }])
                            uom_df = pd.concat([uom_df, new_row], ignore_index=True)
                            db.save_sheet('uom', uom_df)
                            st.session_state.show_add_form = False
                            st.session_state.uom_added = True
                            st.session_state.last_added_uom = name
                            st.rerun()
    
    st.stop()

# ========== MAIN UOM LIST VIEW ==========

col_btn1, col_btn2 = st.columns([1, 5])
with col_btn1:
    if st.button("➕ Add New UOM", type="primary", use_container_width=True):
        st.session_state.show_add_form = True
        st.rerun()

st.markdown("---")
st.subheader("UOM List")

uom_df = init_uom()
products_df = db.get_sheet('products')

if uom_df.empty:
    st.info("No UOMs yet. Click 'Add New UOM' to get started.")
else:
    # Sort by name A-Z
    uom_df = uom_df.sort_values('Name')
    
    base_units = uom_df[uom_df['Type'] == 'BASE']
    
    if not base_units.empty:
        for _, base in base_units.iterrows():
            base_product_count = get_product_count_by_uom(base['ID'])
            
            packaging = uom_df[(uom_df['Type'] == 'PACKAGING') & (uom_df['Base_Unit'] == base['Name'])]
            packaging = packaging.sort_values('Factor', ascending=False)
            
            packaging_product_count = 0
            for _, pkg in packaging.iterrows():
                packaging_product_count += get_product_count_by_uom(pkg['ID'])
            
            total_products = base_product_count + packaging_product_count
            
            with st.expander(f"📁 {base['Name']} (Base Unit) - Used by {total_products} product(s)", expanded=False):
                table_data = []
                table_data.append({
                    'ID': base['ID'], 'Name': base['Name'], 'Type': 'BASE',
                    'Factor': 1.0, 'Products': base_product_count
                })
                
                for _, pkg in packaging.iterrows():
                    pkg_product_count = get_product_count_by_uom(pkg['ID'])
                    table_data.append({
                        'ID': pkg['ID'], 'Name': f"  └─ {pkg['Name']}", 'Type': 'PACKAGING',
                        'Factor': pkg['Factor'], 'Products': pkg_product_count
                    })
                
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.dataframe(pd.DataFrame(table_data), width='stretch', hide_index=True)
                with col2:
                    if st.button(f"✏️ Edit", key=f"edit_base_{base['ID']}"):
                        st.session_state.edit_uom_id = base['ID']
                        st.rerun()
                
                for _, pkg in packaging.iterrows():
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.write("")
                    with col2:
                        if st.button(f"✏️ Edit", key=f"edit_pkg_{pkg['ID']}"):
                            st.session_state.edit_uom_id = pkg['ID']
                            st.rerun()
    else:
        st.info("No base units found. Add a BASE unit first.")

st.divider()
st.caption("💡 Base units are the foundation. Packaging units are multiples (e.g., 1 DOZEN = 12 PC)")