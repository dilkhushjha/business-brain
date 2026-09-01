from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(slots=True)
class ConnectorConfig:
    """Local connector configuration.

    The first milestone deliberately keeps configuration local and simple. The
    cloud API URL/token are supplied by the operator rather than hard-coded.
    """

    business_id: str
    source_dir: str
    api_base_url: str = "http://localhost:8000/api"
    poll_seconds: int = 30
    api_token: str | None = None
    max_upload_retries: int = 5
    retry_backoff_seconds: float = 5.0

    @classmethod
    def load(cls, path: str | Path) -> "ConnectorConfig":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(**payload)

    def save(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")
