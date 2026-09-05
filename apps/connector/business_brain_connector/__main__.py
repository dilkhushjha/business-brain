from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from apps.connector.business_brain_connector.config import ConnectorConfig
from apps.connector.business_brain_connector.sync import run
from apps.connector.business_brain_connector.uploader import UploadError, register_connector


def _cmd_run(args: argparse.Namespace) -> int:
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Config file not found: {config_path}", file=sys.stderr)
        print("Run 'business-brain-connector register' first to create one.", file=sys.stderr)
        return 1

    config = ConnectorConfig.load(config_path)
    state_path = Path(args.state) if args.state else config_path.parent / "connector.state.json"

    try:
        run(config, state_path)
    except KeyboardInterrupt:
        return 0
    return 0


def _cmd_register(args: argparse.Namespace) -> int:
    """One-time interactive setup: exchange a registration key for a
    connector token, then write a ready-to-use config file. Everything
    after this runs unattended -- this is deliberately the one manual step."""
    config_path = Path(args.config)
    if config_path.exists() and not args.force:
        print(f"{config_path} already exists. Pass --force to overwrite it.", file=sys.stderr)
        return 1

    try:
        result = register_connector(args.business_id, args.api_base_url, args.registration_key)
    except UploadError as exc:
        print(f"Registration failed: {exc}", file=sys.stderr)
        return 1

    token = result.get("token")
    if not token:
        print(f"Registration response did not include a token: {result}", file=sys.stderr)
        return 1

    config = ConnectorConfig(
        business_id=args.business_id,
        source_dir=args.source_dir,
        api_base_url=args.api_base_url,
        api_token=token,
    )
    config.save(config_path)

    print(f"Registered connector {result.get('connector_id', '?')} for business {args.business_id}.")
    print(f"Config written to {config_path}.")
    if result.get("warning"):
        print(result["warning"])
    print("Run 'business-brain-connector run' to start syncing.")
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:]) if argv is None else list(argv)

    parser = argparse.ArgumentParser(prog="business-brain-connector")
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="Watch the source folder and sync files (default)")
    run_parser.add_argument("--config", default="connector.config.json",
                             help="Path to the connector config JSON file")
    run_parser.add_argument("--state", default=None,
                             help="Path to the sync-state file (default: <config dir>/connector.state.json)")
    run_parser.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging")
    run_parser.set_defaults(func=_cmd_run)

    register_parser = subparsers.add_parser("register", help="One-time setup: obtain a token and write a config file")
    register_parser.add_argument("--business-id", required=True)
    register_parser.add_argument("--source-dir", required=True, help="Folder to watch for Tally exports")
    register_parser.add_argument("--api-base-url", default="http://localhost:8000/api")
    register_parser.add_argument("--registration-key", default=None,
                                  help="X-Connector-Registration-Key (required unless the server is in dev mode)")
    register_parser.add_argument("--config", default="connector.config.json",
                                  help="Where to write the resulting config file")
    register_parser.add_argument("--force", action="store_true", help="Overwrite an existing config file")
    register_parser.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging")
    register_parser.set_defaults(func=_cmd_register)

    # Preserve old-style invocations with no subcommand (e.g. `--config x`)
    # by defaulting to `run` -- argparse subparsers otherwise have no
    # built-in notion of a default subcommand.
    if not argv or argv[0] not in ("run", "register", "-h", "--help"):
        argv = ["run", *argv]

    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if getattr(args, "verbose", False) else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
