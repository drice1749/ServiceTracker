#!/usr/bin/env python3
"""
Aruba CX Switch Collector (AOS-CX)
=================================

Evidence-based quarterly collector generated from frozen probe results.

Source of truth:
- Frozen command set: tools/command_probe/command_sets/aruba_cx.yaml
- Verified probe ID: cb03d34e-927e-4a34-b2ef-54bc5315d68f
- Software version tested: ML.10.15.1030

Guarantees:
- Read-only execution
- Timing-safe Netmiko interaction
- Raw artifact preservation
- Deterministic quarterly layout
"""

import json
import yaml
import uuid
import hashlib
import time
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any

from netmiko import ConnectHandler
from jsonschema import Draft202012Validator


# -------------------------
# Configuration
# -------------------------

COMMAND_SET_PATH = Path("tools/command_probe/command_sets/aruba_cx.yaml")
SCHEMA_PATH = Path("schemas/command_set.schema.json")

OUTPUT_ROOT = Path("artifacts/aruba_cx_switch")

COLLECTOR_NAME = "aruba_cx_switch_collector"
COLLECTOR_VERSION = "1.0.0"


# -------------------------
# Helpers
# -------------------------

def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def load_yaml(path: Path) -> Dict[str, Any]:
    with path.open() as f:
        return yaml.safe_load(f)


def load_schema(path: Path) -> Dict[str, Any]:
    with path.open() as f:
        return json.load(f)


def validate_command_set(data: Dict[str, Any], schema: Dict[str, Any]) -> None:
    validator = Draft202012Validator(schema)
    errors = list(validator.iter_errors(data))
    if errors:
        for err in errors:
            print(f"[SCHEMA ERROR] {list(err.path)}: {err.message}")
        raise SystemExit(1)


def enforce_blocked_keywords(command: str, blocked: list[str]) -> None:
    lowered = command.lower()
    for word in blocked:
        if word in lowered:
            raise ValueError(f"Blocked keyword '{word}' detected: {command}")


# -------------------------
# SSH (Timing-Safe)
# -------------------------

def connect_aruba_cx(host: str, username: str, password: str):
    return ConnectHandler(
        device_type="aruba_aoscx",
        host=host,
        username=username,
        password=password,
        fast_cli=False
    )


def disable_paging(conn, commands: list[str]):
    for cmd in commands:
        conn.send_command_timing(cmd)
        time.sleep(0.3)


def flush_channel(conn):
    time.sleep(0.2)
    conn.read_channel()


def execute_command(conn, command: str) -> Dict[str, Any]:
    flush_channel(conn)

    start = time.time()
    try:
        output = conn.send_command_timing(
            command,
            strip_prompt=False,
            strip_command=False
        )
        status = "success" if output.strip() else "empty"
        error = None
    except Exception as e:
        output = str(e)
        status = "failed"
        error = str(e)

    duration = int((time.time() - start) * 1000)

    return {
        "status": status,
        "output": output.encode(),
        "error": error,
        "duration_ms": duration
    }


# -------------------------
# Collector Core
# -------------------------

def run_collector(
    host: str,
    username: str,
    password: str,
    site: str,
    quarter: str
) -> None:
    command_set = load_yaml(COMMAND_SET_PATH)
    schema = load_schema(SCHEMA_PATH)

    validate_command_set(command_set, schema)

    blocked = command_set["safety"]["blocked_keywords"]

    run_id = str(uuid.uuid4())
    run_dir = OUTPUT_ROOT / site / quarter / host / run_id
    artifacts_dir = run_dir / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "collector": {
            "name": COLLECTOR_NAME,
            "version": COLLECTOR_VERSION
        },
        "run_id": run_id,
        "collected_at": now_utc(),
        "target": {
            "host": host,
            "platform": "aruba_cx",
            "vendor": "aruba"
        },
        "artifacts": [],
        "results": {}
    }

    conn = connect_aruba_cx(host, username, password)

    paging_cmds = (
        command_set
        .get("transport", {})
        .get("ssh", {})
        .get("paging_disable", [])
    )
    disable_paging(conn, paging_cmds)

    for category, commands in command_set["commands"].items():
        manifest["results"].setdefault(
            category,
            {"success": [], "failed": []}
        )

        for idx, entry in enumerate(commands, start=1):
            cmd = entry["command"]
            enforce_blocked_keywords(cmd, blocked)

            result = execute_command(conn, cmd)

            artifact_path = artifacts_dir / f"{category}_{idx}.txt"
            artifact_path.write_bytes(result["output"])
            checksum = sha256_bytes(result["output"])

            manifest["artifacts"].append({
                "category": category,
                "command": cmd,
                "path": str(artifact_path),
                "checksum": checksum,
                "status": result["status"],
                "duration_ms": result["duration_ms"]
            })

            if result["status"] == "success":
                manifest["results"][category]["success"].append(cmd)
            else:
                manifest["results"][category]["failed"].append(cmd)

    conn.disconnect()

    manifest_path = run_dir / "collector_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))

    print("[OK] Aruba CX Switch collection complete")
    print(f"     Artifacts: {artifacts_dir}")
    print(f"     Manifest : {manifest_path}")


# -------------------------
# CLI
# -------------------------

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Aruba CX Switch Quarterly Collector (Evidence-Based)"
    )
    parser.add_argument("--host", required=True)
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--site", required=True)
    parser.add_argument("--quarter", required=True)

    args = parser.parse_args()

    run_collector(
        host=args.host,
        username=args.username,
        password=args.password,
        site=args.site,
        quarter=args.quarter
    )


if __name__ == "__main__":
    main()
