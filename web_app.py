import streamlit as st
import pandas as pd
import os

# 1. הגדרות תצוגה כלליות
st.set_page_config(page_title="מערכת ניתוח עובדים", layout="wide")

# 2. פונקציה לעיצוב האתר בעברית (RTL) ושימוש בגופן Heebo
def local_css():
    st.markdown(
        """
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;700&display=swap" rel="stylesheet">
        <style>
        /* הגדרת גופן וכיוון לכל האתר */
        html, body, [data-testid="stSidebar"], .main, stApp {
            direction: rtl;
            text-align: right;
            font-family: 'Heebo', sans-serif;
        }
        
        /* החלת הגופן על כותרות ורכיבי טקסט */
        h1, h2, h3, h4, p, label, .stButton, .stTextInput, .stSelectbox, .stDataFrame {
            font-family: 'Heebo', sans-serif !important;
            direction: rtl;
            text-align: right !important;
        }

        /* עיצוב כפתורים */
        .stButton>button {
            width: 100%;
            border-radius: 10px;
            font-weight: 700;
        }

        /* יישור תיבות הטקסט */
        input {
            text-align: right;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

local_css()

# 3. מנגנון סיסמה
PASSWORD = "123" # ניתן לשנות לסיסמה הרצויה

def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    
    if st.session_state["password_correct"]:
        return True

    st.title("🔒 כניסה למערכת")
    user_password = st.text_input("הכנס סיסמה:", type="password")
    if st.button("התחבר"):
        if user_password == PASSWORD:
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("סיסמה שגויה, נסה שוב.")
    return False

# 4. תוכן האפליקציה (יוצג רק לאחר התחברות)
if check_password():
    # הצגת לוגו במידה וקיים
    if os.path.exists("logo.png"):
        st.image("logo.png", width=150)
    
    st.title("🔍 מערכת ניתוח ובקרה")
    
    # טעינת נתונים מתיקיית data
    data_folder = "data"
    all_data = []

    if os.path.exists(data_folder):
        excel_files = [f for f in os.listdir(data_folder) if f.endswith(('.xlsx', '.xls'))]
        
        if excel_files:
            for f in excel_files:
                try:
                    file_path = os.path.join(data_folder, f)
                    df = pd.read_excel(file_path)
                    # ניקוי שמות עמודות
                    df.columns = df.columns.astype(str).str.strip()
                    all_data.append(df)
                except Exception as e:
                    st.error(f"שגיאה בקריאת הקובץ {f}: {e}")
            
            st.sidebar.success(f"נטענו {len(excel_files)} קבצים מהמאגר")
        else:
            st.sidebar.warning("לא נמצאו קבצים בתיקיית data")
    else:
        st.sidebar.error("תיקיית data לא נמצאה")

    # ניתוח הנתונים
    if all_data:
        full_df = pd.concat(all_data, ignore_index=True)
        
        # זיהוי עמודת ת.ז
        possible_id_columns = ['ת.ז', 'ת.ז.', 'תעודת זהות', 'ID', 'מספר זהות']
        id_col = next((col for col in possible_id_columns if col in full_df.columns), None)

        if id_col:
            # ניקוי פורמט ת"ז
            full_df[id_col] = full_df[id_col].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()

            # יצירת לשוניות
            tab1, tab2 = st.tabs(["🔎 חיפוש פרטני", "👯 איתור כפילויות"])

            with tab1:
                search_id = st.text_input("הכנס תעודת זהות לחיפוש:")
                if search_id:
                    results = full_df[full_df[id_col] == search_id.strip()]
                    if not results.empty:
                        st.success(f"נמצאו {len(results)} רשומות:")
                        # הצגת הטבלה ללא עמודת האינדקס
                        st.dataframe(results, use_container_width=True, hide_index=True)
                    else:
                        st.info("לא נמצאו נתונים עבור ת.ז זו")

            with tab2:
                if st.button("בצע בדיקת כפילויות"):
                    duplicates = full_df[full_df.duplicated(subset=[id_col], keep=False)]
                    if not duplicates.empty:
                        st.warning(f"נמצאו {duplicates[id_col].nunique()} מספרי ת.ז המופיעים יותר מפעם אחת")
                        # הצגת הטבלה ללא עמודת האינדקס
                        st.dataframe(duplicates.sort_values(by=id_col), use_container_width=True, hide_index=True)
                    else:
                        st.success("לא נמצאו כפילויות במאגר")
        else:
            st.error("לא נמצאה עמודת תעודת זהות בקבצים")
    
    # כפתור התנתקות בתפריט הצד
    if st.sidebar.button("התנתק מהמערכת"):
        st.session_state["password_correct"] = False
        st.rerun()
