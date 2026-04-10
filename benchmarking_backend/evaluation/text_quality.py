from __future__ import annotations
from dataclasses import dataclass
import re

@dataclass
class TextQualityEvaluator:
    def evaluate(self, output_text: str) -> dict[str, float]:
        if not output_text or not output_text.strip():
            return {
                "quality_score": 0.0,
                "length_score": 0.0,
                "coherence_score":0.0,
            }
        length= len(output_text.split())
        length_score= min(100.0, (length/50)*100)
        coherence_score= 100.0 if self.__looks__coherent(output_text) else 50.0
        quality_score= (length_score *0.4)+ (coherence_score*0.6)

        return {
            "quality_score": quality_score,
            "length_score": length_score,
            "coherence_score": coherence_score,
        }
    
    def __looks__coherent(self, text: str) -> bool:
        return bool(re.search(r"[.!?]$", text.strip()))