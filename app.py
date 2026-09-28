"""AIライティングツール（個人用）

起動: .venv/bin/streamlit run app.py
"""
import streamlit as st

import gemini_client
from prompts import TOOLS, Field

st.set_page_config(page_title="AIライティングツール", page_icon="✍️", layout="wide")

if "history" not in st.session_state:
    st.session_state.history = []  # [{"tool": 名前, "output": 本文}]

# ---------------------------------------------------------------- サイドバー
with st.sidebar:
    st.title("✍️ AIライティング")
    tool = st.radio(
        "機能を選ぶ", TOOLS,
        format_func=lambda t: f"{t.icon} {t.name}",
        label_visibility="collapsed",
    )
    st.divider()
    st.caption(f"モデル: {gemini_client.MODELS[0]}（予備: {', '.join(gemini_client.MODELS[1:])}）")


def render_field(f: Field, tool_id: str):
    key = f"{tool_id}:{f.key}"
    label = f.label + (" *" if f.required else "")
    if f.kind == "textarea":
        return st.text_area(label, key=key, placeholder=f.placeholder, height=200)
    if f.kind == "select":
        idx = f.options.index(f.default) if f.default in f.options else 0
        return st.selectbox(label, f.options, index=idx, key=key)
    if f.kind == "number":
        return st.number_input(label, min_value=1, value=int(f.default or 1), step=1, key=key)
    return st.text_input(label, key=key, placeholder=f.placeholder)


# ---------------------------------------------------------------- メイン
st.header(f"{tool.icon} {tool.name}")
st.caption(tool.description)

col_in, col_out = st.columns(2, gap="large")

with col_in:
    with st.form(f"form-{tool.id}"):
        values = {f.key: render_field(f, tool.id) for f in tool.fields}
        submitted = st.form_submit_button("生成する", type="primary", use_container_width=True)

with col_out:
    st.subheader("出力")
    if submitted:
        missing = [f.label for f in tool.fields if f.required and not str(values[f.key]).strip()]
        if missing:
            st.warning("入力してください: " + "、".join(missing))
        else:
            filled = {k: (v if str(v).strip() else "（指定なし）") for k, v in values.items()}
            try:
                output = st.write_stream(
                    gemini_client.stream(tool.prompt.format(**filled), tool.system, tool.temperature)
                )
                st.session_state.history.insert(0, {"tool": f"{tool.icon} {tool.name}", "output": output})
                st.code(output, language=None, wrap_lines=True)  # 右上のボタンでコピーできる
            except Exception as e:
                st.error(f"生成に失敗しました: {e}")
    else:
        st.info("左のフォームに入力して「生成する」を押してください。")

# ---------------------------------------------------------------- 履歴（このセッション内のみ）
if st.session_state.history:
    st.divider()
    st.subheader("履歴")
    for i, h in enumerate(st.session_state.history[:20]):
        with st.expander(f"{h['tool']} — {h['output'][:40].strip()}…"):
            st.code(h["output"], language=None, wrap_lines=True)
