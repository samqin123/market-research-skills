# 价格表 · Pricing

> English canonical: [pricing.md](pricing.md)。英文为唯一权威源；先改英文，再同步本文件。
>
> 本文件是 `scripts/estimate.py` **唯一**的价格来源。模型缺失、标为 `unmetered`、或费率为空时，
> 预估器必须输出 **未计量 / unmetered**，绝不凭记忆编价。依赖付费预估前，请填入你与 magpie
> 的实际合同价。

## 规则

1. **免费通道按定义 ¥0。** 默认工作路径是免费优先；付费通道默认关闭（`ALLOW_PAID=0`）。
2. **未知 = 未计量。** 缺行、`unmetered`、`?`、非数字费率都表示「未计量」。不要用记忆里的刊例价替代。
3. **币种为人民币 / 百万 token**（¥ / 1M tokens），与 `.env` 预算单位一致。
4. **改表不改代码。** `scripts/estimate.py` 解析下方 fenced `csv` 块。
5. 即使价格已知，付费调用仍须通过**三级单独确认**。

## 机器可读表

预估器解析此 fenced 块；保持表头与逗号分隔列不变。`status` 取 `free` / `metered` / `unmetered`。

```csv
model_id,tier,input_cny_per_mtok,output_cny_per_mtok,status,notes
group/free-first,free,0,0,free,默认 free-first 路由组
group/smart-split,free,0,0,free,free-first/smart-split 路由组；除非 ALLOW_PAID=1，否则不升级付费
auto/deepseek-v4.1-flash,free,0,0,free,免费 DeepSeek 通道（以你网关实际可用为准）
paid/heavy-review,paid,unmetered,unmetered,unmetered,可选 heavy 终审强模型——填入你的合同价
paid/vision,paid,unmetered,unmetered,unmetered,可选付费视觉/OCR 模型——填入你的合同价
```

## 人类备注

- 上表模型 ID 是 `.env.example` 的默认示例；以本机网关 `/v1/models` 返回为准。
- 路由组内部可能选择付费模型。除非你明确批准付费升级，否则保持 `ALLOW_PAID=0`；若某路由组可能升级，
  就按付费通道处理，走三级闸口。
- 预算上限写在 `.env`（`COST_MAX_PER_RUN_CNY`、`COST_MAX_MONTH_CNY`），不在本文件。