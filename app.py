import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import google.generativeai as genai

# --- 1. การตั้งค่าหน้าจอ (Page Config) ---
st.set_page_config(page_title="AI Smart Finance Dashboard", layout="wide", page_icon="💰")
st.title("📊 AI Personal Finance Dashboard")

# --- 2. การตั้งค่า AI Gemini ---
# ตรวจสอบว่ามี API Key ใน Secrets หรือไม่
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.error("❌ กรุณาตั้งค่า GEMINI_API_KEY ใน Streamlit Secrets ก่อนใช้งานระบบ AI")

# --- 3. การเชื่อมต่อ Google Sheets ---
# เปลี่ยน URL เป็นของไฟล์คุณ
url = "https://docs.google.com/spreadsheets/d/1ClxM35IaY617QQ_2-RqRZR9dvq7r5SR7zjwU_rN55Us/edit?gid=0#gid=0"
conn = st.connection("gsheets", type=GSheetsConnection)

# ฟังก์ชันดึงข้อมูลแบบ Real-time และ Clean ข้อมูลให้พร้อมใช้งาน
def get_data():
    try:
        raw_df = conn.read(spreadsheet=url, ttl=0)
        if raw_df is not None and not raw_df.empty:
            # คลีนข้อมูล: ลบแถวว่าง, แปลงวันที่, แปลงตัวเลข
            raw_df = raw_df.dropna(subset=['Date', 'Amount'])
            raw_df['Date'] = pd.to_datetime(raw_df['Date'], errors='coerce')
            raw_df = raw_df.dropna(subset=['Date'])
            raw_df['Date'] = raw_df['Date'].dt.date  # เก็บเฉพาะวันที่ ไม่เอาเวลา
            raw_df['Amount'] = pd.to_numeric(raw_df['Amount'], errors='coerce').fillna(0)
            return raw_df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการดึงข้อมูล: {e}")
        return pd.DataFrame()

# เรียกใช้งานฟังก์ชันดึงข้อมูล
df = get_data()

# --- 4. ส่วน Dashboard แสดงผล ---
if not df.empty:
    # คำนวณยอดสรุป
    income = df[df['Type'] == 'Income']['Amount'].sum()
    expense = df[df['Type'] == 'Expense']['Amount'].sum()
    balance = income - expense

    # แสดง Metric (ตัวเลขสรุป)
    st.write("### 💰 สรุปภาพรวมการเงิน")
    c1, c2, c3 = st.columns(3)
    c1.metric("รายรับรวม", f"฿{income:,.2f}")
    c2.metric("รายจ่ายรวม", f"฿{expense:,.2f}", delta=f"-{expense:,.2f}", delta_color="inverse")
    c3.metric("คงเหลือ", f"฿{balance:,.2f}")

    st.write("---")

    # ส่วนกราฟวิเคราะห์
    col_l, col_r = st.columns(2)
    exp_df = df[df['Type'] == 'Expense']

    with col_l:
        st.subheader("📊 สัดส่วนรายจ่าย")
        if not exp_df.empty:
            cat_sum = exp_df.groupby('Category')['Amount'].sum()
            fig, ax = plt.subplots(figsize=(6, 4))
            ax.pie(cat_sum, labels=cat_sum.index, autopct='%1.1f%%', startangle=90)
            st.pyplot(fig)
        else:
            st.info("ยังไม่มีข้อมูลรายจ่ายเพื่อแสดงกราฟ")

    with col_r:
        st.subheader("📈 แนวโน้มการใช้เงินรายวัน")
        if not exp_df.empty:
            daily_trend = exp_df.groupby('Date')['Amount'].sum()
            st.line_chart(daily_trend)
        else:
            st.info("เพิ่มข้อมูลรายจ่ายเพื่อดูแนวโน้ม")

    # --- 🤖 ส่วนของ AI Gemini Advisor ---
    st.write("---")
    st.header("✨ AI Financial Advisor")
    if st.button("ให้ Gemini วิเคราะห์การเงินของฉัน"):
        if "GEMINI_API_KEY" in st.secrets:
            with st.spinner('Gemini กำลังประมวลผลข้อมูล...'):
                # เตรียมข้อมูลสรุปส่งให้ AI
                cat_summary = exp_df.groupby('Category')['Amount'].sum().to_dict() if not exp_df.empty else "ไม่มีรายจ่าย"
                prompt = f"""
                คุณคือที่ปรึกษาการเงินส่วนตัว (Personal Finance Advisor) 
                นี่คือข้อมูลของฉัน:
                - รายรับรวม: {income} บาท
                - รายจ่ายรวม: {expense} บาท
                - ยอดคงเหลือ: {balance} บาท
                - รายจ่ายแยกตามหมวดหมู่: {cat_summary}
                
                ช่วยวิเคราะห์สถานะการเงินของฉัน และให้คำแนะนำที่นำไปใช้ได้จริง 3 ข้อ 
                พร้อมสรุปด้วย Emoji ให้ดูน่าอ่านและเป็นกันเอง
                """
                try:
                    response = model.generate_content(prompt)
                    st.info(response.text)
                except Exception as e:
                    st.error(f"AI เกิดข้อผิดพลาด: {e}")
        else:
            st.warning("กรุณาใส่ API Key ในระบบ Secrets ก่อนครับ")
else:
    st.info("💡 ยินดีต้อนรับ! เริ่มต้นโดยการบันทึกรายการแรกที่แถบด้านข้าง")

# --- 5. ส่วนบันทึกข้อมูล (Sidebar) ---
with st.sidebar:
    st.header("➕ เพิ่มรายการใหม่")
    t_date = st.date_input("วันที่", datetime.now())
    t_type = st.selectbox("ประเภท", ["Income", "Expense"])
    t_cat = st.selectbox("หมวดหมู่", ["🍔 Food", "🚗 Travel", "🛍️ Shopping", "📑 Bills", "💰 Salary", "🎁 Other"])
    t_amt = st.number_input("จำนวนเงิน (บาท)", min_value=0.0, step=100.0)
    t_note = st.text_input("รายละเอียด/หมายเหตุ")
    
    if st.button("บันทึกข้อมูล"):
        # ดึงข้อมูลล่าสุดมาก่อน (ป้องกันทับของเดิม)
        current_df = get_data()
        
        new_row = pd.DataFrame([{
            'Date': t_date.strftime("%Y-%m-%d"),
            'Type': t_type,
            'Category': t_cat,
            'Amount': t_amt,
            'Note': t_note
        }])
        
        # รวมข้อมูล
        if not current_df.empty:
            updated_df = pd.concat([current_df, new_row], ignore_index=True)
        else:
            updated_df = new_row
            
        # อัปเดตกลับไปที่ Google Sheets
        conn.update(spreadsheet=url, data=updated_df)
        st.success("✅ บันทึกข้อมูลเรียบร้อย!")
        st.rerun()

# --- 6. ส่วนตารางประวัติ ---
st.write("---")
st.write("### 📋 ประวัติรายการล่าสุด")
if not df.empty:
    st.dataframe(df.sort_values(by='Date', ascending=False), use_container_width=True)
