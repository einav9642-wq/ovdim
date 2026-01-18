import streamlit as st
import pandas as pd
import os
uploaded_file = st.file_uploader("בחר קובץ אקסל")

if uploaded_file is not None:
    # הגדרת הנתיב שבו נרצה לשמור (תיקיית data בתוך הפרויקט)
    folder_path = "data"
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        
    file_path = os.path.join(folder_path, uploaded_file.name)
    
    # כתיבת הקובץ לתיקייה
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
        
    st.success(f"הקובץ נשמר בהצלחה בכתובת: {file_path}")
# 1. הגדרות תצוגה
st.set_page_config(page_title="מערכת ניתוח עובדים", layout="wide")

# 2. עיצוב עברית (RTL), גופן Heebo ויישור כותרות לימין
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Heebo:wght@400;700&display=swap');
    
    /* יישור כללי לימין ושינוי גופן */
    html, body, [data-testid="stSidebar"], .main {
        direction: rtl;
        text-align: right;
        font-family: 'Heebo', sans-serif;
    }

    /* יישור כותרות (h1, h2, h3) לימין */
    h1, h2, h3, h4, p, label {
        font-family: 'Heebo', sans-serif !important;
        direction: rtl;
        text-align: right !important;
    }

    /* תיקון ספציפי לכותרת הראשית של Streamlit */
    .stMarkdown h1 {
        text-align: right !important;
    }

    /* עיצוב ויישור כפתורים */
    .stButton>button { 
        width: 100%; 
        border-radius: 10px; 
        font-weight: 700; 
    }
    
    /* יישור תיבות קלט */
    input { 
        text-align: right; 
        direction: rtl !important; 
    }
    
    /* יישור טבלאות לימין */
    .stDataFrame, [data-testid="stTable"] { 
        direction: rtl; 
        text-align: right; 
    }

    /* יישור לשוניות (Tabs) */
    button[data-baseweb="tab"] {
        direction: rtl;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. מנגנון סיסמה
PASSWORD = "123"

if "password_correct" not in st.session_state:
    st.session_state["password_correct"] = False

if not st.session_state["password_correct"]:
    st.title("🔒 כניסה למערכת")
    pwd = st.text_input("הכנס סיסמה:", type="password")
    if st.button("התחבר"):
        if pwd == PASSWORD:
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("סיסמה שגויה")
    st.stop()

# --- תוכן האפליקציה ---

# 4. לוגו מוגדל (450)
if os.path.exists("logo.png"):
    st.image("logo.png", width=450)

# הכותרת כעת תיושר לימין בזכות ה-CSS למעלה
st.title("🔍 מערכת ניתוח נתונים")

# 5. טעינת נתונים מתיקיית data
data_folder = "data"
all_data = []

if not os.path.exists(data_folder):
    os.makedirs(data_folder)

excel_files = [f for f in os.listdir(data_folder) if f.endswith(('.xlsx', '.xls'))]

if excel_files:
    for f in excel_files:
        try:
            file_path = os.path.join(data_folder, f)
            df = pd.read_excel(file_path)
            df.columns = df.columns.astype(str).str.strip()
            all_data.append(df)
        except Exception as e:
            st.error(f"שגיאה בקריאת הקובץ {f}: {e}")
    
    st.sidebar.success(f"נטענו {len(excel_files)} קבצים")
else:
    st.sidebar.warning("לא נמצאו קבצי אקסל בתיקיית data")

# 6. הצגת נתונים וחיפוש
if all_data:
    full_df = pd.concat(all_data, ignore_index=True)
    
    possible_id_cols = ['ת.ז', 'ת.ז.', 'תעודת זהות', 'ID', 'מספר זהות']
    id_col = next((col for col in possible_id_cols if col in full_df.columns), None)

    if id_col:
        full_df[id_col] = full_df[id_col].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()

        tab1, tab2 = st.tabs(["🔎 חיפוש פרטני", "👯 איתור כפילויות"])

        with tab1:
            search_id = st.text_input("הכנס מספר זהות לחיפוש:")
            if search_id:
                results = full_df[full_df[id_col] == search_id.strip()]
                if not results.empty:
                    st.dataframe(results, use_container_width=True, hide_index=True)
                else:
                    st.info("לא נמצאו תוצאות למספר זהות זה")

        with tab2:
            if st.button("בדוק כפילויות"):
                duplicates = full_df[full_df.duplicated(subset=[id_col], keep=False)]
                if not duplicates.empty:
                    st.warning(f"נמצאו {duplicates[id_col].nunique()} מספרי זהות כפולים")
                    st.dataframe(duplicates.sort_values(by=id_col), use_container_width=True, hide_index=True)
                else:
                    st.success("לא נמצאו כפילויות במאגר")
    else:
        st.error("לא נמצאה עמודת תעודת זהות בקבצים")

if st.sidebar.button("התנתק"):
    st.session_state["password_correct"] = False
    st.rerun()

