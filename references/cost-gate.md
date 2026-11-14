# Cost gate · 消耗预估与三级确认闸口（shared protocol）

> 中文镜像：[cost-gate.zh.md](cost-gate.zh.md). English is canonical.
>
> Deterministic estimator: `scripts/estimate.py` (pure local; never calls a model).

## Why this exists

A skill must not start expensive or cloud-bound work just because it can. Before formal work,
produce an **estimate card**; match the card to a **gate level**; get the confirmation that level
requires. During work, stop if actual consumption runs past the estimate or the budget. At the
end, write one consumption line into the artifact.

## The card

### Level 1 — compact one-liner

For a **free-channel, single-shot** run in `light`, `verifying`, or `topic-brief`:

```text
[L1] verifying · free (group/free-first) · tokens ≈ 12k–15k in / 0.8k–2k out · 2–6 min · ¥0 · template: light-green · proceed? (one word)
```

A one-word yes ("go" / "好") is enough. Do not start before it.

### Levels 2 and 3 — full card

For `medium` / `heavy`, a **batch local-vault sync**, any **paid** channel, any **cloud upload**
(MinerU), or multi-model external calls:

```text
=== COST ESTIMATE / 预估卡 ===
Mode / 模式:            medium (analyst-research) · gate L2
Template / 模板:        light-green (default; classic-blue / warm-paper optional)
Input size / 输入体量:  ~15 sources, ~90k input tokens
Token range / token:    90k–105k input · 18k–28k output
Duration / 预计时长:    50–80 min
Channels / 通道:
  Free / 免费:          group/free-first — ¥0
  Paid / 付费:          off (ALLOW_PAID=0)
Cloud upload / 云端:    none
Estimated cost / 费用:  ¥0 (free only)
Budget / 预算:          per-run ¥20 · month ¥200 · month used ¥0
MinerU / 云端 OCR:      not needed
---
Confirm? (explicit yes / no)
```

For a **level 3** item, add a separate line that must be confirmed **on its own**:

```text
[L3 · separate confirmation] Paid channel: paid/heavy-review · est. ¥未计量 · NOT approved by default.
[L3 · separate confirmation] Cloud upload: MinerU · 3 files · token configured · NOT approved by default.
```

If the user does not confirm the level-3 line, **default to no**: continue on the free/local path,
or skip the optional step. Never treat a level-2 "yes" as approval for a level-3 item.

### MinerU line (mandatory when relevant)

If any file needs MinerU and `MINERU_TOKEN` is absent, the card must contain a separate warning:

```text
⚠️ MinerU / 云端 OCR: 需要 MINERU_TOKEN，当前未配置。
   请先到 https://mineru.net 控制台申请官方 API token，写入 skills/local-vault/scripts/.env；
   或明确确认跳过这些文件（它们会在报告末尾列明，不会被静默丢弃）。
```

A token that starts with `sk-` is a valid official API-key format. Never reject it because it is
not a JWT; only a successfully parsed JWT `exp` may produce an expiry reminder. Presence is
checked; the value is never printed.

## Gate levels

| Level | Trigger | What to show | Confirmation |
|---|---|---|---|
| **1** | Free channel **and** one-shot `light` / `verifying` / `topic-brief` | compact one-liner | one word |
| **2** | `medium` / `heavy`; batch `local-vault` sync; multi-file conversion | full card | explicit yes |
| **3** | **Any** paid channel; **any** cloud upload (MinerU); multi-model external calls | full card **plus** a separate level-3 line | separate explicit yes per item |

Rules:

- Multiple triggers → use the **highest** level.
- No confirmation → do not start. Level 1 waits for the one word; levels 2/3 wait for explicit yes.
- Level 3 default is **no**. "Not confirmed" means free/local path or skip, never silent spend.
- The template choice sits on the same screen as the card (`light-green` default; choosing nothing
  does not block).
- `estimate.py` models this: without `--confirmed` it prints the card and exits **10** (awaiting
  confirmation). `--confirmed` exits 0. Use `--level` to preview, but the script computes the
  level from the actual flags.

## Deterministic estimate (`scripts/estimate.py`)

```bash
# Level-1 card, awaiting confirmation
python3 scripts/estimate.py --mode verifying --sources 5

# Full card for medium, confirmed
python3 scripts/estimate.py --mode medium --sources 15 --confirmed

# Batch local-vault with a cloud fallback and no token
python3 scripts/estimate.py --mode local-vault --files 12 --cloud-upload mineru

# Overrun guard after a run (exit 3 = STOP)
python3 scripts/estimate.py --mode heavy --actual-total-tokens 210000 --actual-cost 32

# Record actual consumption for the monthly cap
python3 scripts/estimate.py --mode light --record --actual-total-tokens 12000 --actual-cost 0
```

The estimator:

- estimates input/output token ranges from mode, sources, files, pages and optional
  `--input-chars` (deterministic formulas documented in the script);
- reads prices **only** from `references/pricing.md`; unknown → `未计量 / unmetered`;
- reads `.env` for `ALLOW_PAID`, `MAGPIE_*` model IDs and budget caps (never prints secrets);
- checks `MINERU_TOKEN` presence only, and prints the application entry when missing;
- reads a local ledger (`MRS_COST_LEDGER`, default `.cost-ledger.jsonl`, git-ignored) for the
  month-to-date total;
- exits **10** when confirmation is still required, **3** when the guard trips, **0** otherwise.

## Overrun guard during execution

Stop immediately and report when **either**:

1. actual consumption exceeds the **high end of the estimate by 50%**, or
2. the per-run cap (`COST_MAX_PER_RUN_CNY`, default ¥20) or the month-to-date cap
   (`COST_MAX_MONTH_CNY`, default ¥200) is reached.

The stop message must state: what was consumed (tokens / channel / cost or unmetered), what work
remains, and what confirmation is needed to continue. Do not silently continue, and do not
auto-downgrade a paid run into a different paid run.

If the price is unmetered, compare **tokens** against the estimate high end and say the cost is
unmetered. Never invent a yuan figure to make the guard look satisfied.

## End-of-run consumption line

Append one line to the artifact (HTML comment for HTML, a final line for Markdown):

```text
<!-- cost: mode=medium tokens=96k_in/24k_out channel=group/free-first cost=¥0 estimate=90k–105k/18k–28k -->
```

For Markdown:

```text
---
Cost: medium · 96k in / 24k out · group/free-first · ¥0 · estimate 90k–105k / 18k–28k
```

If unmetered: `cost=未计量 (unmetered)`. If the run stopped early: add `stopped=overrun`.

## Budget keys

```dotenv
ALLOW_PAID=0
COST_MAX_PER_RUN_CNY=20
COST_MAX_MONTH_CNY=200
MRS_COST_LEDGER=.cost-ledger.jsonl
```

Changing a default requires the user's explicit instruction; record the change in the project
notes, not by silently editing the estimator.