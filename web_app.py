import streamlit as st
import pandas as pd
import os

# --- הגדרות ראשוניות ---
st.set_page_config(page_title="ניהול נתוני עובדים", layout="wide")
DATA_FILE = "master_data.xlsx"

# --- פונקציות עזר ---

def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_excel(DATA_FILE)
    return pd.DataFrame()

def save_data(df):
    df.to_excel(DATA_FILE, index=False)

def process_and_filter(uploaded_file):
    df = pd.read_excel(uploaded_file)
    rename_map = {
        'ת.ז': 'תעודת זהות',
        'מספר זהות': 'תעודת זהות',
        'שם עובד': 'שם',
        'מעסיק': 'מקום העסקה'
    }
    df.rename(columns=rename_map, inplace=True)
    required_columns = ['שם', 'תעודת זהות', 'תקופת העסקה', 'מקום העסקה']
    existing_cols = [col for col in required_columns if col in df.columns]
    return df[existing_cols]

# --- ממשק המשתמש ---

st.title("📂 מערכת ניתוח וחיפוש עובדים")

with st.sidebar:
    st.header("ניהול נתונים")
    uploaded_file = st.file_uploader("העלה קובץ אקסל חדש", type=["xlsx"])
    
    if uploaded_file:
        new_data = process_and_filter(uploaded_file)
        if st.button("✅ הוסף למאגר התוכנה"):
            current_df = load_data()
            # חיבור הנתונים ללא מחיקת כפילויות אוטומטית כדי שנוכל לאתר אותן אחר כך
            combined_df = pd.concat([current_df, new_data]).reset_index(drop=True)
            save_data(combined_df)
            st.success("הנתונים נוספו!")

    st.divider()
    
    # כפתור איתור כפילויות
    if st.button("🔍 אתר כפילויות"):
        master_df = load_data()
        if not master_df.empty:
            # מציאת כל השורות שבהן תעודת הזהות מופיעה יותר מפעם אחת
            duplicates = master_df[master_df.duplicated(subset=['תעודת זהות'], keep=False)]
            if not duplicates.empty:
                st.session_state['show_dupes'] = duplicates
            else:
                st.session_state['show_dupes'] = "none"
        else:
            st.error("המאגר ריק, אין מה לבדוק.")

    if st.button("🗑️ מחק את כל המאגר (Reset)"):
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)
            st.rerun()

# --- תצוגת תוצאות איתור כפילויות ---
if 'show_dupes' in st.session_state:
    if isinstance(st.session_state['show_dupes'], pd.DataFrame):
        st.warning("⚠️ נמצאו מספרי תעודת זהות כפולים במערכת:")
        st.dataframe(st.session_state['show_dupes'].sort_values(by='תעודת זהות'))
        if st.button("נקה כפילויות ושמור רק שורה אחת לכל ת.ז"):
            master_df = load_data()
            clean_df = master_df.drop_duplicates(subset=['תעודת זהות'], keep='first')
            save_data(clean_df)
            st.success("הכפילויות הוסרו בהצלחה!")
            del st.session_state['show_dupes']
            st.rerun()
    elif st.session_state['show_dupes'] == "none":
        st.success("לא נמצאו כפילויות במאגר.")

# --- חיפוש והצגה רגילה ---
master_df = load_data()
if not master_df.empty:
    st.subheader("חיפוש עובד במאגר")
    col1, col2 = st.columns(2)
    with col1:
        search_name = st.text_input("חפש לפי שם")
    with col2:
        search_id = st.text_input("חפש לפי תעודת זהות")

    results = master_df.copy()
    if search_name:
        results = results[results['שם'].astype(str).str.contains(search_name, na=False)]
    if search_id:
        results = results[results['תעודת זהות'].astype(str).str.contains(search_id, na=False)]

    st.dataframe(results, use_container_width=True)
