# modules/connections.py - Connections Management with Conditional Form
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

st.title("🔗 Connections Management")
st.caption("Unified management for Suppliers, Customers, and Prospects")

db = ExcelBackend()

# Initialize session state
if 'show_add_form' not in st.session_state:
    st.session_state.show_add_form = False
if 'edit_connection_id' not in st.session_state:
    st.session_state.edit_connection_id = None
if 'connection_added' not in st.session_state:
    st.session_state.connection_added = False
if 'last_added_connection' not in st.session_state:
    st.session_state.last_added_connection = None

def init_colaborators():
    colaborators_df = db.get_sheet('colaborators')
    if colaborators_df.empty:
        colaborators_df = pd.DataFrame(columns=[
            'ID', 'Name', 'Type', 'Phone', 'Location', 'Contact_Person',
            'Balance', 'Is_Active', 'Notes', 'Created'
        ])
        db.save_sheet('colaborators', colaborators_df)
    return colaborators_df

# Show success message
if st.session_state.connection_added:
    st.balloons()
    st.success(f"✅ {st.session_state.last_added_connection} added successfully!")
    st.session_state.connection_added = False
    st.rerun()

# ========== ADD/EDIT FORM ==========
if st.session_state.show_add_form or st.session_state.edit_connection_id:
    
    if st.button("← Back to Connections List", use_container_width=True):
        st.session_state.show_add_form = False
        st.session_state.edit_connection_id = None
        st.rerun()
    
    st.markdown("---")
    
    if st.session_state.edit_connection_id:
        st.subheader("✏️ Edit Connection")
        colaborators_df = init_colaborators()
        connection = colaborators_df[colaborators_df['ID'] == st.session_state.edit_connection_id].iloc[0]
        is_edit = True
    else:
        st.subheader("➕ Add New Connection")
        is_edit = False
    
    with st.form(key="connection_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            if is_edit:
                name = st.text_input("Name *", value=connection['Name'])
                type_options = ["CUSTOMER", "SUPPLIER", "PROSPECT"]
                type_index = type_options.index(connection['Type'])
                conn_type = st.selectbox("Type *", type_options, index=type_index)
                phone = st.text_input("Phone", value=connection['Phone'] if connection['Phone'] else "")
                location = st.text_input("Location", value=connection['Location'] if connection['Location'] else "")
            else:
                name = st.text_input("Name *", placeholder="Company or person name")
                conn_type = st.selectbox("Type *", ["CUSTOMER", "SUPPLIER", "PROSPECT"])
                phone = st.text_input("Phone")
                location = st.text_input("Location")
        
        with col2:
            if is_edit:
                contact_person = st.text_input("Contact Person", value=connection['Contact_Person'] if connection['Contact_Person'] else "")
                balance = st.number_input("Balance (MGA)", value=float(connection['Balance']), step=10000.0)
                notes = st.text_area("Notes", value=connection['Notes'] if connection['Notes'] else "")
                is_active = st.checkbox("Active", value=connection['Is_Active'])
            else:
                contact_person = st.text_input("Contact Person")
                balance = st.number_input("Initial Balance (MGA)", value=0.0, step=10000.0)
                notes = st.text_area("Notes", placeholder="Payment terms, special conditions...")
                is_active = st.checkbox("Active", value=True)
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.form_submit_button("Cancel", use_container_width=True):
                st.session_state.show_add_form = False
                st.session_state.edit_connection_id = None
                st.rerun()
        with col_btn2:
            if st.form_submit_button("Save Connection", type="primary", use_container_width=True):
                if not name:
                    st.error("Name is required!")
                else:
                    colaborators_df = init_colaborators()
                    
                    if is_edit:
                        colaborators_df.loc[colaborators_df['ID'] == st.session_state.edit_connection_id, 'Name'] = name.upper()
                        colaborators_df.loc[colaborators_df['ID'] == st.session_state.edit_connection_id, 'Type'] = conn_type
                        colaborators_df.loc[colaborators_df['ID'] == st.session_state.edit_connection_id, 'Phone'] = phone
                        colaborators_df.loc[colaborators_df['ID'] == st.session_state.edit_connection_id, 'Location'] = location
                        colaborators_df.loc[colaborators_df['ID'] == st.session_state.edit_connection_id, 'Contact_Person'] = contact_person
                        colaborators_df.loc[colaborators_df['ID'] == st.session_state.edit_connection_id, 'Balance'] = balance
                        colaborators_df.loc[colaborators_df['ID'] == st.session_state.edit_connection_id, 'Notes'] = notes
                        colaborators_df.loc[colaborators_df['ID'] == st.session_state.edit_connection_id, 'Is_Active'] = is_active
                        db.save_sheet('colaborators', colaborators_df)
                        st.session_state.edit_connection_id = None
                        st.success(f"Connection '{name}' updated!")
                        st.rerun()
                    else:
                        if name.upper() in colaborators_df['Name'].str.upper().values:
                            st.error(f"Connection '{name}' already exists!")
                        else:
                            new_id = db.get_next_id('colaborators')
                            new_row = pd.DataFrame([{
                                'ID': new_id, 'Name': name.upper(), 'Type': conn_type,
                                'Phone': phone, 'Location': location, 'Contact_Person': contact_person,
                                'Balance': balance, 'Is_Active': is_active, 'Notes': notes,
                                'Created': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            }])
                            colaborators_df = pd.concat([colaborators_df, new_row], ignore_index=True)
                            db.save_sheet('colaborators', colaborators_df)
                            st.session_state.show_add_form = False
                            st.session_state.connection_added = True
                            st.session_state.last_added_connection = f"{conn_type} '{name}'"
                            st.rerun()
    
    st.stop()

# ========== MAIN CONNECTIONS LIST VIEW ==========

col_btn1, col_btn2 = st.columns([1, 5])
with col_btn1:
    if st.button("➕ Add New Connection", type="primary", use_container_width=True):
        st.session_state.show_add_form = True
        st.rerun()

st.markdown("---")
st.subheader("Connections List")

colaborators_df = init_colaborators()

if colaborators_df.empty:
    st.info("No connections yet. Click 'Add New Connection' to get started.")
else:
    # Sort by name A-Z
    colaborators_df = colaborators_df.sort_values('Name')
    
    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        type_filter = st.selectbox("Filter by Type", ["ALL", "SUPPLIER", "CUSTOMER", "PROSPECT"])
    with col2:
        active_filter = st.selectbox("Status", ["ALL", "ACTIVE", "INACTIVE"])
    with col3:
        search = st.text_input("Search", placeholder="Name or contact...")
    
    filtered_df = colaborators_df.copy()
    if type_filter != "ALL":
        filtered_df = filtered_df[filtered_df['Type'] == type_filter]
    if active_filter == "ACTIVE":
        filtered_df = filtered_df[filtered_df['Is_Active'] == True]
    elif active_filter == "INACTIVE":
        filtered_df = filtered_df[filtered_df['Is_Active'] == False]
    if search:
        filtered_df = filtered_df[
            filtered_df['Name'].str.contains(search, case=False, na=False) |
            filtered_df['Contact_Person'].str.contains(search, case=False, na=False)
        ]
    
    if not filtered_df.empty:
        for _, conn in filtered_df.iterrows():
            icon = "🏢" if conn['Type'] == 'SUPPLIER' else "👤" if conn['Type'] == 'CUSTOMER' else "🤝"
            
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            with col1:
                st.write(f"{icon} **{conn['Name']}**")
                st.caption(f"{conn['Type']}")
            with col2:
                st.write(f"📞 {conn['Phone'] if conn['Phone'] else '-'}")
                st.write(f"📍 {conn['Location'] if conn['Location'] else '-'}")
            with col3:
                st.write(f"👥 {conn['Contact_Person'] if conn['Contact_Person'] else '-'}")
                balance_color = "🟢" if conn['Balance'] > 0 else "🔴" if conn['Balance'] < 0 else "⚪"
                st.write(f"{balance_color} Balance: {conn['Balance']:,.0f} MGA")
            with col4:
                if st.button(f"✏️ Edit", key=f"edit_conn_{conn['ID']}"):
                    st.session_state.edit_connection_id = conn['ID']
                    st.rerun()
            st.markdown("---")
    else:
        st.info("No connections match the filters")

st.divider()
st.caption(f"📊 Total: {len(colaborators_df)} connections")