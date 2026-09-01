from __future__ import annotations

import json
import mimetypes
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path


class UploadError(Exception):
    """Raised when a single upload attempt fails. The caller (sync.py) owns
    retry/backoff policy -- this module only performs one attempt."""


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
    """Upload a source file to the ingestion API's import endpoint.

    Uses only the standard library (urllib) so the connector has no
    third-party runtime dependency on a bare Windows/Tally workstation,
    matching the constraint already documented for the folder watcher.

    Raises UploadError for any network failure or non-2xx/409 response, so
    the caller can apply its own retry/backoff policy. A 409 (the backend
    telling us this exact source was already imported) is treated as a
    successful outcome from the connector's point of view: the file is
    synced either way, so there is nothing to retry.
    """
    file_path = Path(path)
    boundary = "----BusinessBrainConnectorBoundary"
    content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    body = _build_multipart_body(file_path, boundary, content_type)

    url = f"{api_base_url.rstrip('/')}/ingestion/import/{business_id}"
    headers = {
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "Content-Length": str(len(body)),
    }
    if api_token:
        headers["Authorization"] = f"Bearer {api_token}"

    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = _parse_json(response.read())
            return UploadResult(status_code=response.status, already_imported=False, response_body=payload)
    except urllib.error.HTTPError as exc:
        detail = exc.read()
        if exc.code == 409:
            return UploadResult(status_code=exc.code, already_imported=True, response_body=_parse_json(detail))
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
    return b"".join(
        [
            f"--{boundary}\r\n".encode(),
            f'Content-Disposition: form-data; name="file"; filename="{file_path.name}"\r\n'.encode(),
            f"Content-Type: {content_type}\r\n\r\n".encode(),
            data,
            f"\r\n--{boundary}--\r\n".encode(),
        ]
    )
