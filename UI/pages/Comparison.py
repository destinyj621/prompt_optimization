import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(
    page_title="Results & Comparison", layout="wide")
if "screen" not in st.session_state:
    st.session_state.screen= "results-comparison"
experiment= st.session_state.get("last_experiment")
if not experiment:
    st.warning("No experiment selected.")
    st.stop()
df = pd.DataFrame(experiment["results"])
#helper functions
def highlight_best(c):
    if c.name == "variance":
        best= c.min()
    else:
        best= c.max()
    return ["background-color: #E6FFFA; font-weight: 600" if v == best else "" for v in c]
def render_summary_cards():
    c1, c2, c3, c4= st.columns(4)
    with c1:
        st.metric(
            "Best Quality",
            f"{df['quality'].max():.1f}%",
            df.loc[df["quality"].idxmax(), "variant"],)

    with c2:
        st.metric(
            "Lowest Cost",
            f"${df['cost'].min():.4f}",
            df.loc[df["cost"].idxmin(), "variant"], )
    with c3:
        st.metric(
            "Fastest",
            f"{df['latency'].min()} ms",
            df.loc[df["latency"].idxmin(), "variant"],
        )
    with c4:
        st.metric(
            "Best Efficiency",
            f"{df['efficiency'].max():.1f}",
            df.loc[df["efficiency"].idxmax(), "variant"],
        )
def render_table():
    styled_df=(
        df.style
        .apply(highlight_best, subset=["cost"], axis=0)
        .apply(highlight_best, subset=["latency"], axis=0)
        .apply(highlight_best, subset=["quality"], axis=0)
        .apply(highlight_best, subset=["variance"], axis=0)
        .apply(highlight_best, subset=["efficiency"], axis=0)
    )
    st.dataframe(styled_df, use_container_width=True)
def render_charts():
    c1, c2= st.columns(2)
    with c1:
        st.subheader("Cost per Request")
        st.bar_chart(df.set_index("variant")["cost"])
    with c2:
        st.subheader("Average Latency")
        st.bar_chart(df.set_index("variant")["latency"])
    c3, c4= st.columns(2)
    with c3:
        st.subheader("Quality Score")
        st.bar_chart(df.set_index("variant")["quality"])
    with c4:
        st.subheader("Composite Efficiency Score")
        st.bar_chart(df.set_index("variant")["efficiency"])
#header
st.title("Results & Comparison")
st.caption(
    f"customer-support-optimization-v1 • Completed on {datetime.now().strftime('%b %d, %Y')}"
)

c1, c2 = st.columns([3, 1])
with c1:
    t1, t2 = st.tabs(["Table","Charts"])
    st.divider()
    with t1:
        st.markdown("### Summary")
        render_summary_cards()
        st.markdown("### Detailed Results")
        render_table()
    with t2:
        st.markdown("### Summary")
        render_summary_cards()
        t2.markdown("### Visual Comparison")
        render_charts()
with c2:
    st.download_button(
        "Export Report",
        data=df.to_csv(index=False),
        file_name="benchmark_results.csv",
        mime="text/csv",
    )
#efficiency
best_idx= df["efficiency"].idxmax()
best_variant= df.loc[best_idx, "variant"]
best_score= df.loc[best_idx, "efficiency"]
#footer
c1, c2= st.columns([8.3,1])
with c1:
    if st.button("← Back to Experiment Setup"):
        st.switch_page("app.py")
        st.rerun()
with c2:
    if st.button("View Recent Runs →"):
        st.switch_page("pages/Recent_runs.py")
        st.rerun()