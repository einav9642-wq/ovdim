import streamlit as st
import pandas as pd
import os

# --- הגדרות קובץ ---
DATA_FILE = "master_data.xlsx"

def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_excel(DATA_FILE)
    return pd.DataFrame()

# --- ממשק המשתמש ---
st.title("🔍 ניתוח כפילויות והיסטוריית העסקה")

master_df = load_data()

if not master_df.empty:
    # כפתור איתור כפילויות
    if st.button("אתר כפילויות (הצג היסטוריית העסקה)"):
        # מציאת כל השורות שבהן הת.ז מופיעה יותר מפעם אחת
        # keep=False מבטיח שנראה את כל המופעים של אותה ת.ז
        duplicates = master_df[master_df.duplicated(subset=['תעודת זהות'], keep=False)]
        
        if not duplicates.empty:
            st.warning(f"נמצאו {duplicates['תעודת זהות'].nunique()} עובדים עם מספר רשומות במערכת:")
            
            # מיון לפי ת.ז כדי שהכפילויות יופיעו אחת מתחת לשנייה
            duplicates_sorted = duplicates.sort_values(by=['תעודת זהות', 'תקופת העסקה'])
            
            # הצגת הטבלה עם העמודות הרלוונטיות בלבד שביקשת
            display_cols = ['תעודת זהות', 'שם', 'מקום העסקה', 'תקופת העסקה']
            st.dataframe(duplicates_sorted[display_cols], use_container_width=True)
            
            # אפשרות ייצא לדו"ח אקסל של הכפילויות בלבד
            with pd.ExcelWriter("duplicates_report.xlsx") as writer:
                duplicates_sorted.to_excel(writer, index=False)
            
            with open("duplicates_report.xlsx", "rb") as file:
                st.download_button(
                    label="📥 הורד דו"ח כפילויות לאקסל",
                    data=file,
                    file_name="כפילויות_עובדים.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        else:
            st.success("לא נמצאו מספרי תעודת זהות כפולים. כל עובד מופיע פעם אחת בלבד.")
else:
    st.info("המאגר ריק. אנא העלה נתונים כדי לבצע בדיקת כפילויות.")
