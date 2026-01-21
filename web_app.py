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
            df = df.fillna('').astype(str)
            return df
        except:
            return pd.DataFrame()
    return pd.DataFrame()

def save_data(df):
    df = df.fillna('').astype(str)
    df.to_excel(DATA_FILE, index=False)

def clean_id(val):
    """מנקה את מספר הזהות מתווים מיותרים"""
    s = str(val).strip().split('.')[0] # הסרת סיומת עשרונית
    return s

def process_and_filter(uploaded_file):
    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.astype(str).str.strip()
    
    rename_map = {
        "ת.ז": "תעודת זהות", "ת'ז": "תעודת זהות", "תז": "תעודת זהות",
        "מספר זהות": "תעודת זהות", "מס' זהות": "תעודת זהות", "מס זהות": "תעודת זהות",
        "שם עובד": "שם", "שם מלא": "שם", "שם": "שם",
        "מעסיק": "מקום העסקה", "חברה": "מקום העסקה", "שם מעסיק": "מקום העסקה",
        "תקופה": "תקופת העסקה", "שנה": "תקופת העסקה", "תאריך": "תקופת העסקה"
    }
    df.rename(columns=rename_map, inplace=True)
    
    if 'תעודת זהות' in df.columns:
        df['תעודת זהות'] = df['תעודת זהות'].apply(clean_id)
        df = df[df['תעודת זהות'] != '']
    
    required = ['שם', 'תעודת זהות', 'תקופת העסקה', 'מקום העסקה']
    existing = [c for c in required if c in df.columns]
    return df[existing].fillna('').astype(str)

# --- ממשק המשתמש ---
st.title('📂 מערכת הצלבת נתונים - גרסה יציבה')

with st.sidebar:
    st.header('1. ניהול נתונים')
    uploaded_file = st.file_uploader('העלה קובץ אקסל חדש', type=['xlsx'])
    if uploaded_file and st.button('✅ הוסף למאגר'):
        new_data = process_and_filter(uploaded_file)
        if not new_data.empty:
            current_df = load_data()
            combined = pd.concat([current_df, new_data], ignore_index=True)
            save_data(combined)
            st.success(f'נוספו {len(new_data)} שורות.')
            st.rerun()

    if st.button('🗑️ איפוס מאגר מוחלט'):
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)
        st.session_state.clear()
        st.rerun()

master_df = load_data()

if not master_df.empty:
    # --- חיפוש ---
    st.subheader('🔍 חיפוש')
    c1, c2 = st.columns(2)
    with c1: 
        s_name = st.text_input('לפי שם')
    with c2: 
        s_id = st.text_input('לפי תעודת זהות')
    
    if s_name or s_id:
        res = master_df.copy()
        if s_name and 'שם' in res.columns: 
            res = res[res['שם'].str.contains(s_name, na=False)]
        if s_id and 'תעודת זהות' in res.columns: 
            res = res[res['תעודת זהות'].str.contains(s_id, na=False)]
        st.dataframe(res, use_container_width=True)

    st.divider()

    # --- איתור כפילויות ---
    st.subheader('👥 איתור כפילויות (תצוגה מקובצת)')
    
    if st.button('🔍 נתח והצג כפילויות'):
        if 'תעודת זהות' in master_df.columns:
            valid_df = master_df[master_df['תעודת זהות'] != '']
            is_duplicate = valid_df.duplicated(subset=['תעודת זהות'], keep=False)
            dupes = valid_df[is_duplicate].copy()
            
            if not dupes.empty:
                def get_main_name(x):
                    names = [n for n in x if n and str(n).lower() not in ['nan', 'none', 'שם']]
                    return names[0] if names else ''

                agg_dict = {}
                if 'שם' in dupes.columns:
                    agg_dict['שם'] = get_main_name
                if 'מקום העסקה' in dupes.columns:
                    agg_dict['מקום העסקה'] = lambda x: ' | '.join(sorted(set(filter(None, x))))
                if 'תקופת העסקה' in dupes.columns:
                    agg_dict['תקופת העסקה'] = lambda x: ', '.join(sorted(set(filter(None, x))))
                
                summary = dupes.groupby('תעודת זהות').agg(agg_dict).reset_index()
                
                st.warning(f"נמצאו {len(summary)} עובדים כפולים.")
                st.dataframe(summary, use_container_width=True)
                
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    summary.to_excel(writer, index=False)
                st.download_button('📥 הורד סיכום לאקסל', output.getvalue(), 'summary.xlsx')
            else:
                st.success('לא נמצאו כפילויות.')
        else:
            st.error('עמודת תעודת זהות לא זוהתה.')

    with st.expander('צפה במאגר המלא'):
        st.write(master_df)
else:
    st.info('המערכת ריקה. העלה קובץ אקסל כדי להתחיל.')
