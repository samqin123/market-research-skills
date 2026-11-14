#!/usr/bin/env python3
"""Render the same sample content through all three topic-brief templates.

Outputs:
  templates/preview/classic-blue.html
  templates/preview/light-green.html
  templates/preview/warm-paper.html
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
SKILL_ROOT = REPO_ROOT / "skills" / "topic-brief"
sys.path.insert(0, str(SKILL_ROOT))

from lib.renderer import render_briefing  # noqa: E402
from lib.schema import Briefing  # noqa: E402


def main() -> int:
    seed = json.loads((HERE / "sample.json").read_text(encoding="utf-8"))
    briefing = Briefing.from_dict(seed)
    if briefing.author:
        print("ERROR: preview sample must keep the author blank", file=sys.stderr)
        return 1
    for name in ("classic-blue", "light-green", "warm-paper"):
        html = render_briefing(briefing, template=name)
        out = HERE / f"{name}.html"
        out.write_text(html, encoding="utf-8")
        print(f"OK: {out.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())