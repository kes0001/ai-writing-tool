# 約80行で読み解く AIライティングツールの `app.py`

## はじめに：このファイルの役割

`app.py` は、このツールの**画面をまるごと担当するファイル**です。Gemini への問い合わせは `gemini_client.py`、機能ごとの入力欄やプロンプトは `prompts.py` に任せていて、`app.py` はその2つをつないで画面に並べる役です。

読む前に、Streamlit の大事なルールを1つだけ覚えてください。

> **Streamlit は、ボタンを押すなどの操作があるたびに `app.py` を上から下まで丸ごと実行し直す。**

JavaScript で「クリックされたらこの関数を動かす」と書くのとは考え方が違います。**毎回ページ全体を作り直すスクリプト**だと思って読むと、コードが分かりやすくなります。

---

## 1. 準備：部品を読み込んでページを設定する

```python
import streamlit as st

import gemini_client
from prompts import TOOLS, Field

st.set_page_config(page_title="AIライティングツール", page_icon="✍️", layout="wide")
```

- `st` は Streamlit の部品箱です。`st.button()` や `st.text_area()` のように呼ぶと、画面に部品が出ます。
- `TOOLS` は `prompts.py` で定義した機能（ブログ、メール返信、要約……）のリストです。
- `set_page_config` は、HTML の `<title>` やファビコンを決めるのと同じ役割です。`layout="wide"` で画面いっぱいの横幅を使います。

## 2. 消えない保存場所：`session_state`

```python
if "history" not in st.session_state:
    st.session_state.history = []
```

スクリプトは操作のたびに最初から実行し直されるので、ふつうの変数はそのたびに空に戻ります。そこで使うのが `st.session_state` です。**再実行をまたいでも中身が残る保存場所**です。

`if` で「まだ作っていなければ空のリストを作る」としているので、初回だけ初期化されて、2回目以降は中身がそのまま残ります。ここに生成結果の履歴をためていきます。

（ブラウザのタブを再読み込みすると、セッションごと作り直されて空になります。）

## 3. サイドバー：機能を選ぶ

```python
with st.sidebar:
    st.title("✍️ AIライティング")
    tool = st.radio(
        "機能を選ぶ", TOOLS,
        format_func=lambda t: f"{t.icon} {t.name}",
        label_visibility="collapsed",
    )
```

- `with st.sidebar:` の中に書いたものは、左のサイドバーに表示されます。HTML で `<aside>` の中に要素を入れるイメージです。
- `st.radio` はラジオボタンです。選択肢に `TOOLS` をそのまま渡しているので、戻り値の `tool` は **選ばれた機能のオブジェクトそのもの**になります。あとは `tool.name` や `tool.fields` でその機能の情報を取り出せます。
- `format_func` は、選択肢を画面に表示するときの文字を決める関数です。ここでは「📝 ブログ記事の執筆」のように、アイコンと名前をつなげて表示しています。

## 4. 入力欄を作る関数：`render_field`

```python
def render_field(f: Field, tool_id: str):
    key = f"{tool_id}:{f.key}"
    label = f.label + (" *" if f.required else "")
    if f.kind == "textarea":
        return st.text_area(...)
    if f.kind == "select":
        return st.selectbox(...)
    if f.kind == "number":
        return st.number_input(...)
    return st.text_input(...)
```

`prompts.py` の入力欄の定義（`Field`）を受け取って、**種類に合った部品を1つ出す**関数です。

- `kind` の値で部品を分けます：`textarea` は複数行、`select` はプルダウン、`number` は数値、それ以外は1行のテキスト欄。
- 必須の項目は、ラベルの後ろに「 *」が付きます。
- `key` は `"blog:topic"` のように **機能ID + 項目名** にしています。こうすると、別の機能の同じ名前の欄と入力内容が混ざりません。

この関数があるので、**機能を増やすときに画面側のコードを書く必要がありません**。`prompts.py` に定義を足せば、フォームは自動で作られます。

## 5. メイン画面：左に入力、右に出力

```python
st.header(f"{tool.icon} {tool.name}")
st.caption(tool.description)

col_in, col_out = st.columns(2, gap="large")
```

選んだ機能の名前と説明を出してから、`st.columns(2)` で画面を左右2列に分けます。CSS で 2カラムのグリッドを組むのと同じです。

### 左の列：フォーム

```python
with col_in:
    with st.form(f"form-{tool.id}"):
        values = {f.key: render_field(f, tool.id) for f in tool.fields}
        submitted = st.form_submit_button("生成する", type="primary", use_container_width=True)
```

- `st.form` で囲むと、**入力している間はスクリプトが再実行されず**、「生成する」を押したときにまとめて送信されます。HTML の `<form>` と同じ感覚です。
- `values = {...}` は、その機能の入力欄を全部作って、`{"topic": "入力された値", "tone": "やわらかい", ...}` という辞書にまとめています。
- `submitted` は、ボタンが押されたときの実行でだけ `True` になります。

### 右の列：出力

```python
with col_out:
    st.subheader("出力")
    if submitted:
        ...
    else:
        st.info("左のフォームに入力して「生成する」を押してください。")
```

ボタンが押されていなければ案内文を出すだけです。押されたときの流れは次のとおりです。

**① 必須項目のチェック**

```python
missing = [f.label for f in tool.fields if f.required and not str(values[f.key]).strip()]
if missing:
    st.warning("入力してください: " + "、".join(missing))
```

必須なのに空欄の項目を集めて、あれば警告を出して止めます。

**② 空欄を「（指定なし）」で埋める**

```python
filled = {k: (v if str(v).strip() else "（指定なし）") for k, v in values.items()}
```

任意の項目が空のままだと、プロンプトが「キーワード: 」のように途中で切れて AI が迷います。そこで「（指定なし）」と書き入れておきます。

**③ AI に投げて、届いた順に表示する**

```python
output = st.write_stream(
    gemini_client.stream(tool.prompt.format(**filled), tool.system, tool.temperature)
)
```

1行に3つの処理が入っているので、内側から順に読みます。

1. `tool.prompt.format(**filled)`：プロンプトの型にある `{topic}` や `{tone}` に、入力された値を差し込みます。JavaScript のテンプレートリテラルと同じです。
2. `gemini_client.stream(...)`：できあがったプロンプトを Gemini に送り、返ってきた文章を**少しずつ**受け取ります。
3. `st.write_stream(...)`：受け取った文章を、届いた順に画面へ書き足します。ChatGPT のように文字が流れて表示されるのはこの部分です。すべて届くと、全文が `output` に入ります。

**④ 履歴に保存して、コピーできる形で表示する**

```python
st.session_state.history.insert(0, {"tool": f"{tool.icon} {tool.name}", "output": output})
st.code(output, language=None, wrap_lines=True)
```

- 履歴リストの**先頭**に追加するので、新しいものが上に並びます。
- `st.code` はコードブロックとして表示する部品です。右上にコピーボタンが付くので、生成した文章をワンクリックでコピーできます。

**⑤ エラー処理**

```python
except Exception as e:
    st.error(f"生成に失敗しました: {e}")
```

API の上限や通信エラーで失敗しても、アプリは止まらずに赤いメッセージが出ます。

## 6. 履歴の表示

```python
if st.session_state.history:
    st.divider()
    st.subheader("履歴")
    for i, h in enumerate(st.session_state.history[:20]):
        with st.expander(f"{h['tool']} — {h['output'][:40].strip()}…"):
            st.code(h["output"], language=None, wrap_lines=True)
```

- 履歴が1件以上あるときだけ表示します。
- 表示するのは新しい順に最大20件です。
- `st.expander` は開閉できるパネルで、HTML の `<details>` にあたります。見出しには「機能名 — 本文の最初の40文字…」を出しています。

---

## まとめ：「生成する」を押したときの流れ

```
「生成する」をクリック
   ↓
app.py が上から丸ごと再実行される
   ↓
session_state から履歴を取り出す（消えていない）
   ↓
サイドバーで選ばれている機能 → tool
   ↓
フォームを作り直す（submitted = True）
   ↓
必須チェック → 空欄を「（指定なし）」で埋める → プロンプトを組み立てる
   ↓
Gemini に送る → 返ってきた文章を少しずつ画面に表示する
   ↓
履歴に追加して、コピーボタン付きで表示する
```

押さえておきたいポイントは3つです。

1. **Streamlit は操作のたびにスクリプトを最初から実行し直す**。残したいデータは `session_state` に入れる。
2. **`with` ブロックで表示場所を決める**。サイドバー・列・フォーム・開閉パネルなど、HTML で要素を入れ子にするのと同じ感覚で使える。
3. **画面は `prompts.py` の定義から自動で作られる**。機能を増やすときに `app.py` を触る必要はない。
