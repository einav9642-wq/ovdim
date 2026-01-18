import streamlit as st
import pandas as pd
import os

# --- הגדרות ראשוניות ---
st.set_page_config(page_title="ניהול נתוני עובדים", layout="wide")
DATA_FILE = "master_data.xlsx" # קובץ המאגר המקומי

# --- פונקציות עזר ---

def load_data():
    """טעינת המאגר הקיים מהדיסק"""
    if os.path.exists(DATA_FILE):
        return pd.read_excel(DATA_FILE)
    return pd.DataFrame()

def save_data(df):
    """שמירת המאגר לדיסק"""
    df.to_excel(DATA_FILE, index=False)

def process_and_filter(uploaded_file):
    """טעינת קובץ חדש וסינון עמודות רלוונטיות בלבד"""
    df = pd.read_excel(uploaded_file)
    
    # מיפוי שמות עמודות אפשריים (נרמול)
    rename_map = {
        'ת.ז': 'תעודת זהות',
        'מספר זהות': 'תעודת זהות',
        'שם עובד': 'שם',
        'מעסיק': 'מקום העסקה'
    }
    df.rename(columns=rename_map, inplace=True)
    
    # העמודות שאנחנו רוצים לשמור
    required_columns = ['שם', 'תעודת זהות', 'תקופת העסקה', 'מקום העסקה']
    
    # סינון: רק מה שקיים מתוך הרשימה שלנו
    existing_cols = [col for col in required_columns if col in df.columns]
    return df[existing_cols]

# --- ממשק המשתמש (UI) ---

st.title("📂 מערכת ניתוח וחיפוש עובדים")

# תפריט צדדי להעלאה ומחיקה
with st.sidebar:
    st.header("ניהול נתונים")
    uploaded_file = st.file_uploader("העלה קובץ אקסל חדש", type=["xlsx"])
    
    if uploaded_file:
        new_data = process_and_filter(uploaded_file)
        if st.button("הוסף למאגר התוכנה"):
            current_df = load_data()
            combined_df = pd.concat([current_df, new_data]).drop_duplicates().reset_index(drop=True)
            save_data(combined_df)
            st.success("הנתונים נוספו ועודכנו!")

    if st.button("❌ מחק את כל המאגר (Reset)"):
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)
            st.warning("הקובץ הוסר מהספרייה לצמיתות.")
            st.rerun()

# גוף התוכנה - חיפוש והצגה
master_df = load_data()

if not master_df.empty:
    st.subheader("חיפוש עובד במאגר")
    
    col1, col2 = st.columns(2)
    with col1:
        search_name = st.text_input("חפש לפי שם")
    with col2:
        search_id = st.text_input("חפש לפי תעודת זהות")

    # לוגיקת החיפוש
    results = master_df.copy()
    if search_name:
        results = results[results['שם'].str.contains(search_name, na=False)]
    if search_id:
        results = results[results['תעודת זהות'].astype(str).str.contains(search_id, na=False)]

    if not results.empty:
        st.write(f"נמצאו {len(results)} תוצאות:")
        st.dataframe(results, use_container_width=True)
    else:
        st.info("אין תוצאות התואמות לחיפוש.")

    with st.expander("צפה בכל המאגר הקיים"):
        st.table(master_df)
else:
    st.info("המאגר ריק. אנא העלה קובץ אקסל דרך תפריט הצד.")
