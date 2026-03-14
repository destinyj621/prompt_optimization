import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Results & Comparison", layout="wide")


experiment = st.session_state.get("last_experiment")
if not experiment or not experiment.get("results"):
    st.warning("No experiment selected.")
    st.stop()

raw_results = experiment["results"]


results = []
for r in raw_results:
    results.append({
        "variant": r.get("variant") or r.get("strategy_name") or "Unknown Variant",
        "latency": r.get("latency") or r.get("mean_latency_ms") or 0,
        "quality": r.get("quality") or r.get("mean_quality_score") or 0,
        "tokens": r.get("tokens") or r.get("mean_total_tokens") or 0,
        "efficiency": r.get("efficiency") or r.get("mean_throughput_tokens_per_sec") or 0,
        "variance": r.get("variance") or 0,
        "cost": r.get("cost") or r.get("total_energy_cost") or 0,
        "output_text": r.get("output_text", ""),
        "run_records": r.get("run_records", []),
    })

df = pd.DataFrame(results)
table_df = df.drop(columns=["output_text"], errors="ignore")
def highlight_best(c):
    if c.name == "variance":
        best = c.min()
    else:
        best = c.max()
    return ["background-color: #E6FFFA; font-weight: 600" if v == best else "" for v in c]

def render_summary_cards():
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric(
            "Best Quality",
            f"{df['quality'].max():.1f}%",
            df.loc[df['quality'].idxmax(), "variant"]
        )
    with c2:
        st.metric(
            "Lowest Cost",
            f"${df['cost'].min():.4f}",
            df.loc[df['cost'].idxmin(), "variant"]
        )
    with c3:
        st.metric(
            "Fastest",
            f"{df['latency'].min():.0f} ms",
            df.loc[df['latency'].idxmin(), "variant"]
        )
    with c4:
        st.metric(
            "Best Efficiency",
            f"{df['efficiency'].max():.1f}",
            df.loc[df['efficiency'].idxmax(), "variant"]
        )

def render_table():
    styled_df = (
        table_df.style
        .apply(highlight_best, subset=["cost"], axis=0)
        .apply(highlight_best, subset=["latency"], axis=0)
        .apply(highlight_best, subset=["quality"], axis=0)
        .apply(highlight_best, subset=["variance"], axis=0)
        .apply(highlight_best, subset=["efficiency"], axis=0)
    )
    st.dataframe(styled_df, use_container_width=True)

def render_charts():
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Cost per Request")
        st.bar_chart(df.set_index("variant")["cost"])
    with c2:
        st.subheader("Average Latency")
        st.bar_chart(df.set_index("variant")["latency"])
    c3, c4 = st.columns(2)
    with c3:
        st.subheader("Quality Score")
        st.bar_chart(df.set_index("variant")["quality"])
    with c4:
        st.subheader("Composite Efficiency Score")
        st.bar_chart(df.set_index("variant")["efficiency"])

st.title("Results & Comparison")
st.caption(
    f"{experiment.get('experiment_name', 'Unnamed Experiment')} • Completed on {datetime.now().strftime('%b %d, %Y')}"
)
c1, c2 = st.columns([3, 1])
with c1:
    t1, t2, t3 = st.tabs(["Chat","Table", "Charts", ])
    st.divider()
    with t1:
        st.markdown("LLM Outputs")

        outputs = df["output_text"].fillna("").astype(str)

        if outputs.str.strip().eq("").all():
            st.info("No output text recorded for this run.")
        else:
            for idx, row in df.iterrows():
                output = str(row.get("output_text", "")).strip()
                if output:
                    with st.expander(f"Output — {row['variant']}"):
                        st.markdown(output)
    with t2:
        st.markdown("### Summary")
        render_summary_cards()
        st.markdown("### Detailed Results")
        render_table()
    with t3:
        st.markdown("### Summary")
        render_summary_cards()
        t2.markdown("### Visual Comparison")
        render_charts()

with c2:
    st.download_button(
        "Export Report",
        data=df.drop(columns=["output_text"], errors="ignore").to_csv(index=False),
        file_name="benchmark_results.csv",
        mime="text/csv",
    )


c1, c2 = st.columns([8.3, 1])
with c1:
    if st.button("← Back to Experiment Setup"):
        st.switch_page("pages/Experiment_setup.py")
with c2:
    if st.button("View Recent Runs →"):
        st.switch_page("pages/Recent_runs.py")