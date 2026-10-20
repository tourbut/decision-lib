"""Start the MCP server over stdio like a coding agent would, list its tools, and measure
the three labelled sets through real MCP calls.

Usage: python demo.py
"""

from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path

from mcp.client.client import Client
from mcp.client.stdio import StdioServerParameters

from cases import APPROVAL, FASTPATH, RELATIONS

HERE = Path(__file__).parent


async def call(client: Client, name: str, args: dict) -> dict:
    result = await client.call_tool(name, args)
    return json.loads(result.content[0].text)


async def measure(client: Client, title: str, items: list[dict], tool: str, args, field: str) -> None:
    started = time.perf_counter()
    results = [await call(client, tool, args(item)) for item in items]
    hits = sum(r[field] == item["label"] for item, r in zip(items, results))
    print(f"\n{title}: {hits}/{len(items)} in {time.perf_counter() - started:.1f}s")
    for item, r in zip(items, results):
        if r[field] != item["label"]:
            print(f"  MISS want {item['label']}, got {r[field]} ({r.get('reason', '')}): {list(args(item).values())[0]}")
    if tool == "fastpath":
        answered = [r for r in results if r["answer"]]
        print("  answered locally: " + " | ".join(r["answer"] for r in answered))


async def main() -> None:
    server = StdioServerParameters(command="uv", args=["run", "--quiet", "python", "server.py"], cwd=str(HERE))
    async with Client(server) as client:
        listed = await client.list_tools()
        print("tools:", ", ".join(t.name for t in listed.tools))
        await measure(client, "fastpath", FASTPATH, "fastpath", lambda c: {"text": c["text"]}, "handler")
        await measure(client, "approval", APPROVAL, "approval", lambda c: {"command": c["command"]}, "decision")
        await measure(client, "skill_relation", RELATIONS, "skill_relation",
                      lambda c: {"skill_a": c["a"], "skill_b": c["b"]}, "relation")


if __name__ == "__main__":
    asyncio.run(main())
