"""Standalone deterministic tool discovery; never executes or authorizes tools.

Original implementation of behavior observed in Claude Code 2.1.323. This
recreates the small ranker, not the surrounding MCP/session/context machinery.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class Tool:
    name: str
    description: str = ""
    search_hint: str = ""
    server_name: str | None = None
    remote_tool_name: str | None = None

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> Tool:
        info = value.get("mcp_info") or {}
        result = cls(
            name=value["name"],
            description=value.get("description", ""),
            search_hint=value.get("search_hint", ""),
            server_name=info.get("server_name"),
            remote_tool_name=info.get("tool_name"),
        )
        if not isinstance(result.name, str) or not result.name:
            raise ValueError("Tool name must be a nonempty string")
        if not all(isinstance(text, str) for text in
                   (result.description, result.search_hint)):
            raise ValueError("Tool description and search_hint must be strings")
        if any(text is not None and not isinstance(text, str)
               for text in (result.server_name, result.remote_tool_name)):
            raise ValueError("MCP names must be strings")
        return result

    def mcp_names(self) -> tuple[str, str] | None:
        if self.server_name is not None and self.remote_tool_name is not None:
            return self.server_name, self.remote_tool_name
        segments = self.name.split("__", 2)
        if len(segments) == 3 and segments[0] == "mcp":
            return segments[1], segments[2]
        return None


@dataclass(frozen=True)
class Hit:
    name: str
    score: int | None  # Direct name selection has no relevance score.


@dataclass(frozen=True)
class SearchResult:
    query: str
    hits: tuple[Hit, ...]
    catalog_size: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "matches": [hit.name for hit in self.hits],
            "scores": {hit.name: hit.score for hit in self.hits},
            "total_visible_tools": self.catalog_size,
        }

    def as_tool_result(self, tool_use_id: str) -> dict[str, Any]:
        """Public Messages API client-tool result, not a server-tool result."""
        return {
            "type": "tool_result",
            "tool_use_id": tool_use_id,
            "content": [
                {"type": "tool_reference", "tool_name": hit.name}
                for hit in self.hits
            ],
        }


def _name_parts(tool: Tool) -> tuple[list[str], list[str], bool]:
    mcp = tool.mcp_names()
    if mcp is not None:
        coarse = [part.lower() for part in mcp if part]
        fine = [part for name in coarse for part in re.split(r"[\s_.]+", name)
                if part]
        return fine, coarse, True
    name = re.sub(r"([a-z])([A-Z])", r"\1 \2", tool.name).replace("_", " ")
    return name.lower().split(), [tool.name.lower()], False


def _word_match(term: str, text: str) -> bool:
    # ASCII word boundaries approximate JavaScript's \b behavior.
    return re.search(r"\b" + re.escape(term) + r"\b", text, re.ASCII) is not None


def _score(tool: Tool, terms: list[str], required: list[str]) -> int:
    fine, coarse, is_mcp = _name_parts(tool)
    description = tool.description.lower()
    hint = tool.search_hint[:4096].lower()
    for term in required:
        if not (any(term in name for name in fine + coarse)
                or _word_match(term, description) or _word_match(term, hint)):
            return 0

    score = 0
    full = " ".join(fine)
    for term in terms:
        if term in fine:
            score += 12 if is_mcp else 10
        elif any(term in part for part in fine):
            score += 6 if is_mcp else 5
        if term in coarse:
            score += 12 if is_mcp else 10
        elif any(term in part for part in coarse):
            score += 4 if is_mcp else 3
        if term in full and score == 0:
            score += 3
        if _word_match(term, hint):
            score += 4
        if _word_match(term, description):
            score += 2
    return score


def search(
    catalog: Iterable[Tool],
    query: str,
    max_results: int = 5,
    *,
    allowed_names: set[str] | None = None,
) -> SearchResult:
    """Search only the supplied/visible catalog. No execution rights are granted.

    Differences from the inspected client: no internal MCP name sanitization,
    loaded-tool tracking, server refresh, special tool expansion, or token budget.
    Limits are validated rather than inheriting JavaScript slice edge cases.
    """
    if not isinstance(query, str):
        raise ValueError("query must be a string")
    if type(max_results) is not int or not 1 <= max_results <= 10000:
        raise ValueError("max_results must be an integer from 1 to 10000")

    tools = list(catalog)
    if len({tool.name for tool in tools}) != len(tools):
        raise ValueError("Duplicate tool names are not allowed")
    if allowed_names is not None:
        tools = [tool for tool in tools if tool.name in allowed_names]

    bounded = query[:16384]
    direct = re.fullmatch(r"select:(.+)", bounded, flags=re.IGNORECASE)
    if direct:
        names = [name.strip() for name in direct.group(1).split(",")[:64]]
        selected: list[Hit] = []
        seen: set[str] = set()
        for name in names:
            matches = [tool for tool in tools if tool.name == name]
            if not matches:
                matches = [tool for tool in tools if tool.mcp_names() is not None
                           and tool.mcp_names()[1] == name]
            for tool in matches:
                if tool.name not in seen:
                    selected.append(Hit(tool.name, None))
                    seen.add(tool.name)
        # Direct-select lists specify the desired tools; k applies to ranking.
        return SearchResult(bounded, tuple(selected), len(tools))

    words = bounded.strip().split()[:32]
    normalized = " ".join(words).lower()
    for tool in tools:
        if tool.name.lower() == normalized:
            return SearchResult(bounded, (Hit(tool.name, None),), len(tools))
    if normalized.startswith("mcp__") and len(normalized) > 5:
        matches = [Hit(tool.name, None) for tool in tools
                   if tool.name.lower().startswith(normalized)]
        if matches:
            return SearchResult(bounded, tuple(matches[:max_results]), len(tools))

    required = [word[1:] for word in normalized.split()
                if word.startswith("+") and len(word) > 1]
    optional = [word for word in normalized.split()
                if not (word.startswith("+") and len(word) > 1)]
    terms = required + optional
    ranked = [Hit(tool.name, _score(tool, terms, required)) for tool in tools]
    ranked = [hit for hit in ranked if hit.score and hit.score > 0]
    ranked.sort(key=lambda hit: hit.score, reverse=True)  # Stable on ties.
    return SearchResult(bounded, tuple(ranked[:max_results]), len(tools))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", required=True, type=Path)
    parser.add_argument("--query", required=True)
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--allow", action="append", help="Visible tool name; repeatable")
    parser.add_argument("--tool-use-id", help="Emit API tool_result with references")
    args = parser.parse_args()
    catalog = [Tool.from_dict(item) for item in json.loads(args.catalog.read_text())]
    result = search(catalog, args.query, args.limit,
                    allowed_names=set(args.allow) if args.allow is not None else None)
    print(json.dumps(result.as_tool_result(args.tool_use_id)
                     if args.tool_use_id else result.as_dict(), indent=2))


if __name__ == "__main__":
    main()
