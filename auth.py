# auth.py - Authentication and User Management (No Last_Login)
import streamlit as st
import hashlib
import pandas as pd
from datetime import datetime
from excel_backend import ExcelBackend

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_users():
    db = ExcelBackend()
    users_df = db.get_sheet('users')
    
    if users_df.empty or len(users_df) == 0:
        # Create new users without Last_Login column
        new_users = pd.DataFrame({
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
        })
        db.save_sheet('users', new_users)
        print("Default users created:")
        print("   ADMIN / admin123")
        print("   MANAGER / manager123")
        print("   SUPERVISOR / super123")
        print("   CASHIER / cash123")
    
    return db.get_sheet('users')

def login():
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔐 Login")
    
    if 'user' in st.session_state and st.session_state.user:
        user = st.session_state.user
        st.sidebar.success(f"Logged in as: {user['full_name']}")
        st.sidebar.caption(f"Role: {user['role']}")
        if st.sidebar.button("Logout", use_container_width=True):
            st.session_state.user = None
            st.rerun()
        return True
    
    with st.sidebar.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login", use_container_width=True)
        
        if submitted:
            db = ExcelBackend()
            users_df = db.get_sheet('users')
            hashed = hash_password(password)
            
            # Find user
            user_match = None
            for idx, row in users_df.iterrows():
                if row['Username'] == username.upper() and row['Password'] == hashed and row['Is_Active'] == True:
                    user_match = row
                    break
            
            if user_match is not None:
                st.session_state.user = {
                    'id': int(user_match['ID']),
                    'username': user_match['Username'],
                    'full_name': user_match['Full_Name'],
                    'role': user_match['Role']
                }
                st.rerun()
            else:
                st.sidebar.error("Invalid username or password")
    
    return False

def has_access(required_role):
    if 'user' not in st.session_state or not st.session_state.user:
        return False
    
    role_hierarchy = {'CASHIER': 1, 'SUPERVISOR': 2, 'MANAGER': 3, 'ADMIN': 4}
    user_role = st.session_state.user['role']
    user_level = role_hierarchy.get(user_role, 0)
    required_level = role_hierarchy.get(required_role, 0)
    
    return user_level >= required_level

def get_current_user():
    return st.session_state.get('user', None)