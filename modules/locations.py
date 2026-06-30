# modules/locations.py - Location Management with Conditional Form
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

st.title("📍 Location Management")
st.caption("Manage storage locations with supervisor assignments")

db = ExcelBackend()

# Initialize session state
if 'show_add_form' not in st.session_state:
    st.session_state.show_add_form = False
if 'edit_location_id' not in st.session_state:
    st.session_state.edit_location_id = None
if 'location_added' not in st.session_state:
    st.session_state.location_added = False
if 'last_added_location' not in st.session_state:
    st.session_state.last_added_location = None

def init_locations():
    locations_df = db.get_sheet('locations')
    required_columns = ['ID', 'Name', 'Parent_ID', 'Level', 'Can_Hold_Stock', 'Supervisor_ID', 'Description', 'Created']
    for col in required_columns:
        if col not in locations_df.columns:
            locations_df[col] = None
    if locations_df.empty:
        default_location = pd.DataFrame([{
            'ID': 1, 'Name': 'TSENA RHIA-RHEA', 'Parent_ID': None, 'Level': 0,
            'Can_Hold_Stock': False, 'Supervisor_ID': None,
            'Description': 'Main headquarters - Cannot hold stock directly',
            'Created': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }])
        locations_df = default_location
        db.save_sheet('locations', locations_df)
    return locations_df

def init_staff():
    staff_df = db.get_sheet('staff')
    if staff_df.empty:
        staff_df = pd.DataFrame(columns=[
            'ID', 'Name', 'Position', 'Department', 'Phone', 'Email',
            'Is_Supervisor', 'Supervisor_Of_Location', 'Is_Active', 'Notes', 'Created'
        ])
        db.save_sheet('staff', staff_df)
    return staff_df

def get_staff_name(staff_id):
    if pd.isna(staff_id) or staff_id is None:
        return "Unassigned"
    df = db.get_sheet('staff')
    result = df[df['ID'] == staff_id]
    return result.iloc[0]['Name'] if not result.empty else "Unassigned"

def get_full_path(location_id, locations_df):
    if pd.isna(location_id) or location_id is None:
        return ""
    result = locations_df[locations_df['ID'] == location_id]
    if result.empty:
        return ""
    loc = result.iloc[0]
    if pd.isna(loc['Parent_ID']) or loc['Parent_ID'] is None:
        return loc['Name']
    else:
        parent_path = get_full_path(loc['Parent_ID'], locations_df)
        return f"{parent_path} > {loc['Name']}"

def get_all_sub_locations(parent_id, locations_df):
    sub_locs = []
    children = locations_df[locations_df['Parent_ID'] == parent_id]
    for _, child in children.iterrows():
        sub_locs.append(child['ID'])
        sub_locs.extend(get_all_sub_locations(child['ID'], locations_df))
    return sub_locs

# Show success message
if st.session_state.location_added:
    st.balloons()
    st.success(f"✅ Location '{st.session_state.last_added_location}' added successfully!")
    st.session_state.location_added = False
    st.rerun()

# ========== ADD/EDIT FORM ==========
if st.session_state.show_add_form or st.session_state.edit_location_id:
    
    if st.button("← Back to Location List", use_container_width=True):
        st.session_state.show_add_form = False
        st.session_state.edit_location_id = None
        st.rerun()
    
    st.markdown("---")
    
    if st.session_state.edit_location_id:
        st.subheader("✏️ Edit Location")
        locations_df = init_locations()
        location = locations_df[locations_df['ID'] == st.session_state.edit_location_id].iloc[0]
        is_edit = True
    else:
        st.subheader("➕ Add New Location")
        is_edit = False
    
    locations_df = init_locations()
    staff_df = init_staff()
    
    with st.form(key="location_form"):
        if is_edit:
            name = st.text_input("Location Name", value=location['Name'])
            description = st.text_area("Description", value=location['Description'] if location['Description'] else "")
        else:
            name = st.text_input("Location Name", placeholder="Example: MAIN AREA, OUTSIDE DISPLAY")
            description = st.text_area("Description", placeholder="What is stored here?")
        
        # Parent selection (only for add)
        if not is_edit:
            parent_locations = locations_df[locations_df['Can_Hold_Stock'] == False]
            parent_options = {"None (Root Level)": None}
            for _, loc in parent_locations.iterrows():
                path = get_full_path(loc['ID'], locations_df)
                parent_options[path] = loc['ID']
            parent_selected = st.selectbox("Parent Location", list(parent_options.keys()))
            parent_id = parent_options[parent_selected]
            parent_level = locations_df[locations_df['ID'] == parent_id]['Level'].iloc[0] if parent_id else 0
        
        # Can hold stock
        if is_edit:
            can_hold = st.checkbox("Can hold stock?", value=location['Can_Hold_Stock'])
        else:
            can_hold = st.checkbox("Can hold stock?", value=True)
        
        # Supervisor selection
        supervisors = staff_df[staff_df['Is_Supervisor'] == True]
        supervisor_options = {row['Name']: row['ID'] for _, row in supervisors.iterrows()}
        supervisor_options["None"] = None
        
        if is_edit:
            current_supervisor = get_staff_name(location['Supervisor_ID'])
            default_index = list(supervisor_options.keys()).index(current_supervisor) if current_supervisor in supervisor_options.keys() else len(supervisor_options) - 1
            supervisor_selected = st.selectbox("Supervisor", list(supervisor_options.keys()), index=default_index)
        else:
            supervisor_selected = st.selectbox("Supervisor", list(supervisor_options.keys()))
        
        supervisor_id = supervisor_options[supervisor_selected]
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.form_submit_button("Cancel", use_container_width=True):
                st.session_state.show_add_form = False
                st.session_state.edit_location_id = None
                st.rerun()
        with col_btn2:
            if st.form_submit_button("Save Location", type="primary", use_container_width=True):
                if not name:
                    st.error("Name is required!")
                else:
                    if is_edit:
                        locations_df.loc[locations_df['ID'] == st.session_state.edit_location_id, 'Name'] = name.upper()
                        locations_df.loc[locations_df['ID'] == st.session_state.edit_location_id, 'Description'] = description
                        locations_df.loc[locations_df['ID'] == st.session_state.edit_location_id, 'Can_Hold_Stock'] = can_hold
                        locations_df.loc[locations_df['ID'] == st.session_state.edit_location_id, 'Supervisor_ID'] = supervisor_id
                        db.save_sheet('locations', locations_df)
                        st.session_state.edit_location_id = None
                        st.success(f"Location '{name}' updated!")
                        st.rerun()
                    else:
                        if name.upper() in locations_df['Name'].str.upper().values:
                            st.error(f"Location '{name}' already exists!")
                        else:
                            new_id = db.get_next_id('locations')
                            level = parent_level + 1 if parent_id else 0
                            new_row = pd.DataFrame([{
                                'ID': new_id, 'Name': name.upper(), 'Parent_ID': parent_id,
                                'Level': level, 'Can_Hold_Stock': can_hold,
                                'Supervisor_ID': supervisor_id, 'Description': description,
                                'Created': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            }])
                            locations_df = pd.concat([locations_df, new_row], ignore_index=True)
                            db.save_sheet('locations', locations_df)
                            st.session_state.show_add_form = False
                            st.session_state.location_added = True
                            st.session_state.last_added_location = name
                            st.rerun()
    
    st.stop()

# ========== MAIN LOCATION LIST VIEW ==========

col_btn1, col_btn2 = st.columns([1, 5])
with col_btn1:
    if st.button("➕ Add New Location", type="primary", use_container_width=True):
        st.session_state.show_add_form = True
        st.rerun()

st.markdown("---")
st.subheader("Location List")

locations_df = init_locations()
staff_df = init_staff()

if len(locations_df) <= 1:
    st.info("Only the main location exists. Click 'Add New Location' to get started.")
else:
    table_data = []
    for _, loc in locations_df.iterrows():
        if loc['ID'] == 1:
            continue
        indent = "  " * loc['Level'] if loc['Level'] > 0 else ""
        icon = "📍" if loc['Can_Hold_Stock'] else "🏢"
        
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        with col1:
            st.write(f"{indent}{icon} **{loc['Name']}**")
            st.caption(f"{indent}  {loc['Description'] if loc['Description'] else '-'}")
        with col2:
            st.caption(f"ID: {loc['ID']}")
            st.caption(f"Level: {loc['Level']}")
        with col3:
            st.caption(f"Supervisor: {get_staff_name(loc['Supervisor_ID'])}")
            st.caption(f"Type: {'Storage' if loc['Can_Hold_Stock'] else 'Parent'}")
        with col4:
            if st.button(f"✏️ Edit", key=f"edit_loc_{loc['ID']}"):
                st.session_state.edit_location_id = loc['ID']
                st.rerun()
        st.markdown("---")

st.divider()
st.caption("💡 Parent locations (🏢) organize - Storage locations (📍) hold inventory")