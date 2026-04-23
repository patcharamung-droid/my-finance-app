import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# ตั้งค่าหน้าจอ
st.set_page_config(page_title="My Finance Fixed", layout="wide")
st.title("💰 ระบบบันทึกรายรับ-รายจ่าย (Complete)")

# 1. เชื่อมต่อ Google Sheets
url = "https://docs.google.com/spreadsheets/d/1ClxM35IaY617QQ_2-RqRZR9dvq7r5SR7zjwU_rN55Us/edit?gid=0#gid=0"
conn = st.connection("gsheets", type=GSheetsConnection)

# 2. ฟังก์ชันดึงข้อมูลและคลีนข้อมูลในตัวเดียว
def get_data():
    raw_df = conn.read(spreadsheet=url, ttl=0)
    if raw_df is not None and not raw_df.empty:
        # ลบแถวว่างและจัดการวันที่/ตัวเลขทันที
        raw_df = raw_df.dropna(subset=['Date', 'Amount'])
        raw_df['Date'] = pd.to_datetime(raw_df['Date'], errors='coerce')
        raw_df = raw_df.dropna(subset=['Date'])
        raw_df['Date'] = raw_df['Date'].dt.date # แปลงเป็นวันที่อย่างเดียว
        raw_df['Amount'] = pd.to_numeric(raw_df['Amount'], errors='coerce').fillna(0)
    return raw_df

df = get_data()

# --- ส่วนที่ 1: Dashboard ---
if df is not None and not df.empty:
    # คำนวณยอดสรุป
    income = df[df['Type'] == 'Income']['Amount'].sum()
    expense = df[df['Type'] == 'Expense']['Amount'].sum()
    balance = income - expense

    # แสดง Metric (ตัวเลขสรุปด้านบน)
    c1, c2, c3 = st.columns(3)
    c1.metric("รายรับทั้งหมด", f"฿{income:,.2f}")
    c2.metric("รายจ่ายทั้งหมด", f"฿{expense:,.2f}", delta=f"-{expense:,.2f}", delta_color="inverse")
    c3.metric("คงเหลือสุทธิ", f"฿{balance:,.2f}")

    st.write("---")
    
    # แสดงกราฟ
    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader("📊 สัดส่วนรายจ่ายตามหมวดหมู่")
        exp_df = df[df['Type'] == 'Expense']
        if not exp_df.empty:
            cat_sum = exp_df.groupby('Category')['Amount'].sum()
            fig, ax = plt.subplots(figsize=(6, 4))
            ax.pie(cat_sum, labels=cat_sum.index, autopct='%1.1f%%', startangle=90)
            st.pyplot(fig)
        else:
            st.info("ยังไม่มีข้อมูลรายจ่าย")

    with col_r:
        st.subheader("📈 แนวโน้มการใช้เงินรายวัน")
        if not exp_df.empty:
            # รวมยอดรายวันเพื่อลากกราฟเส้น
            daily_trend = exp_df.groupby('Date')['Amount'].sum()
            st.line_chart(daily_trend)
        else:
            st.info("เพิ่มข้อมูลเพื่อดูแนวโน้ม")
else:
    st.info("💡 ยินดีต้อนรับ! เริ่มบันทึกรายการแรกได้ที่แถบด้านข้างครับ")

# --- ส่วนที่ 2: บันทึกข้อมูล (Sidebar) ---
with st.sidebar:
    st.header("➕ เพิ่มรายการ")
    t_date = st.date_input("วันที่", datetime.now())
    t_type = st.selectbox("ประเภท", ["Income", "Expense"])
    t_cat = st.selectbox("หมวดหมู่", ["Food", "Travel", "Shopping", "Bills", "Salary", "Other"])
    t_amt = st.number_input("จำนวนเงิน", min_value=0.0, step=100.0)
    t_note = st.text_input("รายละเอียด")
    
    if st.button("บันทึกข้อมูล"):
        # ดึงข้อมูลล่าสุดมาดูลูก่อนต่อท้าย (สำคัญป้องกันข้อมูลหาย)
        current_df = get_data()
        
        new_row = pd.DataFrame([{
            'Date': t_date.strftime("%Y-%m-%d"),
            'Type': t_type,
            'Category': t_cat,
            'Amount': t_amt,
            'Note': t_note
        }])
        
        if current_df is not None and not current_df.empty:
            updated_df = pd.concat([current_df, new_row], ignore_index=True)
        else:
            updated_df = new_row
            
        conn.update(spreadsheet=url, data=updated_df)
        st.success("✅ บันทึกเรียบร้อย!")
        st.rerun()

# --- ส่วนที่ 3: ประวัติรายการ ---
st.write("---")
st.write("### 📋 ประวัติรายการล่าสุด")
if df is not None and not df.empty:
    # เรียงตามวันที่ล่าสุดขึ้นก่อน
    st.dataframe(df.sort_values(by='Date', ascending=False), use_container_width=True)
