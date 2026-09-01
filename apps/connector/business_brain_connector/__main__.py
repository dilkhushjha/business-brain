from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from apps.connector.business_brain_connector.config import ConnectorConfig
from apps.connector.business_brain_connector.sync import run


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="business-brain-connector")
    parser.add_argument(
        "--config",
        default="connector.config.json",
        help="Path to the connector config JSON file (default: connector.config.json)",
    )
    parser.add_argument(
        "--state",
        default=None,
        help="Path to the sync-state file (default: <config dir>/connector.state.json)",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Config file not found: {config_path}", file=sys.stderr)
        return 1

    config = ConnectorConfig.load(config_path)
    state_path = Path(args.state) if args.state else config_path.parent / "connector.state.json"

    try:
        run(config, state_path)
    except KeyboardInterrupt:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
