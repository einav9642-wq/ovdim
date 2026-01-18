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
            # ניקוי שמות עמודות וערכי NaN מיד עם הטעינה
            df.columns = df.columns.astype(str).str.strip()
            df = df.fillna('')
            # וידוא שכל העמודות הן בפורמט טקסט
            df = df.astype(str)
            if 'תעודת זהות' in df.columns:
                df['תעודת זהות'] = df['תעודת זהות'].str.replace('.0', '', regex=False).str.strip()
            return df
        except:
            return pd.DataFrame()
    return pd.DataFrame()

def save_data(df):
    # החלפת כל מה שעלול להפוך ל-NaN לפני השמירה
    df = df.fillna('').astype(str)
    df.to_excel(DATA_FILE, index=False)

def process_and_filter(uploaded_file):
    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.astype(str).str.strip()
    
    # נרמול שמות עמודות (שימוש בגרשיים כפולים למניעת שגיאות סינטקס)
    rename_map = {
        "ת.ז": "תעודת זהות", "ת'ז": "תעודת זהות", "תז": "תעודת זהות",
        "מספר זהות": "תעודת זהות", "מס זהות": "תעודת זהות", "מס' זהות": "תעודת זהות",
        "שם עובד": "שם", "שם מלא": "שם",
        "מעסיק": "מקום העסקה", "חברה": "מקום העסקה",
        "תקופה": "תקופת העסקה", "שנה": "תקופת העסקה"
    }
    df.rename(columns=rename_map, inplace=True)
    
    if 'תעודת זהות' in df.columns:
        # ניקוי שורות ללא ת"ז
        df = df.dropna(subset=['תעודת זהות'])
        df['תעודת זהות'] = df['תעודת זהות'].astype(str).str.replace('.0', '', regex=False).str.strip()
        df = df[df['תעודת זהות'] != '']
    
    # בחירת עמודות קיימות בלבד
    required = ['שם', 'תעודת זהות', 'תקופת העסקה', 'מקום העסקה']
    existing = [c for c in required if c in df.columns]
    
    # החזרת המידע כשהוא נקי מ-NaN
    return df[existing].fillna('').astype(str)

# --- ממשק המשתמש ---
st.title('📂 מערכת איתור כפילויות - ניקוי נתונים סופי')

with st.sidebar:
    st.header('1. ניהול נתונים')
    uploaded_file = st.file_uploader('העלה קובץ אקסל חדש', type=['xlsx'])
    if uploaded_file and st.button('✅ הוסף למאגר'):
        new_data = process_and_filter(uploaded_file)
        if not new_data.empty:
            current_df = load_data()
            combined = pd.concat([current_df, new_data], ignore_index=True)
            save_data(combined)
            st.success('הנתונים נוספו! המאגר נוקה מ-NaN.')
            st.rerun()
        else:
            st.error('לא נמצאו נתונים תקינים (ודא שיש עמודת ת.ז).')
    
    st.divider()
    if st.button('🗑️ מחק את כל המאגר והתחל מחדש'):
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)
        st.session_state.clear()
        st.warning('המאגר נמחק לצורך ניקוי. העלה קבצים מחדש.')
        st.rerun()

master_df = load_data()

if not master_df.empty:
    # --- חיפוש ---
    st.subheader('🔍 חיפוש מהיר')
    c1, c2 = st.columns(2)
    with c1: s_name = st.text_input('לפי שם')
    with c2: s_id = st.text_input('לפי תעודת זהות')
    
    if s_name or s_id:
        res = master_df.copy()
        if s_name and 'שם' in res.columns:
            res = res[res['שם'].str.contains(s_name, na=False)]
        if s_id and 'תעודת זהות' in res.columns:
            res = res[res['תעודת זהות'].str.contains(s_id, na=False)]
        st.dataframe(res, use_container_width=True)

    st.divider()

    # --- איתור כפילויות ---
    st.subheader('👥 איתור רשומות כפולות')
    
    if st.button('🔍 הצג כפילויות (ת"ז שחוזרת על עצמה)'):
        if 'תעודת זהות' in master_df.columns:
            # סינון רק לערכים שיש להם ת"ז בפועל
            valid_df = master_df[master_df['תעודת זהות'].str.strip() != '']
            is_duplicate = valid_df.duplicated(subset=['תעודת זהות'], keep=False)
            dupes = valid_df[is_duplicate].copy()
            
            if not dupes.empty:
                sort_cols = [c for c in ['תעודת זהות', 'מקום העסקה'] if c in dupes.columns]
                dupes_sorted = dupes.sort_values(by=sort_cols)
                
                st.warning(f'נמצאו {dupes["תעודת זהות"].nunique()} עובדים המופיעים ביותר ממקום אחד.')
                
                # הצגת הטבלה כולל שמות העובדים
                display_cols = ['תעודת זהות', 'שם', 'מקום העסקה', 'תקופת העסקה']
                final_cols = [c for c in display_cols if c in dupes_sorted.columns]
                
                st.dataframe(dupes_sorted[final_cols], use_container_width=True)
                
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    dupes_sorted[final_cols].to_excel(writer, index=False)
                st.download_button('📥 הורד את רשימת הכפילויות לאקסל', output.getvalue(), 'duplicates_report.xlsx')
            else:
                st.success('לא נמצאו כפילויות במאגר.')
        else:
            st.error('עמודת תעודת זהות לא זוהתה.')

    with st.expander('צפה במאגר המלא'):
        st.write(master_df)
else:
    st.info('המאגר ריק. אנא העלה קבצים כדי להתחיל.')
