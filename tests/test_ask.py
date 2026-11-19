from types import SimpleNamespace

from app import ask


class FakeClient:
    pass


def test_chat_compacts_old_turns_and_reuses_summary(monkeypatch):
    responses = iter(["answer"] * 6 + ["summary", "next answer", "summary 2"])
    calls = []

    def fake_generate_content(client, contents, **kwargs):
        calls.append((contents, kwargs))
        return SimpleNamespace(text=next(responses), usage_metadata=None)

    monkeypatch.setattr(ask, "_generate_content", fake_generate_content)
    session = ask.ChatSession(FakeClient())

    for turn in range(6):
        assert session.send(f"question {turn}") == "answer"

    assert session.summary == "summary"
    assert len(session.history) == ask.RECENT_TURNS * 2
    assert calls[6][1]["max_output_tokens"] == ask.SUMMARY_MAX_TOKENS
    assert session.send("next question") == "next answer"
    assert calls[7][1]["system_instruction"] == "summary"