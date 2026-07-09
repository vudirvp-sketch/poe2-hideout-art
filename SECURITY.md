# Reporting security issues

This project is a offline file-format toolkit. It does not run a server,
does not make network requests, and does not execute code from `.hideout`
files. The attack surface is therefore minimal.

That said, if you find a way to:

* cause the parser to crash on a malformed `.hideout` file (DoS),
* write outside the intended output directory (path traversal),
* execute arbitrary code via a crafted input,

please report it **privately** by emailing the maintainers rather than
opening a public issue. There is no bug bounty programme; we just ask
for responsible disclosure.

## Threat model

| Asset | Risk | Mitigation |
|---|---|---|
| `.hideout` files (input) | Could be crafted to crash the parser | Parser is regex-based, never `eval`s or `exec`s input |
| Output paths | Could contain `..` segments | `write_hideout()` uses `Path.parent.mkdir(parents=True, exist_ok=True)` — paths are user-supplied and trusted |
| Image inputs (Pillow) | Decoding vulnerabilities in Pillow | Out of scope; update Pillow regularly |

## What is NOT in scope

- The game itself — Path of Exile 2 is owned by Grinding Gear Games.
- Anything related to cheating, automation, or violating the game's
  Terms of Service. This tool reads and writes export files only.
