import streamlit as st
import uuid
import re
from typing import List, Dict, Any

from ollama_exec import get_dataset_inputs, get_models, get_strategies, get_tasks, run_experiment

def _parse_context_examples(context_text: str) -> List[Dict[str, Any]]:
    """Parse context text into examples format for few-shot strategies."""
    if not context_text.strip():
        return []
    
    examples = []
    # Split by "Example" or similar patterns
    parts = re.split(r'(?:^|\n)(?:Example\s*\d*:?\s*|E\.g\.?\s*|For example:?\s*)', context_text.strip(), flags=re.IGNORECASE)
    
    for i, part in enumerate(parts):
        if not part.strip():
            continue
        
        # Try to split by common separators
        if '\nInput:' in part and '\nOutput:' in part:
            # Already in structured format
            input_match = re.search(r'Input:\s*(.+?)(?:\nOutput:|$)', part, re.DOTALL)
            output_match = re.search(r'Output:\s*(.+?)(?:\n|$)', part, re.DOTALL)
            if input_match and output_match:
                examples.append({
                    "example_input": input_match.group(1).strip(),
                    "example_output": output_match.group(1).strip(),
                    "example_order": i
                })
        elif ':' in part:
            # Try to split by first colon
            colon_idx = part.find(':')
            if colon_idx > 0:
                input_part = part[:colon_idx].strip()
                output_part = part[colon_idx+1:].strip()
                if input_part and output_part:
                    examples.append({
                        "example_input": input_part,
                        "example_output": output_part,
                        "example_order": i
                    })
    
    # If no structured examples found, treat the whole context as one example
    if not examples and context_text.strip():
        examples.append({
            "example_input": context_text.strip(),
            "example_output": "Expected output format",
            "example_order": 1
        })
    
    return examples

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
experiment_name= st.text_input(
    "Experiment Name",
    placeholder="e.g., prompt-benchmark-run-1",
    help="Give your experiment a descriptive name for easy identification in results and history"
)
st.divider()
st.subheader("Task Definition")
c1, c2= st.columns(2)
with c1:
    task_options= {f"{t['task_id']}-{t['task_name']}": t for t in tasks}
    selected_task= task_options[st.selectbox(
        "Select Task", 
        list(task_options.keys()),
        help="Choose the type of task to benchmark: Sentiment Classification, Summarization, or Question Answering"
    )]
with c2:
    # Show expected label field for Sentiment Classification
    if selected_task["task_name"] == "Sentiment Classification":
        expected_label_options = ["", "positive", "negative", "neutral"]
        selected_expected_label = st.selectbox(
            "Expected Sentiment Label (for accuracy evaluation)",
            expected_label_options,
            index=0,
            help="Required for accuracy measurement in sentiment classification tasks"
        )
    else:
        selected_expected_label = ""
    
    dataset_file= st.file_uploader(
        "Evaluation Dataset (CSV, JSON, PDF)",
        type=["csv","json","jsonl","pdf"],
        help="Upload a dataset file to evaluate multiple inputs. Currently supports CSV, JSON, JSONL, and PDF formats"
    )
    input_options = {"None (use raw input only)": None}
    for row in dataset_inputs:
        preview = row["input_text"].strip().replace("\n", " ")
        if len(preview) > 70:
            preview = preview[:70] + "..."
        input_options[f"{row['input_id']} - {preview}"] = row["input_id"]
    
    selected_input_key = st.selectbox(
        "Or Select Existing Dataset Input",
        list(input_options.keys()), 
        key="existing_dataset_input",
        help="Choose from previously stored dataset inputs, or select 'None' to use only the prompt inputs below"
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
to_duplicate = None
model_options = {f"{m['model_id']} - {m['model_name']}": m for m in models}
strategy_options = {f"{s['strategy_id']} - {s['strategy_name']}": s for s in strategies}

for i, variant in enumerate(st.session_state.variants):
    with st.container(border=True):
        c1, c2, c3 = st.columns([4,1,1])
        with c1:
            st.markdown(f"### Variant {i+1}")
        with c2:
            if st.button("Duplicate", key=f"duplicate_{variant['id']}"):
                to_duplicate = i
        with c3:
            if len(st.session_state.variants) > 1:
                if st.button("Remove", key=f"remove_{variant['id']}"):
                    to_remove = i
    c1, c2= st.columns(2)
    with c1:
        strategy_keys = list(strategy_options.keys())
        default_strategy = next(
            (key for key, value in strategy_options.items() if value["strategy_id"] == variant.get("strategy_id")),
            strategy_keys[0],
        )
        selected_strategy_key = st.selectbox(
            "Select Strategy",
            strategy_keys,
            index=strategy_keys.index(default_strategy) if default_strategy in strategy_keys else 0,
            key=f"strategy_{variant['id']}",
            help="Choose prompting strategy: Zero-Shot (no examples) or Few-Shot (with examples)"
        )
        variant["strategy_id"] = strategy_options[selected_strategy_key]["strategy_id"]
        variant["strategy_type"] = strategy_options[selected_strategy_key]["strategy_name"]

    with c2: 
        variant["description"]= st.text_input(
            "Description", 
            value=variant["description"],
            placeholder="e.g., Baseline with direct instructions",
            key=f"description_{variant['id']}",
            help="Optional description to identify this prompt variant"
        )
    
    # Dynamic system prompt label based on task
    system_prompt_label = {
        "Sentiment Classification": "Text to Classify",
        "Summarization": "Text to Summarize", 
        "Question Answering": "Question"
    }.get(selected_task["task_name"], "System Prompt")
    
    model_keys = list(model_options.keys())
    default_model = next(
        (key for key, value in model_options.items() if value["model_id"] == variant.get("model_id")),
        model_keys[0],
    )
    variant_model_key = st.selectbox(
        "Select Model",
        model_keys,
        index=model_keys.index(default_model) if default_model in model_keys else 0,
        key=f"model_{variant['id']}",
        help="Choose the Ollama model to use for this experiment"
    )
    variant["model_id"] = model_options[variant_model_key]["model_id"]
    
    system_prompt_help = {
        "Sentiment Classification": "The text you want to classify as positive, negative, or neutral",
        "Summarization": "The long text that you want the model to summarize",
        "Question Answering": "The question you want answered (context will be provided separately if needed)"
    }.get(selected_task["task_name"], "Define the AI's role and behavior (optional)")
    
    variant["system_prompt"]=st.text_area(
        system_prompt_label, 
        value=variant["system_prompt"], 
        placeholder=system_prompt_help,
        height=80, 
        key=f"system_{variant['id']}",
        help=system_prompt_help
    )
    
    instruction_help = {
        "Sentiment Classification": "Instructions for how to classify the sentiment (e.g., 'Classify this text as positive, negative, or neutral')",
        "Summarization": "Instructions for how to summarize (e.g., 'Write a concise summary in 2-3 sentences')",
        "Question Answering": "Instructions for how to answer (e.g., 'Answer the question using only the provided context')"
    }.get(selected_task["task_name"], "Provide clear task instructions for the AI")
    
    variant["instruction_prompt"]=st.text_area(
        "Instruction Prompt *", 
        value=variant["instruction_prompt"], 
        placeholder=instruction_help,
        height=120, 
        key=f"Instruction_{variant['id']}",
        help=instruction_help
    )
    variant["context"]=st.text_area(
        "Context/ Examples (Optional)", 
        value=variant["context"], 
        placeholder="Add examples or additional context...",
        height=80, 
        key=f"context_{variant['id']}",
        help="For Few-Shot strategies: Add example input-output pairs. For Question Answering: Add context information. Format: 'Example 1: Input: [text] Output: [expected]'"
    )
    estimated_tokens= max(50, len(variant["instruction_prompt"])//3)
    estimated_cost = estimated_tokens* 0.00002
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
execution_mode= st.radio(
    "Execution Mode", 
    ["Mock Estimation", "Limited Cloud Execution", "Local Execution"], 
    index=0,
    help="Mock: Test without running models. Limited Cloud: Use cloud APIs with limits. Local: Use local Ollama models"
)
runs_per_prompt= st.number_input(
    "Runs per Prompt",
    min_value=1, 
    max_value=50, 
    value=5,
    help="Number of times to run each prompt variant for statistical reliability (higher = more accurate but slower)"
)
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
        
        # Validate expected label for Sentiment Classification
        if selected_task["task_name"] == "Sentiment Classification" and not selected_expected_label:
            st.error("Expected sentiment label is required for Sentiment Classification tasks to measure accuracy.")
            valid = False
        
        if valid:
            st.session_state.pop("last_experiment", None)
            experiment_run_id= str(uuid.uuid4())
            payloads=[]
            for variant in st.session_state.variants:
                input_text_value = f"{variant['system_prompt']}\n{variant['instruction_prompt']}".strip()
                if not input_text_value:
                    input_text_value = None
                
                # Parse context into examples for few-shot strategies
                runtime_examples = None
                prompt_config_context = variant["context"]
                if "few" in variant["strategy_type"].lower() and variant["context"].strip():
                    runtime_examples = _parse_context_examples(variant["context"])
                    prompt_config_context = ""  # Don't include examples in prompt config for few-shot
                
                payloads.append({
                    "task_id": selected_task["task_id"],
                    "strategy_id": int(variant["strategy_id"]),
                    "model_id": int(variant["model_id"]),
                    "run_count": int(runs_per_prompt),
                    "input_text": input_text_value,
                    "raw_input": input_text_value,
                    "input_id": selected_input_id,
                    "expected_label": selected_expected_label,
                    "experiment_run_id": experiment_run_id,
                    "runtime_examples": runtime_examples,
                    "system_prompt": variant["system_prompt"],
                    "instruction_prompt": variant["instruction_prompt"],
                    "context": prompt_config_context,
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
                    "task_id": selected_task["task_id"],
                    "execution_mode": execution_mode,
                    "runs_per_prompt": runs_per_prompt,
                    "variants": st.session_state.variants,
                    "results": results
                }
                st.success("Experiment completed.")
                st.switch_page("pages/Comparison.py")
            else:
                st.error("No results were returned.")