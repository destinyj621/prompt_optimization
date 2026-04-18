from dataclasses import dataclass
import re

@dataclass
class QAEvaluator:
    def normalize(self, text:str)-> str:
        return re.sub(f"\s+"," ", text.strip.lower())
    def evaluate(self, reference: str, prediction: str)-> dict[str,float]:
        ref= self.normalize(reference)
        pred= self.normalize(prediction)
        if not ref or not pred:
            return {
                "exact_match": 0.0,
                "f1_score": 0.0,
                "quality_score": 0.0,
            }
        exact_match= 1.0 if ref == pred else 0.0
        ref_tokens= set(ref.split())
        pred_tokens= set(pred.split())
        overlap = ref_tokens & pred_tokens
        precision = len(overlap)/ len(pred_tokens) if pred_tokens else 0
        recall = len(overlap)/ len(ref_tokens) if ref_tokens else 0
        f1= ((2*precision*recall)/(precision+recall)if (precision+recall)>0 else 0.0)
        quality_score = (f1*100*0.7)+ (exact_match*100*0.3)
        return {
            "exact_match":exact_match,
            "f1_score": f1*100,
            "quality_score": quality_score,
        }