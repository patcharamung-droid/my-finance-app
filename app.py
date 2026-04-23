import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# ตั้งค่าหน้าจอ
st.set_page_config(page_title="My Finance Fixed", layout="wide")
st.title("💰 ระบบบันทึกรายรับ-รายจ่าย (ฉบับแก้ไข)")

# 1. เชื่อมต่อ Google Sheets
url = "https://docs.google.com/spreadsheets/d/1ClxM35IaY617QQ_2-RqRZR9dvq7r5SR7zjwU_rN55Us/edit?gid=0#gid=0"
conn = st.connection("gsheets", type=GSheetsConnection)

# 2. ฟังก์ชันดึงข้อมูลแบบ Real-time (บังคับไม่ใช้ Cache)
def get_data():
    return conn.read(spreadsheet=url, ttl=0)

df = get_data()

# --- ส่วนที่ 1: Dashboard (จะแสดงเมื่อมีข้อมูล) ---
if df is not None and not df.empty:
    # 1. ลบแถวที่ไม่มีข้อมูลวันที่หรือจำนวนเงินออกก่อน
    df = df.dropna(subset=['Date', 'Amount'])
    
    # 2. แปลงวันที่ให้เป็นรูปแบบ Datetime ของ Python (หัวใจสำคัญ)
    # errors='coerce' จะช่วยให้ถ้าเจอข้อมูลวันที่ผิดรูปแบบ มันจะไม่พังแต่จะข้ามไปแทน
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    
    # 3. ลบแถวที่แปลงวันที่ไม่สำเร็จออก
    df = df.dropna(subset=['Date'])
    
    # 4. แปลงวันที่เป็น "วันที่อย่างเดียว" (ไม่มีเวลามาพ่วง) เพื่อให้กราฟรวมกลุ่มได้ง่าย
    df['Date'] = df['Date'].dt.date 
    
    # 5. แปลงจำนวนเงินให้เป็นตัวเลข
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce').fillna(0)

    # --- ส่วนแสดงผล Dashboard ---
    # (ใช้ df ที่ผ่านการ Clean ด้านบนไปคำนวณต่อ)
    income = df[df['Type'] == 'Income']['Amount'].sum()
    expense = df[df['Type'] == 'Expense']['Amount'].sum()
    
    # กราฟแนวโน้มรายวัน (Daily Trend)
    st.subheader("📈 แนวโน้มการใช้เงินรายวัน")
    exp_df = df[df['Type'] == 'Expense']
    if not exp_df.empty:
        # จัดกลุ่มตามวันที่และรวมยอดเงิน
        daily_trend = exp_df.groupby('Date')['Amount'].sum()
        st.line_chart(daily_trend)

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
