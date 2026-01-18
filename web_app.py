import streamlit as st
import pandas as pd
import os
import io

# --- הגדרות דף ---
st.set_page_config(page_title='ניהול נתוני עובדים', layout='wide')
DATA_FILE = 'master_data.xlsx'

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_excel(DATA_FILE)
            df.columns = df.columns.astype(str).str.strip()
            return df
        except:
            return pd.DataFrame()
    return pd.DataFrame()

def save_data(df):
    df.to_excel(DATA_FILE, index=False)

def process_and_filter(uploaded_file):
    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.astype(str).str.strip()
    # נרמול עמודות - קריטי לזיהוי הנתונים שביקשת
    rename_map = {
        'ת.ז': 'תעודת זהות', 'מספר זהות': 'תעודת זהות', 
        'שם עובד': 'שם', 'שם מלא': 'שם',
        'מעסיק': 'מקום העסקה', 'שם מעסיק': 'מקום העסקה', 'חברה': 'מקום העסקה',
        'תקופה': 'תקופת העסקה', 'שנה': 'תקופת העסקה', 'תאריך': 'תקופת העסקה'
    }
    df.rename(columns=rename_map, inplace=True)
    required = ['שם', 'תעודת זהות', 'תקופת העסקה', 'מקום העסקה']
    return df[[c for c in required if c in df.columns]]

# --- ממשק המשתמש ---
st.title('📂 מערכת לאיתור כפילויות והיסטוריית העסקה')

with st.sidebar:
    st.header('1. ניהול נתונים')
    uploaded_file = st.file_uploader('העלה קובץ אקסל חדש', type=['xlsx'])
    if uploaded_file and st.button('✅ הוסף למאגר'):
        new_data = process_and_filter(uploaded_file)
        current_df = load_data()
        save_data(pd.concat([current_df, new_data], ignore_index=True))
        st.success('הנתונים נוספו למערכת!')
        st.rerun()
    
    st.divider()
    if st.button('🗑️ איפוס ומחיקת כל המאגר'):
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)
        st.session_state.clear()
        st.rerun()

master_df = load_data()

if not master_df.empty:
    # --- חיפוש חופשי ---
    st.subheader('🔍 חיפוש עובד ספציפי')
    col1, col2 = st.columns(2)
    with col1:
        s_name = st.text_input('לפי שם')
    with col2:
        s_id = st.text_input('לפי תעודת זהות')
    
    if s_name or s_id:
        res = master_df.copy()
        if s_name: res = res[res['שם'].astype(str).str.contains(s_name, na=False)]
        if s_id: res = res[res['תעודת זהות'].astype(str).str.contains(s_id, na=False)]
        st.dataframe(res, use_container_width=True)

    st.divider()

    # --- איתור כפילויות - התצוגה שביקשת ---
    st.subheader('👥 איתור רשומות כפולות (היסטוריית עבודה)')
    
    if st.button('🔍 הצג את כל העובדים שמופיעים יותר מפעם אחת'):
        if 'תעודת זהות' in master_df.columns:
            # מציאת כל השורות שבהן תעודת הזהות חוזרת על עצמה
            is_duplicate = master_df.duplicated(subset=['תעודת זהות'], keep=False)
            dupes = master_df[is_duplicate].copy()
            
            if not dupes.empty:
                # מיון כדי לראות את כל הרשומות של אותו עובד ברצף (לפי ת"ז ואז תקופה)
                dupes_sorted = dupes.sort_values(by=['תעודת זהות', 'תקופת העסקה'])
                
                st.warning(f'נמצאו {dupes["תעודת זהות"].nunique()} עובדים עם רשומות כפולות.')
                
                # הצגת הטבלה המפורטת בדיוק כפי שביקשת
                display_cols = ['שם', 'תעודת זהות', 'מקום העסקה', 'תקופת העסקה']
                final_cols = [c for c in display_cols if c in dupes_sorted.columns]
                
                st.write('להלן פירוט המקומות והתקופות של העובדים הכפולים:')
                st.dataframe(dupes_sorted[final_cols], use_container_width=True)
                
                # ייצוא לאקסל
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    dupes_sorted[final_cols].to_excel(writer, index=False)
                st.download_button('📥 הורד את רשימת הכפילויות לאקסל', output.getvalue(), 'duplicate_history.xlsx')
            else:
                st.success('לא נמצאו כפילויות. כל עובד מופיע פעם אחת בלבד.')
        else:
            st.error('חסרה עמודת תעודת זהות לביצוע הבדיקה.')

    st.divider()
    with st.expander('צפה במאגר המלא (כל העובדים)'):
        st.write(master_df)
else:
    st.info('המערכת ריקה. העלה קובץ אקסל כדי להתחיל.')
