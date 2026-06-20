"""
Appointment Management System - Streamlit Dashboard
Beautiful UI to test and manage appointments with automatic date format conversion
"""

import streamlit as st
import requests
import json
from datetime import datetime, timedelta
import pandas as pd
from typing import Dict, Any
import sys
sys.path.append('.')

# Import the date converter
try:
    from date_converter import (
        convert_to_backend_format,
        validate_future_date,
        detect_and_parse_datetime,
        validate_datetime_format
    )
except ImportError:
    st.error("❌ date_converter.py not found. Make sure it's in the same directory.")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="Appointment Manager",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        h1 { color: #6366f1; margin-bottom: 0.5rem; }
        h2 { color: #6366f1; border-bottom: 2px solid #e0e7ff; padding-bottom: 0.5rem; }
        
        .success-box {
            background-color: #d1fae5;
            border-left: 4px solid #10b981;
            padding: 1rem;
            border-radius: 0.5rem;
            margin: 1rem 0;
        }
        
        .error-box {
            background-color: #fee2e2;
            border-left: 4px solid #ef4444;
            padding: 1rem;
            border-radius: 0.5rem;
            margin: 1rem 0;
        }
        
        .info-box {
            background-color: #dbeafe;
            border-left: 4px solid #3b82f6;
            padding: 1rem;
            border-radius: 0.5rem;
            margin: 1rem 0;
        }
    </style>
""", unsafe_allow_html=True)

# API Configuration
API_BASE_URL = "http://127.0.0.1:5000"

# Session state initialization
if "last_response" not in st.session_state:
    st.session_state.last_response = None
if "error_message" not in st.session_state:
    st.session_state.error_message = None

# Header
st.markdown("""
    <div style='text-align: center; padding: 2rem; background: linear-gradient(135deg, #6366f1 0%, #ec4899 100%); 
    border-radius: 1rem; color: white; margin-bottom: 2rem;'>
        <h1 style='color: white; font-size: 2.5rem; margin: 0;'>📅 Appointment Manager</h1>
        <p style='font-size: 1.1rem; margin: 0.5rem 0 0 0; opacity: 0.9;'>Beautiful Dashboard with Automatic Date Conversion</p>
    </div>
""", unsafe_allow_html=True)

# API Status Check
def check_api_status():
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False

# Display API status
col1, col2, col3, col4 = st.columns(4)
with col1:
    api_status = check_api_status()
    status_text = "🟢 Connected" if api_status else "🔴 Disconnected"
    st.metric("API Status", status_text)

with col2:
    st.metric("Timezone", "IST (UTC+5:30)")

with col3:
    st.metric("Date Format", "YYYY-MM-DD")

with col4:
    st.metric("DateTime Format", "YYYY-MM-DD HH:MM AM/PM")

if not api_status:
    st.error("❌ Cannot connect to API. Make sure your FastAPI server is running on http://127.0.0.1:5000")
    st.stop()

st.success("✅ API Connected Successfully!")

# Sidebar navigation
st.sidebar.markdown("## 📋 Navigation")
page = st.sidebar.radio(
    "Select an operation:",
    [
        "📌 Dashboard",
        "➕ Schedule Appointment",
        "📑 List Appointments",
        "🔍 Search Patient",
        "✏️ Reschedule Appointment",
        "❌ Cancel Appointment",
        "🧪 Date Format Tester"
    ]
)

# ============ DASHBOARD PAGE ============
if page == "📌 Dashboard":
    st.markdown("## 📊 System Overview")
    
    today = datetime.now().strftime("%Y-%m-%d")
    
    try:
        response = requests.get(f"{API_BASE_URL}/list_appointments/", params={"date": today})
        
        if response.status_code == 200:
            data = response.json()
            total_appts = data.get("total_appointments", 0)
            appointments = data.get("appointments", [])
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("📅 Today", today)
            
            with col2:
                st.metric("👥 Total Appointments", total_appts)
            
            with col3:
                active = total_appts - sum(1 for a in appointments if a["canceled"])
                st.metric("✅ Active", active)
            
            with col4:
                canceled = sum(1 for a in appointments if a["canceled"])
                st.metric("❌ Canceled", canceled)
            
            if total_appts > 0:
                st.markdown("### 📋 Appointments Today")
                
                for appt in appointments:
                    with st.container():
                        col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
                        
                        with col1:
                            st.write(f"**👤 {appt['patient_name']}**")
                        
                        with col2:
                            st.write(f"📍 {appt['reason']}")
                        
                        with col3:
                            st.write(f"🕐 {appt['start_time']}")
                        
                        with col4:
                            if not appt["canceled"]:
                                st.write("✅ Active")
                            else:
                                st.write("❌ Canceled")
                        
                        st.divider()
            else:
                st.info("📭 No appointments scheduled for today")
        else:
            st.error(f"Error fetching appointments: {response.json()}")
    
    except Exception as e:
        st.error(f"Error: {str(e)}")

# ============ SCHEDULE APPOINTMENT PAGE ============
elif page == "➕ Schedule Appointment":
    st.markdown("## ➕ Schedule New Appointment")
    
    with st.form("schedule_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            patient_name = st.text_input(
                "Patient Name",
                placeholder="e.g., John Doe",
                help="Full name of the patient"
            )
        
        with col2:
            reason = st.text_input(
                "Reason for Appointment",
                placeholder="e.g., Check-up",
                help="Reason or type of appointment"
            )
        
        st.markdown("### 📅 Appointment Date & Time")
        st.info("ℹ️ Accept any date format! (e.g., 15-05-2026, 05/15/2026, May 15 2026, etc.)")
        
        date_input = st.text_input(
            "Date (Any Format)",
            placeholder="e.g., 2026-05-15 or 15-05-2026 or May 15, 2026",
            help="Can accept multiple formats - will auto-convert to YYYY-MM-DD"
        )
        
        time_input = st.text_input(
            "Time (Any Format)",
            placeholder="e.g., 14:30 or 02:30 PM or 2:30 PM",
            help="Can accept 24-hour or 12-hour (AM/PM) format"
        )
        
        submitted = st.form_submit_button("📅 Schedule Appointment", use_container_width=True)
    
    if submitted:
        # Validate inputs
        if not patient_name:
            st.error("❌ Please enter patient name")
        elif not reason:
            st.error("❌ Please enter reason for appointment")
        elif not date_input:
            st.error("❌ Please enter date")
        elif not time_input:
            st.error("❌ Please enter time")
        else:
            try:
                # Validate date/time format
                is_valid, validation_msg = validate_datetime_format(f"{date_input} {time_input}")
                
                if not is_valid:
                    st.warning(f"⚠️ Format check: {validation_msg}")
                    st.info("Trying to parse with available patterns...")
                
                # Convert to backend format
                try:
                    backend_datetime = convert_to_backend_format(date_input, time_input)
                    
                    st.info(f"✅ Converted format: `{backend_datetime}`")
                    
                    # Validate future date
                    is_future, future_msg = validate_future_date(date_input, time_input)
                    
                    if not is_future:
                        st.error(f"❌ {future_msg}")
                    else:
                        st.success(f"✅ {future_msg}")
                        
                        # Send to API
                        payload = {
                            "patient_name": patient_name,
                            "reason": reason,
                            "start_time": backend_datetime
                        }
                        
                        response = requests.post(
                            f"{API_BASE_URL}/schedule_appointments/",
                            json=payload
                        )
                        
                        if response.status_code == 201:
                            st.success("✅ Appointment scheduled successfully!")
                            st.json(response.json())
                        elif response.status_code == 409:
                            st.error(f"⚠️ Conflict: Patient already has appointment at this time")
                            st.json(response.json())
                        else:
                            st.error(f"❌ Error: {response.json()}")
                
                except ValueError as e:
                    st.error(f"❌ Date/Time parsing error: {str(e)}")
            
            except Exception as e:
                st.error(f"❌ Unexpected error: {str(e)}")

# ============ LIST APPOINTMENTS PAGE ============
elif page == "📑 List Appointments":
    st.markdown("## 📑 List Appointments by Date")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        date_input = st.text_input(
            "Enter Date (Any Format)",
            placeholder="e.g., 2026-05-15 or 15-05-2026 or May 15, 2026",
            help="Auto-converts any date format to YYYY-MM-DD"
        )
    
    with col2:
        st.write("")
        st.write("")
        search_btn = st.button("🔍 Search", use_container_width=True)
    
    if search_btn and date_input:
        try:
            # Convert to backend format (date only)
            backend_date = convert_to_backend_format(date_input, include_time=False)
            
            st.info(f"✅ Converted to: `{backend_date}`")
            
            # Fetch appointments
            response = requests.get(
                f"{API_BASE_URL}/list_appointments/",
                params={"date": backend_date}
            )
            
            if response.status_code == 200:
                data = response.json()
                total = data.get("total_appointments", 0)
                appointments = data.get("appointments", [])
                
                st.success(f"📊 Found {total} appointments on {backend_date}")
                
                if total > 0:
                    # Convert to DataFrame for display
                    df_data = []
                    for appt in appointments:
                        df_data.append({
                            "ID": appt["id"],
                            "Patient": appt["patient_name"],
                            "Reason": appt["reason"],
                            "Time": appt["start_time"],
                            "Status": "✅ Active" if not appt["canceled"] else "❌ Canceled",
                            "Created": appt["created_at"]
                        })
                    
                    df = pd.DataFrame(df_data)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("📭 No appointments found for this date")
            else:
                st.error(f"❌ Error: {response.json()}")
        
        except ValueError as e:
            st.error(f"❌ Date parsing error: {str(e)}")

# ============ SEARCH PATIENT PAGE ============
elif page == "🔍 Search Patient":
    st.markdown("## 🔍 Search Patient Appointments")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        patient_name = st.text_input(
            "Patient Name",
            placeholder="e.g., John Doe or John",
            help="Search for patient by full or partial name"
        )
    
    with col2:
        st.write("")
        st.write("")
        search_btn = st.button("🔍 Search", use_container_width=True)
    
    if search_btn and patient_name:
        try:
            response = requests.get(f"{API_BASE_URL}/search_appointments/{patient_name}")
            
            if response.status_code == 200:
                data = response.json()
                total = data.get("total_appointments", 0)
                appointments = data.get("appointments", [])
                
                st.success(f"📊 Found {total} upcoming appointments")
                
                if total > 0:
                    df_data = []
                    for appt in appointments:
                        df_data.append({
                            "ID": appt["id"],
                            "Date & Time": appt["start_time"],
                            "Reason": appt["reason"],
                            "Status": "✅ Active" if not appt["canceled"] else "❌ Canceled",
                            "Created": appt["created_at"]
                        })
                    
                    df = pd.DataFrame(df_data)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info(f"📭 No appointments found for {patient_name}")
            else:
                st.error(f"❌ Error: {response.json()}")
        
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

# ============ RESCHEDULE APPOINTMENT PAGE ============
elif page == "✏️ Reschedule Appointment":
    st.markdown("## ✏️ Reschedule Appointment")
    
    with st.form("reschedule_form"):
        appointment_id = st.number_input(
            "Appointment ID",
            min_value=1,
            help="ID of the appointment to reschedule"
        )
        
        st.markdown("### 📅 New Date & Time")
        st.info("ℹ️ Accept any date format!")
        
        date_input = st.text_input(
            "New Date (Any Format)",
            placeholder="e.g., 2026-05-20 or 20-05-2026"
        )
        
        time_input = st.text_input(
            "New Time (Any Format)",
            placeholder="e.g., 14:30 or 02:30 PM"
        )
        
        submitted = st.form_submit_button("✏️ Reschedule", use_container_width=True)
    
    if submitted:
        if not date_input or not time_input:
            st.error("❌ Please enter both date and time")
        else:
            try:
                # Convert to backend format
                backend_datetime = convert_to_backend_format(date_input, time_input)
                
                st.info(f"✅ Converted to: `{backend_datetime}`")
                
                # Validate future date
                is_future, future_msg = validate_future_date(date_input, time_input)
                
                if not is_future:
                    st.error(f"❌ {future_msg}")
                else:
                    st.success(f"✅ {future_msg}")
                    
                    # Send to API
                    response = requests.put(
                        f"{API_BASE_URL}/reschedule_appointment/{int(appointment_id)}",
                        params={"new_time": backend_datetime}
                    )
                    
                    if response.status_code == 200:
                        st.success("✅ Appointment rescheduled successfully!")
                        st.json(response.json())
                    else:
                        st.error(f"❌ Error: {response.json()}")
            
            except ValueError as e:
                st.error(f"❌ Date/Time parsing error: {str(e)}")

# ============ CANCEL APPOINTMENT PAGE ============
elif page == "❌ Cancel Appointment":
    st.markdown("## ❌ Cancel Appointment")
    
    cancel_method = st.radio(
        "Cancel by:",
        ["Appointment ID", "Patient Name & Date"]
    )
    
    if cancel_method == "Appointment ID":
        with st.form("cancel_by_id_form"):
            appointment_id = st.number_input(
                "Appointment ID",
                min_value=1
            )
            
            submitted = st.form_submit_button("❌ Cancel Appointment", use_container_width=True)
        
        if submitted:
            try:
                payload = {
                    "patient_name": "N/A",
                    "appointment_id": int(appointment_id)
                }
                
                response = requests.post(
                    f"{API_BASE_URL}/cancel_appointment/",
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    st.success(f"✅ {result.get('message')}")
                    st.json(result)
                else:
                    st.error(f"❌ Error: {response.json()}")
            
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    else:  # By Patient Name & Date
        with st.form("cancel_by_date_form"):
            patient_name = st.text_input("Patient Name")
            
            date_input = st.text_input(
                "Date (Any Format)",
                placeholder="e.g., 2026-05-15 or 15-05-2026"
            )
            
            submitted = st.form_submit_button("❌ Cancel Appointment(s)", use_container_width=True)
        
        if submitted:
            if not patient_name or not date_input:
                st.error("❌ Please enter both patient name and date")
            else:
                try:
                    # Convert to backend format (date only)
                    backend_date = convert_to_backend_format(date_input, include_time=False)
                    
                    st.info(f"✅ Converted date to: `{backend_date}`")
                    
                    payload = {
                        "patient_name": patient_name,
                        "date": backend_date
                    }
                    
                    response = requests.post(
                        f"{API_BASE_URL}/cancel_appointment/",
                        json=payload
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.success(f"✅ {result.get('message')}")
                        st.json(result)
                    else:
                        st.error(f"❌ Error: {response.json()}")
                
                except ValueError as e:
                    st.error(f"❌ Date parsing error: {str(e)}")

# ============ DATE FORMAT TESTER PAGE ============
elif page == "🧪 Date Format Tester":
    st.markdown("## 🧪 Date Format Converter Tester")
    
    st.info("""
    Test the date format converter to see how different formats are parsed and converted.
    The converter automatically detects and converts any date/time format to your backend format.
    """)
    
    st.markdown("### Test Different Date Formats")
    
    # Example formats
    examples = {
        "ISO Format": "2026-05-15",
        "US Format": "05/15/2026",
        "EU Format": "15-05-2026",
        "Text Format": "May 15, 2026",
        "Day Name": "Friday, May 15, 2026",
        "ISO DateTime": "2026-05-15 14:30:00",
        "US DateTime": "05/15/2026 02:30 PM",
        "EU DateTime": "15-05-2026 14:30",
        "Short Format": "15.05.2026",
        "Abbreviated": "15 May 2026"
    }
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Predefined Examples:**")
        selected_example = st.selectbox(
            "Choose an example:",
            list(examples.keys())
        )
        example_value = examples[selected_example]
        st.write(f"Input: `{example_value}`")
    
    with col2:
        st.markdown("**Or Test Custom Input:**")
        custom_input = st.text_input(
            "Enter any date format",
            placeholder="e.g., 2026-05-15 or 15-05-2026 or May 15, 2026"
        )
        test_input = custom_input if custom_input else example_value
    
    if st.button("🔄 Convert", use_container_width=True):
        try:
            # Test conversion
            result = convert_to_backend_format(test_input, include_time=False)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Input Format", test_input)
            
            with col2:
                st.write("")
                st.write("")
                st.write("➜")
            
            with col3:
                st.metric("Backend Format", result)
            
            st.success("✅ Format converted successfully!")
            
            # Show validation result
            is_valid, validation_msg = validate_future_date(test_input)
            if is_valid:
                st.success(f"✅ {validation_msg}")
            else:
                st.warning(f"⚠️ {validation_msg}")
        
        except Exception as e:
            st.error(f"❌ Conversion error: {str(e)}")
    
    st.markdown("### Supported Date Formats")
    
    formats = {
        "ISO": ["2026-05-15", "2026/05/15"],
        "US": ["05/15/2026", "05-15-2026"],
        "EU": ["15/05/2026", "15-05-2026"],
        "Text": ["May 15, 2026", "15 May 2026"],
        "DateTime": ["2026-05-15 14:30:00", "05/15/2026 02:30 PM"]
    }
    
    for category, format_list in formats.items():
        st.write(f"**{category}:** {', '.join(format_list)}")

st.sidebar.markdown("---")
st.sidebar.markdown("**About**")
st.sidebar.markdown("""
This dashboard provides a complete interface for managing appointments.
- Automatic date format conversion
- Support for multiple date/time formats
- Real-time API validation
- UTC/IST timezone handling
""")
