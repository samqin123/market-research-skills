# 消耗预估与三级确认闸口 · Cost gate（共用协议）

> English canonical: [cost-gate.md](cost-gate.md)。英文为唯一权威源；先改英文，再同步本文件。
>
> 确定性预估器：`scripts/estimate.py`（纯本地，绝不调用模型）。

## 为什么需要

一个 skill 不能「因为能做」就开工昂贵或上云的任务。正式开工前先出**预估卡**，判断**闸口级别**，
拿到该级别要求的确认；执行中超过预估或预算就停；结束时在产物尾部写一行实际消耗。

## 预估卡

### 一级 —— 一句话版

适用于 **免费通道 + 单次** 的 `light` / `verifying` / `topic-brief`：

```text
[L1] verifying · 免费（group/free-first）· token ≈ 12k–15k 入 / 0.8k–2k 出 · 2–6 分钟 · ¥0 · 模板 light-green · 开工？（回一词）
```

用户回一个「好 / go」即可。没回之前不要开工。

### 二、三级 —— 完整卡

适用于 `medium` / `heavy`、**批量 local-vault 同步**、任何**付费**通道、任何**云端上传**
（MinerU）、多模型外部调用：

```text
=== 预估卡 / COST ESTIMATE ===
模式 / Mode:            medium（analyst-research）· 闸口 L2
模板 / Template:        light-green（默认；可选 classic-blue / warm-paper）
输入体量 / Input:       ~15 个来源，~90k 输入 token
token 区间 / Range:     90k–105k 入 · 18k–28k 出
预计时长 / Duration:    50–80 分钟
通道 / Channels:
  免费 / Free:          group/free-first — ¥0
  付费 / Paid:          关闭（ALLOW_PAID=0）
云端上传 / Cloud:       无
预计费用 / Cost:        ¥0（仅免费）
预算 / Budget:          单次 ¥20 · 月度 ¥200 · 本月已用 ¥0
MinerU / 云端 OCR:      不需要
---
确认开工？（明确 yes / no）
```

**三级**项目须另起一行、**单独确认**：

```text
[L3 · 单独确认] 付费通道：paid/heavy-review · 预估 ¥未计量 · 默认不批准。
[L3 · 单独确认] 云端上传：MinerU · 3 个文件 · token 已配置 · 默认不批准。
```

三级行没被单独确认 → **默认不走**：继续免费/本地路径，或跳过可选步骤。二级的「yes」不等于批准三级。

### MinerU 单独提示（相关时必写）

若有文件需要 MinerU 而 `MINERU_TOKEN` 缺失，卡里必须有单独警告：

```text
⚠️ MinerU / 云端 OCR：需要 MINERU_TOKEN，当前未配置。
   请先到 https://mineru.net 控制台申请官方 API token，写入 skills/local-vault/scripts/.env；
   或明确确认跳过这些文件（它们会在报告末尾列明，不会被静默丢弃）。
```

`sk-` 开头的 token 是官方现行 API key 格式，**不得**因为不是 JWT 就拒绝；只有成功解析出 JWT `exp`
时才做过期提醒。只检查是否存在，绝不打印值。

## 闸口级别

| 级别 | 触发条件 | 展示 | 确认方式 |
|---|---|---|---|
| **一级** | 免费通道 **且** 单次 `light` / `verifying` / `topic-brief` | 一句话版 | 回一词 |
| **二级** | `medium` / `heavy`；批量 `local-vault` 同步；多文件转换 | 完整卡 | 明确 yes |
| **三级** | **任何**付费通道；**任何**云端上传（MinerU）；多模型外部调用 | 完整卡 **+** 单独三级行 | 逐项单独明确 yes |

规则：

- 多个触发 → 取**最高**级别。
- 没确认 → 不开工。一级等那一词；二/三级等明确 yes。
- 三级默认 **no**。「未确认」= 走免费/本地路径或跳过，绝不静默花钱。
- 模板选择与预估卡**同屏**（默认 `light-green`，不选不阻塞）。
- `estimate.py` 已实现该语义：不带 `--confirmed` 打印卡并退出 **10**（等待确认）；带 `--confirmed` 退出 0。
  `--level` 可预览，但脚本按实际参数计算级别。

## 确定性预估（`scripts/estimate.py`）

```bash
# 一级卡，等待确认
python3 scripts/estimate.py --mode verifying --sources 5

# medium 完整卡，已确认
python3 scripts/estimate.py --mode medium --sources 15 --confirmed

# 批量 local-vault + 云端兜底、token 未配置
python3 scripts/estimate.py --mode local-vault --files 12 --cloud-upload mineru

# 运行后超支守卫（退出 3 = STOP）
python3 scripts/estimate.py --mode heavy --actual-total-tokens 210000 --actual-cost 32

# 记录实际消耗，供月度上限使用
python3 scripts/estimate.py --mode light --record --actual-total-tokens 12000 --actual-cost 0
```

预估器：

- 按模式、来源数、文件数、页数与可选 `--input-chars` 做确定性 token 区间估算（公式见脚本注释）；
- 价格**只**读 `references/pricing.md`；未知 → `未计量 / unmetered`；
- 从 `.env` 读 `ALLOW_PAID`、`MAGPIE_*` 模型 ID 与预算上限（绝不打印密钥）；
- 只检查 `MINERU_TOKEN` 是否存在，缺失时打印申请入口；
- 读本地台账（`MRS_COST_LEDGER`，默认 `.cost-ledger.jsonl`，已 gitignore）算本月已用；
- 待确认退出 **10**，守卫触发退出 **3**，其余退出 **0**。

## 执行中的超支守卫

满足**任一**即立即停并报告：

1. 实际消耗超过预估**上限的 50%**；
2. 触及单次上限（`COST_MAX_PER_RUN_CNY`，默认 ¥20）或月度上限
   （`COST_MAX_MONTH_CNY`，默认 ¥200）。

停机信息必须写清：已耗（token / 通道 / 费用或未计量）、剩余工作量、继续所需确认。不得静默续跑，
也不得把付费任务自动降级成另一个付费任务。

价格未计量时，用 **token** 对比预估上限，并注明费用未计量。绝不为了「让守卫看起来通过」编一个 yuan 数。

## 运行结束的消耗行

在产物尾部追加一行（HTML 用注释，Markdown 用末行）：

```text
<!-- cost: mode=medium tokens=96k_in/24k_out channel=group/free-first cost=¥0 estimate=90k–105k/18k–28k -->
```

Markdown：

```text
---
Cost: medium · 96k 入 / 24k 出 · group/free-first · ¥0 · 预估 90k–105k / 18k–28k
```

未计量写 `cost=未计量 (unmetered)`。中途停机加 `stopped=overrun`。

## 预算变量

```dotenv
ALLOW_PAID=0
COST_MAX_PER_RUN_CNY=20
COST_MAX_MONTH_CNY=200
MRS_COST_LEDGER=.cost-ledger.jsonl
```

改默认值必须由用户明确指示；改完记进项目笔记，不得静默改预估器。