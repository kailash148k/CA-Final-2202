import streamlit as st
import pandas as pd
import os
import io
import json
from datetime import date
from dateutil.relativedelta import relativedelta

# --- 1. SETUP & DIRECTORIES ---
for folder in ["saved_clients", "templates"]:
    if not os.path.exists(folder): os.makedirs(folder)

st.set_page_config(page_title="CA Practice Manager - Final 2202", layout="wide", page_icon="⚖️")

# --- 2. SIDEBAR: KYC & ITR ---
with st.sidebar:
    st.header("👤 Customer Dossier")
    company_name = st.text_input("Firm/Client Name", "M/s Rudra Earthmovers")
    selected_fy = st.selectbox("Financial Year", ["2023-24", "2024-25", "2025-26"])
    firm_type = st.selectbox("Category", ["Trading Firm", "Service Provider", "Manufacturing", "Salaried Individual"])
    itr_type = st.selectbox("ITR Type", ["ITR-1", "ITR-2", "ITR-3", "ITR-4"])

    num_apps = st.number_input("Applicants", 1, 10, 1)
    for i in range(int(num_apps)):
        with st.expander(f"Applicant {i+1}", expanded=(i==0)):
            st.text_input("Name", key=f"app_n_{i}")
            st.date_input("DOB", value=date(1990, 1, 1), min_value=date(1940, 1, 1), key=f"app_d_{i}")

# --- 3. RUNNING LOANS: INTEREST SYNC ENGINE ---
st.header("📊 1. Running Loan Analysis (Interest & Obligation)")
if 'detailed_loans' not in st.session_state: st.session_state.detailed_loans = []

if st.button("➕ Add Loan for Interest Analysis"):
    st.session_state.detailed_loans.append({"amt": 0.0, "roi": 9.0, "tenure": 120, "start": date(2023, 4, 1)})

total_active_emi = 0.0
total_interest_to_addback = 0.0

for idx, loan in enumerate(st.session_state.detailed_loans):
    with st.container(border=True):
        c1, c2, c3, c4, c5 = st.columns([2, 1, 1, 1, 1])
        bank = c1.text_input("Bank/Facility", key=f"bnk_{idx}")
        amt = c2.number_input("Loan Amt", key=f"amt_{idx}", value=loan['amt'])
        roi = c3.number_input("ROI %", key=f"roi_{idx}", value=loan['roi'])
        tenure = c4.number_input("Months", key=f"ten_{idx}", value=loan['tenure'])
        start_dt = c5.date_input("Start Date", key=f"sd_{idx}", value=loan['start'])

        # EMI Calculation
        r = (roi/12)/100
        emi = (amt * r * (1+r)**tenure) / ((1+r)**tenure - 1) if amt > 0 else 0.0
        
        o1, o2, o3 = st.columns([2, 2, 2])
        is_obligate = o1.checkbox("Obligate in FOIR? (Tick if open)", value=True, key=f"ob_{idx}")
        add_int_to_inc = o2.checkbox("Add Interest to Income? (Tick to Addback)", value=True, key=f"ai_{idx}")
        to_be_closed = o3.checkbox("To be Closed? (Untick EMI)", value=False, key=f"tc_{idx}")

        # Interest Portion for Current Year (Simplified Analysis)
        est_annual_interest = amt * (roi/100)
        
        if is_obligate and not to_be_closed:
            total_active_emi += emi
        if add_int_to_inc:
            total_interest_to_addback += est_annual_interest
        
        st.caption(f"Calculated EMI: ₹{emi:,.0f} | Est. Yearly Interest: ₹{est_annual_interest:,.0f}")

# --- 4. DATA ENTRY & ELIGIBILITY ---
st.divider()
t_input, t_eligibility = st.tabs(["📝 Input Sheet", "🏦 Loan Eligibility"])

with t_input:
    st.subheader("Profit & Loss Account")
    pl_ed = st.data_editor(pd.DataFrame({"Particulars": ["Sales", "Depreciation"], "Amount": [0.0, 0.0], "Add Back": [False, True]}), num_rows="dynamic", use_container_width=True)

with t_eligibility:
    st.header("🏦 Integrated Eligibility Assessment")
    
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        npbt = st.number_input("Annual NPBT (Net Profit)", value=0.0)
        dep = st.number_input("Depreciation (Addback)", value=float(pl_ed[pl_ed['Particulars']=="Depreciation"]['Amount'].sum()))
        # Automatically syncs the calculated interest from the loan engine
        sync_int = st.number_input("Interest Addback (Synced)", value=float(total_interest_to_addback))
        cash_profit = npbt + dep + sync_int
        st.metric("Adjusted Annual Cash Profit", f"₹{cash_profit:,.2f}")

    with col_e2:
        st.metric("Total Monthly EMI Obligations", f"₹{total_active_emi:,.2f}")
        foir = st.slider("FOIR %", 10, 100, 60)
    
    eligible_emi = max(0.0, ((cash_profit/12) * (foir/100)) - total_active_emi)
    st.success(f"### Additional Eligible Monthly EMI: ₹{eligible_emi:,.2f}")
