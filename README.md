# AIライティングツール（個人用）

Python + Streamlit + Gemini API。認証・DBなし。

## 起動
```sh
cd ~/Desktop/claude-work/ai-writing-tool
.venv/bin/streamlit run app.py   # → http://localhost:8501
```
初回のみ: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`、`.env` に `GEMINI_API_KEY=...`

## 機能
ブログ記事 / メール返信 / 要約 / 校正 / トーン変換 / キャッチコピー / SNS投稿文 / 翻訳 / タイトル案 / 箇条書き→文章化

## 機能の追加
`prompts.py` の `TOOLS` に `Tool(...)` を1つ足すだけ。画面はフィールド定義から自動生成される。
