import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import google.generativeai as genai

# --- 1. การตั้งค่าหน้าจอ ---
st.set_page_config(page_title="Smart Finance AI", layout="wide", page_icon="🤖")
st.title("💰 ระบบบันทึกรายรับ-รายจ่าย (AI Powered)")

# --- 2. ตั้งค่า AI Gemini (ใช้รุ่น 1.5-flash ตามที่คุณอัปเดต Library) ---
model = None
if "GEMINI_API_KEY" in st.secrets:
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        # ใช้รุ่นที่เสถียรที่สุดสำหรับเวอร์ชัน 0.5.0 ขึ้นไป
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
    except Exception as e:
        st.error(f"การตั้งค่า AI ผิดพลาด: {e}")
else:
    st.warning("❌ กรุณาตั้งค่า GEMINI_API_KEY ใน Streamlit Secrets")

# --- 3. การเชื่อมต่อ Google Sheets ---
url = "https://docs.google.com/spreadsheets/d/1ClxM35IaY617QQ_2-RqRZR9dvq7r5SR7zjwU_rN55Us/edit?gid=0#gid=0"
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    try:
        raw_df = conn.read(spreadsheet=url, ttl=0)
        if raw_df is not None and not raw_df.empty:
            raw_df = raw_df.dropna(subset=['Date', 'Amount'])
            raw_df['Date'] = pd.to_datetime(raw_df['Date'], errors='coerce')
            raw_df = raw_df.dropna(subset=['Date'])
            raw_df['Date'] = raw_df['Date'].dt.date
            raw_df['Amount'] = pd.to_numeric(raw_df['Amount'], errors='coerce').fillna(0)
            return raw_df
    except:
        return pd.DataFrame()
    return pd.DataFrame()

df = get_data()

# --- 4. ส่วน Dashboard ---
if not df.empty:
    income = df[df['Type'] == 'Income']['Amount'].sum()
    expense = df[df['Type'] == 'Expense']['Amount'].sum()
    balance = income - expense

    c1, c2, c3 = st.columns(3)
    c1.metric("รายรับทั้งหมด", f"฿{income:,.2f}")
    c2.metric("รายจ่ายทั้งหมด", f"฿{expense:,.2f}", delta=f"-{expense:,.2f}", delta_color="inverse")
    c3.metric("คงเหลือสุทธิ", f"฿{balance:,.2f}")

    # --- AI Financial Insights ---
    st.write("---")
    if st.button("✨ ให้ AI ช่วยวิเคราะห์กระเป๋าเงินเดือนนี้"):
        if model:
            with st.spinner('Gemini กำลังวิเคราะห์ข้อมูลของคุณ...'):
                try:
                    exp_df = df[df['Type'] == 'Expense']
                    cat_summary = exp_df.groupby('Category')['Amount'].sum().to_dict()
                    prompt = f"วิเคราะห์ข้อมูลการเงินนี้: รายรับ {income}, รายจ่าย {expense}, รายจ่ายแยกหมวดหมู่ {cat_summary}. บอกข้อดี 1 ข้อ และสิ่งที่ต้องระวัง 1 ข้อ สั้นๆ"
                    response = model.generate_content(prompt)
                    st.info(response.text)
                except Exception as e:
                    st.error(f"AI วิเคราะห์ไม่ได้: {e}")

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

# --- 5. ส่วนบันทึกข้อมูล (Sidebar) ---
with st.sidebar:
    st.header("➕ บันทึกรายการใหม่")
    t_date = st.date_input("วันที่", datetime.now())
    t_type = st.selectbox("ประเภท", ["Expense", "Income"])
    t_note = st.text_input("รายละเอียด (เช่น ซื้อข้าวกะเพรา)")
    
    # --- AI Auto-Category ---
    suggested_cat = "Other"
    if model and t_note:
        with st.spinner('AI กำลังเลือกหมวดหมู่...'):
            try:
                cat_prompt = f"จากข้อความ '{t_note}' เลือกหมวดหมู่ 1 คำจากรายการนี้: Food, Travel, Shopping, Bills, Salary, Other ตอบคำเดียวเท่านั้น"
                cat_res = model.generate_content(cat_prompt)
                suggested_cat = cat_res.text.strip()
            except:
                suggested_cat = "Other"

    categories = ["Food", "Travel", "Shopping", "Bills", "Salary", "Other"]
    default_index = categories.index(suggested_cat) if suggested_cat in categories else 5
    t_cat = st.selectbox("หมวดหมู่ (AI แนะนำ)", categories, index=default_index)
    t_amt = st.number_input("จำนวนเงิน", min_value=0.0, step=100.0)
    
    if st.button("บันทึกข้อมูล"):
        current_df = get_data()
        new_row = pd.DataFrame([{'Date': t_date.strftime("%Y-%m-%d"), 'Type': t_type, 'Category': t_cat, 'Amount': t_amt, 'Note': t_note}])
        updated_df = pd.concat([current_df, new_row], ignore_index=True) if not current_df.empty else new_row
        conn.update(spreadsheet=url, data=updated_df)
        st.success("บันทึกเรียบร้อย!")
        st.rerun()

# --- 6. ประวัติรายการ ---
st.write("---")
if not df.empty:
    st.dataframe(df.sort_values(by='Date', ascending=False), use_container_width=True)
