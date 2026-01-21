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
    s = str(val).strip().split('.')[0]
    return s

def process_file(uploaded_file):
    df = pd.read_excel(uploaded_file)
    original_columns = df.columns.astype(str).str.strip().tolist()
    df.columns = original_columns
    
    # מילון המרה מורחב מאוד
    rename_map = {
        "ת.ז": "תעודת זהות", "ת'ז": "תעודת זהות", "תז": "תעודת זהות", "ת.ז.": "תעודת זהות",
        "מספר זהות": "תעודת זהות", "מס' זהות": "תעודת זהות", "מס זהות": "תעודת זהות",
        "מספר זהות עובד": "תעודת זהות", "ID": "תעודת זהות",
        "שם עובד": "שם", "שם מלא": "שם", "שם": "שם", "העובד": "שם",
        "מעסיק": "מקום העסקה", "חברה": "מקום העסקה", "שם מעסיק": "מקום העסקה",
        "תקופה": "תקופת העסקה", "שנה": "תקופת העסקה", "תאריך": "תקופת העסקה", "חודש": "תקופת העסקה"
    }
    
    # זיהוי אוטומטי אם השם לא במילון
    for col in original_columns:
        if col not in rename_map.values():
            if any(key in col for key in ["זהות", "ת.ז", 'ת"ז']):
                rename_map[col] = "תעודת זהות"
            elif any(key in col for key in ["שם", "עובד"]) and "מעסיק" not in col:
                rename_map[col] = "שם"
            elif any(key in col for key in ["מעסיק", "חברה", "מקום"]):
                rename_map[col] = "מקום העסקה"

    df.rename(columns=rename_map, inplace=True)
    
    if 'תעודת זהות' in df.columns:
        df['תעודת זהות'] = df['תעודת זהות'].apply(clean_id)
        df = df[df['תעודת זהות'] != '']
    else:
        st.error(f"⚠️ בקובץ '{uploaded_file.name}' לא נמצאה עמודת זיהוי. העמודות שנמצאו: {original_columns}")
    
    df['מקור קובץ'] = uploaded_file.name
    required = ['שם', 'תעודת זהות', 'תקופת העסקה', 'מקום העסקה', 'מקור קובץ']
    existing = [c for c in required if c in df.columns]
    return df[existing].fillna('').astype(str)

# --- ממשק המשתמש ---
st.title('📂 מערכת ניתוח נתוני עובדים')

master_df = load_data()

with st.sidebar:
    st.header('1. ניהול נתונים')
    uploaded_files = st.file_uploader('בחר קבצים (ניתן לבחור כמה)', type=['xlsx'], accept_multiple_files=True)
    
    if uploaded_files and st.button('✅ הוסף למאגר'):
        all_new_data = []
        for f in uploaded_files:
            new_data = process_file(f)
            if not new_data.empty:
                all_new_data.append(new_data)
        
        if all_new_data:
            combined_new = pd.concat(all_new_data, ignore_index=True)
            updated_master = pd.concat([master_df, combined_new], ignore_index=True)
            save_data(updated_master)
            st.success('הקבצים נוספו בהצלחה.')
            st.rerun()

    st.divider()
    st.subheader('📄 קבצים במערכת:')
    if not master_df.empty and 'מקור קובץ' in master_df.columns:
        for i, filename in enumerate(master_df['מקור קובץ'].unique(), 1):
            st.text(f"{i}. {filename}")

    if st.button('🗑️ איפוס מאגר'):
        if os.path.exists(DATA_FILE): os.remove(DATA_FILE)
        st.session_state.clear()
        st.rerun()

# --- גוף האפליקציה ---
if not master_df.empty:
    st.subheader('🔍 חיפוש וניתוח')
    c1, c2 = st.columns(2)
    with c1: s_name = st.text_input('לפי שם')
    with c2: s_id = st.text_input('לפי תעודת זהות')
    
    if s_name or s_id:
        res = master_df.copy()
        if s_name: res = res[res['שם'].str.contains(s_name, na=False)]
        if s_id: res = res[res['תעודת זהות'].str.contains(s_id, na=False)]
        st.dataframe(res, use_container_width=True)

    st.divider()
    st.subheader('👥 איתור כפילויות והיסטוריית העסקה')
    
    if st.button('🔍 אתר כפילויות'):
        if 'תעודת זהות' in master_df.columns:
            valid_df = master_df[master_df['תעודת זהות'] != '']
            is_duplicate = valid_df.duplicated(subset=['תעודת זהות'], keep=False)
            dupes = valid_df[is_duplicate].copy()
            
            if not dupes.empty:
                dupes_sorted = dupes.sort_values(by=['תעודת זהות'])
                display_cols = ['תעודת זהות', 'שם', 'מקום העסקה', 'תקופת העסקה', 'מקור קובץ']
                final_cols = [c for c in display_cols if c in dupes_sorted.columns]
                
                st.warning(f"נמצאו {dupes['תעודת זהות'].nunique()} עובדים כפולים.")
                st.dataframe(dupes_sorted[final_cols], use_container_width=True)
                
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    dupes_sorted[final_cols].to_excel(writer, index=False)
                st.download_button('📥 הורד אקסל', output.getvalue(), 'duplicates.xlsx')
            else: st.success('אין כפילויות.')
        else: st.error('עמודת תעודת זהות לא זוהתה במאגר הכללי.')

    with st.expander('צפה במאגר המלא'):
        st.write(master_df)
else:
    st.info('המערכת ריקה. העלה קבצים מימין.')
