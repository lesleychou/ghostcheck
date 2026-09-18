"""no_mutation

THE PROPERTY (cards/properties.json). The router treats its inputs as read-only. It changes no
field of the Request copy it is handed and no key of the fleet_view dict or of the nested
per-provider dicts and lists inside it; its scratch state lives on itself.

THE PROBE, two legs, because one of them cannot see half the property:

  REPLAY leg. The fixture trace per tenant through TenantReplay at the scored outage schedule.
  The harness diffs the router-facing Request copy against its own record after every callback
  (replay_tenants.py :229 / :235 / :243), fingerprints the fleet config at start and end (:453),
  and cross-checks each provider's meter against its own ledger (:455), so a router that edits a
  request is reported with a typed `req_mutation`.

  UNIT leg, which the scored replay CANNOT catch. The fleet view is published BY VALUE, rebuilt
  from the provider's private config on every decide (replay_tenants.py:156), so a router that
  scribbles on it -- the realistic bug being local pacing by decrementing `rpm_left` / `tpm_left`,
  or popping a model out of `models` -- produces no harness violation at all: the scribble is
  simply thrown away. The test therefore calls `candidate.decide(req, now_ms, fleet_view)` on a
  fixture it built itself, holding a `copy.deepcopy` of both arguments taken BEFORE the call, and
  compares by value after the call. The case table is seeded and covers healthy fleets, a `prime`
  in its announced outage (empty catalogue, `outage_until` published), and downgrade_ok=False
  requests, drawn from both tenants' fixture rows.

THE ORACLE:
  * replay leg, from the harness's books only: `violation_kinds` contains none of `req_mutation`,
    `env_mutation`, `meter_mutation`, `bad_bill` or `router_exception`, and `violation_count == 0`;
  * unit leg, checked by the test's own deepcopy: after decide() returns, the fleet_view equals
    its pre-call copy recursively -- every provider's `models`, `rpm_left`, `tpm_left`,
    `inflight`, `error_rate` -- and every field of the Request equals its pre-call copy, in
    particular `equiv_class` the same list contents and `quality` / `features` the same dict
    contents.

The `has_prefix` entry is excluded from the fleet-view comparison: the harness publishes a fresh
closure on every call, so it is not data and an identity change there is not a mutation. Nothing
here asserts WHICH action the router returns; a defer, a dispatch and a shed are all fine.
"""

import copy
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _support as S

FORBIDDEN = ("req_mutation", "env_mutation", "meter_mutation", "bad_bill", "router_exception")
REQ_FIELDS = tuple(S.Request.__dataclass_fields__)


def view_difference(before, after):
    before, after = S.strip_callables(before), S.strip_callables(after)
    for name in sorted(set(before) | set(after)):
        if name not in before:
            return "the router ADDED provider %r to the fleet view" % (name,)
        if name not in after:
            return "the router REMOVED provider %r from the fleet view" % (name,)
        lhs, rhs = before[name], after[name]
        for key in sorted(set(lhs) | set(rhs)):
            if key not in lhs:
                return "the router added %s[%r] to the fleet view" % (name, key)
            if key not in rhs:
                return "the router removed %s[%r] from the fleet view" % (name, key)
            if lhs[key] != rhs[key]:
                return "%s[%r]: %r before decide(), %r after" % (name, key, lhs[key], rhs[key])
    return None


def request_difference(before, after):
    for field in REQ_FIELDS:
        lhs, rhs = getattr(before, field, None), getattr(after, field, None)
        if lhs != rhs:
            return "req.%s: %r before decide(), %r after" % (field, lhs, rhs)
    return None


def replay_leg(classes):
    for tenant in S.TENANTS:
        books = S.replay(S.FIXTURE[tenant], S.fresh(tenant, classes))
        kinds = books["violation_kinds"]
        hit = [k for k in FORBIDDEN if k in kinds]
        if hit:
            S.fail(
                "tenant %s: the harness reported %s over the fixture replay (%s); the router is "
                "editing what it was handed" % (tenant, ", ".join(hit), kinds)
            )
        if books["violation_count"] != 0:
            S.fail(
                "tenant %s: the fixture replay took %d typed violation(s) %s"
                % (tenant, books["violation_count"], kinds)
            )
        S.ok(
            "no_mutation tenant %s, replay leg: %d requests, %d decisions, no req_mutation / "
            "env_mutation / meter_mutation / bad_bill and no violation of any kind"
            % (tenant, books["requests"], books["decides"])
        )


def unit_leg(classes):
    table = S.case_table()
    for tenant in S.TENANTS:
        router = S.fresh(tenant, classes)
        for label, req, view, now_ms in table:
            req_before = copy.deepcopy(req)
            view_before = copy.deepcopy(view)
            router.decide(req, now_ms, view)
            diff = view_difference(view_before, view)
            if diff:
                S.fail(
                    "tenant %s, case %s: the router MUTATED the fleet view -- %s. The view is "
                    "published by value and rebuilt every call, so the scored replay would "
                    "never have shown this: the router is pacing against a number the fleet "
                    "does not have." % (tenant, label, diff)
                )
            diff = request_difference(req_before, req)
            if diff:
                S.fail(
                    "tenant %s, case %s: the router MUTATED the request it was handed -- %s"
                    % (tenant, label, diff)
                )
        S.ok(
            "no_mutation tenant %s, unit leg: %d seeded cases (healthy fleet, prime in its "
            "announced outage, downgrade_ok=False) left every fleet-view field and every "
            "request field byte-for-byte as handed in" % (tenant, len(table))
        )


def run():
    classes = S.candidate_classes()
    unit_leg(classes)
    replay_leg(classes)


if __name__ == "__main__":
    raise SystemExit(S.main(run))
