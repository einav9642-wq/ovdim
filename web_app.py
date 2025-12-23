import streamlit as st
import pandas as pd

st.set_page_config(page_title="מערכת ניתוח אקסל", layout="wide")

st.title("🔍 מערכת לניתוח נתוני עובדים")
st.write("העלה קבצי אקסל כדי לחפש עובד או למצוא כפילויות")

# רכיב להעלאת קבצים מרובים
uploaded_files = st.file_uploader("בחר קבצי אקסל", type=["xlsx", "xls"], accept_multiple_files=True)

if uploaded_files:
    all_data = []
    for file in uploaded_files:
        df = pd.read_excel(file)
        df.columns = df.columns.astype(str).str.strip()
        df['מקור'] = file.name
        all_data.append(df)
    
    full_df = pd.concat(all_data, ignore_index=True)
    
    # זיהוי עמודת ת.ז
    possible_id_columns = ['ת.ז', 'ת.ז.', 'תעודת זהות', 'ID']
    id_col = next((col for col in possible_id_columns if col in full_df.columns), None)

    if id_col:
        full_df[id_col] = full_df[id_col].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()

        # תפריט צד לאפשרויות
        option = st.sidebar.selectbox("מה תרצה לעשות?", ["חיפוש פרטני", "איתור כפילויות"])

        if option == "חיפוש פרטני":
            search_id = st.text_input("הכנס תעודת זהות לחיפוש:")
            if search_id:
                results = full_df[full_df[id_col] == search_id]
                if not results.empty:
                    st.success(f"נמצאו {len(results)} רשומות")
                    st.write(results)
                else:
                    st.warning("לא נמצאו נתונים")

        elif option == "איתור כפילויות":
            duplicates = full_df[full_df.duplicated(subset=[id_col], keep=False)]
            if not duplicates.empty:
                st.error(f"נמצאו {duplicates[id_col].nunique()} עובדים כפולים")
                st.write(duplicates.sort_values(by=id_col))
                
                # כפתור הורדה
                csv = duplicates.to_csv(index=False).encode('utf-8-sig')
                st.download_button("הורד רשימת כפילויות", data=csv, file_name="duplicates.csv")
            else:
                st.success("אין כפילויות במאגר")