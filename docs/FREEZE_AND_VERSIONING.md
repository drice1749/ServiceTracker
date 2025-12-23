FREEZE & VERSIONING RULES
========================

Once a command set is validated and verified:

chmod 444 <command_set.yaml>

This is REQUIRED.


WHY FREEZE?
-----------

Freezing prevents:
- Accidental edits
- Schema drift
- Silent behavior changes
- False assumptions during audits


MAKING CHANGES
--------------

If a change is required:
- Create a NEW command set file
- Increment version or filename
- Re-validate
- Re-test
- Re-freeze


NEVER:
- Edit a frozen contract
- Hotfix production contracts
- Assume backward compatibility

