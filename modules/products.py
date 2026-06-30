# modules/products.py - Product Management with Category View
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

st.title("📦 Product Management")
st.caption("Complete product management with packaging breakdown")

db = ExcelBackend()

# Initialize session state
if 'show_add_form' not in st.session_state:
    st.session_state.show_add_form = False
if 'edit_product_id' not in st.session_state:
    st.session_state.edit_product_id = None
if 'product_added' not in st.session_state:
    st.session_state.product_added = False
if 'last_added_product' not in st.session_state:
    st.session_state.last_added_product = None
if 'view_mode' not in st.session_state:
    st.session_state.view_mode = "list"  # "list" or "category"
if 'selected_category' not in st.session_state:
    st.session_state.selected_category = None

def safe_str(value):
    if pd.isna(value) or value is None:
        return ""
    return str(value).strip()

def safe_float(value):
    if value is None or pd.isna(value):
        return 0.0
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0

def safe_int(value):
    if value is None or pd.isna(value):
        return 0
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return 0

def get_uom_name(uom_id):
    if pd.isna(uom_id) or uom_id is None:
        return "Unknown"
    df = db.get_sheet('uom')
    result = df[df['ID'] == uom_id]
    return result.iloc[0]['Name'] if not result.empty else "Unknown"

def get_uom_factor(uom_id):
    if pd.isna(uom_id) or uom_id is None:
        return 1
    df = db.get_sheet('uom')
    result = df[df['ID'] == uom_id]
    return float(result.iloc[0]['Factor']) if not result.empty else 1

def get_category_path(category_id, categories_df):
    if pd.isna(category_id) or category_id is None:
        return "Uncategorized"
    result = categories_df[categories_df['ID'] == category_id]
    if result.empty:
        return "Unknown"
    cat = result.iloc[0]
    if pd.isna(cat['Parent_ID']) or cat['Parent_ID'] is None:
        return cat['Name']
    else:
        parent_path = get_category_path(cat['Parent_ID'], categories_df)
        return f"{parent_path} > {cat['Name']}"

def get_location_name(location_id):
    if pd.isna(location_id) or location_id is None:
        return "Unknown"
    df = db.get_sheet('locations')
    result = df[df['ID'] == location_id]
    return result.iloc[0]['Name'] if not result.empty else "Unknown"

def get_colaborator_name(colab_id):
    if pd.isna(colab_id) or colab_id is None:
        return "None"
    df = db.get_sheet('colaborators')
    result = df[df['ID'] == colab_id]
    return result.iloc[0]['Name'] if not result.empty else "Unknown"

def get_packaging_units(base_uom_id):
    if pd.isna(base_uom_id) or base_uom_id is None:
        return pd.DataFrame()
    uom_df = db.get_sheet('uom')
    base_uom = uom_df[uom_df['ID'] == base_uom_id]
    if base_uom.empty:
        return pd.DataFrame()
    base_name = base_uom.iloc[0]['Name']
    packaging = uom_df[(uom_df['Type'] == 'PACKAGING') & (uom_df['Base_Unit'] == base_name)]
    return packaging.sort_values('Factor', ascending=False)

def get_product_packaging(product_id):
    pp_df = db.get_sheet('product_packaging')
    result = pp_df[pp_df['Product_ID'] == product_id]
    return result['UOM_ID'].tolist() if not result.empty else []

def save_product_packaging(product_id, uom_ids):
    pp_df = db.get_sheet('product_packaging')
    pp_df = pp_df[pp_df['Product_ID'] != product_id]
    for uom_id in uom_ids:
        new_id = db.get_next_id('product_packaging')
        new_row = pd.DataFrame([{
            'ID': new_id, 'Product_ID': product_id, 'UOM_ID': uom_id, 'Is_Active': True
        }])
        pp_df = pd.concat([pp_df, new_row], ignore_index=True)
    db.save_sheet('product_packaging', pp_df)

def init_products():
    products_df = db.get_sheet('products')
    required_columns = [
        'ID', 'Name', 'Category_ID', 'Base_UOM_ID', 'Location_ID', 
        'Primary_Supplier_ID', 'Current_Stock', 'Min_Stock_Alert', 
        'Selling_Price', 'Purchase_Cost', 'Color', 'Is_Active', 'Notes', 'Created'
    ]
    for col in required_columns:
        if col not in products_df.columns:
            products_df[col] = None
    db.save_sheet('products', products_df)
    return products_df

def get_child_categories(parent_id, categories_df):
    """Get all child categories of a parent"""
    return categories_df[categories_df['Parent_ID'] == parent_id].sort_values('Name')

def get_products_by_category(category_id, products_df):
    """Get all products in a category"""
    return products_df[products_df['Category_ID'] == category_id].sort_values('Name')

def get_all_descendant_categories(category_id, categories_df):
    """Get all descendant category IDs recursively"""
    descendants = []
    children = categories_df[categories_df['Parent_ID'] == category_id]
    for _, child in children.iterrows():
        descendants.append(child['ID'])
        descendants.extend(get_all_descendant_categories(child['ID'], categories_df))
    return descendants

def get_all_products_in_tree(category_id, categories_df, products_df):
    """Get all products in category and all sub-categories"""
    all_cats = get_all_descendant_categories(category_id, categories_df)
    all_cats.append(category_id)
    return products_df[products_df['Category_ID'].isin(all_cats)].sort_values('Name')

# Show success message if product was just added
if st.session_state.product_added:
    st.balloons()
    st.success(f"✅ Product '{st.session_state.last_added_product}' added successfully!")
    st.session_state.product_added = False
    st.rerun()

# ========== ADD/EDIT FORM (shown conditionally) ==========
if st.session_state.show_add_form or st.session_state.edit_product_id:
    
    # Cancel button at top
    if st.button("← Back to Product List", use_container_width=True):
        st.session_state.show_add_form = False
        st.session_state.edit_product_id = None
        st.rerun()
    
    st.markdown("---")
    
    if st.session_state.edit_product_id:
        st.subheader("✏️ Edit Product")
        products_df = init_products()
        product = products_df[products_df['ID'] == st.session_state.edit_product_id].iloc[0]
        is_edit = True
    else:
        st.subheader("➕ Add New Product")
        is_edit = False
    
    uom_df = db.get_sheet('uom')
    categories_df = db.get_sheet('categories')
    locations_df = db.get_sheet('locations')
    colaborators_df = db.get_sheet('colaborators')
    
    if uom_df.empty:
        st.error("No UOMs found! Please add Base Units in UOM module first.")
    elif categories_df.empty or len(categories_df) <= 1:
        st.error("No categories found! Please add categories first.")
    elif locations_df.empty or len(locations_df) <= 1:
        st.error("No storage locations found! Please add locations first.")
    else:
        with st.form(key="product_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                if is_edit:
                    name = st.text_input("Product Name *", value=safe_str(product['Name']))
                else:
                    name = st.text_input("Product Name *", placeholder="Example: PORTLAND CEMENT")
                
                sub_categories = categories_df[categories_df['Parent_ID'].notna()]
                if not sub_categories.empty:
                    category_options = {get_category_path(cat['ID'], categories_df): cat['ID'] for _, cat in sub_categories.iterrows()}
                    if is_edit:
                        current_cat_path = get_category_path(product['Category_ID'], categories_df)
                        default_index = list(category_options.keys()).index(current_cat_path) if current_cat_path in category_options.keys() else 0
                        category_selected = st.selectbox("Category *", list(category_options.keys()), index=default_index)
                    else:
                        category_selected = st.selectbox("Category *", list(category_options.keys()))
                    category_id = category_options[category_selected]
                else:
                    category_id = None
                
                base_uoms = uom_df[uom_df['Type'] == 'BASE']
                uom_options = {row['Name']: row['ID'] for _, row in base_uoms.iterrows()}
                if is_edit:
                    current_uom = get_uom_name(product['Base_UOM_ID'])
                    default_index = list(uom_options.keys()).index(current_uom) if current_uom in uom_options.keys() else 0
                    uom_selected = st.selectbox("Base Unit of Measure *", list(uom_options.keys()), index=default_index)
                else:
                    uom_selected = st.selectbox("Base Unit of Measure *", list(uom_options.keys()))
                base_uom_id = uom_options[uom_selected]
                base_uom_name = uom_selected
                
                if is_edit:
                    color = st.text_input("Color/Variation (optional)", value=safe_str(product['Color']))
                else:
                    color = st.text_input("Color/Variation (optional)", placeholder="Example: RED, BLUE, 5KG")
            
            with col2:
                storage_locs = locations_df[locations_df['Can_Hold_Stock'] == True]
                loc_options = {row['Name']: row['ID'] for _, row in storage_locs.iterrows()}
                if is_edit:
                    current_loc = get_location_name(product['Location_ID'])
                    default_index = list(loc_options.keys()).index(current_loc) if current_loc in loc_options.keys() else 0
                    loc_selected = st.selectbox("Default Storage Location *", list(loc_options.keys()), index=default_index)
                else:
                    loc_selected = st.selectbox("Default Storage Location *", list(loc_options.keys()))
                location_id = loc_options[loc_selected]
                
                suppliers = colaborators_df[colaborators_df['Type'] == 'SUPPLIER']
                supplier_options = {row['Name']: row['ID'] for _, row in suppliers.iterrows()} if not suppliers.empty else {}
                supplier_list = ["None"] + list(supplier_options.keys())
                
                if is_edit:
                    current_supplier = get_colaborator_name(product['Primary_Supplier_ID']) if product['Primary_Supplier_ID'] else "None"
                    default_index = supplier_list.index(current_supplier) if current_supplier in supplier_list else 0
                    supplier_selected = st.selectbox("Primary Supplier", supplier_list, index=default_index)
                else:
                    supplier_selected = st.selectbox("Primary Supplier", supplier_list)
                supplier_id = supplier_options[supplier_selected] if supplier_selected != "None" else None
            
            col3, col4 = st.columns(2)
            with col3:
                if is_edit:
                    current_stock = st.number_input("Current Stock (in base units)", min_value=0.0, step=1.0, value=safe_float(product['Current_Stock']))
                else:
                    current_stock = st.number_input("Initial Stock (in base units)", min_value=0.0, step=1.0, value=0.0)
                
                if is_edit:
                    min_alert = st.number_input("Minimum Stock Alert", min_value=0.0, step=1.0, value=safe_float(product['Min_Stock_Alert']))
                else:
                    min_alert = st.number_input("Minimum Stock Alert", min_value=0.0, step=1.0, value=10.0)
            
            with col4:
                if is_edit:
                    selling_price = st.number_input("Base Selling Price (per base unit) *", min_value=0.0, step=100.0, value=safe_float(product['Selling_Price']))
                else:
                    selling_price = st.number_input("Base Selling Price (per base unit) *", min_value=0.0, step=100.0, value=0.0)
                
                if is_edit:
                    purchase_cost = st.number_input("Base Purchase Cost (per base unit)", min_value=0.0, step=100.0, value=safe_float(product['Purchase_Cost']))
                else:
                    purchase_cost = st.number_input("Base Purchase Cost (per base unit)", min_value=0.0, step=100.0, value=0.0)
            
            st.markdown("---")
            st.markdown("### Packaging Options")
            
            if is_edit:
                current_packaging = get_product_packaging(st.session_state.edit_product_id)
            else:
                current_packaging = []
            
            packaging_units = get_packaging_units(base_uom_id)
            selected_packaging = []
            if not packaging_units.empty:
                pkg_cols = st.columns(2)
                for idx, (_, pkg) in enumerate(packaging_units.iterrows()):
                    with pkg_cols[idx % 2]:
                        is_checked = pkg['ID'] in current_packaging
                        checked = st.checkbox(f"{pkg['Name']} = {pkg['Factor']:.0f} {base_uom_name}", value=is_checked, key=f"pkg_{pkg['ID']}")
                        if checked:
                            selected_packaging.append(pkg['ID'])
            else:
                st.info("No packaging units available. Add packaging units in the UOM module first.")
            
            if is_edit:
                notes = st.text_area("Notes", value=safe_str(product['Notes']))
                is_active = st.checkbox("Active", value=bool(product['Is_Active']))
            else:
                notes = st.text_area("Notes")
                is_active = st.checkbox("Active", value=True)
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.form_submit_button("Cancel", use_container_width=True):
                    st.session_state.show_add_form = False
                    st.session_state.edit_product_id = None
                    st.rerun()
            with col_btn2:
                if st.form_submit_button("Save Product", type="primary", use_container_width=True):
                    if not name:
                        st.error("Product name is required!")
                    elif not category_id:
                        st.error("Please select a category!")
                    elif not base_uom_id:
                        st.error("Please select a base unit!")
                    elif not location_id:
                        st.error("Please select a storage location!")
                    elif selling_price <= 0:
                        st.error("Selling price must be greater than 0!")
                    else:
                        products_df = init_products()
                        
                        if is_edit:
                            products_df.loc[products_df['ID'] == st.session_state.edit_product_id, 'Name'] = name.strip().upper()
                            products_df.loc[products_df['ID'] == st.session_state.edit_product_id, 'Category_ID'] = category_id
                            products_df.loc[products_df['ID'] == st.session_state.edit_product_id, 'Base_UOM_ID'] = base_uom_id
                            products_df.loc[products_df['ID'] == st.session_state.edit_product_id, 'Location_ID'] = location_id
                            products_df.loc[products_df['ID'] == st.session_state.edit_product_id, 'Primary_Supplier_ID'] = supplier_id
                            products_df.loc[products_df['ID'] == st.session_state.edit_product_id, 'Current_Stock'] = float(current_stock)
                            products_df.loc[products_df['ID'] == st.session_state.edit_product_id, 'Min_Stock_Alert'] = float(min_alert)
                            products_df.loc[products_df['ID'] == st.session_state.edit_product_id, 'Selling_Price'] = float(selling_price)
                            products_df.loc[products_df['ID'] == st.session_state.edit_product_id, 'Purchase_Cost'] = float(purchase_cost)
                            products_df.loc[products_df['ID'] == st.session_state.edit_product_id, 'Color'] = color.strip().upper() if color else None
                            products_df.loc[products_df['ID'] == st.session_state.edit_product_id, 'Notes'] = notes if notes else None
                            products_df.loc[products_df['ID'] == st.session_state.edit_product_id, 'Is_Active'] = is_active
                            db.save_sheet('products', products_df)
                            save_product_packaging(st.session_state.edit_product_id, selected_packaging)
                            
                            st.session_state.edit_product_id = None
                            st.success(f"Product '{name}' updated successfully!")
                            st.rerun()
                        else:
                            new_id = db.get_next_id('products')
                            new_row = pd.DataFrame([{
                                'ID': new_id, 'Name': name.strip().upper(), 'Category_ID': category_id,
                                'Base_UOM_ID': base_uom_id, 'Location_ID': location_id, 'Primary_Supplier_ID': supplier_id,
                                'Current_Stock': float(current_stock), 'Min_Stock_Alert': float(min_alert),
                                'Selling_Price': float(selling_price), 'Purchase_Cost': float(purchase_cost),
                                'Color': color.strip().upper() if color else None, 'Is_Active': is_active,
                                'Notes': notes if notes else None, 'Created': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            }])
                            products_df = pd.concat([products_df, new_row], ignore_index=True)
                            db.save_sheet('products', products_df)
                            save_product_packaging(new_id, selected_packaging)
                            
                            st.session_state.show_add_form = False
                            st.session_state.product_added = True
                            st.session_state.last_added_product = name
                            st.rerun()
    
    st.stop()

# ========== MAIN PRODUCT LIST VIEW ==========

# View Mode Toggle Buttons
col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 4])

with col_btn1:
    if st.button("📋 List View", type="primary" if st.session_state.view_mode == "list" else "secondary", use_container_width=True):
        st.session_state.view_mode = "list"
        st.session_state.selected_category = None
        st.rerun()

with col_btn2:
    if st.button("📁 Category View", type="primary" if st.session_state.view_mode == "category" else "secondary", use_container_width=True):
        st.session_state.view_mode = "category"
        st.session_state.selected_category = None
        st.rerun()

with col_btn3:
    if st.button("➕ Add New Product", use_container_width=True):
        st.session_state.show_add_form = True
        st.rerun()

st.markdown("---")

# ========== LIST VIEW ==========
if st.session_state.view_mode == "list":
    st.subheader("Product List (A-Z)")
    
    products_df = init_products()
    categories_df = db.get_sheet('categories')
    locations_df = db.get_sheet('locations')
    
    if products_df.empty:
        st.info("No products yet. Click 'Add New Product' to get started.")
    else:
        # Filters
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            cat_list = ["ALL"] + categories_df[categories_df['Parent_ID'].notna()]['Name'].tolist() if not categories_df.empty else ["ALL"]
            category_filter = st.selectbox("Category", cat_list)
        with col2:
            loc_list = ["ALL"] + locations_df[locations_df['Can_Hold_Stock'] == True]['Name'].tolist() if not locations_df.empty else ["ALL"]
            location_filter = st.selectbox("Location", loc_list)
        with col3:
            stock_filter = st.selectbox("Stock Status", ["ALL", "In Stock", "Out of Stock", "Low Stock"])
        with col4:
            search = st.text_input("Search", placeholder="Product name...")
        
        filtered_df = products_df.copy()
        if category_filter != "ALL":
            cat_ids = categories_df[categories_df['Name'] == category_filter]['ID'].tolist()
            if cat_ids:
                filtered_df = filtered_df[filtered_df['Category_ID'] == cat_ids[0]]
        if location_filter != "ALL":
            loc_ids = locations_df[locations_df['Name'] == location_filter]['ID'].tolist()
            if loc_ids:
                filtered_df = filtered_df[filtered_df['Location_ID'] == loc_ids[0]]
        if stock_filter == "In Stock":
            filtered_df = filtered_df[filtered_df['Current_Stock'].apply(safe_float) > 0]
        elif stock_filter == "Out of Stock":
            filtered_df = filtered_df[filtered_df['Current_Stock'].apply(safe_float) == 0]
        elif stock_filter == "Low Stock":
            filtered_df = filtered_df[filtered_df['Current_Stock'].apply(safe_float) < filtered_df['Min_Stock_Alert'].apply(safe_float)]
        if search:
            filtered_df = filtered_df[filtered_df['Name'].str.contains(search, case=False, na=False)]
        
        # Sort alphabetically A-Z
        filtered_df = filtered_df.sort_values('Name')
        
        if not filtered_df.empty:
            for _, prod in filtered_df.iterrows():
                stock = safe_float(prod['Current_Stock'])
                min_stock = safe_float(prod['Min_Stock_Alert'])
                base_uom = get_uom_name(prod['Base_UOM_ID'])
                
                if stock <= 0:
                    stock_status = "🔴 OUT OF STOCK"
                elif stock < min_stock:
                    stock_status = "🟡 LOW STOCK"
                else:
                    stock_status = "🟢 IN STOCK"
                
                with st.expander(f"📦 {prod['Name']} - {stock_status} - {stock:,.0f} {base_uom}", expanded=False):
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        st.markdown(f"**ID:** {safe_int(prod['ID'])}")
                        st.markdown(f"**Category:** {get_category_path(prod['Category_ID'], categories_df)}")
                        st.markdown(f"**Location:** {get_location_name(prod['Location_ID'])}")
                        st.markdown(f"**Base Unit:** {base_uom}")
                        if prod['Color']:
                            st.markdown(f"**Color:** {prod['Color']}")
                    
                    with col2:
                        st.markdown(f"**Selling Price:** {safe_float(prod['Selling_Price']):,.0f} MGA per {base_uom}")
                        st.markdown(f"**Purchase Cost:** {safe_float(prod['Purchase_Cost']):,.0f} MGA per {base_uom}")
                        st.markdown(f"**Min Stock Alert:** {safe_float(prod['Min_Stock_Alert']):,.0f} {base_uom}")
                        st.markdown(f"**Supplier:** {get_colaborator_name(prod['Primary_Supplier_ID'])}")
                    
                    with col3:
                        if st.button(f"✏️ Edit", key=f"edit_{prod['ID']}"):
                            st.session_state.edit_product_id = prod['ID']
                            st.rerun()
                    
                    packaging_ids = get_product_packaging(prod['ID'])
                    if packaging_ids:
                        st.markdown("---")
                        st.markdown("**Packaging Options Available:**")
                        pkg_text = ", ".join([f"1 {get_uom_name(pkg_id)} = {get_uom_factor(pkg_id):,.0f} {base_uom}" for pkg_id in packaging_ids])
                        st.caption(pkg_text)
        else:
            st.info("No products match the filters")

# ========== CATEGORY VIEW ==========
else:
    st.subheader("Products by Category")
    
    products_df = init_products()
    categories_df = db.get_sheet('categories')
    locations_df = db.get_sheet('locations')
    
    if products_df.empty:
        st.info("No products yet. Click 'Add New Product' to get started.")
    else:
        # Get root categories (Parent_ID is None and ID != 1)
        root_categories = categories_df[(categories_df['Parent_ID'].isna()) & (categories_df['ID'] != 1)].sort_values('Name')
        
        if root_categories.empty:
            st.info("No categories found. Please add categories first.")
        else:
            # Display each root category with its products
            for _, root_cat in root_categories.iterrows():
                # Get all products in this category tree
                products_in_tree = get_all_products_in_tree(root_cat['ID'], categories_df, products_df)
                
                if not products_in_tree.empty:
                    with st.expander(f"📁 {root_cat['Name']} ({len(products_in_tree)} products)", expanded=False):
                        # Get child categories
                        child_categories = get_child_categories(root_cat['ID'], categories_df)
                        
                        if not child_categories.empty:
                            # Show products by sub-category
                            for _, child_cat in child_categories.iterrows():
                                cat_products = get_products_by_category(child_cat['ID'], products_df)
                                if not cat_products.empty:
                                    st.markdown(f"**└─ {child_cat['Name']}** ({len(cat_products)} products)")
                                    for _, prod in cat_products.iterrows():
                                        stock = safe_float(prod['Current_Stock'])
                                        base_uom = get_uom_name(prod['Base_UOM_ID'])
                                        col1, col2 = st.columns([3, 1])
                                        with col1:
                                            st.write(f"   • **{prod['Name']}** - {stock:,.0f} {base_uom}")
                                        with col2:
                                            if st.button(f"Edit", key=f"cat_edit_{prod['ID']}"):
                                                st.session_state.edit_product_id = prod['ID']
                                                st.rerun()
                                    st.markdown("")
                        else:
                            # No child categories, show products directly under root
                            for _, prod in products_in_tree.iterrows():
                                stock = safe_float(prod['Current_Stock'])
                                base_uom = get_uom_name(prod['Base_UOM_ID'])
                                col1, col2 = st.columns([3, 1])
                                with col1:
                                    st.write(f"   • **{prod['Name']}** - {stock:,.0f} {base_uom}")
                                with col2:
                                    if st.button(f"Edit", key=f"root_edit_{prod['ID']}"):
                                        st.session_state.edit_product_id = prod['ID']
                                        st.rerun()
                else:
                    # Root category has no products, but might have sub-categories with products
                    child_categories = get_child_categories(root_cat['ID'], categories_df)
                    if not child_categories.empty:
                        has_products = False
                        for _, child_cat in child_categories.iterrows():
                            cat_products = get_products_by_category(child_cat['ID'], products_df)
                            if not cat_products.empty:
                                has_products = True
                                break
                        
                        if has_products:
                            with st.expander(f"📁 {root_cat['Name']}", expanded=False):
                                for _, child_cat in child_categories.iterrows():
                                    cat_products = get_products_by_category(child_cat['ID'], products_df)
                                    if not cat_products.empty:
                                        st.markdown(f"**└─ {child_cat['Name']}** ({len(cat_products)} products)")
                                        for _, prod in cat_products.iterrows():
                                            stock = safe_float(prod['Current_Stock'])
                                            base_uom = get_uom_name(prod['Base_UOM_ID'])
                                            col1, col2 = st.columns([3, 1])
                                            with col1:
                                                st.write(f"   • **{prod['Name']}** - {stock:,.0f} {base_uom}")
                                            with col2:
                                                if st.button(f"Edit", key=f"child_edit_{prod['ID']}"):
                                                    st.session_state.edit_product_id = prod['ID']
                                                    st.rerun()
                                        st.markdown("")
        
        # Summary
        st.divider()
        total_products = len(products_df)
        st.caption(f"📊 Total Products: {total_products}")

st.divider()
st.caption("💡 Click 'List View' for alphabetical product list, or 'Category View' to browse by category.")