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
    rename_map = {
        'ת.ז': 'תעודת זהות', 'מספר זהות': 'תעודת זהות', 
        'שם עובד': 'שם', 'מעסיק': 'מקום העסקה', 
        'תקופה': 'תקופת העסקה'
    }
    df.rename(columns=rename_map, inplace=True)
    required = ['שם', 'תעודת זהות', 'תקופת העסקה', 'מקום העסקה']
    return df[[c for c in required if c in df.columns]]

# --- ממשק המשתמש ---
st.title('📂 מערכת לניהול וניתוח נתוני עובדים')

with st.sidebar:
    st.header('1. ניהול נתונים')
    uploaded_file = st.file_uploader('העלה קובץ אקסל חדש', type=['xlsx'])
    if uploaded_file and st.button('✅ הוסף למאגר'):
        new_data = process_and_filter(uploaded_file)
        current_df = load_data()
        save_data(pd.concat([current_df, new_data], ignore_index=True))
        st.success('הנתונים נוספו!')
        st.rerun()
    if st.button('🗑️ איפוס מאגר'):
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)
        st.session_state.clear()
        st.rerun()

master_df = load_data()

if not master_df.empty:
    # --- חיפוש ---
    st.subheader('🔍 חיפוש עובד')
    col1, col2 = st.columns(2)
    with col1:
        s_name = st.text_input('חפש לפי שם')
    with col2:
        s_id = st.text_input('חפש לפי תעודת זהות')
    
    if s_name or s_id:
        res = master_df.copy()
        if s_name and 'שם' in res.columns:
            res = res[res['שם'].astype(str).str.contains(s_name, na=False)]
        if s_id and 'תעודת זהות' in res.columns:
            res = res[res['תעודת זהות'].astype(str).str.contains(s_id, na=False)]
        st.dataframe(res, use_container_width=True)

    st.divider()

    # --- איתור כפילויות ---
    st.subheader('👥 איתור כפילויות')
    
    if st.button('🔍 נתח כפילויות'):
        if 'תעודת זהות' in master_df.columns:
            is_duplicate = master_df.duplicated(subset=['תעודת זהות'], keep=False)
            dupes = master_df[is_duplicate].copy()
            
            if not dupes.empty:
                agg_dict = {}
                if 'שם' in dupes.columns: agg_dict['שם'] = 'first'
                if 'מקום העסקה' in dupes.columns:
                    agg_dict['מקום העסקה'] = lambda x: ', '.join(x.astype(str).unique())
                if 'תקופת העסקה' in dupes.columns:
                    agg_dict['תקופת העסקה'] = 'count'
                
                summary = dupes.groupby('תעודת זהות').agg(agg_dict).reset_index()
                if 'תקופת העסקה' in summary.columns:
                    summary.rename(columns={'תקופת העסקה': 'מספר רשומות'}, inplace=True)
                
                st.session_state['dupes_summary'] = summary
                st.session_state['dupes_full'] = dupes.sort_values(by='תעודת זהות')
            else:
                st.session_state['dupes_summary'] = 'empty'
        else:
            st.error('עמודת תעודת זהות חסרה.')

    # תצוגת התוצאות
    if 'dupes_summary' in st.session_state:
        if isinstance(st.session_state['dupes_summary'], pd.DataFrame):
            st.warning(f"נמצאו {len(st.session_state['dupes_summary'])} עובדים כפולים.")
            
            t1, t2 = st.tabs(["📋 סיכום", "📄 פירוט מלא"])
            with t1:
                st.dataframe(st.session_state['dupes_summary'], use_container_width=True)
            with t2:
                st.dataframe(st.session_state['dupes_full'], use_container_width=True)
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    st.session_state['dupes_full'].to_excel(writer, index=False)
                st.download_button('📥 הורד פירוט מלא לאקסל', output.getvalue(), 'duplicates.xlsx')
        elif st.session_state['dupes_summary'] == 'empty':
            st.success('לא נמצאו כפילויות.')

    st.divider()
    with st.expander('צפה במאגר המלא'):
        st.write(master_df)
else:
    st.info('המערכת מוכנה. העלה קובץ אקסל כדי להתחיל.')
