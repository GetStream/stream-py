# 0.4.0 (11-04-2024): Fix OwnCapability enum
- Fix/Breaking: OwnCapability as an enum was causing issues, we changed it to a class with Final attributes

# 0.3.0 (25-03-2024): External Storage and Transcriptions
- New: Support for external storage endpoints
- New: Support for transcriptions endpoints

# 0.2.0 (06-12-2023): Support User management endpoints

- New: reactivate_users and deactivate_users
- New: upsert_users and delete_users
- New: query_users
- breaking change: rename Apierror -> ApiError

# 0.1.2: Initial release of the package to PyPI (25-10-2023)
