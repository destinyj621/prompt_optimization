import streamlit as st
import pandas as pd
from datetime import datetime

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


experiment = st.session_state.get("last_experiment")
if not experiment or not experiment.get("results"):
    st.warning("No experiment selected.")
    st.stop()

raw_results = experiment["results"]

task_id = experiment.get("task_id")
assert isinstance(task_id, int), f"Invalid task_id: {task_id}"
task_cfg = TASK_METRICS.get(task_id,{})
SHOW_ACCURACY = task_cfg.get("show_accuracy",False)
SHOW_QUALITY = task_cfg.get("show_quality", False)
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

df = pd.DataFrame(results)
if not SHOW_ACCURACY:
    table_df = df.drop(columns=["output_text", "expected_label", "run_records", "accuracy"], errors="ignore")
if not SHOW_QUALITY:
        table_df = df.drop(columns=["output_text", "expected_label", "run_records", "quality"], errors="ignore")


def highlight_best(column: pd.Series) -> list[str]:
    if column.name == "throughput" or column.name=="accuracy" or column.name=="quality":
        best = column.max()
    else:
        best = column.min()
    return ["background-color: #5CE488; font-weight: 600" if value == best else "" for value in column]


def render_summary_cards() -> None:
    c1, c2, c3, c4, c5 = st.columns(5)
    if SHOW_ACCURACY:
        with c1:
            st.metric(
                "Best Accuracy",
                f"{df['accuracy'].max():.1f}%",
                df.loc[df["accuracy"].idxmax(), "variant"],
            )
    if SHOW_QUALITY:
        with c1:
            st.metric(
                "Best Quality",
                f"{df['quality'].max():.1f}%",
                df.loc[df["quality"].idxmax(), "variant"],
            )
    with c2:
        st.metric(
            "Lowest Energy ",
            f"{df['energy_cost'].min():.4f} kWh",
            df.loc[df["energy_cost"].idxmin(), "variant"],
        )
    with c3:
        st.metric(
            "Fastest",
            f"{df['latency'].min():.0f} ms",
            df.loc[df["latency"].idxmin(), "variant"],
        )
    with c4:
        st.metric(
            "Best Throughput",
            f"{df['throughput'].max():.1f}",
            df.loc[df["throughput"].idxmax(), "variant"],
        )
    with c5:
        st.metric(
            "Lowest Tokens",
            f"{df['tokens'].min():.0f}",
            df.loc[df["tokens"].idxmin(), "variant"],
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
                            st.markdown(f"**Expected:** {expected}")
                        if output:
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
