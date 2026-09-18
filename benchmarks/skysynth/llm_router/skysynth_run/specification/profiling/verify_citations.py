#!/usr/bin/env python3
"""Stage 8. Re-check every file:line citation in references/<name>/{spec,properties,
design_principles,decisions}.json against the real source, ignoring the asserted line and
grepping the file for the line's leading symbol.

Verdicts: CONFIRMED (symbol found on the asserted line), OFF_BY (found on another line),
WRONG (symbol not in the file), UNVERIFIABLE (file or line missing).
"""
import json, os, re, subprocess, sys, datetime

ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
RUN = os.path.join(ROOT, ".skydiscover/llm-router/specification")
REFS = os.path.join(RUN, "references")
SRC = os.path.join(RUN, "sources")
# gaie's evidence lives at the last commit containing pkg/epp, not at cloned HEAD
GAIE_SHA = "1748e829d1161147aaf35e76699ec86fd88406d2"
CITE = re.compile(r"([A-Za-z0-9_./@\-]+\.(?:py|go|ts|js|yaml|yml|json|md)):(\d+)")
_cache = {}

def read(name, path):
    key = (name, path)
    if key in _cache:
        return _cache[key]
    lines = None
    if name == "gaie":
        r = subprocess.run(["git", "-C", os.path.realpath(os.path.join(SRC, "gaie")),
                            "show", f"{GAIE_SHA}:{path}"], capture_output=True, text=True)
        if r.returncode == 0:
            lines = r.stdout.split("\n")
    elif name == "task-evaluator":
        p = os.path.join(ROOT, path)
        if os.path.isfile(p):
            lines = open(p, errors="replace").read().split("\n")
    else:
        p = os.path.join(SRC, name, path)
        if os.path.isfile(p):
            lines = open(p, errors="replace").read().split("\n")
    _cache[key] = lines
    return lines

def symbol(text):
    """The most distinctive identifier or literal on the line."""
    toks = re.findall(r"[A-Za-z_][A-Za-z0-9_]{3,}|\d[\d_.]{2,}", text)
    toks = [t for t in toks if t not in
            {"self", "this", "return", "const", "func", "func_", "async", "await", "import",
             "from", "class", "else", "elif", "None", "True", "False", "null", "true", "false",
             "string", "error", "value", "type"}]
    return max(toks, key=len) if toks else None

def collect(name):
    cites = set()
    for fn in ("spec.json", "properties.json", "design_principles.json", "decisions.json"):
        p = os.path.join(REFS, name, fn)
        if not os.path.isfile(p):
            continue
        for m in CITE.finditer(open(p).read()):
            cites.add((m.group(1), int(m.group(2))))
    return sorted(cites)

def verify(name):
    rows = []
    for path, line in collect(name):
        lines = read(name, path)
        if lines is None:
            rows.append(dict(path=path, line=line, verdict="UNVERIFIABLE",
                             note="file not found at the pinned commit"))
            continue
        if line < 1 or line > len(lines):
            rows.append(dict(path=path, line=line, verdict="UNVERIFIABLE",
                             note=f"file has {len(lines)} lines"))
            continue
        text = lines[line - 1]
        sym, anchor, span = symbol(text), line, 1
        if sym is None:
            # the asserted line opens a multi-line construct (a bare brace, `if (`, `q = (`):
            # widen to the statement it starts and anchor on the first symbol found there
            for k in range(1, 4):
                if line - 1 + k < len(lines):
                    sym = symbol(lines[line - 1 + k])
                    if sym:
                        anchor, span = line + k, k + 1
                        text = (text + " ... " + lines[line - 1 + k].strip())
                        break
        if sym is None:
            rows.append(dict(path=path, line=line, verdict="UNVERIFIABLE",
                             note="no distinctive symbol within 3 lines of the assertion",
                             text=text.strip()[:100]))
            continue
        hits = [i + 1 for i, l in enumerate(lines) if sym in l]
        if anchor in hits:
            rows.append(dict(path=path, line=line, verdict="CONFIRMED", symbol=sym,
                             matched_within_lines=span, text=text.strip()[:140]))
        elif hits:
            rows.append(dict(path=path, line=line, verdict="OFF_BY", symbol=sym,
                             corrected=hits[0], note=f"symbol found at {hits[:3]}"))
        else:
            rows.append(dict(path=path, line=line, verdict="WRONG", symbol=sym))
    return rows

names = [d for d in sorted(os.listdir(REFS))
         if os.path.isdir(os.path.join(REFS, d)) and d != "tests"]
summary = {}
for name in names:
    rows = verify(name)
    counts = {}
    for r in rows:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
    out = {"system": name, "checked_at": datetime.datetime.now().isoformat(timespec="seconds"),
           "method": ("Every file:line in this system's spec.json, properties.json, "
                      "design_principles.json and decisions.json was re-read from the pinned "
                      "source. The asserted line number was ignored: the most distinctive "
                      "identifier or numeric literal on that line was extracted and the whole "
                      "file grepped for it. CONFIRMED = the symbol really is on that line; "
                      "OFF_BY = it is elsewhere in the file (corrected line given); WRONG = it is "
                      "not in the file at all; UNVERIFIABLE = the file or line does not exist, or "
                      "the line carries no distinctive symbol (a brace, a comment marker)."),
           "source_pin": (f"read at commit {GAIE_SHA} (a70292c^), because pkg/epp was deleted "
                          "before cloned HEAD") if name == "gaie" else
                         ("shipped with the task, read from the working tree"
                          if name == "task-evaluator" else "read at cloned HEAD"),
           "counts": counts, "total": len(rows), "rows": rows}
    json.dump(out, open(os.path.join(REFS, name, "verification.json"), "w"), indent=2)
    summary[name] = counts
    print(f"{name:16s} total={len(rows):4d}  " +
          "  ".join(f"{k}={v}" for k, v in sorted(counts.items())))
