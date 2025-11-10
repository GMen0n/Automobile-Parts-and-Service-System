import streamlit as st
from sqlalchemy import text

# Set the page configuration (do this first!)
st.set_page_config(
    page_title="Auto Service Management",
    page_icon="🚗",
    layout="wide"
)

# --- DATABASE CONNECTION ---
# Connect to the database using the name from secrets.toml
try:
    conn = st.connection("autoservicedb", type="sql", ttl=10)
    st.success("Successfully connected to the database!")
except Exception as e:
    st.error(f"Error connecting to database: {e}")
    st.stop() # Stop the app if connection fails

# --- PAGE TITLE ---
st.title("🚗 Auto Service Management System")

# --- NAVIGATION TABS ---
# This is the biggest improvement!
tab1, tab2 = st.tabs(["👥 View Customers", "👨‍🔧 Manage Mechanics"])

# --- TAB 1: VIEW CUSTOMERS ---
with tab1:
    st.header("Admin View: All Customers (FR-3)")
    try:
        customers_df = conn.query("SELECT * FROM customers ORDER BY CustomerID;", ttl=0)
        st.dataframe(customers_df, use_container_width=True) # Fills the width
    except Exception as e:
        st.error(f"Error fetching customers: {e}")

# --- TAB 2: MANAGE MECHANICS ---
with tab2:
    st.header("Admin Panel: Manage Mechanics (FR-14)")

    # --- This is the Delete function ---
    def delete_mechanic(mechanic_id_to_delete):
        """Callback function to delete a mechanic."""
        try:
            query = text("DELETE FROM mechanics WHERE MechanicID = :id;")
            with conn.session as s:
                s.execute(query, {"id": mechanic_id_to_delete})
                s.commit()
            st.toast(f"✅ Successfully deleted mechanic ID: {mechanic_id_to_delete}")
        except Exception as e:
            st.error(f"Error deleting mechanic: {e}")
            if 'foreign key constraint' in str(e).lower():
                st.warning(f"Cannot delete mechanic {mechanic_id_to_delete}: They are assigned to an appointment.")

    # --- LAYOUT WITH COLUMNS ---
    # We'll put the list in col1 and the form in col2
    col1, col2 = st.columns([0.6, 0.4]) # 60% for list, 40% for form

    with col1:
        # 1. READ (Show all mechanics with delete buttons)
        st.subheader("Current Mechanics")
        try:
            mechanics_df = conn.query("SELECT * FROM mechanics ORDER BY MechanicID;", ttl=0)
            
            if mechanics_df.empty:
                st.info("No mechanics found in the database. Add one below.")
            else:
                # Use a container with a border for a cleaner look
                with st.container(border=True):
                    for index, mechanic in mechanics_df.iterrows():
                        # Create columns for layout
                        row_col1, row_col2 = st.columns([4, 1])
                        
                        with row_col1:
                            st.write(f"**{mechanic['FirstName']} {mechanic['LastName']}** (ID: {mechanic['MechanicID']})")
                            st.caption(f"Specialization: {mechanic['Specialization']}")
                        
                        with row_col2:
                            st.button(
                                "Delete",
                                key=f"delete_mechanic_{mechanic['MechanicID']}",
                                on_click=delete_mechanic,
                                args=(mechanic['MechanicID'],)
                            )
                        if index < len(mechanics_df) - 1: # Don't add divider after last item
                            st.divider()
                        
        except Exception as e:
            st.error(f"Error fetching mechanics: {e}")

    with col2:
        # 2. CREATE (Add a new mechanic via a form)
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
                            s.execute(query, {
                                "fname": first_name, 
                                "lname": last_name, 
                                "spec": specialization
                            })
                            s.commit()
                        
                        st.toast(f"✅ Added new mechanic: {first_name} {last_name}")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Error adding mechanic: {e}")