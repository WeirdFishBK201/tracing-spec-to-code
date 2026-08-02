from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ParsedMarkdownValues:
    values: tuple[str, ...]
    error: str | None = None


def parse_markdown_values(value: str) -> ParsedMarkdownValues:
    """Parse a comma-separated Markdown value list without guessing intent."""
    stripped = value.strip()
    if not stripped:
        return ParsedMarkdownValues(())

    values: list[str] = []
    seen: set[str] = set()
    for position, raw_item in enumerate(stripped.split(","), start=1):
        item = raw_item.strip()
        if not item:
            return ParsedMarkdownValues(
                tuple(values),
                f"empty value at position {position}",
            )

        if "`" in item:
            if (
                len(item) < 2
                or not item.startswith("`")
                or not item.endswith("`")
                or "`" in item[1:-1]
            ):
                return ParsedMarkdownValues(
                    tuple(values),
                    f"unpaired backtick at position {position}",
                )
            item = item[1:-1].strip()
            if not item:
                return ParsedMarkdownValues(
                    tuple(values),
                    f"empty value at position {position}",
                )

        if item in seen:
            return ParsedMarkdownValues(
                tuple(values),
                f"duplicate value at position {position}: {item}",
            )
        seen.add(item)
        values.append(item)

    return ParsedMarkdownValues(tuple(values))
