#!/usr/bin/env python3
"""
Command Probe — ArubaOS-Switch (Read-Only, Timing-Safe)
------------------------------------------------------
Fixes Netmiko prompt desync issues by using send_command_timing().

- ArubaOS / ProCurve compatible
- No expect_string usage
- Deterministic output capture
- Read-only
"""

import json
import uuid
import yaml
import hashlib
import time
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any

from jsonschema import Draft202012Validator
from netmiko import ConnectHandler


# -------------------------
# Configuration
# -------------------------

SCHEMA_PATH = Path("schemas/command_set.schema.json")
OUTPUT_ROOT = Path("tools/command_probe/output")

TOOL_NAME = "command_probe"
TOOL_VERSION = "0.3.0"


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


def load_schema() -> Dict[str, Any]:
    with SCHEMA_PATH.open() as f:
        return json.load(f)


def validate_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> None:
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
    if errors:
        for err in errors:
            print(f"[SCHEMA ERROR] {list(err.path)}: {err.message}")
        raise SystemExit(1)


def enforce_blocked_keywords(command: str, blocked: list[str]) -> None:
    lowered = command.lower()
    for word in blocked:
        if word in lowered:
            raise ValueError(
                f"Blocked keyword '{word}' detected in command: {command}"
            )


# -------------------------
# SSH Execution (Timing-Safe)
# -------------------------

def connect_aruba_os(host: str, username: str, password: str):
    return ConnectHandler(
        device_type="aruba_os",
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
    """
    Drain any residual output before issuing the next command.
    """
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
# Probe Core
# -------------------------

def run_probe(
    command_set_path: Path,
    host: str,
    username: str,
    password: str
) -> None:
    schema = load_schema()
    command_set = load_yaml(command_set_path)
    validate_schema(command_set, schema)

    blocked = command_set["safety"]["blocked_keywords"]

    probe_id = str(uuid.uuid4())
    probe_dir = OUTPUT_ROOT / probe_id
    artifacts_dir = probe_dir / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "probe_id": probe_id,
        "created_at": now_utc(),
        "tool": {
            "name": TOOL_NAME,
            "version": TOOL_VERSION
        },
        "target": {
            "host": host,
            "port": 22,
            "transport": "ssh",
            "platform_guess": "aos-switch",
            "vendor_guess": "aruba",
            "auth_method": "password"
        },
        "safety": command_set["safety"],
        "command_attempts": [],
        "results": {},
        "artifacts": []
    }

    conn = connect_aruba_os(host, username, password)

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
            {"supported": [], "unsupported": []}
        )

        for idx, entry in enumerate(commands, start=1):
            cmd = entry["command"]
            enforce_blocked_keywords(cmd, blocked)

            result = execute_command(conn, cmd)

            artifact_path = artifacts_dir / f"{category}_{idx}.txt"
            artifact_path.write_bytes(result["output"])
            checksum = sha256_bytes(result["output"])

            manifest["command_attempts"].append({
                "command": cmd,
                "category": category,
                "attempt_index": idx,
                "status": result["status"],
                "duration_ms": result["duration_ms"],
                "error": result["error"],
                "artifact_path": str(artifact_path)
            })

            manifest["artifacts"].append({
                "path": str(artifact_path),
                "command": cmd,
                "category": category,
                "checksum": checksum
            })

            if result["status"] == "success":
                manifest["results"][category]["supported"].append(cmd)
            else:
                manifest["results"][category]["unsupported"].append(cmd)

    conn.disconnect()

    manifest_path = probe_dir / "probe_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))

    print("[OK] Probe complete (timing-safe)")
    print(f"     Manifest: {manifest_path}")


# -------------------------
# CLI
# -------------------------

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="ArubaOS-Switch Command Probe (Timing-Safe, Read-Only)"
    )
    parser.add_argument("--command-set", required=True)
    parser.add_argument("--host", required=True)
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)

    args = parser.parse_args()

    run_probe(
        Path(args.command_set),
        args.host,
        args.username,
        args.password
    )


if __name__ == "__main__":
    main()
