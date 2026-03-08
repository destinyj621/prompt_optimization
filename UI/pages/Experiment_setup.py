import streamlit as st

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

experiment_name = st.text_input(
    "Experiment Name",
    placeholder="e.g., prompt-benchmark-run-1",
)

task_options = {f"{t['task_id']} - {t['task_name']}": t for t in tasks}
strategy_options = {f"{s['strategy_id']} - {s['strategy_name']}": s for s in strategies}
model_options = {f"{m['model_id']} - {m['model_name']}": m for m in models}

selected_task = task_options[st.selectbox("Select Task", list(task_options.keys()))]
selected_strategy = strategy_options[st.selectbox("Select Prompt Strategy", list(strategy_options.keys()))]
selected_model = model_options[st.selectbox("Select Model", list(model_options.keys()))]

raw_input_text = st.text_area(
    "Raw Input (Optional)",
    placeholder="Enter raw input text. If provided, it will be used for this run.",
    height=120,
)

input_options = {"None (use raw input only)": None}
for row in dataset_inputs:
    preview = row["input_text"].strip().replace("\n", " ")
    if len(preview) > 70:
        preview = preview[:70] + "..."
    input_options[f"{row['input_id']} - {preview}"] = row["input_id"]

selected_input_id = input_options[
    st.selectbox("Or Select Existing Dataset Input", list(input_options.keys()))
]

run_count = st.number_input("Number of Runs", min_value=1, value=3, step=1)

if st.button("Run Experiment", type="primary"):
    payload = {
        "task_id": selected_task["task_id"],
        "strategy_id": selected_strategy["strategy_id"],
        "model_id": selected_model["model_id"],
        "run_count": int(run_count),
        "input_text": raw_input_text,
        "raw_input": raw_input_text,
        "input_id": selected_input_id,
    }

    with st.spinner("Running benchmark..."):
        try:
            result = run_experiment(payload)
        except Exception as exc:
            st.error(f"Experiment failed: {exc}")
            st.stop()

    st.session_state["last_experiment"] = {
        "experiment_name": experiment_name,
        "task": selected_task,
        "strategy": selected_strategy,
        "model": selected_model,
        "run_count": int(run_count),
        "result": result,
    }
    st.success("Experiment completed.")
    st.switch_page("pages/Comparison.py")
