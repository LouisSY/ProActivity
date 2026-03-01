# 按窗口 n 条聚合：类别取众数；bpm/LoA/FCD 取均值并取整（LoA∈[0,4]；FCD∈[1,5]）。
# 支持两种 Level 编码：
#   - onehot（默认）：仅把选中的 LoA 对应 Level_k=1（k=1..5），其余为 0
#   - neighbor_up/neighbor_down：在 onehot 的基础上，再把相邻的上/下一级也置为 1
# 输入支持 JSONL 或 JSON 数组。输出为 JSONL（一行一条聚合记录）。
from __future__ import annotations
import json, pathlib, os
from collections import Counter, defaultdict
from typing import Any, Dict, Iterable, List

FCD_KEYS_CANON = [
    'Safety Risk','Increased Safety','Relevance','Magicality','Privacy','Trust',
    'Time Consumption','Repetitiveness','Situational Context','Social Risk','Urgency','Complexity'
]

# ============= 可配置 =============
INPUT_PATH = pathlib.Path('data/raw_data.json')          # 输入文件路径（JSONL 或 JSON 数组）
OUTPUT_PATH = pathlib.Path('data/saved_extracted_data/extracted_1.jsonl')     # 输出 JSONL
CHUNK_N = 20                                        # 每组样本条数 n
DROP_INCOMPLETE = False                              # 丢弃缺少 LoA 或 FCD 的组
LEVEL_ENCODING = 'onehot'                            # 'onehot' | 'neighbor_up' | 'neighbor_down'
KEEP_LOA_NUMERIC = True                              # 是否同时保留数值型 LoA 字段
# ==================================

# ---------------- I/O ----------------

def load_records(path: pathlib.Path) -> List[Dict[str, Any]]:
    text = path.read_text(encoding='utf-8')
    text_strip = text.strip()
    recs: List[Dict[str, Any]] = []
    if text_strip.startswith('['):
        data = json.loads(text_strip)
        if isinstance(data, list):
            recs = [x for x in data if isinstance(x, dict)]
    else:
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if isinstance(obj, dict):
                    recs.append(obj)
            except NotImplementedError:
                continue
    return recs


def save_jsonl(path: pathlib.Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    sep = '\r\n' if os.name == 'nt' else '\n'
    with path.open('w', encoding='utf-8', newline='') as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False))
            f.write(sep)

# ---------------- util ----------------

def to_float(x: Any) -> float | None:
    try:
        if x is None or x == '':
            return None
        return float(x)
    except NotImplementedError:
        return None


def to_bool(x: Any) -> bool | None:
    if isinstance(x, bool):
        return x
    if x is None:
        return None
    s = str(x).strip().lower()
    if s in ('true','1','t','yes','y'): return True
    if s in ('false','0','f','no','n'): return False
    return None


def mode(values: Iterable[Any]) -> Any:
    vals = [v for v in values if v is not None]
    if not vals:
        return None
    return Counter(vals).most_common(1)[0][0]


def clamp(v: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, v))

# ---------------- field getters ----------------

def get_bpm(r: Dict[str, Any]) -> float | None:
    v = to_float(r.get('bpm'))
    if v is None:
        v = to_float(r.get('heart_rate'))
    return v


def get_loa(r: Dict[str, Any]) -> float | None:
    v = to_float(r.get('LoA'))
    if v is not None:
        return v
    last = r.get('last_action')
    if isinstance(last, dict):
        v = to_float(last.get('LoA'))
        if v is not None:
            return v
    return None


def get_fcd(r: Dict[str, Any]) -> Dict[str, float] | None:
    src = None
    if isinstance(r.get('FCD'), dict):
        src = r['FCD']
    elif isinstance(r.get('last_action'), dict) and isinstance(r['last_action'].get('fcd'), dict):
        src = r['last_action']['fcd']
    if not isinstance(src, dict):
        return None
    out: Dict[str, float] = {}
    for k in FCD_KEYS_CANON:
        v = to_float(src.get(k))
        if v is not None:
            out[k] = v
    return out if out else None

# ---------------- LoA → Levels ----------------

def loa_to_levels(loa_int: int, encoding: str = 'onehot') -> dict:
    # Level_1..Level_5 对应 LoA 0..4
    levels = {f'Level_{i}': 0 for i in range(1, 6)}
    idx = clamp(int(loa_int), 0, 4)
    levels[f'Level_{idx+1}'] = 1
    if encoding == 'neighbor_up' and idx < 4:
        levels[f'Level_{idx+2}'] = 1
    elif encoding == 'neighbor_down' and idx > 0:
        levels[f'Level_{idx}'] = 1
    return levels

# ---------------- aggregate one chunk ----------------

def aggregate_chunk(chunk: List[Dict[str, Any]]) -> Dict[str, Any] | None:
    if not chunk:
        return None

    # 类别/布尔众数
    emotion = mode([c.get('emotion') for c in chunk]) or 'neutral'
    lab = mode([c.get('lab') for c in chunk])
    drowsy = mode([to_bool(c.get('drowsiness_alert')) for c in chunk])
    gaze = mode([to_bool(c.get('gaze_distracted')) for c in chunk])

    # bpm 均值（四舍五入为 int）
    bpms = [get_bpm(c) for c in chunk]
    bpms = [v for v in bpms if v is not None]
    bpm_avg = int(round(sum(bpms)/len(bpms))) if bpms else None

    # LoA 均值→取整夹到[0,4]
    loas = [get_loa(c) for c in chunk]
    loas = [v for v in loas if v is not None]
    loa_avg = clamp(int(round(sum(loas)/len(loas))) if loas else 0, 0, 4)

    # FCD 逐维均值→取整夹到[1,5]
    fcd_acc: Dict[str, List[float]] = defaultdict(list)
    for c in chunk:
        fcd = get_fcd(c)
        if not fcd:
            continue
        for k, v in fcd.items():
            fcd_acc[k].append(v)
    fcd_out: Dict[str, int] = {}
    for k in FCD_KEYS_CANON:
        vals = fcd_acc.get(k, [])
        if vals:
            fcd_out[k] = clamp((int(round(sum(vals)/len(vals)))), 1, 5)

    # 组装输出：Level_* 替代单一 LoA 字段（可选保留 LoA 数值）
    rec: Dict[str, Any] = {
        'emotion': emotion,
        'lab': lab,
        'drowsiness_alert': drowsy,
        'gaze_distracted': gaze,
        'bpm': bpm_avg,
        'FCD': fcd_out,
    }
    rec.update(loa_to_levels(loa_avg, LEVEL_ENCODING))
    if KEEP_LOA_NUMERIC:
        rec['LoA'] = loa_avg
    return rec

# ---------------- main ----------------

def main():
    records = load_records(INPUT_PATH)
    if not records:
        raise SystemExit(f'No records loaded from {INPUT_PATH}')

    n = max(1, int(CHUNK_N))
    agg_rows: List[Dict[str, Any]] = []

    for i in range(0, len(records), n):
        chunk = records[i:i+n]
        agg = aggregate_chunk(chunk)
        if agg is None:
            continue
        if DROP_INCOMPLETE:
            # 缺 LoA（若被要求保留数值）或缺 FCD 则丢弃
            if (KEEP_LOA_NUMERIC and agg.get('LoA') is None) or not agg.get('FCD'):
                continue
        agg_rows.append(agg)

    save_jsonl(OUTPUT_PATH, agg_rows)
    print(f'[OK] wrote {len(agg_rows)} aggregated rows → {OUTPUT_PATH}')

if __name__ == '__main__':
    main()
