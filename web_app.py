import streamlit as st
import pandas as pd
import os

# פונקציה ליישור האתר לימין
def set_rtl():
    st.markdown(
        """
        <style>
        /* יישור כללי של האתר לימין */
        .main .block-container {
            direction: rtl;
            text-align: right;
        }
        /* יישור תפריט הצד לימין */
        section[data-testid="stSidebar"] > div {
            direction: rtl;
            text-align: right;
        }
        /* יישור טבלאות נתונים */
        .stDataFrame {
            direction: rtl;
        }
        /* תיקון יישור לתיבות טקסט */
        input {
            direction: rtl;
        }
        </style>
        """,
        unsafe_allow_complete_html=True,
        unsafe_allow_html=True
    )

# הפעלת היישור לימין
set_rtl()

# הצגת לוגו (אם העלית קובץ בשם logo.png)
if os.path.exists("logo.png"):
    st.image("logo.png", width=150)

# --- כאן ממשיך שאר הקוד שלך (סיסמה, חיפוש וכו') ---
st.title("🔍 מערכת ניתוח נתונים בעברית")

# לדוגמה, תיבת החיפוש תהיה עכשיו מיושרת לימין
search_id = st.text_input("הכנס תעודת זהות לחיפוש:")
