import streamlit as st
import pandas as pd
import os
import io

# --- הגדרות דף ---
st.set_page_config(page_title="ניהול נתוני עובדים", layout="wide")
DATA_FILE = "master_data.xlsx"

if "approved_files_data" not in st.session_state:
    st.session_state["approved_files_data"] = {}

def clean_id_logic(val):
    if pd.isna(val) or val == "":
        return ""
    s = str(val).strip()
    if s.endswith(".0"):
        s = s[:-2]
    return s

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_excel(DATA_FILE)
            df.columns = df.columns.astype(str).str.strip()
            df = df.fillna("").astype(str)
            if "תעודת זהות" in df.columns:
                df["תעודת זהות"] = df["תעודת זהות"].apply(clean_id_logic)
            return df
        except:
            return pd.DataFrame()
    return pd.DataFrame()

def save_data(df):
    if "תעודת זהות" in df.columns:
        df["תעודת זהות"] = df["תעודת זהות"].apply(clean_id_logic)
    df.to_excel(DATA_FILE, index=False)

def process_file_structure(uploaded_file):
    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.astype(str).str.strip()
    return df

# --- ממשק המשתמש ---
st.title("📂 מערכת ניתוח נתוני עובדים - תיקון שגיאת עמודות")

master_df = load_data()

with st.sidebar:
    st.header("1. טעינת קבצים")
    uploaded_files = st.file_uploader("בחר קבצי אקסל (אפשר כמה)", type=["xlsx"], accept_multiple_files=True)
    
    if uploaded_files:
        for f in uploaded_files:
            if f.name in st.session_state["approved_files_data"]:
                col_a, col_b = st.columns([4, 1])
                col_a.success(f"✅ {f.name}")
                if col_b.button("✖️", key=f"del_{f.name}"):
                    del st.session_state["approved_files_data"][f.name]
                    st.rerun()
                continue
                
            temp_df = process_file_structure(f)
            cols = ["- ללא -"] + list(temp_df.columns)
            
            with st.expander(f"⚙️ הגדר עמודות עבור: {f.name}"):
                def find_idx(keywords, columns):
                    for i, col in enumerate(columns):
                        if any(k in col for k in keywords): return i
                    return 0

                id_idx = find_idx(["זהות", "ת.ז", "תז", "ID"], cols)
                name_idx = find_idx(["שם", "עובד"], cols)
                emp_idx = find_idx(["מעסיק", "חברה", "מקום"], cols)
                lawyer_idx = find_idx(["עו\"ד", "עורך דין", "מייצג"], cols)
                period_idx = find_idx(["תקופה", "שנה", "תאריך"], cols)

                id_col = st.selectbox(f"עמודת ת'ז ({f.name})", cols[1:], index=max(0, id_idx-1))
                name_col = st.selectbox(f"עמודת שם ({f.name})", cols[1:], index=max(0, name_idx-1))
                employer_col = st.selectbox(f"עמודת מעסיק ({f.name})", cols[1:], index=max(0, emp_idx-1))
                lawyer_col = st.selectbox(f"עמודת שם העו'ד ({f.name})", cols, index=lawyer_idx)
                time_col = st.selectbox(f"עמודת תקופה ({f.name})", cols[1:], index=max(0, period_idx-1))
                
                if st.button(f"אשר את {f.name}", key=f"btn_{f.name}"):
                    final_df = temp_df.copy()
                    final_df["תעודת זהות"] = final_df[id_col].apply(clean_id_logic)
                    final_df["שם"] = final_df[name_col].astype(str)
                    final_df["מקום העסקה"] = final_df[employer_col].astype(str)
                    final_df["תקופת העסקה"] = final_df[time_col].astype(str)
                    
                    if lawyer_col != "- ללא -":
                        final_df["שם העו\"ד"] = final_df[lawyer_col].astype(str)
                    else:
                        final_df["שם העו\"ד"] = ""
                        
                    final_df["מקור קובץ"] = f.name
                    
                    selected = ["תעודת זהות", "שם", "מקום העסקה", "תקופת העסקה", "שם העו\"ד", "מקור קובץ"]
                    st.session_state["approved_files_data"][f.name] = final_df[selected]
                    st.rerun()

        if st.session_state["approved_files_data"]:
            st.divider()
            if st.button("🚀 העלה את כל המאושרים למאגר"):
                new_batch = pd.concat(st.session_state["approved_files_data"].values(), ignore_index=True)
                updated_master = pd.concat([master_df, new_batch], ignore_index=True)
                save_data(updated_master)
                st.session_state["approved_files_data"] = {} 
                st.success("הנתונים נשמרו!")
                st.rerun()

    st.divider()
    if st.button("🗑️ איפוס מאגר מוחלט"):
        if os.path.exists(DATA_FILE): os.remove(DATA_FILE)
        st.session_state.clear()
        st.rerun()

# --- גוף האפליקציה ---
if not master_df.empty:
    st.subheader("🔍 חיפוש וניתוח")
    
    c1, c2 = st.columns(2)
    with c1: s_name = st.text_input("חפש לפי שם עובד")
    with c2: s_id = st.text_input("חפש לפי תעודת זהות")
    
    display_df = master_df.copy()
    if s_name: display_df = display_df[display_df["שם"].str.contains(s_name, na=False)]
    if s_id: display_df = display_df[display_df["תעודת זהות"].str.contains(s_id, na=False)]
    
    st.dataframe(display_df, use_container_width=True)

    st.divider()
    
    if st.button("🔍 אתר כפילויות (תצוגה מרוכזת)"):
        valid_df = master_df[master_df["תעודת זהות"].str.strip() != ""].copy()
        id_counts = valid_df["תעודת זהות"].value_counts()
        duplicate_ids = id_counts[id_counts > 1].index
        
        if not duplicate_ids.empty:
            dupes = valid_df[valid_df["תעודת זהות"].isin(duplicate_ids)].copy()
            
            # בניית מילון האגרגציה בצורה דינמית כדי למנוע KeyError
            agg_dict = {}
            if "שם" in dupes.columns: agg_dict["שם"] = "first"
            if "מקום העסקה" in dupes.columns: 
                agg_dict["מקום העסקה"] = lambda x: ", ".join(sorted(set(filter(None, x.astype(str)))))
            if "שם העו\"ד" in dupes.columns: 
                agg_dict["שם העו\"ד"] = lambda x: ", ".join(sorted(set(filter(None, x.astype(str)))))
            if "מקור קובץ" in dupes.columns: 
                agg_dict["מקור קובץ"] = lambda x: ", ".join(sorted(set(filter(None, x.astype(str)))))
            if "תקופת העסקה" in dupes.columns: 
                agg_dict["תקופת העסקה"] = lambda x: ", ".join(sorted(set(filter(None, x.astype(str)))))
            
            # ביצוע האיחוד רק עם העמודות הקיימות
            summary_dupes = dupes.groupby("תעודת זהות").agg(agg_dict).reset_index()
            
            st.warning(f"נמצאו {len(summary_dupes)} עובדים כפולים.")
            st.dataframe(summary_dupes, use_container_width=True)
            
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                summary_dupes.to_excel(writer, index=False)
            st.download_button("📥 הורד דוח כפילויות מרוכז", output.getvalue(), "summary_duplicates.xlsx")
        else:
            st.success("לא נמצאו כפילויות.")

    with st.expander("צפה במאגר המלא"):
        st.write(master_df)
else:
    st.info("המערכת ריקה. העלה קבצים מימין.")
