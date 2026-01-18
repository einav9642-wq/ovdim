import streamlit as st
import pandas as pd
import os

# --- הגדרות דף ---
st.set_page_config(page_title="ניהול נתוני עובדים", layout="wide")
DATA_FILE = "master_data.xlsx"

# --- פונקציות עזר ---

def load_data():
    """טעינת המאגר הקיים מהדיסק"""
    if os.path.exists(DATA_FILE):
        try:
            return pd.read_excel(DATA_FILE)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()

def save_data(df):
    """שמירת המאגר לדיסק"""
    df.to_excel(DATA_FILE, index=False)

def process_and_filter(uploaded_file):
    """טעינת קובץ וסינון עמודות רלוונטיות בלבד"""
    df = pd.read_excel(uploaded_file)
    
    # נרמול שמות עמודות נפוצים
    rename_map = {
        'ת.ז': 'תעודת זהות',
        'מספר זהות': 'תעודת זהות',
        'שם עובד': 'שם',
        'מעסיק': 'מקום העסקה',
        'תקופה': 'תקופת העסקה'
    }
    df.rename(columns=rename_map, inplace=True)
    
    # השדות שביקשת להשאיר (התעלמות מכל השאר)
    required_columns = ['שם', 'תעודת זהות', 'תקופת העסקה', 'מקום העסקה']
    
    # סינון רק מה שקיים מתוך הרשימה
    existing_cols = [col for col in required_columns if col in df.columns]
    return df[existing_cols]

# --- ממשק המשתמש (UI) ---

st.title("📂 מערכת ניתוח עובדים - חיפוש ואיתור כפילויות")

with st.sidebar:
    st.header("ניהול נתונים")
    uploaded_file = st.file_uploader("העלה קובץ אקסל חדש", type=["xlsx"])
    
    if uploaded_file:
        new_data = process_and_filter(uploaded_file)
        if st.button("✅ הוסף למאגר התוכנה"):
            current_df = load_data()
            combined_df = pd.concat([current_df, new_data]).reset_index(drop=True)
            save_data(combined_df)
            st.success("הנתונים נוספו בהצלחה!")
            st.rerun()

    st.divider()
    
    if st.button("🗑️ מחק את כל המאגר (איפוס)"):
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)
            st.warning("הקובץ נמחק מהספרייה.")
            st.rerun()

# טעינת המאגר
master_df = load_data()

if not master_df.empty:
    # --- חיפוש עובדים ---
    st.subheader("🔍 חיפוש עובד מהיר")
    c1, c2 = st.columns(2)
    with c1:
        search_name = st.text_input("חפש לפי שם")
    with c2:
        search_id = st.text_input("חפש לפי תעודת זהות")

    results = master_df.copy()
    if search_name:
        results = results[results['שם'].astype(str).str.contains(search_name, na=False)]
    if search_id:
        results = results[results['תעודת זהות'].astype(str).str.contains(search_id, na=False)]

    st.dataframe(results, use_container_width=True)

    st.divider()

    # --- איתור כפילויות וייצוא ---
    st.subheader("👥 איתור כפילויות והיסטוריית העסקה")
    
    # כפתור איתור כפילויות מרכזי
    if st.button("אתר כפילויות במערכת"):
        # מציאת כל המופעים של תעודות זהות שחוזרות על עצמן
        dupes = master_df[master_df.duplicated(subset=['תעודת זהות'], keep=False)]
        
        if not dupes.empty:
            st.warning(f"נמצאו {dupes['תעודת זהות'].nunique()} עובדים עם מספר רשומות כפולות:")
            
            # מיון כדי להציג את ההיסטוריה של כל עובד ברצף
            dupes_sorted = dupes.sort_values(by=['תעודת זהות', 'תקופת העסקה'])
            
            # הצגת הטבלה של הכפילויות בלבד
            st.dataframe(dupes_sorted[['תעודת זהות', 'שם', 'מקום העסקה', 'תקופת העסקה']], use_container_width=True)
            
            # יצירת קובץ אקסל לייצוא בזיכרון (כדי שלא יכתוב קבצים מיותרים לשרת)
            import io
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                dupes_sorted.to_excel(writer, index=False, sheet_name='כפילויות')
            processed_data = output.getvalue()

            # כפתור הורדה
            st.download_button(
                label='📥 ייצא תוצאות כפילויות לאקסל',
                data=processed_data,
                file_name="כפילויות_עובדים.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.success("לא נמצאו כפילויות. כל תעודת זהות ייחודית במערכת.")

    with st.expander("צפה במאגר המלא"):
        st.write(master_df)

else:
    st.info("המאגר ריק. העלה קובץ אקסל כדי להתחיל.")
