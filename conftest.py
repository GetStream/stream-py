import sys


def pytest_ignore_collect(path, config):
    # Only skip plugin/webrtc tests on Python < 3.10
    if sys.version_info < (3, 10):
        path_str = str(path)
        if "getstream/plugins/" in path_str or "getstream/video/rtc/" in path_str:
            return True
    return False
