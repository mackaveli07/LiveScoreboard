from db_utils import connect_to_db
import streamlit as st
import pandas as pd

try:
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("SELECT TOP 10 * FROM your_table")
    data = cursor.fetchall()
    columns = [col[0] for col in cursor.description]
    df = pd.DataFrame(data, columns=columns)
    st.dataframe(df)
except Exception as e:
    st.error(f"Error: {e}")

