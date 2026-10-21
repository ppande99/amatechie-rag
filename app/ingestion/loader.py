"""Read Markdown / text files from a folder into `RawDoc`s.

Access control starts here. A file may begin with a small front-matter block:

    ---
    groups: sre, platform
    ---

Only users in one of those groups can later retrieve the file. No front matter means the
whole tenant can see it.
"""

import hashlib
from dataclasses import dataclass, field
from pathlib import Path

SUPPORTED_SUFFIXES = {".md", ".markdown", ".txt"}


@dataclass(frozen=True)
class RawDoc:
    source: str  # path relative to the ingest root; shown in citations
    text: str
    allowed_groups: list[str] = field(default_factory=list)

    @property
    def content_hash(self) -> str:
        # Hash the groups too: changing who may see a file must trigger re-indexing.
        payload = "\x00".join(sorted(self.allowed_groups)) + "\x01" + self.text
        return hashlib.sha256(payload.encode()).hexdigest()


def parse_front_matter(raw: str) -> tuple[list[str], str]:
    lines = raw.splitlines()
    if not lines or lines[0].strip() != "---":
        return [], raw
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        return [], raw

    groups: list[str] = []
    for line in lines[1:end]:
        key, _, value = line.partition(":")
        if key.strip() == "groups":
            groups = [g.strip() for g in value.split(",") if g.strip()]
    return groups, "\n".join(lines[end + 1 :]).lstrip("\n")


def load_directory(root: Path) -> list[RawDoc]:
    docs: list[RawDoc] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_SUFFIXES:
            continue
        groups, text = parse_front_matter(path.read_text(encoding="utf-8", errors="replace"))
        if text.strip():
            docs.append(RawDoc(source=path.relative_to(root).as_posix(), text=text, allowed_groups=groups))
    return docs
