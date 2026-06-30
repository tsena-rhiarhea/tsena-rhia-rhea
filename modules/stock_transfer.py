# pages/6_Stock_Transfer.py
import streamlit as st
import pandas as pd
from datetime import datetime
import sys
from excel_backend import ExcelBackend
from auth import has_access, get_current_user

user = get_current_user()
if not user:
    st.error("Please login first")
    st.stop()

if not has_access('SUPERVISOR'):
    st.error("Access denied. Supervisor access required.")
    st.stop()

st.title("🔄 Stock Transfer Management")
st.caption("Intelligent stock transfers between locations")

db = ExcelBackend()

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

def get_location_name(location_id):
    if pd.isna(location_id) or location_id is None:
        return "Unknown"
    df = db.get_sheet('locations')
    result = df[df['ID'] == location_id]
    return result.iloc[0]['Name'] if not result.empty else "Unknown"

def get_product_name(product_id):
    df = db.get_sheet('products')
    result = df[df['ID'] == product_id]
    return result.iloc[0]['Name'] if not result.empty else "Unknown"

def get_current_stock_breakdown(product_id, location_id):
    breakdown_df = db.get_sheet('packaging_breakdown')
    result = breakdown_df[(breakdown_df['Product_ID'] == product_id) & (breakdown_df['Location_ID'] == location_id)]
    if result.empty:
        return {'full_pallets': 0, 'full_pqt': 0, 'partial_pqt': 0, 'loose_pc': 0, 'total_pc': 0}
    row = result.iloc[0]
    uom_id = row.get('UOM_ID', None)
    uom_name = get_uom_name(uom_id) if uom_id else "PC"
    full = safe_int(row.get('Full_Units', 0))
    partial = safe_int(row.get('Partial_Units', 0))
    loose = safe_int(row.get('Loose_Pieces', 0))
    if uom_name == 'PALLET':
        return {'full_pallets': full, 'full_pqt': 0, 'partial_pqt': 0, 'loose_pc': loose, 'total_pc': (full * 480) + loose}
    elif uom_name == 'PQT':
        return {'full_pallets': 0, 'full_pqt': full, 'partial_pqt': partial, 'loose_pc': loose, 'total_pc': (full * 24) + (partial * 24) + loose}
    else:
        return {'full_pallets': 0, 'full_pqt': 0, 'partial_pqt': 0, 'loose_pc': full + partial + loose, 'total_pc': full + partial + loose}

def get_all_locations_stock(product_id):
    locations_df = db.get_sheet('locations')
    storage_locs = locations_df[locations_df['Can_Hold_Stock'] == True]
    stock_data = []
    for _, loc in storage_locs.iterrows():
        breakdown = get_current_stock_breakdown(product_id, loc['ID'])
        if breakdown['total_pc'] > 0:
            stock_data.append({
                'location_id': loc['ID'], 'location_name': loc['Name'],
                'full_pallets': breakdown['full_pallets'], 'full_pqt': breakdown['full_pqt'],
                'partial_pqt': breakdown['partial_pqt'], 'loose_pc': breakdown['loose_pc'],
                'total_pc': breakdown['total_pc']
            })
    return stock_data

def check_transfer_needed(product_id, needed_pc, target_location_id):
    target_stock = get_current_stock_breakdown(product_id, target_location_id)
    if target_stock['total_pc'] >= needed_pc:
        return {'needed': False, 'message': f"Target location has sufficient stock: {target_stock['total_pc']} PC"}
    shortage = needed_pc - target_stock['total_pc']
    all_stock = get_all_locations_stock(product_id)
    other_locations = [s for s in all_stock if s['location_id'] != target_location_id]
    if not other_locations:
        return {'needed': False, 'message': f"Insufficient stock across all locations. Shortage: {shortage} PC"}
    return {'needed': True, 'shortage': shortage, 'available_locations': other_locations}

def calculate_transfer_plan(product_id, needed_pc, target_location_id):
    check = check_transfer_needed(product_id, needed_pc, target_location_id)
    if not check['needed']:
        return check
    shortage = check['shortage']
    available = check['available_locations']
    transfers = []
    for loc in available:
        if shortage <= 0:
            break
        if loc['full_pallets'] > 0 and shortage >= 480:
            take_pallets = min(loc['full_pallets'], shortage // 480)
            if take_pallets > 0:
                transfers.append({'from_location_id': loc['location_id'], 'from_location_name': loc['location_name'], 'packaging': 'PALLET', 'quantity': take_pallets, 'pc_value': take_pallets * 480})
                shortage -= take_pallets * 480
        if shortage > 0 and loc['full_pqt'] > 0 and shortage >= 24:
            take_pqt = min(loc['full_pqt'], shortage // 24)
            if take_pqt > 0:
                transfers.append({'from_location_id': loc['location_id'], 'from_location_name': loc['location_name'], 'packaging': 'PQT', 'quantity': take_pqt, 'pc_value': take_pqt * 24})
                shortage -= take_pqt * 24
        if shortage > 0 and loc['partial_pqt'] > 0:
            take_partial = min(loc['partial_pqt'], 1)
            if take_partial > 0:
                transfers.append({'from_location_id': loc['location_id'], 'from_location_name': loc['location_name'], 'packaging': 'PARTIAL_PQT', 'quantity': take_partial, 'pc_value': take_partial * 24})
                shortage -= 24
        if shortage > 0 and loc['loose_pc'] > 0:
            take_loose = min(loc['loose_pc'], shortage)
            if take_loose > 0:
                transfers.append({'from_location_id': loc['location_id'], 'from_location_name': loc['location_name'], 'packaging': 'LOOSE', 'quantity': take_loose, 'pc_value': take_loose})
                shortage -= take_loose
    return {'needed': True, 'original_shortage': check['shortage'], 'remaining_shortage': shortage, 'transfers': transfers, 'can_fulfill': shortage <= 0}

def execute_transfer(transfer_plan, order_ref, user_name):
    movements = []
    breakdown_df = db.get_sheet('packaging_breakdown')
    for transfer in transfer_plan['transfers']:
        from_loc_id = transfer['from_location_id']
        packaging = transfer['packaging']
        qty = transfer['quantity']
        record = breakdown_df[(breakdown_df['Product_ID'] == transfer_plan['product_id']) & (breakdown_df['Location_ID'] == from_loc_id)]
        if not record.empty:
            idx = record.index[0]
            if packaging == 'PALLET':
                current = safe_int(breakdown_df.at[idx, 'Full_Units'])
                breakdown_df.at[idx, 'Full_Units'] = current - qty
            elif packaging == 'PQT':
                current = safe_int(breakdown_df.at[idx, 'Full_Units'])
                breakdown_df.at[idx, 'Full_Units'] = current - qty
            elif packaging == 'PARTIAL_PQT':
                current = safe_int(breakdown_df.at[idx, 'Partial_Units'])
                breakdown_df.at[idx, 'Partial_Units'] = current - qty
            elif packaging == 'LOOSE':
                current = safe_int(breakdown_df.at[idx, 'Loose_Pieces'])
                breakdown_df.at[idx, 'Loose_Pieces'] = current - qty
        movements.append({'date': datetime.now(), 'type': 'TRANSFER', 'product_id': transfer_plan['product_id'], 'from_location': from_loc_id, 'to_location': transfer_plan['target_location_id'], 'quantity': qty, 'uom_id': None, 'reference': order_ref, 'user': user_name, 'notes': f"Transfer {qty} {packaging} for {order_ref}"})
    db.save_sheet('packaging_breakdown', breakdown_df)
    movements_df = db.get_sheet('stock_movements')
    for move in movements:
        new_id = db.get_next_id('stock_movements')
        new_row = pd.DataFrame([{'ID': new_id, **move}])
        movements_df = pd.concat([movements_df, new_row], ignore_index=True)
    db.save_sheet('stock_movements', movements_df)
    return movements

tab1, tab2, tab3 = st.tabs(["📦 Check Stock", "🔄 Transfer Needed", "📋 Transfer History"])

with tab1:
    st.subheader("Current Stock by Location")
    products_df = db.get_sheet('products')
    if products_df.empty:
        st.info("No products available.")
    else:
        product_options = {row['Name']: row['ID'] for _, row in products_df.iterrows()}
        selected_product = st.selectbox("Select Product", list(product_options.keys()))
        product_id = product_options[selected_product]
        stock_data = get_all_locations_stock(product_id)
        if stock_data:
            display_data = []
            for loc in stock_data:
                display_data.append({'Location': loc['location_name'], 'Pallets': loc['full_pallets'], 'Full PQT': loc['full_pqt'], 'Partial PQT': loc['partial_pqt'], 'Loose PC': loc['loose_pc'], 'Total PC': loc['total_pc']})
            st.dataframe(pd.DataFrame(display_data), width='stretch', hide_index=True)
        else:
            st.info(f"No stock found for {selected_product}")

with tab2:
    st.subheader("Check Transfer Need")
    products_df = db.get_sheet('products')
    locations_df = db.get_sheet('locations')
    if products_df.empty:
        st.info("No products available.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            product_options = {row['Name']: row['ID'] for _, row in products_df.iterrows()}
            selected_product = st.selectbox("Product", list(product_options.keys()), key="transfer_product")
            product_id = product_options[selected_product]
        with col2:
            storage_locs = locations_df[locations_df['Can_Hold_Stock'] == True]
            loc_options = {row['Name']: row['ID'] for _, row in storage_locs.iterrows()}
            selected_loc = st.selectbox("Target Location", list(loc_options.keys()))
            target_loc_id = loc_options[selected_loc]
        needed_pc = st.number_input("PC Needed", min_value=1, step=1, value=1)
        if st.button("Check Transfer Need", type="primary"):
            check = check_transfer_needed(product_id, needed_pc, target_loc_id)
            if not check['needed']:
                st.success(check['message'])
            else:
                st.warning(f"Shortage: {check['shortage']} PC")
                plan = calculate_transfer_plan(product_id, needed_pc, target_loc_id)
                if plan['transfers']:
                    st.subheader("Proposed Transfer Plan")
                    plan_data = []
                    for t in plan['transfers']:
                        plan_data.append({'From': t['from_location_name'], 'Packaging': t['packaging'], 'Quantity': t['quantity'], 'PC Value': t['pc_value']})
                    st.dataframe(pd.DataFrame(plan_data), width='stretch', hide_index=True)
                    if plan['remaining_shortage'] > 0:
                        st.error(f"Cannot fully fulfill. Still short: {plan['remaining_shortage']} PC")
                    else:
                        if st.button("Execute Transfer"):
                            plan['product_id'] = product_id
                            plan['target_location_id'] = target_loc_id
                            movements = execute_transfer(plan, f"AUTO-{datetime.now().strftime('%Y%m%d%H%M%S')}", user['full_name'])
                            st.success(f"Transfer completed! {len(movements)} item(s) moved.")
                            st.rerun()
                else:
                    st.error("No transfer plan generated. Insufficient stock?")

with tab3:
    st.subheader("Transfer History")
    movements_df = db.get_sheet('stock_movements')
    transfers = movements_df[movements_df['Type'] == 'TRANSFER']
    if transfers.empty:
        st.info("No transfer history")
    else:
        display_history = []
        for _, t in transfers.iterrows():
            display_history.append({'Date': t['Date'], 'Product': get_product_name(t['Product_ID']), 'From': get_location_name(t['From_Location']), 'To': get_location_name(t['To_Location']), 'Quantity': t['Quantity'], 'Reference': t['Reference'], 'User': t['User']})
        st.dataframe(pd.DataFrame(display_history), width='stretch', hide_index=True)

st.divider()
st.caption("Tip: Transfers move full packaging units between locations to maintain stock at MAIN location.")