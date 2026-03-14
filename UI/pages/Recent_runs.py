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

rows = []
for run in recent_runs:
    summary = run.get("summary", {})
    rows.append({
        "run_id": run.get("run_id", "-"),
        "run_datetime": f"{run.get('run_date')} {run.get('run_time')}",
        "task_name": run.get("task_name", "-"),
        "strategy_name": run.get("strategy_name", "-"),
        "model_name": run.get("model_name", "-"),
        "latency_ms": run.get("latency_ms", None),
        "total_tokens": run.get("total_tokens", None),
        "accuracy_percent": run.get("accuracy_percent", None),
        "quality_score": run.get("quality_score", None),
        "output_text": run["output_text"],
    })

df = pd.DataFrame(rows)


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
    selected = df[df["run_id"] == selected_run_id].iloc[0]
    
    comparison_row = {
        "variant": selected["strategy_name"] or "Unknown Variant",
        "cost": 0.0,  
        "latency": float(selected["latency_ms"] or 0),
        "tokens": int(selected["total_tokens"] or 0),
        "quality": float(selected["quality_score"] or 0),
        "variance": 0.0,      
        "efficiency": float(selected["quality_score"] or 0),  
        "output_text": selected.get("output_text",""),
    }

    st.session_state["last_experiment"] = {
        "experiment_name": f"run-{selected_run_id}",
        "results": [comparison_row],
    }

    st.switch_page("pages/Comparison.py")