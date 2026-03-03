"""CSV reporting utilities."""

import csv
from typing import Any, Dict, List, Union


class ReportGenerator:
    """Creates and exports benchmark summaries."""

    def generate_strategy_summary(
        self, summary_data: Union[Dict[str, Any], List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """Normalizes summary payload into CSV-exportable rows."""
        if isinstance(summary_data, list):
            return summary_data
        return [summary_data]

    def export_summary_to_csv(self, summary_rows: List[Dict[str, Any]], output_file: str) -> None:
        if not summary_rows:
            raise ValueError("No summary rows to export.")

        fieldnames = list(summary_rows[0].keys())
        with open(output_file, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(summary_rows)
