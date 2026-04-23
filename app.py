import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# --- การตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="Personal Finance V2", layout="wide")
st.title("💰 ระบบบันทึกรายรับ-รายจ่าย (Complete Version)")

# --- 1. เชื่อมต่อฐานข้อมูล ---
url = "ใส่_URL_ของ_GOOGLE_SHEET_คุณที่นี่"
conn = st.connection("gsheets", type=GSheetsConnection)

# ดึงข้อมูลใหม่ล่าสุดเสมอ (ttl=0)
df = conn.read(spreadsheet=url, ttl=0)

# --- 2. ส่วนการคำนวณ (Processing) ---
if df is not None and not df.empty:
    # คลีนข้อมูล
    df = df.dropna(subset=['Date', 'Amount'])
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce').fillna(0)
    df = df.dropna(subset=['Date'])

    # คำนวณยอด
    total_income = df[df['Type'] == 'Income']['Amount'].sum()
    total_expense = df[df['Type'] == 'Expense']['Amount'].sum()
    balance = total_income - total_expense

    # --- 3. ส่วนการแสดงผล (Dashboard) ---
    c1, c2, c3 = st.columns(3)
    c1.metric("รายรับทั้งหมด", f"฿{total_income:,.2f}")
    c2.metric("รายจ่ายทั้งหมด", f"฿{total_expense:,.2f}", delta=f"-{total_expense:,.2f}", delta_color="inverse")
    c3.metric("คงเหลือสุทธิ", f"฿{balance:,.2f}")

    st.write("---")
    
    col_left, col_right = st.columns(2)
    with col_left:
        st.subheader("📊 สัดส่วนรายจ่าย")
        exp_df = df[df['Type'] == 'Expense']
        if not exp_df.empty:
            cat_data = exp_df.groupby('Category')['Amount'].sum()
            fig, ax = plt.subplots()
            ax.pie(cat_data, labels=cat_data.index, autopct='%1.1f%%', startangle=90)
            st.pyplot(fig)
            
    with col_right:
        st.subheader("📈 แนวโน้มการใช้เงิน")
        if not exp_df.empty:
            daily = exp_df.groupby('Date')['Amount'].sum()
            st.line_chart(daily)
else:
    st.info("💡 เริ่มต้นใช้งานโดยการเพิ่มข้อมูลที่แถบด้านข้าง")

# --- 4. ส่วนการรับข้อมูล (Input Sidebar) ---
with st.sidebar:
    st.header("➕ เพิ่มรายการใหม่")
    t_date = st.date_input("วันที่", datetime.now())
    t_type = st.selectbox("ประเภท", ["Income", "Expense"])
    t_cat = st.selectbox("หมวดหมู่", ["Food", "Travel", "Shopping", "Bills", "Salary", "Gift", "Other"])
    t_amt = st.number_input("จำนวนเงิน", min_value=0.0, step=100.0)
    t_note = st.text_input("รายละเอียด")
    
    if st.button("บันทึกข้อมูล"):
        new_data = pd.DataFrame([{
            'Date': t_date.strftime("%Y-%m-%d"),
            'Type': t_type,
            'Category': t_cat,
            'Amount': t_amt,
            'Note': t_note
        }])
        updated_df = pd.concat([df, new_data], ignore_index=True) if not df.empty else new_data
        conn.update(spreadsheet=url, data=updated_df)
        st.success("บันทึกเรียบร้อย!")
        st.rerun()

st.write("---")
st.write("### 📋 ประวัติรายการ")
st.dataframe(df.sort_values(by='Date', ascending=False) if not df.empty else df, use_container_width=True)
