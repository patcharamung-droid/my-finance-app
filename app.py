import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import google.generativeai as genai

# --- 1. ตั้งค่าหน้าจอและ AI ---
st.set_page_config(page_title="AI Smart Finance", layout="wide")
st.title("💰 AI Personal Finance Dashboard")

if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.error("กรุณาตั้งค่า GEMINI_API_KEY ใน Streamlit Secrets")

# --- 2. เชื่อมต่อ Google Sheets ---
url = "https://docs.google.com/spreadsheets/d/1ClxM35IaY617QQ_2-RqRZR9dvq7r5SR7zjwU_rN55Us/edit?gid=0#gid=0"
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    raw_df = conn.read(spreadsheet=url, ttl=0)
    if raw_df is not None and not raw_df.empty:
        raw_df = raw_df.dropna(subset=['Date', 'Amount'])
        raw_df['Date'] = pd.to_datetime(raw_df['Date'], errors='coerce')
        raw_df = raw_df.dropna(subset=['Date'])
        raw_df['Amount'] = pd.to_numeric(raw_df['Amount'], errors='coerce').fillna(0)
    return raw_df

df = get_data()

# --- 3. แสดงผล Dashboard ---
if df is not None and not df.empty:
    income = df[df['Type'] == 'Income']['Amount'].sum()
    expense = df[df['Type'] == 'Expense']['Amount'].sum()
    balance = income - expense

    c1, c2, c3 = st.columns(3)
    c1.metric("รายรับรวม", f"฿{income:,.2f}")
    c2.metric("รายจ่ายรวม", f"฿{expense:,.2f}", delta=f"-{expense:,.2f}", delta_color="inverse")
    c3.metric("คงเหลือ", f"฿{balance:,.2f}")

    # กราฟ
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

    # --- 🤖 ฟีเจอร์ AI Advisor ---
    st.write("---")
    if st.button("✨ ให้ Gemini วิเคราะห์การเงินเดือนนี้"):
        with st.spinner('Gemini กำลังอ่านข้อมูล...'):
            cat_summary = exp_df.groupby('Category')['Amount'].sum().to_dict()
            prompt = f"รายรับ {income}, รายจ่าย {expense}, แยกหมวดหมู่: {cat_summary}. ช่วยวิเคราะห์และแนะนำ 3 ข้อ สั้นๆ ง่ายๆ"
            response = model.generate_content(prompt)
            st.info(response.text)

# --- 4. Sidebar เพิ่มข้อมูล ---
with st.sidebar:
    st.header("➕ บันทึกรายการ")
    t_date = st.date_input("วันที่", datetime.now())
    t_type = st.selectbox("ประเภท", ["Income", "Expense"])
    t_cat = st.selectbox("หมวดหมู่", ["Food", "Travel", "Shopping", "Bills", "Salary", "Other"])
    t_amt = st.number_input("จำนวนเงิน", min_value=0.0)
    
    if st.button("บันทึกข้อมูล"):
        current_df = get_data()
        new_row = pd.DataFrame([{'Date': t_date.strftime("%Y-%m-%d"), 'Type': t_type, 'Category': t_cat, 'Amount': t_amt}])
        updated_df = pd.concat([current_df, new_row], ignore_index=True) if not current_df.empty else new_row
        conn.update(spreadsheet=url, data=updated_df)
        st.success("บันทึกแล้ว!")
        st.rerun()

st.write("---")
st.dataframe(df.sort_values(by='Date', ascending=False) if not df.empty else df, use_container_width=True)
