"""Redaction helpers for the SDK's structured log events. Secret values are
replaced with a literal marker."""

REDACTED = "<redacted>"
REDACTED_QUERY_PARAMS = {"api_key", "api_secret", "token"}
REDACTED_BODY_KEYS = {"api_secret", "token", "password"}
_REDACTED_KEY_SUBSTRINGS = (
    "secret",
    "token",
    "password",
    "credential",
    "private_key",
    "auth_key",
    "p12_cert",
    "stream_key",
)


def _is_sensitive_key(key):
    if not isinstance(key, str):
        return False
    lower = key.lower()
    if lower in REDACTED_BODY_KEYS:
        return True
    return any(sub in lower for sub in _REDACTED_KEY_SUBSTRINGS)


def redact_query(params):
    if not params:
        return params
    return {
        k: (REDACTED if k.lower() in REDACTED_QUERY_PARAMS else v)
        for k, v in dict(params).items()
    }


def redact_json_body(body):
    if isinstance(body, dict):
        return {
            k: (REDACTED if _is_sensitive_key(k) else redact_json_body(v))
            for k, v in body.items()
        }
    if isinstance(body, list):
        return [redact_json_body(item) for item in body]
    return body
