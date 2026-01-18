import streamlit as st
import pandas as pd
import os
import io

# --- הגדרות דף ---
st.set_page_config(page_title='ניהול נתוני עובדים', layout='wide')
DATA_FILE = 'master_data.xlsx'

# --- פונקציות עזר ---
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
        'ת.ז': 'תעודת זהות',
        'מספר זהות': 'תעודת זהות',
        'שם עובד': 'שם',
        'מעסיק': 'מקום העסקה',
        'תקופה': 'תקופת העסקה'
    }
    df.rename(columns=rename_map, inplace=True)
    
    required_columns = ['שם', 'תעודת זהות', 'תקופת העסקה', 'מקום העסקה']
    existing_cols = [col for col in required_columns if col in df.columns]
    return df[existing_cols]

# --- ממשק המשתמש ---
st.title('📂 מערכת לניהול וניתוח נתוני עובדים')

with st.sidebar:
    st.header('1. ניהול נתונים')
    uploaded_file = st.file_uploader('העלה קובץ אקסל חדש', type=['xlsx'])
    if uploaded_file:
        if st.button('✅ הוסף למאגר'):
            new_data = process_and_filter(uploaded_file)
            current_df = load_data()
            combined_df = pd.concat([current_df, new_data], ignore_index=True)
            save_data(combined_df)
            st.success('הנתונים נוספו!')
            st.rerun()

    st.divider()
    if st.button('🗑️ איפוס מאגר הנתונים'):
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)
            st.warning('המאגר אופס ונמחק.')
            st.rerun()

master_df = load_data()

# מסך פתיחה נקי
if not master_df.empty:
    # --- חלק 2: חיפוש ---
    st.subheader('🔍 חיפוש עובד')
    col1, col2 = st.columns(2)
    with col1:
        s_name = st.text_input('חפש לפי שם')
    with col2:
        s_id = st.text_input('חפש לפי תעודת זהות')
    
    if s_name or s_id:
        res = master_df.copy()
        if s_name:
            res = res[res['שם'].astype(str).str.contains(s_name, na=False)]
        if s_id:
            res = res[res['תעודת זהות'].astype(str).str.contains(s_id, na=False)]
        
        if not res.empty:
            st.write(f'נמצאו {len(res)} תוצאות:')
            st.dataframe(res, use_container_width=True)
        else:
            st.info('לא נמצאו תוצאות לחיפוש זה.')

    st.divider()

    # --- חלק 3: איתור כפילויות ---
    st.subheader('👥 איתור כפילויות במערכת')
    
    if st.button('🔍 הצג רשימת כפילויות בלבד'):
        if 'תעודת זהות' in master_df.columns:
            # מציאת כל המופעים של תעודות זהות שחוזרות על עצמן
            is_duplicate = master_df.duplicated(subset=['תעודת זהות'], keep=False)
            dupes = master_df[is_duplicate].copy()
            
            if not dupes.empty:
                st.warning(f'נמצאו {dupes["תעודת זהות"].nunique()} עובדים עם רשומות כפולות:')
                dupes_sorted = dupes.sort_values(by=['תעודת זהות'])
                
                display_cols = ['תעודת זהות', 'שם', 'מקום העסקה', 'תקופת העסקה']
                final_cols = [c for c in display_cols if c in dupes_sorted.columns]
                
                # הצגת הטבלה המסוננת
                st.dataframe(dupes_sorted[final_cols], use_container_width=True)
                
                # ייצוא לאקסל
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    dupes_sorted[final_cols].to_excel(writer, index=False)
                
                st.download_button(
                    label='📥 הורד את רשימת הכפילויות לאקסל',
                    data=output.getvalue(),
                    file_name='duplicate_workers.xlsx',
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
            else:
                st.success('לא נמצאו כפילויות במערכת. כל עובד מופיע פעם אחת בלבד.')
        else:
            st.error('לא ניתן לבצע בדיקה - עמודת תעודת זהות חסרה.')

    st.divider()
    with st.expander('צפה בכל נתוני המאגר (ניהול פנימי)'):
        st.write(master_df)

else:
    st.info('המערכת מוכנה. אנא העלה קובץ אקסל דרך התפריט בצד כדי להתחיל.')
