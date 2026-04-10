import pandas as pd
import streamlit as st

from ollama_exec import get_recent_runs

st.set_page_config(page_title="Recent Experiments", layout="wide")
def load_css():
    with open(".streamlit/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
load_css()
c1, c2 = st.columns([9, 1])
with c1:
    st.title("Recent Experiments")
    st.caption("Recent benchmark runs from the database")
with c2:
    if st.button("New Experiment"):
        st.switch_page("pages/Experiment_Setup.py")

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
    run_results= run.get("results",[run])
    for variant in run_results:
        rows.append({
            "run_id": run.get("run_id", "-"),
            "experiment_run_id": run.get("experiment_run_id",""),
            "run_datetime": f"{run.get('run_date')} {run.get('run_time')}",
            "task_name": run.get("task_name", "-"),
            "task_id": run.get("task_id"),
            "strategy_name": variant.get("strategy_name", "-"),
            "model_name": variant.get("model_name", "-"),
            "latency_ms": variant.get("latency_ms", None),
            "total_tokens": variant.get("total_tokens", None),
            "accuracy_percent": variant.get("accuracy_percent", None),
            "quality_score": variant.get("quality_score", None),
            "throughput_tokens_per_sec": variant.get("throughput_tokens_per_sec", None),
            "energy_cost": variant.get("energy_cost", None),
            "output_text": variant.get("output_text",""),
            "expected_label": variant.get("expected_label", ""),
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
    "task_id",
    "strategy_name",
    "model_name",
    "latency_ms",
    "total_tokens",
    "accuracy_percent",
    "quality_score",
]
st.dataframe(df[show_cols], use_container_width=True, height=420)

unique_run_ids= df["run_id"].unique().tolist()
selected_run_id = st.selectbox("Select run ID to inspect", unique_run_ids)  

if st.button("View Selected Run"):
    selected = df[df["run_id"] == selected_run_id]
    comparison_results=[]
    for _, row in selected.iterrows():
        comparison_results.append({
            "variant": str(row["strategy_name"]) if pd.notna(row["strategy_name"]) else "Unknown Variant",
            "energy_cost": float(row["energy_cost"] or 0) if pd.notna(row["energy_cost"]) else 0.0,
            "latency": float(row["latency_ms"]) if pd.notna(row["latency_ms"]) else 0.0,
            "tokens": int(row["total_tokens"]) if pd.notna(row["total_tokens"]) else 0,
            "quality": float(row["quality_score"]) if pd.notna(row["quality_score"]) else 0.0,
            "accuracy": float(row["accuracy_percent"]) if pd.notna(row["accuracy_percent"]) else 0.0,
            "throughput": float(row["throughput_tokens_per_sec"]) if pd.notna(row["throughput_tokens_per_sec"]) else 0.0,
            "output_text": str(row["output_text"]) if pd.notna(row["output_text"]) else "",
            "expected_label": str(row["expected_label"]) if pd.notna(row["expected_label"]) else "",
        })
    st.session_state["last_experiment"] = {
        "experiment_name": f"Run #{selected_run_id} — {selected.iloc[0]['task_name']}",
        "task_name": selected.iloc[0]["task_name"],
        "task_id": int(selected.iloc[0]["task_id"]),
        "results": comparison_results,
    }

    st.switch_page("pages/Comparison.py")
