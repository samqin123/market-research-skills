# Pricing table · 价格表

> 中文镜像：[pricing.zh.md](pricing.zh.md). English is canonical; edit here first.
>
> This file is the **only** price source used by `scripts/estimate.py`. If a model is missing,
> marked `unmetered`, or a rate is blank, the estimator MUST print **未计量 / unmetered** — it
> must never invent a price. Fill in your actual magpie contract rates before relying on the
> paid-channel estimate.

## Rules

1. **Free channels are ¥0 by definition.** The default working path is free-first; paid channels
   are opt-in only (`ALLOW_PAID=0` by default).
2. **Unknown = unmetered.** A missing row, `unmetered`, `?`, or a non-numeric rate all mean
   "未计量". Do not substitute a list price from memory.
3. **Currency is CNY per 1M tokens** (¥ / 1M tokens), matching the `.env` budget unit.
4. **Update the table, not the code.** `scripts/estimate.py` parses the fenced `csv` block below.
5. Paid usage still requires a **level-3 separate confirmation** even when the price is known.

## Machine-readable table

The estimator parses this fenced block. Keep the header and comma-separated columns intact.
`status` is one of `free`, `metered`, `unmetered`.

```csv
model_id,tier,input_cny_per_mtok,output_cny_per_mtok,status,notes
group/free-first,free,0,0,free,default free-first routing group
group/smart-split,free,0,0,free,free-first/smart-split routing group; paid escalation stays off unless ALLOW_PAID=1
auto/deepseek-v4.1-flash,free,0,0,free,free DeepSeek channel (verify availability on your gateway)
paid/heavy-review,paid,unmetered,unmetered,unmetered,optional heavy final-review model — fill your contract rate
paid/vision,paid,unmetered,unmetered,unmetered,optional paid vision/OCR model — fill your contract rate
```

## Human notes

- The model IDs above are the defaults documented in `.env.example`; the gateway's `/v1/models`
  endpoint is authoritative for what your machine actually exposes.
- A routing group may internally choose a paid model. Keep `ALLOW_PAID=0` unless you have
  explicitly approved paid escalation; if a group can escalate, treat it as a paid channel and
  apply the level-3 gate.
- Budget caps live in `.env` (`COST_MAX_PER_RUN_CNY`, `COST_MAX_MONTH_CNY`), not in this file.