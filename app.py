import streamlit as st
import pandas as pd
import os
import io
import json
from datetime import date
from dateutil.relativedelta import relativedelta

# --- 1. DIRECTORY & INITIAL SETUP ---
for folder in ["saved_clients", "templates"]:
    if not os.path.exists(folder):
        os.makedirs(folder)

st.set_page_config(page_title="CA Practice Manager - Final 2202", layout="wide", page_icon="⚖️")

# --- 2. DYNAMIC ZOOM & STYLING ---
if 'main_zoom' not in st.session_state: st.session_state.main_zoom = 18
with st.sidebar:
    st.header("🔍 View Settings")
    main_zoom = st.slider("Workspace Font Size", 10, 30, st.session_state.main_zoom)
    st.markdown(f"<style>[data-testid='stMain'] {{ font-size: {main_zoom}px !important; }}</style>", unsafe_allow_html=True)

# --- 3. LIBRARIES ---
TRADING_PL_HEADS = ["Sales", "Opening Stock", "Purchases", "Wages", "Direct Expenses", "Salaries", "Office Rent", "Audit Fees", "Depreciation", "Interest Received"]
BALANCE_SHEET_HEADS = ["Proprietor's Capital", "Secured Loans", "Unsecured Loans", "Sundry Creditors", "Sundry Debtors", "Cash-in-Hand", "Balance with Banks"]
IT_BLOCKS = {"Building (10%)": 0.10, "Furniture (10%)": 0.10, "Plant & Machinery (15%)": 0.15, "Computers (40%)": 0.40}

# --- 4. SIDEBAR: KYC, LOANS & REFERENCES ---
with st.sidebar:
    st.header("👤 Customer & KYC Dossier")
    company_name = st.text_input("Firm/Client Name", "M/s Rudra Earthmovers")
    selected_fy = st.selectbox("Financial Year", ["2023-24", "2024-25", "2025-26"])
    firm_type = st.selectbox("Firm Category", ["Trading Firm", "Service Provider", "Manufacturing"])

    num_applicants = st.number_input("Number of Applicants", 1, 10, 1)
    for i in range(int(num_applicants)):
        with st.expander(f"Applicant {i+1} Details", expanded=(i==0)):
            st.text_input(f"Name", key=f"app_name_{i}")
            st.date_input(f"DOB", key=f"app_dob_{i}")
            st.checkbox("Light Bill collected", key=f"lb_{i}")
            st.checkbox("Photo collected", key=f"ph_{i}")

    st.divider()
    st.header("📞 References")
    for r in range(1, 4):
        st.text_input(f"Ref {r} Name", key=f"ref_name_{r}")
        st.text_input(f"Ref {r} Contact", key=f"ref_num_{r}")

    st.divider()
    st.header("💳 Running Loans (EMIs)")
    num_loans = st.number_input("Existing Loans?", 0, 10, 0)
    total_existing_emi = 0.0
    for j in range(int(num_loans)):
        with st.expander(f"Loan {j+1}", expanded=False):
            st.text_input("Bank Name", key=f"ln_bnk_{j}")
            emi = st.number_input("Monthly EMI", key=f"emi_{j}")
            total_existing_emi += emi

# --- 5. MAIN INTERFACE TABS ---
st.title(f"⚖️ CA Practice & Loan Master: {company_name}")
st.markdown("**CA KAILASH MALI | Udaipur**")

t_input, t_analysis, t_eligibility, t_report = st.tabs(["📝 Input Sheet", "🧮 Cash Profit Analysis", "🏦 Loan Eligibility", "📈 Final Reports"])

# --- TAB 1: INPUT SHEET ---
with t_input:
    def load_template(form_type, firm_cat):
        file_path = f"templates/{firm_cat.replace(' ', '_')}_{form_type}.csv"
        if os.path.exists(file_path): return pd.read_csv(file_path)
        if form_type == "PL":
            # FIXED: Added 'Group' column back to prevent KeyError
            return pd.DataFrame({
                "Particulars": ["Sales", "Purchases", "Salaries", "Depreciation"], 
                "Group": ["Income", "Expense", "Expense", "Expense"], 
                "Amount": [0.0]*4, 
                "Add Back": [False]*4
            })
        return pd.DataFrame({"Particulars": ["Capital", "Sundry Creditors"], "Group": ["Liability", "Liability"], "Amount": [0.0]*2})
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Profit & Loss Account")
        pl_ed = st.data_editor(load_template("PL", firm_type), key=f"pl_ed", num_rows="dynamic", use_container_width=True,
                               column_config={"Particulars": st.column_config.SelectboxColumn("Account Head", options=TRADING_PL_HEADS)})
        if st.button("💾 Save Default P&L"):
            pl_ed.to_csv(f"templates/{firm_type.replace(' ', '_')}_PL.csv", index=False)
            st.success("Template Saved!")

    with c2:
        st.subheader("Balance Sheet")
        bs_ed = st.data_editor(load_template("BS", firm_type), key=f"bs_ed", num_rows="dynamic", use_container_width=True,
                               column_config={"Particulars": st.column_config.SelectboxColumn("Account Head", options=BALANCE_SHEET_HEADS)})
        if st.button("💾 Save Default BS"):
            bs_ed.to_csv(f"templates/{firm_type.replace(' ', '_')}_BS.csv", index=False)
            st.success("Template Saved!")

    if st.button("🚀 SAVE CLIENT DATA"):
        file_path = f"saved_clients/{company_name.replace(' ', '_')}_{selected_fy}.csv"
        pd.concat([pl_ed, bs_ed], ignore_index=True).to_csv(file_path, index=False)
        st.success(f"Dossier for {company_name} saved!")

# --- TAB 3: LOAN ELIGIBILITY ---
with t_eligibility:
    st.header("🏦 Loan Eligibility Assessment")
    # Fetch Data from PL table securely
    input_dep = pl_ed[pl_ed['Particulars'] == "Depreciation"]['Amount'].sum()
    
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        st.subheader("Income Analysis")
        # Let user override NP but pre-fill Dep
        net_profit = st.number_input("Annual Net Profit (NPBT)", value=0.0)
        depreciation = st.number_input("Depreciation (Auto-filled)", value=float(input_dep))
        cash_profit = net_profit + depreciation
        st.metric("Total Annual Cash Profit", f"₹{cash_profit:,.2f}")

    with col_e2:
        st.subheader("Obligations")
        st.metric("Total Monthly EMIs", f"₹{total_existing_emi:,.2f}")
        st.metric("Yearly Obligations", f"₹{total_existing_emi * 12:,.2f}")

    st.divider()
    foir = st.slider("FOIR % (Capacity)", 10, 100, 60)
    max_emi_cap = (cash_profit / 12) * (foir / 100)
    net_emi_eligible = max(0.0, max_emi_cap - total_existing_emi)
    
    st.write(f"### Eligible Additional Monthly EMI: ₹{net_emi_eligible:,.2f}")
    
    r_p, t_p = st.columns(2)
    roi = r_p.number_input("Bank ROI (%)", value=9.5)
    tenure = t_p.number_input("Tenure (Years)", value=15)
    
    if net_emi_eligible > 0:
        r_v = (roi/12)/100
        n_v = tenure * 12
        loan_amt = net_emi_eligible * ((1 - (1 + r_v)**-n_v) / r_v)
        st.success(f"## Estimated Loan Eligibility: ₹{loan_amt:,.0f}")
