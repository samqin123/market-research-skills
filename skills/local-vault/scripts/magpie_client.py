"""magpie_client.py — 统一的本机 magpie 网关客户端（OpenAI 兼容）。

设计约束（见 references/cost-routing.md）：
  - 地址 / 模型名全部来自 .env（MAGPIE_BASE_URL / MAGPIE_MODEL_FAST / ...），代码不写死。
  - 绝不打印或记录 API key；错误信息只报状态码与脱敏后的响应片段。
  - 免费优先：默认用 MAGPIE_MODEL_FAST；付费模型只有调用方显式传入才用。
  - 任何失败由调用方 fail-soft 处理（enrich / OCR 跳过，不中断转换）。
"""
from __future__ import annotations

import base64
import json
import logging
import mimetypes
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional

import config


class MagpieError(RuntimeError):
    """网关不可用 / 配置缺失 / 响应异常。调用方应 fail-soft。"""


def _is_configured() -> bool:
    return bool(config.MAGPIE_BASE_URL and config.MAGPIE_MODEL_FAST)


class MagpieClient:
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger
        self.base_url = config.MAGPIE_BASE_URL
        self.api_key = config.MAGPIE_API_KEY
        self.timeout = config.MAGPIE_TIMEOUT_SEC
        self.max_retries = max(0, config.MAGPIE_MAX_RETRIES)

    def _post(self, payload: dict) -> dict:
        if not self.base_url:
            raise MagpieError(
                "MAGPIE_BASE_URL 未配置：请在 skills/local-vault/scripts/.env 写入网关地址"
                "（见 .env.example），不要硬编码。"
            )
        url = self.base_url.rstrip("/") + "/chat/completions"
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        last_exc: Optional[Exception] = None
        for attempt in range(self.max_retries + 1):
            req = urllib.request.Request(url, data=data, headers=headers, method="POST")
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    body = resp.read().decode("utf-8", errors="replace")
                return json.loads(body)
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="replace")[:200]
                last_exc = MagpieError(f"magpie HTTP {exc.code}: {detail}")
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                last_exc = MagpieError(f"magpie 不可达: {exc}")
            except json.JSONDecodeError as exc:
                last_exc = MagpieError(f"magpie 返回非 JSON: {exc}")
            if attempt < self.max_retries:
                time.sleep(1.0 + attempt)
        raise last_exc or MagpieError("magpie 调用失败")

    def _extract(self, response: dict) -> str:
        try:
            choice = response["choices"][0]
            content = choice["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise MagpieError(f"magpie 响应缺少 choices/message/content: {exc}") from exc
        if isinstance(content, list):
            content = "".join(
                part.get("text", "") for part in content if isinstance(part, dict)
            )
        usage = response.get("usage") or {}
        if self.logger and usage:
            self.logger.info(
                "    magpie usage: in=%s out=%s model=%s",
                usage.get("prompt_tokens", "?"),
                usage.get("completion_tokens", "?"),
                response.get("model", "?"),
            )
        return str(content or "").strip()

    def chat(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.2,
    ) -> str:
        model = (model or config.MAGPIE_MODEL_FAST).strip()
        if not model:
            raise MagpieError("MAGPIE_MODEL_FAST 未配置（见 .env.example）")
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False,
        }
        return self._extract(self._post(payload))

    def ocr_image(
        self,
        image_path: Path,
        model: Optional[str] = None,
        max_tokens: int = 4096,
    ) -> str:
        model = (model or config.MAGPIE_MODEL_VISION or config.MAGPIE_MODEL_FAST).strip()
        if not model:
            raise MagpieError("MAGPIE_MODEL_VISION / MAGPIE_MODEL_FAST 未配置")
        mime = mimetypes.guess_type(str(image_path))[0] or "image/png"
        b64 = base64.b64encode(image_path.read_bytes()).decode("ascii")
        prompt = (
            "Transcribe ALL text, numbers and data in this image, preserving structure "
            "(render any tables as Markdown). Output ONLY the transcription, no commentary. "
            "If there is no readable text, output nothing."
        )
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime};base64,{b64}"},
                        },
                    ],
                }
            ],
            "max_tokens": max_tokens,
            "temperature": 0.0,
            "stream": False,
        }
        return self._extract(self._post(payload))


def is_configured() -> bool:
    """只检查配置是否存在，不返回值、不打印 key。"""
    return _is_configured()