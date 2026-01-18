import pandas as pd
import streamlit as st

def process_data(uploaded_file):
    # טעינת הקובץ
    df = pd.read_excel(uploaded_file)
    
    # הגדרת העמודות שאנחנו רוצים לשמור
    required_columns = ['שם', 'תעודת זהות', 'תקופת העסקה', 'מקום העסקה']
    
    # בדיקה אילו מהעמודות קיימות בפועל בקובץ (כדי למנוע שגיאות)
    existing_columns = [col for col in required_columns if col in df.columns]
    
    # השארת העמודות הרלוונטיות בלבד
    df_filtered = df[existing_columns]
    
    return df_filtered

# בממשק ה-Streamlit:
uploaded_file = st.file_uploader("העלה קובץ אקסל של עובדים")
if uploaded_file:
    clean_df = process_data(uploaded_file)
    st.write("נתוני העובדים (עמודות נבחרות בלבד):")
    st.dataframe(clean_df)
