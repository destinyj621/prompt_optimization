import streamlit as st
import uuid
from ollama_exec import run_experiment

st.set_page_config(page_title="Prompt Optimization Workbench", layout="wide")

#Initialization
if "variants" not in st.session_state:
    st.session_state.variants = [{
        "id":str(uuid.uuid4()),
        "strategy_type":"Zero-Shot",
        "description": "Baseline strategy",
        "system_prompt": "",
        "instruction_prompt":"",
        "context":"",
    }]
seen_ids = set()
for v in st.session_state.variants:
    if not isinstance(v["id"], str) or v["id"] in seen_ids:
        v["id"] = str(uuid.uuid4())
    seen_ids.add(v["id"])
#Header
st.title("Prompt Optimization Workbench")
st.caption("Evaluate and compare prompt strategies for generative AI workloads")

c1, c2 = st.columns([6,1])
with c2:
    if st.button("Recent Runs"):
        st.switch_page("pages/Recent_runs.py")
st.divider()
#Experiments 
experiment_name= st.text_input("Experiment Name",placeholder="e.g., customer-support-optimization-v1")
#Task Definition
st.subheader("Task Definition")
c1, c2 = st.columns(2)
with c1:
    st.markdown('<div class="equal-box outlined-widget">', unsafe_allow_html=True)
    task_type = st.selectbox(
        "Task Type",
        [
            "Text Classification",
            "Summarization",
            "Entity Extraction",
            "Question Answering",
            "Sentiment Analysis"
        ],
    )
    st.markdown("</div>", unsafe_allow_html=True)
with c2:
    st.markdown('<div class="equal-box outlined-widget">', unsafe_allow_html=True)
    dataset_file= st.file_uploader("Evaluation Dataset (CSV, JSON, PDF)", 
                                   type=["cvs","json","jsonl","pdf"])
    st.markdown("</div>", unsafe_allow_html=True)
st.divider()
#Prompt Variants
st.subheader("Prompt Strategies")
if st.button("+ Add Prompt Variant"):
    st.session_state.variants.append({
        "id":str(uuid.uuid4()),
        "strategy_type":"Few-Shot",
        "description": "",
        "system_prompt": "",
        "instruction_prompt":"",
        "context":"",
    })
to_remove = None

for i, variant in enumerate(st.session_state.variants):
    with st.container(border=True):
        c1, c2 = st.columns([5,1])
        with c1:
            st.markdown(f"### Variant {i+1}")
        with c2:
            if len(st.session_state.variants)>1:
                if st.button("Remove",key=f"remove_{variant['id']}"):
                    to_remove= i
    c1, c2= st.columns(2)
    with c1:
        variant["strategy_type"]= st.selectbox(
            "Strategy Type",
            ["Zero-Shot","Few-Shot","Compressed","Chain-of-Thought"],
            index=["Zero-Shot","Few-Shot","Compressed","Chain-of-Thought"].index(variant["strategy_type"]),
            key=f"strategy{variant['id']}" )
    with c2: variant["description"]= st.text_input("Description", value=variant["description"],
                                                   placeholder="e.g., Baseline with direct instructions",
                                                   key=f"description_{variant['id']}",)
    variant["system_prompt"]=st.text_area(
        "System Prompt", value=variant["system_prompt"], placeholder= "Define the AI's role and behaviour...",
        height=80, key=f"system_{variant['id']}",)
    variant["instruction_prompt"]=st.text_area(
        "Instruction Prompt *", value=variant["instruction_prompt"], placeholder= "Provide clear task instructions...",
        height=120, key=f"Instruction_{variant['id']}",)
    variant["context"]=st.text_area(
        "Context/ Examples (Optional)", value=variant["context"], placeholder= "Add examples or additional context...",
        height=80, key=f"context_{variant['id']}",)
    estimated_tokens= max(50, len(variant["instruction_prompt"])//3)
    estimated_cost = estimated_tokens* 0.00002
    st.caption(f"Estimated tokens: ~{estimated_tokens} | Estimated cost: ~${estimated_cost:.4f}")
if to_remove is not None:
    st.session_state.variants.pop(to_remove)
    st.rerun()
#Execution config
st.divider()
st.subheader("Execution Configuration")
execution_mode= st.radio("Execution Mode", ["Mock Estimation", "Limited Cloud Execution", "Local Execution"], index=0,)
runs_per_prompt= st.number_input("Runs per Prompt",min_value=1, max_value=50, value=5)
#footer
st.divider()
c1, c2 = st.columns([9,1])
with c1: 
    st.caption(f"{len(st.session_state.variants)} prompt variant(s) configured")
with c2:
    if st.button ("▷ Run Experiment",type="primary"):
        st.session_state["last_experiment"]={
            "Experiment_name": experiment_name,
            "task_type": task_type,
            "execution_mode": execution_mode,
            "runs_per_prompt": runs_per_prompt,
            "variants": st.session_state.variants,
            "results":[]
        }
        with st.spinner("Running prompts in Ollama..."):
            results= run_experiment(st.session_state.variants, runs_per_prompt)
            st.session_state["last_experiment"]["results"]= results
        st.switch_page("pages/Comparison.py")