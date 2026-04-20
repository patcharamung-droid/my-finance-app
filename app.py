import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

st.set_page_config(page_title="My Finance", layout="wide")

st.title("💰 ระบบบริหารการเงินส่วนตัว")

# สำหรับการบันทึกข้อมูลบน Cloud เราจะใช้การแสดงผลตารางให้ก๊อปปี้ไปวางใน Excel/Sheet ก่อน
# เพราะการเชื่อมต่อ Google Sheets แบบเขียนข้อมูลลงไปได้ทันทีต้องใช้คีย์ความลับ (Secrets) 
# ซึ่งเราจะทำเป็นขั้นถัดไปหลังจากแอปออนไลน์แล้วครับ

if 'data' not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=['Date', 'Type', 'Category', 'Amount', 'Note'])

# ส่วนเพิ่มข้อมูล
with st.sidebar:
    st.header("➕ เพิ่มรายการ")
    t_type = st.selectbox("ประเภท", ["Income", "Expense"])
    category = st.selectbox("หมวดหมู่", ["Food", "Travel", "Shopping", "Bills", "Salary"])
    amount = st.number_input("จำนวนเงิน", min_value=0.0)
    note = st.text_input("รายละเอียด")
    
    if st.button("บันทึก"):
        new_row = {'Date': datetime.now().strftime("%Y-%m-%d"), 'Type': t_type, 
                    'Category': category, 'Amount': amount, 'Note': note}
        st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_row])], ignore_index=True)
        st.success("บันทึกชั่วคราวสำเร็จ!")

# สรุปยอด
df = st.session_state.data
if not df.empty:
    income = df[df['Type'] == 'Income']['Amount'].sum()
    expense = df[df['Type'] == 'Expense']['Amount'].sum()
    
    c1, c2, c3 = st.columns(3)
    c1.metric("รายรับ", f"{income:,.2f}")
    c2.metric("รายจ่าย", f"{expense:,.2f}")
    c3.metric("คงเหลือ", f"{income-expense:,.2f}")

    st.write("### 📋 รายการทั้งหมด")
    st.dataframe(df)
else:
    st.info("ยังไม่มีข้อมูลบันทึกในเซสชั่นนี้")
