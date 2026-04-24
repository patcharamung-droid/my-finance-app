import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# --- 1. การตั้งค่าหน้าจอ ---
st.set_page_config(page_title="Smart Finance", layout="wide", page_icon="💰")
st.title("💰 ระบบบันทึกรายรับ-รายจ่าย")

# --- 2. การเชื่อมต่อ Google Sheets ---
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
# --- ส่วนตัวกรองข้อมูล (Sidebar Filters) ---
with st.sidebar:
    st.write("---")
    st.header("🔍 ตัวกรองข้อมูล")
    
    # 1. กรองตามช่วงวันที่
    if not df.empty:
        min_date = min(df['Date'])
        max_date = max(df['Date'])
        start_date, end_date = st.date_input(
            "เลือกช่วงเวลา",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
        
        # 2. กรองตามหมวดหมู่ (เลือกได้หลายหมวด)
        all_cats = df['Category'].unique().tolist()
        selected_cats = st.multiselect("เลือกหมวดหมู่", all_cats, default=all_cats)

        # นำตัวกรองมาใช้กับ DataFrame
        mask = (df['Date'] >= start_date) & (df['Date'] <= end_date) & (df['Category'].isin(selected_cats))
        filtered_df = df.loc[mask]
    else:
        filtered_df = df

# --- 3. ส่วน Dashboard ---
if not filtered_df.empty:
    income = filtered_df[filtered_df['Type'] == 'Income']['Amount'].sum()
    expense = filtered_df[filtered_df['Type'] == 'Expense']['Amount'].sum()
    balance = income - expense

    # แสดง Metric ที่เปลี่ยนไปตามตัวกรอง
    c1, c2, c3 = st.columns(3)
    c1.metric("รายรับ (ตามตัวกรอง)", f"฿{income:,.2f}")
    c2.metric("รายจ่าย (ตามตัวกรอง)", f"฿{expense:,.2f}")
    c3.metric("คงเหลือสุทธิ", f"฿{balance:,.2f}")

    # กราฟวงกลมที่เปลี่ยนตามตัวกรอง
    st.write("---")
    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader("📊 สัดส่วนรายจ่าย")
        if not exp_filtered.empty:
            cat_sum = exp_filtered.groupby('Category')['Amount'].sum()
            fig, ax = plt.subplots()
            ax.pie(cat_sum, labels=cat_sum.index, autopct='%1.1f%%', startangle=90)
            st.pyplot(fig)
    with col_r:
        st.subheader("📈 แนวโน้มรายวัน")
        if not exp_filtered.empty:
            daily = exp_filtered.groupby('Date')['Amount'].sum()
            st.line_chart(daily)

    # --- ส่วนที่เพิ่มใหม่: ตารางสรุปยอดเงินแต่ละรายการ ---
    st.write("### 📑 สรุปยอดเงินแยกตามหมวดหมู่")
    
    # แยกเฉพาะรายการที่เป็นรายจ่าย (Expense)
    exp_df = df[df['Type'] == 'Expense']
    
    if not exp_df.empty:
        # รวมยอดเงินแยกตามหมวดหมู่
        category_summary = exp_df.groupby('Category')['Amount'].sum().reset_index()
        # เปลี่ยนชื่อคอลัมน์ให้ดูง่าย
        category_summary.columns = ['หมวดหมู่', 'ยอดเงินรวม (บาท)']
        # เรียงลำดับจากมากไปน้อย
        category_summary = category_summary.sort_values(by='ยอดเงินรวม (บาท)', ascending=False)
        
        # แสดงผลเป็นตารางใน Streamlit
        st.table(category_summary.style.format({'ยอดเงินรวม (บาท)': '{:,.2f}'}))
    else:
        st.info("ยังไม่มีรายการรายจ่ายในขณะนี้")

# --- 4. ส่วนบันทึกข้อมูล (Sidebar) ---
with st.sidebar:
    st.header("➕ บันทึกรายการใหม่")
    t_date = st.date_input("วันที่", datetime.now())
    t_type = st.selectbox("ประเภท", ["Expense", "Income"])
    t_note = st.text_input("รายละเอียด (เช่น ซื้อข้าวกะเพรา)")
    
    # เปลี่ยนเป็นรายการให้เลือกแบบปกติ
    categories = ["Food", "Travel", "Shopping", "Bills", "Salary", "Other"]
    t_cat = st.selectbox("หมวดหมู่", categories)
    
    t_amt = st.number_input("จำนวนเงิน", min_value=0.0, step=100.0)
    
    if st.button("บันทึกข้อมูล"):
        if t_note and t_amt > 0:
            current_df = get_data()
            new_row = pd.DataFrame([{
                'Date': t_date.strftime("%Y-%m-%d"), 
                'Type': t_type, 
                'Category': t_cat, 
                'Amount': t_amt, 
                'Note': t_note
            }])
            updated_df = pd.concat([current_df, new_row], ignore_index=True) if not current_df.empty else new_row
            conn.update(spreadsheet=url, data=updated_df)
            st.success("บันทึกเรียบร้อย!")
            st.rerun()
        else:
            st.warning("กรุณากรอกรายละเอียดและจำนวนเงิน")

# --- 5. ประวัติรายการ ---
st.write("---")
if not df.empty:
    st.dataframe(df.sort_values(by='Date', ascending=False), use_container_width=True)

# --- 6. ประวัติรายการ (แสดงเฉพาะที่กรอง) ---
st.write("### 📜 ประวัติรายการที่เลือก")
if not filtered_df.empty:
    st.dataframe(filtered_df.sort_values(by='Date', ascending=False), use_container_width=True)
