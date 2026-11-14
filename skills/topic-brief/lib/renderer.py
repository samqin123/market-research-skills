"""Jinja2 渲染器：把 Briefing 渲染为最终 HTML。

模板解析顺序：
  1. 显式文件路径（含 `/` 或以 `.html` 结尾且存在）
  2. 仓级共享模板 `templates/<name>/briefing.html`（classic-blue / light-green / warm-paper）
  3. skill 内置 `templates/<name>`（兼容旧用法 `briefing.html`）

模板设计同时兼容浏览器查看 + 复制粘贴进微信公众号编辑器：
  - 全 inline `style=""`，不依赖 `<style>` 块
  - `<table>` 嵌套布局，背景色 / 横条放在 `<td>` 上
  - 装饰元素用实体 `<span>` / `<td>`，不用伪元素 / 渐变 / CSS 变量
"""
from __future__ import annotations
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

from .schema import Briefing

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"
REPO_ROOT = Path(__file__).resolve().parents[3]
SHARED_TEMPLATE_DIR = REPO_ROOT / "templates"
DEFAULT_TEMPLATE = "light-green"


def resolve_template(template: str) -> tuple[Path, str]:
    """返回 (模板目录, 模板文件名)。找不到时回退到 skill 内置 briefing.html。"""
    candidate = Path(template).expanduser()
    if candidate.is_file():
        return candidate.parent, candidate.name

    shared = SHARED_TEMPLATE_DIR / template / "briefing.html"
    if shared.is_file():
        return shared.parent, shared.name

    builtin = TEMPLATE_DIR / template
    if builtin.is_file():
        return builtin.parent, builtin.name

    fallback = TEMPLATE_DIR / "briefing.html"
    if fallback.is_file():
        return fallback.parent, fallback.name

    raise FileNotFoundError(f"template not found: {template}")


def render_briefing(
    briefing: Briefing,
    template: str = DEFAULT_TEMPLATE,
    cost_line: str | None = None,
) -> str:
    """渲染单期简报为完整 HTML 字符串。"""
    tpl_dir, tpl_name = resolve_template(template)
    env = Environment(
        loader=FileSystemLoader(str(tpl_dir)),
        autoescape=select_autoescape(["html"]),
    )

    seen_urls: list[str] = []

    def footnote_index(url: str) -> int:
        if url not in seen_urls:
            seen_urls.append(url)
        return seen_urls.index(url) + 1

    tmpl = env.get_template(tpl_name)
    all_sources = briefing.all_sources()
    for s in all_sources:
        footnote_index(s.url)
    html = tmpl.render(
        briefing=briefing,
        all_sources=all_sources,
        footnote_index=footnote_index,
    )
    if cost_line:
        html = html.rstrip() + f"\n<!-- cost: {cost_line} -->\n"
    return html


def save_briefing(
    briefing: Briefing,
    out_dir,
    template: str = DEFAULT_TEMPLATE,
    filename=None,
    cost_line: str | None = None,
):
    """渲染并保存到磁盘，返回文件路径。"""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if filename is None:
        safe = briefing.issue_title.replace("/", "_").replace(" ", "_")[:60]
        filename = f"{briefing.period_end}_{safe}.html"

    html = render_briefing(briefing, template=template, cost_line=cost_line)
    p = out_dir / filename
    p.write_text(html, encoding="utf-8")
    return p