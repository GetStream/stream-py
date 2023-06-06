class VideoClientError(Exception):
    def __init__(self, message, code, status_code):
        super().__init__(message)
        self.code = code
        self.status_code = status_code


class VideoCallTypeBadRequest(VideoClientError):
    def __init__(self, message, code, status_code):
        super().__init__(message, code, status_code)


class VideoCallTypeNotFound(VideoClientError):
    def __init__(self, message, code, status_code):
        super().__init__(message, code, status_code)


class VideoUnauthorized(VideoClientError):
    def __init__(self, message, code, status_code):
        super().__init__(message, code, status_code)


class VideoForbidden(VideoClientError):
    def __init__(self, message, code, status_code):
        super().__init__(message, code, status_code)


class VideoTimeout(VideoClientError):
    def __init__(self, message, code, status_code):
        super().__init__(message, code, status_code)


class VideoPayloadTooLarge(VideoClientError):
    def __init__(self, message, code, status_code):
        super().__init__(message, code, status_code)


class VideoTooManyRequests(VideoClientError):
    def __init__(self, message, code, status_code):
        super().__init__(message, code, status_code)


class VideoRequestHeaderFieldsTooLarge(VideoClientError):
    def __init__(self, message, code, status_code):
        super().__init__(message, code, status_code)


class VideoInternalServerError(VideoClientError):
    def __init__(self, message, code, status_code):
        super().__init__(message, code, status_code)
