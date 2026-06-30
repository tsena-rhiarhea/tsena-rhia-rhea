# modules/internal.py - Unified Users & Staff Management
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from excel_backend import ExcelBackend
from auth import has_access, get_current_user, hash_password

user = get_current_user()
if not user:
    st.error("Please login first")
    st.stop()

st.title("Internal Directory")
st.caption("Manage Users (login accounts) and Staff (employees)")

db = ExcelBackend()

def init_staff():
    staff_df = db.get_sheet('staff')
    if staff_df.empty:
        staff_df = pd.DataFrame(columns=[
            'ID', 'Name', 'Position', 'Department', 'Phone', 'Email',
            'Is_Supervisor', 'Supervisor_Of_Location', 'Is_Active', 'Notes', 'Created'
        ])
        db.save_sheet('staff', staff_df)
    return staff_df

def safe_str(value):
    if pd.isna(value) or value is None:
        return ""
    return str(value)

def safe_bool(value):
    if pd.isna(value) or value is None:
        return False
    return bool(value)

tab1, tab2, tab3, tab4 = st.tabs(["All Personnel", "Add Staff", "Edit Staff", "Manage Users"])

# ========== TAB 1: ALL PERSONNEL ==========
with tab1:
    st.subheader("All Personnel")
    
    staff_df = init_staff()
    users_df = db.get_sheet('users')
    
    if staff_df.empty and users_df.empty:
        st.info("No staff or users found. Add staff members or create user accounts.")
    else:
        display_data = []
        
        for _, staff in staff_df.iterrows():
            user_match = users_df[users_df['Full_Name'] == staff['Name']] if not users_df.empty else pd.DataFrame()
            
            display_data.append({
                'ID': int(staff['ID']),
                'Type': 'Staff',
                'Name': safe_str(staff['Name']),
                'Position': safe_str(staff['Position']) if safe_str(staff['Position']) else '-',
                'Department': safe_str(staff['Department']) if safe_str(staff['Department']) else '-',
                'Supervisor': 'Yes' if safe_bool(staff['Is_Supervisor']) else 'No',
                'Has Login': 'Yes' if not user_match.empty else 'No',
                'User Role': safe_str(user_match.iloc[0]['Role']) if not user_match.empty else '-',
                'User Name': safe_str(user_match.iloc[0]['Username']) if not user_match.empty else '-',
                'Status': 'Active' if safe_bool(staff['Is_Active']) else 'Inactive'
            })
        
        if not users_df.empty:
            for _, usr in users_df.iterrows():
                staff_match = staff_df[staff_df['Name'] == usr['Full_Name']]
                if staff_match.empty:
                    display_data.append({
                        'ID': int(usr['ID']),
                        'Type': 'User Only',
                        'Name': safe_str(usr['Full_Name']),
                        'Position': '-',
                        'Department': '-',
                        'Supervisor': '-',
                        'Has Login': 'Yes',
                        'User Role': safe_str(usr['Role']),
                        'User Name': safe_str(usr['Username']),
                        'Status': 'Active' if safe_bool(usr['Is_Active']) else 'Inactive'
                    })
        
        st.dataframe(pd.DataFrame(display_data), width='stretch', hide_index=True)

# ========== TAB 2: ADD STAFF ==========
with tab2:
    st.subheader("Add Staff Member")
    st.caption("Add an employee and optionally create their login account")
    
    staff_df = init_staff()
    users_df = db.get_sheet('users')
    
    col1, col2 = st.columns(2)
    
    with col1:
        staff_name = st.text_input("Full Name *", key="add_staff_name")
        staff_position = st.text_input("Position", placeholder="Warehouse Manager, Shift Supervisor", key="add_staff_position")
        staff_dept = st.text_input("Department", key="add_staff_dept")
        staff_phone = st.text_input("Phone", key="add_staff_phone")
        staff_email = st.text_input("Email", key="add_staff_email")
    
    with col2:
        is_supervisor = st.checkbox("Is Supervisor", key="add_is_supervisor")
        staff_notes = st.text_area("Notes", key="add_staff_notes")
        is_active = st.checkbox("Active", value=True, key="add_staff_active")
    
    st.markdown("---")
    st.markdown("Create User Account")
    create_user = st.checkbox("Create login account for this staff member", key="add_create_user")
    
    if create_user:
        col1, col2 = st.columns(2)
        with col1:
            username = st.text_input("Username", key="add_staff_username")
        with col2:
            password = st.text_input("Password", type="password", key="add_staff_password")
        user_role = st.selectbox("User Role", ["CASHIER", "SUPERVISOR", "MANAGER", "ADMIN"], key="add_staff_role")
    
    if st.button("Add Staff Member", type="primary", key="add_staff_btn"):
        if not staff_name:
            st.error("Name is required!")
        else:
            if staff_name.upper() in staff_df['Name'].str.upper().values:
                st.error(f"Staff '{staff_name}' already exists!")
            else:
                new_id = db.get_next_id('staff')
                new_row = pd.DataFrame([{
                    'ID': new_id,
                    'Name': staff_name.strip().upper(),
                    'Position': staff_position if staff_position else None,
                    'Department': staff_dept if staff_dept else None,
                    'Phone': staff_phone if staff_phone else None,
                    'Email': staff_email if staff_email else None,
                    'Is_Supervisor': bool(is_supervisor),
                    'Supervisor_Of_Location': None,
                    'Is_Active': bool(is_active),
                    'Notes': staff_notes if staff_notes else None,
                    'Created': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }])
                staff_df = pd.concat([staff_df, new_row], ignore_index=True)
                db.save_sheet('staff', staff_df)
                
                if create_user and username and password:
                    if username.upper() in users_df['Username'].str.upper().values:
                        st.warning(f"Staff added but username '{username}' already exists. No user account created.")
                    else:
                        new_user_id = db.get_next_id('users')
                        new_user = pd.DataFrame([{
                            'ID': new_user_id,
                            'Username': username.upper(),
                            'Password': hash_password(password),
                            'Full_Name': staff_name.strip().upper(),
                            'Role': user_role,
                            'Is_Active': True,
                            'Created': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }])
                        users_df = pd.concat([users_df, new_user], ignore_index=True)
                        db.save_sheet('users', users_df)
                        st.success(f"Staff '{staff_name}' added with user account '{username}'!")
                        st.rerun()
                else:
                    st.success(f"Staff '{staff_name}' added (no login account)!")
                    st.rerun()

# ========== TAB 3: EDIT STAFF ==========
with tab3:
    st.subheader("Edit Staff Member")
    st.caption("Edit staff details, link/unlink user accounts, or delete staff")
    
    staff_df = init_staff()
    users_df = db.get_sheet('users')
    
    if staff_df.empty:
        st.info("No staff members to edit. Add some first.")
    else:
        staff_options = {f"{safe_str(row['Name'])} (ID: {int(row['ID'])})": row['ID'] for _, row in staff_df.iterrows()}
        
        if 'edit_selected_staff_id' not in st.session_state:
            st.session_state.edit_selected_staff_id = list(staff_options.values())[0] if staff_options else None
        
        selected_staff_display = st.selectbox(
            "Select Staff Member", 
            list(staff_options.keys()),
            key="edit_select_staff_dropdown"
        )
        
        new_staff_id = staff_options[selected_staff_display]
        if st.session_state.edit_selected_staff_id != new_staff_id:
            st.session_state.edit_selected_staff_id = new_staff_id
            st.rerun()
        
        staff_id = st.session_state.edit_selected_staff_id
        selected = staff_df[staff_df['ID'] == staff_id].iloc[0]
        
        st.divider()
        
        # Check current linked user
        current_user = users_df[users_df['Full_Name'] == selected['Name']] if not users_df.empty else pd.DataFrame()
        
        # LINK/UNLINK SECTION (outside the main form)
        if not current_user.empty:
            st.info(f"Currently linked to user: {safe_str(current_user.iloc[0]['Username'])} (Role: {safe_str(current_user.iloc[0]['Role'])})")
            if st.button("Unlink User Account", key="unlink_user_btn"):
                users_df.loc[users_df['Full_Name'] == selected['Name'], 'Full_Name'] = safe_str(selected['Name']) + "_UNLINKED"
                db.save_sheet('users', users_df)
                st.success(f"User account unlinked from {safe_str(selected['Name'])}")
                st.rerun()
        else:
            st.info("No user account linked to this staff member")
            
            link_option = st.radio("Option", ["Create new user", "Link existing user"], key=f"link_option_{staff_id}")
            
            if link_option == "Create new user":
                with st.form(key=f"create_user_form_{staff_id}"):
                    new_username = st.text_input("Username", key=f"link_new_username_{staff_id}")
                    new_password = st.text_input("Password", type="password", key=f"link_new_password_{staff_id}")
                    new_role = st.selectbox("Role", ["CASHIER", "SUPERVISOR", "MANAGER", "ADMIN"], key=f"link_new_role_{staff_id}")
                    
                    if st.form_submit_button("Create and Link User", key="create_link_user_btn"):
                        if new_username and new_password:
                            if new_username.upper() in users_df['Username'].str.upper().values:
                                st.error(f"Username '{new_username}' already exists!")
                            else:
                                new_user_id = db.get_next_id('users')
                                new_user = pd.DataFrame([{
                                    'ID': new_user_id,
                                    'Username': new_username.upper(),
                                    'Password': hash_password(new_password),
                                    'Full_Name': safe_str(selected['Name']),
                                    'Role': new_role,
                                    'Is_Active': True,
                                    'Created': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                }])
                                users_df = pd.concat([users_df, new_user], ignore_index=True)
                                db.save_sheet('users', users_df)
                                st.success(f"User '{new_username}' created and linked to {safe_str(selected['Name'])}!")
                                st.rerun()
                        else:
                            st.error("Username and password required")
            
            else:
                linked_names = staff_df['Name'].tolist()
                available_users = users_df[~users_df['Full_Name'].isin(linked_names)]
                
                if not available_users.empty:
                    user_options = {f"{safe_str(row['Username'])} ({safe_str(row['Full_Name'])})": row['ID'] for _, row in available_users.iterrows()}
                    
                    selected_user_display = st.selectbox(
                        "Select User", 
                        list(user_options.keys()), 
                        key=f"existing_user_select_{staff_id}"
                    )
                    
                    user_id = user_options[selected_user_display]
                    
                    if st.button("Link User", key=f"link_existing_user_btn_{staff_id}"):
                        users_df.loc[users_df['ID'] == user_id, 'Full_Name'] = safe_str(selected['Name'])
                        db.save_sheet('users', users_df)
                        st.success(f"User linked to {safe_str(selected['Name'])}!")
                        st.rerun()
                else:
                    st.info("No available users to link. Create a new user instead.")
        
        st.markdown("---")
        
        # EDIT STAFF DETAILS FORM
        with st.form(key=f"edit_staff_details_form_{staff_id}"):
            st.markdown("### Edit Staff Details")
            
            col1, col2 = st.columns(2)
            
            with col1:
                new_name = st.text_input("Full Name", value=safe_str(selected['Name']), key=f"edit_staff_name_{staff_id}")
                new_position = st.text_input("Position", value=safe_str(selected['Position']), key=f"edit_position_{staff_id}")
                new_dept = st.text_input("Department", value=safe_str(selected['Department']), key=f"edit_dept_{staff_id}")
                new_phone = st.text_input("Phone", value=safe_str(selected['Phone']), key=f"edit_phone_{staff_id}")
            
            with col2:
                new_email = st.text_input("Email", value=safe_str(selected['Email']), key=f"edit_email_{staff_id}")
                new_supervisor = st.checkbox("Is Supervisor", value=safe_bool(selected['Is_Supervisor']), key=f"edit_supervisor_{staff_id}")
                new_notes = st.text_area("Notes", value=safe_str(selected['Notes']), key=f"edit_notes_{staff_id}")
                new_active = st.checkbox("Active", value=safe_bool(selected['Is_Active']), key=f"edit_active_{staff_id}")
            
            if st.form_submit_button("Save Staff Changes", type="primary"):
                staff_df.loc[staff_df['ID'] == staff_id, 'Name'] = new_name.strip().upper() if new_name else selected['Name']
                staff_df.loc[staff_df['ID'] == staff_id, 'Position'] = new_position if new_position else None
                staff_df.loc[staff_df['ID'] == staff_id, 'Department'] = new_dept if new_dept else None
                staff_df.loc[staff_df['ID'] == staff_id, 'Phone'] = new_phone if new_phone else None
                staff_df.loc[staff_df['ID'] == staff_id, 'Email'] = new_email if new_email else None
                staff_df.loc[staff_df['ID'] == staff_id, 'Is_Supervisor'] = bool(new_supervisor)
                staff_df.loc[staff_df['ID'] == staff_id, 'Notes'] = new_notes if new_notes else None
                staff_df.loc[staff_df['ID'] == staff_id, 'Is_Active'] = bool(new_active)
                db.save_sheet('staff', staff_df)
                st.success("Staff member updated!")
                st.rerun()
        
        st.markdown("---")
        
        # DELETE SECTION
        st.markdown("### Delete Staff Member")
        delete_confirm = st.text_input("Type 'DELETE' to confirm deletion", key=f"delete_confirm_{staff_id}")
        
        if delete_confirm == "DELETE":
            if st.button("Delete Staff Member", type="secondary", key=f"delete_staff_btn_{staff_id}"):
                staff_df = staff_df[staff_df['ID'] != staff_id]
                db.save_sheet('staff', staff_df)
                st.success(f"Staff member '{safe_str(selected['Name'])}' deleted!")
                st.rerun()
        else:
            if delete_confirm:
                st.warning("Type 'DELETE' exactly to enable deletion")

# ========== TAB 4: MANAGE USERS ==========
with tab4:
    st.subheader("Manage User Accounts")
    st.caption("Create, edit, or delete user login accounts")
    
    users_df = db.get_sheet('users')
    staff_df = init_staff()
    
    if user['role'] != 'ADMIN':
        st.warning("Only ADMIN can manage user accounts")
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Create New User")
            
            with st.form(key="create_user_form"):
                new_username = st.text_input("Username", key="manage_new_username")
                new_password = st.text_input("Password", type="password", key="manage_new_password")
                new_full_name = st.text_input("Full Name", key="manage_new_full_name")
                new_role = st.selectbox("Role", ["CASHIER", "SUPERVISOR", "MANAGER", "ADMIN"], key="manage_new_role")
                new_active = st.checkbox("Active", value=True, key="manage_new_active")
                
                if st.form_submit_button("Create User", type="primary"):
                    if not new_username or not new_password or not new_full_name:
                        st.error("Username, password, and full name are required!")
                    elif new_username.upper() in users_df['Username'].str.upper().values:
                        st.error(f"Username '{new_username}' already exists!")
                    else:
                        new_id = db.get_next_id('users')
                        new_user = pd.DataFrame([{
                            'ID': new_id,
                            'Username': new_username.upper(),
                            'Password': hash_password(new_password),
                            'Full_Name': new_full_name.strip().upper(),
                            'Role': new_role,
                            'Is_Active': bool(new_active),
                            'Created': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }])
                        users_df = pd.concat([users_df, new_user], ignore_index=True)
                        db.save_sheet('users', users_df)
                        st.success(f"User '{new_username}' created!")
                        st.rerun()
        
        with col2:
            st.markdown("### Edit/Delete User")
            
            if not users_df.empty:
                user_options = {f"{safe_str(row['Username'])} ({safe_str(row['Full_Name'])})": row['ID'] for _, row in users_df.iterrows()}
                
                if 'manage_selected_user_id' not in st.session_state:
                    st.session_state.manage_selected_user_id = list(user_options.values())[0] if user_options else None
                
                selected_user_display = st.selectbox(
                    "Select User", 
                    list(user_options.keys()),
                    key="manage_select_user_dropdown"
                )
                
                new_user_id = user_options[selected_user_display]
                if st.session_state.manage_selected_user_id != new_user_id:
                    st.session_state.manage_selected_user_id = new_user_id
                    st.rerun()
                
                user_id = st.session_state.manage_selected_user_id
                selected = users_df[users_df['ID'] == user_id].iloc[0]
                
                st.markdown(f"**Editing: {safe_str(selected['Username'])}**")
                
                with st.form(key=f"edit_user_form_{user_id}"):
                    edit_full_name = st.text_input("Full Name", value=safe_str(selected['Full_Name']), key=f"manage_edit_full_name_{user_id}")
                    edit_role = st.selectbox("Role", ["CASHIER", "SUPERVISOR", "MANAGER", "ADMIN"], 
                                            index=["CASHIER", "SUPERVISOR", "MANAGER", "ADMIN"].index(selected['Role']),
                                            key=f"manage_edit_role_{user_id}")
                    edit_active = st.checkbox("Active", value=safe_bool(selected['Is_Active']), key=f"manage_edit_active_{user_id}")
                    
                    linked_staff = staff_df[staff_df['Name'] == selected['Full_Name']]
                    if not linked_staff.empty:
                        st.info(f"Linked to staff: {safe_str(linked_staff.iloc[0]['Name'])}")
                    
                    col_edit, col_delete = st.columns(2)
                    with col_edit:
                        if st.form_submit_button("Save Changes", key="manage_save_user"):
                            users_df.loc[users_df['ID'] == user_id, 'Full_Name'] = edit_full_name.strip().upper()
                            users_df.loc[users_df['ID'] == user_id, 'Role'] = edit_role
                            users_df.loc[users_df['ID'] == user_id, 'Is_Active'] = bool(edit_active)
                            db.save_sheet('users', users_df)
                            st.success("User updated!")
                            st.rerun()
                    
                    with col_delete:
                        if st.form_submit_button("Delete User", type="secondary", key="manage_delete_user"):
                            if selected['Username'] == 'ADMIN':
                                st.error("Cannot delete the default ADMIN user!")
                            else:
                                users_df = users_df[users_df['ID'] != user_id]
                                db.save_sheet('users', users_df)
                                st.success(f"User '{safe_str(selected['Username'])}' deleted!")
                                st.rerun()
            else:
                st.info("No users found")

st.divider()
st.caption("Staff members can have linked user accounts for system access.")