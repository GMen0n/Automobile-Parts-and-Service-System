import streamlit as st
from sqlalchemy import text
import pandas as pd
import datetime

# Set the page configuration (do this first!)
st.set_page_config(
    page_title="Auto Service Management",
    page_icon="🔧",
    layout="wide"
)

# --- DYNAMIC GRADIENT BACKGROUND ---
def inject_custom_css():
    st.markdown(
        f"""
        <style>
        @keyframes gradientBG {{
            0% {{ background-position: 0% 50%; }}
            50% {{ background-position: 100% 50%; }}
            100% {{ background-position: 0% 50%; }}
        }}
        [data-testid="stAppViewContainer"] > .main {{
            background: linear-gradient(-45deg, #1A1A2E, #1F2833, #3D405B, #4E4E5A);
            background-size: 400% 400%;
            animation: gradientBG 20s ease infinite;
            color: #FFFFFF;
        }}
        [data-testid="stTabs"] [data-baseweb="tab-list"] {{
            background-color: transparent;
        }}
        [data-testid="stForm"], [data-testid="stContainer"], [data-testid="stExpander"] {{
            background-color: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
        }}
        h1, h2, h3, h4, h5, h6 {{
            color: #FFFFFF;
        }}
        .stDataFrame {{
            color: #333;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

inject_custom_css()
# --- END OF CSS INJECTION ---


# --- DATABASE CONNECTION ---
try:
    conn = st.connection("autoservicedb", type="sql", ttl=10)
    conn.query("SELECT 1;")
except Exception as e:
    st.error(f"Error connecting to database: {e}")
    st.stop() 

st.title("Auto Service Management System")
st.toast("Successfully connected to database!")

# --- DATA CACHING FUNCTIONS ---
@st.cache_data(ttl=60)
def get_customers():
    return conn.query("SELECT * FROM customers ORDER BY FirstName;", ttl=0)

@st.cache_data(ttl=60)
def get_mechanics():
    return conn.query("SELECT * FROM mechanics ORDER BY FirstName;", ttl=0)

@st.cache_data(ttl=60)
def get_services():
    return conn.query("SELECT * FROM services ORDER BY ServiceName;", ttl=0)

@st.cache_data(ttl=60)
def get_parts():
    return conn.query("SELECT * FROM parts ORDER BY PartName;", ttl=0)

@st.cache_data(ttl=60)
def get_vehicles(customer_id):
    return conn.query("SELECT * FROM vehicles WHERE CustomerID = :id", params={"id": customer_id}, ttl=0)

@st.cache_data(ttl=60)
def get_appointments():
    query = """
    SELECT sa.AppointmentID, sa.AppointmentDate, sa.Status, sa.DurationMinutes,
           CONCAT(c.FirstName, ' ', c.LastName) AS Customer,
           CONCAT(v.Year, ' ', v.Make, ' ', v.Model) AS Vehicle,
           s.ServiceName,
           CONCAT(m.FirstName, ' ', m.LastName) AS Mechanic
    FROM serviceappointments sa
    JOIN customers c ON sa.CustomerID = c.CustomerID
    JOIN vehicles v ON sa.VehicleID = v.VehicleID
    JOIN services s ON sa.ServiceID = s.ServiceID
    JOIN mechanics m ON sa.MechanicID = m.MechanicID
    ORDER BY sa.AppointmentDate DESC;
    """
    return conn.query(query, ttl=0)

@st.cache_data(ttl=60)
def get_orders():
    query = """
    SELECT o.OrderID, o.OrderDate, o.TotalAmount, o.Status,
           CONCAT(c.FirstName, ' ', c.LastName) AS Customer
    FROM orders o
    JOIN customers c ON o.CustomerID = c.CustomerID
    ORDER BY o.OrderDate DESC;
    """
    return conn.query(query, ttl=0)

@st.cache_data(ttl=60)
def get_order_items(order_id):
    items_query = """
    SELECT p.PartName, oi.Quantity, oi.UnitPrice
    FROM orderitems oi
    JOIN parts p ON oi.PartID = p.PartID
    WHERE oi.OrderID = :id;
    """
    return conn.query(items_query, params={"id": order_id}, ttl=0)

# --- NAVIGATION TABS ---
tab_customers, tab_bookings, tab_shop, tab_admin = st.tabs([
    "Customers & Vehicles", 
    "Bookings", 
    "Shop (Orders & Parts)", 
    "Admin Panel"
])


# --- TAB 1: CUSTOMERS & VEHICLES ---
with tab_customers:
    st.header("Customer and Vehicle Management")
    
    sub_tab_c_view, sub_tab_c_edit, sub_tab_c_vehicles = st.tabs(["View All Customers", "Add/Edit Customer", "Manage Vehicles"])
    
    with sub_tab_c_view:
        st.subheader("All Customers (FR-3)")
        try:
            customers_df = get_customers()
            st.dataframe(customers_df, use_container_width=True)
        except Exception as e:
            st.error(f"Error fetching customers: {e}")

    with sub_tab_c_edit:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Add New Customer")
            with st.form("add_customer_form", clear_on_submit=True, border=True):
                first_name = st.text_input("First Name")
                last_name = st.text_input("Last Name")
                email = st.text_input("Email")
                phone = st.text_input("Phone")
                address = st.text_area("Address")
                
                submitted = st.form_submit_button("Add Customer")
                if submitted:
                    if not all([first_name, last_name, email]):
                        st.warning("First Name, Last Name, and Email are required.")
                    else:
                        try:
                            query = text("CALL sp_AddCustomer(:fname, :lname, :email, :phone, :address);")
                            with conn.session as s:
                                s.execute(query, {"fname": first_name, "lname": last_name, "email": email, "phone": phone, "address": address})
                                s.commit()
                            st.toast("Customer added successfully!")
                            get_customers.clear()
                            st.rerun() 
                        except Exception as e:
                            st.error(f"Error adding customer: {e}")

        with col2:
            st.subheader("Edit Customer Details")
            try:
                customers_df = get_customers()
                customer_list = list(customers_df.itertuples(index=False, name=None))
                selected_customer_tuple = st.selectbox(
                    "Select Customer to Edit",
                    customer_list,
                    format_func=lambda x: f"{x[1]} {x[2]} (ID: {x[0]})",
                    key="edit_customer_select" 
                )
                if selected_customer_tuple:
                    selected_id = selected_customer_tuple[0]
                    selected_customer = customers_df[customers_df['CustomerID'] == selected_id].iloc[0]
                    with st.form("edit_customer_form", border=True):
                        first_name = st.text_input("First Name", value=selected_customer['FirstName'])
                        last_name = st.text_input("Last Name", value=selected_customer['LastName'])
                        email = st.text_input("Email", value=selected_customer['Email'])
                        phone = st.text_input("Phone", value=selected_customer['Phone'])
                        address = st.text_area("Address", value=selected_customer['Address'])
                        submitted = st.form_submit_button("Save Changes")
                        if submitted:
                            try:
                                query = text("CALL sp_UpdateCustomer(:id, :fname, :lname, :email, :phone, :address);")
                                with conn.session as s:
                                    s.execute(query, {"id": selected_id, "fname": first_name, "lname": last_name, "email": email, "phone": phone, "address": address})
                                    s.commit()
                                st.toast("Customer details updated!")
                                get_customers.clear()
                                st.rerun() 
                            except Exception as e:
                                st.error(f"Error updating customer: {e}")
            except Exception as e:
                st.error(f"Error fetching customer list: {e}")

    with sub_tab_c_vehicles:
        st.subheader("Manage Customer Vehicles")
        try:
            customers_df = get_customers()
            customer_list = list(customers_df.itertuples(index=False, name=None))
            selected_customer_tuple = st.selectbox(
                "Select Customer to Manage Vehicles",
                customer_list,
                format_func=lambda x: f"{x[1]} {x[2]} (ID: {x[0]})",
                key="vehicle_customer_select"
            )
            if selected_customer_tuple:
                selected_cust_id = selected_customer_tuple[0]
                st.info(f"Managing vehicles for {selected_customer_tuple[1]} {selected_customer_tuple[2]}")
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Add New Vehicle")
                    with st.form("add_vehicle_form", clear_on_submit=True, border=True):
                        make = st.text_input("Make (e.g., Toyota)")
                        model = st.text_input("Model (e.g., Camry)")
                        year = st.number_input("Year", min_value=1980, max_value=2026, value=2020, step=1)
                        vin = st.text_input("VIN (17 Chars)", max_chars=17)
                        submitted = st.form_submit_button("Add Vehicle")
                        if submitted:
                            if not all([make, model, year, vin]):
                                st.warning("All fields are required.")
                            else:
                                try:
                                    query = text("CALL sp_AddVehicle(:id, :make, :model, :year, :vin);")
                                    with conn.session as s:
                                        s.execute(query, {"id": selected_cust_id, "make": make, "model": model, "year": int(year), "vin": vin})
                                        s.commit()
                                    st.toast("Vehicle added successfully!")
                                    get_vehicles.clear(selected_cust_id)
                                    st.rerun() 
                                except Exception as e:
                                    st.error(f"Error adding vehicle: {e}")
                with col2:
                    st.subheader("Edit Existing Vehicle")
                    vehicles_df = get_vehicles(selected_cust_id)
                    if vehicles_df.empty:
                        st.info("This customer has no vehicles to edit.")
                    else:
                        vehicle_list = list(vehicles_df.itertuples(index=False, name=None))
                        selected_vehicle_tuple = st.selectbox(
                            "Select Vehicle to Edit",
                            vehicle_list,
                            format_func=lambda x: f"{x[3]} {x[4]} ({x[5]}) (ID: {x[0]})",
                            key="edit_vehicle_select"
                        )
                        if selected_vehicle_tuple:
                            selected_vehicle_id = selected_vehicle_tuple[0]
                            with st.form("edit_vehicle_form", border=True):
                                make = st.text_input("Make", value=selected_vehicle_tuple[2])
                                model = st.text_input("Model", value=selected_vehicle_tuple[3])
                                year = st.number_input("Year", min_value=1980, max_value=2026, step=1, value=selected_vehicle_tuple[4])
                                vin = st.text_input("VIN (17 Chars)", max_chars=17, value=selected_vehicle_tuple[5])
                                submitted = st.form_submit_button("Save Vehicle Changes")
                                if submitted:
                                    try:
                                        query = text("CALL sp_UpdateVehicle(:id, :make, :model, :year, :vin);")
                                        with conn.session as s:
                                            s.execute(query, {"id": selected_vehicle_id, "make": make, "model": model, "year": int(year), "vin": vin})
                                            s.commit()
                                        st.toast("Vehicle details updated!")
                                        get_vehicles.clear(selected_cust_id)
                                        st.rerun() 
                                    except Exception as e:
                                        st.error(f"Error updating vehicle: {e}")
        except Exception as e:
            st.error(f"Error fetching customer list for vehicles: {e}")


# --- TAB 2: BOOKINGS (Service Appointments) ---
with tab_bookings:
    st.header("Service Appointments (FR-15, FR-16, FR-17)")
    
    sub_tab_b_new, sub_tab_b_view = st.tabs(["Book New Appointment", "View All Appointments"])
    
    def load_booking_data():
        data = {}
        data["customers"] = get_customers()
        data["mechanics"] = get_mechanics()
        data["services"] = get_services()
        return data

    booking_data = load_booking_data()

    with sub_tab_b_new:
        st.subheader("Book a New Service Appointment")
        
        with st.form("book_appointment_form", clear_on_submit=True, border=True):
            customer_list = list(booking_data["customers"].itertuples(index=False, name=None))
            selected_customer_tuple = st.selectbox(
                "Select Customer",
                customer_list,
                format_func=lambda x: f"{x[1]} {x[2]} (ID: {x[0]})",
                key="book_customer_select"
            )
            
            selected_vehicle_tuple = None
            if selected_customer_tuple:
                selected_cust_id = selected_customer_tuple[0]
                vehicles_df = get_vehicles(selected_cust_id)
                if vehicles_df.empty:
                    st.warning("This customer has no vehicles. Please add one in the 'Customers & Vehicles' tab.")
                    vehicle_list = []
                else:
                    vehicle_list = list(vehicles_df.itertuples(index=False, name=None))
                
                selected_vehicle_tuple = st.selectbox(
                    "Select Vehicle",
                    vehicle_list,
                    format_func=lambda x: f"{x[2]} {x[3]} ({x[4]}) (VIN: {x[5]})",
                    key="book_vehicle_select"
                )

            service_list = list(booking_data["services"].itertuples(index=False, name=None))
            selected_service_tuple = st.selectbox(
                "Select Service",
                service_list,
                format_func=lambda x: f"{x[1]} (${x[3]})",
                key="book_service_select"
            )

            mechanic_list = list(booking_data["mechanics"].itertuples(index=False, name=None))
            selected_mechanic_tuple = st.selectbox(
                "Select Mechanic",
                mechanic_list,
                format_func=lambda x: f"{x[1]} {x[2]} ({x[3]})",
                key="book_mechanic_select"
            )
            
            col1, col2, col3 = st.columns(3)
            with col1:
                appt_date = st.date_input("Appointment Date", min_value=datetime.date.today())
            with col2:
                appt_time = st.time_input("Appointment Time", value=datetime.time(9, 0))
            with col3:
                duration = st.number_input("Duration (Minutes)", min_value=30, value=60, step=15)

            submitted = st.form_submit_button("Book Appointment")
            if submitted:
                if not all([selected_customer_tuple, selected_vehicle_tuple, selected_service_tuple, selected_mechanic_tuple]):
                    st.warning("All fields are required. Please check if customer has a vehicle.")
                else:
                    try:
                        appointment_datetime = datetime.datetime.combine(appt_date, appt_time)
                        query = text("CALL sp_BookAppointment(:cid, :vid, :mid, :sid, :date, :duration);")
                        with conn.session as s:
                            s.execute(query, {
                                "cid": selected_customer_tuple[0],
                                "vid": selected_vehicle_tuple[0],
                                "mid": selected_mechanic_tuple[0],
                                "sid": selected_service_tuple[0],
                                "date": appointment_datetime,
                                "duration": int(duration)
                            })
                            s.commit()
                        st.toast("Appointment booked successfully!")
                        get_appointments.clear()
                        st.rerun() 
                    except Exception as e:
                        st.error(f"Error booking appointment: {e}")

    with sub_tab_b_view:
        st.subheader("All Scheduled Appointments")

        def update_status(appt_id, new_status):
            try:
                query = text("CALL sp_UpdateAppointmentStatus(:id, :status);")
                with conn.session as s:
                    s.execute(query, {"id": appt_id, "status": new_status})
                    s.commit()
                st.toast(f"Status updated for Appointment {appt_id}")
                get_appointments.clear() 
            except Exception as e:
                st.error(f"Error updating status: {e}")

        def cancel_appointment(appt_id):
            try:
                query = text("CALL sp_CancelAppointment(:id);")
                with conn.session as s:
                    s.execute(query, {"id": appt_id})
                    s.commit()
                st.toast(f"Appointment {appt_id} cancelled.")
                get_appointments.clear()
            except Exception as e:
                st.error(f"Error cancelling appointment: {e}")

        try:
            appointments_df = get_appointments()
            
            if appointments_df.empty:
                st.info("No appointments found.")
            else:
                for index, row in appointments_df.iterrows():
                    with st.container(border=True):
                        col1, col2 = st.columns([3, 1.5])
                        with col1:
                            st.subheader(f"Appointment #{row['AppointmentID']} - {row['ServiceName']}")
                            st.write(f"**Customer:** {row['Customer']}")
                            st.write(f"**Vehicle:** {row['Vehicle']}")
                            st.write(f"**Mechanic:** {row['Mechanic']}")
                            st.write(f"**Date:** {row['AppointmentDate'].strftime('%Y-%m-%d %I:%M %p')}")
                            st.write(f"**Duration:** {row['DurationMinutes']} minutes")
                        
                        with col2:
                            status_options = ["Scheduled", "Completed", "Cancelled", "In Progress"]
                            current_status_index = status_options.index(row['Status']) if row['Status'] in status_options else 0
                            
                            new_status = st.selectbox(
                                "Update Status",
                                status_options,
                                index=current_status_index,
                                key=f"status_{row['AppointmentID']}"
                            )
                            st.button(
                                "Save Status", 
                                key=f"save_status_{row['AppointmentID']}",
                                on_click=update_status,
                                args=(row['AppointmentID'], new_status)
                            )
                            st.button(
                                "Cancel Appointment", 
                                type="primary",
                                key=f"cancel_{row['AppointmentID']}",
                                on_click=cancel_appointment,
                                args=(row['AppointmentID'],)
                            )
        except Exception as e:
            st.error(f"Error fetching appointments: {e}")


# --- TAB 3: SHOP (Orders & Parts) ---
with tab_shop:
    st.header("Place and View Orders")
    
    sub_tab_s_new, sub_tab_s_view = st.tabs(["Place New Order", "View All Orders"])

    if 'cart' not in st.session_state:
        st.session_state.cart = []

    with sub_tab_s_new:
        col1, col2 = st.columns([0.6, 0.4])
        
        with col1:
            st.subheader("Available Parts (FR-12)")
            
            with st.form("add_to_cart_form", border=True):
                parts_df = get_parts()
                parts_df = parts_df[parts_df['StockQuantity'] > 0]
                
                part_list = list(parts_df.itertuples(index=False, name=None))
                
                selected_part_tuple = st.selectbox(
                    "Select Part",
                    part_list,
                    format_func=lambda x: f"{x[1]} ({x[2]}) - ${x[3]} (Stock: {x[4]})"
                )
                quantity = st.number_input("Quantity", min_value=1, value=1, step=1)
                
                add_to_cart = st.form_submit_button("Add to Cart")
                
                if add_to_cart:
                    if selected_part_tuple:
                        if quantity > selected_part_tuple[4]:
                            st.warning("Cannot add more than available stock.")
                        else:
                            st.session_state.cart.append({
                                "PartID": selected_part_tuple[0],
                                "PartName": selected_part_tuple[1],
                                "Quantity": quantity,
                                "Price": selected_part_tuple[3]
                            })
                            st.toast(f"Added {quantity}x {selected_part_tuple[1]} to cart.")
                            # No rerun here, cart updates on its own

            st.subheader("All Parts Inventory")
            low_stock_df = get_parts()
            
            def highlight_low_stock(row):
                return ['background-color: #FFF0F0'] * len(row) if row.StockQuantity < 10 else [''] * len(row)

            st.dataframe(low_stock_df.style.apply(highlight_low_stock, axis=1), use_container_width=True)

        with col2:
            st.subheader("Your Cart")
            if not st.session_state.cart:
                st.info("Your cart is empty.")
            else:
                cart_total = 0
                for i, item in enumerate(st.session_state.cart):
                    with st.container(border=True):
                        st.write(f"**{item['PartName']}**")
                        st.write(f"Quantity: {item['Quantity']} @ ${item['Price']:.2f} each")
                        st.write(f"Subtotal: ${item['Quantity'] * item['Price']:.2f}")
                        cart_total += item['Quantity'] * item['Price']
                        
                        if st.button("Remove", key=f"remove_cart_{i}"):
                            st.session_state.cart.pop(i)
                            st.rerun() 
                
                st.subheader(f"Cart Total: ${cart_total:.2f}")
                
                with st.form("place_order_form", border=True):
                    customers_df = get_customers()
                    customer_list = list(customers_df.itertuples(index=False, name=None))
                    selected_customer_tuple = st.selectbox(
                        "Select Customer for this Order",
                        customer_list,
                        format_func=lambda x: f"{x[1]} {x[2]} (ID: {x[0]})",
                        key="order_customer_select"
                    )
                    
                    place_order = st.form_submit_button("Place Order")
                    
                    if place_order:
                        if not selected_customer_tuple:
                            st.warning("Please select a customer.")
                        elif not st.session_state.cart:
                            st.warning("Your cart is empty.")
                        else:
                            try:
                                with conn.session as s:
                                    query_create_order = text("CALL sp_CreateOrder(:cid, @new_order_id);")
                                    s.execute(query_create_order, {"cid": selected_customer_tuple[0]})
                                    new_order_id = s.execute(text("SELECT @new_order_id;")).scalar()
                                    
                                    if new_order_id:
                                        for item in st.session_state.cart:
                                            query_add_item = text("CALL sp_AddOrderItem(:oid, :pid, :qty);")
                                            s.execute(query_add_item, {
                                                "oid": new_order_id,
                                                "pid": item['PartID'],
                                                "qty": item['Quantity']
                                            })
                                        s.commit()
                                        st.session_state.cart = []
                                        st.success(f"Order #{new_order_id} placed successfully!")
                                        
                                        get_orders.clear()
                                        get_parts.clear()
                                        get_order_items.clear_cache() # Clear all order item caches
                                        st.rerun() 
                                    else:
                                        st.error("Failed to create order.")
                            except Exception as e:
                                st.error(f"Error placing order: {e}")
                                st.info("This is likely due to the 'trg_CheckStockBeforeOrder' trigger. Stock may have changed.")

    with sub_tab_s_view:
        st.subheader("All Placed Orders")
        
        def update_order_status(order_id, new_status):
            try:
                query = text("CALL sp_UpdateOrderStatus(:id, :status);")
                with conn.session as s:
                    s.execute(query, {"id": order_id, "status": new_status})
                    s.commit()
                st.toast(f"Status updated for Order {order_id}")
                get_orders.clear()
            except Exception as e:
                st.error(f"Error updating status: {e}")
        
        try:
            orders_df = get_orders()
            
            if orders_df.empty:
                st.info("No orders found.")
            else:
                for index, row in orders_df.iterrows():
                    with st.expander(f"**Order #{row['OrderID']}** - {row['Customer']} - **${row['TotalAmount']:.2f}** ({row['Status']})"):
                        
                        col1, col2 = st.columns([2,1])
                        with col1:
                            st.write(f"**Order Date:** {row['OrderDate'].strftime('%Y-%m-%d')}")
                            
                            items_df = get_order_items(row['OrderID'])
                            st.dataframe(items_df, use_container_width=True)
                        
                        with col2:
                            status_options = ["Pending", "Processing", "Shipped", "Cancelled"]
                            current_status_index = status_options.index(row['Status']) if row['Status'] in status_options else 0
                            
                            new_status = st.selectbox(
                                "Update Status",
                                status_options,
                                index=current_status_index,
                                key=f"order_status_{row['OrderID']}"
                            )
                            st.button(
                                "Save Order Status", 
                                key=f"save_order_status_{row['OrderID']}",
                                on_click=update_order_status,
                                args=(row['OrderID'], new_status)
                            )

        except Exception as e:
            st.error(f"Error fetching orders: {e}")


# --- TAB 4: ADMIN PANEL ---
with tab_admin:
    st.header("Site Administration")
    
    sub_tab_m_mech, sub_tab_m_serv, sub_tab_m_part = st.tabs(["Manage Mechanics", "Manage Services", "Manage Parts"])
    
    with sub_tab_m_mech:
        def delete_mechanic(mechanic_id_to_delete):
            try:
                query = text("DELETE FROM mechanics WHERE MechanicID = :id;")
                with conn.session as s:
                    s.execute(query, {"id": mechanic_id_to_delete})
                    s.commit()
                st.toast(f"Successfully deleted mechanic ID: {mechanic_id_to_delete}")
                get_mechanics.clear()
            except Exception as e:
                st.error(f"Error deleting mechanic: {e}")
                if 'foreign key constraint' in str(e).lower():
                    st.warning(f"Cannot delete mechanic {mechanic_id_to_delete}: They are assigned to an appointment.")

        col1, col2 = st.columns([0.6, 0.4])
        with col1:
            st.subheader("Current Mechanics")
            try:
                mechanics_df = get_mechanics()
                if mechanics_df.empty:
                    st.info("No mechanics found.")
                else:
                    with st.container(border=True):
                        for index, mechanic in mechanics_df.iterrows():
                            row_col1, row_col2 = st.columns([4, 1])
                            with row_col1:
                                st.write(f"**{mechanic['FirstName']} {mechanic['LastName']}** (ID: {mechanic['MechanicID']})")
                                st.caption(f"Specialization: {mechanic['Specialization']}")
                            with row_col2:
                                st.button("Delete", key=f"del_mech_{mechanic['MechanicID']}", on_click=delete_mechanic, args=(mechanic['MechanicID'],))
                            if index < len(mechanics_df) - 1: st.divider()
            except Exception as e:
                st.error(f"Error fetching mechanics: {e}")
        with col2:
            st.subheader("Add a New Mechanic")
            with st.form("add_mechanic_form", clear_on_submit=True, border=True):
                first_name = st.text_input("First Name")
                last_name = st.text_input("Last Name")
                specialization = st.text_input("Specialization")
                submitted = st.form_submit_button("Add Mechanic")
                if submitted:
                    if not first_name or not last_name:
                        st.warning("First Name and Last Name are required.")
                    else:
                        try:
                            query = text("CALL sp_AddMechanic(:fname, :lname, :spec);")
                            with conn.session as s:
                                s.execute(query, {"fname": first_name, "lname": last_name, "spec": specialization})
                                s.commit()
                            st.toast(f"Added new mechanic: {first_name} {last_name}")
                            get_mechanics.clear()
                            st.rerun() 
                        except Exception as e:
                            st.error(f"Error adding mechanic: {e}")

    with sub_tab_m_serv:
        col1, col2 = st.columns([0.6, 0.4])
        with col1:
            st.subheader("Current Services")
            try:
                services_df = get_services()
                if services_df.empty:
                    st.info("No services found.")
                else:
                    st.dataframe(services_df, use_container_width=True)
            except Exception as e:
                st.error(f"Error fetching services: {e}")
        with col2:
            st.subheader("Add/Edit Service")
            
            services_list = list(get_services().itertuples(index=False, name=None))
            services_list.insert(0, ("NEW", "--- ADD NEW SERVICE ---", "", 0.0))
            
            selected_service_tuple = st.selectbox(
                "Select Service to Edit (or select NEW)",
                services_list,
                format_func=lambda x: x[1],
                key="edit_service_select"
            )
            is_new = selected_service_tuple[0] == "NEW"
            
            with st.form("service_form", border=True):
                name = st.text_input("Service Name", value="" if is_new else selected_service_tuple[1])
                desc = st.text_area("Description", value="" if is_new else selected_service_tuple[2])
                cost = st.number_input("Standard Cost", min_value=0.0, value=float(selected_service_tuple[3]), format="%.2f")
                submitted = st.form_submit_button("Save Service" if not is_new else "Add Service")
                
                if submitted:
                    try:
                        if is_new:
                            query = text("CALL sp_AddService(:name, :desc, :cost);")
                            with conn.session as s:
                                s.execute(query, {"name": name, "desc": desc, "cost": cost})
                                s.commit()
                            st.toast("Service added!")
                        else:
                            query = text("CALL sp_UpdateService(:id, :name, :desc, :cost);")
                            with conn.session as s:
                                s.execute(query, {"id": selected_service_tuple[0], "name": name, "desc": desc, "cost": cost})
                                s.commit()
                            st.toast("Service updated!")
                        get_services.clear()
                        st.rerun() 
                    except Exception as e:
                        st.error(f"Error saving service: {e}")

    with sub_tab_m_part:
        col1, col2 = st.columns([0.6, 0.4])
        with col1:
            st.subheader("Current Parts Inventory")
            try:
                parts_df = get_parts()
                if parts_df.empty:
                    st.info("No parts found.")
                else:
                    st.dataframe(parts_df, use_container_width=True)
            except Exception as e:
                st.error(f"Error fetching parts: {e}")
        with col2:
            st.subheader("Add/Edit Part")
            
            parts_list = list(get_parts().itertuples(index=False, name=None))
            parts_list.insert(0, ("NEW", "--- ADD NEW PART ---", "", 0.0, 0))
            
            selected_part_tuple = st.selectbox(
                "Select Part to Edit (or select NEW)",
                parts_list,
                format_func=lambda x: x[1],
                key="edit_part_select"
            )
            is_new = selected_part_tuple[0] == "NEW"
            
            with st.form("part_form", border=True):
                name = st.text_input("Part Name", value="" if is_new else selected_part_tuple[1])
                mfg = st.text_input("Manufacturer", value="" if is_new else selected_part_tuple[2])
                price = st.number_input("Price", min_value=0.0, value=float(selected_part_tuple[3]), format="%.2f")
                stock = st.number_input("Stock Quantity", min_value=0, value=int(selected_part_tuple[4]), step=1)
                submitted = st.form_submit_button("Save Part" if not is_new else "Add Part")
                
                if submitted:
                    try:
                        if is_new:
                            query = text("CALL sp_AddPart(:name, :mfg, :price, :stock);")
                            with conn.session as s:
                                s.execute(query, {"name": name, "mfg": mfg, "price": price, "stock": stock})
                                s.commit()
                            st.toast("Part added!")
                        else:
                            query = text("CALL sp_UpdatePart(:id, :name, :mfg, :price, :stock);")
                            with conn.session as s:
                                s.execute(query, {"id": selected_part_tuple[0], "name": name, "mfg": mfg, "price": price, "stock": stock})
                                s.commit()
                            st.toast("Part updated!")
                        get_parts.clear()
                        st.rerun() 
                    except Exception as e:
                        st.error(f"Error saving part: {e}")