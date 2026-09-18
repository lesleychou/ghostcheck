# portkey-gateway — Portkey-AI/gateway @ 669825cbe89ee51569918b8f78a9db486fd69dd4

## Purpose
A stateless HTTP proxy that takes an OpenAI-shaped request plus a routing config carried in the
request headers, and walks a recursive target tree (single / fallback / loadbalance / conditional)
until one (provider, model) returns a response (`src/handlers/handlerUtils.ts:476`,
`src/types/requestBody.ts:22`).

## Public interface
- Entry: `POST /v1/chat/completions` -> requestValidator -> chatCompletionsHandler
  (`src/index.ts:147`); same shape for the other endpoints (`src/index.ts:135`-`:220`).
- Request: OpenAI JSON body plus `x-portkey-config` (JSON config) or `x-portkey-provider`
  (`src/middlewares/requestValidator/index.ts:111`); one of the two is mandatory (`:116`). Other
  headers: retry-count, request-timeout, metadata, trace-id, cache, custom-host, virtual-key
  (`src/globals.ts:13`).
- Response: provider response passed through, plus `x-portkey-last-used-option-index`,
  `x-portkey-trace-id`, `x-portkey-retry-attempt-count`, `x-portkey-cache-status`,
  `x-portkey-provider` (`src/handlers/services/responseService.ts:99`, `src/globals.ts:30`).
- Config schema: `strategy.mode` in {single, loadbalance, fallback, conditional},
  `strategy.on_status_codes`, `strategy.conditions`/`default`, `provider`, `api_key`, `weight`,
  `retry{attempts, on_status_codes, use_retry_after_header}`, `cache{mode, max_age}`,
  `request_timeout`, recursive `targets`
  (`src/middlewares/requestValidator/schema/config.ts:14`, `:53`; parsed at
  `src/middlewares/requestValidator/index.ts:185`).

## Module map
| Path | Role |
|---|---|
| `src/index.ts` | the app and its middleware order (`:57`) |
| `src/middlewares/requestValidator/` | content-type, provider/config validation, SSRF host blocklist |
| `src/middlewares/hooks/` | per-request guardrail manager (`index.ts:551`) |
| `src/middlewares/cache/` | the optional process-global response cache (`index.ts:3`) |
| `src/middlewares/log/` | per-attempt log records, broadcast to websocket clients (`index.ts:112`) |
| `src/handlers/handlerUtils.ts` | the router: `tryTargetsRecursively` (`:476`), `tryPost` (`:288`) |
| `src/handlers/retryHandler.ts` | the retry loop and the per-attempt timeout (`:65`, `:4`) |
| `src/services/conditionalRouter.ts` | predicate evaluation over metadata, params and URL (`:44`) |
| `src/handlers/services/` | config resolution, provider context, cache, hooks, budget seam, response headers, logs |
| `src/shared/services/cache/utils/rateLimiter.ts` | a Redis rate limiter that **no file imports** (`:84`) |

## Execution spine of ONE request
1. Route to the handler (`src/index.ts:147`), then the validator: content-type gate
   (`src/middlewares/requestValidator/index.ts:88`), config/provider header gate (`:111`), schema
   parse (`:185`).
2. A fresh guardrail manager is created per request (`src/middlewares/hooks/index.ts:551`).
3. The handler parses the body, builds the config from headers and enters the recursion
   (`src/handlers/chatCompletionsHandler.ts:18`).
4. Inherited config is merged; retry and cache are inherited, `requestTimeout` is reset and then
   re-inherited (`src/handlers/handlerUtils.ts:491`, `:553`).
5. Targets flagged `isOpen` are dropped — **but nothing in this repository ever sets that flag**
   (`src/handlers/handlerUtils.ts:646`, filter at `:653`).
6. Switch on the strategy (`:662`):
   - fallback: targets in declaration order (`:664`), stopping when the status is outside
     `strategy.on_status_codes`, or (with no codes) on success, or when the response carries the
     gateway's own exception marker (`:676`).
   - loadbalance: missing weights default to 1 (`:694`), total is the raw sum with **no
     normalisation** (`:699`), then one draw `Math.random() * totalWeight` (`:704`) selects exactly
     one target (`:705`). No sibling is tried if it fails.
   - conditional: predicates over metadata, params and URL (`:728`, `src/services/conditionalRouter.ts:44`);
     any failure becomes a 400 (`:749`).
   - single: `targets[0]` (`:768`).
   - leaf: `tryPost` (`:783`), optionally a host-injected circuit-breaker callback (`:792`), and any
     thrown error becomes a 500 tagged `x-portkey-gateway-exception` (`:815`).
7. `tryPost` builds the contexts (`:297`), runs before-request guardrails, denying with 446 without
   calling the provider (`:320`), looks up the cache (`:372`), runs the host-injected budget seam
   (`:407`), then enters the retry loop (`:441`, `:1212`).
8. The retry loop makes one attempt (`src/handlers/retryHandler.ts:91`), retries when the status is
   in the configured set (`:103`), optionally honours a server `Retry-After` within a 60 s
   per-request budget (`:108`, `:129`, `src/globals.ts:5`), bails immediately on any other non-2xx
   (`:155`), and uses async-retry with **`randomize: false`** — no jitter (`:174`).
9. The response is transformed, after-request guardrails run, and a still-retriable result may
   recurse into a fresh provider call from the same budget (`src/handlers/handlerUtils.ts:1250`,
   `:1258`). Each abandoned attempt is logged as its own record (`:1266`); the reported attempt
   count becomes **-1** when the budget was exhausted (`:1284`).

## Build / config
`npm run dev:node` runs the server on port 8787; `conf.json` gates the plugins and the in-memory
cache (`"cache": false`, `conf.json:20`). Redis is used only by the unused shared cache backend
(`src/index.ts:49`).
