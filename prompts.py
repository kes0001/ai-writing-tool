"""ライティング機能の定義。

機能を増やすときは TOOLS に Tool を1つ足すだけでよい。
画面（app.py）は Field 定義を読んでフォームを自動生成する。
prompt 内の {key} は Field.key の入力値に置き換わる。
"""
from dataclasses import dataclass, field


@dataclass
class Field:
    key: str
    label: str
    kind: str = "text"  # text / textarea / select / number
    options: list = field(default_factory=list)
    default: object = ""
    placeholder: str = ""
    required: bool = False


@dataclass
class Tool:
    id: str
    name: str
    icon: str
    description: str
    fields: list
    prompt: str
    system: str = "あなたは日本語の文章を得意とするプロのライターです。"
    temperature: float = 0.7


TONES = ["丁寧", "カジュアル", "ビジネス", "フレンドリー", "やわらかい", "論理的"]

TOOLS = [
    Tool(
        id="blog",
        name="ブログ記事の執筆",
        icon="📝",
        description="テーマから見出し付きのブログ記事を書きます。",
        fields=[
            Field("topic", "テーマ・タイトル案", required=True,
                  placeholder="例：初心者向け 在宅ワークの集中力を上げるコツ"),
            Field("keywords", "含めたいキーワード（任意）", placeholder="例：ポモドーロ, デスク環境"),
            Field("reader", "想定読者（任意）", placeholder="例：在宅勤務1年目の会社員"),
            Field("tone", "文体", "select", TONES, "やわらかい"),
            Field("length", "目安の文字数", "number", default=2000),
            Field("notes", "盛り込みたい内容・メモ（任意）", "textarea"),
        ],
        prompt="""次の条件でブログ記事を書いてください。

- テーマ: {topic}
- キーワード: {keywords}
- 想定読者: {reader}
- 文体: {tone}
- 目安の文字数: {length}字程度
- メモ: {notes}

構成: タイトル → 導入 → 見出し（##）ごとの本文 → まとめ。Markdownで出力してください。
事実が不確かな数値や固有名詞は書かないでください。""",
        system="あなたは読みやすさとSEOを意識するプロのブログライターです。",
    ),
    Tool(
        id="mail_reply",
        name="メールの返信",
        icon="✉️",
        description="受け取ったメールと伝えたい要点から返信文を作ります。",
        fields=[
            Field("received", "受信したメール", "textarea", required=True),
            Field("points", "返信で伝えたいこと", "textarea", required=True,
                  placeholder="例：日程は来週水曜で了承。資料は金曜までに送る"),
            Field("relation", "相手との関係", "select",
                  ["社外（取引先）", "社外（初めての相手）", "社内（上司）", "社内（同僚）", "友人・知人"]),
            Field("sender", "署名に使う名前（任意）"),
        ],
        prompt="""次のメールへの返信文を作成してください。

【受信メール】
{received}

【返信で伝えたいこと】
{points}

【相手との関係】{relation}
【差出人名】{sender}

件名（Re: 形式）と本文を出力してください。関係性にふさわしい敬語・距離感にしてください。""",
        system="あなたはビジネスメールに精通した秘書です。",
        temperature=0.5,
    ),
    Tool(
        id="summary",
        name="文章の要約",
        icon="📋",
        description="長い文章を指定の形式で要約します。",
        fields=[
            Field("text", "要約したい文章", "textarea", required=True),
            Field("style", "要約の形式", "select",
                  ["3行要約", "箇条書き（要点5つ程度）", "100字要約", "300字要約", "見出し付きの詳しめ要約"]),
        ],
        prompt="""次の文章を「{style}」で要約してください。原文にない情報は加えないでください。

{text}""",
        temperature=0.3,
    ),
    Tool(
        id="proofread",
        name="校正・推敲",
        icon="🔍",
        description="誤字脱字・不自然な表現を直し、修正点を一覧で示します。",
        fields=[
            Field("text", "校正したい文章", "textarea", required=True),
            Field("level", "修正の強さ", "select",
                  ["誤字脱字のみ", "読みやすさも改善", "大きく書き直してよい"], "読みやすさも改善"),
        ],
        prompt="""次の文章を校正してください。修正の強さ: {level}

出力形式:
## 修正後の文章
（全文）

## 修正点
| 修正前 | 修正後 | 理由 |

【文章】
{text}""",
        system="あなたは経験豊富な日本語の校正者です。",
        temperature=0.2,
    ),
    Tool(
        id="tone",
        name="トーン変換",
        icon="🎨",
        description="内容を変えずに文体・言い回しを変換します。",
        fields=[
            Field("text", "変換したい文章", "textarea", required=True),
            Field("target", "変換後のトーン", "select",
                  ["丁寧な敬語", "カジュアル", "ビジネス文書", "やわらかく親しみやすく", "簡潔に", "小学生にもわかるように"]),
        ],
        prompt="""次の文章を、意味を変えずに「{target}」のトーンに書き換えてください。書き換え後の文章のみ出力してください。

{text}""",
        temperature=0.5,
    ),
    Tool(
        id="catchcopy",
        name="キャッチコピー",
        icon="💡",
        description="商品・サービスのキャッチコピー案を複数出します。",
        fields=[
            Field("product", "商品・サービス名", required=True),
            Field("feature", "特徴・強み", "textarea", required=True),
            Field("target", "ターゲット（任意）"),
            Field("count", "案の数", "number", default=10),
        ],
        prompt="""次の商品・サービスのキャッチコピーを{count}案出してください。

- 名称: {product}
- 特徴・強み: {feature}
- ターゲット: {target}

切り口（ベネフィット訴求・共感・数字・問いかけ など）を散らし、各案に「狙い」を一言添えて番号付きで出力してください。""",
        system="あなたは広告代理店のベテランコピーライターです。",
        temperature=1.0,
    ),
    Tool(
        id="sns",
        name="SNS投稿文",
        icon="📣",
        description="媒体に合わせた投稿文を作ります。",
        fields=[
            Field("topic", "投稿したい内容", "textarea", required=True),
            Field("platform", "媒体", "select", ["X（旧Twitter）", "Instagram", "Threads", "Facebook", "LinkedIn"]),
            Field("count", "案の数", "number", default=3),
        ],
        prompt="""次の内容で{platform}向けの投稿文を{count}案作ってください。
媒体の文字数制限・文化（ハッシュタグの有無や数、絵文字の使い方）に合わせてください。

【内容】
{topic}""",
        system="あなたはSNS運用に詳しいマーケターです。",
        temperature=0.9,
    ),
    Tool(
        id="translate",
        name="翻訳",
        icon="🌐",
        description="自然な訳文に翻訳します。",
        fields=[
            Field("text", "翻訳したい文章", "textarea", required=True),
            Field("lang", "翻訳先", "select", ["英語", "日本語", "中国語（簡体字）", "韓国語"]),
            Field("style", "スタイル", "select", ["自然な意訳", "直訳寄り", "ビジネス向け"]),
        ],
        prompt="""次の文章を{lang}に翻訳してください。スタイル: {style}。訳文のみ出力してください。

{text}""",
        system="あなたはプロの翻訳者です。",
        temperature=0.3,
    ),
    Tool(
        id="title",
        name="タイトル・見出し案",
        icon="🏷️",
        description="記事や資料の本文からタイトル案を出します。",
        fields=[
            Field("text", "本文または概要", "textarea", required=True),
            Field("purpose", "用途", "select", ["ブログ記事（SEO重視）", "プレゼン資料", "メルマガ件名", "YouTube動画"]),
            Field("count", "案の数", "number", default=10),
        ],
        prompt="""次の内容に対する「{purpose}」向けのタイトル案を{count}個出してください。番号付きで、文字数も併記してください。

{text}""",
        temperature=0.9,
    ),
    Tool(
        id="expand",
        name="箇条書き→文章化",
        icon="🧩",
        description="メモや箇条書きを、つながりのある文章に仕上げます。",
        fields=[
            Field("memo", "メモ・箇条書き", "textarea", required=True),
            Field("use", "用途", "select", ["報告書", "日報", "社内連絡", "自己紹介", "ブログの一節"]),
            Field("tone", "文体", "select", TONES, "丁寧"),
        ],
        prompt="""次のメモを「{use}」として自然な文章にまとめてください。文体: {tone}。メモにない事実は足さないでください。

{memo}""",
        temperature=0.5,
    ),
]

TOOLS_BY_ID = {t.id: t for t in TOOLS}
