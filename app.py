import streamlit as st
import pandas as pd
import os
import io
import json
from datetime import date
from dateutil.relativedelta import relativedelta

# --- 1. DIRECTORY & PAGE CONFIG ---
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

# --- 3. LIBRARIES & DATABASE ---
TRADING_PL_HEADS = ["Sales", "Opening Stock", "Purchases", "Wages", "Direct Expenses", "Salaries", "Office Rent", "Audit Fees", "Depreciation", "Interest Received"]
BALANCE_SHEET_HEADS = ["Proprietor's Capital", "Secured Loans", "Unsecured Loans", "Sundry Creditors", "Sundry Debtors", "Cash-in-Hand", "Balance with Banks"]
DB_FILE = "client_database.json"

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f: return json.load(f)
        except: return {}
    return {}

if 'db' not in st.session_state: st.session_state.db = load_db()

# --- 4. SIDEBAR: CLIENT DOSSIER & KYC ---
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

# --- 5. MAIN INTERFACE TABS ---
st.title(f"⚖️ CA Practice & Loan Master: {company_name}")
st.markdown("**CA KAILASH MALI | Udaipur**")

t_input, t_analysis, t_eligibility, t_report = st.tabs(["📝 Input Sheet", "🧮 Cash Profit Analysis", "🏦 Loan Eligibility", "📈 Final Reports"])

# --- TAB 1: INPUT SHEET ---
with t_input:
    def load_template(form_type, firm_cat):
        file_path = f"templates/{firm_cat.replace(' ', '_')}_{form_type}.csv"
        if os.path.exists(file_path): return pd.read_csv(file_path)
        return pd.DataFrame({"Particulars": ["Sales", "Purchases", "Salaries", "Depreciation"], "Amount": [0.0]*4, "Add Back": [False]*4})
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Profit & Loss Account")
        pl_ed = st.data_editor(load_template("PL", firm_type), key=f"pl_{firm_type}", num_rows="dynamic", use_container_width=True,
                               column_config={"Particulars": st.column_config.SelectboxColumn("Account Head", options=TRADING_PL_HEADS)})
    with c2:
        st.subheader("Balance Sheet")
        bs_ed = st.data_editor(load_template("BS", firm_type), key=f"bs_{firm_type}", num_rows="dynamic", use_container_width=True,
                               column_config={"Particulars": st.column_config.SelectboxColumn("Account Head", options=BALANCE_SHEET_HEADS)})
    
    if st.button("🚀 SAVE CLIENT DATA"):
        file_path = f"saved_clients/{company_name.replace(' ', '_')}_{selected_fy}.csv"
        pd.concat([pl_ed, bs_ed], ignore_index=True).to_csv(file_path, index=False)
        st.success(f"Dossier for {company_name} saved!")

# --- TAB 2: CASH PROFIT ANALYSIS ---
with t_analysis:
    st.header("🧮 Average Cash Profit Calculation")
    years_to_avg = st.multiselect("Select years to include", ["2023-24", "2024-25", "2025-26"])
    if st.button("Calculate Average"):
        cp_vals = []
        for y in years_to_avg:
            path = f"saved_clients/{company_name.replace(' ', '_')}_{y}.csv"
            if os.path.exists(path):
                data = pd.read_csv(path)
                add_back = data[data['Add Back'] == True]['Amount'].sum()
                cp_vals.append(add_back) 
        if cp_vals: st.metric("Average Cash Profit", f"₹{sum(cp_vals)/len(cp_vals):,.2f}")

# --- TAB 3: LOAN ELIGIBILITY (Integrated Logic) ---
with t_eligibility:
    st.header("🏦 Integrated Loan Eligibility Assessment")
    
    # Auto-fetch data from P&L Input
    input_dep = pl_ed[pl_ed['Particulars'] == "Depreciation"]['Amount'].sum()
    input_np = pl_ed[pl_ed['Group'] == "Expense"]['Amount'].sum() # Example: Using Expense sum for NP logic
    
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        st.subheader("Income Details (Auto-Fetched)")
        net_profit = st.number_input("Net Profit (Current FY)", value=0.0)
        depreciation = st.number_input("Add Back: Depreciation", value=float(input_dep))
        cash_profit = net_profit + depreciation
        st.metric("Total Annual Cash Profit", f"₹{cash_profit:,.2f}")

    with col_e2:
        st.subheader("Running Obligations")
        num_other_emis = st.number_input("How many existing Monthly EMIs?", 0, 10, 0)
        total_other_emi = 0.0
        for k in range(int(num_other_emis)):
            total_other_emi += st.number_input(f"EMI {k+1} Amount", key=f"elig_emi_{k}")

    # Eligibility Logic
    st.divider()
    foir = st.slider("FOIR % (Fixed Obligation to Income Ratio)", 10, 100, 60)
    max_emi_allowed = (cash_profit / 12) * (foir / 100)
    net_eligible_emi = max(0.0, max_emi_allowed - total_other_emi)
    
    st.write(f"### Additional EMI Capacity: ₹{net_eligible_emi:,.2f}")
    
    r_p, t_p = st.columns(2)
    new_roi = r_p.number_input("Proposed Interest Rate (%)", value=9.5)
    new_tenure = t_p.number_input("Proposed Tenure (Years)", value=15)
    
    if net_eligible_emi > 0:
        r_v, n_v = (new_roi/12)/100, new_tenure * 12
        eligible_loan = net_eligible_emi * ((1 - (1 + r_v)**-n_v) / r_v)
        st.success(f"## Maximum Eligible Loan Amount: ₹{eligible_loan:,.0f}")

# --- TAB 4: FINAL REPORTS ---
with t_report:
    if st.button("📊 GENERATE BANK APPLICATION SUMMARY"):
        st.markdown(f'<div style="background-color:#5B9BD5;color:white;text-align:center;padding:10px;font-weight:bold;font-size:24px;">BANK LOAN APPLICATION DOSSIER</div>', unsafe_allow_html=True)
        st.write(f"**Client:** {company_name} | **FY:** {selected_fy}")
        st.subheader("Reference Details")
        refs = [{"Ref": f"Ref {r}", "Name": st.session_state.get(f"ref_name_{r}", ""), "Contact": st.session_state.get(f"ref_num_{r}", "")} for r in range(1, 4)]
        st.table(pd.DataFrame(refs))
