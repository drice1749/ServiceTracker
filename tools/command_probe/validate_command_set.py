import json
import sys
import yaml
from jsonschema import Draft202012Validator

SCHEMA_PATH = "schemas/command_set.schema.json"


def enforce_blocked_keywords(command: str, blocked: list[str]):
    lowered = command.lower()
    for word in blocked:
        if word in lowered:
            raise ValueError(
                f"Blocked keyword '{word}' detected in command: {command}"
            )


def main(path):
    with open(SCHEMA_PATH) as f:
        schema = json.load(f)

    with open(path) as f:
        data = yaml.safe_load(f)

    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: e.path)

    if errors:
        for err in errors:
            print(f"[SCHEMA ERROR] {list(err.path)}: {err.message}")
        sys.exit(1)

    blocked = data["safety"]["blocked_keywords"]
    for category, commands in data["commands"].items():
        for entry in commands:
            enforce_blocked_keywords(entry["command"], blocked)

    print(f"[OK] Command set '{path}' is valid and safe.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python validate_command_set.py <command_set.yaml>")
        sys.exit(1)

    main(sys.argv[1])
