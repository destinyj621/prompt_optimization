import streamlit as st
import pandas as pd

st.set_page_config(page_title="Recent Experiments", layout="wide")

if "screen" not in st.session_state:
    st.session_state.screen="recent-runs"
#will be changed to load from database this is just example code
experiments =[{
        "id": 1,
        "name": "customer-support-optimization-v1",
        "task": "Text Classification",
        "variants": 3,
        "avgCost": 0.0051,
        "avgLatency": 245,
        "date": "2026-02-09",
        "status": "Completed", },
    {
        "id": 2,
        "name": "doc-summarization-test",
        "task": "Summarization",
        "variants": 2,
        "avgCost": 0.0063,
        "avgLatency": 412,
        "date": "2026-02-08",
        "status": "Completed",},
    {
        "id": 3,
        "name": "sentiment-analysis-v2",
        "task": "Sentiment Analysis",
        "variants": 4,
        "avgCost": 0.0042,
        "avgLatency": 198,
        "date": "2026-02-07",
        "status": "Completed",},
    {
        "id": 4,
        "name": "entity-extraction-baseline",
        "task": "Entity Extraction",
        "variants": 3,
        "avgCost": 0.0055,
        "avgLatency": 267,
        "date": "2026-02-06",
        "status": "In Progress",},
    {
        "id": 5,
        "name": "qa-system-optimization",
        "task": "Question Answering",
        "variants": 5,
        "avgCost": 0.0078,
        "avgLatency": 523,
        "date": "2026-02-05",
        "status": "Completed",},]

df = pd.DataFrame(experiments)
#header
c1, c2= st.columns([9,1])
with c1:
    st.title("Recent Experiments")
    st.caption("View and compare past prompt optimization experiments")
with c2:
    if st.button("New Experiment"):
        st.switch_page("app.py")
st.divider()
#search and filter buttons
c1, c2= st.columns([3,1])
with c1:
    search= st.text_input("🔍︎ Search Experiments...",value="")
with c2:
    filter=st.selectbox("Filter by Status", ["All","Completed","In Progress"], index=0, label_visibility="collapsed")
df_filtered= df.copy()
if search: 
    df_filtered= df_filtered[df_filtered["name"].str.contains(search, case=False)]
if filter !="All":
    df_filtered= df_filtered[df_filtered["status"]==filter]
#table of experiments
st.markdown("### Experiment History")
if not df_filtered.empty:
    display_df= df_filtered.rename(
        columns={
            "name": "Experiment Name",
            "task": "Task Type",
            "variants": "Variants",
            "avgCost": "Avg Cost",
            "avgLatency": "Avg Latency",
            "date": "Date",
            "status": "Status",
        }
    )
    def highlight_status(val):
        if val== "Completed":
            return "background-color: #D1FAE5; font-weight: 600"
        elif val== "In Progress":
            return "background-color: #FEF3C7; font-weight: 600"
        return ""

    st.dataframe(
        display_df.style.applymap(highlight_status, subset=["Status"]),
        use_container_width=True,
        height=400,
    )
    selected_id = st.selectbox(
        "Select experiment to view results",
        df_filtered["id"],
        format_func=lambda x: df_filtered[df_filtered["id"] == x]["name"].values[0],
    )

    if st.button("View Results →"):
        st.session_state.selected_experiment_id = selected_id
        st.switch_page("pages/comparison.py")
        st.rerun()
else:
    st.info("No experiments match your search/filter criteria.")
st.divider()
#summary cards
st.markdown("### Summary Stats")
c1,c2,c3,c4= st.columns(4)
with c1:
    st.metric("Total Experiments", len(df_filtered))
with c2:
    st.metric("Completed", len(df_filtered[df_filtered["status"]=="Completed"]))
with c3:
    st.metric("Avgg Cost per run",f"${df_filtered['avgCost'].mean():.4f}"if not df_filtered.empty else "$0.0000")
with c4:
    st.metric("Avg Latency", f"{int(df_filtered['avgLatency'].mean())} ms"if not df_filtered.empty else "0 ms")