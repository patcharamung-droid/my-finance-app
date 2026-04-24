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

# --- 3. ส่วนตัวกรองข้อมูล (Sidebar Filters) ---
with st.sidebar:
    st.header("➕ บันทึกรายการใหม่")
    t_date = st.date_input("วันที่", datetime.now())
    t_type = st.selectbox("ประเภท", ["Expense", "Income"])
    t_note = st.text_input("รายละเอียด (เช่น ซื้อข้าวกะเพรา)")
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

    st.write("---")
    st.header("🔍 ตัวกรองข้อมูล")
    if not df.empty:
        min_date = min(df['Date'])
        max_date = max(df['Date'])
        # ตัวเลือกช่วงวันที่
        date_range = st.date_input(
            "เลือกช่วงเวลา",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
        
        # กรองหมวดหมู่
        all_cats = sorted(df['Category'].unique().tolist())
        selected_cats = st.multiselect("เลือกหมวดหมู่", all_cats, default=all_cats)

        # ตรวจสอบการเลือกช่วงวันที่ (ป้องกัน error กรณีเลือกแค่วันเดียว)
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_date, end_date = date_range
            mask = (df['Date'] >= start_date) & (df['Date'] <= end_date) & (df['Category'].isin(selected_cats))
            filtered_df = df.loc[mask]
        else:
            filtered_df = df
    else:
        filtered_df = df

# --- 4. ส่วน Dashboard ---
if not filtered_df.empty:
    income = filtered_df[filtered_df['Type'] == 'Income']['Amount'].sum()
    expense = filtered_df[filtered_df['Type'] == 'Expense']['Amount'].sum()
    balance = income - expense

    # แสดง Metric
    c1, c2, c3 = st.columns(3)
    c1.metric("รายรับ", f"฿{income:,.2f}")
    c2.metric("รายจ่าย", f"฿{expense:,.2f}", delta=f"-{expense:,.2f}", delta_color="inverse")
    c3.metric("คงเหลือสุทธิ", f"฿{balance:,.2f}")

    st.write("---")
    col_l, col_r = st.columns([1, 1.5])
    
    with col_l:
        st.write("### 📑 สรุปยอดเงินรายจ่าย")
        exp_filtered = filtered_df[filtered_df['Type'] == 'Expense']
        if not exp_filtered.empty:
            cat_summary = exp_filtered.groupby('Category')['Amount'].sum().reset_index()
            cat_summary.columns = ['หมวดหมู่', 'รวม (บาท)']
            st.table(cat_summary.sort_values(by='รวม (บาท)', ascending=False).style.format({'รวม (บาท)': '{:,.2f}'}))
        else:
            st.info("ไม่มีข้อมูลรายจ่ายในช่วงนี้")

    with col_r:
        st.write("### 📊 สัดส่วนและแนวโน้ม")
        tab1, tab2 = st.tabs(["สัดส่วนรายจ่าย", "แนวโน้มรายวัน"])
        with tab1:
            if not exp_filtered.empty:
                cat_sum = exp_filtered.groupby('Category')['Amount'].sum()
                fig, ax = plt.subplots()
                ax.pie(cat_sum, labels=cat_sum.index, autopct='%1.1f%%', startangle=90)
                st.pyplot(fig)
        with tab2:
            if not exp_filtered.empty:
                daily = exp_filtered.groupby('Date')['Amount'].sum()
                st.line_chart(daily)

# --- 5. ประวัติรายการ ---
st.write("---")
st.write("### 📜 ประวัติรายการ (ตามตัวกรอง)")
if not filtered_df.empty:
    st.dataframe(filtered_df.sort_values(by='Date', ascending=False), use_container_width=True)
else:
    st.info("ไม่พบข้อมูลตามเงื่อนไขที่เลือก")
