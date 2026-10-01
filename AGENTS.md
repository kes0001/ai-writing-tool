# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## 概要

個人用の AI ライティングツール。Python + Streamlit + Gemini API（`google-genai`）。認証・DB なし、git 管理なし。
Node/npm は使っていない（`package.json` なし）。`npm run dev` ではなく下記の Streamlit コマンドで起動する。

## コマンド

```sh
# 初回セットアップ
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
# .env に GEMINI_API_KEY=... を設定（雛形は .env.example）

# 起動 → http://localhost:8501（.streamlit/config.toml で headless = true）
.venv/bin/streamlit run app.py
```

テスト・リンターは未導入。

## アーキテクチャ

3ファイル構成で、役割がはっきり分かれている。

- **`prompts.py`（機能の定義）**: `Field`（入力欄）と `Tool`（1機能 = 入力欄 + プロンプトテンプレート + system 指示 + temperature）の dataclass と、`TOOLS` リスト。
  - 機能の追加は `TOOLS` に `Tool(...)` を1つ足すだけ。画面側の変更はいらない。
  - `Tool.prompt` は `str.format` で埋めるので、`{key}` は `Field.key` と一致させる。文中に `{` `}` をそのまま書くときは `{{` `}}` にエスケープする。
  - `Field.kind` は `text` / `textarea` / `select` / `number` の4種類。種類を増やすときは `app.py` の `render_field` も直す。
  - temperature は用途で使い分けている（校正 0.2・要約/翻訳 0.3 〜 キャッチコピー 1.0）。
- **`app.py`（画面）**: サイドバーで `TOOLS` から機能を選ぶ → `Field` 定義からフォームを自動生成 → 右の列にストリーミングで出力する。
  - 空欄の任意項目は「（指定なし）」に置き換えてからプロンプトに渡す。
  - ウィジェットの key は `"{tool.id}:{field.key}"`。機能を切り替えても入力が混ざらない。
  - 履歴は `st.session_state.history` にだけ持つ（最大20件表示、再読み込みで消える）。
- **`gemini_client.py`（API 呼び出し）**: `stream(prompt, system, temperature)` がチャンクを yield する。
  - `MODELS` は先頭が主モデル、残りが予備。一時エラー（429 / 503 / quota / 接続断）はモデルごとに `RETRIES_PER_MODEL` 回まで、待ち時間を延ばしながら再試行し、それでも失敗したら次のモデルへ切り替える。
  - **最初のチャンクを返した後のエラーは再試行しない**（本文が重複するため）。この制約は崩さないこと。
