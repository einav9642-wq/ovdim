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
            
            # ניסיון לנרמל את עמודת הזהות בתוך המאגר הקיים
            rename_map = {}
            for col in df.columns:
                if any(key in col for key in ["זהות", "ת.ז", 'ת"ז', 'ID']):
                    rename_map[col] = "תעודת זהות"
            if rename_map:
                df.rename(columns=rename_map, inplace=True)
                
            if 'תעודת זהות' in df.columns:
                df['תעודת זהות'] = df['תעודת זהות'].str.replace('.0', '', regex=False).str.strip()
            return df
        except:
            return pd.DataFrame()
    return pd.DataFrame()

def save_data(df):
    df = df.fillna('').astype(str)
    df.to_excel(DATA_FILE, index=False)

def clean_id(val):
    return str(val).strip().split('.')[0]

def process_file(uploaded_file):
    try:
        df = pd.read_excel(uploaded_file)
        original_columns = df.columns.astype(str).str.strip().tolist()
        df.columns = original_columns
        
        rename_map = {
            "ת.ז": "תעודת זהות", "ת'ז": "תעודת זהות", "תז": "תעודת זהות", "ת.ז.": "תעודת זהות",
            "מספר זהות": "תעודת זהות", "מס' זהות": "תעודת זהות", "מס זהות": "תעודת זהות",
            "מספר זהות עובד": "תעודת זהות", "ID": "תעודת זהות", "id": "תעודת זהות",
            "שם עובד": "שם", "שם מלא": "שם", "שם": "שם",
            "מעסיק": "מקום העסקה", "חברה": "מקום העסקה", "שם מעסיק": "מקום העסקה",
            "תקופה": "תקופת העסקה", "שנה": "תקופת העסקה", "תאריך": "תקופת העסקה"
        }
        
        # זיהוי אוטומטי נוסף
        for col in original_columns:
            if col not in rename_map.values():
                if any(key in col for key in ["זהות", "ת.ז", 'ת"ז', 'ID']):
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
            st.error(f"⚠️ בקובץ '{uploaded_file.name}' לא נמצאה עמודת תעודת זהות. העמודות הן: {original_columns}")
            return pd.DataFrame()
        
        df['מקור קובץ'] = uploaded_file.name
        required = ['שם', 'תעודת זהות', 'תקופת העסקה', 'מקום העסקה', 'מקור קובץ']
        existing = [c for c in required if c in df.columns]
        return df[existing].fillna('').astype(str)
    except Exception as e:
        st.error(f"שגיאה בעיבוד הקובץ {uploaded_file.name}: {e}")
        return pd.DataFrame()

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
            if not master_df.empty:
                updated_master = pd.concat([master_df, combined_new], ignore_index=True)
            else:
                updated_master = combined_new
            save_data(updated_master)
            st.success('הנתונים נוספו בהצלחה.')
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
        if s_name and 'שם' in res.columns: res = res[res['שם'].str.contains(s_name, na=False)]
        if s_id and 'תעודת זהות' in res.columns: res = res[res['תעודת זהות'].str.contains(s_id, na=False)]
        st.dataframe(res, use_container_width=True)

    st.divider()
    st.subheader('👥 איתור כפילויות')
    
    if st.button('🔍 אתר כפילויות'):
        # בדיקה אם עמודת תעודת זהות קיימת (אחרי הניסיון לנרמל בטעינה)
        col_to_check = None
        if 'תעודת זהות' in master_df.columns:
            col_to_check = 'תעודת זהות'
        else:
            # מוצאים את העמודה שמתנהגת כמו תעודת זהות
            for col in master_df.columns:
                if any(key in col for key in ["זהות", "ת.ז", 'ת"ז', 'ID']):
                    col_to_check = col
                    break
        
        if col_to_check:
            valid_df = master_df[master_df[col_to_check] != '']
            is_duplicate = valid_df.duplicated(subset=[col_to_check], keep=False)
            dupes = valid_df[is_duplicate].copy()
            
            if not dupes.empty:
                dupes_sorted = dupes.sort_values(by=[col_to_check])
                display_cols = ['תעודת זהות', col_to_check, 'שם', 'מקום העסקה', 'תקופת העסקה', 'מקור קובץ']
                final_cols = [c for c in display_cols if c in dupes_sorted.columns]
                # הסרת כפילות אם 'תעודת זהות' ו-col_to_check הם אותו דבר
                final_cols = list(dict.fromkeys(final_cols))
                
                st.warning(f"נמצאו {dupes[col_to_check].nunique()} עובדים כפולים.")
                st.dataframe(dupes_sorted[final_cols], use_container_width=True)
                
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    dupes_sorted[final_cols].to_excel(writer, index=False)
                st.download_button('📥 הורד אקסל', output.getvalue(), 'duplicates.xlsx')
            else: st.success('אין כפילויות.')
        else:
            st.error(f"לא זוהתה עמודת זהות. העמודות הקיימות במאגר: {list(master_df.columns)}")

    with st.expander('צפה במאגר המלא'):
        st.write(master_df)
else:
    st.info('המערכת ריקה. העלה קבצים מימין.')
