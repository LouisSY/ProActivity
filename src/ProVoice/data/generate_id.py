
#   python data/generate_id.py --in data/raw_data.jsonl --out data/with_segments.jsonl --chunk 500
#   （--chunk=0 关闭按帧数切段，仅遇到组合键变化时+1）
import argparse, json, pathlib

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="in_jsonl", required=True)
    ap.add_argument("--out", dest="out_jsonl", required=True)
    ap.add_argument("--chunk", type=int, default=0, help="每段最大帧数，0=不按帧数切段")
    # 组合键字段（可以改）
    ap.add_argument("--keys", default="participantid,environment,secondary_task,functionname",
                    help="用于组成段键的字段名，逗号分隔")
    ap.add_argument("--sep", default="|", help="组合键分隔符")
    return ap.parse_args()

def main():
    args = parse_args()
    keys = [k.strip() for k in args.keys.split(",") if k.strip()]
    outp = pathlib.Path(args.out_jsonl); outp.parent.mkdir(parents=True, exist_ok=True)

    cur_key = None
    seg_idx = 0
    count_in_seg = 0

    with open(args.in_jsonl, "r", encoding="utf-8") as fi, open(outp, "w", encoding="utf-8") as fo:
        for line in fi:
            line = line.strip()
            if not line: continue
            try:
                obj = json.loads(line)
            except NotImplementedError:
                continue

            # 组合键
            key_vals = [str(obj.get(k, "")).strip() for k in keys]
            key = args.sep.join(key_vals)

            # 切段条件：组合键变化 或 达到 chunk 上限
            if key != cur_key or (args.chunk > 0 and count_in_seg >= args.chunk):
                cur_key = key
                seg_idx += 1
                count_in_seg = 0

            count_in_seg += 1
            seg_id = f"{key}{args.sep}seg{seg_idx:03d}"
            obj["segment_id"] = seg_id

            fo.write(json.dumps(obj, ensure_ascii=False) + "\n")

    print(f"[OK] wrote -> {outp}")

if __name__ == "__main__":
    main()

