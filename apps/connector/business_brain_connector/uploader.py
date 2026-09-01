from __future__ import annotations

import json
import mimetypes
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path


class UploadError(Exception):
    """Raised when a single upload attempt fails."""


@dataclass(frozen=True)
class UploadResult:
    status_code: int
    already_imported: bool
    response_body: dict


def upload_file(
    path: str | Path,
    business_id: str,
    api_base_url: str,
    api_token: str | None = None,
    timeout: float = 60.0,
) -> UploadResult:
    """Upload a source file through the authenticated connector endpoint."""
    if not api_token:
        raise UploadError("Connector API token is required for automatic synchronization")

    file_path = Path(path)
    boundary = "----BusinessBrainConnectorBoundary"
    content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    body = _build_multipart_body(file_path, boundary, content_type)
    url = f"{api_base_url.rstrip('/')}/connectors/import/{business_id}"
    headers = {
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "Content-Length": str(len(body)),
        "Authorization": f"Bearer {api_token}",
    }
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return UploadResult(response.status, False, _parse_json(response.read()))
    except urllib.error.HTTPError as exc:
        detail = exc.read()
        if exc.code == 409:
            return UploadResult(exc.code, True, _parse_json(detail))
        raise UploadError(f"HTTP {exc.code}: {detail.decode('utf-8', errors='replace')}") from exc
    except urllib.error.URLError as exc:
        raise UploadError(f"Connection error: {exc.reason}") from exc
    except TimeoutError as exc:
        raise UploadError(f"Upload timed out after {timeout}s") from exc


def _parse_json(raw: bytes) -> dict:
    if not raw:
        return {}
    try:
        return json.loads(raw.decode("utf-8"))
    except ValueError:
        return {"raw": raw.decode("utf-8", errors="replace")}


def _build_multipart_body(file_path: Path, boundary: str, content_type: str) -> bytes:
    data = file_path.read_bytes()
    return b"".join([
        f"--{boundary}\r\n".encode(),
        f'Content-Disposition: form-data; name="file"; filename="{file_path.name}"\r\n'.encode(),
        f"Content-Type: {content_type}\r\n\r\n".encode(),
        data,
        f"\r\n--{boundary}--\r\n".encode(),
    ])
