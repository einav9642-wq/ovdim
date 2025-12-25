import streamlit as st
import pandas as pd
import os

# 1. הגדרות דף רחב
st.set_page_config(page_title="מערכת ניהול עובדים", layout="wide")

# 2. עיצוב עברית (RTL), גופן Heebo והגדלת רכיבים
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Heebo:wght@400;700&display=swap');
    
    /* יישור כללי לימין */
    html, body, [data-testid="stSidebar"], .main {
        direction: rtl;
        text-align: right;
        font-family: 'Heebo', sans-serif;
    }

    /* יישור תיבות טקסט ותוויות */
    .stTextInput label, .stSelectbox label, .stMultiSelect label {
        text-align: right !important;
        display: block;
    }
    
    input {
        direction: rtl !important;
        text-align: right !important;
    }

    /* יישור כפתורים וטבלאות */
    div.stButton > button {
        width: 100%;
        border-radius: 10px;
    }
    
    .stDataFrame, [data-testid="stTable"] {
        direction: rtl;
        text-align: right;
    }

    /* תיקון ללשוניות (Tabs) שיהיו מימין לשמאל */
    button[data-baseweb="tab"] {
        direction: rtl;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. מנגנון סיסמה
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

# --- תוכן האתר (מוצג רק לאחר התחברות) ---

# 4. לוגו (מוגדל ל-450) וכותרת
if os.path.exists("logo.png"):
    st.image("logo.png", width=450)

st.title("🔍 מערכת ניתוח ובקרת נתונים")

# 5. טעינת נתונים אוטומטית מתיקיית data
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
    
    # חיפוש עמודת ת"ז לפי שמות נפוצים
    id_cols = ['ת.ז', 'ת.ז.', 'תעודת זהות', 'ID', 'מספר זהות']
    id_col = next((c for c in id_cols if c in df.columns), None)

    if id_col:
        # ניקוי נתוני ת"ז
        df[id_col] = df[id_col].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
        
        # תפריט לשוניות
        t1, t2 = st.tabs(["🔎 חיפוש פרטני", "👯 איתור כפילויות"])
        
        with t1:
            sid = st.text_input("הכנס תעודת זהות לחיפוש:")
            if sid:
                res = df[df[id_col] == sid.strip()]
                if not res.empty:
                    st.success(f"נמצאו {len(res)} רשומות")
                    st.dataframe(res, use_container_width=True, hide_index=True)
                else:
                    st.info("לא נמצאו תוצאות עבור תז זו")
        
        with t2:
            st.write("בדיקת כפילויות על בסיס מספר תעודת זהות")
            if st.button("בצע סריקת כפילויות"):
                dups = df[df.duplicated(subset=[id_col], keep=False)]
                if not dups.empty:
                    st.warning("נמצאו כפילויות במאגר")
                    st.dataframe(dups.sort_values(by=id_col), use_container_width=True, hide_index=True)
                else:
                    st.success("לא נמצאו כפילויות - המאגר תקין")
    else:
        st.error("לא נמצאה עמודת תעודת זהות בקבצים")
else:
    st.warning("נא לוודא שקיימים קבצי אקסל בתיקיית data ב-GitHub")

# כפתור התנתקות בתפריט הצד
if st.sidebar.button("התנתק"):
    st.session_state["password_correct"] = False
    st.rerun()
