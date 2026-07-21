"""Centralized secret redaction for operational output."""

from __future__ import annotations

import re
from collections.abc import Iterable
from urllib.parse import quote, unquote

REDACTED = "[REDACTED]"

# Supplementary pattern-based redaction for recognizable credential shapes.
_GITHUB_TOKEN_PATTERN = re.compile(
    r"(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})",
)
_BEARER_PATTERN = re.compile(
    r"(?i)(Authorization:\s*Bearer\s+)\S+",
)
_BASIC_PATTERN = re.compile(
    r"(?i)(Authorization:\s*Basic\s+)\S+",
)
_URL_USERINFO_PATTERN = re.compile(
    r"(https?://)([^/\s:@]+):([^/\s@]+)@",
)
_HELPER_PATH_PATTERN = re.compile(
    r"(?i)(/[^\s]*aimf[-_](?:askpass|git-auth)[^\s]*)",
)


class Redactor:
    """Sanitize secrets from operational text while preserving structure."""

    def __init__(
        self,
        *,
        secrets: Iterable[str] | None = None,
        helper_paths: Iterable[str] | None = None,
    ) -> None:
        self._secrets = [secret for secret in (secrets or []) if secret]
        self._helper_paths = [path for path in (helper_paths or []) if path]

    def with_secrets(self, *secrets: str) -> Redactor:
        """Return a new redactor that also redacts the given secret values."""

        return Redactor(
            secrets=[*self._secrets, *secrets],
            helper_paths=self._helper_paths,
        )

    def with_helper_paths(self, *paths: str) -> Redactor:
        """Return a new redactor that also redacts helper filesystem paths."""

        return Redactor(
            secrets=self._secrets,
            helper_paths=[*self._helper_paths, *paths],
        )

    def redact(self, text: str | None) -> str:
        """Return sanitized text. Exact secret values are always removed."""

        if text is None:
            return ""
        if text == "":
            return ""

        sanitized = text

        for secret in sorted(self._secrets, key=len, reverse=True):
            sanitized = sanitized.replace(secret, REDACTED)
            encoded = quote(secret, safe="")
            if encoded and encoded != secret:
                sanitized = sanitized.replace(encoded, REDACTED)
            try:
                decoded = unquote(secret)
            except Exception:  # noqa: BLE001 - defensive decoding only
                decoded = secret
            if decoded and decoded != secret:
                sanitized = sanitized.replace(decoded, REDACTED)

        for path in sorted(self._helper_paths, key=len, reverse=True):
            sanitized = sanitized.replace(path, REDACTED)

        sanitized = _URL_USERINFO_PATTERN.sub(rf"\1{REDACTED}:{REDACTED}@", sanitized)
        sanitized = _BEARER_PATTERN.sub(rf"\1{REDACTED}", sanitized)
        sanitized = _BASIC_PATTERN.sub(rf"\1{REDACTED}", sanitized)
        sanitized = _GITHUB_TOKEN_PATTERN.sub(REDACTED, sanitized)
        sanitized = _HELPER_PATH_PATTERN.sub(REDACTED, sanitized)

        # Keep already-redacted markers stable under repeated application.
        sanitized = sanitized.replace(f"{REDACTED}{REDACTED}", REDACTED)
        return sanitized


def redact_secrets(
    text: str | None,
    *,
    secrets: Iterable[str] | None = None,
    helper_paths: Iterable[str] | None = None,
) -> str:
    """Convenience wrapper around :class:`Redactor`."""

    return Redactor(secrets=secrets, helper_paths=helper_paths).redact(text)
