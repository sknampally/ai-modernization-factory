# Security Policy

## Supported versions

| Version | Supported |
| ------- | --------- |
| 0.1.x   | Yes |

## Reporting a vulnerability

Please **do not** open a public GitHub issue for security vulnerabilities.

Report privately by emailing the maintainer listed in the repository profile, or
by opening a private GitHub Security Advisory if enabled on the repository.

Include:

* A description of the issue and its impact
* Steps to reproduce (proof of concept if available)
* Affected versions or commit SHAs if known

You should receive an acknowledgment within a reasonable time. We will coordinate
a fix and disclosure timeline with you.

## Scope notes for AIMF

* Never commit secrets, tokens, or `.env` files.
* Configuration should reference credentials via environment variable names
  (`token_env`), not embed secret values.
* Reports and JSON artifacts must not include runtime credentials or absolute
  host paths that expose private environments.
