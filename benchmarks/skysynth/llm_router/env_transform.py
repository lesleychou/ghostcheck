"""Pure transforms of SkySynth's frozen environment card.

TenantReplay reads the fleet and the outage schedule from a YAML file, so perturbing
capacity or outages means handing it a transformed copy. We never write to their card.

Only the `val` outage list is touched. The `test` split derives its windows from a
committed seed at replay time and task.md puts it out of bounds.
"""
import copy


def _scale_int(value, factor, floor=1):
    return max(floor, int(round(value * factor)))


def transform_env(env: dict, w: dict) -> dict:
    out = copy.deepcopy(env)

    rl = float(w.get("rate_limit_scale", 1.0))
    er = float(w.get("error_rate_scale", 1.0))
    if rl != 1.0 or er != 1.0:
        for cfg in out.get("providers", {}).values():
            if rl != 1.0:
                for key in ("rpm", "tpm", "concurrency"):
                    if key in cfg:
                        cfg[key] = _scale_int(cfg[key], rl)
            if er != 1.0 and "error_rate" in cfg:
                cfg["error_rate"] = min(1.0, max(0.0, cfg["error_rate"] * er))

    outages = out.get("outages") or {}
    windows = [list(win) for win in outages.get("val", [])]
    count = w.get("outage_count")
    dur = float(w.get("outage_duration_scale", 1.0))
    shift = int(w.get("outage_shift_ms", 0))
    if windows and (dur != 1.0 or shift):
        for win in windows:
            length = max(1, int(round((win[1] - win[0]) * dur)))
            start = max(0, win[0] + shift)
            win[0], win[1] = start, start + length
    if count is not None:
        windows = windows[: max(0, int(count))]
    if outages:
        outages["val"] = windows
        out["outages"] = outages
    return out
