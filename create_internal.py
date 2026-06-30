# create_internal.py
content = '''# modules/internal.py - Unified Users & Staff Management
import streamlit as st
import pandas as pd
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

tab1, tab2, tab3 = st.tabs(["All Personnel", "Add Staff", "Manage Users"])

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
                'Type': 'Staff',
                'Name': staff['Name'],
                'Position': staff['Position'] if staff['Position'] else '-',
                'Department': staff['Department'] if staff['Department'] else '-',
                'Supervisor': 'Yes' if staff['Is_Supervisor'] else 'No',
                'Has Login': 'Yes' if not user_match.empty else 'No',
                'User Role': user_match.iloc[0]['Role'] if not user_match.empty else '-',
                'Status': 'Active' if staff['Is_Active'] else 'Inactive'
            })
        
        if not users_df.empty:
            for _, usr in users_df.iterrows():
                staff_match = staff_df[staff_df['Name'] == usr['Full_Name']]
                if staff_match.empty:
                    display_data.append({
                        'Type': 'User Only',
                        'Name': usr['Full_Name'],
                        'Position': '-',
                        'Department': '-',
                        'Supervisor': '-',
                        'Has Login': 'Yes',
                        'User Role': usr['Role'],
                        'Status': 'Active' if usr['Is_Active'] else 'Inactive'
                    })
        
        st.dataframe(pd.DataFrame(display_data), width='stretch', hide_index=True)

with tab2:
    st.subheader("Add Staff Member")
    st.caption("Add an employee and optionally create their login account")
    
    staff_df = init_staff()
    users_df = db.get_sheet('users')
    
    col1, col2 = st.columns(2)
    
    with col1:
        staff_name = st.text_input("Full Name *", key="staff_name")
        staff_position = st.text_input("Position", placeholder="Warehouse Manager, Shift Supervisor", key="staff_position")
        staff_dept = st.text_input("Department", key="staff_dept")
        staff_phone = st.text_input("Phone", key="staff_phone")
        staff_email = st.text_input("Email", key="staff_email")
    
    with col2:
        is_supervisor = st.checkbox("Is Supervisor?", key="is_supervisor")
        staff_notes = st.text_area("Notes", key="staff_notes")
        is_active = st.checkbox("Active", value=True, key="staff_active")
    
    st.markdown("---")
    st.markdown("Create User Account")
    create_user = st.checkbox("Create login account for this staff member", key="create_user")
    
    if create_user:
        col1, col2 = st.columns(2)
        with col1:
            username = st.text_input("Username", key="staff_username")
        with col2:
            password = st.text_input("Password", type="password", key="staff_password")
        user_role = st.selectbox("User Role", ["CASHIER", "SUPERVISOR", "MANAGER", "ADMIN"], key="staff_role")
    
    if st.button("Add Staff Member", type="primary"):
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
                    'Position': staff_position,
                    'Department': staff_dept,
                    'Phone': staff_phone,
                    'Email': staff_email,
                    'Is_Supervisor': is_supervisor,
                    'Supervisor_Of_Location': None,
                    'Is_Active': is_active,
                    'Notes': staff_notes,
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

with tab3:
    st.subheader("Manage User Accounts")
    st.caption("Create, edit, or delete user login accounts")
    
    users_df = db.get_sheet('users')
    staff_df = init_staff()
    
    if user['role'] != 'ADMIN':
        st.warning("Only ADMIN can manage user accounts")
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("Create New User")
            
            new_username = st.text_input("Username", key="new_username")
            new_password = st.text_input("Password", type="password", key="new_password")
            new_full_name = st.text_input("Full Name", key="new_full_name")
            new_role = st.selectbox("Role", ["CASHIER", "SUPERVISOR", "MANAGER", "ADMIN"], key="new_role")
            new_active = st.checkbox("Active", value=True, key="new_active")
            
            if st.button("Create User", type="primary"):
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
                        'Is_Active': new_active,
                        'Created': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }])
                    users_df = pd.concat([users_df, new_user], ignore_index=True)
                    db.save_sheet('users', users_df)
                    st.success(f"User '{new_username}' created!")
                    st.rerun()
        
        with col2:
            st.markdown("Edit/Delete User")
            
            if not users_df.empty:
                user_options = {f"{row['Username']} ({row['Full_Name']})": row['ID'] for _, row in users_df.iterrows()}
                selected_user = st.selectbox("Select User", list(user_options.keys()))
                user_id = user_options[selected_user]
                selected = users_df[users_df['ID'] == user_id].iloc[0]
                
                st.markdown(f"**Editing: {selected['Username']}**")
                
                edit_full_name = st.text_input("Full Name", value=selected['Full_Name'], key="edit_full_name")
                edit_role = st.selectbox("Role", ["CASHIER", "SUPERVISOR", "MANAGER", "ADMIN"], 
                                        index=["CASHIER", "SUPERVISOR", "MANAGER", "ADMIN"].index(selected['Role']),
                                        key="edit_role")
                edit_active = st.checkbox("Active", value=selected['Is_Active'], key="edit_active")
                
                col_edit, col_delete = st.columns(2)
                with col_edit:
                    if st.button("Save Changes", key="save_user"):
                        users_df.loc[users_df['ID'] == user_id, 'Full_Name'] = edit_full_name.strip().upper()
                        users_df.loc[users_df['ID'] == user_id, 'Role'] = edit_role
                        users_df.loc[users_df['ID'] == user_id, 'Is_Active'] = edit_active
                        db.save_sheet('users', users_df)
                        st.success("User updated!")
                        st.rerun()
                
                with col_delete:
                    if st.button("Delete User", key="delete_user"):
                        if selected['Username'] == 'ADMIN':
                            st.error("Cannot delete the default ADMIN user!")
                        else:
                            users_df = users_df[users_df['ID'] != user_id]
                            db.save_sheet('users', users_df)
                            st.success(f"User '{selected['Username']}' deleted!")
                            st.rerun()
            else:
                st.info("No users found")

st.divider()
st.caption("Staff members can have linked user accounts for system access.")
'''

# Write the file with utf-8 encoding
with open('modules/internal.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Created modules/internal.py successfully!")