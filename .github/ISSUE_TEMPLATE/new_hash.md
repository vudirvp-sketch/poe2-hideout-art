---
name: New decoration hash
about: Contribute a new entry for KNOWN_HASHES
title: "[hashes] add <Decoration Name> (hash <N>)"
labels: catalogue
---

## Decoration

- **Name (as shown in export):** <!-- e.g. "Palm Tree" -->
- **Hash (uint32):** <!-- e.g. 1234567890 -->
- **Source hideout:** <!-- e.g. "Kurast Hideout" -->
- **Is it art-only (not a gameplay object)?** yes / no

## How I verified it

<!-- Briefly: where did you observe this hash? If you parsed a file with
`hideout-art inspect`, paste the relevant output line. -->

```
# Output of: hideout-art inspect path/to/file.hideout | grep <Name>
```

## Suggested edit

```python
# In src/hideout_art/constants.py, KNOWN_HASHES:
"<Name>": <hash>,
# (and add to ART_TYPES if it is art-only)
```
