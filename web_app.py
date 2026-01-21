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
            return df.fillna('').astype(str)
        except:
            return pd.DataFrame()
    return pd.DataFrame()

def save_data(df):
    df.to_excel(DATA_FILE, index=False)

def clean_id(val):
    return str(val).strip().split('.')[0]

def process_file(uploaded_file):
    """מעבד קובץ ומנסה לנרמל עמודות"""
    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.astype(str).str.strip()
    
    # מילון שמות מורחב מאוד
    rename_map = {
        "ת.ז": "תעודת זהות", "ת'ז": "תעודת זהות", "תז": "תעודת זהות", "ת.ז.": "תעודת זהות",
        "מספר זהות": "תעודת זהות", "מס' זהות": "תעודת זהות", "מס זהות": "תעודת זהות",
        "זהות": "תעודת זהות", "ID": "תעודת זהות", "id": "תעודת זהות", "מספר": "תעודת זהות",
        "שם עובד": "שם", "שם מלא": "שם", "שם": "שם", "עובד": "שם",
        "מעסיק": "מקום העסקה", "חברה": "מקום העסקה", "שם מעסיק": "מקום העסקה",
        "תקופה": "תקופת העסקה", "שנה": "תקופת העסקה", "תאריך": "תקופת העסקה"
    }
    
    df.rename(columns=rename_map, inplace=True)
    return df

# --- ממשק המשתמש ---
st.title('📂 מערכת חכמה לניהול והצלבת נתוני עובדים')

master_df = load_data()

with st.sidebar:
    st.header('1. טעינת קבצים')
    uploaded_files = st.file_uploader('בחר קבצי אקסל (אפשר כמה)', type=['xlsx'], accept_multiple_files=True)
    
    if uploaded_files:
        st.info(f"נטענו {len(uploaded_files)} קבצים. וודא זיהוי עמודות:")
        
        all_processed_data = []
        for f in uploaded_files:
            temp_df = process_file(f)
            
            # אם לא זוהתה תעודת זהות או שם, נאפשר למשתמש לבחור ידנית
            cols = list(temp_df.columns)
            
            with st.expander(f"הגדרות עבור: {f.name}"):
                id_col = st.selectbox(f"בחר עמודת תעודת זהות עבור {f.name}", 
                                    options=cols, 
                                    index=cols.index("תעודת זהות") if "תעודת זהות" in cols else 0)
                name_col = st.selectbox(f"בחר עמודת שם עבור {f.name}", 
                                      options=cols, 
                                      index=cols.index("שם") if "שם" in cols else 0)
                
                if st.button(f"אשר והוסף את {f.name}"):
                    final_df = temp_df.copy()
                    final_df['תעודת זהות'] = final_df[id_col].apply(clean_id)
                    final_df['שם'] = final_df[name_col]
                    final_df['מקור קובץ'] = f.name
                    
                    # שמירה רק של עמודות רלוונטיות
                    target_cols = ['תעודת זהות', 'שם', 'מקום העסקה', 'תקופת העסקה', 'מקור קובץ']
                    available = [c for c in target_cols if c in final_df.columns]
                    
                    all_processed_data.append(final_df[available])
                    st.success(f"{f.name} מוכן להוספה")

        if all_processed_data and st.button('🚀 הוסף את כל המאושרים למאגר'):
            new_batch = pd.concat(all_processed_data, ignore_index=True)
            updated_master = pd.concat([master_df, new_batch], ignore_index=True)
            save_data(updated_master)
            st.success("הנתונים עודכנו במאגר!")
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
    st.subheader('🔍 חיפוש ואיתור כפילויות')
    
    # חיפוש
    c1, c2 = st.columns(2)
    with c1: s_name = st.text_input('חפש לפי שם')
    with c2: s_id = st.text_input('חפש לפי תעודת זהות')
    
    if s_name or s_id:
        res = master_df.copy()
        if s_name: res = res[res['שם'].str.contains(s_name, na=False)]
        if s_id: res = res[res['תעודת זהות'].str.contains(s_id, na=False)]
        st.dataframe(res, use_container_width=True)

    st.divider()
    
    if st.button('🔍 אתר כפילויות עכשיו'):
        # וידוא שקיימת עמודת זהות
        if 'תעודת זהות' in master_df.columns:
            valid_df = master_df[master_df['תעודת זהות'] != '']
            is_duplicate = valid_df.duplicated(subset=['תעודת זהות'], keep=False)
            dupes = valid_df[is_duplicate].copy()
            
            if not dupes.empty:
                dupes_sorted = dupes.sort_values(by=['תעודת זהות'])
                st.warning(f"נמצאו {dupes['תעודת זהות'].nunique()} עובדים כפולים.")
                st.dataframe(dupes_sorted, use_container_width=True)
                
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    dupes_sorted.to_excel(writer, index=False)
                st.download_button('📥 הורד דוח כפילויות', output.getvalue(), 'duplicates.xlsx')
            else:
                st.success("לא נמצאו כפילויות.")
        else:
            st.error("לא נמצאה עמודת 'תעודת זהות' במאגר. נסה לאפס ולהעלות מחדש תוך בחירה נכונה של העמודות.")

    with st.expander('צפה במאגר המלא'):
        st.write(master_df)
else:
    st.info('המערכת ריקה. העלה קבצים דרך התפריט בצד.')
