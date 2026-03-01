# Usage: python train_XLSTM.py --in data/with_segments.jsonl --label-map data/labels.csv --out trained_models/state_xlstm.pt
import argparse, json, pathlib, random, os
from typing import List, Dict, Any, Tuple

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

from fcd_config import FCD_NAMES, get_fcd_for_function

LEVELS = [f"Level_{i}" for i in range(1,6)]
CAT    = ['environment','secondary_task','lab','emotion']
NUM    = ['drowsiness_alert','gaze_distracted','heart_rate']

def set_seed(s: int):
    random.seed(s); np.random.seed(s); torch.manual_seed(s)
    if torch.cuda.is_available(): torch.cuda.manual_seed_all(s)

def as01(x: Any) -> float:
    s = str(x).strip().lower()
    if s in ('true','1','t','yes','y'): return 1.0
    if s in ('false','0','f','no','n','', 'nan','none','null'): return 0.0
    try: return float(s)
    except NotImplementedError: return 0.0

def read_jsonl(path: pathlib.Path) -> List[Dict[str, Any]]:
    rows=[]
    with path.open('r', encoding='utf-8') as f:
        for line in f:
            line=line.strip()
            if not line: continue
            try:
                obj=json.loads(line)
            except NotImplementedError:
                continue
            rows.append(obj)
    return rows

def normalize_row(row: Dict[str, Any]) -> Dict[str, Any]:
    def pick(*keys, default=""):
        for k in keys:
            if k in row and row[k] not in (None,""): return row[k]
        return default
    out={}
    out['segment_id']      = pick('segment_id','segment','trial_id','trial','block_id')
    out['functionname']    = pick('functionname','function','func_name','FunctionName')
    out['environment']     = pick('environment','env','environment_type')
    out['secondary_task']  = pick('secondary_task','sec_task','secondaryTask')
    out['lab']             = pick('lab','lab_state')
    out['emotion']         = pick('emotion','affect','emo','mood','Emotion')
    out['drowsiness_alert']= pick('drowsiness_alert','drowsy','fatigue')
    out['gaze_distracted'] = pick('gaze_distracted','gaze','distraction')
    out['heart_rate']      = pick('heart_rate','hr','heartrate','bpm')
    for k in LEVELS:
        if k in row and row[k] not in (None,""):
            out[k] = int(float(row[k]))
    return out

def load_label_map(path: str|None) -> Dict[str, List[int]]:
    if not path: return {}
    p = pathlib.Path(path)
    if not p.exists(): return {}
    df = pd.read_csv(p)
    miss = [k for k in (["segment_id"]+LEVELS) if k not in df.columns]
    if miss:
        raise ValueError(f"--label-map missing columns: {miss}; required: ['segment_id'] + Level_1..Level_5")
    m={}
    for _,r in df.iterrows():
        sid = str(r['segment_id']).strip()
        if not sid: continue
        vec = [int(float(r[k])) for k in LEVELS]
        vec = [1 if v>=1 else 0 for v in vec]
        m[sid]=vec
    return m

def encode_frame(sr: pd.Series) -> np.ndarray:
    fcd = get_fcd_for_function(sr.get('functionname') or "")
    fcd_vec = [float(fcd[k]) for k in FCD_NAMES]
    num = [as01(sr.get(k)) for k in NUM]
    catv=[]
    for k in CAT:
        c = str(sr.get(k, "") or "")
        catv.extend([0.0 if c=="" else 1.0, min(len(c)/16.0, 1.0)])
    return np.asarray([*fcd_vec, *num, *catv], dtype=np.float32)

class SeqDataset(Dataset):
    def __init__(self, df: pd.DataFrame, max_len: int = 512):
        assert 'segment_id' in df.columns and df['segment_id'].astype(bool).any(), "segment_id is required"
        self.max_len = max_len
        self.groups: List[Tuple[np.ndarray, np.ndarray]] = []
        for gid, g in df.groupby('segment_id'):
            g = g.reset_index(drop=True)
            if not all(k in g.columns for k in LEVELS):
                continue
            y = g[LEVELS].iloc[0].astype(float).values
            xs = [encode_frame(g.iloc[i]) for i in range(len(g))]
            X = np.stack(xs, axis=0).astype(np.float32)
            self.groups.append((X, y.astype(np.float32)))

    def __len__(self): return len(self.groups)
    def __getitem__(self, i): return self.groups[i]

def collate(batch):
    if len(batch)==0:
        return torch.empty(0,1,23), torch.empty(0,5), torch.empty(0,dtype=torch.long)
    maxlen = min(max(x[0].shape[0] for x in batch), 512)
    xs, ys, ls=[],[],[]
    for X,y in batch:
        T = X.shape[0]
        if T>maxlen: X = X[-maxlen:]
        pad = maxlen - X.shape[0]
        if pad>0:
            X = np.concatenate([np.zeros((pad, X.shape[1]), dtype=X.dtype), X], axis=0)
        xs.append(torch.from_numpy(X)); ys.append(torch.from_numpy(y)); ls.append(min(T,maxlen))
    return torch.stack(xs,0), torch.stack(ys,0), torch.tensor(ls,dtype=torch.long)

class _xLSTMBlock(nn.Module):
    def __init__(self, d_in, d_hid, dropout=0.1):
        super().__init__()
        self.d_in = d_in
        self.d_hid = d_hid
        self.in_norm = nn.LayerNorm(d_in)
        self.h_norm  = nn.LayerNorm(d_hid)
        self.x2cand = nn.Linear(d_in, d_hid, bias=True)
        self.h2cand = nn.Linear(d_hid, d_hid, bias=False)
        self.x2gate = nn.Linear(d_in, 3*d_hid, bias=True)
        self.h2gate = nn.Linear(d_hid, 3*d_hid, bias=False)
        self.dropout = nn.Dropout(dropout)
        for m in [self.h2cand, self.h2gate]:
            nn.init.orthogonal_(m.weight, gain=1.0)

    @staticmethod
    def _exp_gate(z):
        return torch.exp(z.clamp(min=-5.0, max=5.0))

    def forward(self, x, lengths):
        B, T, _ = x.size()
        device = x.device
        h = torch.zeros(B, self.d_hid, device=device)
        c = torch.zeros(B, self.d_hid, device=device)
        outputs = []
        arange_t = torch.arange(T, device=device).unsqueeze(0).expand(B, T)
        valid_mask = arange_t < lengths.unsqueeze(1)
        for t in range(T):
            xt = self.in_norm(x[:, t, :])
            ht = self.h_norm(h)
            g_t = torch.tanh(self.x2cand(xt) + self.h2cand(ht))
            gate_x = self.x2gate(xt)
            gate_h = self.h2gate(ht)
            gi, gf, go = torch.chunk(gate_x + gate_h, chunks=3, dim=-1)
            i_hat = self._exp_gate(gi)
            f_hat = self._exp_gate(gf)
            denom = (i_hat + f_hat + 1e-6)
            alpha = i_hat / denom
            beta  = f_hat / denom
            c_new = beta * c + alpha * g_t
            o = torch.sigmoid(go)
            h_new = o * torch.tanh(c_new)
            mask_t = valid_mask[:, t].unsqueeze(1)
            h = torch.where(mask_t, h_new, h)
            c = torch.where(mask_t, c_new, c)
            outputs.append(torch.where(mask_t, h_new, torch.zeros_like(h_new)))
        H = torch.stack(outputs, dim=1)
        H = self.dropout(H)
        return H

class XLSTM(nn.Module):
    def __init__(self, d_in=23, d_hid=128, n_layers=2, dropout=0.1):
        super().__init__()
        self.fwd = _xLSTMBlock(d_in, d_hid, dropout)
        self.bwd = _xLSTMBlock(d_in, d_hid, dropout)
        self.proj = nn.Sequential(nn.Linear(2*d_hid, d_hid), nn.ReLU(), nn.Dropout(dropout))
        self.head = nn.Linear(d_hid, 5)
    def forward(self, x, lengths):
        B, T, _ = x.size()
        T_eff = int(lengths.max().item())
        x_eff = x[:, -T_eff:, :]
        h_f = self.fwd(x_eff, lengths)
        x_rev = torch.flip(x_eff, dims=[1])
        h_b = self.bwd(x_rev, lengths)
        idx = (lengths - 1).clamp_min(0)
        h_last_f = h_f[torch.arange(B, device=x.device), idx]
        h_last_b = h_b[torch.arange(B, device=x.device), idx]
        h_cat = torch.cat([h_last_f, h_last_b], dim=-1)
        h = self.proj(h_cat)
        return self.head(h)

def micro_f1(y_true: np.ndarray, y_prob: np.ndarray, thr: float = 0.5) -> float:
    yt = (y_true>0.5).astype(int); yp=(y_prob>=thr).astype(int)
    inter=(yt&yp).sum(); denom=yt.sum()+yp.sum()
    return float(2.0*inter / (denom+1e-9))

def main():
    ap = argparse.ArgumentParser(description="Train xLSTM (strict Level_* labels).")
    ap.add_argument("--in",        dest="in_jsonl", required=True)
    ap.add_argument("--out",       dest="out_pt",   default="trained_models/state_xlstm.pt")
    ap.add_argument("--label-map", dest="label_map", default=None, help="CSV with columns: segment_id, Level_1..Level_5")
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--batch",  type=int, default=16)
    ap.add_argument("--seed",   type=int, default=42)
    ap.add_argument("--lr",     type=float, default=2e-3)
    ap.add_argument("--weight_decay", type=float, default=1e-4)
    ap.add_argument("--max_len", type=int, default=512)
    args = ap.parse_args()

    set_seed(args.seed)
    device = "cuda" if torch.cuda.is_available() else "cpu"

    rows = [normalize_row(r) for r in read_jsonl(pathlib.Path(args.in_jsonl))]
    if not rows:
        raise ValueError("JSONL is empty or contains no valid rows.")
    df = pd.DataFrame(rows)

    if args.label_map:
        lm = pd.read_csv(args.label_map)
        miss = [k for k in (["segment_id"]+LEVELS) if k not in lm.columns]
        if miss:
            raise ValueError(f"--label-map missing columns: {miss}")
        df = df.merge(lm, on="segment_id", how="left", suffixes=("", "_map"))
        for k in LEVELS:
            if k not in df.columns or df[k].isna().all():
                df[k] = df.get(k+"_map")
            df[k] = df[k].fillna(0).astype(int)
            if k+"_map" in df.columns: df.drop(columns=[k+"_map"], inplace=True)

    if 'segment_id' not in df.columns or df['segment_id'].eq("").all():
        raise ValueError("Missing segment_id; cannot build sequences.")
    for k in CAT:
        if k not in df.columns: df[k] = ""
        df[k] = df[k].fillna("").astype(str)
    for k in NUM:
        if k not in df.columns: df[k] = 0.0
        df[k] = df[k].apply(as01)

    gids = df['segment_id'].drop_duplicates().sample(frac=1.0, random_state=args.seed).values
    ntr = max(1, int(0.8*len(gids)))
    tr_ids, te_ids = set(gids[:ntr]), set(gids[ntr:])
    tr_df = df[df['segment_id'].isin(tr_ids)].reset_index(drop=True)
    te_df = df[df['segment_id'].isin(te_ids)].reset_index(drop=True)

    train_ds = SeqDataset(tr_df, max_len=args.max_len)
    test_ds  = SeqDataset(te_df, max_len=args.max_len)
    if len(train_ds)==0 or len(test_ds)==0:
        raise ValueError(f"Insufficient segments: train={len(train_ds)}, val={len(test_ds)}. Ensure Level_* labels exist.")
    train_dl = DataLoader(train_ds, batch_size=args.batch, shuffle=True,  collate_fn=collate)
    test_dl  = DataLoader(test_ds,  batch_size=max(8,args.batch), shuffle=False, collate_fn=collate)

    d_in = 12 + len(NUM) + 2*len(CAT)
    model = XLSTM(d_in=d_in).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    loss_fn = nn.BCEWithLogitsLoss()

    best = 0.0
    outp = pathlib.Path(args.out_pt); outp.parent.mkdir(parents=True, exist_ok=True)

    for ep in range(args.epochs):
        model.train()
        for xb,yb,lb in train_dl:
            xb,yb,lb = xb.to(device), yb.to(device), lb.to(device)
            logits = model(xb,lb)
            loss = loss_fn(logits, yb)
            opt.zero_grad(); loss.backward(); opt.step()

        model.eval(); y_true=[]; y_prob=[]
        with torch.no_grad():
            for xb,yb,lb in test_dl:
                xb,yb,lb = xb.to(device), yb.to(device), lb.to(device)
                prob = torch.sigmoid(model(xb,lb))
                y_true.append(yb.cpu().numpy()); y_prob.append(prob.cpu().numpy())
        Yt = np.concatenate(y_true,0); Yp = np.concatenate(y_prob,0)
        mf1 = micro_f1(Yt, Yp, 0.5)
        print(f"[epoch {ep:02d}] micro-F1={mf1:.3f} (val_n={len(Yt)})")

        if mf1 > best:
            best = mf1
            torch.save({"model": model.state_dict(), "d_in": d_in}, outp)
            print(f"[OK] saved -> {outp}")

    print(f"[BEST] micro-F1={best:.3f}")

if __name__ == "__main__":
    main()
