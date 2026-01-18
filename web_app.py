import streamlit as st
import pandas as pd
import os
import io

# --- הגדרות דף ---
st.set_page_config(page_title="ניהול נתוני עובדים", layout="wide")
DATA_FILE = "master_data.xlsx"

# --- פונקציות עזר ---
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            return pd.read_excel(DATA_FILE)
        except:
            return pd.DataFrame()
    return pd.DataFrame()

def save_data(df):
    df.to_excel(DATA_FILE, index=False)

def process_and_filter(uploaded_file):
    df = pd.read_excel(uploaded_file)
    rename_map = {
        'ת.ז': 'תעודת זהות',
        'מספר זהות': 'תעודת זהות',
        'שם עובד': 'שם',
        'מעסיק': 'מקום העסקה',
        'תקופה': 'תקופת העסקה'
    }
    df.rename(columns=rename_map, inplace=True)
    required_columns = ['שם', 'תעודת זהות', 'תקופת העסקה', 'מקום העסקה']
    existing_cols = [col for col in required_columns if col in df.columns]
    return df[existing_cols]

# --- ממשק המשתמש (UI) ---
st.title("📂 מערכת ניתוח עובדים")

# תפריט צד להעלאת קבצים
with st.sidebar:
    st.header("1. ניהול נתונים")
    uploaded_file = st.file_uploader("העלה קובץ אקסל חדש", type=["xlsx"])
    if uploaded_file:
        if st.button("✅ הוסף למאגר"):
            new_data = process_and_filter(uploaded_file)
            current_df = load_data()
            combined_df = pd.concat([current_df, new_data]).reset_index(drop=True)
            save_data(combined_df)
            st.success("הנתונים נוספו!")
            st.rerun()

    if st.button("🗑️ איפוס מאגר"):
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)
            st.rerun()

# טעינת המאגר
master_df = load_data()

if not master_df.empty:
    # --- חיפוש ---
    st.subheader("2. חיפוש מהיר")
    col1, col2 = st.columns(2)
    with col1:
        s_name = st.text_input("לפי שם")
    with col2:
        s_id = st.text_input("לפי תעודת זהות")
    
    res = master_df.copy()
    if s_name:
        res = res[res['שם'].astype(str).str.contains(s_name, na=False)]
    if s_id:
        res = res[res['תעודת זהות'].astype(str).str.contains(s_id, na=False)]
    st.dataframe(res, use_container_width=True)

    st.divider()

    # --- איתור כפילויות (הכפתור שחיפשת) ---
    st.subheader("3. איתור כפילויות (היסטוריית העסקה)")
    
    # יצירת הכפתור
    btn_detect = st.button("🔍 לחץ כאן לאיתור כפילויות")
    
    if btn_detect:
        # לוגיקת מציאת כפילויות
        dupes = master_df[master_df.duplicated(subset=['תעודת זהות'], keep=False)]
        
        if not dupes.empty:
            st.warning(f"נמצאו {dupes['תעודת זהות'].nunique()} עובדים עם מספר רשומות.")
            dupes_sorted = dupes.sort_values(by=['תעודת זהות', 'תקופת העסקה'])
            
            # הצגת הטבלה
            st.dataframe(dupes_sorted[['תעודת זהות', 'שם', 'מקום העסקה', 'תקופת העסקה']], use_container_width=True)
            
            # ייצוא לאקסל
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                dupes_sorted.to_excel(writer, index=False)
            
            st.download_button(
                label='📥 הורד תוצאות איתור כפילויות לאקסל',
                data=output.getvalue(),
                file_name="duplicates_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.success("לא נמצאו כפילויות במערכת.")

    # הצגת המאגר המלא בסוף
    with st.expander("צפה בכל המאגר המלא"):
        st.write(master_df)
else:
    st.info("המאגר ריק. העלה קובץ דרך התפריט בצד.")
