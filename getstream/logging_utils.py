"""Redaction helpers for the SDK's structured log events. Secret values are
replaced with a literal marker; the scan is shallow by design."""

REDACTED = "<redacted>"
REDACTED_QUERY_PARAMS = {"api_key", "api_secret", "token"}
REDACTED_BODY_KEYS = {"api_secret", "token", "password"}


def redact_query(params):
    if not params:
        return params
    return {
        k: (REDACTED if k.lower() in REDACTED_QUERY_PARAMS else v)
        for k, v in dict(params).items()
    }


def redact_json_body(body):
    if not isinstance(body, dict):
        return body
    return {k: (REDACTED if k in REDACTED_BODY_KEYS else v) for k, v in body.items()}
