"""Issue #599: raw unexecuted tool_call JSON must never become section content.

Covers the two layers of the fix:
1. _parse_tool_calls understands fenced JSON tool calls so they get executed.
2. _looks_like_tool_call_artifact detects tool-call leftovers the parser cannot
   execute (unknown tool name, broken JSON, fenced blobs) so the ReACT loop
   retries instead of returning them as the section's final answer.
"""

import pytest

from app.services.report_agent import ReportAgent


def make_agent() -> ReportAgent:
    """ReportAgent without running __init__ (methods under test are stateless)."""
    return ReportAgent.__new__(ReportAgent)


RAW_CALL = '{"name": "quick_search", "parameters": {"query": "群体互动", "limit": 15}}'


class TestParseToolCalls:
    def test_parses_bare_json_call(self):
        calls = make_agent()._parse_tool_calls(RAW_CALL)
        assert len(calls) == 1
        assert calls[0]["name"] == "quick_search"

    def test_parses_fenced_json_call(self):
        calls = make_agent()._parse_tool_calls(f"```json\n{RAW_CALL}\n```")
        assert len(calls) == 1
        assert calls[0]["name"] == "quick_search"

    def test_parses_fenced_call_without_language_tag(self):
        calls = make_agent()._parse_tool_calls(f"```\n{RAW_CALL}\n```")
        assert len(calls) == 1
        assert calls[0]["name"] == "quick_search"

    def test_unknown_tool_name_is_not_parsed(self):
        calls = make_agent()._parse_tool_calls('{"name": "search_graph", "parameters": {}}')
        assert calls == []


class TestLooksLikeToolCallArtifact:
    @pytest.mark.parametrize(
        "text",
        [
            RAW_CALL,
            f"```json\n{RAW_CALL}\n```",
            # unknown tool name still looks like a call, must not become content
            '{"name": "search_graph", "parameters": {"q": "x"}}',
            '{"tool": "quick_search", "params": {}}',
            # broken JSON that still carries tool-call keys
            '{"name": "quick_search", "parameters": {"query": "x",}',
            '<tool_call>{"name": "quick_search"}</tool_call>',
        ],
    )
    def test_detects_tool_call_artifacts(self, text):
        assert ReportAgent._looks_like_tool_call_artifact(text)

    @pytest.mark.parametrize(
        "text",
        [
            "",
            None,
            "## 群体反应与互动动态\n\n模拟显示用户之间形成了明显的意见分化……",
            "Final Answer: 本章节分析了……",
            # JSON without tool-call keys (e.g. a data table) is fine
            '{"total_posts": 120, "total_comments": 456}',
            # long prose that merely mentions tool_call
            "正文开头 " + "分析内容。" * 200 + ' 提到 <tool_call> 机制 ' + "结尾。" * 50,
        ],
    )
    def test_accepts_real_content(self, text):
        assert not ReportAgent._looks_like_tool_call_artifact(text)
