import streamlit as st
import pandas as pd
import os

# הגדרת סיסמה
PASSWORD = "123" # שנה לסיסמה שלך

def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    if st.session_state["password_correct"]:
        return True

    st.title("🔒 כניסה למאגר הנתונים")
    user_password = st.text_input("הכנס סיסמה:", type="password")
    if st.button("התחבר"):
        if user_password == PASSWORD:
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("סיסמה שגויה")
    return False

if check_password():
    st.title("🔍 מערכת ניתוח מאגר קבוע")
    
    # --- טעינת נתונים אוטומטית מתיקיית data ---
    data_folder = "data"
    all_data = []

    if os.path.exists(data_folder):
        excel_files = [f for f in os.listdir(data_folder) if f.endswith(('.xlsx', '.xls'))]
        
        if excel_files:
            for f in excel_files:
                try:
                    file_path = os.path.join(data_folder, f)
                    # שימוש ב-timestamp כדי למנוע טעינה של נתונים ישנים מהזיכרון
                    df = pd.read_excel(file_path)
                    df.columns = df.columns.astype(str).str.strip()
                    df['מקור הקובץ'] = f
                    all_data.append(df)
                except Exception as e:
                    st.error(f"שגיאה בקריאת הקובץ {f}: {e}")
            
            st.sidebar.success(f"נטענו {len(excel_files)} קבצים מהמאגר")
        else:
            st.sidebar.warning("לא נמצאו קבצי אקסל בתיקיית data")
    else:
        st.sidebar.error("תיקיית data לא קיימת ב-GitHub")

    if all_data:
        full_df = pd.concat(all_data, ignore_index=True)
        
        # זיהוי עמודת ת.ז
        possible_id_columns = ['ת.ז', 'ת.ז.', 'תעודת זהות', 'ID', 'מספר זהות']
        id_col = next((col for col in possible_id_columns if col in full_df.columns), None)

        if id_col:
            full_df[id_col] = full_df[id_col].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()

            tab1, tab2 = st.tabs(["🔎 חיפוש פרטני", "👯 איתור כפילויות"])

            with tab1:
                search_id = st.text_input("הכנס תעודת זהות לחיפוש:")
                if search_id:
                    results = full_df[full_df[id_col] == search_id.strip()]
                    if not results.empty:
                        st.write(f"נמצאו {len(results)} רשומות:")
                        st.dataframe(results)
                    else:
                        st.info("לא נמצאו נתונים עבור ת.ז זו במאגר")

            with tab2:
                if st.button("בצע בדיקת כפילויות גלובלית"):
                    duplicates = full_df[full_df.duplicated(subset=[id_col], keep=False)]
                    if not duplicates.empty:
                        st.warning(f"נמצאו {duplicates[id_col].nunique()} מספרי ת.ז כפולים")
                        st.dataframe(duplicates.sort_values(by=id_col))
                        
                        csv = duplicates.to_csv(index=False).encode('utf-8-sig')
                        st.download_button("הורד דוח כפילויות (CSV)", data=csv, file_name="duplicates_report.csv")
                    else:
                        st.success("לא נמצאו כפילויות במאגר הנוכחי")
        else:
            st.error("לא נמצאה עמודת ת.ז באף אחד מהקבצים במאגר")
    
    if st.sidebar.button("התנתק"):
        st.session_state["password_correct"] = False
        st.rerun()
