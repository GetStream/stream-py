from getstream import _rust
from getstream.version import VERSION


class TestVersion:
    def test_version_matches_package(self):
        assert _rust.__version__ == VERSION
