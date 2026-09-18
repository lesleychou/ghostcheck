"""Checks that read the books after a replay, plus the offline fitting step the data
protocol constrains. Nothing here asks the router anything."""


def audit_reasons(run, fleet, requests):
    """Every dispatch must carry a record that names the target actually used, and a claimed
    rule that the fleet's own price table agrees with. A reason nobody checks is decoration."""
    by_rid = {r.rid: r for r in requests}
    complaints = []
    for rid, provider, model, reason in run.reason_log:
        if not isinstance(reason, dict) or not reason:
            complaints.append(f"{rid}: dispatch carried no decision record")
            continue
        if reason.get("provider") != provider or reason.get("model") != model:
            complaints.append(
                f"{rid}: record says {reason.get('provider')}/{reason.get('model')} "
                f"but the request went to {provider}/{model}"
            )
            continue
        if reason.get("rule") == "cheapest":
            p = fleet.providers[provider]
            legal = [m for m in by_rid[rid].equiv_class if p.stocks(m)]
            floor = min(p.prices[m] for m in legal)
            if p.prices[model] > floor:
                complaints.append(
                    f"{rid}: record claims the cheapest choice but {model} costs "
                    f"{p.prices[model]} where {floor} was available on {provider}"
                )
    return complaints


def fit_best_model(rows, allowed_prompt_ids):
    """The honest fit: a per-prompt best model learned from the rows of the training split
    only. `rows` is (prompt_id, model, score)."""
    allowed = set(allowed_prompt_ids)
    best = {}
    for prompt_id, model, score in rows:
        if prompt_id not in allowed:
            continue
        if prompt_id not in best or score > best[prompt_id][1]:
            best[prompt_id] = (model, score)
    return {k: v[0] for k, v in best.items()}


def fit_best_model_leaky(rows, allowed_prompt_ids):
    """The mutant fit: the same code with the split boundary removed."""
    best = {}
    for prompt_id, model, score in rows:
        if prompt_id not in best or score > best[prompt_id][1]:
            best[prompt_id] = (model, score)
    return {k: v[0] for k, v in best.items()}


def artifact_leaks(table, held_out_prompt_ids):
    """Which held-out prompts the fitted artifact knows about. Must be empty."""
    return sorted(set(table) & set(held_out_prompt_ids))
