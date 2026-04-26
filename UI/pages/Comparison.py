import streamlit as st
import pandas as pd
from datetime import datetime
import re

def _strip_ansi_codes(text: str) -> str:
    """Remove ANSI escape codes from text."""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

TASK_METRICS = {
    1: {
        "show_accuracy": True,
        "show_quality": False,
    },
    2: {
        "show_accuracy": False,
        "show_quality": True,
    },
    3:{
        "show_accuracy": False,
        "show_quality": True,
    },
}

st.set_page_config(page_title="Results & Comparison", layout="wide")
def load_css():
    with open(".streamlit/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
load_css()

def _pick_metric(result: dict, *keys: str, default: float | None = None):
    for key in keys:
        if key in result and  result[key] is not None:
            try:
                return float(result[key])
            except Exception:
                pass
    return default

with st.expander("Metric Definitions & Calculation Methodology"):
    st.markdown("""
### Latency
**Formula:**  
Latency (ms) = End Time - Start Time  

---
### Total Tokens
**Formula:**  
Prompt Tokens + Completion Tokens  

---
### Throughput
**Tokens/sec:**  
Total Tokens ÷ Latency (seconds)  

**Requests/sec:**  
1 ÷ Latency (seconds)

---
### Energy Consumption (Energy(KWh))
**Formula:**  
(GPU Power x Latency) ÷ (1000 x 3600)

---
### Energy Cost
**Formula:**  
Energy (kWh) x Cost per kWh  

---
### Hardware Cost
**Formula:**  
Latency (seconds) ÷ 3600 x Hourly Hardware Cost  

---
### Carbon Emissions
**Formula:**  
Energy (kWh) x kg CO₂ per kWh  

---
# TASK-SPECIFIC EVALUATION METRICS

## 1. Classification Accuracy
**Formula:**  
Accuracy = 100 if predicted label == expected label else 0  

---
## 2. Summarization Quality (LLM-as-a-Judge)

A judge model evaluates the summary against the original input and reference summary.

### Inputs:
- Document (input text)
- Reference summary (if available)
- Model-generated summary

### Evaluation criteria:
- factual correctness
- coverage of key points
- conciseness
- clarity

### Output:
A single score:


Quality in [0, 100]

### Final Meaning:
- 90-100 → excellent summary (fully faithful + complete)
- 70-89 → good summary (minor omissions)
- 50-69 → partial coverage or minor hallucinations
- <50 → poor or incorrect summary

---
## 3. Question Answering Quality (LLM-as-a-Judge)

A judge model evaluates the answer using:

- correctness
- completeness
- grounding in context
- clarity

### Inputs:
- Context / passage
- Expected answer (if available)
- Model answer

### Output:

Quality in [0, 100]

### Interpretation:
- 90-100 → fully correct and grounded
- 70-89 → mostly correct
- 50-69 → partially correct
- <50 → incorrect or hallucinated
""")
experiment = st.session_state.get("last_experiment")
if not experiment or not experiment.get("results"):
    st.warning("No experiment selected.")
    st.stop()

raw_results = experiment["results"]

task_id = experiment.get("task_id") or (experiment.get("task", {}).get("task_id") if experiment.get("task") else None)
if isinstance(task_id, int):
    task_cfg = TASK_METRICS.get(task_id,{})
    SHOW_ACCURACY = task_cfg.get("show_accuracy", False)
    SHOW_QUALITY = task_cfg.get("show_quality", False)
else:
    task_cfg = {}
    SHOW_ACCURACY = False
    SHOW_QUALITY = False
results = []
for result in raw_results:
    results.append(
        {
            "variant": result.get("variant") or result.get("strategy_name") or "Unknown Variant",
            "latency": _pick_metric(result, "latency", "mean_latency_ms"),
            "accuracy": _pick_metric(result, "accuracy", "accuracy_percent", "mean_accuracy_percent"),
            "quality": _pick_metric(result, "quality", "quality_score", "mean_quality_score"),
            "tokens": _pick_metric(result, "tokens", "total_tokens", "mean_total_tokens"),
            "throughput": _pick_metric(result, "throughput", "throughput_tokens_per_sec","mean_throughput_tokens_per_sec",),
            "energy_cost": _pick_metric(result, "cost", "energy_cost", "total_energy_cost"),
            "output_text": result.get("output_text", ""),
            "expected_label": result.get("expected_label", ""),
            "run_records": result.get("run_records", []),
        }
    )

if not isinstance(task_id, int):
    if any(item.get("accuracy") is not None for item in results):
        SHOW_ACCURACY = True
    if any(item.get("quality") is not None for item in results):
        SHOW_QUALITY = True


df = pd.DataFrame(results)
drop_cols = ["output_text", "expected_label", "run_records"]
if not SHOW_ACCURACY:
    drop_cols.append("accuracy")
if not SHOW_QUALITY:
    drop_cols.append("quality")
table_df = df.drop(columns=drop_cols, errors="ignore")


def highlight_best(column: pd.Series) -> list[str]:
    if column.name == "throughput" or column.name=="accuracy" or column.name=="quality":
        best = column.max()
    else:
        best = column.min()
    return ["background-color: #5CE488; font-weight: 600" if value == best else "" for value in column]


def render_summary_cards() -> None:
    def _best_variant(column: pd.Series, minimize: bool = False) -> str:
        if column.empty or column.dropna().empty:
            return "N/A"
        idx = column.idxmin() if minimize else column.idxmax()
        if pd.isna(idx) or idx not in df.index:
            return "N/A"
        return str(df.loc[idx, "variant"])

    c1, c2, c3, c4, c5 = st.columns(5)
    if SHOW_ACCURACY:
        with c1:
            st.metric(
                "Best Accuracy",
                f"{df['accuracy'].max():.1f}%" if df["accuracy"].dropna().any() else "N/A",
                _best_variant(df["accuracy"]),
            )
    if SHOW_QUALITY:
        with c1:
            st.metric(
                "Best Quality",
                f"{df['quality'].max():.1f}%" if df["quality"].dropna().any() else "N/A",
                _best_variant(df["quality"]),
            )
    with c2:
        st.metric(
            "Lowest Energy ",
            f"{df['energy_cost'].min():.4f} kWh" if df["energy_cost"].dropna().any() else "N/A",
            _best_variant(df["energy_cost"], minimize=True),
        )
    with c3:
        st.metric(
            "Fastest",
            f"{df['latency'].min():.0f} ms" if df["latency"].dropna().any() else "N/A",
            _best_variant(df["latency"], minimize=True),
        )
    with c4:
        st.metric(
            "Best Throughput",
            f"{df['throughput'].max():.1f}" if df["throughput"].dropna().any() else "N/A",
            _best_variant(df["throughput"]),
        )
    with c5:
        st.metric(
            "Lowest Tokens",
            f"{df['tokens'].min():.0f}" if df["tokens"].dropna().any() else "N/A",
            _best_variant(df["tokens"], minimize=True),
        )


def render_table() -> None:
    styled_df = table_df.style
    if SHOW_ACCURACY:
        styled_df = styled_df.apply(highlight_best, subset=["accuracy"],axis=0)
    if SHOW_QUALITY:
        styled_df = styled_df.apply(highlight_best, subset=["quality"],axis=0)
    styled_df = (
        styled_df
        .apply(highlight_best, subset=["energy_cost"], axis=0)
        .apply(highlight_best, subset=["latency"], axis=0)
        .apply(highlight_best, subset=["throughput"], axis=0)
        .apply(highlight_best, subset=["tokens"], axis=0)
    )
    st.dataframe(styled_df, use_container_width=True)


def render_charts() -> None:
    c1, c2 = st.columns(2)
    with c1:
        if SHOW_ACCURACY:
            st.subheader("Accuracy")
            st.bar_chart(df.set_index("variant")["accuracy"])
        if SHOW_QUALITY:
            st.subheader("Quality")
            st.bar_chart(df.set_index("variant")["quality"])
    with c2:
        st.subheader("Average Latency")
        st.bar_chart(df.set_index("variant")["latency"])

    c3, c4 = st.columns(2)
    with c3:
        st.subheader("Throughput per second")
        st.bar_chart(df.set_index("variant")["throughput"])
    with c4:
        st.subheader("Energy Cost")
        st.bar_chart(df.set_index("variant")["energy_cost"])

# def render_charts():
   

#     if "accuracy" in table_df.columns:
#         st.bar_chart(df.set_index("variant")["accuracy"])

#     if "quality" in table_df.columns:
#         st.bar_chart(df.set_index("variant")["quality"])

#     if "latency" in table_df.columns:
#         st.bar_chart(df.set_index("variant")["latency"])

st.title("Results & Comparison")
st.caption(
    f"{experiment.get('experiment_name', 'Unnamed Experiment')} • Completed on {datetime.now().strftime('%b %d, %Y')}"
)

c1, c2 = st.columns([3, 1])
with c1:
    tab_chat, tab_table, tab_charts = st.tabs(["Chat", "Table", "Charts"])
    st.divider()

    with tab_chat:
        st.markdown("LLM Outputs")
        outputs = df["output_text"].fillna("").astype(str)

        if outputs.str.strip().eq("").all():
            st.info("No output text recorded for this run.")
        else:
            for _, row in df.iterrows():
                output = str(row.get("output_text", "")).strip()
                expected = str(row.get("expected_label", "")).strip()
                if not expected:
                    run_records = row.get("run_records", [])
                    if isinstance(run_records, list) and run_records:
                        expected = str(run_records[-1].get("expected_label", "")).strip()
                variant = row['variant']
                if output or expected:
                    with st.expander(f"Output - {variant}"):
                        if expected:
                            expected = _strip_ansi_codes(expected)
                            st.markdown(f"**Expected:** {expected}")
                        if output:
                            output = _strip_ansi_codes(output)
                            st.markdown(f"**Predicted:** {output}")

    with tab_table:
        st.markdown("### Summary")
        render_summary_cards()
        st.markdown("### Detailed Results")
        render_table()

    with tab_charts:
        st.markdown("### Summary")
        render_summary_cards()
        st.markdown("### Visual Comparison")
        render_charts()

with c2:
    st.download_button(
        "Export Report",
        data=df.drop(columns=["output_text", "expected_label", "run_records"], errors="ignore").to_csv(index=False),
        file_name="benchmark_results.csv",
        mime="text/csv",
    )

c1, c2 = st.columns([8.3, 1])
with c1:
    if st.button("Back to Experiment Setup"):
        st.switch_page("pages/Experiment_Setup.py")
with c2:
    if st.button("View Recent Runs"):
        st.switch_page("pages/Recent_Runs.py")
