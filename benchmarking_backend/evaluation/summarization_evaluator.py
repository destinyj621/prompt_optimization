"""summarization_evaluator.py"""
from dataclasses import dataclass
from rouge_score import rouge_scorer

@dataclass
class SummarizationEvaluator:
    def __init__(self):
        self.scorer = rouge_scorer.RougeScorer(["rouge1","rouge2","rougeL"], use_stemmer=True)
    def evaluate(self, reference: str, prediction: str)-> dict[str, float]:
        if not reference or not prediction:
            return {
                "rouge1": 0.0,
                "rouge2": 0.0,
                "rougeL": 0.0,
                "quality_score": 0.0,
            }
        scores = self.scorer.score(reference, prediction)
        rouge1= scores["rouge1"].fmeasure * 100
        rouge2= scores["rouge2"].fmeasure * 100
        rougeL= scores["rougeL"].fmeasure * 100
        quality_score= (rougeL*0.6)+(rouge1*0.4)
        return {
            "rouge1":rouge1,
            "rouge2":rouge2,
            "rougeL":rougeL,
            "quality_score":quality_score,
        }