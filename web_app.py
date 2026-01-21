import streamlit as st
import pandas as pd
import os
import io

# --- הגדרות דף ---
st.set_page_config(page_title="ניהול נתוני עובדים", layout="wide")
DATA_FILE = "master_data.xlsx"

# אתחול זיכרון זמני לקבצים מאושרים
if "approved_files_data" not in st.session_state:
    st.session_state["approved_files_data"] = {}

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_excel(DATA_FILE)
            df.columns = df.columns.astype(str).str.strip()
            return df.fillna("").astype(str)
        except:
            return pd.DataFrame()
    return pd.DataFrame()

def save_data(df):
    df.to_excel(DATA_FILE, index=False)

def clean_id(val):
    return str(val).strip().split(".")[0]

def process_file_structure(uploaded_file):
    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.astype(str).str.strip()
    return df

# --- ממשק המשתמש ---
st.title("📂 מערכת ניתוח נתוני עובדים - תהליך טעינה חכם")

master_df = load_data()

with st.sidebar:
    st.header("1. טעינת קבצים")
    uploaded_files = st.file_uploader("בחר קבצי אקסל (אפשר כמה)", type=["xlsx"], accept_multiple_files=True)
    
    if uploaded_files:
        st.info(f"נטענו {len(uploaded_files)} קבצים להגדרה.")
        
        for f in uploaded_files:
            # אם הקובץ כבר אושר
            if f.name in st.session_state["approved_files_data"]:
                col_a, col_b = st.columns([4, 1])
                col_a.success(f"✅ {f.name}")
                if col_b.button("✖️", key=f"del_{f.name}", help="ביטול אישור קובץ"):
                    del st.session_state["approved_files_data"][f.name]
                    st.rerun()
                continue
                
            temp_df = process_file_structure(f)
            cols = list(temp_df.columns)
            
            with st.expander(f"⚙️ הגדר עמודות עבור: {f.name}"):
                # זיהוי אוטומטי של אינדקסים
                def find_idx(keywords, columns):
                    for i, col in enumerate(columns):
                        if any(k in col for k in keywords): return i
                    return 0

                id_idx = find_idx(["זהות", "ת.ז", "תז", "ID"], cols)
                name_idx = find_idx(["שם", "עובד"], cols)
                emp_idx = find_idx(["מעסיק", "חברה", "מקום"], cols)
                period_idx = find_idx(["תקופה", "שנה", "תאריך"], cols)

                # שימוש בגרשיים משולבים למניעת שגיאת סינטקס
                id_col = st.selectbox(f"עמודת ת'ז ({f.name})", cols, index=id_idx)
                name_col = st.selectbox(f"עמודת שם ({f.name})", cols, index=name_idx)
                employer_col = st.selectbox(f"עמודת מעסיק ({f.name})", cols, index=emp_idx)
                time_col = st.selectbox(f"עמודת תקופה ({f.name})", cols, index=period_idx)
                
                if st.button(f"אשר את {f.name}", key=f"btn_{f.name}"):
                    final_df = temp_df.copy()
                    final_df["תעודת זהות"] = final_df[id_col].apply(clean_id)
                    final_df["שם"] = final_df[name_col].astype(str)
                    final_df["מקום העסקה"] = final_df[employer_col].astype(str)
                    final_df["תקופת העסקה"] = final_df[time_col].astype(str)
                    final_df["מקור קובץ"] = f.name
                    
                    selected = ["תעודת זהות", "שם", "מקום העסקה", "תקופת העסקה", "מקור קובץ"]
                    st.session_state["approved_files_data"][f.name] = final_df[selected]
                    st.rerun()

        # כפתור הוספה סופי למאגר
        if st.session_state["approved_files_data"]:
            st.divider()
            st.warning(f"ממתינים להוספה: {len(st.session_state['approved_files_data'])} קבצים")
            if st.button("🚀 העלה את כל המאושרים למאגר"):
                new_batch = pd.concat(st.session_state["approved_files_data"].values(), ignore_index=True)
                updated_master = pd.concat([master_df, new_batch], ignore_index=True)
                save_data(updated_master)
                st.session_state["approved_files_data"] = {} 
                st.success("הנתונים נשמרו בהצלחה!")
                st.rerun()

    st.divider()
    if st.button("🗑️ איפוס מאגר מוחלט"):
        if os.path.exists(DATA_FILE): os.remove(DATA_FILE)
        st.session_state.clear()
        st.rerun()

# --- גוף האפליקציה ---
if not master_df.empty:
    st.subheader("🔍 חיפוש וניתוח")
    
    with st.expander("📄 רשימת הקבצים במאגר"):
        if "מקור קובץ" in master_df.columns:
            for fn in master_df["מקור קובץ"].unique():
                st.text(f"• {fn}")

    c1, c2 = st.columns(2)
    with c1: s_name = st.text_input("חפש לפי שם")
    with c2: s_id = st.text_input("חפש לפי תעודת זהות")
    
    if s_name or s_id:
        res = master_df.copy()
        if s_name: res = res[res["שם"].str.contains(s_name, na=False)]
        if s_id: res = res[res["תעודת זהות"].str.contains(s_id, na=False)]
        st.dataframe(res, use_container_width=True)

    st.divider()
    
    if st.button("🔍 אתר כפילויות עכשיו"):
        valid_df = master_df[master_df["תעודת זהות"].str.strip() != ""]
        is_duplicate = valid_df.duplicated(subset=["תעודת זהות"], keep=False)
        dupes = valid_df[is_duplicate].copy()
        
        if not dupes.empty:
            dupes_sorted = dupes.sort_values(by=["תעודת זהות", "תקופת העסקה"])
            st.warning(f"נמצאו {dupes['תעודת זהות'].nunique()} עובדים כפולים.")
            st.dataframe(dupes_sorted, use_container_width=True)
            
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                dupes_sorted.to_excel(writer, index=False)
            st.download_button("📥 הורד דוח כפילויות (אקסל)", output.getvalue(), "duplicates.xlsx")
        else:
            st.success("לא נמצאו כפילויות.")

    with st.expander("צפה במאגר המלא"):
        st.write(master_df)
else:
    st.info("המערכת ריקה. העלה קבצים דרך התפריט בצד.")
