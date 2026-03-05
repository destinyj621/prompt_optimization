import streamlit as st

st.title("Experiment Setup")

task = st.selectbox(
    "Task Type",
    ["Summarization", "Classification", "Information Extraction"]
)

prompt = st.text_area("Enter Prompt", height=200)

strategies = st.multiselect(
    "Prompt Strategies",
    [
        "Zero-shot",
        "Few-shot",
        "Chain-of-thought",
        "Compressed Prompt",
        "Structured Output"
    ]
)

if st.button("Run Experiment"):
    if "results" not in st.session_state:
        st.session_state["results"] = []

    for strategy in strategies:
        st.session_state["results"].append({
            "task": task,
            "strategy": strategy,
            "latency_ms": 300,
            "tokens": 800,
            "cost": 0.01
        })

    st.success("Experiment completed.")