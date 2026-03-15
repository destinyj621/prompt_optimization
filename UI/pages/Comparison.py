import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Results & Comparison", layout="wide")


def _pick_metric(result: dict, *keys: str, default: float = 0.0) -> float:
    for key in keys:
        value = result.get(key)
        if value is not None:
            return float(value)
    return float(default)


experiment = st.session_state.get("last_experiment")
if not experiment or not experiment.get("results"):
    st.warning("No experiment selected.")
    st.stop()

raw_results = experiment["results"]

results = []
for result in raw_results:
    results.append(
        {
            "variant": result.get("variant") or result.get("strategy_name") or "Unknown Variant",
            "latency": _pick_metric(result, "latency", "mean_latency_ms"),
            "accuracy": _pick_metric(result, "accuracy", "accuracy_percent", "mean_accuracy_percent"),
            "quality": _pick_metric(result, "quality", "quality_score", "mean_quality_score"),
            "tokens": _pick_metric(result, "tokens", "total_tokens", "mean_total_tokens"),
            "efficiency": _pick_metric(
                result,
                "efficiency",
                "throughput_tokens_per_sec",
                "mean_throughput_tokens_per_sec",
            ),
            "variance": _pick_metric(result, "variance"),
            "cost": _pick_metric(result, "cost", "energy_cost", "total_energy_cost"),
            "output_text": result.get("output_text", ""),
            "run_records": result.get("run_records", []),
        }
    )

df = pd.DataFrame(results)
table_df = df.drop(columns=["output_text", "run_records"], errors="ignore")


def highlight_best(column: pd.Series) -> list[str]:
    if column.name == "variance":
        best = column.min()
    else:
        best = column.max()
    return ["background-color: #E6FFFA; font-weight: 600" if value == best else "" for value in column]


def render_summary_cards() -> None:
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric(
            "Best Accuracy",
            f"{df['accuracy'].max():.1f}%",
            df.loc[df["accuracy"].idxmax(), "variant"],
        )
    with c2:
        st.metric(
            "Best Quality",
            f"{df['quality'].max():.1f}%",
            df.loc[df["quality"].idxmax(), "variant"],
        )
    with c3:
        st.metric(
            "Lowest Cost",
            f"${df['cost'].min():.4f}",
            df.loc[df["cost"].idxmin(), "variant"],
        )
    with c4:
        st.metric(
            "Fastest",
            f"{df['latency'].min():.0f} ms",
            df.loc[df["latency"].idxmin(), "variant"],
        )
    with c5:
        st.metric(
            "Best Efficiency",
            f"{df['efficiency'].max():.1f}",
            df.loc[df["efficiency"].idxmax(), "variant"],
        )


def render_table() -> None:
    styled_df = (
        table_df.style
        .apply(highlight_best, subset=["accuracy"], axis=0)
        .apply(highlight_best, subset=["quality"], axis=0)
        .apply(highlight_best, subset=["cost"], axis=0)
        .apply(highlight_best, subset=["latency"], axis=0)
        .apply(highlight_best, subset=["variance"], axis=0)
        .apply(highlight_best, subset=["efficiency"], axis=0)
    )
    st.dataframe(styled_df, use_container_width=True)


def render_charts() -> None:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Accuracy")
        st.bar_chart(df.set_index("variant")["accuracy"])
    with c2:
        st.subheader("Average Latency")
        st.bar_chart(df.set_index("variant")["latency"])

    c3, c4 = st.columns(2)
    with c3:
        st.subheader("Quality Score")
        st.bar_chart(df.set_index("variant")["quality"])
    with c4:
        st.subheader("Cost per Request")
        st.bar_chart(df.set_index("variant")["cost"])


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
                if output:
                    with st.expander(f"Output - {row['variant']}"):
                        st.markdown(output)

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
        data=df.drop(columns=["output_text", "run_records"], errors="ignore").to_csv(index=False),
        file_name="benchmark_results.csv",
        mime="text/csv",
    )

c1, c2 = st.columns([8.3, 1])
with c1:
    if st.button("Back to Experiment Setup"):
        st.switch_page("pages/Experiment_setup.py")
with c2:
    if st.button("View Recent Runs"):
        st.switch_page("pages/Recent_runs.py")
