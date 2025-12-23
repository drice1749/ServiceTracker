COMMAND SET SCHEMA
==================

The command_set.schema.json file is the single source of truth
for what a command contract may contain.

The schema enforces:
- Structural consistency
- Safety guarantees
- Predictable execution behavior


KEY SCHEMA CONSTRAINTS
---------------------

- commands MUST be grouped by category
- commands are lists, not objects
- only "command" and "optional" keys are allowed per entry
- unknown top-level keys are rejected
- safety flags must be correct types

This schema exists to prevent:
- Silent permission escalation
- Vendor-specific hacks
- Human error during editing


IMPORTANT YAML GOTCHA
---------------------

The following words are booleans in YAML and MUST be quoted:

- no
- yes
- false
- true
- off
- on

Failure to quote these will break validation.

