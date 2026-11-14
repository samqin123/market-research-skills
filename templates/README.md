# Templates · 共享输出模板

Three first-party templates shared by `topic-brief` and `analyst-research`. The default is
**`light-green`**. Selection happens on the same screen as the cost estimate card; choosing
nothing does not block and falls back to `light-green`.

## Taste decision (required before building)

The style genes were chosen through the `taste` decision flow:
**emotion → 1 main gene + 1 auxiliary gene → CSS parameters → one-line self-check**.
No generic "AI default" look (blue-purple gradients, glassmorphism, floating rounded cards,
rainbow charts) is used anywhere.

| Template | Reader should feel | Main gene | Auxiliary gene | One-line self-check |
|---|---|---|---|---|
| `classic-blue` | Trust, order, "this is the original institutional brief" | Swiss grid / Bauhaus (`moods/09`, `code-genes/01`): alignment, restrained palette, hairline rules | Neoclassicism (`moods/04`): gold used only as a 4px hairline, symmetrical cover | "Swiss grid + one gold line — the upstream TOPIC BRIEF blue, unchanged." |
| `light-green` **(default)** | Quiet, held, comfortable for a long read | Chinese-painting negative space / paper-silk (`moods/06`, `code-genes/03`): 0 radius, 1px ink rules, large leading, content not crowded | Ghibli natural green (`moods/02`, `code-genes/05`): natural green family, warm low-contrast ink; colour warmth only, no cartoon shapes | "Paper ground + deep-green serif titles + 2.0 leading — a page to read, not a dashboard." |
| `warm-paper` | Nostalgia, gravity, humanities / history | Neoclassicism (`moods/04`): serif, symmetry, muted earth palette | Chinese-painting paper / negative space (`moods/06`, `code-genes/03`): warm rice paper, ink text, one seal-red accent, hairline rules | "Warm paper + ink serif + one terracotta point — a printed essay, not a slide." |

### Palette rationale (CSS tokens)

- `classic-blue`: upstream values preserved exactly (`#1e3a5f` navy, `#d4a259` gold hairline,
  `#f0f5fa` panel, `#4a90c2` accent). It is an **optional** template, not the default.
- `light-green`: `#eef4ea` page ground / `#fbfaf4` rice-paper body / `#1f4d3a` deep-green titles /
  `#2f3a33` low-contrast ink / `#6f8f5f` moss accent / `#d7e0cf` rules. No pure white, no pure
  black, no gradient. Leading 2.0; WeChat-paste friendly inline styles.
- `warm-paper`: `#e9dcc6` page ground / `#faf3e6` warm paper / `#3b2f27` ink-brown titles /
  `#3a332c` ink / `#8c4a32` terracotta accent / `#b08a5a` brass **hairline only**. Leading 2.05;
  serif body and titles.

## File contract

Each `templates/<name>/` contains:

| File | Purpose |
|---|---|
| `tokens.css` | CSS variable block (the single source of the palette / fonts / leading) |
| `briefing.html` | `topic-brief` HTML layout (Jinja2, inline styles for browser + WeChat paste) |
| `analyst.css` | `analyst-research` Quarto HTML / publication derivation CSS (imports `tokens.css`) |
| `analyst.html` | One-page `analyst-research` publication sample using `tokens.css` + `analyst.css` |

`templates/preview/` contains the **same sample content** rendered through all three
`briefing.html` layouts:

- `templates/preview/classic-blue.html`
- `templates/preview/light-green.html`
- `templates/preview/warm-paper.html`
- `templates/preview/sample.json` (the shared content; `author` is explicitly empty)

Re-render after editing a template:

```bash
python3 templates/preview/render_previews.py
```

## How skills use it

- `topic-brief`: `python3 skills/topic-brief/scripts/render.py <seed.json> --template light-green`.
  The renderer resolves `templates/<name>/briefing.html` first, then the skill's built-in template.
- `analyst-research`: copy the chosen `tokens.css` / `analyst.css` into the project or point
  Quarto at them (`format: html: css: templates/<name>/analyst.css`). PDF/Word derivations inherit
  the same palette and font temperament (serif for `warm-paper`, sans body / serif display for
  `light-green`, sans for `classic-blue`).
- The template choice is recorded on the estimate card; `light-green` is the default and requires
  no blocking question.

## Anti-patterns (rejected)

- Blue-purple gradient hero, neon glow, glassmorphism.
- Stacks of rounded white cards on a coloured ground.
- Gold flood / ornate borders (gold and brass are hairlines only).
- Rainbow chart series, 3-D pies, drop shadows on data marks.
- Filling negative space with QR codes, watermarks or decorative patterns.