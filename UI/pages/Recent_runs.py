import pandas as pd
import streamlit as st

from ollama_exec import get_recent_runs

st.set_page_config(page_title="Recent Experiments", layout="wide")

c1, c2 = st.columns([9, 1])
with c1:
    st.title("Recent Experiments")
    st.caption("Recent benchmark runs from the database")
with c2:
    if st.button("New Experiment"):
        st.switch_page("pages/Experiment_setup.py")

st.divider()

try:
    recent_runs = get_recent_runs(limit=200)
except Exception as exc:
    st.error(f"Failed to load recent runs: {exc}")
    st.stop()

if not recent_runs:
    st.info("No experiment runs found yet.")
    st.stop()

df = pd.DataFrame(recent_runs)

df["run_datetime"] = df["run_date"].astype(str) + " " + df["run_time"].astype(str)

search = st.text_input("Search by task, strategy, or model", value="")
if search:
    mask = (
        df["task_name"].str.contains(search, case=False)
        | df["strategy_name"].str.contains(search, case=False)
        | df["model_name"].str.contains(search, case=False)
    )
    df = df[mask]

if df.empty:
    st.info("No runs match your search.")
    st.stop()

show_cols = [
    "run_id",
    "run_datetime",
    "task_name",
    "strategy_name",
    "model_name",
    "latency_ms",
    "total_tokens",
    "accuracy_percent",
    "quality_score",
]
st.dataframe(df[show_cols], use_container_width=True, height=420)

selected_run_id = st.selectbox("Select run ID to inspect", df["run_id"].tolist())

if st.button("View Selected Run"):
    selected = df[df["run_id"] == selected_run_id].iloc[0].to_dict()
    st.session_state["last_experiment"] = {
        "experiment_name": f"run-{selected_run_id}",
        "result": {
            "run_records": [selected],
            "summary": {
                "task_name": selected.get("task_name", "-"),
                "model_name": selected.get("model_name", "-"),
                "strategy_name": selected.get("strategy_name", "-"),
                "total_runs": 1,
                "mean_latency_ms": selected.get("latency_ms", 0.0),
                "mean_accuracy_percent": selected.get("accuracy_percent", 0.0),
            },
        },
    }
    st.switch_page("pages/Comparison.py")
