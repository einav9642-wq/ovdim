import streamlit as st
import pandas as pd
import os

# 1. הגדרות דף
st.set_page_config(page_title="מערכת עובדים", layout="wide")

# 2. עיצוב (CSS) פשוט ונקי למניעת שגיאות תצוגה
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Heebo:wght@400;700&display=swap');
    html, body, [data-testid="stSidebar"], .main {
        direction: rtl;
        text-align: right;
        font-family: 'Heebo', sans-serif;
    }
    div.stButton > button { width: 100%; border-radius: 10px; }
    input { text-align: right; direction: rtl; }
    </style>
    """, unsafe_allow_html=True)

# 3. מערכת סיסמה
if "password_correct" not in st.session_state:
    st.session_state["password_correct"] = False

if not st.session_state["password_correct"]:
    st.title("🔒 כניסה למערכת")
    pwd = st.text_input("הכנס סיסמה:", type="password")
    if st.button("התחבר"):
        if pwd == "123":
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("סיסמה שגויה")
    st.stop()

# --- אם הגענו כאן, המשתמש מחובר ---

# 4. לוגו וכותרת
if os.path.exists("logo.png"):
    st.image("logo.png", width=150)

st.title("🔍 מערכת ניתוח נתונים")

# 5. טעינת נתונים
data_folder = "data"
all_data = []

if os.path.exists(data_folder):
    files = [f for f in os.listdir(data_folder) if f.endswith(('.xlsx', '.xls'))]
    for f in files:
        try:
            temp_df = pd.read_excel(os.path.join(data_folder, f))
            temp_df.columns = temp_df.columns.astype(str).str.strip()
            all_data.append(temp_df)
        except:
            continue

if all_data:
    df = pd.concat(all_data, ignore_index=True)
    
    # חיפוש עמודת ת"ז
    id_cols = ['ת.ז', 'ת.ז.', 'תעודת זהות', 'ID', 'מספר זהות']
    id_col = next((c for c in id_cols if c in df.columns), None)

    if id_col:
        df[id_col] = df[id_col].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
        
        t1, t2 = st.tabs(["🔎 חיפוש", "👯 כפילויות"])
        
        with t1:
            sid = st.text_input("חפש לפי תעודת זהות:")
            if sid:
                res = df[df[id_col] == sid.strip()]
                if not res.empty:
                    st.dataframe(res, use_container_width=True, hide_index=True)
                else:
                    st.info("לא נמצאו תוצאות")
        
        with t2:
            if st.button("בצע בדיקת כפילויות"):
                dups = df[df.duplicated(subset=[id_col], keep=False)]
                if not dups.empty:
                    st.warning(f"נמצאו כפילויות")
                    st.dataframe(dups.sort_values(by=id_col), use_container_width=True, hide_index=True)
                else:
                    st.success("אין כפילויות")
else:
    st.info("נא לוודא שיש קבצים בתיקיית data ב-GitHub")

# כפתור התנתקות
if st.sidebar.button("התנתק"):
    st.session_state["password_correct"] = False
    st.rerun()
