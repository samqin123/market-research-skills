#!/usr/bin/env python3
"""estimate.py — deterministic cost estimate + three-level confirmation gate.

Pure local: this script NEVER calls a model. It reads:
  - references/pricing.md   (the only price source; unknown => unmetered)
  - .env / environment      (model IDs, ALLOW_PAID, budget caps, token presence only)
  - a local JSONL ledger    (month-to-date consumption)

Exit codes:
  0  ready / recorded / guard OK
  3  overrun guard tripped — STOP and report
  10 confirmation still required (no --confirmed)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TEMPLATE = "light-green"
TEMPLATES = ("classic-blue", "light-green", "warm-paper")

# Deterministic estimate model. Tokens are deliberately ranges, not promises.
# input = base + sources * per_source (or base + files * per_file for local-vault)
MODES = {
    "verifying": dict(base=12000, per_source=1000, out_lo=800, out_hi=2000,
                      min_lo=2, min_hi=6, level=1, default_sources=5),
    "topic-brief": dict(base=12000, per_source=700, out_lo=4500, out_hi=7500,
                        min_lo=15, min_hi=30, level=1, default_sources=8),
    "light": dict(base=18000, per_source=500, out_lo=7000, out_hi=11000,
                  min_lo=15, min_hi=25, level=1, default_sources=25),
    "medium": dict(base=45000, per_source=2500, out_lo=18000, out_hi=28000,
                   min_lo=50, min_hi=80, level=2, default_sources=15),
    "heavy": dict(base=120000, per_source=3000, out_lo=55000, out_hi=80000,
                  min_lo=120, min_hi=180, level=2, default_sources=40),
    "local-vault": dict(base=12000, per_file=4000, out_per_file_lo=1200,
                        out_per_file_hi=2500, min_per_file_lo=1.5,
                        min_per_file_hi=3.0, level=1, default_sources=0),
}


def _load_env(path: Path) -> None:
    """Load KEY=VALUE without printing or overriding already-set variables."""
    if not path.is_file():
        return
    try:
        for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip("'\"")
            if key and key not in os.environ:
                os.environ[key] = value
    except OSError:
        pass


def load_config() -> None:
    # Root .env is optional; local-vault's .env carries MINERU_TOKEN in this repo.
    _load_env(REPO_ROOT / ".env")
    _load_env(REPO_ROOT / "skills" / "local-vault" / "scripts" / ".env")


def env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, "") or default)
    except ValueError:
        return default


def env_model(name: str, default: str) -> str:
    return (os.getenv(name) or default).strip()


def load_prices(path: Optional[Path] = None) -> dict[str, dict]:
    """Parse the fenced csv block in references/pricing.md. Missing => empty (unmetered)."""
    path = path or (REPO_ROOT / "references" / "pricing.md")
    prices: dict[str, dict] = {}
    if not path.is_file():
        return prices
    in_block = False
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if line.startswith("```"):
            if not in_block and "csv" in line.lower():
                in_block = True
            elif in_block:
                in_block = False
            continue
        if not in_block or not line or line.startswith("model_id,"):
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 5:
            continue
        model_id, tier, in_rate, out_rate, status = parts[:5]
        prices[model_id] = {
            "tier": tier,
            "input": _rate(in_rate, status),
            "output": _rate(out_rate, status),
            "status": status.lower(),
        }
    return prices


def _rate(value: str, status: str) -> Optional[float]:
    if status.lower() == "free":
        return 0.0
    if value.lower() in {"", "unmetered", "?", "-", "n/a", "none"}:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def price_for(prices: dict, model: str, side: str) -> Optional[float]:
    row = prices.get(model)
    if not row:
        return None
    return row.get(side)


def fmt_tokens(n: int) -> str:
    if n >= 1000:
        return f"{n / 1000:.1f}k".replace(".0k", "k")
    return str(n)


def fmt_cny(value: Optional[float]) -> str:
    if value is None:
        return "未计量 / unmetered"
    return f"¥{value:.2f}".rstrip("0").rstrip(".")


def estimate_tokens(args) -> dict:
    if args.mode == "local-vault":
        files = max(1, args.files or 1)
        spec = MODES["local-vault"]
        in_lo = spec["base"] + files * spec["per_file"]
        in_hi = int(in_lo * 1.15)
        out_lo = files * spec["out_per_file_lo"]
        out_hi = files * spec["out_per_file_hi"]
        min_lo = files * spec["min_per_file_lo"]
        min_hi = files * spec["min_per_file_hi"]
    else:
        spec = MODES[args.mode]
        sources = args.sources if args.sources is not None else spec["default_sources"]
        in_lo = spec["base"] + max(0, sources) * spec["per_source"]
        in_hi = int(in_lo * 1.15)
        out_lo, out_hi = spec["out_lo"], spec["out_hi"]
        min_lo, min_hi = spec["min_lo"], spec["min_hi"]

    if args.input_chars:
        char_lo = int(args.input_chars / 2)
        char_hi = int(args.input_chars / 1.3)
        in_lo, in_hi = max(in_lo, char_lo), max(in_hi, char_hi)

    if args.pages:
        # Reading pages adds ~350 tokens/page on top of the mode baseline.
        in_lo += args.pages * 350
        in_hi += args.pages * 400

    in_lo = max(1000, (in_lo // 1000) * 1000)
    in_hi = max(in_lo + 1000, (in_hi // 1000) * 1000)
    out_lo = max(200, (out_lo // 100) * 100)
    out_hi = max(out_lo + 200, (out_hi // 100) * 100)
    return {
        "input_lo": in_lo, "input_hi": in_hi,
        "output_lo": out_lo, "output_hi": out_hi,
        "minutes_lo": min_lo, "minutes_hi": min_hi,
    }


def compute_level(args) -> int:
    level = MODES[args.mode]["level"]
    if args.files and args.files > 1:
        level = max(level, 2)
    if args.cloud_upload == "mineru" or args.mineru_files:
        level = max(level, 3)
    if args.paid or args.multi_model:
        level = max(level, 3)
    return level


def read_ledger(path: Path) -> dict:
    total_cost = 0.0
    total_tokens = 0
    month = datetime.now().strftime("%Y-%m")
    if not path.is_file():
        return {"month": month, "cost": 0.0, "tokens": 0, "entries": 0}
    try:
        for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                row = json.loads(raw)
            except json.JSONDecodeError:
                continue
            ts = str(row.get("ts", ""))
            if not ts.startswith(month):
                continue
            if row.get("cost") is not None:
                total_cost += float(row["cost"])
            if row.get("total_tokens") is not None:
                total_tokens += int(row["total_tokens"])
    except OSError:
        pass
    return {"month": month, "cost": total_cost, "tokens": total_tokens, "entries": 0}


def card(args) -> dict:
    tokens = estimate_tokens(args)
    prices = load_prices(Path(args.pricing) if args.pricing else None)
    level = compute_level(args)
    free_model = args.free_model or env_model("MAGPIE_MODEL_MAIN", "") or env_model("MAGPIE_MODEL_FAST", "") or "unset"
    paid_model = args.paid_model or env_model("MAGPIE_MODEL_HEAVY", "unset")
    allow_paid = (os.getenv("ALLOW_PAID", "0").strip().lower() in {"1", "true", "yes", "on"})

    free_cost = 0.0
    paid_cost = None
    if args.paid or allow_paid:
        pin = price_for(prices, paid_model, "input")
        pout = price_for(prices, paid_model, "output")
        if pin is not None and pout is not None:
            # Paid escalation is a bounded final-review slice, not the whole run.
            paid_in, paid_out = 12000, 4000
            paid_cost = (paid_in / 1_000_000) * pin + (paid_out / 1_000_000) * pout
        paid_cost = paid_cost  # None => unmetered

    estimate_cost = free_cost if not args.paid else paid_cost
    # MinerU cloud pricing is not in pricing.md; never present the free-LLM ¥0 as the total.
    if args.cloud_upload == "mineru" or args.mineru_files:
        estimate_cost = None
    budget_run = env_float("COST_MAX_PER_RUN_CNY", 20.0)
    budget_month = env_float("COST_MAX_MONTH_CNY", 200.0)
    ledger_path = Path(os.getenv("MRS_COST_LEDGER", str(REPO_ROOT / ".cost-ledger.jsonl"))).expanduser()
    ledger = read_ledger(ledger_path)

    mineru_relevant = bool(args.cloud_upload == "mineru" or args.mineru_files)
    token_present = bool(os.getenv("MINERU_TOKEN", "").strip())

    return {
        "mode": args.mode,
        "level": level,
        "template": args.template,
        "free_model": free_model,
        "magpie_base_set": bool(os.getenv("MAGPIE_BASE_URL", "").strip()),
        "paid_model": paid_model,
        "allow_paid": allow_paid,
        "paid_requested": bool(args.paid),
        "multi_model": bool(args.multi_model),
        "cloud_upload": args.cloud_upload,
        "mineru_files": args.mineru_files,
        "mineru_relevant": mineru_relevant,
        "mineru_token_present": token_present,
        "tokens": tokens,
        "free_cost": free_cost,
        "paid_cost": paid_cost,
        "estimate_cost": estimate_cost,
        "budget_run": budget_run,
        "budget_month": budget_month,
        "month_used": ledger["cost"],
        "month_tokens": ledger["tokens"],
        "ledger_path": str(ledger_path),
        "pricing_found": bool(prices),
    }


def print_card(c: dict) -> None:
    t = c["tokens"]
    tok = f"{fmt_tokens(t['input_lo'])}–{fmt_tokens(t['input_hi'])} in · {fmt_tokens(t['output_lo'])}–{fmt_tokens(t['output_hi'])} out"
    dur = f"{t['minutes_lo']:g}–{t['minutes_hi']:g} min"
    if c["level"] == 1 and not c["mineru_relevant"] and not c["paid_requested"] and not c["multi_model"]:
        warn = "" if c["magpie_base_set"] else " · ⚠ magpie unset"
        print(
            f"[L1] {c['mode']} · free ({c['free_model']}) · tokens ≈ {tok} · {dur} · ¥0 · "
            f"template: {c['template']}{warn} · proceed? (one word)"
        )
        return

    print("=== COST ESTIMATE / 预估卡 ===")
    print(f"Mode / 模式:            {c['mode']} · gate L{c['level']}")
    print(f"Template / 模板:        {c['template']} (default light-green; classic-blue / warm-paper optional)")
    print(f"Token range / token:    {tok}")
    print(f"Duration / 预计时长:    {dur}")
    print("Channels / 通道:")
    print(f"  Free / 免费:          {c['free_model']} — ¥0")
    if not c["magpie_base_set"]:
        print("  ⚠ magpie:            MAGPIE_BASE_URL 未配置；脚本内 LLM 步骤会跳过（见 .env.example）")
    if c["paid_requested"] or c["allow_paid"]:
        paid_note = fmt_cny(c["paid_cost"])
        state = "requested" if c["paid_requested"] else "available, not requested"
        print(f"  Paid / 付费:          {c['paid_model']} — {paid_note} ({state})")
    else:
        print("  Paid / 付费:          off (ALLOW_PAID=0)")
    print(f"Cloud upload / 云端:    {c['cloud_upload'] if c['cloud_upload'] != 'none' else 'none'}")
    print(f"Estimated cost / 费用:  {fmt_cny(c['estimate_cost'])}")
    print(
        f"Budget / 预算:          per-run ¥{c['budget_run']:g} · month ¥{c['budget_month']:g} · "
        f"month used ¥{c['month_used']:.2f}"
    )
    if c["mineru_relevant"]:
        if c["mineru_token_present"]:
            print(f"MinerU / 云端 OCR:      {c['mineru_files'] or 'needed'} file(s) · token configured (value never printed)")
        else:
            print("MinerU / 云端 OCR:      ⚠️ 需要 MINERU_TOKEN，当前未配置。")
            print("                        请先到 https://mineru.net 控制台申请官方 API token，")
            print("                        写入 skills/local-vault/scripts/.env；或明确确认跳过这些文件。")
    else:
        print("MinerU / 云端 OCR:      not needed")

    if c["level"] >= 3:
        print("---")
        if c["paid_requested"]:
            print(f"[L3 · separate confirmation] Paid channel: {c['paid_model']} · est. {fmt_cny(c['paid_cost'])} · NOT approved by default.")
        if c["multi_model"]:
            print("[L3 · separate confirmation] Multi-model external calls via magpie · NOT approved by default.")
        if c["cloud_upload"] == "mineru" or c["mineru_files"]:
            print(f"[L3 · separate confirmation] Cloud upload: MinerU · {c['mineru_files'] or 'needed'} file(s) · NOT approved by default.")
        print("---")
    print("Confirm? (explicit yes / no)")


def guard(c: dict, args) -> tuple[bool, list[str], Optional[float]]:
    """Return (tripped, messages, actual_cost_or_None)."""
    messages: list[str] = []
    actual_tokens = args.actual_total_tokens
    actual_cost = args.actual_cost
    total_hi = c["tokens"]["input_hi"] + c["tokens"]["output_hi"]
    tripped = False

    if actual_tokens is not None and actual_tokens > 1.5 * total_hi:
        tripped = True
        messages.append(
            f"STOP: actual tokens {actual_tokens:,} > 150% of estimate high ({int(total_hi * 1.5):,})."
        )

    if actual_cost is not None:
        if actual_cost > c["budget_run"]:
            tripped = True
            messages.append(
                f"STOP: actual cost {fmt_cny(actual_cost)} > per-run cap ¥{c['budget_run']:g}."
            )
        if c["estimate_cost"] is not None and c["estimate_cost"] > 0 and actual_cost > 1.5 * c["estimate_cost"]:
            tripped = True
            messages.append(
                f"STOP: actual cost {fmt_cny(actual_cost)} > 150% of estimate ({fmt_cny(c['estimate_cost'])})."
            )
        if c["month_used"] + actual_cost > c["budget_month"]:
            tripped = True
            messages.append(
                f"STOP: month-to-date ¥{c['month_used']:.2f} + actual {fmt_cny(actual_cost)} > monthly cap ¥{c['budget_month']:g}."
            )
        if c["estimate_cost"] is None:
            messages.append("Cost is unmetered; token guard still applies. Do not invent a yuan figure.")

    if tripped:
        messages.append(
            "Report consumed tokens/channel/cost and remaining work; wait for explicit confirmation before continuing."
        )
    return tripped, messages, actual_cost


def record(c: dict, args, actual_cost: Optional[float]) -> None:
    path = Path(c["ledger_path"]).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "ts": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "mode": c["mode"],
        "level": c["level"],
        "total_tokens": args.actual_total_tokens,
        "input_tokens": args.actual_input_tokens,
        "output_tokens": args.actual_output_tokens,
        "cost": actual_cost,
        "channel": c["free_model"] if not c["paid_requested"] else c["paid_model"],
    }
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> int:
    p = argparse.ArgumentParser(
        description="Deterministic cost estimate + three-level confirmation gate (never calls a model)."
    )
    p.add_argument("--mode", required=True, choices=sorted(MODES))
    p.add_argument("--sources", type=int, default=None, help="number of sources/documents")
    p.add_argument("--files", type=int, default=None, help="number of files (local-vault batch)")
    p.add_argument("--pages", type=int, default=None, help="pages to read")
    p.add_argument("--input-chars", type=int, default=None, help="override input volume (characters)")
    p.add_argument("--template", default=DEFAULT_TEMPLATE, choices=TEMPLATES)
    p.add_argument("--cloud-upload", default="none", choices=("none", "mineru"))
    p.add_argument("--mineru-files", type=int, default=0)
    p.add_argument("--paid", action="store_true", help="request a paid channel (level 3)")
    p.add_argument("--multi-model", action="store_true", help="request multi-model external calls (level 3)")
    p.add_argument("--free-model", default=None)
    p.add_argument("--paid-model", default=None)
    p.add_argument("--pricing", default=None, help="override pricing.md path")
    p.add_argument("--confirmed", action="store_true", help="the user has confirmed this gate level")
    p.add_argument("--actual-total-tokens", type=int, default=None)
    p.add_argument("--actual-input-tokens", type=int, default=None)
    p.add_argument("--actual-output-tokens", type=int, default=None)
    p.add_argument("--actual-cost", type=float, default=None, help="actual cost in CNY; omit if unmetered")
    p.add_argument("--record", action="store_true", help="append actual usage to the ledger")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    args = p.parse_args()

    load_config()
    c = card(args)

    if args.json:
        print(json.dumps(c, ensure_ascii=False, indent=2))
    else:
        print_card(c)

    tripped, messages, actual_cost = guard(c, args)
    if tripped:
        print()
        for msg in messages:
            print(msg, file=sys.stderr)
        if args.record:
            record(c, args, actual_cost)
        return 3

    if args.record:
        record(c, args, actual_cost)
        print(f"\nRecorded to {c['ledger_path']} (month-to-date ¥{c['month_used'] + (actual_cost or 0):.2f}).")

    if not args.confirmed:
        print("\nGATE: awaiting confirmation — no work starts yet (exit 10).")
        return 10

    print("\nGATE: confirmed — proceed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())