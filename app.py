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
if not df.empty:
    # 1. คลีนข้อมูล (สำคัญมาก)
    df = df.dropna(subset=['Date', 'Amount'])
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce').fillna(0)
    df = df.dropna(subset=['Date'])

    # 2. คำนวณค่า (ต้องคำนวณก่อนนำไปแสดงใน Metric)
    income_rows = df[df['Type'] == 'Income']
    expense_rows = df[df['Type'] == 'Expense']
    
    total_income = income_rows['Amount'].sum() if not income_rows.empty else 0.0
    total_expense = expense_rows['Amount'].sum() if not expense_rows.empty else 0.0
    balance = total_income - total_expense

    # 3. แสดง Metrics (ตัวเลขใหญ่)
    st.write("### 💰 สรุปภาพรวม")
    c1, c2, c3 = st.columns(3)
    c1.metric("รายรับทั้งหมด", f"฿{total_income:,.2f}")
    c2.metric("รายจ่ายทั้งหมด", f"฿{total_expense:,.2f}")
    c3.metric("คงเหลือ", f"฿{balance:,.2f}")

    st.write("---")

    # 4. แสดงกราฟ
    col_left, col_right = st.columns(2)
    with col_left:
        st.subheader("📊 สัดส่วนรายจ่าย")
        if not expense_rows.empty:
            category_sum = expense_rows.groupby('Category')['Amount'].sum()
            fig1, ax1 = plt.subplots()
            ax1.pie(category_sum, labels=category_sum.index, autopct='%1.1f%%', startangle=90)
            st.pyplot(fig1)
        else:
            st.info("ยังไม่มีข้อมูลรายจ่ายเพื่อแสดงกราฟ")

    with col_right:
        st.subheader("📈 แนวโน้มการใช้เงิน")
        if not expense_rows.empty:
            daily_trend = expense_rows.groupby('Date')['Amount'].sum()
            st.line_chart(daily_trend)
else:
    st.warning("⚠️ ไม่พบข้อมูลใน Google Sheets โปรดเพิ่มรายการแรกที่แถบด้านข้าง")

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
