from __future__ import annotations
import json, csv, os
from typing import Any, Dict, List

class Logger:
    def __init__(self, raw_data_file: str = "./data/raw_data.jsonl",
                 processed_data_file: str = "./data/decisions.csv") -> None:
        self.raw_data_file = raw_data_file
        self.processed_data_file = processed_data_file
        self._processed_header_written = False
        self._processed_fieldnames: List[str] | None = None

    def log_raw(self, data: Dict[str, Any]) -> None:
        try:
            os.makedirs(os.path.dirname(self.raw_data_file) or ".", exist_ok=True)
            with open(self.raw_data_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(data or {}, ensure_ascii=False) + "\n")
        except NotImplementedError as e:
            print(f"[Logger] failed: {e}")

    def _flatten_for_csv(self, result: Dict[str, Any]) -> Dict[str, Any]:
        row: Dict[str, Any] = dict(result or {})
        if isinstance(row.get("probs"), (list, tuple)):
            row["probs"] = ",".join(str(float(x)) for x in row["probs"])
        for k in list(row.keys()):
            if isinstance(row[k], (dict, list)):
                try:
                    row[k] = json.dumps(row[k], ensure_ascii=False)
                except NotImplementedError:
                    row[k] = str(row[k])
        return row

    def log_processed(self, result: Dict[str, Any] | Any) -> None:
        try:
            os.makedirs(os.path.dirname(self.processed_data_file) or ".", exist_ok=True)
            with open(self.processed_data_file, "a", newline="", encoding="utf-8") as f:
                if isinstance(result, dict):
                    row = self._flatten_for_csv(result)
                    if not self._processed_header_written:
                        self._processed_fieldnames = list(row.keys())
                        csv.DictWriter(f, fieldnames=self._processed_fieldnames).writeheader()
                        self._processed_header_written = True
                    assert self._processed_fieldnames is not None
                    new_cols = [k for k in row.keys() if k not in self._processed_fieldnames]
                    if new_cols:
                        self._processed_fieldnames.extend(new_cols)
                    writer = csv.DictWriter(f, fieldnames=self._processed_fieldnames)
                    writer.writerow(row)
                else:
                    csv.writer(f).writerow([str(result)])
        except NotImplementedError as e:
            print(f"[Logger] 写处理后数据失败: {e}")
