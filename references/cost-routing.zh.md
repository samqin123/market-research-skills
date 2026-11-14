# 成本路由 · Cost routing（四 skill 共用）

> English canonical: [cost-routing.md](cost-routing.md)。英文为唯一权威源；先改英文，再同步本文件。

## 一个网关，一条政策

四个 skill 的**脚本**发起的模型调用统一走本机 **magpie** 网关（OpenAI 兼容
`/v1/chat/completions`）。任何脚本都不写死服务商地址、模型名或 key；全部来自 `.env`
（见 `.env.example`）。

政策按优先级：

1. **免费优先。** 默认 `group/free-first`（或 `group/smart-split`，且付费升级关闭）。免费通道 ¥0。
2. **付费必须三级单独确认。** `ALLOW_PAID=0` 是默认值。即使 `ALLOW_PAID=1`，付费调用也要单独一行、
   单独确认（见 `cost-gate.zh.md`）。
3. **失败降级，绝不静默。** 网关不可达、模型缺失、key 未配置时，记一行日志、跳过该步骤、继续转换/起草；
   不得伪造被跳过的内容。MinerU token 缺失要在预估卡单独提示。
4. **绝不打印密钥。** key 只从 `.env` / 环境变量读取，不回显、不进日志、不入库；文档与报错只出现变量名。

## 环境变量

| 变量 | 用途 | `.env.example` 默认 |
|---|---|---|
| `MAGPIE_BASE_URL` | 网关基址（含 `/v1`） | `http://127.0.0.1:3425/v1` |
| `MAGPIE_API_KEY` | 本机可选 key；网关无鉴权则留空 | *留空* |
| `MAGPIE_MODEL_FAST` | 摘要、标签、OCR | `group/free-first` |
| `MAGPIE_MODEL_MAIN` | 分析、起草、核实 | `group/free-first` |
| `MAGPIE_MODEL_VISION` | 图片 OCR 兜底 | `group/free-first` |
| `MAGPIE_MODEL_HEAVY` | 可选 heavy 终审（仅付费档） | `paid/heavy-review` |
| `MAGPIE_TIMEOUT_SEC` | 单次调用超时 | `90` |
| `ALLOW_PAID` | `0` = 仅免费（默认） | `0` |
| `COST_MAX_PER_RUN_CNY` | 单次预算上限 | `20` |
| `COST_MAX_MONTH_CNY` | 月度预算上限 | `200` |

`MAGPIE_API_KEY` 是这里唯一的密钥。现有 `MINERU_TOKEN` 同理：只在本机
`skills/local-vault/scripts/.env`，不打印、不提交。

## 环节 → 模型档位

| Skill / 环节 | 模型档位 | 理由 |
|---|---|---|
| `local-vault` frontmatter 富化（abstract / tags / synonyms / key_data） | **免费小/快模型**（`MAGPIE_MODEL_FAST`） | 短结构化抽取；强模型只增成本不增价值 |
| `local-vault` PPT 图片 OCR | **免费视觉模型**（`MAGPIE_MODEL_VISION`） | 转写而非推理；失败降级为图片引用 |
| `local-vault` MinerU 云端 OCR（扫描 PDF / 老 Office / 图片） | **云端上传**，不是 LLM 档位 | 需单独三级确认 + token |
| `verifying` | **免费主力**（`MAGPIE_MODEL_MAIN`） | 多源阅读与综合，free-first 足够 |
| `topic-brief` | **免费主力** | 基于已采集素材起草与引用 |
| `analyst-research` light / medium | **免费主力** | 起草与自检 |
| `analyst-research` heavy 起草 | **免费主力** | 长文起草保持免费 |
| `analyst-research` heavy 终审 | 默认免费主力；**只有用户明确要求**才用付费强模型 | 唯一可能值得上强模型的环节；永远走三级 |

**口径：** 摘要 / OCR / 打标签 → 免费小模型；分析 / 起草 / 核实 → 免费主力；heavy 终审 → 默认免费主力，
除非用户明确选择付费强模型。绝不为了「试试看」启动付费调用。

## skill 如何表达

- `local-vault`：`scripts/magpie_client.py` 封装网关；`enrich_frontmatter()` 与
  `ocr_image_via_magpie()` 调它。任何失败都记日志并返回 `""` / `False`，转换照常落地。
- `verifying` / `topic-brief` / `analyst-research`：skill 文本在每处调用模型的地方写「经 magpie 路由」。
  AI 使用 `.env` 提供的模型 ID，不写死厂商与 key。
- 四个 skill 正式开工前都跑 `scripts/estimate.py`，按 `cost-gate.zh.md` 出预估卡。

## 降级阶梯

1. 指定模型不可用 → 用 `MAGPIE_MODEL_FAST` 重试一次。
2. 网关不可达 → 记一行、跳过可选步骤；所有本地转换器继续。
3. 免费路由耗尽 → **停**，不自动升级付费；报剩余工作量，等确认。
4. 请求付费但未确认 → 继续免费路径，或跳过可选步骤；绝不静默花钱。

## 这里的「免费」怎么算

价格表 `references/pricing.md` 中状态为 `free` / `0` 的通道才算免费。可能内部升级到付费模型的路由组
**不算**免费：保持 `ALLOW_PAID=0`，或按付费通道处理并走三级闸口。未知价格打印
**未计量 / unmetered**，绝不猜。