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

# --- 2. DYNAMIC ZOOM CONTROLS ---
if 'main_zoom' not in st.session_state: st.session_state.main_zoom = 18
with st.sidebar:
    st.header("🔍 View Settings")
    main_zoom = st.slider("Workspace Font Size", 10, 30, st.session_state.main_zoom)
    st.markdown(f"<style>[data-testid='stMain'] {{ font-size: {main_zoom}px !important; }}</style>", unsafe_allow_html=True)

# --- 3. LIBRARIES ---
TRADING_PL_HEADS = ["Sales", "Opening Stock", "Purchases", "Wages", "Direct Expenses", "Salaries", "Office Rent", "Audit Fees", "Depreciation", "Interest Received", "Commission Received"]
BALANCE_SHEET_HEADS = ["Proprietor's Capital", "Secured Loans", "Unsecured Loans", "Sundry Creditors", "Duties & Taxes", "Sundry Debtors", "Cash-in-Hand", "Balance with Banks", "Security Deposits"]

# --- 4. SIDEBAR: KYC & ITR ---
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
            st.text_input("Mobile", key=f"app_m_{i}")

    st.divider()
    st.header("📞 References")
    for r in range(1, 4):
        st.text_input(f"Ref {r} Name", key=f"ref_n_{r}")
        st.text_input(f"Ref {r} Mobile", key=f"ref_m_{r}")

# --- 5. RUNNING LOANS: INTEREST SYNC ENGINE ---
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
        ten = c4.number_input("Months", key=f"ten_{idx}", value=loan['tenure'])
        sd = c5.date_input("Start Date", key=f"sd_{idx}", value=loan['start'])

        r = (roi/12)/100
        emi = (amt * r * (1+r)**ten) / ((1+r)**ten - 1) if amt > 0 else 0.0
        est_annual_int = amt * (roi/100)

        o1, o2, o3 = st.columns(3)
        is_ob = o1.checkbox("Obligate in FOIR?", value=True, key=f"ob_{idx}")
        add_int = o2.checkbox("Add Interest to Inc?", value=True, key=f"ai_{idx}")
        to_close = o3.checkbox("To be Closed?", value=False, key=f"tc_{idx}")

        if is_ob and not to_close: total_active_emi += emi
        if add_int: total_interest_to_addback += est_annual_int
        st.caption(f"EMI: ₹{emi:,.0f} | Est. Yearly Interest: ₹{est_annual_int:,.0f}")

# --- 6. TEMPLATE LOADER ---
def load_template(form_type, firm_cat):
    file_path = f"templates/{firm_cat.replace(' ', '_')}_{form_type}.csv"
    if os.path.exists(file_path): return pd.read_csv(file_path)
    if form_type == "PL":
        return pd.DataFrame({"Particulars": ["Sales", "Purchases", "Salaries", "Depreciation"], "Group": ["Income", "Expense", "Expense", "Expense"], "Amount": [0.0]*4, "Add Back": [False, False, False, True]})
    return pd.DataFrame({"Particulars": ["Capital", "Sundry Creditors"], "Group": ["Liability", "Liability"], "Amount": [0.0]*2})

# --- 7. MAIN TABS ---
st.divider()
st.title(f"💼 Business & Eligibility Suite: {company_name}")
t_input, t_analysis, t_eligibility, t_report = st.tabs(["📝 Input Sheet", "🧮 Cash Profit Analysis", "🏦 Loan Eligibility", "📈 Final Reports"])

with t_input:
    st.subheader(f"Data Entry: {firm_type} ({itr_type})")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Profit & Loss**")
        pl_ed = st.data_editor(load_template("PL", firm_type), key="pl_main", num_rows="dynamic", use_container_width=True,
                               column_config={"Particulars": st.column_config.SelectboxColumn("Account Head", options=TRADING_PL_HEADS)})
        if st.button("💾 Save P&L Default"):
            pl_ed.to_csv(f"templates/{firm_type.replace(' ', '_')}_PL.csv", index=False)
            st.success("P&L Default Set!")
    with c2:
        st.markdown("**Balance Sheet**")
        bs_ed = st.data_editor(load_template("BS", firm_type), key="bs_main", num_rows="dynamic", use_container_width=True,
                               column_config={"Particulars": st.column_config.SelectboxColumn("Account Head", options=BALANCE_SHEET_HEADS)})
        if st.button("💾 Save BS Default"):
            bs_ed.to_csv(f"templates/{firm_type.replace(' ', '_')}_BS.csv", index=False)
            st.success("BS Default Set!")

    if st.button("🚀 SAVE CLIENT DOSSIER"):
        path = f"saved_clients/{company_name.replace(' ', '_')}_{selected_fy}.csv"
        pd.concat([pl_ed, bs_ed], ignore_index=True).to_csv(path, index=False)
        st.success(f"Dossier for {company_name} saved!")

with t_analysis:
    st.header("🧮 Average Cash Profit Calculation")
    years = st.multiselect("Select years to include", ["2022-23", "2023-24", "2024-25", "2025-26"])
    if st.button("Calculate Avg Cash Profit"):
        cp_results = []
        for y in years:
            p = f"saved_clients/{company_name.replace(' ', '_')}_{y}.csv"
            if os.path.exists(p):
                data = pd.read_csv(p)
                # Cash Profit = Net Profit + Items marked 'Add Back'
                # Note: This tool assumes users tick 'Add Back' for Dep and Int
                ab_amt = data[data['Add Back'] == True]['Amount'].sum()
                cp_results.append(ab_amt)
        if cp_results: st.metric("Average Cash Profit", f"₹{sum(cp_results)/len(cp_results):,.2f}")

with t_eligibility:
    st.header("🏦 Integrated Eligibility Assessment")
    dep_sync = pl_ed[pl_ed['Particulars'] == "Depreciation"]['Amount'].sum()
    
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        npbt = st.number_input("Annual Net Profit (NPBT)", value=0.0)
        dep_val = st.number_input("Depreciation (Synced)", value=float(dep_sync))
        int_sync = st.number_input("Interest (Synced from Loan Analysis)", value=float(total_interest_to_addback))
        cash_p = npbt + dep_val + int_sync
        st.metric("Adjusted Annual Cash Profit", f"₹{cash_p:,.2f}")

    with col_e2:
        st.metric("Monthly EMI Obligations", f"₹{total_active_emi:,.2f}")
        foir = st.slider("FOIR %", 10, 100, 60)
    
    eligible_emi = max(0.0, ((cash_p/12) * (foir/100)) - total_active_emi)
    st.divider()
    if eligible_emi > 0:
        st.success(f"### Additional EMI Eligibility: ₹{eligible_emi:,.2f}")
        r_p, t_p = st.columns(2)
        new_roi = r_p.number_input("Proposed ROI %", value=9.5)
        new_ten = t_p.number_input("Proposed Tenure (Years)", value=15)
        rv, nv = (new_roi/12)/100, new_ten * 12
        loan_eligible = eligible_emi * ((1 - (1 + rv)**-nv) / rv)
        st.success(f"## Estimated Loan Amount: ₹{loan_eligible:,.0f}")
    else: st.error("Negative Eligibility: Existing obligations exceed capacity.")

with t_report:
    if st.button("📊 GENERATE FINAL BANK SUMMARY"):
        st.markdown(f'<div style="background-color:#5B9BD5;color:white;text-align:center;padding:10px;font-weight:bold;font-size:24px;">BANK LOAN APPLICATION SUMMARY</div>', unsafe_allow_html=True)
        st.write(f"**Client:** {company_name} | **FY:** {selected_fy} | **Category:** {firm_type} ({itr_type})")
        st.subheader("Reference Checklist")
        ref_data = [{"Ref": f"Ref {r}", "Name": st.session_state.get(f"ref_n_{r}",""), "Mobile": st.session_state.get(f"ref_m_{r}","")} for r in range(1, 4)]
        st.table(pd.DataFrame(ref_data))
