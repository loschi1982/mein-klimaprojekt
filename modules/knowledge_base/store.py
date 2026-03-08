"""
Knowledge Base – JSON-basierter Wissensspeicher
Team-Branch: team/knowledge-base
"""
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path


KNOWLEDGE_BASE_PATH = Path(__file__).parent.parent.parent / "memory" / "knowledge_base.json"


@dataclass
class KnowledgeEntry:
    id: str
    topic: str
    title: str
    content: str
    facts: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    updated_at: str = ""

    def __post_init__(self):
        if not self.updated_at:
            self.updated_at = datetime.now(timezone.utc).isoformat()


class KnowledgeStore:
    def __init__(self, path: Path | None = None):
        self.path = path or KNOWLEDGE_BASE_PATH
        self._data: dict[str, KnowledgeEntry] = {}
        self._load()

    def get(self, topic: str) -> KnowledgeEntry | None:
        return self._data.get(topic)

    def list_topics(self) -> list[str]:
        return sorted(self._data.keys())

    def search(self, query: str) -> list[KnowledgeEntry]:
        q = query.lower()
        results = []
        for entry in self._data.values():
            haystack = f"{entry.title} {entry.content} {' '.join(entry.tags)}".lower()
            if q in haystack:
                results.append(entry)
        return results

    def upsert(self, entry: KnowledgeEntry) -> None:
        entry.updated_at = datetime.now(timezone.utc).isoformat()
        self._data[entry.topic] = entry
        self._save()

    def _load(self) -> None:
        if not self.path.exists():
            self._data = {}
            return
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        self._data = {
            k: KnowledgeEntry(**v)
            for k, v in raw.get("entries", {}).items()
        }

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"entries": {k: asdict(v) for k, v in self._data.items()}}
        self.path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
