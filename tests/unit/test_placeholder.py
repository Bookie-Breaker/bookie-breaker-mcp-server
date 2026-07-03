"""Placeholder test so pytest collects at least one test until the service is scaffolded."""

import mcp_server


def test_package_imports() -> None:
    assert mcp_server is not None
