"""experiment_setup.py"""
import streamlit as st
import uuid

from ollama_exec import get_dataset_inputs, get_models, get_strategies, get_tasks, run_experiment

st.set_page_config(page_title="Experiment Setup", layout="wide")
def load_css():
    with open(".streamlit/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
load_css()
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
    st.session_state.variants = [
        {
            "id": str(uuid.uuid4()),
            "strategy_type": "Zero-Shot",
            "expected_label": "",
            "strategy_id": None,
            "model_id": None,
            "description": "Baseline strategy",
            "system_prompt": "",
            "instruction_prompt": "",
            "context": "",
        }
    ]

seen_ids = set()
for v in st.session_state.variants:
    if not isinstance(v["id"], str) or v["id"] in seen_ids:
        v["id"] = str(uuid.uuid4())
    seen_ids.add(v["id"])
st.divider()
experiment_name= st.text_input("Experiment Name",placeholder="e.g., prompt-benchmark-run-1",
                               help="Give your experiment a descriptive name for easy identification in results and history")
st.divider()
st.subheader("Task Definition")
c1, c2= st.columns(2)

task_options= {f"{t['task_id']}-{t['task_name']}": t for t in tasks}
selected_task= task_options[st.selectbox("Select Task", list(task_options.keys()))]
task_name = selected_task["task_name"]
task_id = selected_task["task_id"]
if task_name == "Text Classification":
    input_placeholder = "Enter text to classify sentiment..."
elif task_name == "Summarization":
    input_placeholder = "Enter a document to summarize..."
elif task_name == "Question Answering":
    input_placeholder = (
        "Enter context first.\n\n---\n\nQuestion: <your question here>"
    )
else:
    input_placeholder = "Enter input text..."

with c1:

    custom_input_text = st.text_area(
        "Custom Input Text",
        placeholder=input_placeholder,
        height=120,
        key="custom_input_text",
    )
    reference_text = ""
    if task_name == "Summarization":
        reference_text = st.text_area("Reference Summary",
                                      placeholder= "Optional: provide a high-quality referenece summary for evaluation...",
                                      height=120, key="reference_summary",)
    elif task_name == "Question Answering":
        reference_text = st.text_area("Reference Answer",
                                      placeholder = "Optional: provide the correct answer for evaluation...",
                                      height = 120, key="reference_answer",)
        
with c2:
    dataset_file= st.file_uploader("Evaluation Dataset (CSV, JSON, PDF)",type=["csv","json","jsonl","pdf"], 
                                   help="Upload a dataset file to evaluate multiple inputs. Currently supports CSV, JSON, JSONL, and PDF formats")
    input_options = {"None (use raw input only)": None}
    for row in dataset_inputs:
        preview = row["input_text"].strip().replace("\n", " ")
        if len(preview) > 70:
            preview = preview[:70] + "..."
        input_options[f"{row['input_id']} - {preview}"] = row["input_id"]
    
    selected_input_key = st.selectbox(
        "Or Select Existing Dataset Input",
        list(input_options.keys()), key="existing_dataset_input",
        help="Choose from previously stored dataset inputs, or select 'None' to use only the prompt inputs below"
    )
    selected_input_id = input_options[selected_input_key]


st.caption(
    "Use an existing dataset input or enter custom input text. "
    "The prompt fields below configure the instructions sent to the model."
)
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
to_duplicate = None
model_options = {f"{m['model_id']} - {m['model_name']}": m for m in models}
strategy_options = {f"{s['strategy_id']} - {s['strategy_name']}": s for s in strategies}

for i, variant in enumerate(st.session_state.variants):
    with st.container(border=True):
        c1, c2, c3 = st.columns([4, 1, 1])
        with c1:
            st.markdown(f"### Variant {i+1}")
        with c2:
            if st.button("Duplicate", key=f"duplicate_{variant['id']}"):
                to_duplicate = i
        with c3:
            if len(st.session_state.variants)>1:
                if st.button("Remove",key=f"remove_{variant['id']}"):
                    to_remove= i
    c1, c2= st.columns(2)
    with c1:
        selected_strategy_key = st.selectbox(
            "Select Strategy",
            list(strategy_options.keys()),
            index=0,
            key=f"strategy_{variant['id']}",
            help="Choose prompting strategy: Zero-Shot (no examples) or Few-Shot (with examples)"
        )
        variant["strategy_id"] = strategy_options[selected_strategy_key]["strategy_id"]
        variant["strategy_type"] = strategy_options[selected_strategy_key]["strategy_name"]
        variant_model_key = st.selectbox(
            "Select Model",
            list(model_options.keys()),
            index=0,
            key=f"model_{variant['id']}",
            help="Choose the Ollama model to use for this experiment"
        )
        variant["model_id"] = model_options[variant_model_key]["model_id"]
    with c2:
        variant["description"] = st.text_input(
            "Description",
            value=variant["description"],
            placeholder="e.g., Baseline with direct instructions",
            key=f"description_{variant['id']}",
            help="Optional description to identify this prompt variant"
        )
        if task_name == "Sentiment Classification":
            label_options = [   "", "positive", "negative", "neutral"]
            current_label = variant.get("expected_label", "")
            if current_label not in label_options:
                current_label = ""
            variant["expected_label"] = st.selectbox(
                "Evaluation Label",
                label_options,
                index=label_options.index(current_label),
                key=f"expected_label_{variant['id']}",
            )
        else:
            variant["expected_label"]= ""
    system_prompt_help = {
        "Sentiment Classification": "The text you want to classify as positive, negative, or neutral",
        "Summarization": "The long text that you want the model to summarize",
        "Question Answering": "The question you want answered (context will be provided separately if needed)"
    }.get(selected_task["task_name"], "Define the AI's role and behavior (optional)")

    variant["system_prompt"] = st.text_area(
        "System Prompt",
        value=variant["system_prompt"],
        placeholder="Define the AI's role and behaviour...",
        height=120,
        key=f"system_{variant['id']}",
        help=system_prompt_help
    )
    instruction_help = {
        "Sentiment Classification": "Instructions for how to classify the sentiment (e.g., 'Classify this text as positive, negative, or neutral')",
        "Summarization": "Instructions for how to summarize (e.g., 'Write a concise summary in 2-3 sentences')",
        "Question Answering": "Instructions for how to answer (e.g., 'Answer the question using only the provided context')"
    }.get(selected_task["task_name"], "Provide clear task instructions for the AI")
    variant["instruction_prompt"] = st.text_area(
        "Instruction Prompt",
        value=variant["instruction_prompt"],
        placeholder="Provide clear task instructions...",
        height=120,
        key=f"instruction_{variant['id']}",
        help=instruction_help
    )
    variant["context"] = st.text_area(
        "Context / Examples (Few-Shot Examples)", # used to provide few-shot examples or additional context to the model without including it in the main instruction prompt
        value=variant["context"],
        placeholder="Add examples or additional context...",
        height=120,
        key=f"context_{variant['id']}",
        help="For Few-Shot strategies: Add example input-output pairs. For Question Answering: Add context information. Format: 'Example 1: Input: [text] Output: [expected]'"
    )

    estimated_tokens = max(50, len(variant["instruction_prompt"]) // 3)
    estimated_cost = estimated_tokens * 0.00002
    st.caption(f"Estimated tokens: ~{estimated_tokens} | Estimated cost: ~${estimated_cost:.4f}")

if to_duplicate is not None:
    new_variant = dict(st.session_state.variants[to_duplicate])
    new_variant["id"] = str(uuid.uuid4())
    st.session_state.variants.insert(to_duplicate + 1, new_variant)
    st.rerun()

if to_remove is not None:
    st.session_state.variants.pop(to_remove)
    st.rerun()

st.divider()
st.subheader("Execution Configuration")
execution_mode = st.radio(
    "Execution Mode",
    ["Local Execution"],
    index=0,
    help="Mock: Test without running models. Limited Cloud: Use cloud APIs with limits. Local: Use local Ollama models"
)
runs_per_prompt = st.number_input("Runs per Prompt", min_value=1, max_value=50, value=5,
                                   help="Number of times to run each prompt variant for statistical reliability (higher = more accurate but slower)")

st.divider()
c1, c2 = st.columns([9, 1])
with c1:
    st.caption(f"{len(st.session_state.variants)} prompt variant(s) configured")
with c2:
    if st.button("Run Experiment", type="primary"):
        valid = True

        if selected_input_id is None and not custom_input_text.strip():
            st.error("Provide either a custom input text or select an existing dataset input.")
            valid = False

        for variant in st.session_state.variants:
            if variant["strategy_id"] is None or variant["model_id"] is None:
                st.error(f"Variant {variant['id']} is missing a strategy or model. Cannot run.")
                valid = False
                break

        if valid:
            st.session_state.pop("last_experiment", None)
            experiment_run_id = str(uuid.uuid4())
            raw_input_text = custom_input_text.strip() or None
            payloads = []

            for variant in st.session_state.variants:
                payload = {
                    "task_id": int(task_id),
                    "strategy_id": int(variant["strategy_id"]),
                    "model_id": int(variant["model_id"]),
                    "run_count": int(runs_per_prompt),
                    "input_id": None if raw_input_text else selected_input_id,
                    "input_text": raw_input_text,
                    "raw_input": raw_input_text,
                    "system_prompt": variant["system_prompt"],
                    "instruction_prompt": variant["instruction_prompt"],
                    "context": variant["context"],
                    "experiment_run_id": experiment_run_id,
                    "reference_output": reference_text.strip(), #added this
                }
                if variant.get("expected_label"):
                    payload["expected_label"] = variant["expected_label"]
                payloads.append(payload)

            results = []
            with st.spinner("Running experiment..."):
                for payload in payloads:
                    try:
                        result = run_experiment(payload)
                        summary = {**result.get("summary", {})}
                        run_records = result.get("run_records", [])
                        summary["output_text"] = run_records[-1]["output_text"] if run_records else ""
                        summary["expected_label"] = payload.get("expected_label", "") or (
                            run_records[-1].get("expected_label", "") if run_records else ""
                        )
                        summary["reference_output"] = payload.get("reference_output", "")
                        summary["run_records"] = run_records
                        results.append(summary)
                    except Exception as exc:
                        st.error(f"Experiment failed for variant {payload['strategy_id']}: {exc}")
                        st.exception(exc)

            if results:
                st.session_state["last_experiment"] = {
                    "experiment_name": experiment_name,
                    "task_id": int(task_id),
                    "task_name": selected_task["task_name"],
                    "execution_mode": execution_mode,
                    "runs_per_prompt": runs_per_prompt,
                    "variants": st.session_state.variants,
                    "results": results,
                }
                st.success("Experiment completed.")
                st.switch_page("pages/Comparison.py")
            else:
                st.error("No results were returned.")