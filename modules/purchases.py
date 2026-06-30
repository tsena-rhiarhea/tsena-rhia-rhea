# modules/purchases.py - Purchase Order with Goods Receipt and Packaging
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

st.title("🛒 Purchase Order Management")
st.caption("Create purchase orders and receive goods with packaging options")

db = ExcelBackend()

# Initialize session state
if 'show_add_form' not in st.session_state:
    st.session_state.show_add_form = False
if 'show_receive_form' not in st.session_state:
    st.session_state.show_receive_form = False
if 'receive_po_id' not in st.session_state:
    st.session_state.receive_po_id = None
if 'purchase_added' not in st.session_state:
    st.session_state.purchase_added = False
if 'last_purchase_number' not in st.session_state:
    st.session_state.last_purchase_number = None
if 'cart' not in st.session_state:
    st.session_state.cart = []

def init_purchases():
    purchases_df = db.get_sheet('purchases')
    if purchases_df.empty:
        purchases_df = pd.DataFrame(columns=[
            'ID', 'PO_Number', 'Date', 'Supplier_ID', 'Supplier_Name',
            'Total_Amount', 'Status', 'Notes', 'Created_By', 'Created_At'
        ])
        db.save_sheet('purchases', purchases_df)
    return purchases_df

def init_purchase_items():
    items_df = db.get_sheet('purchase_items')
    if items_df.empty:
        items_df = pd.DataFrame(columns=[
            'ID', 'Purchase_ID', 'Product_ID', 'Product_Name', 'UOM_ID', 'UOM_Name',
            'Ordered_Quantity', 'Received_Quantity', 'Unit_Cost', 'Total_Cost'
        ])
        db.save_sheet('purchase_items', items_df)
    return items_df

def get_next_po_number():
    purchases_df = init_purchases()
    if purchases_df.empty:
        return "PO-0001"
    
    existing_nums = []
    for po in purchases_df['PO_Number']:
        try:
            num = int(po.split('-')[1])
            existing_nums.append(num)
        except:
            pass
    
    next_num = max(existing_nums) + 1 if existing_nums else 1
    return f"PO-{next_num:04d}"

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

def get_product_packaging_options(product_id):
    """Get all packaging options available for a product"""
    # Get product's base UOM
    products_df = db.get_sheet('products')
    product = products_df[products_df['ID'] == product_id]
    if product.empty:
        return pd.DataFrame()
    
    base_uom_id = product.iloc[0]['Base_UOM_ID']
    base_uom_name = get_uom_name(base_uom_id)
    
    # Get packaging units for this base UOM
    uom_df = db.get_sheet('uom')
    packaging = uom_df[(uom_df['Type'] == 'PACKAGING') & (uom_df['Base_Unit'] == base_uom_name)]
    
    # Check which packaging is enabled for this product
    product_packaging_df = db.get_sheet('product_packaging')
    enabled_packaging = product_packaging_df[product_packaging_df['Product_ID'] == product_id]['UOM_ID'].tolist()
    
    # Filter to only enabled packaging
    packaging = packaging[packaging['ID'].isin(enabled_packaging)]
    
    return packaging.sort_values('Factor', ascending=False)

def get_supplier_name(supplier_id):
    df = db.get_sheet('colaborators')
    result = df[df['ID'] == supplier_id]
    return result.iloc[0]['Name'] if not result.empty else "Unknown"

def add_to_cart(product_id, product_name, uom_id, uom_name, uom_factor, quantity, unit_cost):
    total_cost = quantity * unit_cost
    base_quantity = quantity * uom_factor  # Convert to base units for stock
    st.session_state.cart.append({
        'product_id': product_id,
        'product_name': product_name,
        'uom_id': uom_id,
        'uom_name': uom_name,
        'uom_factor': uom_factor,
        'quantity': quantity,
        'base_quantity': base_quantity,
        'unit_cost': unit_cost,
        'total_cost': total_cost
    })

def clear_cart():
    st.session_state.cart = []

def get_cart_total():
    return sum(item['total_cost'] for item in st.session_state.cart)

def save_purchase(supplier_id, supplier_name, notes):
    purchases_df = init_purchases()
    items_df = init_purchase_items()
    products_df = db.get_sheet('products')
    stock_movements_df = db.get_sheet('stock_movements')
    
    po_number = get_next_po_number()
    total_amount = get_cart_total()
    
    # Create purchase order
    new_po_id = db.get_next_id('purchases')
    new_po = pd.DataFrame([{
        'ID': new_po_id,
        'PO_Number': po_number,
        'Date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'Supplier_ID': supplier_id,
        'Supplier_Name': supplier_name,
        'Total_Amount': total_amount,
        'Status': 'PENDING',  # PENDING until goods received
        'Notes': notes,
        'Created_By': user['full_name'],
        'Created_At': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }])
    purchases_df = pd.concat([purchases_df, new_po], ignore_index=True)
    db.save_sheet('purchases', purchases_df)
    
    # Save items (ordered quantities)
    for item in st.session_state.cart:
        new_item_id = db.get_next_id('purchase_items')
        new_item = pd.DataFrame([{
            'ID': new_item_id,
            'Purchase_ID': new_po_id,
            'Product_ID': item['product_id'],
            'Product_Name': item['product_name'],
            'UOM_ID': item['uom_id'],
            'UOM_Name': item['uom_name'],
            'Ordered_Quantity': item['quantity'],
            'Received_Quantity': 0,
            'Unit_Cost': item['unit_cost'],
            'Total_Cost': item['total_cost']
        }])
        items_df = pd.concat([items_df, new_item], ignore_index=True)
    
    db.save_sheet('purchase_items', items_df)
    
    return po_number, new_po_id

def receive_goods(po_id, received_items):
    """Process goods receipt for a purchase order"""
    purchases_df = init_purchases()
    items_df = init_purchase_items()
    products_df = db.get_sheet('products')
    stock_movements_df = db.get_sheet('stock_movements')
    
    # Update purchase order status
    purchases_df.loc[purchases_df['ID'] == po_id, 'Status'] = 'RECEIVED'
    db.save_sheet('purchases', purchases_df)
    
    po_number = purchases_df[purchases_df['ID'] == po_id]['PO_Number'].iloc[0]
    supplier_name = purchases_df[purchases_df['ID'] == po_id]['Supplier_Name'].iloc[0]
    
    # Update received quantities and stock
    for item in received_items:
        item_id = item['item_id']
        received_qty = item['received_qty']
        
        # Update received quantity in purchase_items
        current_received = items_df.loc[items_df['ID'] == item_id, 'Received_Quantity'].iloc[0]
        items_df.loc[items_df['ID'] == item_id, 'Received_Quantity'] = current_received + received_qty
        db.save_sheet('purchase_items', items_df)
        
        # Get item details
        purchase_item = items_df[items_df['ID'] == item_id].iloc[0]
        product_id = purchase_item['Product_ID']
        uom_id = purchase_item['UOM_ID']
        uom_factor = get_uom_factor(uom_id)
        unit_cost = purchase_item['Unit_Cost']
        
        # Convert to base units
        base_quantity = received_qty * uom_factor
        
        # Update product stock
        current_stock = products_df.loc[products_df['ID'] == product_id, 'Current_Stock'].iloc[0]
        products_df.loc[products_df['ID'] == product_id, 'Current_Stock'] = current_stock + base_quantity
        
        # Update purchase cost (weighted average)
        current_cost = products_df.loc[products_df['ID'] == product_id, 'Purchase_Cost'].iloc[0]
        if current_cost and current_cost > 0:
            # Weighted average
            total_value = (current_stock * current_cost) + (base_quantity * unit_cost)
            new_stock = current_stock + base_quantity
            new_avg_cost = total_value / new_stock if new_stock > 0 else unit_cost
            products_df.loc[products_df['ID'] == product_id, 'Purchase_Cost'] = new_avg_cost
        else:
            products_df.loc[products_df['ID'] == product_id, 'Purchase_Cost'] = unit_cost
        
        db.save_sheet('products', products_df)
        
        # Record stock movement
        new_move_id = db.get_next_id('stock_movements')
        new_move = pd.DataFrame([{
            'ID': new_move_id,
            'Date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'Type': 'PURCHASE_RECEIPT',
            'Product_ID': product_id,
            'From_Location': None,
            'To_Location': None,
            'Quantity': base_quantity,
            'UOM_ID': uom_id,
            'Reference': po_number,
            'User': user['full_name'],
            'Notes': f"Goods receipt for PO {po_number} from {supplier_name}"
        }])
        stock_movements_df = pd.concat([stock_movements_df, new_move], ignore_index=True)
        db.save_sheet('stock_movements', stock_movements_df)
    
    return po_number

# Show success message
if st.session_state.purchase_added:
    st.balloons()
    st.success(f"✅ Purchase Order '{st.session_state.last_purchase_number}' created successfully!")
    st.session_state.purchase_added = False
    st.rerun()

# ========== ADD PURCHASE FORM ==========
if st.session_state.show_add_form:
    
    if st.button("← Back to Purchase List", use_container_width=True):
        st.session_state.show_add_form = False
        clear_cart()
        st.rerun()
    
    st.markdown("---")
    st.subheader("➕ Create New Purchase Order")
    
    # Step 1: Select Supplier
    colaborators_df = db.get_sheet('colaborators')
    suppliers = colaborators_df[colaborators_df['Type'] == 'SUPPLIER']
    
    if suppliers.empty:
        st.error("No suppliers found. Please add suppliers in Connections module first.")
        st.stop()
    
    supplier_options = {row['Name']: row['ID'] for _, row in suppliers.iterrows()}
    selected_supplier = st.selectbox("Select Supplier", list(supplier_options.keys()))
    supplier_id = supplier_options[selected_supplier]
    supplier_name = selected_supplier
    
    st.markdown("---")
    
    # Step 2: Add Items to Cart
    st.subheader("Add Items")
    
    products_df = db.get_sheet('products')
    products_df = products_df[products_df['Is_Active'] == True]
    
    if products_df.empty:
        st.error("No products found. Please add products first.")
        st.stop()
    
    col1, col2, col3, col4 = st.columns([2, 1.5, 1, 1])
    
    with col1:
        product_options = {row['Name']: row['ID'] for _, row in products_df.iterrows()}
        selected_product = st.selectbox("Product", list(product_options.keys()), key="add_product")
        product_id = product_options[selected_product]
        product_name = selected_product
    
    with col2:
        # Get packaging options for this product
        packaging_options = get_product_packaging_options(product_id)
        
        # Add base unit as option
        base_uom_id = products_df[products_df['ID'] == product_id]['Base_UOM_ID'].iloc[0]
        base_uom_name = get_uom_name(base_uom_id)
        
        uom_options_list = [{"name": base_uom_name, "id": base_uom_id, "factor": 1}]
        for _, pkg in packaging_options.iterrows():
            uom_options_list.append({"name": pkg['Name'], "id": pkg['ID'], "factor": pkg['Factor']})
        
        uom_display_names = [u["name"] for u in uom_options_list]
        selected_uom_display = st.selectbox("UOM", uom_display_names, key="uom_select")
        
        selected_uom = next(u for u in uom_options_list if u["name"] == selected_uom_display)
        uom_id = selected_uom["id"]
        uom_name = selected_uom["name"]
        uom_factor = selected_uom["factor"]
        
        # Show conversion info
        if uom_factor != 1:
            st.caption(f"1 {uom_name} = {uom_factor:.0f} {base_uom_name}")
    
    with col3:
        quantity = st.number_input("Quantity", min_value=0.1, step=1.0, value=1.0, key="qty")
        # Show base quantity equivalent
        base_qty = quantity * uom_factor
        st.caption(f"= {base_qty:.0f} {base_uom_name}")
    
    with col4:
        unit_cost = st.number_input("Unit Cost (MGA)", min_value=0.0, step=100.0, value=0.0, key="unit_cost")
        if uom_factor != 1 and unit_cost > 0:
            base_cost = unit_cost / uom_factor
            st.caption(f"= {base_cost:.2f} MGA/{base_uom_name}")
    
    if st.button("➕ Add to Cart", use_container_width=True):
        if quantity > 0 and unit_cost > 0:
            add_to_cart(product_id, product_name, uom_id, uom_name, uom_factor, quantity, unit_cost)
            st.rerun()
        else:
            st.error("Please enter quantity and unit cost")
    
    st.markdown("---")
    
    # Step 3: Cart Display
    st.subheader("Cart Items")
    
    if st.session_state.cart:
        cart_data = []
        for item in st.session_state.cart:
            cart_data.append({
                'Product': item['product_name'],
                'UOM': item['uom_name'],
                'Quantity': f"{item['quantity']:,.0f}",
                'Base Qty': f"{item['base_quantity']:,.0f}",
                'Unit Cost': f"{item['unit_cost']:,.0f} MGA",
                'Total': f"{item['total_cost']:,.0f} MGA"
            })
        
        st.dataframe(pd.DataFrame(cart_data), width='stretch', hide_index=True)
        
        st.metric("Total Amount", f"{get_cart_total():,.0f} MGA")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Clear Cart", use_container_width=True):
                clear_cart()
                st.rerun()
        
        with col2:
            notes = st.text_area("Purchase Notes", placeholder="Order reference, delivery notes, etc.")
            
            if st.button("✅ Create Purchase Order", type="primary", use_container_width=True):
                po_number, po_id = save_purchase(supplier_id, supplier_name, notes)
                clear_cart()
                st.session_state.show_add_form = False
                st.session_state.purchase_added = True
                st.session_state.last_purchase_number = po_number
                st.rerun()
    else:
        st.info("Cart is empty. Add items to continue.")
    
    st.stop()

# ========== GOODS RECEIPT FORM ==========
if st.session_state.show_receive_form and st.session_state.receive_po_id:
    
    if st.button("← Back to Purchase List", use_container_width=True):
        st.session_state.show_receive_form = False
        st.session_state.receive_po_id = None
        st.rerun()
    
    st.markdown("---")
    st.subheader("📦 Receive Goods")
    
    purchases_df = init_purchases()
    po = purchases_df[purchases_df['ID'] == st.session_state.receive_po_id].iloc[0]
    
    st.info(f"**PO Number:** {po['PO_Number']} | **Supplier:** {po['Supplier_Name']}")
    
    items_df = init_purchase_items()
    po_items = items_df[items_df['Purchase_ID'] == st.session_state.receive_po_id]
    
    if po_items.empty:
        st.error("No items found for this purchase order.")
        st.stop()
    
    st.subheader("Items to Receive")
    
    received_items = []
    
    for _, item in po_items.iterrows():
        remaining = item['Ordered_Quantity'] - item['Received_Quantity']
        
        if remaining > 0:
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            
            with col1:
                st.write(f"**{item['Product_Name']**")
                st.caption(f"UOM: {item['UOM_Name']}")
            
            with col2:
                st.write(f"Ordered: {item['Ordered_Quantity']:,.0f}")
                st.write(f"Already Received: {item['Received_Quantity']:,.0f}")
            
            with col3:
                receive_qty = st.number_input(
                    "Qty to Receive",
                    min_value=0.0,
                    max_value=float(remaining),
                    step=1.0,
                    value=float(remaining),
                    key=f"receive_{item['ID']}"
                )
            
            with col4:
                st.write(f"Remaining: {remaining:,.0f}")
            
            if receive_qty > 0:
                received_items.append({
                    'item_id': item['ID'],
                    'received_qty': receive_qty
                })
            
            st.markdown("---")
    
    if received_items:
        if st.button("✅ Confirm Receipt", type="primary", use_container_width=True):
            po_number = receive_goods(st.session_state.receive_po_id, received_items)
            st.session_state.show_receive_form = False
            st.session_state.receive_po_id = None
            st.balloons()
            st.success(f"✅ Goods received for PO {po_number}!")
            st.rerun()
    else:
        st.warning("No items selected for receipt. All items may have been fully received.")
        if st.button("Cancel", use_container_width=True):
            st.session_state.show_receive_form = False
            st.session_state.receive_po_id = None
            st.rerun()
    
    st.stop()

# ========== MAIN PURCHASE LIST VIEW ==========

col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 4])
with col_btn1:
    if st.button("➕ New Purchase", type="primary", use_container_width=True):
        st.session_state.show_add_form = True
        clear_cart()
        st.rerun()

st.markdown("---")
st.subheader("Purchase Order History")

purchases_df = init_purchases()

if purchases_df.empty:
    st.info("No purchase orders yet. Click 'New Purchase' to get started.")
else:
    # Sort by date descending (newest first)
    purchases_df = purchases_df.sort_values('Date', ascending=False)
    
    # Filters
    col1, col2 = st.columns(2)
    with col1:
        status_filter = st.selectbox("Status", ["ALL", "PENDING", "RECEIVED", "PARTIAL", "CANCELLED"])
    with col2:
        search = st.text_input("Search", placeholder="PO Number or Supplier...")
    
    filtered_df = purchases_df.copy()
    if status_filter != "ALL":
        filtered_df = filtered_df[filtered_df['Status'] == status_filter]
    if search:
        filtered_df = filtered_df[
            filtered_df['PO_Number'].str.contains(search, case=False, na=False) |
            filtered_df['Supplier_Name'].str.contains(search, case=False, na=False)
        ]
    
    items_df = init_purchase_items()
    
    for _, po in filtered_df.iterrows():
        po_items = items_df[items_df['Purchase_ID'] == po['ID']]
        total_ordered = po_items['Ordered_Quantity'].sum() if not po_items.empty else 0
        total_received = po_items['Received_Quantity'].sum() if not po_items.empty else 0
        
        # Determine display status
        if po['Status'] == 'RECEIVED':
            status_display = "✅ RECEIVED"
        elif total_received > 0 and total_received < total_ordered:
            status_display = "🟡 PARTIAL"
            # Update status in database
            if po['Status'] != 'PARTIAL':
                purchases_df.loc[purchases_df['ID'] == po['ID'], 'Status'] = 'PARTIAL'
                db.save_sheet('purchases', purchases_df)
        elif total_received == 0:
            status_display = "⏳ PENDING"
        else:
            status_display = po['Status']
        
        with st.expander(f"📄 {po['PO_Number']} - {po['Supplier_Name']} - {po['Date'][:10]} - {po['Total_Amount']:,.0f} MGA - {status_display}", expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**PO Number:** {po['PO_Number']}")
                st.write(f"**Supplier:** {po['Supplier_Name']}")
                st.write(f"**Date:** {po['Date']}")
            with col2:
                st.write(f"**Total Amount:** {po['Total_Amount']:,.0f} MGA")
                st.write(f"**Created By:** {po['Created_By']}")
                st.write(f"**Status:** {status_display}")
            with col3:
                st.write(f"**Notes:** {po['Notes'] if po['Notes'] else '-'}")
                if total_ordered > 0:
                    st.write(f"**Receipt Progress:** {total_received:,.0f} / {total_ordered:,.0f}")
            
            # Show items
            if not po_items.empty:
                st.markdown("**Items Ordered:**")
                item_data = []
                for _, item in po_items.iterrows():
                    remaining = item['Ordered_Quantity'] - item['Received_Quantity']
                    status = "✅" if remaining == 0 else f"⏳ {remaining:,.0f} left"
                    item_data.append({
                        'Product': item['Product_Name'],
                        'UOM': item['UOM_Name'],
                        'Ordered': f"{item['Ordered_Quantity']:,.0f}",
                        'Received': f"{item['Received_Quantity']:,.0f}",
                        'Unit Cost': f"{item['Unit_Cost']:,.0f} MGA",
                        'Total': f"{item['Total_Cost']:,.0f} MGA",
                        'Status': status
                    })
                st.dataframe(pd.DataFrame(item_data), width='stretch', hide_index=True)
            
            # Receive goods button (only if not fully received)
            total_remaining = (po_items['Ordered_Quantity'] - po_items['Received_Quantity']).sum()
            if total_remaining > 0:
                if st.button(f"📦 Receive Goods", key=f"receive_{po['ID']}"):
                    st.session_state.show_receive_form = True
                    st.session_state.receive_po_id = po['ID']
                    st.rerun()

st.divider()
st.caption("💡 Create purchase orders with packaging options. Receive goods partially or fully to update stock.")