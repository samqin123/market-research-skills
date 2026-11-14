# ADAPT-REPORT — market-research-skills fork adaptation

- **Date**: 2026-11-14
- **Repo**: `~/dev/market-research-skills-xb`
- **Branch**: `adapt/v2`
- **Version**: 2.0.0 (upstream base v1.7.1)
- **Status**: local checkpoint only — **no GitHub repo created, no push, no Release**.
- **Shell smoke**: `git status` and normal shell commands worked; no `SANDBOX_UNAVAILABLE`.

---

## 1. Repository-name / fork check (gh)

`gh auth status` is logged in as `samqin123`.

| Check | Result |
|---|---|
| `samqin123/market-research-skills` | **404 — no same-name repo** |
| `xyb-openharness-dsh-plugins/market-research-skills` | **404 — no same-name repo** |
| `gh search repos market-research-skills --owner samqin123` | `[]` |
| `gh search repos market-research-skills --owner xyb-openharness-dsh-plugins` | `[]` |
| Upstream forks (`genli-ai/market-research-skills/forks`, 7 forks) | none under `samqin123` or `xyb-openharness-dsh-plugins` |

**Conclusion**: no collision. No rename/avoidance was needed; nothing was overwritten. The local repo name
`market-research-skills-xb` is only a working-directory suffix.

---

## 2. What changed (file-level)

### New files

| File | Purpose |
|---|---|
| `references/cost-routing.md` / `.zh.md` | stage → free/paid model tier; magpie env keys; degradation ladder |
| `references/cost-gate.md` / `.zh.md` | three-level estimate/confirmation gate, card formats, overrun guard, end line |
| `references/pricing.md` / `.zh.md` | the only price source; unknown = `未计量`; free rows ¥0 |
| `scripts/estimate.py` | deterministic estimator / gate (never calls a model; exit 10/3/0) |
| `skills/local-vault/scripts/magpie_client.py` | OpenAI-compatible magpie client (stdlib), text + vision |
| `templates/README.md` | template registry + taste decision (genes, rationale, previews) |
| `templates/{classic-blue,light-green,warm-paper}/tokens.css` | CSS variable blocks |
| `templates/{...}/briefing.html` | topic-brief layouts (inline styles, WeChat-paste friendly) |
| `templates/{...}/analyst.css`, `analyst.html` | analyst-research Quarto/publication derived styles + sample |
| `templates/preview/{classic-blue,light-green,warm-paper}.html` | same sample content, three templates |
| `templates/preview/sample.json`, `render_previews.py` | shared preview content + renderer |
| `.env.example` | root magpie/budget/MinerU placeholders (no real key) |
| `smoke/*` | acceptance evidence (grep, cards, smoke logs, checks) |
| `ADAPT-REPORT.md` | this report |

### Modified files (highlights)

| File | Change |
|---|---|
| `skills/verifying/SKILL.md`, `SKILL.zh.md`, `README.md` | deleted block gate; added multi-source side-by-side rule; red-line references updated |
| `skills/topic-brief/SKILL.md`, `SKILL.zh.md`, `lib/schema.py`, `prompts/system.md` | deleted block gate; blank default byline; template question; cost card; multi-source rule |
| `skills/topic-brief/lib/renderer.py`, `scripts/render.py` | shared-template resolution, `--template` (default `light-green`), blank-author cell, optional cost line |
| `skills/analyst-research/SKILL.md`, `SKILL.zh.md`, `MODE_REGISTRY*.md`, three workflow pairs, `report_style_spec*.md` | all model-call wording → “through magpie”; multi-LLM → magpie multi-model; onboarding cost cards; template selection |
| `skills/local-vault/SKILL.md`, `SKILL.zh.md` | setup → magpie; bilingual MinerU reminder; cloud gate; blank-byline note |
| `skills/local-vault/scripts/config.py` | `MAGPIE_*`, budget, confirm flags; removed `ENRICH_CLAUDE_CMD`; token/OCR knobs |
| `skills/local-vault/scripts/sync.py` | all `claude -p` calls → magpie; `sk-` token compatibility; bilingual wizard; `.env` merge; L2 batch card; L3 MinerU gate; explicit skipped list |
| `skills/local-vault/scripts/.env.example` | magpie/budget/MinerU keys; `sk-` note |
| `scripts/pack.sh` | **security fix**: exclude `.env`, `logs/`, `*.log` from zips (token never ships) |
| `.claude-plugin/plugin.json`, `marketplace.json` | version 2.0.0 |
| `README.md`, `CHANGELOG.md`, `.gitignore` | fork section, 2.0.0 entry, cost ledger/log ignores |
| `docs/2026-05-26-design.md` | old deferred-scope heading → “Deferred (V1)” |

**Structure preserved**: four skills (`verifying` / `topic-brief` / `analyst-research` / `local-vault`),
plugin + marketplace manifests, `pack.sh`, English canonical + `.zh.md` mirrors, all workflows,
whisper local transcription, MinerU fallback (now opt-in cloud), topic-brief 5 steps, verifying 5 scenarios.

---

## 3. Cost routing and gate

- All script-side model calls go through `MAGPIE_BASE_URL` (OpenAI-compatible `/v1/chat/completions`);
  model IDs are `MAGPIE_MODEL_FAST` / `_MAIN` / `_VISION` / `_HEAVY`. No key is hard-coded or printed.
- Default free route: `group/free-first`; `ALLOW_PAID=0`; budget `COST_MAX_PER_RUN_CNY=20`,
  `COST_MAX_MONTH_CNY=200` (defaults, changeable in `.env`).
- Gate levels: L1 free one-shot `light`/`verifying`/`topic-brief` (one-word); L2 `medium`/`heavy`/batch
  local-vault (explicit yes); L3 any paid, any cloud upload (MinerU), multi-model external calls
  (separate line + separate yes).
- Guard: actual > 150% of estimate high, or per-run/month cap → stop and report. `estimate.py`
  exits 3 on the guard; 10 when confirmation is missing.
- End line: `<!-- cost: ... -->` or a final Markdown line.

### Card samples (full output in `smoke/estimate-cards.txt`)

```text
[L1] light · free (group/free-first) · tokens ≈ 30k–35k in · 7k–11k out · 15–25 min · ¥0 · template: light-green · proceed? (one word)
```

```text
=== COST ESTIMATE / 预估卡 ===
Mode / 模式:            medium · gate L2
Template / 模板:        light-green (default; classic-blue / warm-paper optional)
Token range / token:    82k–94k in · 18k–28k out
Duration / 预计时长:    50–80 min
Channels / 通道:
  Free / 免费:          group/free-first — ¥0
  Paid / 付费:          off (ALLOW_PAID=0)
Cloud upload / 云端:    none
Estimated cost / 费用:  ¥0
Budget / 预算:          per-run ¥20 · month ¥200 · month used ¥0.00
MinerU / 云端 OCR:      not needed
```

```text
Mode / 模式:            local-vault · gate L3
Cloud upload / 云端:    mineru
Estimated cost / 费用:  未计量 / unmetered   ← MinerU price is unknown, not ¥0
MinerU / 云端 OCR:      12 file(s) · token configured (value never printed)
[L3 · separate confirmation] Cloud upload: MinerU · 12 file(s) · NOT approved by default.
```

Guard sample (`smoke/cost-guard.txt`): 100,000 actual tokens vs ~69,000 estimate high → exit 3 with a
STOP line and “report consumed + remaining work; wait for confirmation”.

---

## 4. Templates and taste decision

The taste flow was run **before** building: emotion → 1 main + 1 auxiliary gene → CSS parameters →
one-line self-check. Full rationale is in `templates/README.md`.

| Template | Emotion | Main gene | Auxiliary gene | Preview |
|---|---|---|---|---|
| `classic-blue` | trust / order | Swiss grid (`moods/09`, `code-genes/01`) | Neoclassical gold hairline (`moods/04`) | `templates/preview/classic-blue.html` |
| `light-green` **(default)** | quiet, held, comfortable long read | Chinese-painting negative space / paper-silk (`moods/06`, `code-genes/03`) | Ghibli natural green (`moods/02`, `code-genes/05`) | `templates/preview/light-green.html` |
| `warm-paper` | nostalgia / gravity / humanities | Neoclassicism (`moods/04`) | Chinese-painting paper / seal accent (`moods/06`, `code-genes/03`) | `templates/preview/warm-paper.html` |

No blue-purple gradient, glassmorphism, rounded-card stack, rainbow chart or gold flood is used.
Every template ships `tokens.css` + `briefing.html` + `analyst.css` + `analyst.html`; the three previews
render the same `templates/preview/sample.json` content. Re-render with
`python3 templates/preview/render_previews.py`.

---

## 5. MinerU (六-bis)

- First-run wizard prints a **bilingual** reminder: apply for an official API token at
  <https://mineru.net> and paste it; it is used only for scanned PDFs / legacy `.doc`/`.ppt` / images;
  all local features work without it, and cloud-only files are listed at the end.
- Token validation accepts `sk-` non-JWT API keys. A non-JWT token is passed to the server for
  validation; a successfully parsed JWT `exp` still triggers an expiry reminder. It never hard-blocks
  a key merely because JWT parsing failed.
- Missing token with files that need MinerU: the card has a separate warning with the application URL,
  and the files are listed as skipped (`smoke/mineru-missing-token.log`, exit 2). Not silent.
- Cloud upload always needs a separate L3 confirmation; non-interactive requires `MINERU_CONFIRM=1`
  or `--confirm-mineru`.
- Token stays in `skills/local-vault/scripts/.env` (0600, gitignored). The assistant did not read or
  print its value, and the setup wizard now merges keys instead of overwriting the file.

---

## 6. Acceptance results

| # | Check | Result | Evidence |
|---|---|---|---|
| 1 | Repo-wide grep: no deleted block-line literal, no scope-filter clause, no built-in Gen byline | **PASS** — both pattern groups `NO MATCHES` | `smoke/acceptance-grep.txt` |
| 2 | verifying smoke on a formerly-blocked military/policy statement | **PASS** — official MND vs SIPRI, `⚖` side-by-side, definition/price-basis/currency attribution, no single-party conclusion | `smoke/verifying-smoke.md` |
| 3 | topic-brief light-green render, blank author | **PASS** — 14,093-byte HTML, template marker `light-green`, 0 author occurrences, cost line present | `smoke/topic-brief-light-green.html`, `smoke/topic-brief-check.txt` |
| 4 | analyst-research light: gate before body; confirmed magpie free call | **PASS** — L1 card exits 10 before confirmation; `--confirmed` exits 0; `MagpieClient` call returns `ANALYST_MAGPIE_OK` on `group/free-first` | `smoke/analyst-light-gate.txt` |
| 5 | local-vault: PDF local conversion, no MinerU, no `claude -p`, magpie frontmatter | **PASS** — `converted_by: pymupdf4llm`, MinerU processed 0, `magpie usage` + enriched frontmatter (abstract/tags/synonyms/key_data) | `smoke/local-vault-semiconductor_note.md`, `smoke/local-vault-sync.log` |
| 6 | `scripts/pack.sh --all` packages all four skills | **PASS** — 4 zips generated; no exact `.env` or logs inside any zip | `smoke/pack-check.txt` |
| 7 (added) | `.env` not git-tracked | **PASS** — `git ls-files --error-unmatch` exit 1; ignored by `.gitignore:7`; mode 600, 65 bytes; value never read/printed | `smoke/env-check.txt` |

Additional smoke: `smoke/mineru-missing-token.log` demonstrates the explicit missing-token path and
exit 2 instead of a silent skip.

### Verifying smoke sources

- Ministry of National Defense of the PRC, 2024-03-09:
  <http://eng.mod.gov.cn/xb/News_213114/NewsRelease/16293055.html>
- SIPRI Yearbook 2025, ch. 3:
  <https://www.sipri.org/yearbook/2025/03>

Both pages were fetched and read in full; no snippet-only conclusion and no fabricated figure.

---

## 7. Defaults I chose (please confirm / override)

1. **Budget defaults** ¥20 per run / ¥200 per month, `ALLOW_PAID=0`.
2. **Template default** `light-green`; `classic-blue` and `warm-paper` are optional.
3. **Free model IDs** `group/free-first` for fast/main/vision; paid IDs left as `paid/heavy-review`
   until you map them to your gateway.
4. **MinerU cloud is opt-in**; a missing token defaults to “skip and list”, never “upload anyway”.

These are written into `.env.example`, `references/pricing.md` and `templates/README.md`; they are
defaults, not irreversible choices.

---

## 8. Open items (≤3)

1. **Add magpie keys to the existing `skills/local-vault/scripts/.env`.** The file was preserved
   untouched (only `MINERU_TOKEN` is present), so a normal `python3 sync.py` currently skips
   frontmatter enrichment / OCR unless you export `MAGPIE_BASE_URL` and `MAGPIE_MODEL_*` or append
   them to that `.env`. Safe keys to add: `MAGPIE_BASE_URL`, `MAGPIE_MODEL_FAST`,
   `MAGPIE_MODEL_MAIN`, `MAGPIE_MODEL_VISION`, `MAGPIE_TIMEOUT_SEC`. The token line stays untouched.
2. **Fill paid rates in `references/pricing.md`.** Paid rows are intentionally `unmetered`; the
   estimator prints `未计量` rather than inventing a price. Paid usage is level 3 and off by default.
3. **Eyeball the three previews and pick a template.** `light-green` is the default; previews:
   `templates/preview/{classic-blue,light-green,warm-paper}.html`. If you prefer a different green
   temperature / serif mix, the values are isolated in each `tokens.css`.

No other known gaps: the four skills, their workflows, whisper, MinerU fallback, pack.sh and the
bilingual mirrors are intact.

---

## 9. Reproduce

```bash
cd ~/dev/market-research-skills-xb

# 1) no block clause / no Gen byline
grep -rniE "out[ ]of[ ]scope|超出[能]力范围|developed[ ]by[ ]gen|小胰[宝]" \
  --exclude-dir=.git --exclude-dir=.venv --exclude-dir=releases \
  --exclude=acceptance-grep.txt .

# 2) templates (needs jinja2; the repo's .venv has it)
python3 templates/preview/render_previews.py

# 3) topic-brief
python3 skills/topic-brief/scripts/render.py smoke/topic-brief-seed.json \
  --out smoke --template light-green

# 4) cost gate / magpie
python3 scripts/estimate.py --mode light --sources 25          # exit 10
python3 scripts/estimate.py --mode light --sources 25 --confirmed  # exit 0

# 5) local-vault (set dirs + magpie env; no MinerU needed for a digital PDF)
KB_SOURCE_DIR=... KB_TARGET_DIR=... \
MAGPIE_BASE_URL=http://127.0.0.1:3425/v1 MAGPIE_MODEL_FAST=group/free-first \
python3 skills/local-vault/scripts/sync.py

# 6) pack
./scripts/pack.sh --all

# 7) .env not tracked
git ls-files --error-unmatch skills/local-vault/scripts/.env   # expected: exit 1
```

---

## 10. Upstream vs this fork (summary)

| Area | Upstream v1.7.1 | This fork v2.0.0 |
|---|---|---|
| Model plumbing | `claude -p` for enrich/OCR; model-specific workflow prose | local magpie gateway; free-first; `.env`-driven |
| Cost control | none | routing / pricing / three-level gate / overrun guard / end line |
| Sensitive topics | politics/military/religion/celebrity/controversial were blocked | multi-source side-by-side, standpoint attribution, no single-party conclusion |
| Byline | built-in default signature | blank default, user-configurable |
| Output style | one blue topic-brief template | 3 shared templates, `light-green` default, previews |
| MinerU token | JWT assumed | `sk-` non-JWT accepted; bilingual first-run reminder; L3 cloud gate |
| Version | 1.7.1 | 2.0.0 |
