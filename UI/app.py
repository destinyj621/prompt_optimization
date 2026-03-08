import streamlit as st

st.set_page_config(page_title="Prompt Optimization Workbench", layout="wide")

st.title("Prompt Optimization Workbench")
st.caption("Run and compare prompt strategy benchmarks on local models.")

st.markdown("### Navigation")

c1, c2 = st.columns(2)
with c1:
    if st.button("Open Experiment Setup", use_container_width=True, type="primary"):
        st.switch_page("pages/Experiment_setup.py")
with c2:
    if st.button("Open Recent Runs", use_container_width=True):
        st.switch_page("pages/Recent_runs.py")

st.divider()
st.write(
    "Use Experiment Setup to select task, strategy, model, input, and number of runs; "
    "then run and inspect detailed metrics in the results page."
)
