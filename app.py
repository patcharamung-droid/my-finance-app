import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# 1. ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="My Finance Dashboard", layout="wide", page_icon="💰")
st.title("📊 My Personal Finance Dashboard")

# 2. เชื่อมต่อ Google Sheets
# หมายเหตุ: ตรวจสอบว่าในไฟล์ Google Sheet มีหัวตารางว่า: Date, Type, Category, Amount, Note
url = "https://docs.google.com/spreadsheets/d/1ClxM35IaY617QQ_2-RqRZR9dvq7r5SR7zjwU_rN55Us/edit?gid=0#gid=0"
conn = st.connection("gsheets", type=GSheetsConnection)

# 3. ดึงข้อมูล (ตั้งค่า ttl=0 เพื่อให้ดึงข้อมูลใหม่ล่าสุดเสมอ ไม่ใช้ค่าแคช)
df = conn.read(spreadsheet=url, ttl=0)

# --- ส่วนจัดการข้อมูลและแสดงผล ---
if df is not None and not df.empty:
    # คลีนข้อมูลป้องกัน Error
    df = df.dropna(subset=['Date', 'Amount'])
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce').fillna(0)
    df = df.dropna(subset=['Date']) # ลบแถวที่วันที่ผิดพลาดออก

    # คำนวณรายรับ-รายจ่าย
    income_rows = df[df['Type'] == 'Income']
    expense_rows = df[df['Type'] == 'Expense']
    
    total_income = income_rows['Amount'].sum() if not income_rows.empty else 0.0
    total_expense = expense_rows['Amount'].sum() if not expense_rows.empty else 0.0
    balance = total_income - total_expense

    # --- ส่วนที่ 1: Metrics (ตัวเลขสรุป) ---
    st.write("### 💰 สรุปภาพรวม")
    c1, c2, c3 = st.columns(3)
    c1.metric("รายรับทั้งหมด", f"฿{total_income:,.2f}")
    c2.metric("รายจ่ายทั้งหมด", f"฿{total_expense:,.2f}", delta=f"-{total_expense:,.2f}", delta_color="inverse")
    c3.metric("คงเหลือสุทธิ", f"฿{balance:,.2f}")

    st.write("---")

    # --- ส่วนที่ 2: กราฟวิเคราะห์ ---
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("📊 สัดส่วนรายจ่าย (Expense)")
        if not expense_rows.empty:
            category_sum = expense_rows.groupby('Category')['Amount'].sum()
            fig1, ax1 = plt.subplots()
            ax1.pie(category_sum, labels=category_sum.index, autopct='%1.1f%%', startangle=90)
            st.pyplot(fig1)
        else:
            st.info("ยังไม่มีข้อมูลรายจ่ายเพื่อแสดงกราฟวงกลม")

    with col_right:
        st.subheader("📈 แนวโน้มการใช้เงินรายวัน")
        if not expense_rows.empty:
            daily_trend = expense_rows.groupby('Date')['Amount'].sum()
            st.line_chart(daily_trend)
        else:
            st.info("ยังไม่มีข้อมูลรายจ่ายเพื่อแสดงกราฟเส้น")
else:
    st.warning("⚠️ ไม่พบข้อมูล หรือหัวตารางใน Google Sheets ไม่ถูกต้อง (ต้องมี Date, Type, Category, Amount, Note)")

# --- ส่วนที่ 3: แถบข้างสำหรับบันทึกข้อมูล (Sidebar) ---
with st.sidebar:
    st.header("➕ เพิ่มรายการใหม่")
    t_type = st.selectbox("ประเภท", ["Income", "Expense"])
    category = st.selectbox("หมวดหมู่", ["Food", "Travel", "Shopping", "Bills", "Salary", "Gift", "Other"])
    amount = st.number_input("จำนวนเงิน (บาท)", min_value=0.0, step=100.0)
    note = st.text_input("รายละเอียด/หมายเหตุ")
    
    if st.button("บันทึกข้อมูลลงระบบ"):
        # สร้างข้อมูลใหม่
        new_row = pd.DataFrame([{
            'Date': datetime.now().strftime("%Y-%m-%d"),
            'Type': t_type, 
            'Category': category, 
            'Amount': amount, 
            'Note': note
        }])
        
        # รวมข้อมูลเดิมที่มีอยู่กับข้อมูลใหม่
        updated_df = pd.concat([df, new_row], ignore_index=True) if not df.empty else new_row
        
        # อัปเดตกลับไปยัง Google Sheets
        conn.update(spreadsheet=url, data=updated_df)
        
        st.success("✅ บันทึกสำเร็จ!")
        # สั่งให้แอปรีโหลดตัวเองทันทีเพื่อดึงข้อมูลใหม่มาแสดงบน Dashboard
        st.rerun()

# --- ส่วนที่ 4: ตารางประวัติ ---
st.write("---")
st.write("### 📋 ประวัติรายการล่าสุด")
if not df.empty:
    # แสดงตารางโดยเรียงจากรายการล่าสุดอยู่บน
    st.dataframe(df.sort_values(by='Date', ascending=False), use_container_width=True)
