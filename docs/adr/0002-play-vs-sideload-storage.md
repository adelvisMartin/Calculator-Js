# ADR 0002: Separate Play and Sideload Storage Policies

- Status: Accepted
- Date: 2026-08-23

## Context
InSave Recovery's automatic WhatsApp/WhatsApp Business status gallery benefits from direct access to current `.Statuses` paths under Android shared storage. The sideload product can explicitly request broad file access, but Google Play policy places strong restrictions on `MANAGE_EXTERNAL_STORAGE` and other special-access permissions.

Trying to hide this distinction behind one manifest would either break the requested automatic sideload experience or create an avoidable Play-policy risk.

## Decision
Use explicit build flavors with different permission contracts.

### GitHub/Recovery sideload
- automatic local status discovery remains primary;
- may retain `MANAGE_EXTERNAL_STORAGE` for this feature;
- user-facing explanation and physical OEM QA are required;
- no status file is sent to Provider C or another server.

### Play
A source-set manifest overlay removes:
- `MANAGE_EXTERNAL_STORAGE`;
- `REQUEST_IGNORE_BATTERY_OPTIMIZATIONS`;
- `SCHEDULE_EXACT_ALARM`.

CI must compile the Play flavor and inspect the merged manifest. Source-file presence alone is not evidence.

The Play product must rely on policy-compliant storage access (MediaStore/SAF or explicit user-selected directory where required). Automatic sideload behavior cannot be falsely claimed as identical if the platform/policy does not permit it.

## Consequences
- distribution intent is explicit in build metadata;
- sideload UX remains strong;
- Play policy risk is reduced;
- QA must cover two permission models;
- documentation/store listing must explain feature differences accurately.
