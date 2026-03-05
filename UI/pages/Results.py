import streamlit as st
import pandas as pd

st.title("Run Results")

if "results" in st.session_state:
    df = pd.DataFrame(st.session_state["results"])
    st.dataframe(df)
else:
    st.info("No experiments run yet.")