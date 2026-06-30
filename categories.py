# modules/categories.py - Category Management with Conditional Form
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

st.title("📁 Category Management")
st.caption("Manage product categories and sub-categories (unlimited levels)")

db = ExcelBackend()

# Initialize session state
if 'show_add_form' not in st.session_state:
    st.session_state.show_add_form = False
if 'edit_category_id' not in st.session_state:
    st.session_state.edit_category_id = None
if 'category_added' not in st.session_state:
    st.session_state.category_added = False
if 'last_added_category' not in st.session_state:
    st.session_state.last_added_category = None

def init_categories():
    categories_df = db.get_sheet('categories')
    if categories_df.empty:
        default_root = pd.DataFrame([{
            'ID': 1, 'Name': 'ALL PRODUCTS', 'Parent_ID': None,
            'Level': 0, 'Created': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }])
        db.save_sheet('categories', default_root)
        return default_root
    return categories_df

def get_category_path(category_id, categories_df):
    if pd.isna(category_id) or category_id is None or category_id == 1:
        return "ALL PRODUCTS"
    result = categories_df[categories_df['ID'] == category_id]
    if result.empty:
        return "Unknown"
    cat = result.iloc[0]
    if pd.isna(cat['Parent_ID']) or cat['Parent_ID'] is None or cat['Parent_ID'] == 1:
        return cat['Name']
    else:
        parent_path = get_category_path(cat['Parent_ID'], categories_df)
        return f"{parent_path} > {cat['Name']}"

def get_product_count(category_id, products_df):
    if products_df.empty or 'Category_ID' not in products_df.columns:
        return 0
    return len(products_df[products_df['Category_ID'] == category_id])

def get_all_subcategories(category_id, categories_df):
    sub_cats = []
    children = categories_df[categories_df['Parent_ID'] == category_id]
    for _, child in children.iterrows():
        sub_cats.append(child['ID'])
        sub_cats.extend(get_all_subcategories(child['ID'], categories_df))
    return sub_cats

def get_total_products_in_tree(category_id, categories_df, products_df):
    all_cats = get_all_subcategories(category_id, categories_df)
    all_cats.append(category_id)
    if products_df.empty or 'Category_ID' not in products_df.columns:
        return 0
    return len(products_df[products_df['Category_ID'].isin(all_cats)])

# Show success message
if st.session_state.category_added:
    st.balloons()
    st.success(f"✅ Category '{st.session_state.last_added_category}' added successfully!")
    st.session_state.category_added = False
    st.rerun()

# ========== ADD/EDIT FORM ==========
if st.session_state.show_add_form or st.session_state.edit_category_id:
    
    if st.button("← Back to Category List", use_container_width=True):
        st.session_state.show_add_form = False
        st.session_state.edit_category_id = None
        st.rerun()
    
    st.markdown("---")
    
    if st.session_state.edit_category_id:
        st.subheader("✏️ Edit Category")
        categories_df = init_categories()
        category = categories_df[categories_df['ID'] == st.session_state.edit_category_id].iloc[0]
        is_edit = True
    else:
        st.subheader("➕ Add New Category")
        is_edit = False
    
    categories_df = init_categories()
    
    with st.form(key="category_form"):
        if is_edit:
            name = st.text_input("Category Name", value=category['Name'])
        else:
            name = st.text_input("Category Name", placeholder="Example: ELECTRONICS, FURNITURE")
        
        if is_edit:
            # For edit, show current parent
            if category['Parent_ID'] is None or category['Parent_ID'] == 1:
                current_parent = "None (Root Category)"
            else:
                parent_cat = categories_df[categories_df['ID'] == category['Parent_ID']].iloc[0]
                current_parent = get_category_path(parent_cat['ID'], categories_df)
            st.info(f"Current Parent: {current_parent}")
        else:
            # For add, allow parent selection
            parent_options = {"None (Root Category)": None}
            for _, cat in categories_df.iterrows():
                if cat['ID'] != 1:
                    path = get_category_path(cat['ID'], categories_df)
                    parent_options[path] = cat['ID']
            parent_selected = st.selectbox("Parent Category", list(parent_options.keys()))
            parent_id = parent_options[parent_selected]
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.form_submit_button("Cancel", use_container_width=True):
                st.session_state.show_add_form = False
                st.session_state.edit_category_id = None
                st.rerun()
        with col_btn2:
            if st.form_submit_button("Save Category", type="primary", use_container_width=True):
                if not name:
                    st.error("Name is required!")
                else:
                    if is_edit:
                        categories_df.loc[categories_df['ID'] == st.session_state.edit_category_id, 'Name'] = name.upper()
                        db.save_sheet('categories', categories_df)
                        st.session_state.edit_category_id = None
                        st.success(f"Category '{name}' updated!")
                        st.rerun()
                    else:
                        if name.upper() in categories_df['Name'].str.upper().values:
                            st.error(f"Category '{name}' already exists!")
                        else:
                            new_id = db.get_next_id('categories')
                            level = 0
                            if parent_id:
                                parent_level = categories_df[categories_df['ID'] == parent_id]['Level'].iloc[0]
                                level = parent_level + 1
                            new_row = pd.DataFrame([{
                                'ID': new_id, 'Name': name.upper(), 'Parent_ID': parent_id,
                                'Level': level, 'Created': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            }])
                            categories_df = pd.concat([categories_df, new_row], ignore_index=True)
                            db.save_sheet('categories', categories_df)
                            st.session_state.show_add_form = False
                            st.session_state.category_added = True
                            st.session_state.last_added_category = name
                            st.rerun()
    
    st.stop()

# ========== MAIN CATEGORY LIST VIEW ==========

col_btn1, col_btn2 = st.columns([1, 5])
with col_btn1:
    if st.button("➕ Add New Category", type="primary", use_container_width=True):
        st.session_state.show_add_form = True
        st.rerun()

st.markdown("---")
st.subheader("Category Hierarchy")

categories_df = init_categories()
products_df = db.get_sheet('products')

if len(categories_df) <= 1:
    st.info("Only 'ALL PRODUCTS' exists. Click 'Add New Category' to get started.")
else:
    root_categories = categories_df[(categories_df['Parent_ID'].isna()) & (categories_df['ID'] != 1)].sort_values('Name')
    
    for _, root in root_categories.iterrows():
        total_products = get_total_products_in_tree(root['ID'], categories_df, products_df)
        
        with st.expander(f"📁 {root['Name']} - {total_products} product(s)", expanded=False):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.caption(f"ID: {root['ID']} | Level: {root['Level']}")
            with col2:
                if st.button(f"✏️ Edit", key=f"edit_root_{root['ID']}"):
                    st.session_state.edit_category_id = root['ID']
                    st.rerun()
            with col3:
                direct_products = get_product_count(root['ID'], products_df)
                st.caption(f"Products: {direct_products} (Tree: {total_products})")
            
            def display_children(parent_id, level=1):
                children = categories_df[categories_df['Parent_ID'] == parent_id].sort_values('Name')
                for _, child in children.iterrows():
                    indent = "  " * level
                    child_products = get_total_products_in_tree(child['ID'], categories_df, products_df)
                    
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.write(f"{indent}└─ 📁 **{child['Name']}**")
                        st.caption(f"{indent}   ID: {child['ID']} | Level: {child['Level']}")
                    with col2:
                        if st.button(f"✏️ Edit", key=f"edit_child_{child['ID']}"):
                            st.session_state.edit_category_id = child['ID']
                            st.rerun()
                    with col3:
                        st.caption(f"Products: {child_products}")
                    
                    display_children(child['ID'], level + 1)
            
            display_children(root['ID'])

st.divider()
st.caption("💡 Categories can have unlimited levels. Click Edit on any category to modify it.")