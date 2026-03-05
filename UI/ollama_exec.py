import time 
import pandas as pd
import ollama

#ollama serve / ollama list to verify
#to kill: taskkill /IM ollama.exe /F

def run_single_variant(variant, runs, model="qwen2"):
    prompt_text=f"""{variant['system_prompt']}\n\n{variant['instruction_prompt']}\n\n{variant['context']}""".strip()
    results=[]
    for _ in range(runs):
        start = time.time()
        response= ollama.generate(model=model, prompt=prompt_text,options={"temperature":0.0})
        latency=(time.time()-start)*1000
        prompt_tokens=response["prompt_eval_count"]
        complete_tokens= response["eval_count"]
        tokens= prompt_tokens+complete_tokens
        cost= tokens *0.00002
        quality= complete_tokens
        output=response["response"]
        results.append({"output":output,"latency":latency, "tokens":tokens, "cost":cost,"quality":quality})
    return results
def run_experiment(variants, runs_per_prompt):
    aggregated_results=[]
    for i, variant in enumerate(variants):
        results= run_single_variant(variant, runs_per_prompt)
        avg_latency= sum(r["latency"] for r in results)/len(results)
        avg_tokens= sum(r["tokens"] for r in results)/len(results)
        avg_cost= sum(r["cost"] for r in results)/len(results)
        avg_quality= sum(r["quality"] for r in results)/len(results)
        variance=pd.Series([r["latency"]for r in results]).var()
    
        aggregated_results.append({
            "variant":f"Variant{i+1}({variant['strategy_type']})",
            "cost":round(avg_cost,4),
            "latency": round(avg_latency,2),
            "tokens":int(avg_tokens),
            "quality":round(avg_quality,2),
            "variance":round(variance,2),
            "efficiency": round((avg_quality/(avg_cost*avg_latency))if avg_cost*avg_latency>0 else 0,2),
        })
    return aggregated_results