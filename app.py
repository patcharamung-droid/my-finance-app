import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

st.set_page_config(page_title="My Finance Dashboard", layout="wide")
st.title("📊 My Finance Dashboard")

# 1. เชื่อมต่อ Google Sheets
url = "https://docs.google.com/spreadsheets/d/1ClxM35IaY617QQ_2-RqRZR9dvq7r5SR7zjwU_rN55Us/edit?gid=0#gid=0"
conn = st.connection("gsheets", type=GSheetsConnection)

# ดึงข้อมูล
df = conn.read(spreadsheet=url, ttl=0)

if not df.empty:
    # --- ส่วนการจัดการข้อมูล (Data Cleaning) ---
    df = df.dropna(subset=['Date', 'Amount'])
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date'])
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce').fillna(0)

    # --- ส่วนที่ต้องเพิ่ม: คำนวณค่าต่างๆ ก่อนนำไปแสดงผล ---
    total_income = df[df['Type'] == 'Income']['Amount'].sum()
    total_expense = df[df['Type'] == 'Expense']['Amount'].sum()
    balance = total_income - total_expense

    # --- ส่วนที่ 1: ตัวเลขสรุป (Metrics) ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Income", f"฿{total_income:,.2f}")
    col2.metric("Total Expense", f"฿{total_expense:,.2f}", delta=f"-{total_expense:,.2f}", delta_color="inverse")
    col3.metric("Net Balance", f"฿{balance:,.2f}")

    st.write("---")

    # --- ส่วนที่ 2: กราฟวิเคราะห์ ---
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Expense Distribution")
        expense_df = df[df['Type'] == 'Expense']
        if not expense_df.empty:
            category_sum = expense_df.groupby('Category')['Amount'].sum()
            fig1, ax1 = plt.subplots(figsize=(5, 5))
            ax1.pie(category_sum, labels=category_sum.index, autopct='%1.1f%%', startangle=90)
            st.pyplot(fig1)
        else:
            st.info("No expense data to show.")

    with c2:
        st.subheader("Daily Spending Trend")
        if not expense_df.empty:
            daily_trend = expense_df.groupby('Date')['Amount'].sum().reset_index()
            st.line_chart(daily_trend.set_index('Date'))
        else:
            st.info("Add more data to see trends.")

# --- ส่วนที่ 3: ส่วนเพิ่มข้อมูล (Sidebar) ---
with st.sidebar:
    st.header("➕ Add Transaction")
    t_type = st.selectbox("Type", ["Income", "Expense"])
    category = st.selectbox("Category", ["Food", "Travel", "Shopping", "Bills", "Salary", "Gift", "Other"])
    amount = st.number_input("Amount (Baht)", min_value=0.0, step=100.0)
    note = st.text_input("Note")
    
    if st.button("บันทึกข้อมูล"):
        new_row = pd.DataFrame([{
            'Date': datetime.now().strftime("%Y-%m-%d"),
            'Type': t_type, 
            'Category': category, 
            'Amount': amount, 
            'Note': note
        }])
        updated_df = pd.concat([df, new_row], ignore_index=True)
        conn.update(spreadsheet=url, data=updated_df)
        st.success("บันทึกและอัปเดตกราฟเรียบร้อย!")
        st.rerun()

st.write("---")
st.write("### 📋 Recent History")
st.dataframe(df.sort_index(ascending=False), use_container_width=True)
