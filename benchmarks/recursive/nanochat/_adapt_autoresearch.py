#!/usr/bin/env python3
"""
Adapt autoresearch / leaderboard nanochat programs to (a) run on H100 and (b) be
importable by the GhostCheck harness — in one pass. Idempotent.

  1. ATTENTION -> SDPA. Replace the flash-attn setup block (FA3 via the `kernels`
     package, OR the FA4 `flash_attn.cute` custom-op block) with a single SDPA shim
     that exposes BOTH `flash_attn_func(q,k,v,causal,window_size)` and
     `fa3.flash_attn_func(...)`, so it works no matter which the program calls.
     This removes the `kernels` trust/version gates and the FA4 (Blackwell-only) dep.

  2. IMPORT-SAFE. Guard the train tail (`t_start = time.time()` .. EOF) behind
     `if __name__ == "__main__" or os.environ.get("GHOSTCHECK_RUN") == "1"`, so the
     harness can import the module (defs only) without training; `python file.py`
     (or GHOSTCHECK_RUN=1 subprocess) still trains.

Usage:
  python _adapt_autoresearch.py best/initial_autoresearch.py leaderboard/programs/rank*.py
"""
import sys

SDPA = '''# --- SDPA attention shim (auto-inserted by _adapt_autoresearch.py) ---
#     Replaces flash-attn-3/`kernels` (moving trust+version gates) and flash-attn-4
#     (Blackwell-only). Same causal + sliding-window math, GQA-aware. Exposes BOTH
#     `flash_attn_func(...)` and `fa3.flash_attn_func(...)`. Layout (B,T,H,D)<->(B,H,T,D).
import torch.nn.functional as _F_sdpa

cap = torch.cuda.get_device_capability()  # kept: some programs read it elsewhere


def flash_attn_func(q, k, v, causal=True, window_size=(-1, -1)):
    q, k, v = q.transpose(1, 2), k.transpose(1, 2), v.transpose(1, 2)
    h_q, h_kv = q.shape[1], k.shape[1]
    if h_kv != h_q:  # GQA: expand kv heads to match query heads
        r = h_q // h_kv
        k = k.repeat_interleave(r, dim=1)
        v = v.repeat_interleave(r, dim=1)
    q, k = q.to(v.dtype), k.to(v.dtype)
    wl = window_size[0] if isinstance(window_size, tuple) else window_size
    seq = q.shape[-2]
    if wl is None or wl <= 0 or wl >= seq:  # full causal
        o = _F_sdpa.scaled_dot_product_attention(q, k, v, is_causal=causal)
    else:  # sliding window of width wl: key j in [i - wl, i]
        idx = torch.arange(seq, device=q.device)
        m = (idx[None, :] <= idx[:, None]) & (idx[None, :] >= idx[:, None] - wl)
        o = _F_sdpa.scaled_dot_product_attention(q, k, v, attn_mask=m)
    return o.transpose(1, 2)


class _SDPAShim:
    flash_attn_func = staticmethod(flash_attn_func)


fa3 = _SDPAShim()'''

GUARD = 'if __name__ == "__main__" or os.environ.get("GHOSTCHECK_RUN") == "1":'


BOOTSTRAP = '''# --- path bootstrap (auto-inserted): add the dir holding prepare.py + lib.py to
#     sys.path so `from prepare import ...` works from any cwd, no PYTHONPATH needed.
import os as _os, sys as _sys
_h = _os.path.dirname(_os.path.abspath(__file__))
while _h != _os.path.dirname(_h):
    if _os.path.exists(_os.path.join(_h, "prepare.py")) and _os.path.exists(_os.path.join(_h, "lib.py")):
        if _h not in _sys.path:
            _sys.path.insert(0, _h)
        break
    _h = _os.path.dirname(_h)
# --- end path bootstrap ---'''


def adapt(src: str):
    lines = src.splitlines()
    changed = False

    # ---- 0. path bootstrap (so the harness import resolves without PYTHONPATH) -
    if "_os.path.join(_h, \"prepare.py\")" not in src:
        oi = next((i for i, l in enumerate(lines) if l.strip() == "import os"), None)
        if oi is not None:
            lines = lines[:oi + 1] + [""] + BOOTSTRAP.splitlines() + lines[oi + 1:]
            changed = True

    # ---- 1. attention -> SDPA -------------------------------------------------
    if not any("_SDPAShim" in l for l in lines):
        # end of the attention block = first harness import line
        end = next((i for i, l in enumerate(lines)
                    if l.startswith("from prepare import") or l.startswith("from lib import")), None)
        if end is None:
            raise SystemExit("no `from prepare/lib import` line found")
        # start = earliest flash-attn setup marker before `end`
        cands = [i for i, l in enumerate(lines[:end])
                 if l.startswith("from kernels import")
                 or l.startswith("cap = torch.cuda.get_device_capability()")
                 or l.startswith("from flash_attn") or l.startswith("import flash_attn")]
        if not cands:
            raise SystemExit("no attention-setup block found before harness import")
        start = min(cands)
        lines = lines[:start] + SDPA.splitlines() + lines[end:]
        changed = True

    # ---- 2. import-safe: guard the train tail --------------------------------
    if not any(l.startswith(GUARD) for l in lines):
        ts = next((i for i, l in enumerate(lines) if l.startswith("t_start = time.time()")), None)
        if ts is None:
            raise SystemExit("no `t_start = time.time()` marker found for the train tail")
        tail = lines[ts:]
        # indenting a MULTI-line triple-quoted string would corrupt it; a line that
        # opens/closes one has an ODD count of that quote. Single-line docstrings are fine.
        for q in ('"""', "'''"):
            for l in tail:
                if l.count(q) % 2 == 1:
                    raise SystemExit(f"tail has a multiline {q} string; manual fix needed: {l!r}")
        indented = ["    " + l if l.strip() else "" for l in tail]
        lines = lines[:ts] + [GUARD] + indented
        changed = True

    return "\n".join(lines) + "\n" if changed else None


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: python _adapt_autoresearch.py <file.py> [<file.py> ...]")
    for path in sys.argv[1:]:
        try:
            out = adapt(open(path).read())
        except SystemExit as e:
            print(f"SKIP  {path}  ({e})"); continue
        if out is None:
            print(f"ok    {path}  (already adapted)"); continue
        compile(out, path, "exec")  # fail loudly on a broken transform
        open(path, "w").write(out)
        print(f"ADAPT {path}")
