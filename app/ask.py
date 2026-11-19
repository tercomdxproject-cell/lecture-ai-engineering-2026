"""第1回: 素のLLMに1回だけ質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 質問を省略すると、講座に固有の質問をする
    uv run python -m app.ask --chat     # 対話モード

ツールも会話履歴も持たない「素の」呼び出し。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse

from google import genai
from google.genai import errors

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"
RECENT_TURNS = 5
SUMMARY_MAX_TOKENS = 300


def _generate_content(client, contents, *, system_instruction=None, max_output_tokens=None):
    config_options = {"temperature": 1}
    if system_instruction is not None:
        config_options["system_instruction"] = system_instruction
    if max_output_tokens is not None:
        config_options["max_output_tokens"] = max_output_tokens
    return client.models.generate_content(
        model=MODEL,
        contents=contents,
        config=genai.types.GenerateContentConfig(**config_options),
    )


def _print_usage(response) -> None:
    usage = response.usage_metadata
    if usage is not None:
        print(
            f"[トークン数] 入力: {usage.prompt_token_count}, "
            f"出力: {usage.candidates_token_count}"
        )


def ask(question: str) -> str:
    client = genai.Client(api_key=get_api_key())
    response = _generate_content(client, question)
    _print_usage(response)
    return response.text


class ChatSession:
    def __init__(self, client) -> None:
        self.client = client
        self.history: list[dict] = []
        self.summary = ""

    def send(self, question: str) -> str:
        self.history.append({"role": "user", "parts": [{"text": question}]})
        response = _generate_content(
            self.client,
            self.history,
            system_instruction=self.summary or None,
        )
        answer = response.text
        self.history.append({"role": "model", "parts": [{"text": answer}]})
        _print_usage(response)
        self._compact_history()
        return answer

    def _compact_history(self) -> None:
        history_limit = RECENT_TURNS * 2
        if len(self.history) <= history_limit:
            return

        old_turn = self.history[:2]
        transcript = "\n".join(
            f"{'ユーザー' if message['role'] == 'user' else 'アシスタント'}: "
            f"{message['parts'][0]['text']}"
            for message in old_turn
        )
        prompt = (
            "既存の要約と古い会話を統合し、今後の応答に必要な情報だけを "
            f"{SUMMARY_MAX_TOKENS} トークン以内で要約してください。\n"
            f"既存の要約:\n{self.summary or '（なし）'}\n\n"
            f"古い会話:\n{transcript}"
        )
        response = _generate_content(
            self.client,
            prompt,
            max_output_tokens=SUMMARY_MAX_TOKENS,
        )
        if not response.text:
            raise RuntimeError("会話履歴を要約できませんでした")

        self.summary = response.text
        del self.history[:2]


def chat() -> None:
    session = ChatSession(genai.Client(api_key=get_api_key()))
    print("対話モードです。終了するには /exit を入力してください。")
    while True:
        try:
            question = input("\nあなた> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if question.lower() in {"/exit", "/quit"}:
            return
        if not question:
            continue
        try:
            print(f"\nGemini> {session.send(question)}")
        except errors.APIError as e:
            print(api_error_message(e.code, e.message))


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?")
    parser.add_argument("--chat", action="store_true", help="会話履歴を保って対話する")
    args = parser.parse_args()

    print(f"[model] {MODEL}")
    if args.chat:
        chat()
        return

    question = args.question or DEFAULT_QUESTION
    print(f"[質問] {question}\n")
    try:
        print(ask(question))
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
