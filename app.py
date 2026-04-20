import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="My Finance", layout="wide")
st.title("💰 ระบบบริหารการเงินส่วนตัว (Live)")

# 1. เชื่อมต่อกับ Google Sheets
# ใส่ URL ของชีตคุณตรงนี้
url = "1ClxM35IaY617QQ_2-RqRZR9dvq7r5SR7zjwU_rN55Us"
conn = st.connection("gsheets", type=GSheetsConnection)

# 2. ดึงข้อมูลมาแสดง
df = conn.read(spreadsheet=url)

# 3. ส่วนเพิ่มข้อมูล (Sidebar)
with st.sidebar:
    st.header("➕ เพิ่มรายการ")
    t_type = st.selectbox("ประเภท", ["Income", "Expense"])
    category = st.selectbox("หมวดหมู่", ["Food", "Travel", "Shopping", "Bills", "Salary"])
    amount = st.number_input("จำนวนเงิน", min_value=0.0)
    note = st.text_input("รายละเอียด")
    
    if st.button("บันทึก"):
        new_row = pd.DataFrame([{
            'Date': datetime.now().strftime("%Y-%m-%d"),
            'Type': t_type, 
            'Category': category, 
            'Amount': amount, 
            'Note': note
        }])
        # รวมข้อมูลเก่ากับใหม่
        updated_df = pd.concat([df, new_row], ignore_index=True)
        # เขียนกลับลงไปใน Google Sheets
        conn.update(spreadsheet=url, data=updated_df)
        st.success("บันทึกข้อมูลลง Google Sheet เรียบร้อย!")
        st.rerun()

# 4. แสดงผล Dashboard
if not df.empty:
    st.write("### 📊 รายการล่าสุด")
    st.dataframe(df.sort_index(ascending=False), use_container_width=True)
else:
    st.info("ยังไม่มีข้อมูลในระบบ")
