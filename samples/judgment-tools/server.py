"""MCP server exposing the judgment tools, backed by whatever /v1/systemone server .env
points at (the local d3-flash here; any TypeSafe-compatible endpoint works).

Run over stdio: uv run python server.py
Register in Claude Code: see README (.mcp.json).
"""

from __future__ import annotations

import os

from dotenv import find_dotenv, load_dotenv
from langchain_typesafe import TypeSafeClassifier
from mcp.server.mcpserver import MCPServer

import tools

INSTRUCTIONS = """Judgment tools backed by a local decision model. Every result is advice
(advisory_only: true, execution_authorized: false); you decide and you enforce.
Use verify before quoting a source, gate before a risky step, approval for shell
commands, fastpath to see whether a turn is a calculator/clock/thanks turn."""


def local_classifier() -> TypeSafeClassifier:
    load_dotenv(find_dotenv())  # the repo-root .env
    return TypeSafeClassifier(
        model=os.environ.get("DECISION_MODEL", "d3-flash"),
        # The client always sends a bearer key; an open local server ignores it.
        api_key=os.environ.get("DECISION_API_KEY") or "local",
        base_url=os.environ["DECISION_BASE_URL"],
    )


def build_server(classifier) -> MCPServer:
    server = MCPServer("decision-judgments", instructions=INSTRUCTIONS)

    @server.tool()
    def check(state: str, question: str) -> dict:
        """Yes/no judgment: probability that the answer to `question` about `state` is yes."""
        return tools.check(classifier, state, question)

    @server.tool()
    def route(state: str, question: str, options: dict[str, str]) -> dict:
        """Pick one of `options` ({label: when to pick it}, at most 255) for `state`."""
        return tools.route(classifier, state, question, options)

    @server.tool()
    def score(state: str, question: str, levels: list[str]) -> dict:
        """Place `state` on an ordered rubric; `levels` run from lowest to highest."""
        return tools.score(classifier, state, question, levels)

    @server.tool()
    def verify(claim: str, evidence: str) -> dict:
        """Does `evidence` support the claim? pass / review / block."""
        return tools.verify(classifier, claim, evidence)

    @server.tool()
    def gate(action: str, context: str) -> dict:
        """Should a proposed action go ahead in this context? pass / review / block."""
        return tools.gate(classifier, action, context)

    @server.tool()
    def approval(command: str, reason: str = "") -> dict:
        """Approve a shell command? APPROVE / DENY / ESCALATE (unsure always escalates)."""
        return tools.approval(classifier, command, reason)

    @server.tool()
    def fastpath(text: str) -> dict:
        """Can a local calculator, clock, or canned reply answer this turn without the LLM?"""
        return tools.fastpath(classifier, text)

    @server.tool()
    def skill_relation(skill_a: str, skill_b: str) -> dict:
        """Relation between two skill descriptions, with a merge hint. Never writes anything."""
        return tools.skill_relation(classifier, skill_a, skill_b)

    return server


if __name__ == "__main__":
    build_server(local_classifier()).run("stdio")
