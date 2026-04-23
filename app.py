import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# ตั้งค่าหน้าจอ
st.set_page_config(page_title="My Finance Fixed", layout="wide")
st.title("💰 ระบบบันทึกรายรับ-รายจ่าย (ฉบับแก้ไข)")

# 1. เชื่อมต่อ Google Sheets
url = "ใส่_URL_ของ_GOOGLE_SHEET_คุณที่นี่"
conn = st.connection("gsheets", type=GSheetsConnection)

# 2. ฟังก์ชันดึงข้อมูลแบบ Real-time (บังคับไม่ใช้ Cache)
def get_data():
    return conn.read(spreadsheet=url, ttl=0)

df = get_data()

# --- ส่วนที่ 1: Dashboard (จะแสดงเมื่อมีข้อมูล) ---
if df is not None and not df.empty:
    # คลีนข้อมูล (ลบแถวว่าง/แปลงชนิดข้อมูล)
    df = df.dropna(subset=['Date', 'Amount'])
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce').fillna(0)
    
    # คำนวณยอดสรุป
    income = df[df['Type'] == 'Income']['Amount'].sum()
    expense = df[df['Type'] == 'Expense']['Amount'].sum()
    balance = income - expense

    # แสดง Metric
    c1, c2, c3 = st.columns(3)
    c1.metric("รายรับทั้งหมด", f"฿{income:,.2f}")
    c2.metric("รายจ่ายทั้งหมด", f"฿{expense:,.2f}")
    c3.metric("คงเหลือสุทธิ", f"฿{balance:,.2f}")

    st.write("---")
    
    # แสดงกราฟ
    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader("📊 สัดส่วนรายจ่าย")
        exp_df = df[df['Type'] == 'Expense']
        if not exp_df.empty:
            cat_sum = exp_df.groupby('Category')['Amount'].sum()
            fig, ax = plt.subplots()
            ax.pie(cat_sum, labels=cat_sum.index, autopct='%1.1f%%', startangle=90)
            st.pyplot(fig)
    with col_r:
        st.subheader("📈 แนวโน้มรายวัน")
        if not exp_df.empty:
            daily = exp_df.groupby('Date')['Amount'].sum()
            st.line_chart(daily)
else:
    st.info("ยังไม่มีข้อมูลในระบบ หรือชื่อคอลัมน์ไม่ถูกต้อง (Date, Type, Category, Amount, Note)")

# --- ส่วนที่ 2: บันทึกข้อมูล (Sidebar) ---
with st.sidebar:
    st.header("➕ เพิ่มรายการ")
    t_date = st.date_input("วันที่", datetime.now())
    t_type = st.selectbox("ประเภท", ["Income", "Expense"])
    t_cat = st.selectbox("หมวดหมู่", ["Food", "Travel", "Shopping", "Bills", "Salary", "Other"])
    t_amt = st.number_input("จำนวนเงิน", min_value=0.0)
    t_note = st.text_input("รายละเอียด")
    
    if st.button("บันทึกข้อมูล"):
        # *** ขั้นตอนสำคัญ: ดึงข้อมูลล่าสุดจากชีตมาเก็บไว้ในตัวแปรอีกครั้งก่อนบันทึก ***
        current_df = get_data()
        
        new_row = pd.DataFrame([{
            'Date': t_date.strftime("%Y-%m-%d"),
            'Type': t_type,
            'Category': t_cat,
            'Amount': t_amt,
            'Note': t_note
        }])
        
        # รวมข้อมูลเก่า + ข้อมูลใหม่ (ป้องกันข้อมูลเดิมหาย)
        if current_df is not None and not current_df.empty:
            updated_df = pd.concat([current_df, new_row], ignore_index=True)
        else:
            updated_df = new_row
            
        # ส่งกลับไปที่ Google Sheets
        conn.update(spreadsheet=url, data=updated_df)
        
        st.success("บันทึกเรียบร้อย!")
        # บังคับรีเฟรชหน้าจอทันที
        st.rerun()

st.write("---")
st.write("### 📋 ประวัติรายการล่าสุด")
st.dataframe(df.sort_index(ascending=False) if not df.empty else df, use_container_width=True)
