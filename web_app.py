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
            # החלפת NaN ו-None בטקסט ריק לתצוגה נקייה
            df = df.fillna('')
            return df
        except:
            return pd.DataFrame()
    return pd.DataFrame()

def save_data(df):
    df.to_excel(DATA_FILE, index=False)

def process_and_filter(uploaded_file):
    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.astype(str).str.strip()
    
    # נרמול שמות עמודות מורחב
    rename_map = {
        'ת.ז': 'תעודת זהות', 'ת"ז': 'תעודת זהות', 'תז': 'תעודת זהות',
        'מספר זהות': 'תעודת זהות', 'מס זהות': 'תעודת זהות', "מס' זהות": 'תעודת זהות',
        'שם עובד': 'שם', 'שם מלא': 'שם',
        'מעסיק': 'מקום העסקה', 'חברה': 'מקום העסקה', 'שם מעסיק': 'מקום העסקה',
        'תקופה': 'תקופת העסקה', 'שנה': 'תקופת העסקה', 'תאריך': 'תקופת העסקה'
    }
    df.rename(columns=rename_map, inplace=True)
    
    # חובה שיהיה תעודת זהות (הסרת ריקים רק מהעמודה הזו לפני העיבוד)
    if 'תעודת זהות' in df.columns:
        df = df.dropna(subset=['תעודת זהות'])
        df = df[df['תעודת זהות'].astype(str).str.strip() != '']
    
    required = ['שם', 'תעודת זהות', 'תקופת העסקה', 'מקום העסקה']
    existing_in_df = [c for c in required if c in df.columns]
    
    # ניקוי NaN גם בשלב העיבוד
    df_filtered = df[existing_in_df].fillna('')
    return df_filtered

# --- ממשק המשתמש ---
st.title('📂 מערכת איתור כפילויות - תצוגה נקייה')

with st.sidebar:
    st.header('1. ניהול נתונים')
    uploaded_file = st.file_uploader('העלה קובץ אקסל חדש', type=['xlsx'])
    if uploaded_file and st.button('✅ הוסף למאגר'):
        new_data = process_and_filter(uploaded_file)
        if not new_data.empty:
            current_df = load_data()
            save_data(pd.concat([current_df, new_data], ignore_index=True))
            st.success(f'נוספו {len(new_data)} רשומות תקינות.')
            st.rerun()
        else:
            st.error('לא נמצאו רשומות עם ת.ז תקין.')
    
    if st.button('🗑️ איפוס מאגר'):
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)
        st.session_state.clear()
        st.rerun()

master_df = load_data()

if not master_df.empty:
    # --- חיפוש ---
    st.subheader('🔍 חיפוש עובד')
    c1, c2 = st.columns(2)
    with c1: s_name = st.text_input('לפי שם')
    with c2: s_id = st.text_input('לפי תעודת זהות')
    
    if s_name or s_id:
        res = master_df.copy()
        if s_name and 'שם' in res.columns: 
            res = res[res['שם'].astype(str).str.contains(s_name, na=False)]
        if s_id and 'תעודת זהות' in res.columns: 
            res = res[res['תעודת זהות'].astype(str).str.contains(s_id, na=False)]
        st.dataframe(res, use_container_width=True)

    st.divider()

    # --- איתור כפילויות ---
    st.subheader('👥 איתור כפילויות לפי ת.ז')
    
    if st.button('🔍 הצג רשומות כפולות'):
        if 'תעודת זהות' in master_df.columns:
            # וידוא שכל ה-ID הם טקסט ללא רווחים
            master_df['תעודת זהות'] = master_df['תעודת זהות'].astype(str).str.strip()
            # איתור כפילויות (מתעלם מתאים שהם טקסט ריק)
            valid_ids = master_df[master_df['תעודת זהות'] != '']
            is_duplicate = valid_ids.duplicated(subset=['תעודת זהות'], keep=False)
            dupes = valid_ids[is_duplicate].copy()
            
            if not dupes.empty:
                sort_cols = [c for c in ['תעודת זהות', 'מקום העסקה'] if c in dupes.columns]
                dupes_sorted = dupes.sort_values(by=sort_cols)
                
                st.warning(f'נמצאו {dupes["תעודת זהות"].nunique()} עובדים כפולים.')
                
                display_cols = ['תעודת זהות', 'שם', 'מקום העסקה', 'תקופת העסקה']
                final_cols = [c for c in display_cols if c in dupes_sorted.columns]
                
                # הצגת הטבלה ללא NaN
                st.dataframe(dupes_sorted[final_cols], use_container_width=True)
                
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    dupes_sorted[final_cols].to_excel(writer, index=False)
                st.download_button('📥 הורד את הכפילויות לאקסל', output.getvalue(), 'duplicates.xlsx')
            else:
                st.success('אין כפילויות במערכת.')
        else:
            st.error('לא נמצאה עמודת תעודת זהות.')

    with st.expander('צפה במאגר המלא'):
        st.write(master_df)
else:
    st.info('המערכת ריקה.')
