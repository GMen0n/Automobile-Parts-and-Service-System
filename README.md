# Auto Service Management System

![Python](https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.30.0-red?style=for-the-badge&logo=streamlit)
![MySQL](https://img.shields.io/badge/MySQL-8.0-orange?style=for-the-badge&logo=mysql)

A full-stack web application for an Auto Service & Parts Management System, built with Streamlit and MySQL. This is a mini-project for the Database Management System (UE23CS351A) course.

### Team Members
* **Gautam Menon** – PES2UG23CS196 https://github.com/GMen0n
* **C Vishwa** – PES2UG23CS139 https://github.com/C-VISHWA

---

## Key Features

* **Admin Dashboard:** A clean, multi-tab interface built with Streamlit for managing different aspects of the auto shop.
* **Full CRUD Functionality:** Complete Create, Read, and Delete operations for managing mechanics.
* **Advanced Database Logic:** Demonstrates the use of triggers, stored procedures, and functions to enforce business rules and data integrity.
* **Dynamic UI:** The "Current Mechanics" list updates in real-time (via `st.rerun()`) after a new mechanic is added or deleted.
* **Error Handling:** The app provides clear, user-friendly error messages (e.g., from the name-check trigger) and warnings (e.g., when trying to delete a mechanic assigned to an appointment).

---

## Tech Stack

* **Frontend:** **Streamlit** (for the web-based GUI)
* **Backend:** **Python**
* **Database:** **MySQL**
* **Core Libraries:** `streamlit`, `sqlalchemy`, `mysqlclient`

---

## Database Design & Advanced Features

The MySQL database schema features 8 tables: `customers`, `mechanics`, `services`, `parts`, `vehicles`, `orders`, `orderitems`, and `serviceappointments`.

This project implements advanced database features as required by the project rubrics:

### 1. Trigger: `trg_CheckMechanicName`
* **Purpose:** Enforces data integrity (a "business rule").
* **Action:** Fires `BEFORE INSERT` on the `mechanics` table.
* **Logic:** Checks if the new `FirstName` or `LastName` contains any numbers. If it does, the trigger raises a custom error ("Error: Mechanic name cannot contain numbers."), which is caught and displayed by the Streamlit app.

### 2. Stored Procedure: `sp_AddMechanic`
* **Purpose:** Encapsulates the logic for adding a new mechanic.
* **Action:** Takes `p_FirstName`, `p_LastName`, and `p_Specialization` as input parameters.
* **Logic:** Runs the `INSERT` command. The `trg_CheckMechanicName` trigger is automatically fired by this `INSERT`. The Streamlit app calls this procedure instead of running a raw `INSERT` query.

### 3. Function: `fn_GetMechanicDetails`
* **Purpose:** A utility function for data formatting.
* **Action:** Takes a mechanic's name and specialization as input.
* **Logic:** Returns a single, formatted string (e.g., "Carlos Ray (Engine Specialist)") that can be used in `SELECT` queries for display.

---

## Getting Started

Follow these instructions to set up and run the project locally.

### Prerequisites
* [Python 3.9+](https://www.python.org/)
* [MySQL Server](https://dev.mysql.com/downloads/mysql/) (Make sure the server is running)
* [Git](https://git-scm.com/)

### 1. Clone the Repository
```bash
git clone [https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git](https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git)
cd YOUR_REPO_NAME
```
### 2. Update secrets.toml with your SQL DB Information
```toml
username = "your sql username"
password = "your sql password"
```
### 3. Install streamlit 
```bash
pip install streamlit
```
### 4. Run the App
```python
streamlit run app.py
```
