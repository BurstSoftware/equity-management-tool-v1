import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import apscheduler.schedulers.background
from apscheduler.triggers.date import DateTrigger
import io

# Initialize session state for cap table and vesting schedules
if 'cap_table' not in st.session_state:
    st.session_state.cap_table = pd.DataFrame({
        'Stakeholder': ['Founder A', 'Founder B', 'Investor X', 'Employee Y'],
        'Shares': [400000, 400000, 150000, 50000],
        'Type': ['Founder', 'Founder', 'Investor', 'Employee'],
        'Vesting Start': ['2023-01-01', '2023-01-01', None, '2024-01-01'],
        'Vesting Duration (Years)': [4, 4, None, 4],
        'Vested Shares': [0, 0, None, 0]
    })

if 'vesting_alerts' not in st.session_state:
    st.session_state.vesting_alerts = []

# Function to calculate vested shares
def calculate_vested_shares(row, current_date):
    if pd.isna(row['Vesting Start']) or pd.isna(row['Vesting Duration (Years)']):
        return row['Shares']
    vesting_start = datetime.strptime(row['Vesting Start'], '%Y-%m-%d')
    duration_years = row['Vesting Duration (Years)']
    months_passed = (current_date - vesting_start).days / 30.42  # Approximate months
    if months_passed <= 0:
        return 0
    fraction_vested = min(months_passed / (duration_years * 12), 1)
    return int(row['Shares'] * fraction_vested)

# Function to simulate vesting alerts
def check_vesting_alerts():
    current_date = datetime.now()
    for idx, row in st.session_state.cap_table.iterrows():
        if pd.notna(row['Vesting Start']) and pd.notna(row['Vesting Duration (Years)']):
            vesting_start = datetime.strptime(row['Vesting Start'], '%Y-%m-%d')
            months = int((current_date - vesting_start).days / 30.42)
            if months > 0 and months % 12 == 0:  # Alert annually
                st.session_state.vesting_alerts.append(
                    f"{row[' Stakeholder']} has vested {calculate_vested_shares(row, current_date)} shares as of {current_date.strftime('%Y-%m-%d')}"
                )

# Streamlit app
st.title("Equity Management Tool")

# Sidebar for navigation
st.sidebar.header("Navigation")
page = st.sidebar.radio("Go to", ["Cap Table Management", "Vesting Schedules", "Dilution Analysis", "Legal Documents", "Reports"])

# Cap Table Management
if page == "Cap Table Management":
    st.header("Cap Table Management")
    
    # Form to add new stakeholder
    with st.form("add_stakeholder"):
        stakeholder = st.text_input("Stakeholder Name")
        shares = st.number_input("Shares", min_value=0, step=1000)
        stakeholder_type = st.selectbox("Type", ["Founder", "Investor", "Employee"])
        vesting_start = st.date_input("Vesting Start Date (optional)", value=None)
        vesting_duration = st.number_input("Vesting Duration (Years, optional)", min_value=0.0, step=0.5, value=0.0)
        submitted = st.form_submit_button("Add Stakeholder")
        
        if submitted:
            new_row = {
                'Stakeholder': stakeholder,
                'Shares': shares,
                'Type': stakeholder_type,
                'Vesting Start': vesting_start.strftime('%Y-%m-%d') if vesting_start else None,
                'Vesting Duration (Years)': vesting_duration if vesting_duration > 0 else None,
                'Vested Shares': 0
            }
            st.session_state.cap_table = pd.concat([st.session_state.cap_table, pd.DataFrame([new_row])], ignore_index=True)
            st.success("Stakeholder added!")

    # Display cap table
    st.subheader("Current Cap Table")
    st.dataframe(st.session_state.cap_table)

    # Ownership visualization
    total_shares = st.session_state.cap_table['Shares'].sum()
    ownership = st.session_state.cap_table.groupby('Stakeholder')['Shares'].sum() / total_shares * 100
    fig = px.pie(values=ownership.values, names=ownership.index, title="Ownership Distribution")
    st.plotly_chart(fig)

# Vesting Schedules
elif page == "Vesting Schedules":
    st.header("Vesting Schedules")
    
    # Update vested shares
    current_date = datetime.now()
    st.session_state.cap_table['Vested Shares'] = st.session_state.cap_table.apply(
        lambda row: calculate_vested_shares(row, current_date), axis=1
    )
    
    # Display vesting schedules
    st.subheader("Vesting Details")
    st.dataframe(st.session_state.cap_table[['Stakeholder', 'Shares', 'Vesting Start', 'Vesting Duration (Years)', 'Vested Shares']])
    
    # Display vesting alerts
    st.subheader("Vesting Alerts")
    check_vesting_alerts()
    for alert in st.session_state.vesting_alerts:
        st.info(alert)

# Dilution Analysis
elif page == "Dilution Analysis":
    st.header("Dilution Analysis")
    
    # Input for new funding round
    new_shares = st.number_input("New Shares Issued", min_value=0, step=1000)
    new_investor = st.text_input("New Investor Name", "Investor Z")
    if st.button("Simulate Funding Round"):
        total_shares_before = st.session_state.cap_table['Shares'].sum()
        new_row = {
            'Stakeholder': new_investor,
            'Shares': new_shares,
            'Type': 'Investor',
            'Vesting Start': None,
            'Vesting Duration (Years)': None,
            'Vested Shares': new_shares
        }
        new_cap_table = pd.concat([st.session_state.cap_table, pd.DataFrame([new_row])], ignore_index=True)
        
        # Calculate ownership before and after
        ownership_before = st.session_state.cap_table.groupby('Stakeholder')['Shares'].sum() / total_shares_before * 100
        total_shares_after = new_cap_table['Shares'].sum()
        ownership_after = new_cap_table.groupby('Stakeholder')['Shares'].sum() / total_shares_after * 100
        
        # Visualize dilution
        st.subheader("Ownership Before Funding")
        fig_before = px.pie(values=ownership_before.values, names=ownership_before.index)
        st.plotly_chart(fig_before)
        
        st.subheader("Ownership After Funding")
        fig_after = px.pie(values=ownership_after.values, names=ownership_after.index)
        st.plotly_chart(fig_after)

# Legal Documents
elif page == "Legal Documents":
    st.header("Legal Documents")
    st.write("Upload shareholder agreements or other legal documents.")
    uploaded_file = st.file_uploader("Choose a file", type=['pdf', 'docx'])
    if uploaded_file:
        st.success(f"Uploaded {uploaded_file.name}")
        # Placeholder for document processing
        st.write("Document processing not implemented in this demo.")

# Reports
elif page == "Reports":
    st.header("Export Cap Table")
    st.write("Download the current cap table as a CSV file.")
    
    # Export to CSV
    csv = st.session_state.cap_table.to_csv(index=False)
    st.download_button(
        label="Download Cap Table",
        data=csv,
        file_name="cap_table.csv",
        mime="text/csv"
    )

# Footer
st.sidebar.write("Built with Streamlit | Equity Management Tool")
