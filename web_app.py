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
            # החלפת ערכים ריקים בטקסט ריק למניעת NaN
            df = df.fillna('').astype(str)
            if 'תעודת זהות' in df.columns:
                df['תעודת זהות'] = df['תעודת זהות'].str.replace('.0', '', regex=False).str.strip()
            return df
        except:
            return pd.DataFrame()
    return pd.DataFrame()

def save_data(df):
    df = df.fillna('').astype(str)
    df.to_excel(DATA_FILE, index=False)

def process_and_filter(uploaded_file):
    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.astype(str).str.strip()
    
    # מילון המרה רחב ככל הניתן
    rename_map = {
        "ת.ז": "תעודת זהות", "ת'ז": "תעודת זהות", "תז": "תעודת זהות",
        "מספר זהות": "תעודת זהות", "מס' זהות": "תעודת זהות", "מס זהות": "תעודת זהות",
        "שם עובד": "שם", "שם מלא": "שם", "שם": "שם",
        "מעסיק": "מקום העסקה", "חברה": "מקום העסקה", "שם מעסיק": "מקום העסקה",
        "תקופה": "תקופת העסקה", "שנה": "תקופת העסקה", "תאריך": "תקופת העסקה"
    }
    df.rename(columns=rename_map, inplace=True)
    
    if 'תעודת זהות' in df.columns:
        df = df.dropna(subset=['תעודת זהות'])
        df['תעודת זהות'] = df['תעודת זהות'].astype(str).str.replace('.0', '', regex=False).str.strip()
        df = df[df['תעודת זהות'] != '']
    
    required = ['שם', 'תעודת זהות', 'תקופת העסקה', 'מקום העסקה']
    existing = [c for c in required if c in df.columns]
    return df[existing].fillna('').astype(str)

# --- ממשק המשתמש ---
st.title('📂 מערכת הצלבת נתונים - סיכום חכם')

with st.sidebar:
    st.header('1. ניהול נתונים')
    uploaded_file = st.file_uploader('העלה קובץ אקסל חדש', type=['xlsx'])
    if uploaded_file and st.button('✅ הוסף למאגר'):
        new_data = process_and_filter(uploaded_file)
        if not new_data.empty:
            current_df = load_data()
            combined = pd.concat([current_df, new_data], ignore_index=True)
            save_data(combined)
            st.success('הנתונים נוספו בהצלחה!')
            st.rerun()

    if st.button('🗑️ איפוס מאגר'):
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)
        st.session_state.clear()
        st.rerun()

master_df = load_data()

if not master_df.empty:
    # --- חיפוש ---
    st.subheader('🔍 חיפוש מהיר')
    c1, c2 = st.columns(2)
    with c1: s_name = st.text_input('חפש לפי שם')
    with c2: s_id = st.text_input('חפש לפי תעודת זהות')
    
    if s_name or s_id:
        res = master_df.copy()
        if s_name and 'שם' in res.columns: res = res[res['שם'].str.contains(s_name, na=False)]
        if s_id and 'תעודת זהות' in res.columns: res = res[res['תעודת זהות'].str.contains(s_id, na=False)]
        st.dataframe(res, use_container_width=True)

    st.divider()

    # --- איתור כפילויות דינמי ---
    st.subheader('👥 איתור כפילויות (תצוגה מקובצת)')
    
    if st.button('🔍 נתח והצג כפילויות'):
        if 'תעודת זהות' in master_df.columns:
            # סינון רק לכפילויות
            is_duplicate = master_df.duplicated(subset=['תעודת זהות'], keep=False)
            dupes = master_df[is_duplicate].copy()
            
            if not dupes.empty:
                # בניית מילון סיכום רק עבור עמודות שקיימות ב-DataFrame
                agg_dict = {}
                if 'שם' in dupes.columns:
                    agg_dict['שם'] = lambda x: ' / '.join(set(filter(None, x)))
                if 'מקום העסקה' in dupes.columns:
                    agg_dict['מקום העסקה'] = lambda x: ' | '.join(set(filter(None, x)))
                if 'תקופת העסקה' in dupes.columns:
                    agg_dict['תקופת העסקה'] = lambda x: ', '.join(set(filter(None, x)))
                
                # ביצוע הקיבוץ
                if agg_dict:
                    summary = dupes.groupby('תעודת זהות').agg(agg_dict).reset_index()
                    
                    st.warning(f"נמצאו {len(summary)} עובדים המופיעים ביותר ממקום אחד.")
                    st.dataframe(summary, use_container_width=True)
                    
                    # הורדה
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        summary.to_excel(writer, index=False)
                    st.download_button('📥 הורד טבלת סיכום', output.getvalue(), 'summary.xlsx')
                else:
                    st.error("לא נמצאו מספיק עמודות לביצוע סיכום (צריך לפחות שם, מקום או תקופה).")
            else:
                st.success('לא נמצאו כפילויות.')
        else:
            st.error('עמודת תעודת זהות לא זוהתה במאגר.')

    with st.expander('צפה במאגר המלא'):
        st.write(master_df)
else:
    st.info('המאגר ריק.')
