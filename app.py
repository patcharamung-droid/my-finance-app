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

# 2. ดึงข้อมูล (สร้างตัวแปร df)
df = conn.read(spreadsheet=url, ttl=0)

# 3. ส่วนการคำนวณและแสดง Dashboard (จะทำงานเมื่อมีข้อมูลเท่านั้น)
if df is not None and not df.empty:
    # คลีนข้อมูล
    df = df.dropna(subset=['Date', 'Amount'])
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce').fillna(0)
    df = df.dropna(subset=['Date'])

    # คำนวณรายรับ-รายจ่าย
    income_rows = df[df['Type'] == 'Income']
    expense_rows = df[df['Type'] == 'Expense']
    
    total_income = income_rows['Amount'].sum() if not income_rows.empty else 0.0
    total_expense = expense_rows['Amount'].sum() if not expense_rows.empty else 0.0
    balance = total_income - total_expense

    # --- แสดงผล Dashboard ---
    st.write("### 💰 สรุปภาพรวมการเงิน")
    col1, col2, col3 = st.columns(3)
    col1.metric("รายรับทั้งหมด", f"฿{total_income:,.2f}")
    col2.metric("รายจ่ายทั้งหมด", f"฿{total_expense:,.2f}")
    col3.metric("คงเหลือสุทธิ", f"฿{balance:,.2f}")

    st.write("---")

    # ส่วนกราฟ
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📊 สัดส่วนรายจ่าย")
        if not expense_rows.empty:
            category_sum = expense_rows.groupby('Category')['Amount'].sum()
            fig1, ax1 = plt.subplots()
            ax1.pie(category_sum, labels=category_sum.index, autopct='%1.1f%%', startangle=90)
            st.pyplot(fig1)
        else:
            st.info("ยังไม่มีข้อมูลรายจ่าย")

    with c2:
        st.subheader("📈 แนวโน้มรายวัน")
        if not expense_rows.empty:
            daily_trend = expense_rows.groupby('Date')['Amount'].sum()
            st.line_chart(daily_trend)
else:
    st.warning("⚠️ ไม่พบข้อมูลในระบบ หรือชื่อคอลัมน์ใน Google Sheets ไม่ถูกต้อง (Date, Type, Category, Amount, Note)")

# 4. ส่วนเพิ่มข้อมูล (Sidebar)
with st.sidebar:
    st.header("➕ เพิ่มรายการใหม่")
    t_type = st.selectbox("ประเภท", ["Income", "Expense"])
    category = st.selectbox("หมวดหมู่", ["Food", "Travel", "Shopping", "Bills", "Salary", "Other"])
    amount = st.number_input("จำนวนเงิน (บาท)", min_value=0.0, step=100.0)
    note = st.text_input("รายละเอียด")
    
    if st.button("บันทึกข้อมูล"):
        # บันทึกข้อมูลลง Google Sheet
        new_row = pd.DataFrame([{
            'Date': datetime.now().strftime("%Y-%m-%d"),
            'Type': t_type, 
            'Category': category, 
            'Amount': amount, 
            'Note': note
        }])
        updated_df = pd.concat([df, new_row], ignore_index=True) if not df.empty else new_row
        conn.update(spreadsheet=url, data=updated_df)
        st.success("บันทึกข้อมูลแล้ว!")
        st.rerun()

st.write("---")
st.write("### 📋 ประวัติรายการล่าสุด")
st.dataframe(df.sort_index(ascending=False) if not df.empty else df, use_container_width=True)
