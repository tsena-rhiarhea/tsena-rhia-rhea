# pages/7_Build_Requests.py
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

st.title("🏗️ Build Request Management")
st.caption("Request and approve packaging builds (breakdown only - no building up)")

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

def get_uom_factor(uom_id):
    if pd.isna(uom_id) or uom_id is None:
        return 1
    df = db.get_sheet('uom')
    result = df[df['ID'] == uom_id]
    return float(result.iloc[0]['Factor']) if not result.empty else 1

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

def get_product_base_uom(product_id):
    df = db.get_sheet('products')
    result = df[df['ID'] == product_id]
    return result.iloc[0]['Base_UOM_ID'] if not result.empty else None

def get_stock_breakdown(product_id):
    breakdown_df = db.get_sheet('packaging_breakdown')
    product_records = breakdown_df[breakdown_df['Product_ID'] == product_id]
    total_pc = 0
    for _, row in product_records.iterrows():
        uom_id = row.get('UOM_ID', None)
        uom_name = get_uom_name(uom_id) if uom_id else "PC"
        full = safe_int(row.get('Full_Units', 0))
        partial = safe_int(row.get('Partial_Units', 0))
        loose = safe_int(row.get('Loose_Pieces', 0))
        if uom_name == 'PALLET':
            total_pc += full * 480 + loose
        elif uom_name == 'PQT':
            total_pc += full * 24 + partial * 24 + loose
        else:
            total_pc += full + partial + loose
    return total_pc

def get_stock_by_location(product_id):
    breakdown_df = db.get_sheet('packaging_breakdown')
    product_records = breakdown_df[breakdown_df['Product_ID'] == product_id]
    location_stock = []
    for _, row in product_records.iterrows():
        loc_id = row['Location_ID']
        loc_name = get_location_name(loc_id)
        uom_id = row.get('UOM_ID', None)
        uom_name = get_uom_name(uom_id) if uom_id else "PC"
        full = safe_int(row.get('Full_Units', 0))
        partial = safe_int(row.get('Partial_Units', 0))
        loose = safe_int(row.get('Loose_Pieces', 0))
        if uom_name == 'PALLET':
            pc = full * 480 + loose
        elif uom_name == 'PQT':
            pc = full * 24 + partial * 24 + loose
        else:
            pc = full + partial + loose
        if pc > 0:
            location_stock.append({'location_id': loc_id, 'location_name': loc_name, 'pallets': full if uom_name == 'PALLET' else 0, 'pqt': full if uom_name == 'PQT' else 0, 'partial_pqt': partial if uom_name == 'PQT' else 0, 'loose': loose, 'total_pc': pc})
    return location_stock

def create_pulling_plan(product_id, needed_pc):
    location_stock = get_stock_by_location(product_id)
    location_stock.sort(key=lambda x: x['total_pc'], reverse=True)
    plan = []
    remaining = needed_pc
    for loc in location_stock:
        if remaining <= 0:
            break
        if loc['pallets'] > 0 and remaining >= 480:
            take = min(loc['pallets'], remaining // 480)
            if take > 0:
                plan.append({'location_id': loc['location_id'], 'location_name': loc['location_name'], 'packaging': 'PALLET', 'quantity': take, 'pc_value': take * 480})
                remaining -= take * 480
        if remaining > 0 and loc['pqt'] > 0 and remaining >= 24:
            take = min(loc['pqt'], remaining // 24)
            if take > 0:
                plan.append({'location_id': loc['location_id'], 'location_name': loc['location_name'], 'packaging': 'PQT', 'quantity': take, 'pc_value': take * 24})
                remaining -= take * 24
        if remaining > 0 and loc['partial_pqt'] > 0:
            take = min(loc['partial_pqt'], 1)
            if take > 0:
                plan.append({'location_id': loc['location_id'], 'location_name': loc['location_name'], 'packaging': 'PARTIAL_PQT', 'quantity': take, 'pc_value': take * 24})
                remaining -= 24
        if remaining > 0 and loc['loose'] > 0:
            take = min(loc['loose'], remaining)
            if take > 0:
                plan.append({'location_id': loc['location_id'], 'location_name': loc['location_name'], 'packaging': 'LOOSE', 'quantity': take, 'pc_value': take})
                remaining -= take
    return plan, remaining

def execute_build(request_id, pulling_plan, approved_by):
    requests_df = db.get_sheet('build_requests')
    breakdown_df = db.get_sheet('packaging_breakdown')
    movements_df = db.get_sheet('stock_movements')
    request = requests_df[requests_df['ID'] == request_id].iloc[0]
    product_id = request['Product_ID']
    target_uom_id = request['Target_Packaging_UOM_ID']
    quantity = request['Quantity']
    target_uom_name = get_uom_name(target_uom_id)
    factor = get_uom_factor(target_uom_id)
    needed_pc = quantity * factor
    for item in pulling_plan:
        loc_id = item['location_id']
        packaging = item['packaging']
        qty = item['quantity']
        record = breakdown_df[(breakdown_df['Product_ID'] == product_id) & (breakdown_df['Location_ID'] == loc_id)]
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
    locations_df = db.get_sheet('locations')
    main_loc = locations_df[locations_df['Name'] == 'MAIN AREA']
    main_loc_id = main_loc.iloc[0]['ID'] if not main_loc.empty else 1
    main_record = breakdown_df[(breakdown_df['Product_ID'] == product_id) & (breakdown_df['Location_ID'] == main_loc_id)]
    if not main_record.empty:
        idx = main_record.index[0]
        current = safe_int(breakdown_df.at[idx, 'Full_Units'])
        breakdown_df.at[idx, 'Full_Units'] = current + quantity
    else:
        new_id = db.get_next_id('packaging_breakdown')
        new_row = pd.DataFrame([{'ID': new_id, 'Product_ID': product_id, 'Location_ID': main_loc_id, 'UOM_ID': target_uom_id, 'Full_Units': quantity, 'Partial_Units': 0, 'Loose_Pieces': 0}])
        breakdown_df = pd.concat([breakdown_df, new_row], ignore_index=True)
    db.save_sheet('packaging_breakdown', breakdown_df)
    new_move_id = db.get_next_id('stock_movements')
    new_move = pd.DataFrame([{'ID': new_move_id, 'Date': datetime.now(), 'Type': 'BUILD', 'Product_ID': product_id, 'From_Location': None, 'To_Location': main_loc_id, 'Quantity': quantity, 'UOM_ID': target_uom_id, 'Reference': f"BUILD-{request_id}", 'User': approved_by, 'Notes': f"Built {quantity} {target_uom_name} from {needed_pc} PC"}])
    movements_df = pd.concat([movements_df, new_move], ignore_index=True)
    db.save_sheet('stock_movements', movements_df)
    requests_df.loc[requests_df['ID'] == request_id, 'Status'] = 'APPROVED'
    requests_df.loc[requests_df['ID'] == request_id, 'Approved_By'] = approved_by
    requests_df.loc[requests_df['ID'] == request_id, 'Approved_Date'] = datetime.now()
    requests_df.loc[requests_df['ID'] == request_id, 'Pulling_Plan'] = str(pulling_plan)
    db.save_sheet('build_requests', requests_df)

tab1, tab2, tab3 = st.tabs(["📝 New Request", "📋 Pending Approval", "📜 Request History"])

with tab1:
    st.subheader("Create Build Request")
    st.warning("NOTE: You are requesting to BUILD packaging from smaller units. This requires manager approval.")
    products_df = db.get_sheet('products')
    uom_df = db.get_sheet('uom')
    if products_df.empty:
        st.error("No products available")
    else:
        product_options = {row['Name']: row['ID'] for _, row in products_df.iterrows()}
        selected_product = st.selectbox("Product", list(product_options.keys()))
        product_id = product_options[selected_product]
        base_uom_id = get_product_base_uom(product_id)
        base_uom_name = get_uom_name(base_uom_id)
        packaging_units = uom_df[uom_df['Type'] == 'PACKAGING']
        pkg_options = {row['Name']: row['ID'] for _, row in packaging_units.iterrows()}
        if not pkg_options:
            st.error("No packaging units found. Add packaging units in UOM module first.")
        else:
            selected_pkg = st.selectbox("Packaging to Build", list(pkg_options.keys()))
            pkg_id = pkg_options[selected_pkg]
            pkg_factor = get_uom_factor(pkg_id)
            quantity = st.number_input(f"Number of {selected_pkg} to build", min_value=1, step=1, value=1)
            needed_pc = quantity * pkg_factor
            st.info(f"Each {selected_pkg} requires {pkg_factor:.0f} {base_uom_name}")
            st.info(f"Total needed: {needed_pc:.0f} {base_uom_name}")
            total_stock = get_stock_breakdown(product_id)
            st.metric("Available Stock (PC)", f"{total_stock:.0f}")
            if total_stock < needed_pc:
                st.error(f"Insufficient stock. Need {needed_pc} PC but only {total_stock} PC available.")
            else:
                plan, remaining = create_pulling_plan(product_id, needed_pc)
                if plan:
                    st.subheader("Proposed Pulling Plan")
                    plan_data = []
                    for p in plan:
                        plan_data.append({'Location': p['location_name'], 'Packaging': p['packaging'], 'Quantity': p['quantity'], 'PC Value': p['pc_value']})
                    st.dataframe(pd.DataFrame(plan_data), width='stretch', hide_index=True)
                    if remaining > 0:
                        st.error(f"Cannot fulfill fully. Still short: {remaining} PC")
                    else:
                        reason = st.text_area("Reason for build request")
                        if st.button("Submit Request", type="primary"):
                            requests_df = db.get_sheet('build_requests')
                            new_id = db.get_next_id('build_requests')
                            new_row = pd.DataFrame([{'ID': new_id, 'Request_Date': datetime.now(), 'Requested_By': user['full_name'], 'Product_ID': product_id, 'Target_Packaging_UOM_ID': pkg_id, 'Quantity': quantity, 'Status': 'PENDING', 'Approved_By': None, 'Approved_Date': None, 'Pulling_Plan': str(plan), 'Notes': reason}])
                            requests_df = pd.concat([requests_df, new_row], ignore_index=True)
                            db.save_sheet('build_requests', requests_df)
                            st.success(f"Build request #{new_id} submitted for manager approval")
                            st.rerun()

with tab2:
    st.subheader("Pending Approval Requests")
    requests_df = db.get_sheet('build_requests')
    pending = requests_df[requests_df['Status'] == 'PENDING']
    if pending.empty:
        st.info("No pending requests")
    else:
        for _, req in pending.iterrows():
            with st.expander(f"Request #{req['ID']} - {req['Request_Date']}"):
                st.write(f"**Product:** {get_product_name(req['Product_ID'])}")
                st.write(f"**Requested By:** {req['Requested_By']}")
                st.write(f"**Target Packaging:** {get_uom_name(req['Target_Packaging_UOM_ID'])}")
                st.write(f"**Quantity:** {req['Quantity']}")
                st.write(f"**Reason:** {req['Notes'] or 'Not provided'}")
                if req['Pulling_Plan']:
                    try:
                        plan = eval(req['Pulling_Plan'])
                        plan_data = []
                        for p in plan:
                            plan_data.append({'Location': p['location_name'], 'Packaging': p['packaging'], 'Quantity': p['quantity']})
                        st.dataframe(pd.DataFrame(plan_data), width='stretch', hide_index=True)
                    except:
                        st.write(req['Pulling_Plan'])
                if user['role'] in ['MANAGER', 'ADMIN']:
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"✅ Approve", key=f"approve_{req['ID']}"):
                            plan = eval(req['Pulling_Plan']) if req['Pulling_Plan'] else []
                            execute_build(req['ID'], plan, user['full_name'])
                            st.success(f"Request #{req['ID']} approved and executed!")
                            st.rerun()
                    with col2:
                        if st.button(f"❌ Reject", key=f"reject_{req['ID']}"):
                            requests_df.loc[requests_df['ID'] == req['ID'], 'Status'] = 'REJECTED'
                            requests_df.loc[requests_df['ID'] == req['ID'], 'Approved_By'] = user['full_name']
                            requests_df.loc[requests_df['ID'] == req['ID'], 'Approved_Date'] = datetime.now()
                            db.save_sheet('build_requests', requests_df)
                            st.success(f"Request #{req['ID']} rejected")
                            st.rerun()

with tab3:
    st.subheader("Request History")
    requests_df = db.get_sheet('build_requests')
    history = requests_df[requests_df['Status'] != 'PENDING']
    if history.empty:
        st.info("No request history")
    else:
        display_history = []
        for _, req in history.iterrows():
            display_history.append({'ID': req['ID'], 'Date': req['Request_Date'], 'Product': get_product_name(req['Product_ID']), 'Requested By': req['Requested_By'], 'Quantity': req['Quantity'], 'Status': req['Status'], 'Approved By': req['Approved_By'] if req['Approved_By'] else '-'})
        st.dataframe(pd.DataFrame(display_history), width='stretch', hide_index=True)

st.divider()
st.caption("Tip: Build requests require manager approval and can only be done when sufficient loose units exist across all locations.")