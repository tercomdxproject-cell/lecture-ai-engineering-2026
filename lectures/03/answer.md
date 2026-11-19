# 第3回 解答

## 演習

- 第1回（素のLLM）とエージェントの回答の違い：
・第1回の `app.ask` の回答と違い、 `data/glossary.json`の内容に即した回答が返ってくる
・初めに検索を行っているため、回答生成の開始に少し遅延が生じる 

- `--trace` で見えたツール呼び出し（ツール名と引数）：
・[tool call]   search_glossary({'query': 'LoRA'})

- 1つの質問での LLM 呼び出し回数（`requests`）：
・requests=2

- 追加したツールと、docstring に書いた説明：
def make_quiz(lecture: int) -> str:
    """指定した回の用語から 1つを選び、
    確認問題と答えを返す。
    「第2回の確認問題を出して」のように、
    復習用の問題を求められたときに使う。
    """
    terms = [term for term in load_glossary() if term["lecture"] == lecture]
    if not terms:
        return f"第{lecture}回の用語は用語集にありません。"
    term = random.choice(terms)
    return json.dumps(
        {"question": f"{term['term']}の意味は？", "answer": term["definition"]},
        ensure_ascii=False,
    )

## 宿題

- 取り組んだレベル：基礎 
- やったこと：
　agent.pyのINSTRUCTIONSを変更。以下の２文を追加
　- 用語集に見つかったことは、回答の初めに「用語集に回答があった」と伝える。
　- 用語集に一部のみ見つかった場合、回答の初めに「用語集に一部解答があった」と伝える。
- 結果：
　１、当初、"""- 用語集に見つかったことは、回答の初めに「用語集に回答があった」と伝える。"""
   と記載。
　　"[model] gemini-3.5-flash-lite
    用語集に回答があった

    LoRAとQLoRAの主な違いは、・・・"
    と解答してくれた。
　しかし、これだと"LoRA とLorandの違いは？ "といった質問でも、"用語集に回答があった"と解答した。

　２、そのため、"""- 用語集に一部のみ見つかった場合、回答の初めに「用語集に一部解答があった」と伝える。"""
    の一文もINSTRUCTIONSに追加したところ、
    "[model] gemini-3.5-flash-lite
    用語集に一部解答があった（「LoRA」のみ登録されています）"
    と、望む形で解答してくれた。
- 気づき・疑問：
　自然言語で処理できる分、修正は容易。しかし、難しい分岐になった際は、tool側で分岐をした方が間違いが少ないように考える。

- 取り組んだレベル：実装 
- やったこと：
    - agent.py,tools.pyにsave_learning_log機能を追加
    - test_agent.py,test_tools.pyに確認のためのコードを追加
- 結果：
    - 実行状況
    "
    uv run python -m app.agent "11月8日、第3回の実装課題で学んだことは、DeferredToolRequestsでツールの承認待ちを扱えることです。この内容を学習記録に保存して"
    [model] gemini-3.5-flash-lite

    save_learning_log の実行確認
    {
    "content": "# 学習記録 (11月8日)\n- 講義: 第3回\n- 学んだこと: DeferredToolRequestsでツールの承認待ちを扱えること。\n"
    "

    - 記録された内容
    "
    # 学習記録 (11月8日)
    - 講義: 第3回
    - 学んだこと: DeferredToolRequestsでツールの承認待ちを扱えること。
    "

- 気づき・疑問：
 - よくある「実行しますか　y/N」の形で確認形式で動作が行えることを理解
 - 日付のような必要な情報を確実に残すためには、入力・出力フォーマットを定める方が良い。
