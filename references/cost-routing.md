# Cost routing · 成本路由（shared by all four skills）

> 中文镜像：[cost-routing.zh.md](cost-routing.zh.md). English is canonical.

## One gateway, one policy

Every model call made **by a skill's scripts** goes through the local **magpie** gateway
(OpenAI-compatible `/v1/chat/completions`). No script embeds a provider URL, model name, or key;
all of them come from `.env` (see `.env.example`).

Policy, in order:

1. **Free first.** Default to `group/free-first` (or `group/smart-split` while paid escalation is
   off). Free channels cost ¥0.
2. **Paid only with a level-3 confirmation.** `ALLOW_PAID=0` by default. Even when `ALLOW_PAID=1`,
   a paid call needs its own line and its own confirmation (see `cost-gate.md`).
3. **Fail soft, never silently.** If the gateway is down, a model is missing, or a key is absent,
   the step logs one line, skips that step, and keeps converting/drafting. It must not fabricate
   the skipped output. A missing MinerU token is called out separately on the estimate card.
4. **Never print secrets.** Keys are read from `.env` / environment and never echoed, logged, or
   committed. Only variable names appear in docs and errors.

## Environment keys

| Key | Purpose | Default in `.env.example` |
|---|---|---|
| `MAGPIE_BASE_URL` | Gateway base, including `/v1` | `http://127.0.0.1:3425/v1` |
| `MAGPIE_API_KEY` | Optional local key; leave blank if the gateway is unauthenticated | *(blank)* |
| `MAGPIE_MODEL_FAST` | Summaries, tags, OCR | `group/free-first` |
| `MAGPIE_MODEL_MAIN` | Analysis, drafting, verification | `group/free-first` |
| `MAGPIE_MODEL_VISION` | Image OCR fallback | `group/free-first` |
| `MAGPIE_MODEL_HEAVY` | Optional heavy final review (paid tier only) | `paid/heavy-review` |
| `MAGPIE_TIMEOUT_SEC` | Per-call timeout | `90` |
| `ALLOW_PAID` | `0` = free only (default) | `0` |
| `COST_MAX_PER_RUN_CNY` | Per-run budget cap | `20` |
| `COST_MAX_MONTH_CNY` | Monthly budget cap | `200` |

`MAGPIE_API_KEY` is the only secret here. The existing `MINERU_TOKEN` follows the same rule:
present in the machine-local `skills/local-vault/scripts/.env`, never printed, never committed.

## Stage → tier map

| Skill / stage | Model tier | Why |
|---|---|---|
| `local-vault` frontmatter enrich (abstract / tags / synonyms / key_data) | **free small/fast** (`MAGPIE_MODEL_FAST`) | short structured extraction; a strong model adds cost without adding value |
| `local-vault` PPT image OCR | **free vision** (`MAGPIE_MODEL_VISION`) | transcription, not reasoning; fail-soft to an image reference |
| `local-vault` MinerU cloud OCR (scanned PDF / legacy Office / images) | **cloud upload**, not an LLM tier | needs a separate level-3 confirmation + token |
| `verifying` | **free main** (`MAGPIE_MODEL_MAIN`) | multi-source reading and synthesis; free-first is sufficient |
| `topic-brief` | **free main** | drafting + quoting from gathered material |
| `analyst-research` light / medium | **free main** | drafting and self-check |
| `analyst-research` heavy draft | **free main** | long-form drafting stays free |
| `analyst-research` heavy final review | free main by default; **paid strong model only if the user explicitly asks** | the single place where a stronger model can be justified; always level 3 |

**Rule of thumb:** summary / OCR / tagging → free small; analysis / drafting / verification →
free main; heavy final review → free main unless the user opts into a paid strong model. Never
start a paid call to "see if it helps".

## How skills express this

- `local-vault`: `scripts/magpie_client.py` wraps the gateway; `enrich_frontmatter()` and
  `ocr_image_via_magpie()` call it. On any failure they log and return `""` / `False`; the
  conversion still lands.
- `verifying` / `topic-brief` / `analyst-research`: the skill text says "route through magpie"
  at every point where a model is invoked. The AI reads `.env`-provided model IDs; it never
  hard-codes a vendor or a key.
- All skills run `scripts/estimate.py` before formal work and show the estimate card from
  `cost-gate.md`.

## Degradation ladder

1. Requested model unavailable → retry once with `MAGPIE_MODEL_FAST`.
2. Gateway unreachable → log one line, skip the optional step; continue all local converters.
3. Free route exhausted → **stop**; do not auto-escalate to paid. Report what remains and wait.
4. Paid route requested but not confirmed → continue on the free route, or skip the optional
   step; never spend silently.

## What "free" means here

A channel is free when its pricing row is `free` / `0` in `references/pricing.md`. A routing
group that can internally escalate to a paid model is **not** treated as free: keep
`ALLOW_PAID=0`, or count it as paid and apply the level-3 gate. Unknown price is printed as
**未计量 / unmetered**, never guessed.