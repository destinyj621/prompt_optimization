import streamlit as st
import uuid

from ollama_exec import get_dataset_inputs, get_models, get_strategies, get_tasks, run_experiment

st.set_page_config(page_title="Experiment Setup", layout="wide")
st.title("Experiment Setup")
st.caption("Configure and run benchmark experiments.")

try:
    tasks = get_tasks()
    strategies = get_strategies()
    models = get_models()
    dataset_inputs = get_dataset_inputs()
except Exception as exc:
    st.error(f"Backend connection failed: {exc}")
    st.stop()

if not tasks or not strategies or not models:
    st.error("Missing required backend data (tasks, strategies, or models).")
    st.stop()


if "variants" not in st.session_state:
    st.session_state.variants = [{
        "id":str(uuid.uuid4()),
        "strategy_type":"Zero-Shot",
        "strategy_id": None,
        "model_id": None,
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
st.divider()
experiment_name= st.text_input("Experiment Name",placeholder="e.g., prompt-benchmark-run-1")
st.divider()
st.subheader("Task Definition")
c1, c2= st.columns(2)
with c1:
    task_options= {f"{t['task_id']}-{t['task_name']}": t for t in tasks}
    selected_task= task_options[st.selectbox("Select Task", list(task_options.keys()))]
with c2:
    dataset_file= st.file_uploader("Evaluation Dataset (CSV, JSON, PDF)",type=["csv","json","jsonl","pdf"])
    input_options = {"None (use raw input only)": None}
    for row in dataset_inputs:
        preview = row["input_text"].strip().replace("\n", " ")
        if len(preview) > 70:
            preview = preview[:70] + "..."
        input_options[f"{row['input_id']} - {preview}"] = row["input_id"]
    
    selected_input_key = st.selectbox(
        "Or Select Existing Dataset Input",
        list(input_options.keys()), key="existing_dataset_input"
    )
    selected_input_id = input_options[selected_input_key]
st.divider()
st.subheader("Prompt Strategies")
if st.button("+ Add Prompt Variant"):
    st.session_state.variants.append({
        "id":str(uuid.uuid4()),
        "strategy_type":"Few-Shot",
        "strategy_id":None,
        "model_id": None,
        "description": "",
        "system_prompt": "",
        "instruction_prompt":"",
        "context":"",
    })
to_remove = None
model_options = {f"{m['model_id']} - {m['model_name']}": m for m in models}
strategy_options = {f"{s['strategy_id']} - {s['strategy_name']}": s for s in strategies}

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
        selected_strategy_key = st.selectbox(
            "Select Strategy",
            list(strategy_options.keys()),
            index=0,
            key=f"strategy_{variant['id']}"
        )
        variant["strategy_id"] = strategy_options[selected_strategy_key]["strategy_id"]
        variant["strategy_type"] = strategy_options[selected_strategy_key]["strategy_name"]

    with c2: 
        variant["description"]= st.text_input("Description", value=variant["description"],
                                                   placeholder="e.g., Baseline with direct instructions",
                                                   key=f"description_{variant['id']}",)
    variant_model_key= st.selectbox("Select Model",list(model_options.keys()), index=0, key=f"model_{variant['id']}")
    variant["model_id"]= model_options[variant_model_key]["model_id"]
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

st.divider()
st.subheader("Execution Configuration")
execution_mode= st.radio("Execution Mode", ["Mock Estimation", "Limited Cloud Execution", "Local Execution"], index=0,)
runs_per_prompt= st.number_input("Runs per Prompt",min_value=1, max_value=50, value=5)
#footer
st.divider()
c1, c2= st.columns([9,1])
with c1:
    st.caption(f"{len(st.session_state.variants)} prompt variants(s) configured")
with c2:
    if st.button("▷ Run Experiment", type="primary"):
        valid=True

        for variant in st.session_state.variants:
            if variant["strategy_id"] is None or variant["model_id"] is None:
                st.error(f"Variant {variant['id']} is missing a strategy or model. Cannot run.")
                valid= False
                break
        if valid:
            st.session_state.pop("last_experiment", None)
            experiment_run_id= str(uuid.uuid4())
            payloads=[]
            for variant in st.session_state.variants:
                input_text_value = f"{variant['system_prompt']}\n{variant['instruction_prompt']}\n{variant['context']}".strip()
                if not input_text_value:
                    input_text_value = None
                payloads.append({
                    "task_id": selected_task["task_id"],
                    "strategy_id": int(variant["strategy_id"]),
                    "model_id": int(variant["model_id"]),
                    "run_count": int(runs_per_prompt),
                    "input_text": input_text_value,
                    "raw_input": input_text_value,
                    "input_id": selected_input_id,
                    "experiment_run_id": experiment_run_id, 
                })
            results = []
            with st.spinner("Running experiment..."):
                for p in payloads:
                    try:
                        result = run_experiment(p)
                        summary = {**result.get("summary",{})} 
                        run_records= result.get("run_records",[])
                        summary["output_text"]= run_records[-1]["output_text"]if run_records else ""
                        summary["run_records"]= run_records 
                        results.append(summary)
                    except Exception as exc:
                        st.error(f"Experiment failed for variant {p['strategy_id']}: {exc}")
            if results:
                st.session_state["last_experiment"] = {
                    "experiment_name": experiment_name,
                    "task": selected_task,
                    "execution_mode": execution_mode,
                    "runs_per_prompt": runs_per_prompt,
                    "variants": st.session_state.variants,
                    "results": results
                }
                st.success("Experiment completed.")
                st.switch_page("pages/Comparison.py")
            else:
                st.error("No results were returned.")