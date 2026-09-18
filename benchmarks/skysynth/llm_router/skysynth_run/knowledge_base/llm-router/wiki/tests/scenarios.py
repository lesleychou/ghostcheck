"""The fleets and traces the tests replay. Small, fixed, and deterministic.

Three models stand in for the real fleet's twelve: `flagship` is dear and good, `mid` is the
middle, `cheap` is fast and weak. Three providers stand in for the real three, with different
prices, quotas, concurrency limits and speeds. Nothing here is random at run time.
"""

from sim import Fleet, Provider, Request, ground_truth

MODELS = ("cheap", "flagship", "mid")
BASE_SERVICE_MS = {"flagship": 1200, "mid": 800, "cheap": 400}


def fleet(outages=None, rpm=None, concurrency=None):
    rpm = rpm or {"value": 30, "prime": 12, "courier": 12}
    concurrency = concurrency or {"value": 8, "prime": 4, "courier": 4}
    outages = outages or {}
    return Fleet(
        providers={
            "courier": Provider(
                "courier",
                {"flagship": 0.020, "mid": 0.008, "cheap": 0.002},
                rpm["courier"],
                concurrency["courier"],
                speed=1.4,
                outages=tuple(outages.get("courier", ())),
            ),
            "prime": Provider(
                "prime",
                {"flagship": 0.030, "mid": 0.010, "cheap": 0.003},
                rpm["prime"],
                concurrency["prime"],
                speed=0.8,
                outages=tuple(outages.get("prime", ())),
            ),
            "value": Provider(
                "value",
                {"mid": 0.004, "cheap": 0.001},
                rpm["value"],
                concurrency["value"],
                speed=1.0,
                outages=tuple(outages.get("value", ())),
            ),
        },
        base_service_ms=dict(BASE_SERVICE_MS),
    )


def trace(n=20, tenant="A", model="flagship", every_ms=400, start_ms=0, deadline_ms=8000,
          first_rid=0, prompt_prefix="p", equiv=None):
    equiv = tuple(equiv) if equiv else MODELS
    return [
        Request(
            rid=first_rid + i,
            t_ms=start_ms + i * every_ms,
            tenant=tenant,
            model=model,
            equiv_class=equiv,
            deadline_ms=deadline_ms,
            prompt_id=f"{prompt_prefix}{i:03d}",
            features={"task": "qa", "difficulty_hint": round(0.01 * (i % 7), 3), "tenant": tenant},
        )
        for i in range(n)
    ]


def gt_for(requests, seed=7):
    return ground_truth(sorted({r.prompt_id for r in requests}), MODELS, seed=seed)


def relabel(requests, shift=10_000, prefix="q"):
    """The same trace with different request and prompt identifiers and identical features.
    A router that reads the request rather than the file produces identical decisions."""
    out = []
    for r in requests:
        out.append(
            Request(
                rid=r.rid + shift,
                t_ms=r.t_ms,
                tenant=r.tenant,
                model=r.model,
                equiv_class=r.equiv_class,
                deadline_ms=r.deadline_ms,
                prompt_id=prefix + r.prompt_id[1:],
                features=dict(r.features),
                retry_safe=r.retry_safe,
            )
        )
    return out


def decisions(run):
    """The dispatch sequence, identifier-free: what was served, in order, per position."""
    return [(p, m) for _rid, p, m in run.dispatch_log]
