from datetime import datetime

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Results & Comparison", layout="wide")

experiment = st.session_state.get("last_experiment")
if not experiment:
    st.warning("No experiment selected.")
    st.stop()

result = experiment.get("result", {})
run_records = result.get("run_records", [])
summary = result.get("summary", {})

if not run_records:
    st.warning("No run records returned.")
    st.stop()

df = pd.DataFrame(run_records)

st.title("Results & Comparison")
st.caption(
    f"{experiment.get('experiment_name') or 'Experiment'} - Completed on {datetime.now().strftime('%b %d, %Y')}"
)

st.markdown("### Experiment Metadata")
meta_c1, meta_c2, meta_c3, meta_c4, meta_c5 = st.columns(5)
with meta_c1:
    st.metric("Task", summary.get("task_name", experiment.get("task", {}).get("task_name", "-")))
with meta_c2:
    st.metric("Strategy", summary.get("strategy_name", experiment.get("strategy", {}).get("strategy_name", "-")))
with meta_c3:
    st.metric("Model", summary.get("model_name", experiment.get("model", {}).get("model_name", "-")))
with meta_c4:
    st.metric("Number of Runs", int(summary.get("total_runs", len(run_records))))
with meta_c5:
    st.metric("Experiment Date", datetime.now().strftime("%Y-%m-%d"))

st.markdown("### Aggregate Metrics")
c1, c2, c3, c4, c5, c6 = st.columns(6)
with c1:
    st.metric("Mean Latency (ms)", f"{summary.get('mean_latency_ms', 0):.2f}")
with c2:
    st.metric("Mean Tokens", f"{summary.get('mean_total_tokens', 0):.2f}")
with c3:
    st.metric("Mean Accuracy (%)", f"{summary.get('mean_accuracy_percent', 0):.2f}")
with c4:
    st.metric("Mean Quality", f"{summary.get('mean_quality_score', 0):.2f}")
with c5:
    st.metric("Total Energy (kWh)", f"{summary.get('total_energy_kwh', 0):.8f}")
with c6:
    st.metric("Total Carbon (kg)", f"{summary.get('total_carbon_kg', 0):.8f}")

st.markdown("### Run-Level Metrics")
visible_columns = [
    "run_id",
    "latency_ms",
    "prompt_tokens",
    "completion_tokens",
    "total_tokens",
    "throughput_tokens_per_sec",
    "throughput_requests_per_sec",
    "accuracy_percent",
    "field_accuracy_percent",
    "exact_record_match",
    "schema_compliance_percent",
    "quality_score",
    "energy_kwh",
    "energy_cost",
    "hardware_cost",
    "carbon_kg",
]
columns = [column for column in visible_columns if column in df.columns]
st.dataframe(df[columns], use_container_width=True, height=360)

st.markdown("### Reproducibility Context")
for idx, record in enumerate(run_records, start=1):
    with st.expander(f"Run {idx} Context"):
        st.markdown("**Raw Input Text**")
        st.code(record.get("input_text", ""))
        st.markdown("**Final Prompt Sent to Model**")
        st.code(record.get("input_prompt", ""))
        st.markdown("**Model Output**")
        st.code(record.get("output_text", ""))

st.download_button(
    "Export Run Results",
    data=df.to_csv(index=False),
    file_name="benchmark_run_records.csv",
    mime="text/csv",
)

b1, b2 = st.columns([8.5, 1.5])
with b1:
    if st.button("Back to Experiment Setup"):
        st.switch_page("pages/Experiment_setup.py")
with b2:
    if st.button("Recent Runs"):
        st.switch_page("pages/Recent_runs.py")
