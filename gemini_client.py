"""Gemini呼び出しの共通部。

一時エラー(429/503/接続断)は同一モデルで数回リトライし、
それでもダメなら予備モデルへフォールバックする。
"""
import os
import random
import time
from typing import Iterator

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

MODELS = ["gemini-3.6-flash", "gemini-3.5-flash"]  # 先頭が主モデル、以降は予備
RETRIES_PER_MODEL = 3

_client = None


def client() -> genai.Client:
    global _client
    if _client is None:
        key = os.getenv("GEMINI_API_KEY")
        if not key:
            raise RuntimeError(".env に GEMINI_API_KEY が設定されていません。")
        _client = genai.Client(api_key=key)
    return _client


def _is_transient(e: Exception) -> bool:
    msg = str(e)
    return any(k in msg for k in ("429", "RESOURCE_EXHAUSTED", "503", "UNAVAILABLE")) \
        or any(k in msg.lower() for k in ("quota", "high demand", "disconnected")) \
        or "RemoteProtocol" in msg


def stream(prompt: str, system: str, temperature: float = 0.7) -> Iterator[str]:
    """応答をチャンクごとに返す。最初のチャンクが届く前の一時エラーのみ再試行する。"""
    config = types.GenerateContentConfig(
        system_instruction=system, temperature=temperature,
    )
    last_exc = None
    for model in MODELS:
        for attempt in range(RETRIES_PER_MODEL):
            started = False
            try:
                for chunk in client().models.generate_content_stream(
                    model=model, contents=prompt, config=config,
                ):
                    if chunk.text:
                        started = True
                        yield chunk.text
                if not started:
                    raise RuntimeError("Geminiから本文が返りませんでした。")
                return
            except Exception as e:
                # 途中まで出力済みならやり直すと本文が重複するので、そのまま投げる
                if started or not _is_transient(e):
                    raise
                last_exc = e
                if attempt < RETRIES_PER_MODEL - 1:
                    time.sleep(3 * (attempt + 1) + random.uniform(0, 1.5))
    raise RuntimeError(
        f"全モデル {MODELS} が無料枠上限・混雑・接続断で応答できませんでした。"
        "時間をおいて再実行してください。"
    ) from last_exc
